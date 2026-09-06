"""
Validação de integridade das páginas HTML geradas: 100% dos links
internos resolvem, 100% dos blocos JSON-LD são JSON válido, HTML sem
tags desbalanceadas, domínio/URL sem ".html" em canonical/sitemap/
links (achado real de 06/set/2026 — ver commit "URLs públicas sem
.html"), e a estrutura de erro (404.html) existe. Espelha
tests/test_paginas_geradas.py do projeto irmão (pseo-simulador-veiculo),
que tinha essa rede de segurança e este projeto nunca teve.

Depende de 'paginas_seo/' já ter sido gerado (python gerador.py). Não
roda por padrão se a pasta não existir (skip), pra não quebrar CI num
checkout limpo sem build.
"""
import html.parser
import json
import os
import re

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_SAIDA = os.path.join(RAIZ, "paginas_seo")
DOMINIO_ESPERADO = "https://simulador.datalabglobal.com"

pytestmark = pytest.mark.skipif(not os.path.isdir(PASTA_SAIDA), reason="paginas_seo/ não gerada — rode python gerador.py antes")


def _arquivos_html():
    return sorted(f for f in os.listdir(PASTA_SAIDA) if f.endswith(".html"))


def _slugs_validos():
    """Slugs sem a extensão .html — é assim que toda URL pública (canonical,
    sitemap, href) deveria referenciar uma página, desde a migração de
    URL de 06/set/2026. index.html vira "" (raiz)."""
    slugs = set()
    for nome in _arquivos_html():
        base = nome[:-5]  # remove ".html"
        slugs.add("" if base == "index" else base)
    return slugs


class VerificadorBalanceamento(html.parser.HTMLParser):
    """Confere que toda tag aberta (não voidelement) tem seu fechamento
    correspondente, na ordem certa."""
    VOID = {"meta", "link", "img", "br", "hr", "input", "area", "base", "col", "embed", "source", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.pilha = []
        self.erros = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.pilha.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.pilha or self.pilha[-1] != tag:
            self.erros.append(f"fechamento inesperado de </{tag}> (topo da pilha: {self.pilha[-1] if self.pilha else 'vazio'})")
            return
        self.pilha.pop()


def test_todo_link_interno_resolve_para_pagina_existente():
    """href="slug" (sem .html) precisa bater com um arquivo real slug.html
    no disco — ou ser "/" (raiz), "styles.css", "logo.svg", "sitemap.xml",
    externo (http/https), ou um dos arquivos estáticos conhecidos."""
    slugs_validos = _slugs_validos()
    arquivos_estaticos = {"styles.css", "logo.svg", "sitemap.xml", "robots.txt", "llms.txt", "/", "404.html"}
    faltando = []
    for nome_arquivo in _arquivos_html():
        with open(os.path.join(PASTA_SAIDA, nome_arquivo), encoding="utf-8") as f:
            # Remove os blocos <script>: o JS ao vivo monta HTML via
            # template literal (`href="${hrefFinanciaTudo}"`), e isso não
            # é um atributo href real do DOM estático — é string dentro
            # de código JS, o regex abaixo pegaria como falso-positivo.
            conteudo = re.sub(r'<script\b[^>]*>.*?</script>', '', f.read(), flags=re.DOTALL)
        for href in re.findall(r'href="([^"]+)"', conteudo):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            href_normalizado = href.lstrip("/")  # "/comparador-bancos" == "comparador-bancos"
            if href in arquivos_estaticos or href_normalizado in slugs_validos or href in slugs_validos:
                continue
            faltando.append(f"{nome_arquivo} -> {href}")
    assert not faltando, f"{len(faltando)} link(s) interno(s) quebrado(s): {faltando[:20]}"


def test_nenhum_html_sobrando_em_url_publica():
    """Achado real (06/set/2026): canonical/sitemap/links com '.html'
    causavam 1,49 mil páginas em 'Página com redirecionamento' no Google
    Search Console (Cloudflare Pages remove a extensão via 308, e o
    canonical apontava pra versão que redireciona). Trava de regressão
    pra essa classe específica de bug nunca voltar."""
    problemas = []
    for nome_arquivo in _arquivos_html():
        with open(os.path.join(PASTA_SAIDA, nome_arquivo), encoding="utf-8") as f:
            conteudo = f.read()
        m = re.search(r'rel="canonical" href="([^"]+)"', conteudo)
        if m and m.group(1).endswith(".html"):
            problemas.append(f"{nome_arquivo}: canonical com .html ({m.group(1)})")
        for href in re.findall(r'href="([^"]+\.html)"', conteudo):
            problemas.append(f"{nome_arquivo}: link interno com .html ({href})")
    assert not problemas, f"{len(problemas)} URL(s) pública(s) ainda com .html: {problemas[:15]}"


def test_todo_bloco_json_ld_e_json_valido():
    invalidos = []
    for nome_arquivo in _arquivos_html():
        with open(os.path.join(PASTA_SAIDA, nome_arquivo), encoding="utf-8") as f:
            conteudo = f.read()
        for bloco in re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', conteudo, re.DOTALL):
            try:
                json.loads(bloco)
            except json.JSONDecodeError as e:
                invalidos.append(f"{nome_arquivo}: {e}")
    assert not invalidos, f"{len(invalidos)} bloco(s) JSON-LD inválido(s): {invalidos[:10]}"


def test_html_sem_tags_desbalanceadas():
    quebradas = {}
    for nome_arquivo in _arquivos_html():
        with open(os.path.join(PASTA_SAIDA, nome_arquivo), encoding="utf-8") as f:
            conteudo = f.read()
        v = VerificadorBalanceamento()
        v.feed(conteudo)
        if v.erros or v.pilha:
            quebradas[nome_arquivo] = v.erros + [f"não fechada: <{t}>" for t in v.pilha]
    assert not quebradas, f"{len(quebradas)} página(s) com HTML desbalanceado: {dict(list(quebradas.items())[:5])}"


def test_dominio_correto_em_todas_as_paginas():
    """Trava a lição #1 original do projeto: canonical precisa bater com
    simulador.datalabglobal.com em toda página — nunca o domínio raiz
    (datalabglobal.com), que já causou uma queda de indexação real
    antes desta sessão."""
    problemas = []
    for nome_arquivo in _arquivos_html():
        if nome_arquivo == "404.html":
            continue  # página de erro, de propósito sem canonical (tem noindex)
        with open(os.path.join(PASTA_SAIDA, nome_arquivo), encoding="utf-8") as f:
            conteudo = f.read()
        m = re.search(r'rel="canonical" href="([^"]+)"', conteudo)
        if not m or not m.group(1).startswith(DOMINIO_ESPERADO):
            problemas.append(f"{nome_arquivo}: canonical={m.group(1) if m else None}")
    assert not problemas, f"{len(problemas)} página(s) com domínio incorreto: {problemas[:10]}"


def test_sitemap_lista_todas_as_paginas_e_sem_html():
    with open(os.path.join(PASTA_SAIDA, "sitemap.xml"), encoding="utf-8") as f:
        sitemap = f.read()
    assert ".html</loc>" not in sitemap, "sitemap ainda tem alguma URL terminando em .html"
    urls_no_sitemap = set(re.findall(r"<loc>(.*?)</loc>", sitemap))
    esperadas = {f"{DOMINIO_ESPERADO}/"} | {f"{DOMINIO_ESPERADO}/{s}" for s in _slugs_validos() if s and s != "404"}
    faltando = esperadas - urls_no_sitemap
    assert not faltando, f"{len(faltando)} página(s) gerada(s) mas ausente(s) do sitemap: {list(faltando)[:10]}"


def test_arquivos_de_infraestrutura_existem():
    for nome in ("sitemap.xml", "robots.txt", "llms.txt", "_headers", "_redirects", "404.html", "styles.css", "logo.svg"):
        assert os.path.isfile(os.path.join(PASTA_SAIDA, nome)), f"{nome} não existe em paginas_seo/"


def test_pagina_404_tem_noindex():
    with open(os.path.join(PASTA_SAIDA, "404.html"), encoding="utf-8") as f:
        conteudo = f.read()
    assert 'name="robots" content="noindex"' in conteudo, "404.html sem noindex — Google poderia tentar indexar a página de erro"
