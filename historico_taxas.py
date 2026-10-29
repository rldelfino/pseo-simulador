"""
Histórico mensal de taxas de juros do financiamento imobiliário por banco,
da mesma fonte oficial que o etl_taxas.py usa (API pública do BACEN, modalidade
903201 — "Aquisição de imóveis, taxa pré-fixada, pessoa física").

Por que existe (auditoria de SEO, 29/out/2026): o ETL guarda só a última taxa
de cada banco. Uma página "taxas por banco" que mostra também a EVOLUÇÃO mês a
mês é o tipo de dado que blogs e jornalistas citam, e é a base do conjunto de
dados abertos publicado em /dados-abertos. A API do BACEN guarda a série desde
2012; aqui guardamos os últimos MESES_HISTORICO meses em historico_taxas.csv e,
a cada execução do ETL, acrescentamos só os meses que ainda faltam.

Cobre só os bancos que o BACEN cobre nesta modalidade (BRB e Poupex não
aparecem no relatório — para esses a taxa do site é estimada, e eles ficam de
fora do histórico de propósito, para nunca redistribuir como "dado oficial" um
número que não é do BACEN).

Rodar: python historico_taxas.py   (idempotente; falha de rede NÃO derruba o
pipeline: avisa e sai com código 0, mantendo o CSV que já existe).
"""
import csv
import os
import re
import sys
from datetime import date

import requests

from etl_taxas import (
    ALIASES_BACEN_IMOVEL,
    FONTE_BACEN_API_DADOS,
    FONTE_BACEN_API_DATAS,
    FONTE_BACEN_CODIGO_MODALIDADE,
    FONTE_BACEN_PAGINA_HUMANA,
    TAXA_MAXIMA_PLAUSIVEL,
    TAXA_MINIMA_PLAUSIVEL,
    _normalizar_nome_instituicao,
)

ARQUIVO_HISTORICO = "historico_taxas.csv"
CABECALHO = ["inicio_periodo", "fim_periodo", "banco", "taxa_aa"]
MESES_HISTORICO = 24
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; datalab-global-etl/1.0; +https://www.datalabglobal.com)"}


def ler_historico(caminho=ARQUIVO_HISTORICO):
    """Lista de dicts {inicio_periodo, fim_periodo, banco, taxa_aa(float)},
    ordenada por período e banco. Arquivo ausente -> lista vazia."""
    try:
        with open(caminho, encoding="utf-8", newline="") as f:
            linhas = [
                {"inicio_periodo": r["inicio_periodo"], "fim_periodo": r["fim_periodo"],
                 "banco": r["banco"], "taxa_aa": float(r["taxa_aa"])}
                for r in csv.DictReader(f, delimiter=";")
            ]
    except FileNotFoundError:
        return []
    return sorted(linhas, key=lambda r: (r["inicio_periodo"], r["banco"]))


def _fim_do_periodo(texto_periodo):
    """'01/09/2026 a 30/09/2026' -> '2026-09-30'."""
    m = re.search(r"a\s+(\d{2})/(\d{2})/(\d{4})", texto_periodo or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def listar_periodos_mensais():
    """Períodos mensais publicados pelo BACEN, do mais recente pro mais antigo:
    [{'inicio': '2026-09-01', 'fim': '2026-09-30'}, ...]."""
    resp = requests.get(
        FONTE_BACEN_API_DATAS,
        params={"codigoSegmento": "1", "codigoModalidade": FONTE_BACEN_CODIGO_MODALIDADE},
        headers=_HEADERS, timeout=30,
    )
    resp.raise_for_status()
    conteudo = resp.json().get("conteudo")
    if not isinstance(conteudo, list):
        raise ValueError("resposta de ConsultaDatas mudou de formato (sem 'conteudo')")
    return [
        {"inicio": p["InicioPeriodo"], "fim": _fim_do_periodo(p.get("Periodo", ""))}
        for p in conteudo if p.get("tipoModalidade") == "M"
    ]


def buscar_taxas_periodo(inicio_periodo):
    """{banco: taxa_aa} dos bancos de ALIASES_BACEN_IMOVEL no período mensal.
    Mesma regra de casamento/plausibilidade do etl_taxas._buscar_bacen_json."""
    filtro = (
        f"(codigoSegmento eq '1') and (codigoModalidade eq '{FONTE_BACEN_CODIGO_MODALIDADE}') "
        f"and (InicioPeriodo eq '{inicio_periodo}')"
    )
    resp = requests.get(FONTE_BACEN_API_DADOS, params={"filtro": filtro}, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    linhas = resp.json().get("conteudo")
    if not isinstance(linhas, list):
        raise ValueError("resposta do BACEN mudou de formato (sem 'conteudo')")
    resultado = {}
    for linha in linhas:
        nome = _normalizar_nome_instituicao(str(linha.get("InstituicaoFinanceira", "")))
        try:
            taxa = float(str(linha["TaxaJurosAoAno"]).replace(",", "."))
        except (KeyError, ValueError, TypeError):
            continue
        if not (TAXA_MINIMA_PLAUSIVEL <= taxa <= TAXA_MAXIMA_PLAUSIVEL):
            continue
        for banco, aliases in ALIASES_BACEN_IMOVEL.items():
            if banco in resultado:
                continue
            if any(_normalizar_nome_instituicao(a) in nome for a in aliases):
                resultado[banco] = taxa
    return resultado


def salvar_historico(linhas, caminho=ARQUIVO_HISTORICO):
    linhas = sorted(linhas, key=lambda r: (r["inicio_periodo"], r["banco"]))
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(CABECALHO)
        for r in linhas:
            w.writerow([r["inicio_periodo"], r["fim_periodo"], r["banco"], f"{r['taxa_aa']:.2f}"])


def atualizar_historico(caminho=ARQUIVO_HISTORICO, meses=MESES_HISTORICO):
    """Acrescenta ao CSV os meses (dos últimos `meses` publicados) que ainda
    não estão lá. Devolve (qtd_meses_novos, total_de_meses)."""
    existentes = ler_historico(caminho)
    ja_tem = {r["inicio_periodo"] for r in existentes}
    periodos = listar_periodos_mensais()[:meses]
    novos = [p for p in periodos if p["inicio"] not in ja_tem]
    linhas = list(existentes)
    adicionados = 0
    for p in novos:
        try:
            taxas = buscar_taxas_periodo(p["inicio"])
        except (requests.RequestException, ValueError) as e:
            print(f"⚠️  histórico: falha no período {p['inicio']} ({e}) — segue sem ele")
            continue
        if not taxas:
            print(f"⚠️  histórico: período {p['inicio']} sem nenhum banco casado — ignorado")
            continue
        for banco, taxa in taxas.items():
            linhas.append({"inicio_periodo": p["inicio"], "fim_periodo": p["fim"], "banco": banco, "taxa_aa": taxa})
        adicionados += 1
    # mantém só a janela dos últimos `meses` períodos conhecidos
    janela = {p["inicio"] for p in periodos}
    linhas = [r for r in linhas if r["inicio_periodo"] in janela] or linhas
    salvar_historico(linhas, caminho)
    return adicionados, len({r["inicio_periodo"] for r in linhas})


if __name__ == "__main__":
    try:
        novos, total = atualizar_historico()
        print(f"✅ histórico de taxas: {novos} mês(es) novo(s); {total} mês(es) no total em {ARQUIVO_HISTORICO} (fonte: {FONTE_BACEN_PAGINA_HUMANA})")
    except (requests.RequestException, ValueError) as e:
        print(f"⚠️  histórico de taxas não atualizado ({e}); mantendo o arquivo existente.")
    sys.exit(0)
