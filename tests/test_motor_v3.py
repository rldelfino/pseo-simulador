"""Motor v3 (31/out/2026): projeção anual, série por banco, páginas mensais,
metodologia, resposta direta nas páginas de banco e a regra de indexação."""
import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gerador import (
    MESES_INDEXAVEIS_MENSAL, SLUG_INDICE_MENSAL, VALORES_INDEXAVEIS, calcular_sac_price, carregar_historico,
    pagina_indexavel, posicao_no_mercado, projecao_anual, serie_do_banco, slug_mes,
)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "paginas_seo")
gerada = os.path.isdir(PASTA)


def _ler(nome):
    return open(os.path.join(PASTA, nome), encoding="utf-8").read()


def test_projecao_anual_fecha_com_o_calculo_principal():
    proj = projecao_anual(400_000, 360, 11.5)
    ref = calcular_sac_price(400_000, 360, 11.5)
    ultimo = proj["linhas"][-1]
    assert ultimo["ano"] == 30
    assert ultimo["saldo_sac"] < 1 and ultimo["saldo_price"] < 1
    assert ultimo["juros_sac"] == pytest.approx(ref["total_sac"] - 400_000, rel=1e-6)
    assert ultimo["juros_price"] == pytest.approx(ref["total_price"] - 400_000, rel=1e-6)
    assert proj["pmt_price"] == pytest.approx(ref["p1_price"], rel=1e-9)
    assert [x["ano"] for x in proj["linhas"]][:3] == [1, 2, 3]


def test_indexabilidade_exige_prazo_e_valor_redondo():
    assert pagina_indexavel(500_000, 360) and pagina_indexavel(150_000, 420)
    assert not pagina_indexavel(500_000, 240)
    assert not pagina_indexavel(1_450_000, 360) and not pagina_indexavel(450_000, 360)
    assert 500_000 in VALORES_INDEXAVEIS and 1_000_000 in VALORES_INDEXAVEIS


def test_posicao_no_mercado_nao_cita_concorrente():
    ranking = [{"banco": b, "cet": c} for b, c in (("A", 10.0), ("B", 11.0), ("C", 12.0), ("D", 13.0))]
    frase = posicao_no_mercado(ranking, "B", 11.0)
    assert "2ª posição entre 4 bancos" in frase and "mediana" in frase
    assert not re.search(r"\b[ABCD]\b", frase.replace("A ", ""))  # sem nomes de banco
    assert posicao_no_mercado(ranking[:2], "A", 10.0) == ""


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_paginas_de_simulacao_tem_blocos_proprios():
    html = _ler("simulador-itau-500-mil-360-meses.html")
    assert "Como a dívida evolui ano a ano" in html
    assert "Taxa do Itaú nos últimos meses" in html
    assert "Valores e prazos vizinhos no Itaú" in html
    assert "posição entre" in html
    assert 'href="metodologia"' in html and f'href="{SLUG_INDICE_MENSAL}"' in html
    # duas páginas do mesmo banco não repetem a tabela anual
    outra = _ler("simulador-itau-300-mil-360-meses.html")
    tab = lambda h: re.search(r"<tbody>(.*?)</tbody>", h[h.index("Como a dívida evolui"):], re.S).group(1)
    assert tab(html) != tab(outra)


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_paginas_mensais_existem_com_indexacao_certa():
    historico = carregar_historico()
    meses = sorted({r["inicio_periodo"] for r in historico})
    assert len(meses) >= 12
    sitemap = _ler("sitemap.xml")
    for k, mes in enumerate(meses):
        html = _ler(slug_mes(mes) + ".html")
        recente = mes in meses[-MESES_INDEXAVEIS_MENSAL:]
        assert ('name="robots" content="noindex,follow"' not in html) == recente, mes
        assert (f"/{slug_mes(mes)}</loc>" in sitemap) == recente, mes
        assert "Taxa de financiamento imobiliário em" in html and "<table" in html
    assert f"/{SLUG_INDICE_MENSAL}</loc>" in sitemap


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_pagina_mensal_faq_visivel_igual_ao_json_ld():
    html = _ler(slug_mes(sorted({r["inicio_periodo"] for r in carregar_historico()})[-1]) + ".html")
    blocos = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    faq = next(json.loads(b) for b in blocos if '"FAQPage"' in b)
    visivel = html
    for q in faq["mainEntity"]:
        assert q["name"] in visivel
        assert q["acceptedAnswer"]["text"] in visivel


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_metodologia_hub_e_footer():
    met = _ler("metodologia.html")
    assert "903201" in met and "TIR" in met and "contato@datalabglobal.com" in met
    assert "/metodologia</loc>" in _ler("sitemap.xml")
    hub = _ler("banco-itau.html")
    assert re.search(r"Taxa do Itaú hoje: \d+,\d{2}% ao ano", hub)
    assert 'href="/metodologia"' in _ler("index.html")
    assert "taxas-financiamento-imobiliario" in _ler("llms.txt")


# ---- motor v3b: renda, llms-full, ItemList/Dataset, medição ----
import gerador  # noqa: E402


def test_renda_minima_cai_com_mais_entrada_e_prazo_maior():
    taxas = {b: 11.5 for b in gerador.BANCOS}
    r20 = gerador.renda_minima(500_000, 0.20, 30, taxas)
    r50 = gerador.renda_minima(500_000, 0.50, 30, taxas)
    r35 = gerador.renda_minima(500_000, 0.20, 35, taxas)
    assert r50["renda_sac"] < r20["renda_sac"]
    if r35:
        assert r35["renda_sac"] < r20["renda_sac"]
    assert r20["renda_sac"] >= r20["p1_sac"] / 0.30 - 50
    assert r20["renda_price"] < r20["renda_sac"]


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_paginas_de_renda_existem_no_sitemap_e_com_faq_igual_ao_json_ld():
    sitemap = _ler("sitemap.xml")
    for v in VALORES_INDEXAVEIS:
        slug = gerador.slug_renda(v)
        html = _ler(slug + ".html")
        assert f"/{slug}</loc>" in sitemap and 'content="noindex' not in html
        blocos = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        faq = next(json.loads(b) for b in blocos if '"FAQPage"' in b)
        for q in faq["mainEntity"]:
            assert q["name"] in html and q["acceptedAnswer"]["text"] in html
    assert f"/{gerador.SLUG_INDICE_RENDA}</loc>" in sitemap
    a, b = _ler(gerador.slug_renda(300_000) + ".html"), _ler(gerador.slug_renda(500_000) + ".html")
    assert re.search(r"<tbody>(.*?)</tbody>", a, re.S).group(1) != re.search(r"<tbody>(.*?)</tbody>", b, re.S).group(1)


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_llms_full_itemlist_dataset_e_medicao_desligada():
    full = _ler("llms-full.txt")
    assert "Taxas usadas nas simulações hoje" in full and "% ao ano" in full and "CC BY 4.0" in full
    comp = _ler("financiamento-imobiliario-500-mil-30-anos.html")
    assert '"ItemList"' in comp
    mensal = _ler(slug_mes(sorted({r["inicio_periodo"] for r in carregar_historico()})[-1]) + ".html")
    assert '"Dataset"' in mensal and "temporalCoverage" in mensal
    assert not gerador.UMAMI_WEBSITE_ID
    assert "umami" not in _ler("index.html").lower() and not os.path.exists(os.path.join(PASTA, "medicao.js"))
    assert "cloud.umami.is" in _ler("_headers")  # CSP já pronta para quando o ID for preenchido


def test_tags_de_medicao_so_com_id(monkeypatch):
    assert gerador.tags_medicao() == []
    monkeypatch.setattr(gerador, "UMAMI_WEBSITE_ID", "abc-123")
    tags = "".join(gerador.tags_medicao())
    assert 'data-website-id="abc-123"' in tags and 'data-do-not-track="true"' in tags and "/medicao.js" in tags
