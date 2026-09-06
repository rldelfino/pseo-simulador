import csv
import json
import re
from datetime import date

import requests
from bs4 import BeautifulSoup

from bancos import BANCOS, normalizar_chave

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
# Pra adicionar uma fonte nova pra um banco que hoje não tem: basta
# acrescentar uma entrada na lista abaixo com a URL e os aliases que o
# nome do banco pode assumir na tabela dessa fonte. Quando duas fontes
# cobrem o mesmo banco, a primeira da lista que encontrar um valor
# "ganha" (ver _buscar_taxas_nas_fontes) — por isso não tem problema a
# tabela do idinheiro abaixo também listar Caixa/BB/Itaú/etc: como a
# fonte da larya já resolve esses, os aliases aqui cobrem só os 4 bancos
# que essa fonte de fato adiciona de novo.
#
# Restam sem fonte automatizada: C6 Bank, Bari, Cash Me e Daycoval — são
# bancos de "Crédito com Garantia de Imóvel" (home equity), não
# financiamento imobiliário tradicional (SFH), e depois de pesquisa
# ativa (ago/2026) não existe hoje nenhuma tabela comparativa pública
# que separe taxa típica de taxa promocional pra esses 4 especificamente
# — os comparativos existentes ou não mencionam esses bancos, ou trazem
# só texto solto sem tabela (o mesmo tipo de fonte não-confiável que
# causou o bug do Banco Inter, que usamos taxa "a partir de" por engano).
# Continuam curados manualmente em bancos.py até uma fonte confiável
# aparecer — não é um bug, é a informação não existir de forma segura
# pra automatizar ainda.
# Fonte primária (achado da auditoria de set/2026, sugerida pelo Rodolfo:
# "faz mais sentido buscar do banco central mesmo"): relatório OFICIAL do
# Banco Central — Taxas de Juros por Instituição Financeira, modalidade
# "Financiamento imobiliário com taxas de mercado - Pós-fixado
# referenciado em TR" (código 903201, pessoa física) — a linha SFH
# clássica, a mais comum no mercado brasileiro. É a taxa média REAL de
# operações efetivamente contratadas, apurada mensalmente pelo próprio
# regulador — mais autoritativa que qualquer comparativo de blog, e sem
# o risco de misturar taxa promocional com taxa típica (o mesmo cuidado
# da lição do Banco Inter, ver docstring de bancos.py).
#
# Consome a API JSON pública que a própria página do BACEN usa
# internamente (achada inspecionando as chamadas de rede da página) —
# não precisa de parsing de HTML/tabela, então é mais robusto a mudança
# de layout do site do que as fontes de blog abaixo.
#
# Página humana equivalente (pra conferência manual):
# https://www.bcb.gov.br/estatisticas/reporttxjuros?codigoSegmento=1&codigoModalidade=903201
FONTE_BACEN_API_URL = "https://www.bcb.gov.br/api/servico/sitebcb/historicotaxajurosdiario/atual"
FONTE_BACEN_PAGINA_HUMANA = "https://www.bcb.gov.br/estatisticas/reporttxjuros?codigoSegmento=1&codigoModalidade=903201"
FONTE_BACEN_CODIGO_MODALIDADE = "903201"

# BACEN usa razão social oficial na resposta (ex: "BCO DO ESTADO DO RS
# S.A." = Banrisul; "CAIXA ECONOMICA FEDERAL" = Caixa) — não bate 1:1 com
# o nome comercial usado em bancos.py, por isso o mapeamento manual
# abaixo. Confirmado manualmente contra o relatório ao vivo (set/2026):
# essa modalidade específica NÃO cobre BRB nem Poupex (não aparecem no
# relatório desse período) — para esses dois, as fontes de blog abaixo
# continuam sendo o que temos. Também não cobre C6 Bank/Bari/Cash Me/
# Daycoval — que em bancos.py são "Crédito com Garantia de Imóvel"
# (home equity), um produto DIFERENTE de financiamento de compra de
# imóvel, então não faz sentido usar esta modalidade pra eles mesmo que
# o nome do banco apareça no relatório (Bari aparece, mas com a taxa do
# produto errado — cuidado se for adicionar uma fonte pra esses 4 no
# futuro: precisa ser a modalidade de home equity, não esta).
#
# Usa a razão social EXATA observada ao vivo (não um alias curto tipo só
# "SANTANDER"), pra reduzir o risco de casar sem querer com uma entidade
# errada do mesmo grupo (ex: um braço de financiamento separado do banco
# de varejo). A comparação em si (_normalizar_nome_instituicao) já tolera
# acento/caixa/pontuação variando — não precisa listar variante acentuada
# e sem acento à mão (antes tinha "ITAÚ"/"ITAU" duplicado; a normalização
# resolve isso sozinha agora, reaproveitando normalizar_chave de bancos.py
# em vez de duplicar a lógica de remover acento).
ALIASES_BACEN_IMOVEL = {
    "Caixa": ["CAIXA ECONOMICA FEDERAL"],
    "Banco do Brasil": ["BCO DO BRASIL S.A."],
    "Santander": ["BCO SANTANDER (BRASIL) S.A."],
    "Itau": ["ITAÚ UNIBANCO S.A."],
    "Bradesco": ["BCO BRADESCO S.A."],
    "Banco Inter": ["BANCO INTER"],
    "Sicredi": ["BANCO COOPERATIVO SICREDI"],
    "Sicoob": ["BANCO SICOOB S.A."],
    "Banrisul": ["BCO DO ESTADO DO RS S.A."],
}


def _normalizar_nome_instituicao(texto):
    """Uppercase + remove acento (reaproveita normalizar_chave de
    bancos.py) + remove pontuação solta + colapsa espaço — deixa a
    comparação tolerante a variações de formatação da razão social entre
    atualizações do relatório do BACEN (ex: 'S.A.' virar 'SA' num mês
    futuro, ou espaçamento duplo)."""
    sem_pontuacao = re.sub(r"[.,]", "", texto)
    sem_espaco_duplo = re.sub(r"\s+", " ", sem_pontuacao).strip()
    return normalizar_chave(sem_espaco_duplo).upper()


def _buscar_taxas_bacen_oficial():
    """
    Consulta o relatório oficial do BACEN (ver FONTE_BACEN_API_URL acima).
    É mensal — tenta o mês corrente e recua até 2 meses se ainda não
    tiver sido publicado (normalmente sai com poucos dias de atraso após
    o fechamento do mês). Retorna {banco: {"taxa": float, "fonte": url}}
    só com o que encontrou; bancos não cobertos por esta modalidade
    (BRB, Poupex, os 4 de home equity) simplesmente não aparecem — quem
    chama decide o fallback.
    """
    hoje = date.today()
    for meses_atras in range(3):
        ano, mes = hoje.year, hoje.month - meses_atras
        while mes <= 0:
            mes += 12
            ano -= 1
        inicio_periodo = f"{ano:04d}-{mes:02d}-01"
        filtro = (
            f"(codigoSegmento eq '1') and (codigoModalidade eq '{FONTE_BACEN_CODIGO_MODALIDADE}') "
            f"and (InicioPeriodo eq '{inicio_periodo}')"
        )
        try:
            resp = requests.get(FONTE_BACEN_API_URL, params={"filtro": filtro}, headers=_HEADERS, timeout=20)
            resp.raise_for_status()
            linhas = resp.json().get("conteudo", [])
        except (requests.RequestException, ValueError) as e:
            print(f"⚠️  BACEN: falha ao consultar período {inicio_periodo}: {e}")
            continue

        if not linhas:
            continue  # período ainda não publicado — tenta o mês anterior

        resultado = {}
        for linha in linhas:
            nome_bacen_norm = _normalizar_nome_instituicao(str(linha.get("InstituicaoFinanceira", "")))
            try:
                taxa_aa = float(str(linha["TaxaJurosAoAno"]).replace(",", "."))
            except (KeyError, ValueError, TypeError):
                continue
            if not (TAXA_MINIMA_PLAUSIVEL <= taxa_aa <= TAXA_MAXIMA_PLAUSIVEL):
                continue
            for banco, aliases in ALIASES_BACEN_IMOVEL.items():
                if not any(_normalizar_nome_instituicao(alias) in nome_bacen_norm for alias in aliases):
                    continue
                if banco in resultado:
                    # Mais de uma linha do relatório bateu no mesmo banco
                    # (ex: duas entidades do mesmo grupo) — mantém a
                    # primeira, mas avisa em vez de trocar em silêncio, pra
                    # não arriscar pegar a taxa da entidade errada sem
                    # ninguém perceber.
                    print(f"⚠️  BACEN: mais de uma linha bateu no alias de {banco} — mantendo a primeira encontrada, ignorando '{linha.get('InstituicaoFinanceira')}'")
                    continue
                resultado[banco] = {"taxa": taxa_aa, "fonte": FONTE_BACEN_PAGINA_HUMANA}

        if resultado:
            print(f"✅ BACEN: {len(resultado)} banco(s) encontrados pro período {inicio_periodo} ({FONTE_BACEN_PAGINA_HUMANA})")
            return resultado

    print("⚠️  BACEN: nenhum dos últimos 3 meses tinha relatório publicado")
    return {}


# Fontes secundárias (blog) — funcionam como fallback. Na prática, hoje
# só BRB e Poupex DEPENDEM delas (é o único par que o BACEN não cobre
# nessa modalidade); Sicoob/Sicredi/Banrisul também aparecem nos aliases
# abaixo, mas o BACEN já resolve os três primeiro — não remover esses
# três achando que são redundantes: são a rede de segurança pro dia em
# que o casamento de alias do BACEN quebrar pra algum deles (ver
# _normalizar_nome_instituicao) sem que ninguém perceba na hora.
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
    {
        "url": "https://www.idinheiro.com.br/financiamentos/imobiliario/melhor-taxa-financiamento-imobiliario/",
        "aliases": {
            "Sicoob": ["sicoob"],
            "Sicredi": ["sicredi"],
            "Poupex": ["poupex"],
            "Banrisul": ["banrisul", "banco do estado do rs", "banco do estado do rio grande do sul"],
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
    Tenta primeiro o BACEN oficial (_buscar_taxas_bacen_oficial —
    prioridade máxima, é a fonte regulatória), depois percorre
    FONTES_TAXA_TIPICA (blog) só pros bancos que o BACEN não cobriu
    nessa modalidade (hoje: BRB, Poupex). Uma fonte que falhar (rede
    fora do ar, HTML/API mudou de estrutura) não derruba as outras —
    cada requisição é isolada em try/except. Retorna um dict
    {banco: {"taxa": float, "fonte": url}} com tudo que conseguiu, de
    qualquer fonte.
    """
    resultado = {}

    try:
        resultado.update(_buscar_taxas_bacen_oficial())
    except Exception as e:
        print(f"⚠️  Falha inesperada consultando o BACEN: {e}")

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
            cabecalho = [c for c in leitor.fieldnames if c != 'cet']

            for col in ['ltv', 'prazo_maximo']:
                if col not in cabecalho:
                    cabecalho.append(col)

            for linha in leitor:
                banco = linha['banco']
                if novas_taxas and banco in novas_taxas:
                    linha['taxa'] = novas_taxas[banco]

                regra = BANCOS.get(banco, {"ltv": 0.80, "prazo_max": 360})
                linha['ltv'] = round(regra['ltv'] * 100)
                linha['prazo_maximo'] = regra.get('prazo_max', 360)

                # Coluna 'cet' removida (achado da auditoria de set/2026):
                # era escrita aqui com uma fórmula grosseira (taxa + 0,15
                # fixo), mas o gerador.py NUNCA leu essa coluna — o CET de
                # verdade sempre foi recalculado do zero via TIR
                # (calcular_cet_real), que já soma seguros MIP/DFI e taxa
                # de administração. Era dado morto e potencialmente
                # enganoso pra quem abrisse o CSV achando que ali estava
                # o CET real.
                linha.pop('cet', None)
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
                            'ltv': round(regra['ltv'] * 100),
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