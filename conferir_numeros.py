"""Conferência dos números do site contra fontes independentes (rodar à mão; usa a rede).

1. Taxas: cada banco de dados.csv x API do Banco Central (modalidade 903201, último mês publicado), mais a coerência
   entre dados.csv, historico_taxas.csv, taxas_cache.json e o que as páginas geradas mostram.
2. Conta: PRICE e SAC recalculados aqui, por fórmula fechada e por tabela mês a mês, contra gerador.calcular_sac_price.
3. Datas: "atualizado em" do site x ultima_atualizacao_taxas.txt x período do BCB.

Uso: python conferir_numeros.py [--sem-rede]   (escreve o relatório em CONFERENCIA-NUMEROS.md)
Python 3.10: sem f-string aninhado.
"""
import csv
import json
import os
import re
import sys
from datetime import date

AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(AQUI)
sys.path.insert(0, AQUI)

import etl_taxas  # noqa: E402  (usa a mesma API e os mesmos apelidos de banco do robô)
from bancos import BANCOS  # noqa: E402
import gerador  # noqa: E402

SEM_REDE = "--sem-rede" in sys.argv
linhas = []


def p(texto=""):
    print(texto)
    linhas.append(texto)


def pct(x):
    return ("%.2f" % x).replace(".", ",")


def taxa_do_csv():
    """{banco: taxa a.a.} da primeira linha de cada banco em dados.csv."""
    out = {}
    with open("dados.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            out.setdefault(r["banco"], float(r["taxa"].replace(",", ".")))
    return out


def bcb_ao_vivo():
    import requests
    h = etl_taxas._HEADERS
    datas = requests.get(etl_taxas.FONTE_BACEN_API_DATAS, headers=h, timeout=30).json()
    periodos = [x for x in datas.get("conteudo", datas) if x.get("tipoModalidade") == "M"]
    ini = periodos[0]["InicioPeriodo"]
    filtro = "(codigoSegmento eq '1') and (codigoModalidade eq '903201') and (InicioPeriodo eq '%s')" % ini
    corpo = requests.get(etl_taxas.FONTE_BACEN_API_DADOS, params={"filtro": filtro}, headers=h, timeout=30).json()
    return ini, corpo.get("conteudo", corpo)


def secao_taxas():
    p("## 1. Taxas por banco x Banco Central")
    csv_taxas = taxa_do_csv()
    cache = {}
    if os.path.exists("taxas_cache.json"):
        with open("taxas_cache.json", encoding="utf-8") as f:
            cache = json.load(f)
    hist = {}
    with open("historico_taxas.csv", encoding="utf-8") as f:
        for r in csv.reader(f, delimiter=";"):
            if r and r[0][:2] == "20":
                hist.setdefault(r[2], {})[r[0]] = float(r[3])
    bcb = {}
    ini = None
    if not SEM_REDE:
        try:
            ini, rows = bcb_ao_vivo()
            for r in rows:
                bcb[etl_taxas._normalizar_nome_instituicao(r["InstituicaoFinanceira"])] = (
                    float(r["TaxaJurosAoMes"].replace(",", ".")), float(r["TaxaJurosAoAno"].replace(",", ".")))
        except Exception as e:  # rede fora do ar não derruba o relatório
            p("Falha ao consultar o BCB: %s. Seção feita só com os arquivos locais." % e)
    p("")
    p("Período mais recente do BCB: %s." % (ini or "não consultado"))
    p("")
    p("| Banco | dados.csv (a.a.) | BCB a.a. | BCB a.m. | (1+a.m.)^12-1 | Último mês em historico_taxas.csv | Fonte no cache | Situação |")
    p("|---|---|---|---|---|---|---|---|")
    for banco in BANCOS:
        t = csv_taxas.get(banco)
        aliases = etl_taxas.ALIASES_BACEN_IMOVEL.get(banco, [])
        achado = None
        for nome, v in bcb.items():
            if any(etl_taxas._normalizar_nome_instituicao(a) in nome for a in aliases):
                achado = v
        meses = sorted(hist.get(banco, {}))
        h_ult = ("%s = %s" % (meses[-1][:7], pct(hist[banco][meses[-1]]))) if meses else "—"
        fonte = str(cache.get(banco, {}).get("fonte", "")) or "—"
        fonte = "BCB" if "bcb.gov.br" in fonte else ("blog/estimativa" if fonte != "—" else "bancos.py (estático)")
        if achado:
            comp = ((1 + achado[0] / 100) ** 12 - 1) * 100
            ok = "confere" if t is not None and abs(t - achado[1]) < 0.005 else "DIFERENTE"
            p("| %s | %s | %s | %s | %s | %s | %s | %s |" % (banco, pct(t) if t else "—", pct(achado[1]), pct(achado[0]), pct(comp), h_ult, fonte, ok))
        else:
            quando = "sem linha no BCB (modalidade não cobre)" if bcb else "não consultado"
            p("| %s | %s | — | — | — | %s | %s | %s: NÃO verificável aqui |" % (banco, pct(t) if t else "—", h_ult, fonte, quando))
    p("")


def secao_conta():
    p("## 2. Conta: PRICE e SAC recalculados do zero")
    casos = [(400_000, 360, 11.97), (250_000, 120, 12.32), (900_000, 420, 14.42), (150_000, 180, 10.00), (640_000, 300, 12.97)]
    p("")
    p("| Financiado | Prazo | Taxa a.a. | PRICE (fórmula) | PRICE (site) | SAC 1ª (fórmula) | SAC 1ª (site) | SAC total (tabela) | SAC total (site) |")
    p("|---|---|---|---|---|---|---|---|---|")
    pior = 0.0
    for fin, n, aa in casos:
        i = (1 + aa / 100) ** (1 / 12) - 1
        pmt = fin * i / (1 - (1 + i) ** -n)
        sac1 = fin / n + fin * i
        saldo, total = fin, 0.0
        for _ in range(n):
            total += fin / n + saldo * i
            saldo -= fin / n
        r = gerador.calcular_sac_price(fin, n, aa)
        pior = max(pior, abs(pmt - r["p1_price"]), abs(sac1 - r["p1_sac"]), abs(total - r["total_sac"]))
        p("| %d | %d | %s | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f |" % (fin, n, pct(aa), pmt, r["p1_price"], sac1, r["p1_sac"], total, r["total_sac"]))
    p("")
    p("Maior diferença entre a fórmula e o site: R$ %.6f." % pior)
    p("")
    # efeito da correção de 20/11/2026
    fin, n, aa = 400_000, 360, 11.97
    velho = aa / 100 / 12
    novo = (1 + aa / 100) ** (1 / 12) - 1
    f = lambda i: fin * i / (1 - (1 + i) ** -n)
    p("Efeito da correção (Caixa, R$ 400 mil, 360 meses, %s%% a.a.): a taxa mensal passou de %.4f%% (a.a. ÷ 12) para %.4f%% (equivalente composta, igual ao 0,95%% a.m. que o próprio BCB publica); "
      "a parcela PRICE caiu de R$ %.2f para R$ %.2f (%.1f%%)." % (pct(aa), velho * 100, novo * 100, f(velho), f(novo), (f(novo) / f(velho) - 1) * 100))
    p("")


def secao_datas():
    p("## 3. Datas de atualização")
    p("")
    ult = open("ultima_atualizacao_taxas.txt", encoding="utf-8").read().strip()
    p("- ultima_atualizacao_taxas.txt: %s (dia em que o robô gravou as taxas)." % ult)
    pagina = os.path.join("paginas_seo", "banco-caixa.html")
    if os.path.exists(pagina):
        h = open(pagina, encoding="utf-8").read()
        datas = sorted(set(re.findall(r"(?:atualizad[ao]s? em|Atualizado em)\s*(\d{2}/\d{2}/\d{4})", h, re.I)))
        p("- Datas mostradas em banco-caixa.html: %s." % (", ".join(datas) or "nenhuma"))
    hist = [r for r in csv.reader(open("historico_taxas.csv", encoding="utf-8"), delimiter=";") if r and r[0][:2] == "20"]
    p("- Último mês no histórico: %s." % max(r[0] for r in hist))
    p("- Lembrete: o site diz \"taxas atualizadas em <dia do robô>\", mas a taxa é a média do mês fechado do BCB (o mês anterior ao do robô). "
      "O texto já fala em \"média de mês/ano\"; conferir se nenhum trecho chama a taxa de \"de hoje\".")
    p("")


def main():
    p("# Conferência dos números — %s" % date.today().strftime("%d/%m/%Y"))
    p("")
    secao_taxas()
    secao_conta()
    secao_datas()
    with open("CONFERENCIA-NUMEROS.md", "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")


if __name__ == "__main__":
    main()
