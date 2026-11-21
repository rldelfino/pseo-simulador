"""Teste de ponta a ponta da home no navegador (Chromium e WebKit, computador e celular), fora do CI.

Sobe o site gerado (paginas_seo/) com os cabeçalhos do _headers (servidor_local.py), bloqueia o Umami e o parceiro (nada sai para fora),
usa o simulador como uma pessoa usaria e confere os números contra calculo_home.py (a conta de referência, em Python).
Também confere: sem erro de console, sem rolagem lateral, CSP/HSTS/XFO/nosniff, links internos sem 404, tela de confirmação e link do parceiro.
Precisa do Playwright (python -m playwright install chromium webkit). Uso: python testar_navegador.py
"""
import json
import math
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright

import calculo_home as C
import gerador
import servidor_local

FALHAS = []
TOTAL = [0]


def confere(nome, cond, detalhe=""):
    TOTAL[0] += 1
    print(("OK     " if cond else "FALHOU ") + nome + ((" -> " + str(detalhe)) if (not cond or detalhe) else ""))
    if not cond:
        FALHAS.append(nome)


def numero(texto):
    return int(re.sub(r"[^\d]", "", texto))


def centavos(texto):
    return float(re.sub(r"[^\d,]", "", texto).replace(",", "."))


class Ref:
    """A mesma regra de limites do home.js, em Python, usando os dados que a própria página carrega."""

    def __init__(self, dados):
        self.D = dados

    def banco(self, k):
        if k == "mercado":
            return {"k": "mercado", "n": "Média dos bancos", **self.D["mercado"]}
        return next(b for b in self.D["bancos"] if b["k"] == k)

    def calc(self, imovel, entrada, anos, k, sistema, taxa_prop=0, nominal=False):
        b = self.banco(k)
        anos = min(max(anos, 5), b["p"] // 12)
        emin = math.ceil(imovel * (1 - b["l"]) / 1000) * 1000
        emax = math.floor(imovel * 0.9 / 1000) * 1000
        ent = min(max(entrada, emin), emax)
        aa = taxa_prop if 3 <= taxa_prop <= 40 else b["t"]
        r = C.simular(imovel, ent, anos, aa, sistema, nominal and 3 <= taxa_prop <= 40)
        r["entrada"] = ent
        r["anos"] = anos
        r["aa"] = aa
        return r


def ler_resultado(pg):
    return {"parcela": numero(pg.inner_text("#r-parcela")), "total": numero(pg.inner_text("#r-total")), "cet": centavos(pg.inner_text("#r-cet"))}


def bate(tag, nome, pg, r):
    got = ler_resultado(pg)
    ok = got["parcela"] == int(r["p1"] + 0.5) and got["total"] == int(r["total"] + 0.5) and abs(got["cet"] - r["cet"]) < 0.006
    confere(tag + nome, ok, "%s esperado parcela=%d total=%d cet=%.2f" % (got, int(r["p1"] + 0.5), int(r["total"] + 0.5), r["cet"]))


def rodar(nav, nome_nav, base, perfil):
    nome, opcoes = perfil
    ctx = nav.new_context(**opcoes)
    ctx.route("**/*umami*", lambda r_: r_.abort())
    ctx.route("**/proposta.api.br/**", lambda r_: r_.fulfill(status=200, content_type="text/html", body="<html><body>parceiro (teste)</body></html>"))
    pg = ctx.new_page()
    erros = []
    pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: erros.append("PAGEERROR " + str(e)))
    pg.add_init_script("window.__ev=[];window.umami={track:function(n,d){window.__ev.push([n,d]);}}")
    tag = nome_nav + "/" + nome + ": "

    resp = pg.goto(base + "/")
    cab = {k.lower(): v for k, v in resp.headers.items()}
    pg.wait_for_selector("#bk-lista li")
    D = json.loads(pg.evaluate("document.getElementById('dados-home').textContent"))
    ref = Ref(D)
    P = D["padrao"]

    confere(tag + "status 200", resp.status == 200)
    csp = cab.get("content-security-policy", "")
    confere(tag + "CSP estrita (sem unsafe-inline, uma política só)", bool(csp) and "unsafe-inline" not in csp and "script-src 'self' https://cloud.umami.is" in csp, csp[:120])
    confere(tag + "cabeçalhos de segurança", all(k in cab for k in ("x-frame-options", "x-content-type-options", "strict-transport-security", "referrer-policy")) and cab.get("x-frame-options") == "DENY" and cab.get("x-content-type-options") == "nosniff", {k: cab.get(k) for k in ("x-frame-options", "x-content-type-options", "strict-transport-security")})
    confere(tag + "sem rolagem lateral ao abrir", pg.evaluate("document.documentElement.scrollWidth") <= pg.evaluate("window.innerWidth"))

    # estado inicial: o que está escrito no HTML tem de ser o que a conta de referência dá
    r0 = ref.calc(P["imovel"], P["entrada"], P["anos"], P["banco"], P["sistema"])
    bate(tag, "números iniciais", pg, r0)
    confere(tag + "11 bancos na lista", pg.locator("#bk-lista li").count() == len(D["bancos"]) == 11)
    cets = [centavos(t) for t in pg.locator("#bk-lista .bk-c b").all_inner_texts()]
    confere(tag + "lista ordenada pelo menor CET", cets == sorted(cets), cets)
    confere(tag + "números da faixa: renda", numero(pg.inner_text("#k-renda")) == r0["renda"], pg.inner_text("#k-renda"))
    confere(tag + "números da faixa: R$ 1 de crédito", abs(centavos(pg.inner_text("#k-juro1")) - round(r0["juros"] / r0["financiado"], 2)) < 0.006, pg.inner_text("#k-juro1"))

    # hub do banco -> home já preenchida (links que substituíram os da grade `simulador-*`, enxugamento de 20/11/2026)
    ph = ctx.new_page()
    ph.goto(base + "/banco-itau")
    href = ph.locator("a[href^='/?v=']").first.get_attribute("href")
    confere(tag + "hub do Itaú tem links para a home preenchida", ph.locator("a[href^='/?v=']").count() >= 4 and "b=Itau" in href, href)
    ph.locator("a[href^='/?v=']").first.click()
    ph.wait_for_selector("#banco-nome:has-text('Itaú')")
    q = dict(x.split("=") for x in href.split("?")[1].split("#")[0].replace("&amp;", "&").split("&"))
    rh = ref.calc(int(q["v"]), int(q["e"]), int(q["p"]), "Itau", "sac")
    bate(tag, "link do hub abre a simulação do banco (R$ %s, %s anos)" % (q["v"], q["p"]), ph, rh)
    confere(tag + "link do hub: banco certo no botão", ph.inner_text("#banco-nome") == "Itaú", ph.inner_text("#banco-nome"))
    ph.close()

    # valor do imóvel (a entrada sobe sozinha ao mínimo de 20%)
    pg.fill("#campo-imovel", "800.000"); pg.press("#campo-imovel", "Enter")
    r = ref.calc(800_000, 100_000, 30, "mercado", "sac")
    bate(tag, "imóvel R$ 800 mil (entrada ajustada ao mínimo)", pg, r)
    confere(tag + "aviso do ajuste da entrada", pg.is_visible("#msg-ajuste") and numero(pg.input_value("#campo-entrada")) == r["entrada"], pg.input_value("#campo-entrada"))
    pg.fill("#campo-entrada", "300.000"); pg.press("#campo-entrada", "Enter")
    r = ref.calc(800_000, 300_000, 30, "mercado", "sac")
    bate(tag, "entrada R$ 300 mil", pg, r)
    confere(tag + "percentual da entrada", "38%" in pg.inner_text("#entrada-pct"), pg.inner_text("#entrada-pct"))
    pg.evaluate("document.getElementById('campo-entrada').value=''")

    # prazo: lista suspensa, teclado e digitação
    confere(tag + "lista de prazos começa fechada", not pg.is_visible("#lista-prazo"))
    pg.click("#btn-prazo")
    confere(tag + "abre a lista de prazos (5 a 35 anos)", pg.is_visible("#lista-prazo") and pg.locator("#lista-prazo li:visible").count() == 31)
    pg.click("#prazo-op-20")
    r = ref.calc(800_000, 300_000, 20, "mercado", "sac")
    bate(tag, "prazo 20 anos pela lista", pg, r)
    confere(tag + "texto do prazo em meses", "240 meses" in pg.inner_text("#r-sub"), pg.inner_text("#r-sub"))
    pg.fill("#campo-prazo", "15"); pg.press("#campo-prazo", "Enter")
    bate(tag, "prazo 15 anos digitado", pg, ref.calc(800_000, 300_000, 15, "mercado", "sac"))
    pg.fill("#campo-prazo", "50"); pg.press("#campo-prazo", "Enter")
    confere(tag + "prazo fora da faixa é ajustado ao máximo", pg.input_value("#campo-prazo") == "35" and pg.is_visible("#msg-prazo"), pg.input_value("#campo-prazo"))
    pg.fill("#campo-prazo", "25"); pg.press("#campo-prazo", "Enter")

    # Price x SAC
    pg.click("label[for=sis-price]")
    bate(tag, "Price", pg, ref.calc(800_000, 300_000, 25, "mercado", "price"))
    confere(tag + "Price: sem linha da última parcela", not pg.is_visible("#r-ultima") and "1ª" not in pg.inner_text("#r-kicker"))
    pg.click("label[for=sis-sac]")
    r = ref.calc(800_000, 300_000, 25, "mercado", "sac")
    bate(tag, "SAC", pg, r)
    confere(tag + "SAC: mostra a última parcela", pg.is_visible("#r-ultima") and ("R$ %s" % format(int(r["pu"] + 0.5), ",").replace(",", ".")) in pg.inner_text("#r-ultima"), pg.inner_text("#r-ultima"))

    # banco: lista, teclado, limites do banco
    pg.click("#btn-banco")
    confere(tag + "lista de bancos abre com 12 opções (média + 11)", pg.is_visible("#lista-banco") and pg.locator("#lista-banco li").count() == 12)
    pg.click("#lista-banco li[data-k='Caixa']")
    bate(tag, "banco Caixa", pg, ref.calc(800_000, 300_000, 25, "Caixa", "sac"))
    confere(tag + "nome do banco no botão", pg.inner_text("#banco-nome") == "Caixa", pg.inner_text("#banco-nome"))
    pg.focus("#btn-banco")
    pg.keyboard.press("ArrowDown"); pg.keyboard.press("ArrowDown"); pg.keyboard.press("Enter")
    estado_k = pg.inner_text("#banco-nome")
    confere(tag + "teclado escolhe o banco (2 abaixo da Caixa)", estado_k != "Caixa", estado_k)
    pg.click("#btn-banco"); pg.click("#lista-banco li[data-k='Banrisul']")
    r = ref.calc(800_000, 300_000, 25, "Banrisul", "sac")
    bate(tag, "banco Banrisul (entrada mínima de 25%)", pg, r)
    pg.click("#btn-banco"); pg.click("#lista-banco li[data-k='Itau']")
    pg.fill("#campo-prazo", "35"); pg.press("#campo-prazo", "Enter")
    confere(tag + "Itaú: prazo máximo de 30 anos", pg.input_value("#campo-prazo") == "30", pg.input_value("#campo-prazo"))
    bate(tag, "Itaú 30 anos", pg, ref.calc(800_000, 300_000, 30, "Itau", "sac"))
    linha = pg.locator("#bk-lista li.us")
    confere(tag + "banco escolhido destacado na lista", linha.count() == 1 and "Itaú" in linha.inner_text(), linha.inner_text() if linha.count() else "")
    confere(tag + "cada banco leva ao hub dele", all(re.match(r"^/banco-[a-z-]+$", a) for a in pg.locator("#bk-lista a").evaluate_all("els=>els.map(e=>e.getAttribute('href'))")))

    # taxa de uma proposta (efetiva e nominal)
    pg.click("#det-taxa summary")
    pg.fill("#campo-taxa-prop", "10,99")
    pg.press("#campo-taxa-prop", "Enter")
    bate(tag, "taxa da proposta 10,99% efetiva", pg, ref.calc(800_000, 300_000, 30, "Itau", "sac", 10.99, False))
    pg.click("#ck-taxa-nominal")
    bate(tag, "taxa da proposta 10,99% nominal (÷ 12)", pg, ref.calc(800_000, 300_000, 30, "Itau", "sac", 10.99, True))
    pg.fill("#campo-taxa-prop", "1"); pg.press("#campo-taxa-prop", "Enter")
    confere(tag + "taxa fora de 3% a 40% volta à do banco", pg.locator("#msg-taxa-prop.warn").count() == 1)
    pg.fill("#campo-taxa-prop", ""); pg.press("#campo-taxa-prop", "Enter")
    pg.click("#ck-taxa-nominal")
    bate(tag, "sem taxa própria volta à do banco", pg, ref.calc(800_000, 300_000, 30, "Itau", "sac"))

    # pagar a mais
    r = ref.calc(800_000, 300_000, 30, "Itau", "sac")
    pg.click("#det-amsim summary")
    pg.wait_for_selector("#am-cartoes .amc")
    # o cartão do valor mensal: economia de juros = juros sem extra - juros com extra
    base_j = C.amortizar_antes(r["financiado"], r["i"], r["meses"], "sac", 0, 0, 12, "prazo")
    com_j = C.amortizar_antes(r["financiado"], r["i"], r["meses"], "sac", 500, 0, 0, "prazo")
    todos = pg.locator("#am-cartoes .amc .big").all_inner_texts()
    unico = C.amortizar_antes(r["financiado"], r["i"], r["meses"], "sac", 0, 20_000, 12, "prazo")
    esp = [int(base_j["juros"] - com_j["juros"] + 0.5), int(base_j["juros"] - unico["juros"] + 0.5)]
    confere(tag + "pagar a mais: economia mensal e única conferem com a conta", [numero(t) for t in todos[:1]] != [] and esp[0] in [numero(t) for t in todos] and esp[1] in [numero(t) for t in todos], "%s esperado %s" % (todos, esp))
    pg.fill("#campo-extra", "1.000"); pg.press("#campo-extra", "Enter")
    com2 = C.amortizar_antes(r["financiado"], r["i"], r["meses"], "sac", 1000, 0, 0, "prazo")
    confere(tag + "pagar a mais: R$ 1.000 por mês economiza mais que R$ 500", int(base_j["juros"] - com2["juros"] + 0.5) in [numero(t) for t in pg.locator("#am-cartoes .amc .big").all_inner_texts()])
    confere(tag + "gráfico anual desenhado (30 anos = 60 barras + linha)", pg.locator("#amort-graf rect").count() == 60 and pg.locator("#amort-graf polyline").count() == 1)
    pg.click("#det-amort summary")
    confere(tag + "tabela ano a ano: 30 linhas", pg.locator("#amort-corpo tr").count() == 30)

    # link da simulação e tela de confirmação
    pg.wait_for_timeout(700)
    url = pg.evaluate("window.location.href")
    confere(tag + "endereço guarda a simulação", all(x in url for x in ("v=800000", "e=300000", "p=30", "b=Itau", "s=sac")) and url.endswith("#simulador"), url)
    pg2 = ctx.new_page()
    pg2.goto(url)
    pg2.wait_for_selector("#bk-lista li")
    confere(tag + "abrir o link repete a simulação", ler_resultado(pg2) == ler_resultado(pg), "%s x %s" % (ler_resultado(pg2), ler_resultado(pg)))
    pg2.close()
    pg.click("#btn-copiar")
    pg.wait_for_selector("#msg-copiado:not(:empty)")
    confere(tag + "botão de copiar responde", len(pg.inner_text("#msg-copiado")) > 10, pg.inner_text("#msg-copiado"))

    confere(tag + "tela de confirmação começa fechada", not pg.is_visible("#dlg-confirma"))
    pg.click("#btn-cta")
    confere(tag + "botão do parceiro abre a tela de confirmação", pg.is_visible("#dlg-confirma"))
    confere(tag + "texto agnóstico sobre o parceiro", "parceiro de crédito" in pg.inner_text("#dlg-confirma") and not re.search(r"comiss|remunera|financia tudo", pg.inner_text("#dlg-confirma"), re.I))
    href = pg.get_attribute("#a-parceiro", "href")
    confere(tag + "link do parceiro é o do gerador", href == gerador.LINK_FINANCIA_TUDO, href)
    with ctx.expect_page() as nova:
        pg.click("#a-parceiro")
    confere(tag + "continuar abre o parceiro em outra aba", nova.value.url.rstrip("/").endswith("/f/ae4809fa-f818-4813-a93d-f0f6cb2f235c"), nova.value.url)
    nova.value.close()
    pg.keyboard.press("Escape")
    confere(tag + "Esc fecha a confirmação", not pg.is_visible("#dlg-confirma"))
    pg.click("#btn-cta"); pg.click("#btn-voltar")
    confere(tag + "Voltar e ajustar fecha a confirmação", not pg.is_visible("#dlg-confirma"))

    ev = [e[0] for e in pg.evaluate("window.__ev")]
    for esperado_ev in ("usou-simulador-imovel", "escolheu-banco", "usou-taxa-propria", "simulou-amortizacao", "abriu-amortizacao", "abriu-confirmacao", "cta-parceiro", "copiou-link"):
        confere(tag + "evento " + esperado_ev, esperado_ev in ev)

    confere(tag + "sem rolagem lateral depois de usar", pg.evaluate("document.documentElement.scrollWidth") <= pg.evaluate("window.innerWidth"), pg.evaluate("[document.documentElement.scrollWidth, window.innerWidth]"))
    campos = pg.evaluate("Array.from(document.querySelectorAll('input[type=text]')).filter(e=>e.offsetParent).map(e=>parseFloat(getComputedStyle(e).fontSize))")
    confere(tag + "campos de texto com 16 px ou mais (iOS não dá zoom)", all(f >= 16 for f in campos), campos)
    pequenos = pg.evaluate("Array.from(document.querySelectorAll('a,button,summary,label.ck')).filter(e=>e.offsetParent && !e.closest('.opts') && !e.closest('dialog')).map(e=>{const r=e.getBoundingClientRect();return [e.textContent.trim().slice(0,30),Math.round(r.width),Math.round(r.height)]}).filter(x=>x[2]<40 && x[1]<40)")
    confere(tag + "alvos de toque grandes o bastante", not pequenos, pequenos[:5])
    confere(tag + "sem erro de console", not erros, erros[:5])
    ctx.close()


def links(base):
    """Todos os links internos da home e das páginas ligadas a ela por 1 salto: nenhum 404."""
    html = urllib.request.urlopen(base + "/").read().decode("utf-8")
    hrefs = sorted(set(re.findall(r'href="([^"#]+)', html)))
    internos = [h for h in hrefs if h.startswith("/") or h.startswith(base)]
    ruins = []
    for h in internos:
        if h.startswith("/") and not h.startswith("//"):
            u = base + h.split("?")[0]
        else:
            u = h
        try:
            c = urllib.request.urlopen(u).status
        except urllib.error.HTTPError as e:
            c = e.code
        if c != 200:
            ruins.append((h, c))
    confere("links internos da home: %d, nenhum com erro" % len(internos), not ruins, ruins)


def main():
    with servidor_local.servir() as base, sync_playwright() as pw:
        links(base)
        for nome_nav in ("chromium", "webkit"):
            nav = getattr(pw, nome_nav).launch()
            perfis = [("desktop", {"viewport": {"width": 1280, "height": 900}}),
                      ("celular", dict(pw.devices["Pixel 5" if nome_nav == "chromium" else "iPhone 13"]))]
            for p in perfis:
                rodar(nav, nome_nav, base, p)
            nav.close()
    print("\n%d checagens, %d falhas" % (TOTAL[0], len(FALHAS)))
    for f in FALHAS:
        print(" - " + f)
    sys.exit(1 if FALHAS else 0)


if __name__ == "__main__":
    main()
