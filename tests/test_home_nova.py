"""Home nova (simulador no estilo do 006): conta de referência, JS x Python, HTML gerado, CSP e arquivo do Yandex.

Os testes que leem paginas_seo/ precisam do site gerado (python gerador.py); os de JS precisam do Node.
"""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import calculo_home as C  # noqa: E402
import gerador  # noqa: E402
import servidor_local  # noqa: E402

PASTA = os.path.join(RAIZ, "paginas_seo")
INDEX = os.path.join(PASTA, "index.html")
gerada = os.path.exists(INDEX) and os.path.exists(os.path.join(PASTA, "home.js"))
precisa_node = pytest.mark.skipif(not shutil.which("node"), reason="node não instalado")


def _home():
    with open(INDEX, encoding="utf-8") as f:
        return f.read()


# ---------------- conta de referência ----------------

CASOS = [(500_000, 100_000, 30, 12.22, "sac"), (500_000, 100_000, 30, 12.22, "price"), (800_000, 160_000, 35, 14.42, "sac"),
         (250_000, 50_000, 10, 10.49, "price"), (1_200_000, 240_000, 20, 12.97, "sac"), (150_000, 30_000, 5, 11.97, "price")]


@pytest.mark.parametrize("imovel, entrada, anos, aa, sis", CASOS)
def test_conta_da_home_bate_com_o_motor_do_site(imovel, entrada, anos, aa, sis):
    r = C.simular(imovel, entrada, anos, aa, sis)
    ref = gerador.calcular_sac_price(imovel - entrada, anos * 12, aa, imovel)
    assert r["p1"] == pytest.approx(ref["p1_" + sis], rel=1e-12)
    assert r["pu"] == pytest.approx(ref["pU_" + sis], rel=1e-12)
    assert r["total"] == pytest.approx(ref["total_" + sis], rel=1e-12)
    assert r["cet"] == ref["cet_" + sis]
    assert r["renda"] == ref["renda_sugerida"] or sis == "price"  # a renda do site é sempre pela 1ª parcela do SAC


def test_taxa_nominal_divide_por_12_e_efetiva_compoe():
    assert C.taxa_mensal(12.0, nominal=True) == pytest.approx(0.01)
    assert (1 + C.taxa_mensal(12.0)) ** 12 == pytest.approx(1.12, rel=1e-12)


def test_amortizacao_anual_fecha_com_o_total_e_o_saldo_zera():
    r = C.simular(500_000, 100_000, 30, 12.22, "sac")
    linhas = C.amortizacao_anual(r["financiado"], r["i"], r["meses"], "sac")
    assert len(linhas) == 30
    assert sum(x["juros"] for x in linhas) == pytest.approx(r["juros"], rel=1e-9)
    assert sum(x["amortizacao"] for x in linhas) == pytest.approx(r["financiado"], rel=1e-9)
    assert linhas[-1]["saldo"] == pytest.approx(0, abs=1e-6)


def test_pagar_a_mais_reduz_juros_e_prazo():
    r = C.simular(500_000, 100_000, 30, 12.22, "price")
    base = C.amortizar_antes(r["financiado"], r["i"], r["meses"], "price", 0, 0, 0, "prazo")
    assert base["meses"] == 360
    assert base["juros"] == pytest.approx(r["juros"], rel=1e-9)
    com = C.amortizar_antes(r["financiado"], r["i"], r["meses"], "price", 500, 0, 0, "prazo")
    assert com["meses"] < 360 and com["juros"] < base["juros"]
    cedo = C.amortizar_antes(r["financiado"], r["i"], r["meses"], "sac", 0, 20_000, 0, "prazo")
    tarde = C.amortizar_antes(r["financiado"], r["i"], r["meses"], "sac", 0, 20_000, 120, "prazo")
    sem = C.amortizar_antes(r["financiado"], r["i"], r["meses"], "sac", 0, 0, 0, "prazo")
    assert sem["juros"] - cedo["juros"] > sem["juros"] - tarde["juros"] > 0  # quanto mais cedo, maior a economia


@precisa_node
def test_js_da_home_bate_com_o_python():
    js = os.path.join(RAIZ, "src", "calculo_home.js").replace("\\", "/")
    casos = [list(c) for c in CASOS]
    code = ("const H=require(%s);const c=%s;const out=c.map(x=>{const r=H.simular(x[0],x[1],x[2],x[3],x[4]);"
            "const l=H.amortizacaoAnual(r.financiado,r.i,r.meses,x[4]);const a=H.amortizarAntes(r.financiado,r.i,r.meses,x[4],500,20000,12,'prazo');"
            "const b=H.amortizarAntes(r.financiado,r.i,r.meses,x[4],0,20000,12,'parcela');"
            "return {p1:r.p1,pu:r.pu,total:r.total,juros:r.juros,cet:r.cet,renda:r.renda,j1:l[0].juros,a:a,b:b};});console.log(JSON.stringify(out));"
            % (json.dumps(js), json.dumps(casos)))
    res = json.loads(subprocess.run(["node", "-e", code], capture_output=True, text=True, check=True).stdout)
    for (imovel, entrada, anos, aa, sis), j in zip(CASOS, res):
        r = C.simular(imovel, entrada, anos, aa, sis)
        for k in ("p1", "pu", "total", "juros"):
            assert j[k] == pytest.approx(r[k], rel=1e-12), k
        assert j["cet"] == r["cet"] and j["renda"] == r["renda"]
        assert j["j1"] == pytest.approx(C.amortizacao_anual(r["financiado"], r["i"], r["meses"], sis)[0]["juros"], rel=1e-12)
        pa = C.amortizar_antes(r["financiado"], r["i"], r["meses"], sis, 500, 20000, 12, "prazo")
        assert j["a"]["meses"] == pa["meses"] and j["a"]["juros"] == pytest.approx(pa["juros"], rel=1e-9)
        pb = C.amortizar_antes(r["financiado"], r["i"], r["meses"], sis, 0, 20000, 12, "parcela")
        assert j["b"]["meses"] == pb["meses"] and j["b"]["juros"] == pytest.approx(pb["juros"], rel=1e-9)


# ---------------- HTML gerado ----------------

@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_home_sem_style_nem_script_inline():
    h = _home()
    assert not re.search(r"<[a-z][^>]*\sstyle=", h), "atributo style: a CSP da home não permite"
    assert "<style" not in h
    for m in re.finditer(r"<script([^>]*)>", h):
        attrs = m.group(1)
        assert "src=" in attrs or "application/ld+json" in attrs or "application/json" in attrs, "script inline: " + attrs
    assert not re.search(r"\son(click|load|error|change|input)=", h)


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_home_nao_cita_remuneracao_nem_nome_do_parceiro():
    h = _home().lower()
    for proibido in ("comiss", "remunerad", "financia tudo", "financiatudo", "financia-tudo"):
        assert proibido not in h, proibido


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_home_seo_basico():
    h = _home()
    titulo = re.search(r"<title>([^<]+)</title>", h).group(1)
    assert len(titulo) <= 60, titulo
    desc = re.search(r'<meta name="description" content="([^"]+)"', h).group(1)
    assert 80 <= len(desc) <= 160, len(desc)
    assert h.count("<h1") == 1 and "Simulador de financiamento" in h
    assert '<link rel="canonical" href="https://simulador.datalabglobal.com/">' in h
    assert '"@type": "WebApplication"' in h and '"@type": "FAQPage"' in h
    # o FAQ do JSON-LD é o mesmo que aparece na página
    for q, a in re.findall(r'"name": "([^"]+)", "acceptedAnswer": \{"@type": "Answer", "text": "([^"]+)"', h):
        assert q in h.replace("&#x27;", "'") or q.replace("'", "&#x27;") in h


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_home_tem_valores_iniciais_iguais_a_conta_de_referencia():
    h = _home()
    dados = json.loads(re.search(r'<script type="application/json" id="dados-home">(.*?)</script>', h, re.S).group(1))
    assert len(dados["bancos"]) == len(gerador.BANCOS)
    r = C.simular(dados["padrao"]["imovel"], dados["padrao"]["entrada"], dados["padrao"]["anos"], dados["mercado"]["t"], dados["padrao"]["sistema"])
    assert 'id="r-parcela">R$ %s<' % format(int(r["p1"] + 0.5), ",").replace(",", ".") in h
    assert 'id="r-total">R$ %s<' % format(int(r["total"] + 0.5), ",").replace(",", ".") in h
    assert 'id="r-cet">%s%%<' % format(r["cet"], ".2f").replace(".", ",") in h


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_taxas_da_home_sao_as_do_dados_csv():
    h = _home()
    dados = json.loads(re.search(r'<script type="application/json" id="dados-home">(.*?)</script>', h, re.S).group(1))
    import csv
    with open(os.path.join(RAIZ, "dados.csv"), encoding="utf-8") as f:
        csv_taxas = {}
        for r in csv.DictReader(f, delimiter=";"):
            csv_taxas.setdefault(r["banco"], float(r["taxa"].replace(",", ".")))
    for b in dados["bancos"]:
        assert b["t"] == pytest.approx(csv_taxas[b["k"]], abs=0.005), b["k"]


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_rodape_da_home_liga_os_irmaos_e_o_hub():
    h = _home()
    for url in ("https://homeequity.datalabglobal.com/", "https://autoequity.datalabglobal.com/", "https://condominio.datalabglobal.com/",
                "https://veiculos.datalabglobal.com/", "https://emprestimo.datalabglobal.com/", "https://www.datalabglobal.com/"):
        assert 'href="%s"' % url in h, url


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_botao_do_parceiro_so_dentro_da_tela_de_confirmacao():
    h = _home()
    assert h.count(gerador.LINK_FINANCIA_TUDO) == 1
    dlg = re.search(r"<dialog.*?</dialog>", h, re.S).group(0)
    assert gerador.LINK_FINANCIA_TUDO in dlg and 'rel="noopener sponsored"' in dlg


# ---------------- cabeçalhos ----------------

def test_csp_da_home_e_estrita_e_sem_unsafe_inline():
    regras = servidor_local.ler_regras()
    cab = servidor_local.cabecalhos_para("/", regras)
    csp = cab["Content-Security-Policy"]
    assert "unsafe-inline" not in csp and "script-src 'self' https://cloud.umami.is" in csp and "style-src 'self'" in csp
    assert "," not in csp.split("default-src")[0]  # só uma política: o "!" tirou a herdada de /*
    for nome in ("X-Frame-Options", "X-Content-Type-Options", "Strict-Transport-Security", "Referrer-Policy"):
        assert nome in cab, nome
    # as demais páginas seguem com a CSP antiga (usam Tailwind e script inline)
    outra = servidor_local.cabecalhos_para("/banco-caixa", regras)["Content-Security-Policy"]
    assert "unsafe-inline" in outra


# ---------------- Yandex ----------------

def test_arquivo_de_verificacao_do_yandex():
    caminho = os.path.join(PASTA, "yandex_90c15c3be650b0ed.html")
    with open(caminho, encoding="utf-8", newline="") as f:
        conteudo = f.read().replace("\r\n", "\n")
    assert conteudo == ('<html>\n<head>\n<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n</head>\n'
                        '<body>Verification: 90c15c3be650b0ed</body>\n</html>')


def test_yandex_nao_esta_no_gitignore():
    r = subprocess.run(["git", "check-ignore", "-q", "paginas_seo/yandex_90c15c3be650b0ed.html"], cwd=RAIZ)
    assert r.returncode == 1  # 1 = não ignorado


# ---------------- marca padrão (21/11/2026) ----------------

HUB = "https://www.datalabglobal.com/"


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
@pytest.mark.parametrize("nome", ["index.html", "banco-caixa.html", "comparador-bancos.html", "aprenda-sac-x-price.html", "sobre.html", "metodologia.html"])
def test_marca_leva_ao_site_principal_e_imovel_leva_a_home_do_simulador(nome):
    with open(os.path.join(PASTA, nome), encoding="utf-8") as f:
        h = f.read()
    m = re.search(r'<a href="https://www\.datalabglobal\.com/"[^>]*aria-label="Datalab Global, site principal"[^>]*>', h)
    assert m, "logo sem link para o site principal em " + nome
    p = re.search(r'<a href="/"[^>]*aria-label="Simulador de financiamento imobiliário, página inicial"[^>]*>Imóvel</a>', h)
    assert p, "rótulo Imóvel sem link para a home em " + nome
    # nenhum link do logo para a home do simulador
    assert not re.search(r'<a href="/"[^>]*>\s*<img src="logo-full.png"', h)


def test_logo_e_exatamente_o_do_006():
    import logo
    caminho = os.path.join(os.path.dirname(RAIZ), "006-pseo-simulador-homeequity", "layout.py")
    if not os.path.exists(caminho):
        pytest.skip("projeto 006 fora da pasta")
    with open(caminho, encoding="utf-8") as f:
        origem = re.search(r'^LOGO = """(.*?)"""', f.read(), re.S | re.M).group(1)
    assert logo.LOGO == origem


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_home_usa_a_marca_padrao_com_wordmark_do_006():
    h = _home()
    assert h.count('<span class="wm"><b>Datalab</b><i>GLOBAL</i></span>') == 2  # cabeçalho e rodapé
    assert h.count('<span class="tile"><svg viewBox="0 0 44 44"') == 2
    assert 'class="prod"' in h
    assert ".prod{display:none}" not in open(os.path.join(PASTA, "home.css"), encoding="utf-8").read()  # visível no celular
