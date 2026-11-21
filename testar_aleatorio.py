"""Sessões aleatórias na home (Chromium no computador e WebKit no celular), fora do CI.

Cada sessão faz 60 passos ao acaso (digitar valor, entrada, prazo; mexer nos controles deslizantes; trocar banco e SAC/Price; taxa de proposta,
às vezes lixo; pagar a mais). A cada passo, o estado esperado é recalculado em Python (calculo_home.py, com as mesmas regras de limite do
home.js) e conferido com o que a tela mostra: parcela, total, CET, % de juros da rosca, melhor banco da lista e o link compartilhável.
Também vigia erro de console e rolagem lateral. Uso: python testar_aleatorio.py [semente]
"""
import json
import math
import random
import re
import sys

from playwright.sync_api import sync_playwright

import calculo_home as C
import servidor_local

FALHAS = []
PASSOS = 60
SESSOES = 6


def numero(t):
    return int(re.sub(r"[^\d]", "", t) or 0)


def centavos(t):
    return float(re.sub(r"[^\d,]", "", t).replace(",", "."))


def ler_numero(texto):
    """Mesma regra de lerNumero() do home.js."""
    t = re.sub(r"[^\d.,]", "", texto)
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    elif re.search(r"\.\d{3}(\.|$)", t):
        t = t.replace(".", "")
    try:
        return float(t)
    except ValueError:
        return 0.0


class Modelo:
    def __init__(self, D):
        self.D = D
        p = D["padrao"]
        self.imovel, self.entrada, self.anos, self.banco, self.sis = p["imovel"], p["entrada"], p["anos"], p["banco"], p["sistema"]
        self.taxa_prop, self.nominal = 0.0, False

    def b(self):
        if self.banco == "mercado":
            return dict(self.D["mercado"], k="mercado")
        return next(x for x in self.D["bancos"] if x["k"] == self.banco)

    def ajustar(self):
        self.imovel = min(max(self.imovel, 100_000), 3_000_000)
        self.anos = min(max(round(self.anos), 5), self.b()["p"] // 12)

    def emin(self):
        return math.ceil(self.imovel * (1 - self.b()["l"]) / 1000) * 1000

    def emax(self):
        return math.floor(self.imovel * 0.9 / 1000) * 1000

    def ent(self):
        return min(max(self.entrada, self.emin()), self.emax())

    def calc(self):
        self.ajustar()
        prop = 3 <= self.taxa_prop <= 40
        aa = self.taxa_prop if prop else self.b()["t"]
        return C.simular(self.imovel, self.ent(), self.anos, aa, self.sis, self.nominal and prop)

    def melhor_banco(self):
        prop = 3 <= self.taxa_prop <= 40
        linhas = []
        for b in self.D["bancos"]:
            m = min(self.anos * 12, b["p"])
            e = min(max(self.ent(), math.ceil(self.imovel * (1 - b["l"]) / 1000) * 1000), self.imovel - 10_000)
            r = C.simular(self.imovel, e, m / 12, self.taxa_prop if prop else b["t"], self.sis, self.nominal and prop)
            linhas.append((r["cet"], b["n"]))
        linhas.sort(key=lambda x: x[0])
        return linhas[0][1], linhas[0][0]


def passo(pg, m, rnd, D, bancos):
    """Faz uma ação ao acaso na página e atualiza o modelo. Devolve a descrição."""
    a = rnd.choice(["imovel", "imovel_lixo", "entrada", "entrada", "prazo", "prazo_range", "banco", "sistema", "taxa", "taxa_lixo", "taxa_limpa", "imovel_range", "entrada_range", "extra"])
    if a == "imovel":
        v = rnd.choice([80_000, 120_000, 350_000, 500_000, 900_000, 1_500_000, 2_999_999, 4_000_000])
        pg.fill("#campo-imovel", format(v, ",").replace(",", ".")); pg.press("#campo-imovel", "Enter")
        m.imovel = float(v)
    elif a == "imovel_lixo":
        t = rnd.choice(["abc", "", "0", "-5", "1e9", "R$ 700.000,00"])
        pg.fill("#campo-imovel", t); pg.press("#campo-imovel", "Enter")
        m.imovel = ler_numero(t)
    elif a == "entrada":
        t = rnd.choice(["0", "5.000", "50.000", "130.000", "250.000", "600.000", "99.999.999", "xx"])
        pg.fill("#campo-entrada", t); pg.press("#campo-entrada", "Enter")
        m.entrada = ler_numero(t)
    elif a == "prazo":
        t = rnd.choice(["5", "10", "17", "30", "35", "36", "3", "0", "abc", "420"])
        pg.fill("#campo-prazo", t); pg.press("#campo-prazo", "Enter")
        v = round(ler_numero(t))
        mx = m.b()["p"] // 12
        if not (5 <= v <= mx):
            v = min(max(v if v > 0 else m.anos, 5), mx)
        m.anos = v
    elif a == "prazo_range":
        v = rnd.randint(5, m.b()["p"] // 12)
        pg.evaluate("v=>{const r=document.getElementById('range-prazo');r.value=v;r.dispatchEvent(new Event('input',{bubbles:true}))}", v)
        m.anos = v
    elif a == "banco":
        k = rnd.choice(["mercado"] + bancos)
        pg.click("#btn-banco"); pg.click("#lista-banco li[data-k='%s']" % k)
        m.banco = k
    elif a == "sistema":
        s = rnd.choice(["sac", "price"])
        pg.click("label[for=sis-%s]" % s)
        m.sis = s
    elif a == "taxa":
        if not pg.evaluate("document.getElementById('det-taxa').open"):
            pg.click("#det-taxa summary")
        t = rnd.choice(["9,5", "10,99", "12", "14,5", "3", "40", "2,9", "41"])
        pg.fill("#campo-taxa-prop", t); pg.press("#campo-taxa-prop", "Enter")
        m.taxa_prop = ler_numero(t)
        if rnd.random() < 0.4:
            pg.click("#ck-taxa-nominal"); m.nominal = not m.nominal
    elif a == "taxa_lixo":
        if not pg.evaluate("document.getElementById('det-taxa').open"):
            pg.click("#det-taxa summary")
        pg.fill("#campo-taxa-prop", "abc"); pg.press("#campo-taxa-prop", "Enter")
        m.taxa_prop = 0.0
    elif a == "taxa_limpa":
        if pg.evaluate("document.getElementById('det-taxa').open"):
            pg.fill("#campo-taxa-prop", ""); pg.press("#campo-taxa-prop", "Enter")
            m.taxa_prop = 0.0
    elif a == "imovel_range":
        v = rnd.randrange(100_000, 3_000_001, 10_000)
        pg.evaluate("v=>{const r=document.getElementById('range-imovel');r.value=v;r.dispatchEvent(new Event('input',{bubbles:true}))}", v)
        m.imovel = float(v)
    elif a == "entrada_range":
        m.ajustar()
        lo, hi = m.emin(), max(m.emin(), m.emax())
        v = rnd.randrange(lo, hi + 1, 5000) if hi > lo else lo
        pg.evaluate("v=>{const r=document.getElementById('range-entrada');r.value=v;r.dispatchEvent(new Event('input',{bubbles:true}))}", v)
        m.entrada = float(pg.evaluate("Number(document.getElementById('range-entrada').value)"))
    elif a == "extra":
        if not pg.evaluate("document.getElementById('det-amsim').open"):
            pg.click("#det-amsim summary")
        t = rnd.choice(["0", "300", "1.000", "5.000"])
        pg.fill("#campo-extra", t); pg.press("#campo-extra", "Enter")
    return a


def sessao(nav, nome, base, opcoes, semente, n_sessao, bancos):
    ctx = nav.new_context(**opcoes)
    ctx.route("**/*umami*", lambda r: r.abort())
    pg = ctx.new_page()
    erros = []
    pg.on("console", lambda msg: erros.append(msg.text) if msg.type == "error" else None)
    pg.on("pageerror", lambda e: erros.append("PAGEERROR " + str(e)))
    pg.add_init_script("window.umami={track:function(){}}")
    pg.goto(base + "/")
    pg.wait_for_selector("#bk-lista li")
    D = json.loads(pg.evaluate("document.getElementById('dados-home').textContent"))
    m = Modelo(D)
    rnd = random.Random(semente * 1000 + n_sessao)
    falhas = 0
    for i in range(PASSOS):
        a = passo(pg, m, rnd, D, bancos)
        r = m.calc()
        got = (numero(pg.inner_text("#r-parcela")), numero(pg.inner_text("#r-total")), centavos(pg.inner_text("#r-cet")))
        esp = (int(r["p1"] + 0.5), int(r["total"] + 0.5), r["cet"])
        ok = got[0] == esp[0] and got[1] == esp[1] and abs(got[2] - esp[2]) < 0.006
        pj = int(r["juros"] / r["total"] * 100 + 0.5)
        ok = ok and (pg.text_content("#rosca-pct") or "").strip() == "%d%%" % pj
        nb, cb = m.melhor_banco()
        primeiro = pg.locator("#bk-lista li").first
        ok = ok and nb in primeiro.inner_text() and abs(centavos(primeiro.locator(".bk-c b").inner_text()) - cb) < 0.006
        ok = ok and pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        if not ok:
            falhas += 1
            msg = "%s sessão %d passo %d (%s): tela %s, esperado %s, melhor banco %s/%s" % (nome, n_sessao, i, a, got, esp, nb, cb)
            print("FALHOU " + msg)
            FALHAS.append(msg)
            if falhas >= 3:
                break
    pg.wait_for_timeout(700)
    url = pg.evaluate("window.location.href")
    pg2 = ctx.new_page()
    pg2.goto(url)
    pg2.wait_for_selector("#bk-lista li")
    mesmo = (pg2.inner_text("#r-parcela"), pg2.inner_text("#r-total")) == (pg.inner_text("#r-parcela"), pg.inner_text("#r-total"))
    if not mesmo:
        FALHAS.append("%s sessão %d: o link compartilhável não repete a simulação" % (nome, n_sessao))
        print("FALHOU link da sessão %d" % n_sessao)
    if erros:
        FALHAS.append("%s sessão %d: erro de console %s" % (nome, n_sessao, erros[:2]))
        print("FALHOU console", erros[:2])
    print("%s sessão %d: %d passos, %d falhas, link %s, console %s" % (nome, n_sessao, PASSOS, falhas, "ok" if mesmo else "DIFERENTE", "limpo" if not erros else "COM ERRO"))
    ctx.close()


def main():
    semente = int(sys.argv[1]) if len(sys.argv) > 1 else 20261120
    print("semente", semente)
    with servidor_local.servir() as base, sync_playwright() as pw:
        for nome_nav, perfil_nome in (("chromium", "desktop"), ("webkit", "celular")):
            nav = getattr(pw, nome_nav).launch()
            opcoes = {"viewport": {"width": 1280, "height": 900}} if perfil_nome == "desktop" else dict(pw.devices["iPhone 13"])
            probe = nav.new_context(**opcoes).new_page()
            probe.goto(base + "/")
            bancos = [b["k"] for b in json.loads(probe.evaluate("document.getElementById('dados-home').textContent"))["bancos"]]
            probe.close()
            for s in range(SESSOES):
                sessao(nav, nome_nav + "/" + perfil_nome, base, opcoes, semente, s, bancos)
            nav.close()
    print("\n%d falhas" % len(FALHAS))
    sys.exit(1 if FALHAS else 0)


if __name__ == "__main__":
    main()
