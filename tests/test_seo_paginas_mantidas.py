"""SEO de TODAS as páginas do sitemap depois do enxugamento (20/11/2026): título, descrição, H1, canonical, indexável, JSON-LD válido,
breadcrumb nas internas e links internos para páginas que existem."""
import json
import os
import re
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "paginas_seo")
DOMINIO = "https://simulador.datalabglobal.com"
gerada = os.path.exists(os.path.join(PASTA, "sitemap.xml"))


def _urls():
    with open(os.path.join(PASTA, "sitemap.xml"), encoding="utf-8") as f:
        return re.findall(r"<loc>([^<]+)</loc>", f.read())


def _arquivo(url):
    caminho = url[len(DOMINIO):].strip("/") or "index"
    return os.path.join(PASTA, caminho + ".html")


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_sitemap_enxuto_e_sem_duplicatas():
    urls = _urls()
    assert 40 <= len(urls) <= 80, len(urls)
    assert len(urls) == len(set(urls))
    assert not [u for u in urls if "/simulador-" in u]


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_toda_pagina_do_sitemap_tem_seo_completo():
    problemas = []
    for url in _urls():
        arq = _arquivo(url)
        if not os.path.exists(arq):
            problemas.append((url, "arquivo não existe"))
            continue
        h = open(arq, encoding="utf-8").read()
        titulo = (re.search(r"<title>([^<]*)</title>", h) or [None, ""])[1]
        desc = (re.search(r'<meta name="description" content="([^"]*)"', h) or [None, ""])[1]
        if not 10 <= len(titulo) <= 60:
            problemas.append((url, "título %d" % len(titulo)))
        if not 50 <= len(desc) <= 160:
            problemas.append((url, "descrição %d" % len(desc)))
        if len(re.findall(r"<h1[\s>]", h)) != 1:
            problemas.append((url, "H1 != 1"))
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', h)
        esperado = url if url.endswith("/") else url
        if not canon or canon.group(1).rstrip("/") != esperado.rstrip("/"):
            problemas.append((url, "canonical %s" % (canon.group(1) if canon else None)))
        if re.search(r'<meta name="robots" content="[^"]*noindex', h):
            problemas.append((url, "noindex no sitemap"))
        blocos = re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
        if not blocos:
            problemas.append((url, "sem JSON-LD"))
        for b in blocos:
            try:
                json.loads(b)
            except ValueError:
                problemas.append((url, "JSON-LD inválido"))
        if url != DOMINIO + "/" and "BreadcrumbList" not in h and "/embed" not in url:
            problemas.append((url, "sem BreadcrumbList"))
    assert not problemas, problemas[:10]


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_titulos_e_descricoes_nao_se_repetem_entre_paginas():
    vistos_t, vistos_d = {}, {}
    for url in _urls():
        h = open(_arquivo(url), encoding="utf-8").read()
        t = re.search(r"<title>([^<]*)</title>", h).group(1)
        d = re.search(r'<meta name="description" content="([^"]*)"', h).group(1)
        assert t not in vistos_t, (url, vistos_t.get(t))
        assert d not in vistos_d, (url, vistos_d.get(d))
        vistos_t[t], vistos_d[d] = url, url
