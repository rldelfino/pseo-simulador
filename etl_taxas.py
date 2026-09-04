import csv
import json
import re
from datetime import date

import requests
from bs4 import BeautifulSoup

from bancos import BANCOS

ARQUIVO_ULTIMA_ATUALIZACAO = 'ultima_atualizacao_taxas.txt'
ARQUIVO_CACHE_TAXAS = 'taxas_cache.json'
ARQUIVO_RELATORIO = 'relatorio_atualizacao_taxas.txt'

# Grade de valores/prazos usada para popular um banco novo com cobertura
# completa (mesma grade já usada organicamente pelos bancos existentes),
# e também a grade-base do dados.csv inteiro. Sem isso, um banco novo
# nasce com 1 página solitária, sem cluster suficiente para se autolincar
# via SEO (ver bug de "páginas órfãs" corrigido no gerador.py).
VALORES_IMOVEL_PADRAO = list(range(150_000, 1_500_001, 50_000))
# Expandido de [360, 420] pra cobrir os prazos "redondos" que as pessoas
# realmente buscam (10/15/20/25/30/35 anos), não só os TETOS máximos de
# cada banco. Cada banco continua limitado ao seu próprio prazo_max (ver
# gerador.py: min(prazo_csv, regra["prazo_max"]) + dedup por slug), então
# um banco com teto de 240 meses (ex: C6) simplesmente não gera páginas
# pros prazos acima disso — não sobra prazo "inválido" nem página duplicada.
PRAZOS_PADRAO = [120, 180, 240, 300, 360, 420]

# Faixa de sanidade: qualquer taxa buscada fora disso é rejeitada (protege
# contra parsing errado — ex: pegar sem querer um número de CPF, um ano,
# ou uma taxa mensal em vez de anual). Financiamento imobiliário real no
# Brasil não sai desse intervalo hoje.
TAXA_MINIMA_PLAUSIVEL = 6.0
TAXA_MAXIMA_PLAUSIVEL = 25.0

# Fontes automatizadas de taxa "típica" de mercado (não promocional/"a
# partir de"). Cada fonte tem uma tabela HTML comparativa — o parser lê a
# tabela de verdade, não texto solto, porque texto solto de blog costuma
# misturar a taxa mínima anunciada (ex: FGTS/Pró-Cotista) com a taxa
# típica, que foi exatamente o bug que corrigimos no Banco Inter. Só
# incluímos aqui fontes que já checamos manualmente e que separam as
# duas coisas com clareza.
#
# Pra adicionar uma fonte nova pra um banco que hoje não tem (Poupex,
# Sicoob, Sicredi, Banrisul, C6, Bari, Cash Me, Daycoval): basta
# acrescentar uma entrada na lista abaixo com a URL e os aliases que o
# nome do banco pode assumir na tabela dessa fonte.
FONTES_TAXA_TIPICA = [
    {
        "url": "https://larya.com.br/blog/qual-banco-tem-a-menor-taxa-para-financiamento-imobiliario-em-2026/",
        "aliases": {
            "Caixa": ["caixa"],
            "Banco do Brasil": ["banco do brasil"],
            "Santander": ["santander"],
            "Itau": ["itaú", "itau"],
            "Bradesco": ["bradesco"],
            "BRB": ["brb"],
            "Banco Inter": ["inter"],
        },
    },
]

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DatalabGlobalBot/1.0; +https://datalabglobal.com.br)"}


def _extrair_taxa_da_tabela(html, aliases_por_banco):
    """
    Procura, em toda <table> da página, uma linha cuja primeira(s) célula(s)
    bata(m) com algum alias de banco, e extrai a primeira porcentagem
    (formato "11,19%" ou "11.19%") encontrada NA MESMA LINHA. Retorna um
    dict {banco: taxa_float} só com o que encontrou — bancos não achados
    simplesmente não aparecem no resultado (o chamador decide o fallback).
    """
    soup = BeautifulSoup(html, "html.parser")
    achadas = {}
    padrao_pct = re.compile(r'(\d{1,2}[,.]\d{1,2})\s*%')

    for tabela in soup.find_all("table"):
        for linha in tabela.find_all("tr"):
            celulas = linha.find_all(["td", "th"])
            if not celulas:
                continue
            texto_linha = " | ".join(c.get_text(" ", strip=True) for c in celulas).lower()

            for banco, aliases in aliases_por_banco.items():
                if banco in achadas:
                    continue
                if any(alias in texto_linha for alias in aliases):
                    m = padrao_pct.search(texto_linha)
                    if m:
                        valor = float(m.group(1).replace(",", "."))
                        if TAXA_MINIMA_PLAUSIVEL <= valor <= TAXA_MAXIMA_PLAUSIVEL:
                            achadas[banco] = valor

    return achadas


def _buscar_taxas_nas_fontes():
    """
    Percorre FONTES_TAXA_TIPICA e tenta extrair taxas reais de cada uma.
    Uma fonte que falhar (rede fora do ar, HTML mudou de estrutura) não
    derruba as outras — cada requisição é isolada em try/except. Retorna
    um dict {banco: {"taxa": float, "fonte": url}} com tudo que
    conseguiu, de qualquer fonte.
    """
    resultado = {}
    for fonte in FONTES_TAXA_TIPICA:
        url = fonte["url"]
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"⚠️  Não foi possível acessar {url}: {e}")
            continue

        try:
            achadas = _extrair_taxa_da_tabela(resp.text, fonte["aliases"])
        except Exception as e:
            print(f"⚠️  Falha ao interpretar a tabela de {url}: {e}")
            continue

        for banco, taxa in achadas.items():
            if banco not in resultado:  # primeira fonte que achar um banco "ganha"
                resultado[banco] = {"taxa": taxa, "fonte": url}

    return resultado


def _carregar_cache():
    try:
        with open(ARQUIVO_CACHE_TAXAS, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _salvar_cache(cache):
    with open(ARQUIVO_CACHE_TAXAS, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2, sort_keys=True)


def obter_taxas_reais_mercado():
    """
    Busca a taxa "típica" de mercado de cada banco em fontes reais na web
    (ver FONTES_TAXA_TIPICA). Regra de fallback, em ordem de prioridade:

      1. Achou na busca de hoje?               -> usa o valor novo.
      2. Não achou, mas tem cache de mês(es)
         anterior(es)?                          -> mantém o valor do cache
                                                    (não regride pro
                                                    hardcoded de bancos.py).
      3. Nunca teve nenhum valor confirmado
         (banco novo, ou nenhuma fonte cobre
         ele ainda, ex: Poupex/Sicoob/C6/Bari)? -> usa o taxa_padrao
                                                    "bootstrap" curado à
                                                    mão em bancos.py.

    Sempre grava um relatório (relatorio_atualizacao_taxas.txt) dizendo
    qual banco caiu em qual caso — isso é o que permite auditar se o ETL
    está de fato encontrando dado fresco ou só reciclando o cache.
    """
    print("Buscando taxas típicas de mercado nas fontes configuradas...")
    achadas_hoje = _buscar_taxas_nas_fontes()
    cache = _carregar_cache()
    hoje = date.today().isoformat()

    taxas_finais = {}
    linhas_relatorio = [f"Atualização de taxas — {hoje}", "=" * 40]

    for banco, regra in BANCOS.items():
        if banco in achadas_hoje:
            taxa = achadas_hoje[banco]["taxa"]
            fonte = achadas_hoje[banco]["fonte"]
            cache[banco] = {"taxa": taxa, "fonte": fonte, "atualizado_em": hoje}
            linhas_relatorio.append(f"✅ {banco}: {taxa}% a.a. (encontrado agora em {fonte})")
        elif banco in cache:
            taxa = cache[banco]["taxa"]
            data_cache = cache[banco].get("atualizado_em", "?")
            linhas_relatorio.append(
                f"↪️  {banco}: {taxa}% a.a. (sem fonte nova hoje — mantido do cache de {data_cache})"
            )
        else:
            taxa = regra["taxa_padrao"]
            linhas_relatorio.append(
                f"⚠️  {banco}: {taxa}% a.a. (nenhuma fonte configurada ainda — usando valor padrão de bancos.py)"
            )

        taxas_finais[banco] = taxa
        print(f"  {banco}: {taxa}% a.a.")

    _salvar_cache(cache)

    with open(ARQUIVO_RELATORIO, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_relatorio) + "\n")
    print(f"\nRelatório detalhado salvo em {ARQUIVO_RELATORIO}")

    return taxas_finais


def atualizar_base_csv(novas_taxas):
    caminho_csv = 'dados.csv'
    dados_atualizados = []

    try:
        with open(caminho_csv, mode='r', encoding='utf-8') as f:
            leitor = csv.DictReader(f, delimiter=';')
            cabecalho = list(leitor.fieldnames)

            for col in ['cet', 'ltv', 'prazo_maximo']:
                if col not in cabecalho:
                    cabecalho.append(col)

            for linha in leitor:
                banco = linha['banco']
                if novas_taxas and banco in novas_taxas:
                    linha['taxa'] = novas_taxas[banco]

                regra = BANCOS.get(banco, {"ltv": 0.80, "prazo_max": 360})
                linha['ltv'] = round(regra['ltv'] * 100)
                linha['prazo_maximo'] = regra.get('prazo_max', 360)

                taxa_atual = float(linha['taxa'])
                linha['cet'] = round(taxa_atual + 0.15, 2)
                dados_atualizados.append(linha)

            # Adiciona bancos novos definidos em bancos.py que ainda não estão no
            # CSV, já com a grade completa de valores x prazos (não apenas 1
            # linha solitária) para que o novo banco tenha cluster suficiente
            # para a linkagem interna funcionar desde o primeiro dia.
            bancos_existentes = {d['banco'] for d in dados_atualizados}
            for novo_banco, regra in BANCOS.items():
                if novo_banco in bancos_existentes:
                    continue
                taxa_n = novas_taxas.get(novo_banco, regra['taxa_padrao'])
                nome_slug = novo_banco.lower().replace(" ", "-")
                for valor in VALORES_IMOVEL_PADRAO:
                    for prazo in PRAZOS_PADRAO:
                        milhares = int(valor / 1000)
                        dados_atualizados.append({
                            'banco': novo_banco, 'valor_imovel': str(valor), 'taxa': taxa_n,
                            'prazo': str(prazo),
                            'slug': f'simulador-{nome_slug}-{milhares}-mil-{prazo}-meses',
                            'cet': round(taxa_n + 0.15, 2), 'ltv': round(regra['ltv'] * 100),
                            'prazo_maximo': regra['prazo_max'],
                        })

        with open(caminho_csv, mode='w', newline='', encoding='utf-8') as f:
            escritor = csv.DictWriter(f, fieldnames=cabecalho, delimiter=';')
            escritor.writeheader()
            escritor.writerows(dados_atualizados)

        # Grava a data real da última atualização de dados — usada pelo
        # gerador.py como <lastmod> do sitemap e dateModified do schema.
        # Importante: isso é a data em que os DADOS mudaram, não a data de
        # cada deploy — o Google trata "lastmod sempre = hoje" como sinal de
        # frescor falso, então só reescrevemos esse arquivo aqui, quando as
        # taxas de fato são recuradas (rodagem mensal do ETL).
        with open(ARQUIVO_ULTIMA_ATUALIZACAO, 'w', encoding='utf-8') as f:
            f.write(date.today().isoformat())

        print("\n🚀 O arquivo dados.csv foi curado com taxas REAIS de mercado!")

    except FileNotFoundError:
        print("Arquivo dados.csv não encontrado para atualização.")


if __name__ == "__main__":
    taxas_seguras = obter_taxas_reais_mercado()
    atualizar_base_csv(taxas_seguras)
