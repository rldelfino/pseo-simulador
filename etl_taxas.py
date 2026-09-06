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
FONTE_BACEN_API_DADOS = "https://www.bcb.gov.br/api/servico/sitebcb/historicotaxajurosdiario/atual"
# Endpoint que lista os períodos disponíveis (achado durante a pesquisa
# do produto de veículos, set/2026) — devolve todo período já publicado
# de uma vez, cada um marcado com tipoModalidade "M" (mensal) ou "D"
# (semanal). Usado aqui pra descobrir o período mensal mais recente sem
# precisar adivinhar mês a mês (ver _buscar_bacen_json).
FONTE_BACEN_API_DATAS = "https://www.bcb.gov.br/api/servico/sitebcb/HistoricoTaxaJurosDiario/ConsultaDatas"
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


def _extrair_conteudo_ou_avisar_schema(corpo_json, nome_endpoint):
    """
    Segunda revisão de código (set/2026): antes, ler resp.json().get(
    "conteudo", []) tratava "a chave 'conteudo' não existe mais" (a API
    do BACEN mudou de formato) exatamente igual a "esse período não tem
    dado ainda" — os dois casos silenciosamente viravam lista vazia, sem
    nenhum jeito de diferenciar um do outro nos logs. Isso importa: se a
    API mudar de formato, o ETL ficaria rodando mês após mês achando
    "ainda não publicado" pra sempre, sem nenhum alarme distinto de "a
    integração quebrou de verdade". Aqui, a chave ausente vira um aviso
    🛑 (schema mudou) separado do ⚠️ normal (período vazio) — quem lê o
    log consegue diferenciar os dois na hora.
    """
    if "conteudo" not in corpo_json:
        print(
            f"🛑 BACEN: resposta de {nome_endpoint} mudou de formato — chave 'conteudo' não "
            f"existe (chaves recebidas: {list(corpo_json.keys())}). A API pode ter mudado; "
            f"confira manualmente {FONTE_BACEN_PAGINA_HUMANA}."
        )
        return None
    return corpo_json["conteudo"]


def _buscar_bacen_json(fonte):
    """
    Estratégia de busca pro tipo "bacen_json" em FONTES_TAXA_TIPICA (só
    existe uma entrada desse tipo: o relatório oficial). Retorna
    {banco: {"taxa": float, "fonte": url}}.

    Terceira revisão de código (set/2026): a versão anterior tentava até
    3 meses pra trás às cegas (mês atual, -1, -2), uma requisição HTTP
    bloqueante separada por tentativa — na prática, quase sempre as 2
    primeiras vinham vazias (o mês corrente e o anterior raramente já
    foram publicados) e só a 3ª tinha dado. Cheguei a cogitar juntar tudo
    numa reqisição só trocando o operador do filtro de 'eq' pra 'ge'
    (>=) — TESTEI ao vivo antes de trocar, não troquei às cegas: funciona
    e devolve vários meses de uma vez, só que cada linha da resposta vem
    SEM o campo InicioPeriodo — ganharia velocidade mas perderia a
    certeza de qual mês cada taxa é de verdade (risco real de misturar
    taxa de um mês mais velho sem ninguém perceber). Descartei essa
    opção por esse motivo.

    Em vez disso, uso FONTE_BACEN_API_DATAS (achado durante a pesquisa
    do produto de veículos): ele lista TODOS os períodos já publicados
    numa chamada só, cada um marcado com o tipo (mensal/semanal) — dá
    pra descobrir o período mensal mais recente direto, sem adivinhar, e
    fazer só MAIS UMA chamada pra buscar os dados desse período exato.
    2 requisições sempre, nunca mais — e sem abrir mão de saber
    exatamente de qual mês cada taxa é.
    """
    try:
        resp_datas = requests.get(
            FONTE_BACEN_API_DATAS,
            params={"codigoSegmento": "1", "codigoModalidade": FONTE_BACEN_CODIGO_MODALIDADE},
            headers=_HEADERS, timeout=20,
        )
        resp_datas.raise_for_status()
        corpo_datas = resp_datas.json()
    except (requests.RequestException, ValueError) as e:
        print(f"⚠️  BACEN: falha ao consultar períodos disponíveis: {e}")
        return {}

    periodos = _extrair_conteudo_ou_avisar_schema(corpo_datas, "ConsultaDatas")
    if periodos is None:
        return {}

    periodos_mensais = [p for p in periodos if p.get("tipoModalidade") == "M"]
    if not periodos_mensais:
        print("⚠️  BACEN: nenhum período mensal (tipoModalidade='M') encontrado em ConsultaDatas")
        return {}
    inicio_periodo = periodos_mensais[0]["InicioPeriodo"]  # o mais recente vem primeiro na lista

    filtro = (
        f"(codigoSegmento eq '1') and (codigoModalidade eq '{FONTE_BACEN_CODIGO_MODALIDADE}') "
        f"and (InicioPeriodo eq '{inicio_periodo}')"
    )
    try:
        resp = requests.get(FONTE_BACEN_API_DADOS, params={"filtro": filtro}, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
        corpo = resp.json()
    except (requests.RequestException, ValueError) as e:
        print(f"⚠️  BACEN: falha ao consultar período {inicio_periodo}: {e}")
        return {}

    linhas = _extrair_conteudo_ou_avisar_schema(corpo, "historicotaxajurosdiario/atual")
    if linhas is None:
        return {}
    if not linhas:
        # Raro: ConsultaDatas apontou esse período como publicado, mas
        # veio vazio na busca de verdade. Não insiste — o mês anterior
        # já teria aparecido em ConsultaDatas como o mais recente se
        # fosse esse o caso.
        print(f"⚠️  BACEN: período {inicio_periodo} (apontado por ConsultaDatas) veio vazio — confira {FONTE_BACEN_PAGINA_HUMANA}")
        return {}

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


def _buscar_html_tabela(fonte):
    """
    Estratégia de busca pro tipo "html_tabela" em FONTES_TAXA_TIPICA (as
    fontes de blog): baixa a página e extrai taxa de uma <table> de
    verdade via _extrair_taxa_da_tabela — nunca texto solto (ver
    docstring do módulo, lição do Banco Inter). Retorna
    {banco: {"taxa": float, "fonte": url}}.
    """
    url = fonte["url"]
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"⚠️  Não foi possível acessar {url}: {e}")
        return {}
    try:
        achadas = _extrair_taxa_da_tabela(resp.text, fonte["aliases"])
    except Exception as e:
        print(f"⚠️  Falha ao interpretar a tabela de {url}: {e}")
        return {}
    return {banco: {"taxa": taxa, "fonte": url} for banco, taxa in achadas.items()}


# Primeira revisão de código (set/2026): antes, o BACEN era uma função
# chamada À PARTE, ANTES do loop de FONTES_TAXA_TIPICA — funcionava,
# mas criava uma segunda noção de "prioridade de fonte" fora da lista, e
# a próxima fonte não-HTML que precisasse ser adicionada (ex: uma
# modalidade de home equity, se um dia cobrirmos C6/Bari/Cash Me/
# Daycoval) ia ter que decidir de novo se vira mais um caso especial
# solto no código ou se generaliza a lista. Unificado aqui: cada entrada
# de FONTES_TAXA_TIPICA declara um "tipo", e esta tabela decide qual
# função sabe buscar aquele tipo — adicionar uma fonte nova (de
# qualquer tipo já suportado) é só acrescentar uma entrada na lista.
_ESTRATEGIAS_BUSCA = {
    "bacen_json": _buscar_bacen_json,
    "html_tabela": _buscar_html_tabela,
}


# Lista unificada de fontes, na ordem de prioridade em que são
# consultadas — a primeira que achar um banco "ganha" (ver
# _buscar_taxas_nas_fontes). O BACEN oficial vem primeiro (é a fonte
# regulatória, mais autoritativa) e cobre a maioria dos bancos; as
# fontes de blog abaixo existem só pra preencher quem o BACEN não cobre
# nessa modalidade (hoje: BRB, Poupex). Sicoob/Sicredi/Banrisul também
# aparecem nos aliases das fontes de blog, mas o BACEN já resolve os
# três primeiro — não remover esses três achando que são redundantes:
# são a rede de segurança pro dia em que o casamento de alias do BACEN
# quebrar pra algum deles (ver _normalizar_nome_instituicao) sem que
# ninguém perceba na hora.
#
# Cada entrada declara um "tipo", que _ESTRATEGIAS_BUSCA usa pra saber
# qual função sabe buscar aquele formato de fonte — adicionar uma fonte
# nova (de qualquer tipo já suportado) é só acrescentar uma entrada
# aqui, sem mexer no loop de _buscar_taxas_nas_fontes.
FONTES_TAXA_TIPICA = [
    {
        "tipo": "bacen_json",
    },
    {
        "tipo": "html_tabela",
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
        "tipo": "html_tabela",
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
    Percorre FONTES_TAXA_TIPICA em ordem (BACEN oficial primeiro, depois
    as fontes de blog), despachando cada uma pra sua função de busca via
    _ESTRATEGIAS_BUSCA["tipo"]. Uma fonte que falhar (rede fora do ar,
    HTML/API mudou de estrutura) não derruba as outras — cada uma é
    isolada em try/except aqui em cima, além do try/except interno que
    cada função de busca já tem pros seus próprios passos. Retorna um
    dict {banco: {"taxa": float, "fonte": url}} com tudo que conseguiu,
    de qualquer fonte; a primeira fonte da lista que achar um banco
    "ganha" — as seguintes só preenchem o que ainda falta.
    """
    resultado = {}

    for fonte in FONTES_TAXA_TIPICA:
        buscar = _ESTRATEGIAS_BUSCA[fonte["tipo"]]
        try:
            achadas = buscar(fonte)
        except Exception as e:
            print(f"⚠️  Falha inesperada buscando fonte do tipo '{fonte['tipo']}' ({fonte.get('url', 'BACEN')}): {e}")
            continue

        for banco, dados in achadas.items():
            if banco not in resultado:  # primeira fonte que achar um banco "ganha"
                resultado[banco] = dados

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