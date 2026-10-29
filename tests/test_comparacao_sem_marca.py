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
