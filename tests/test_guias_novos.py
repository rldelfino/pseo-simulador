"""Guias novos de /aprenda (31/out/2026): existem, estão no sitemap e no hub,
citam fonte oficial com link https, não têm AdSense e os exemplos numéricos
batem com o cálculo do simulador."""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gerador
import guias_novos

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "paginas_seo")
gerada = os.path.isdir(PASTA)
SLUGS = [g["slug"] for g in guias_novos.montar_guias(gerador.calcular_sac_price, gerador.formatar_reais)]


def _ler(nome):
    return open(os.path.join(PASTA, nome), encoding="utf-8").read()


def test_seis_guias_com_campos_e_titulos_dentro_do_limite():
    guias = guias_novos.montar_guias(gerador.calcular_sac_price, gerador.formatar_reais)
    assert len(guias) == 6 and len(set(SLUGS)) == 6
    for g in guias:
        assert {"slug", "titulo_h1", "titulo_pagina", "meta_description", "resumo_card", "corpo_html", "cta_href", "cta_texto"} <= set(g)
        assert len(g["titulo_pagina"]) <= 60 and len(g["meta_description"]) <= 160
        assert len(re.sub(r"<[^>]+>", " ", g["corpo_html"]).split()) >= 550


def test_exemplo_da_portabilidade_bate_com_o_calculo():
    g = next(x for x in guias_novos.montar_guias(gerador.calcular_sac_price, gerador.formatar_reais) if "portabilidade" in x["slug"])
    a, n = gerador.calcular_sac_price(300_000, 240, 12.5), gerador.calcular_sac_price(300_000, 240, 10.5)
    assert gerador.formatar_reais(a["p1_sac"]) in g["corpo_html"] and gerador.formatar_reais(n["p1_sac"]) in g["corpo_html"]
    assert gerador.formatar_reais((a["total_sac"] - 300_000) - (n["total_sac"] - 300_000)) in g["corpo_html"]


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
@pytest.mark.parametrize("slug", SLUGS)
def test_guia_publicado_no_sitemap_hub_e_com_fonte_oficial(slug):
    html = _ler(slug + ".html")
    assert f"/{slug}</loc>" in _ler("sitemap.xml") and f'href="{slug}"' in _ler("aprenda.html")
    assert "adsbygoogle" not in html and 'name="robots" content="noindex' not in html
    assert "Fontes" in html and "Conferido em" in html or "conferidas em" in html
    oficiais = re.findall(r'href="(https://[^"]*(?:gov\.br|fgv\.br)[^"]*)"', html)
    assert len(oficiais) >= 2, slug
    assert f'<link rel="canonical" href="https://simulador.datalabglobal.com/{slug}"' in html


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_guias_recebem_links_das_paginas_de_comparacao():
    comp = _ler("financiamento-imobiliario-500-mil-30-anos.html")
    for slug in SLUGS:
        assert f'href="{slug}"' in comp
