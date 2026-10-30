"""
Páginas de comparação sem marca de banco (financiamento-imobiliario-{valor}-
mil-{anos}-anos) e poda das páginas de prazo curto — ver PRAZOS_INDEXAVEIS e
gerar_paginas_comparacao em gerador.py (auditoria de SEO, 29/out/2026).
"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bancos import BANCOS
from gerador import (
    ANOS_COMPARACAO, MIN_BANCOS_COMPARACAO, PRAZOS_INDEXAVEIS, VALORES_COMPARACAO,
    bancos_com_prazo, calcular_sac_price, linhas_comparacao, pagina_comparacao_existe, slug_comparacao,
)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_SAIDA = os.path.join(RAIZ, "paginas_seo")
gerada = os.path.isdir(PASTA_SAIDA)


def test_slug_comparacao():
    assert slug_comparacao(300_000, 30) == "financiamento-imobiliario-300-mil-30-anos"
    assert slug_comparacao(1_000_000, 10) == "financiamento-imobiliario-1000-mil-10-anos"


def test_prazo_de_35_anos_so_com_bancos_que_oferecem():
    bancos = bancos_com_prazo(420)
    assert bancos and all(BANCOS[b]["prazo_max"] >= 420 for b in bancos)
    assert len(bancos_com_prazo(360)) == len(BANCOS)


def test_comparacao_nunca_mostra_banco_com_prazo_menor_que_o_pedido():
    for anos in ANOS_COMPARACAO:
        if not pagina_comparacao_existe(300_000, anos):
            continue
        for x in linhas_comparacao(300_000, anos * 12):
            assert BANCOS[x["banco"]]["prazo_max"] >= anos * 12


def test_linhas_ordenadas_por_cet_e_batem_com_calculo_direto():
    linhas = linhas_comparacao(300_000, 360)
    cets = [x["cet"] for x in linhas]
    assert cets == sorted(cets)
    x = linhas[0]
    financiado = 300_000 * BANCOS[x["banco"]]["ltv"]
    r = calcular_sac_price(financiado, 360, x["taxa"], 300_000)
    assert x["p1_sac"] == pytest.approx(r["p1_sac"]) and x["cet"] == pytest.approx(r["cet_sac"])


def test_prazos_indexaveis_sao_360_e_420():
    assert PRAZOS_INDEXAVEIS == (360, 420)


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_paginas_de_comparacao_existem_e_estao_no_sitemap():
    sitemap = open(os.path.join(PASTA_SAIDA, "sitemap.xml"), encoding="utf-8").read()
    esperadas = [(v, a) for v in VALORES_COMPARACAO for a in ANOS_COMPARACAO if pagina_comparacao_existe(v, a)]
    assert len(esperadas) > 100
    for v, a in esperadas:
        slug = slug_comparacao(v, a)
        assert os.path.exists(os.path.join(PASTA_SAIDA, slug + ".html")), slug
        assert f"/{slug}</loc>" in sitemap, slug
    assert "/financiamento-imobiliario</loc>" in sitemap


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_paginas_de_prazo_curto_sao_noindex_e_fora_do_sitemap():
    sitemap = open(os.path.join(PASTA_SAIDA, "sitemap.xml"), encoding="utf-8").read()
    for nome in os.listdir(PASTA_SAIDA):
        m = re.match(r"simulador-.+-(\d+)-mil-(\d+)-meses\.html$", nome)
        if not m:
            continue
        prazo = int(m.group(2))
        html = open(os.path.join(PASTA_SAIDA, nome), encoding="utf-8").read()
        tem_noindex = 'name="robots" content="noindex,follow"' in html
        no_sitemap = f"/{nome[:-5]}</loc>" in sitemap
        if prazo in PRAZOS_INDEXAVEIS:
            assert not tem_noindex and no_sitemap, nome
        else:
            assert tem_noindex and not no_sitemap, nome


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_pagina_de_comparacao_tem_titulo_unico_e_numeros_proprios():
    titulos, descs = set(), set()
    for v in VALORES_COMPARACAO:
        for a in ANOS_COMPARACAO:
            if not pagina_comparacao_existe(v, a):
                continue
            html = open(os.path.join(PASTA_SAIDA, slug_comparacao(v, a) + ".html"), encoding="utf-8").read()
            t = re.search(r"<title>(.*?)</title>", html).group(1)
            d = re.search(r'name="description" content="(.*?)"', html).group(1)
            assert len(t) <= 60 and len(d) <= 160 and not d.endswith(("...", "…")), (t, d)
            titulos.add(t); descs.add(d)
    assert len(titulos) == len(descs) and len(titulos) > 100


# ---------------------------------------------------------------------------
# Histórico de taxas, comparador com evolução e dados abertos
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_dados_abertos_so_tem_linhas_do_bacen_e_batem_com_o_historico():
    import csv
    from historico_taxas import ler_historico
    from bancos import nome_exibicao
    hist = ler_historico()
    assert hist, "historico_taxas.csv vazio"
    assert {r["banco"] for r in hist} <= {"Caixa", "Banco do Brasil", "Santander", "Itau", "Bradesco", "Banco Inter", "Sicredi", "Sicoob", "Banrisul"}
    with open(os.path.join(PASTA_SAIDA, "dados", "taxas-financiamento-imobiliario.csv"), encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert len(linhas) == len(hist)
    nomes = {l["instituicao"] for l in linhas}
    assert "BRB" not in nomes and "Poupex" not in nomes  # taxa estimada, não é dado do BACEN
    assert all(2.0 <= float(l["taxa_juros_aa_pct"]) <= 40.0 for l in linhas)
    for nome in ("taxas-financiamento-imobiliario.json", "datapackage.json", "README.md"):
        assert os.path.isfile(os.path.join(PASTA_SAIDA, "dados", nome)), nome


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_pagina_dados_abertos_tem_schema_dataset_e_esta_no_sitemap():
    import json
    html = open(os.path.join(PASTA_SAIDA, "dados-abertos.html"), encoding="utf-8").read()
    blocos = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S)]
    ds = [b for b in blocos if b.get("@type") == "Dataset"]
    assert ds and ds[0]["license"] and ds[0]["distribution"] and ds[0]["temporalCoverage"]
    sitemap = open(os.path.join(PASTA_SAIDA, "sitemap.xml"), encoding="utf-8").read()
    assert "/dados-abertos</loc>" in sitemap


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_comparador_tem_mes_no_titulo_evolucao_e_faq_com_numeros():
    html = open(os.path.join(PASTA_SAIDA, "comparador-bancos.html"), encoding="utf-8").read()
    titulo = re.search(r"<title>(.*?)</title>", html).group(1)
    assert len(titulo) <= 60 and re.search(r"[a-z]{3}/\d{4}", titulo), titulo
    assert "Como as taxas evoluíram" in html
    assert "maior queda na taxa média contratada" in html


def test_resumo_historico_calcula_variacao_e_extremos():
    from gerador import resumo_historico
    h = []
    for i, (mes, a, b) in enumerate([("2026-01-01", 10.0, 12.0), ("2026-02-01", 9.5, 12.5)]):
        h += [{"inicio_periodo": mes, "fim_periodo": mes, "banco": "Caixa", "taxa_aa": a},
              {"inicio_periodo": mes, "fim_periodo": mes, "banco": "Itau", "taxa_aa": b}]
    r = resumo_historico(h)
    assert r["maior_queda"]["banco"] == "Caixa" and r["maior_queda"]["variacao"] == pytest.approx(-0.5)
    assert r["maior_alta"]["banco"] == "Itau" and r["maior_alta"]["variacao"] == pytest.approx(0.5)
    assert resumo_historico(h[:2]) is None  # um mês só: sem evolução


# ---------------------------------------------------------------------------
# Simulador incorporável, página "como incorporar" e imprensa
# ---------------------------------------------------------------------------

def _bloco_calc_do_embed():
    html = open(os.path.join(PASTA_SAIDA, "embed.html"), encoding="utf-8").read()
    m = re.search(r"// <calc>(.*?)// </calc>", html, re.S)
    assert m, "bloco <calc> não encontrado no embed.html"
    return m.group(1)


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_calculo_do_embed_bate_com_o_calculo_do_site():
    """A calculadora JS do /embed tem de dar os mesmos números que o motor Python do site."""
    import json
    import shutil
    import subprocess
    from gerador import calcular_sac_price
    if not shutil.which("node"):
        pytest.skip("node não instalado")
    casos = [(400_000, 360, 11.45), (250_000, 120, 12.30), (900_000, 420, 14.51), (150_000, 180, 9.56)]
    js = _bloco_calc_do_embed() + "\nconst casos=" + json.dumps(casos) + ";\nconsole.log(JSON.stringify(casos.map(c=>calcularFinanciamento(c[0],c[1],c[2]))));"
    saida = subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout
    for (fin, meses, taxa), r in zip(casos, json.loads(saida)):
        py = calcular_sac_price(fin, meses, taxa)
        assert r["p1"] == pytest.approx(py["p1_sac"], rel=1e-9)
        assert r["pU"] == pytest.approx(py["pU_sac"], rel=1e-9)
        assert r["price"] == pytest.approx(py["p1_price"], rel=1e-9)
        assert r["jurosSac"] == pytest.approx(py["total_sac"] - fin, rel=1e-6)
        assert r["jurosPrice"] == pytest.approx(py["total_price"] - fin, rel=1e-6)


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_embed_e_noindex_tem_canonical_e_headers_liberam_iframe_so_nele():
    html = open(os.path.join(PASTA_SAIDA, "embed.html"), encoding="utf-8").read()
    assert 'name="robots" content="noindex,follow"' in html
    assert 'rel="canonical" href="https://simulador.datalabglobal.com/incorporar"' in html
    assert "Datalab Global" in html and "https://simulador.datalabglobal.com/" in html  # link de crédito
    headers = open(os.path.join(PASTA_SAIDA, "_headers"), encoding="utf-8").read()
    bloco_embed = headers.split("\n/embed\n", 1)[1].split("\n\n", 1)[0]
    assert "frame-ancestors *" in bloco_embed and "! X-Frame-Options" in bloco_embed
    bloco_global = headers.split("/*\n", 1)[1].split("\n\n", 1)[0]
    assert "X-Frame-Options: DENY" in bloco_global and "frame-ancestors 'none'" in bloco_global
    sitemap = open(os.path.join(PASTA_SAIDA, "sitemap.xml"), encoding="utf-8").read()
    assert "/embed<" not in sitemap and "/incorporar</loc>" in sitemap and "/imprensa</loc>" in sitemap


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_imprensa_tem_numeros_calculados_e_incorporar_tem_codigo_e_iframe():
    imp = open(os.path.join(PASTA_SAIDA, "imprensa.html"), encoding="utf-8").read()
    assert "Números para citar" in imp and "R$ 500 mil em 30 anos" in imp and "CNPJ 63.998.502/0001-73" in imp
    assert re.search(r"taxa média contratada no financiamento imobiliário foi de \d+,\d{2}% ao ano", imp)
    inc = open(os.path.join(PASTA_SAIDA, "incorporar.html"), encoding="utf-8").read()
    assert "&lt;iframe src=&quot;" not in inc  # o código fica escapado no textarea
    assert "&lt;iframe src=" in inc and 'src="embed"' in inc and "Simulador por" in inc


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_cada_guia_recebe_varios_links_contextuais_e_paginas_novas_sao_alcancaveis():
    """Auditoria de links internos (29/out/2026): cada guia recebia só 1 link e
    /incorporar e /imprensa eram inalcançáveis a partir da home."""
    from gerador import ARTIGOS_APRENDA
    textos = {n: open(os.path.join(PASTA_SAIDA, n), encoding="utf-8").read() for n in os.listdir(PASTA_SAIDA) if n.endswith(".html")}
    for art in ARTIGOS_APRENDA:
        recebidos = sum(1 for n, t in textos.items() if n != art["slug"] + ".html" and f'href="{art["slug"]}"' in t)
        assert recebidos >= 20, (art["slug"], recebidos)
    for destino in ("incorporar", "imprensa"):
        assert f'href="{destino}"' in textos["index.html"], destino  # rodapé da home
