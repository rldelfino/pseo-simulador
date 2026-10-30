"""
⚠️  ATENÇÃO — LÓGICA DE CÁLCULO DUPLICADA NESTE ARQUIVO (Python + JS):

As funções calcular_cet_real(), calcular_sac_price() e comparar_todos_bancos()
existem aqui em Python (pra gerar o HTML estático, bom pra SEO/crawlers) E
de novo, reescritas à mão em JavaScript, dentro do <script> gerado mais
abaixo (calcularCET(), calcularTudo(), calcularRankingBancosLive()) — pra
a página recalcular ao vivo quando o usuário mexe nos sliders, sem precisar
recarregar. É uma escolha arquitetural deliberada (estático pra SEO +
interativo pra UX), não um descuido.

O RISCO: qualquer mudança na fórmula de cálculo (nova taxa de seguro, novo
jeito de arredondar, nova regra de negócio) precisa ser replicada NOS DOIS
LUGARES manualmente. Esquecer de atualizar um dos dois é exatamente o tipo
de bug que já aconteceu neste projeto (a "Comparação com o Mercado" ficava
travada no cenário padrão porque só existia em Python). Ao editar qualquer
fórmula de cálculo aqui, sempre procure a função irmã em JavaScript (busque
pelo nome em português/inglês equivalente) e replique a mudança lá também
— e rode tests/test_calculos.py pra travar a versão Python pelo menos.
"""

import os
import csv
import json
import math
import random
from datetime import date, datetime

from bancos import BANCOS, obter_regra, nome_exibicao, corrigir_concordancia, eh_feminino
from icones import icone, tooltip

LINK_FINANCIA_TUDO = "https://app.financiatudo.com.br/financiamento-de-imoveis/chave/8940d282b765cbf97b6df55fd1eb0b52b18b2f6e"
DOMINIO = 'https://simulador.datalabglobal.com'
ARQUIVO_ULTIMA_ATUALIZACAO = 'ultima_atualizacao_taxas.txt'
ARQUIVO_CACHE_TAXAS = 'taxas_cache.json'
# Identidade da empresa por trás do site — mesmo texto já publicado no rodapé
# e no schema Organization do hub (www.datalabglobal.com). Achado de auditoria
# (29/out/2026): os simuladores, que são tema YMYL (dinheiro), não mostravam
# razão social nem CNPJ; o hub mostrava. Texto copiado do hub, não inventado.
EMPRESA_RODAPE = "Satori Soluções Comerciais LTDA · CNPJ 63.998.502/0001-73"

# Prazos (em meses) cujas páginas "banco x valor x prazo" são INDEXÁVEIS.
# Achado real (auditoria de SEO, 29/out/2026, Search Console): 98% das
# impressões do site vinham das páginas de 360 e 420 meses; as ~1.230
# páginas de 120 a 300 meses (4 prazos x 28 valores x 11 bancos) somaram ~40
# impressões. O simulador deixa o usuário trocar o prazo na própria página,
# então uma URL por prazo curto é duplicação. Essas páginas continuam
# existindo e funcionando (links internos, slider), mas saem do sitemap e
# levam <meta robots="noindex,follow">; a demanda por prazo curto passa a ser
# atendida pelas páginas de comparação sem marca (financiamento-imobiliario-
# {valor}-mil-{anos}-anos), que respondem à busca de verdade ("financiar 200
# mil em 20 anos"). Reversível: basta incluir o prazo aqui e regerar.
PRAZOS_INDEXAVEIS = (360, 420)

# Grade das páginas de comparação sem marca de banco.
VALORES_COMPARACAO = tuple(range(150_000, 1_000_001, 50_000))
ANOS_COMPARACAO = (10, 15, 20, 25, 30, 35)
MIN_BANCOS_COMPARACAO = 3  # não gera a página se menos bancos oferecem aquele prazo

_URL_GOOGLE_FONTS = (
    "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700"
    "&family=Inter:wght@300;400;500;600;700&display=swap"
)
# Achado real (13/set/2026, PageSpeed Insights mobile no projeto irmão de
# veículos — mesmo template de <head>, corrigido aqui em paralelo): o
# <link rel="stylesheet"> síncrono pro Google Fonts é o maior item de
# "solicitações que bloqueiam a renderização" (o navegador para de
# renderizar até baixar o CSS de um domínio terceiro). Troca pelo padrão
# "loadCSS" (preload + media=print que vira media=all no onload): carrega
# em paralelo sem bloquear o first paint, com <noscript> como rede de
# segurança pra quem desabilita JS. O onload inline funciona sob o CSP
# do site porque script-src já inclui 'unsafe-inline' (ver paginas_seo/_headers).
GOOGLE_FONTS_LINK_ASSINCRONO = (
    f'<link rel="preload" as="style" href="{_URL_GOOGLE_FONTS}">\n'
    f'    <link rel="stylesheet" href="{_URL_GOOGLE_FONTS}" media="print" onload="this.media=\'all\'">\n'
    f'    <noscript><link rel="stylesheet" href="{_URL_GOOGLE_FONTS}"></noscript>'
)

# URLs PÚBLICAS (canonical/sitemap/links/schema) NUNCA levam ".html" —
# achado real (06/set/2026, Google Search Console: 1,49 mil páginas em
# "Página com redirecionamento", quase o site inteiro). Causa raiz: o
# Cloudflare Pages devolve 308 de "/pagina.html" pra "/pagina" (remove a
# extensão automaticamente) — mas todo canonical/sitemap/link interno
# aqui sempre apontou pra versão COM ".html", a que redireciona. Isso
# criava um ciclo que o Google não conseguia resolver: rastreia a URL do
# sitemap (.html) -> recebe redirect -> chega na versão sem extensão ->
# essa página diz que o canonical de verdade é a URL com ".html" (a que
# acabou de redirecionar pra cá) -> Google não indexa nenhuma das duas
# com confiança.
#
# Os ARQUIVOS no disco continuam terminando em .html (é isso que diz pro
# Cloudflare "isto é HTML, pode servir e fazer o auto-redirect") — só as
# URLs que este arquivo CONSTRÓI (canonical, sitemap, JSON-LD, <a href>)
# é que não levam mais a extensão, pra bater exatamente com o que o
# Cloudflare serve como resposta final (200), sem nenhum salto no meio.

def _banco_tem_taxa_bacen(banco):
    """True só se a taxa gravada pelo ETL para este banco veio de fato do
    BACEN (url da fonte no taxas_cache.json contém bcb.gov.br).

    Achado real (auditoria de SEO, 29/out/2026): o rodapé de TODA página
    dizia "Fonte: Banco Central do Brasil (BACEN)", mas o relatório do ETL
    mostra que o BRB vem de um artigo de blog e a Poupex nem tem fonte
    (usa o taxa_padrao estático de bancos.py). Num tema YMYL (dinheiro),
    atribuir ao BACEN um número que não é do BACEN é o tipo de afirmação
    imprecisa que derruba confiança (E-E-A-T) e pode ser lida como
    publicidade enganosa. Sem o cache (ou sem entrada pro banco), assume
    "não é BACEN" — o erro seguro é subatribuir, nunca superatribuir."""
    try:
        with open(ARQUIVO_CACHE_TAXAS, encoding='utf-8') as f:
            cache = json.load(f)
    except (FileNotFoundError, ValueError):
        return False
    return 'bcb.gov.br' in str(cache.get(banco, {}).get('fonte', ''))


def texto_fonte_taxa(banco=None):
    """Texto de fonte exibido no rodapé do cabeçalho das páginas.
    banco=None -> página que cobre todos os bancos (home/comparador)."""
    if banco is not None:
        if _banco_tem_taxa_bacen(banco):
            return "Fonte: Banco Central do Brasil (BACEN)"
        return "Taxa estimada com base em referências públicas de mercado — não é taxa oficial do BACEN"
    fora = [nome_exibicao(b) for b in BANCOS if not _banco_tem_taxa_bacen(b)]
    if not fora:
        return "Fonte: Banco Central do Brasil (BACEN)"
    lista = fora[0] if len(fora) == 1 else ", ".join(fora[:-1]) + " e " + fora[-1]
    return f"Fonte: Banco Central do Brasil (BACEN), exceto {lista}, com taxa estimada de referências públicas de mercado"


def taxas_atuais_de(links_por_banco):
    """Extrai {banco: taxa_atual_float} a partir da própria grade de
    páginas já lida do dados.csv — ou seja, a taxa que o etl_taxas.py
    (BACEN/blog) de fato gravou na última atualização, não o
    'taxa_padrao' estático de bancos.py.

    Achado real (06/set/2026, print do Rodolfo): a página-hub, o
    comparador-bancos.html e a caixinha "Comparação com o Mercado"
    (tanto a versão estática quanto a versão ao vivo em JS) usavam
    regra_banco['taxa_padrao'] direto de bancos.py em vez da taxa
    recém-atualizada pelo ETL — então rodar o ETL atualizava a parcela
    da página de simulação individual, mas o resumo do banco e o
    ranking entre bancos continuavam com a taxa antiga. bancos.py
    continua sendo a fonte de LTV/prazo_max (o ETL só re-deriva esses
    dois de lá, nunca busca eles de fonte externa) — só a taxa muda de
    fonte aqui."""
    taxas = {}
    for banco, links in links_por_banco.items():
        if not links:
            continue
        try:
            # Mesmo parsing defensivo usado pra página individual mais
            # abaixo neste arquivo: se por acaso a coluna taxa guardar uma
            # taxa mensal por engano (valor bem abaixo de 4%, implausível
            # pra taxa anual de financiamento imobiliário), converte pra
            # anual em vez de exibir o número mensal como se fosse anual.
            taxa = float(str(links[0]["linha_original"]["taxa"]).replace(",", "."))
            if taxa < 4.0:
                taxa = ((1 + (taxa / 100)) ** 12 - 1) * 100
            taxas[banco] = round(taxa, 2)
        except (KeyError, ValueError, TypeError):
            continue
    return taxas


def construir_bancos_json(taxas_atuais):
    """Matriz dos bancos, compacta, embutida em toda página de simulação
    como JS — usada pela caixinha "Comparação com o Mercado" pra
    recalcular o ranking AO VIVO quando o visitante mexe nos sliders
    (antes, o ranking era só uma foto estática do cenário padrão da
    página, e ficava "errado" assim que o usuário mudava valor/prazo —
    bug relatado pelo Rodolfo). taxas_atuais (ver taxas_atuais_de) tem
    prioridade sobre o taxa_padrao estático de bancos.py, pelo mesmo
    motivo documentado ali."""
    return json.dumps([
        {"chave": chave, "nome": dados["nome_exibicao"],
         "taxa": taxas_atuais.get(chave, dados["taxa_padrao"]),
         "ltv": dados["ltv"], "prazoMax": dados["prazo_max"],
         "fem": eh_feminino(chave)}
        for chave, dados in BANCOS.items()
    ], ensure_ascii=False)

# ajustarTooltips() (corrige o balão de tooltip perto da borda da tela)
# vivia aqui como SCRIPT_AJUSTA_TOOLTIPS, interpolado à mão em cada
# template. Achado real (13/set/2026, débito técnico resolvido junto do
# JS duplicado — ver gerar_calculo_js()): a função foi movida pra dentro
# de calculo.js, o mesmo arquivo externo cacheável que agora concentra
# todo o JS compartilhado do site. O comentário original da correção
# (06/set/2026, overflow de tooltip em mobile) sobrevive dentro do JS
# gerado, não foi perdido.


def render_head_boilerplate(titulo_pagina, meta_description, url_canonica, dominio, json_ld_blocos, meta_keywords=None, titulo_social=None, robots=None):
    """Bloco <head> compartilhado (charset/viewport/OG/Twitter Card/
    stylesheets) — extraído em set/2026 (auditoria pedida pelo
    Rodolfo) porque estava colado quase idêntico em 4 funções geradoras
    diferentes (gerar_paginas_pseo, gerar_hub_bancos,
    gerar_comparador_bancos, gerar_index_home), ~40 linhas cada, e
    divergindo entre si sem motivo (só a página de simulação tinha
    dns-prefetch e twitter:title/description/image completos — as
    outras três tinham só twitter:card). Padronizado aqui pra versão
    mais completa em toda página, não só a de simulação.

    titulo_social: og:title/twitter:title, se precisar ser diferente do
    <title> (ex: a home tinha um og:title deliberadamente mais curto que
    o <title> antes desta função existir — sem esse parâmetro, o refactor
    tinha silenciosamente igualado os dois). Default: usa titulo_pagina.

    json_ld_blocos: lista de strings já formatadas (cada uma o CONTEÚDO
    de um bloco JSON-LD, sem as tags <script>) — mantém o mesmo formato
    "f-string com chaves escapadas" que o resto do arquivo já usa pros
    schemas, pra não precisar reescrever schema_faq/schema_breadcrumb/etc
    de uma vez."""
    titulo_social = titulo_social or titulo_pagina
    # Achado real (21/set/2026, auditoria de SEO das ~1.700 páginas): home,
    # /sobre, comparador e os artigos de /aprenda saíam com <title> de
    # 63-73 caracteres e meta description de 175-183 — o Google corta em
    # ~60 e ~160, e o corte cai no meio da frase. Aparar aqui (função
    # compartilhada por todo template) em vez de página por página: a
    # marca sai do title só quando não cabe, e a description corta na
    # última palavra inteira.
    if len(titulo_pagina) > 60 and titulo_pagina.endswith(" | Datalab Global"):
        titulo_pagina = titulo_pagina[: -len(" | Datalab Global")]
    if len(meta_description) > 160:
        meta_description = meta_description[:157].rsplit(" ", 1)[0].rstrip(" ,;:—-") + "…"
    scripts_json_ld = "\n".join(
        f'    <script type="application/ld+json">\n    {bloco}\n    </script>'
        for bloco in json_ld_blocos
    )
    # Lista de linhas em vez de montar a linha opcional de keywords com um
    # \n embutido à mão (achado da auditoria: só essa linha precisava do
    # \n manual, diferente de todas as outras — frágil pra reformatar).
    linhas_topo = [
        '    <meta charset="UTF-8">',
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f'    <title>{titulo_pagina}</title>',
        f'    <meta name="description" content="{meta_description}">',
        f'    <meta name="robots" content="{robots}">' if robots else None,
        f'    <meta name="keywords" content="{meta_keywords}">' if meta_keywords else None,
        f'    <link rel="canonical" href="{url_canonica}" />',
        # Achado real (06/set/2026, print do usuário comparando nosso
        # resultado de busca com o de um concorrente): o site nunca teve
        # NENHUM <link rel="icon">, então o Google mostrava o domínio cru
        # (datalabglobal.com) com um ícone genérico em vez do nome
        # amigável ("Datalab Global", que o og:site_name abaixo já
        # declarava) + o ícone da marca. SVG primeiro (nítido em qualquer
        # tamanho, suportado por todo navegador atual e pelo Google);
        # .ico depois como fallback pra crawler/navegador antigo que não
        # entende favicon SVG (ver gerar_favicon_svg/rasterizar_favicon_png).
        # Sem "/" na frente (igual a href="logo.svg"/"styles.css" já
        # usados no resto do <head>): o site inteiro é flat (nenhuma
        # página mora em subpasta), então o relativo resolve certo pra
        # raiz a partir de qualquer URL — manter a mesma convenção em
        # vez de introduzir um caminho absoluto isolado.
        '    <link rel="icon" href="favicon.ico?v=20261012" sizes="any">',
        '    <link rel="icon" href="favicon-32.png?v=20261012" type="image/png" sizes="32x32">',
        '    <link rel="icon" href="favicon-192.png?v=20261012" type="image/png" sizes="192x192">',
        '    <link rel="apple-touch-icon" href="apple-touch-icon.png?v=20261012">',
    ]
    linhas_topo_html = "\n".join(l for l in linhas_topo if l is not None)
    return f'''{linhas_topo_html}

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

    <meta property="og:type" content="website">
    <meta property="og:locale" content="pt_BR">
    <meta property="og:site_name" content="Datalab Global">
    <meta property="og:title" content="{titulo_social}">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:url" content="{url_canonica}">
    <meta property="og:image" content="{dominio}/og-image.png">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{titulo_social}">
    <meta name="twitter:description" content="{meta_description}">
    <meta name="twitter:image" content="{dominio}/og-image.png">

    <link rel="stylesheet" href="styles.css">
    {GOOGLE_FONTS_LINK_ASSINCRONO}

{scripts_json_ld}'''


def obter_data_ultima_atualizacao():
    """Lê a data real da última vez que as taxas mudaram (gravada pelo
    etl_taxas.py). Usar isso (em vez de 'hoje' a cada build) no <lastmod>
    do sitemap e no dateModified do schema é o que o Google espera como
    sinal de frescor honesto — 'lastmod sempre = data do deploy' é tratado
    como sinal de frescor falso."""
    try:
        with open(ARQUIVO_ULTIMA_ATUALIZACAO, encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return date.today().isoformat()


def calcular_cet_real(valor_financiado, prazo_meses, taxa_anual, valor_imovel, sistema='SAC'):
    """Calcula o CET (Custo Efetivo Total) de verdade, via TIR (Taxa Interna
    de Retorno) do fluxo de caixa completo do financiamento — não apenas
    'taxa + uma margem fixa' (aproximação grosseira que o site usava antes).

    Isso inclui os custos que a taxa de juros sozinha não mostra:
    - Seguro MIP (Morte e Invalidez Permanente): incide sobre o saldo
      devedor a cada mês.
    - Seguro DFI (Danos Físicos ao Imóvel): incide sobre o valor do imóvel,
      fixo do início ao fim.
    - Taxa de administração mensal (tarifa de manutenção da conta do
      financiamento).

    As alíquotas de seguro usadas são estimativas conservadoras de mercado
    (variam por banco/idade/seguradora e não são públicas de forma
    padronizada) — o objetivo aqui não é replicar o CET exato que o banco
    vai apresentar na proposta, e sim mostrar um número muito mais realista
    do que "taxa de juros anunciada + 0,15 p.p." para efeito de comparação.
    """
    if valor_financiado <= 0 or prazo_meses <= 0:
        return 0.0

    taxa_mensal = (taxa_anual / 100) / 12
    TAXA_MIP_MENSAL = 0.00030    # ~0,030% do saldo devedor/mês
    TAXA_DFI_MENSAL = 0.000129   # ~0,0129% do valor do imóvel/mês
    TAXA_ADMIN_MENSAL = 25.00    # R$ 25,00/mês (valor típico de mercado)

    saldo = valor_financiado
    pmt_price = 0.0
    if sistema == 'PRICE':
        if taxa_mensal > 0:
            pmt_price = valor_financiado * (taxa_mensal * (1 + taxa_mensal) ** prazo_meses) / ((1 + taxa_mensal) ** prazo_meses - 1)
        else:
            pmt_price = valor_financiado / prazo_meses

    fluxo = []
    for _ in range(prazo_meses):
        juros = saldo * taxa_mensal
        amortizacao = (valor_financiado / prazo_meses) if sistema == 'SAC' else (pmt_price - juros)
        seguro_mip = saldo * TAXA_MIP_MENSAL
        seguro_dfi = valor_imovel * TAXA_DFI_MENSAL
        fluxo.append(amortizacao + juros + seguro_mip + seguro_dfi + TAXA_ADMIN_MENSAL)
        saldo -= amortizacao

    def vpl(r):
        total = -valor_financiado
        for i, cf in enumerate(fluxo, start=1):
            total += cf / ((1 + r) ** i)
        return total

    # Busca por bisseção: a TIR mensal de um financiamento imobiliário real
    # está com folga dentro da faixa de 0% a 5% ao mês.
    lo, hi = 0.0, 0.05
    for _ in range(60):
        mid = (lo + hi) / 2
        if vpl(mid) > 0:
            lo = mid
        else:
            hi = mid
    tir_mensal = (lo + hi) / 2
    return round(((1 + tir_mensal) ** 12 - 1) * 100, 2)


def calcular_sac_price(valor_financiado, prazo_meses, taxa_anual, valor_imovel=None):
    """Réplica em Python (server-side) do mesmo cálculo SAC/PRICE que roda
    em JS no navegador, para o cenário padrão de cada página. O resultado
    vira texto estático no HTML — visível sem JS, e principalmente: são
    NÚMEROS REAIS e únicos por página (não apenas troca de variável em
    texto template), que é exatamente o que a política de conteúdo
    programático do Google pede pra diferenciar página de verdade de
    template raso."""
    taxa_mensal = (taxa_anual / 100) / 12

    saldo = valor_financiado
    juros_total_sac = 0.0
    amortizacao = valor_financiado / prazo_meses
    p1_sac = pU_sac = 0.0
    for m in range(1, prazo_meses + 1):
        juros = saldo * taxa_mensal
        juros_total_sac += juros
        parcela = amortizacao + juros
        if m == 1:
            p1_sac = parcela
        if m == prazo_meses:
            pU_sac = parcela
        saldo -= amortizacao

    if taxa_mensal > 0:
        pmt_price = valor_financiado * (taxa_mensal * (1 + taxa_mensal) ** prazo_meses) / ((1 + taxa_mensal) ** prazo_meses - 1)
    else:
        pmt_price = valor_financiado / prazo_meses
    juros_total_price = (pmt_price * prazo_meses) - valor_financiado

    resultado = {
        "p1_sac": p1_sac, "pU_sac": pU_sac, "total_sac": valor_financiado + juros_total_sac,
        "p1_price": pmt_price, "pU_price": pmt_price, "total_price": valor_financiado + juros_total_price,
        "economia_sac": juros_total_price - juros_total_sac,
    }

    if valor_imovel:
        resultado["cet_sac"] = calcular_cet_real(valor_financiado, prazo_meses, taxa_anual, valor_imovel, 'SAC')
        resultado["cet_price"] = calcular_cet_real(valor_financiado, prazo_meses, taxa_anual, valor_imovel, 'PRICE')
        # Renda familiar bruta sugerida: os bancos não aprovam financiamentos
        # cuja parcela ultrapasse ~30% da renda bruta mensal (regra de
        # comprometimento de renda). Arredondado pra cima, pro R$ 50 mais
        # próximo, porque é uma sugestão de "piso", não um valor exato.
        resultado["renda_sugerida"] = math.ceil((p1_sac / 0.30) / 50) * 50

    return resultado


def comparar_todos_bancos(valor_imovel, prazo_alvo, lookup_paginas, taxas_atuais=None):
    """Compara o CET (sistema SAC) de TODOS os bancos cadastrados para o
    mesmo valor de imóvel, usando o prazo mais próximo do desejado que cada
    banco permite e a ENTRADA MÍNIMA exigida por cada um (regra de LTV
    própria) — não a entrada configurada no banco que está sendo exibido
    nesta página. É a base da caixinha "Comparação com o Mercado": qual
    banco teria o menor CET nas mesmas condições de imóvel/prazo.

    taxas_atuais (opcional, ver taxas_atuais_de): quando informado, usa a
    taxa que o etl_taxas.py de fato gravou por último em dados.csv em vez
    do taxa_padrao estático de bancos.py — sem isso, o ranking entre
    bancos ficava desatualizado mesmo depois do ETL rodar (achado real,
    06/set/2026). Sem taxas_atuais, cai de volta pro estático (mantém
    chamadas antigas/testes funcionando sem precisar passar o parâmetro).

    Retorna a lista ordenada por CET (menor primeiro)."""
    resultados = []
    for nome_banco, regra_banco in BANCOS.items():
        taxa_banco = (taxas_atuais or {}).get(nome_banco, regra_banco["taxa_padrao"])
        prazo_b = min(prazo_alvo, regra_banco["prazo_max"])
        entrada_b = valor_imovel * (1 - regra_banco["ltv"])
        vfinanciado_b = valor_imovel - entrada_b
        if vfinanciado_b <= 0:
            continue
        cet_b = calcular_cet_real(vfinanciado_b, prazo_b, taxa_banco, valor_imovel, 'SAC')
        slug_b = lookup_paginas.get((nome_banco, valor_imovel, prazo_b))
        resultados.append({
            "banco": nome_banco,
            "banco_exib": nome_exibicao(nome_banco),
            "cet": cet_b,
            "prazo": prazo_b,
            "entrada_perc": round((1 - regra_banco["ltv"]) * 100),
            "slug": slug_b,
        })
    resultados.sort(key=lambda r: r["cet"])
    return resultados


def calcular_marcador_posicao_mercado(ranking_ordenado, banco):
    """Posição (0-100) do marcador nas barras "Faixa/Posição no Mercado":
    interpolação linear do CET real deste banco contra o mínimo/máximo
    real da faixa (valor, não ranking).

    Achado real (07/set/2026, pedido explícito do usuário no projeto
    irmão, aplicado aqui pra manter os dois consistentes): uma versão
    anterior desta função usava fração do ranking (índice/(n-1)) — cada
    marcador ficava igualmente espaçado dos vizinhos, independente da
    distância real entre as taxas, "parece uma fila indiana" (palavras
    do usuário). Isso resolvia um problema (outlier isolado esticando a
    régua e comprimindo o resto perto do centro — ver histórico de
    04-06/set/2026 se precisar do caso do Banco Inter), mas criava outro
    pior: nenhuma noção real de o quanto os bancos se aproximam ou se
    distanciam uns dos outros. Voltado pra escala de valor: dois bancos
    com CET bem próximo aparecem próximos no marcador; um banco isolado
    longe dos outros aparece isolado — a informação que "Posição no
    Mercado" deveria mostrar.

    ranking_ordenado precisa já estar ordenado por CET crescente (é o
    retorno de comparar_todos_bancos) e cada item precisa ter a chave
    "cet". Se o banco não aparece na lista (não deveria acontecer, mas
    defensivamente) ou a lista tem 0-1 elemento, cai no centro (50%) em
    vez de quebrar."""
    if len(ranking_ordenado) <= 1:
        return 50
    entrada = next((r for r in ranking_ordenado if r["banco"] == banco), None)
    if entrada is None:
        return 50
    cet_min, cet_max = ranking_ordenado[0]["cet"], ranking_ordenado[-1]["cet"]
    spread = cet_max - cet_min
    marcador_pct = round(((entrada["cet"] - cet_min) / spread) * 100) if spread > 0 else 50
    return max(2, min(98, marcador_pct))  # nunca cola nas bordas (marcador cortado)


def svg_donut_capital_juros(capital, juros):
    """Gráfico donut SVG puro (sem lib externa) mostrando a proporção
    Capital vs Juros do custo total — visualização de dado real em vez de
    só números em caixinha de texto."""
    total = capital + juros
    if total <= 0:
        return ""
    pct_capital = capital / total
    r = 42
    circ = 2 * 3.14159265 * r
    dash_capital = pct_capital * circ
    dash_juros = circ - dash_capital
    pct_juros_label = round((1 - pct_capital) * 100)
    return f'''<div class="flex items-center gap-6">
        <svg viewBox="0 0 100 100" class="w-24 h-24 shrink-0" style="transform: rotate(-90deg)">
            <circle cx="50" cy="50" r="{r}" fill="none" stroke="#1e293b" stroke-width="12"></circle>
            <circle cx="50" cy="50" r="{r}" fill="none" stroke="#10b981" stroke-width="12"
                    stroke-dasharray="{dash_capital:.2f} {circ:.2f}" stroke-linecap="round"></circle>
            <circle cx="50" cy="50" r="{r}" fill="none" stroke="#f59e0b" stroke-width="12"
                    stroke-dasharray="{dash_juros:.2f} {circ:.2f}" stroke-dashoffset="-{dash_capital:.2f}" stroke-linecap="round"></circle>
        </svg>
        <div class="space-y-2 text-xs">
            <div class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0"></span><span class="text-slate-400">Capital</span><span class="text-white font-medium ml-auto">{100 - pct_juros_label}%</span></div>
            <div class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0"></span><span class="text-slate-400">Juros</span><span class="text-white font-medium ml-auto">{pct_juros_label}%</span></div>
        </div>
    </div>'''


def favicon_com_fallback(url_logo, banco_exib, classe_tamanho="w-7 h-7"):
    """<img> do favicon do banco com fallback silencioso: se o serviço
    externo de favicons falhar pra algum domínio (ex: Poupex), o onerror
    esconde a imagem quebrada via classe CSS e revela um ícone de banco
    genérico ao lado (ver .favicon-img/.favicon-fallback no input.css)."""
    return f'''<span class="relative inline-flex items-center justify-center {classe_tamanho} shrink-0">
        <img src="{url_logo}" alt="Logo {banco_exib}" width="28" height="28" loading="lazy"
             class="favicon-img {classe_tamanho} rounded object-contain"
             onerror="this.classList.add('favicon-erro')">
        <span class="favicon-fallback {classe_tamanho} rounded bg-white/10 text-emerald-400 items-center justify-center absolute inset-0">{icone('bank')}</span>
    </span>'''
LINK_WHATSAPP_SUPORTE = "https://wa.me/5527995051571?text=Ol%C3%A1%2C%20preciso%20de%20ajuda%20com%20o%20simulador"


def criar_csv_exemplo(caminho_csv):
    cabecalho = ['banco', 'valor_imovel', 'taxa', 'prazo', 'slug']
    dados = [['Caixa', '300000', '11.49', '420', 'simulador-caixa-300-mil-420-meses']]
    with open(caminho_csv, mode='w', newline='', encoding='utf-8') as arquivo:
        writer = csv.writer(arquivo, delimiter=';')
        writer.writerow(cabecalho)
        writer.writerows(dados)


def gerar_logo_svg(pasta_saida):
    svg_transparente = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 200" width="100%" height="100%">
    <defs>
        <linearGradient id="emeraldGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#34d399" /><stop offset="100%" stop-color="#047857" /></linearGradient>
        <linearGradient id="emeraldDark" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#059669" /><stop offset="100%" stop-color="#022c22" /></linearGradient>
        <filter id="glowMedium" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3.5" result="blur" /><feComposite in="SourceGraphic" in2="blur" operator="over" /></filter>
    </defs>
    <g transform="translate(60, 50)">
        <g opacity="0.8">
            <ellipse cx="40" cy="40" rx="78" ry="44" fill="none" stroke="#34d399" stroke-width="1" stroke-dasharray="8 8" opacity="0.3"/>
            <ellipse cx="40" cy="40" rx="64" ry="36" fill="none" stroke="#059669" stroke-width="1" opacity="0.4"/>
            <ellipse cx="40" cy="40" rx="78" ry="44" fill="none" stroke="#fef08a" stroke-width="1.8" stroke-dasharray="35 300" stroke-dashoffset="15" stroke-linecap="round" filter="url(#glowMedium)" opacity="0.8"/>
            <circle cx="118" cy="40" r="2.5" fill="#fef08a" filter="url(#glowMedium)"/><circle cx="118" cy="40" r="1" fill="#ffffff"/><circle cx="-38" cy="40" r="2.5" fill="#34d399" filter="url(#glowMedium)"/><circle cx="70" cy="-2" r="1.5" fill="#ffffff" opacity="0.6"/>
        </g>
        <path d="M 40 80 L 40 40 L 5 20 L 5 60 Z" fill="url(#emeraldDark)" opacity="0.85"/><path d="M 40 80 L 40 40 L 75 20 L 75 60 Z" fill="#064e3b" opacity="0.9"/><path d="M 40 40 L 75 20 L 40 0 L 5 20 Z" fill="url(#emeraldGrad)"/>
        <line x1="40" y1="40" x2="40" y2="80" stroke="#022c22" stroke-width="1.5" /><line x1="40" y1="40" x2="5" y2="20" stroke="#34d399" stroke-width="1" opacity="0.5" /><line x1="40" y1="40" x2="75" y2="20" stroke="#34d399" stroke-width="1" opacity="0.5" />
        <line x1="40" y1="0" x2="5" y2="20" stroke="#fef08a" stroke-width="2" filter="url(#glowMedium)"/><line x1="40" y1="0" x2="75" y2="20" stroke="#fef08a" stroke-width="2" filter="url(#glowMedium)"/><line x1="40" y1="0" x2="40" y2="40" stroke="#fef08a" stroke-width="2.5" filter="url(#glowMedium)"/><line x1="5" y1="20" x2="40" y2="40" stroke="#10b981" stroke-width="1.5" /><line x1="75" y1="20" x2="40" y2="40" stroke="#10b981" stroke-width="1.5" />
        <circle cx="40" cy="0" r="4.5" fill="#fef08a" filter="url(#glowMedium)"/><circle cx="40" cy="0" r="2" fill="#ffffff"/><circle cx="5" cy="20" r="3.5" fill="#34d399" filter="url(#glowMedium)"/><circle cx="75" cy="20" r="3.5" fill="#34d399" filter="url(#glowMedium)"/><circle cx="40" cy="40" r="4.5" fill="#fef08a" filter="url(#glowMedium)"/><circle cx="40" cy="40" r="2" fill="#ffffff"/><circle cx="40" cy="80" r="3" fill="#059669"/>
    </g>
    <text x="185" y="105" font-family="'Playfair Display', Georgia, serif" font-size="64" font-weight="700" fill="#ffffff">Datalab</text>
    <text x="190" y="145" font-family="'Inter', system-ui, sans-serif" font-size="20" font-weight="600" fill="#10b981" letter-spacing="14">GLOBAL</text>
    <circle cx="375" cy="139" r="2.5" fill="#fef08a" filter="url(#glowMedium)"/>
</svg>"""
    with open(os.path.join(pasta_saida, 'logo.svg'), "w", encoding="utf-8") as f:
        f.write(svg_transparente)


def gerar_favicon_svg(pasta_saida):
    """Ícone quadrado (só o cubo/losango, sem o texto "Datalab" + "GLOBAL"
    de logo.svg) pra usar como favicon — achado real (06/set/2026, print
    do usuário comparando o resultado de busca do nosso site com o de um
    concorrente): o site nunca teve NENHUM <link rel="icon">, então o
    Google mostrava o domínio cru (datalabglobal.com) com um ícone
    genérico em vez do nome amigável + ícone da marca, do jeito que
    outros sites bem indexados aparecem.

    Reaproveita exatamente as mesmas cores/gradientes/formas do cubo de
    gerar_logo_svg (é o mesmo ícone da marca, só recortado pra um
    viewBox quadrado e sem o texto) — não é um ícone novo, é o mesmo
    elemento visual que já aparece no cabeçalho de toda página, só que
    isolado pra caber num favicon pequeno. As elipses decorativas
    (órbita tracejada bem fina, baixa opacidade) do logo.svg foram
    deixadas de fora aqui de propósito: em 16-32px elas viram ruído
    ilegível, então o favicon usa só o cubo sólido + os pontos
    brilhantes nos vértices, que continuam reconhecíveis em tamanho
    pequeno.

    Gera tanto o .svg (favicon moderno, nítido em qualquer resolução,
    suportado por todo navegador atual e pelo Google) quanto, via
    rasterizar_favicon_png (chamada por quem invoca esta função), os
    fallbacks .ico/.png pra compatibilidade ampla."""
    # Duas simplificações em relação ao ícone de logo.svg, cada uma por
    # um motivo diferente e testado ao vivo, não suposição:
    #
    # 1. Sem filter="url(#glowMedium)" (glow via feGaussianBlur): um
    #    blur suave some visualmente num ícone de 16-48px, só vira
    #    ruído nesse tamanho — puramente uma escolha de legibilidade.
    #
    # 2. Cores SÓLIDAS em vez de linearGradient nas faces do cubo: essa
    #    troca não é escolha de design, é uma limitação real da
    #    biblioteca de rasterização (svglib 2.2.0 + reportlab 5 com
    #    backend rlPyCairo, usada por rasterizar_favicon_png pra gerar
    #    o .ico/.png a partir deste .svg): path com fill="url(#gradiente)"
    #    quebra a conversão (AttributeError: 'NoneType' object has no
    #    attribute 'moveTo' em svglib._shape_to_pdf_path), MESMO sem
    #    opacity e MESMO com um SVG minimalista de 1 path — isolei o
    #    bug testando incrementalmente (retângulo simples OK, gradiente
    #    sozinho quebra, fill sólido com opacity OK). Como não tem
    #    workaround simples na versão atual da lib, troquei os 2
    #    gradientes por 3 tons sólidos de emerald que preservam a
    #    mesma ilusão de cubo isométrico (topo claro, lateral esquerda
    #    média, lateral direita escura) sem depender de gradiente.
    svg_favicon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="-10 -10 100 100" width="100%" height="100%">
    <rect x="-10" y="-10" width="100" height="100" fill="#022c22"/>
    <path d="M 40 80 L 40 40 L 5 20 L 5 60 Z" fill="#065f46" opacity="0.85"/><path d="M 40 80 L 40 40 L 75 20 L 75 60 Z" fill="#064e3b" opacity="0.9"/><path d="M 40 40 L 75 20 L 40 0 L 5 20 Z" fill="#34d399"/>
    <line x1="40" y1="40" x2="40" y2="80" stroke="#022c22" stroke-width="1.5" /><line x1="40" y1="40" x2="5" y2="20" stroke="#34d399" stroke-width="1" opacity="0.5" /><line x1="40" y1="40" x2="75" y2="20" stroke="#34d399" stroke-width="1" opacity="0.5" />
    <line x1="40" y1="0" x2="5" y2="20" stroke="#fef08a" stroke-width="2"/><line x1="40" y1="0" x2="75" y2="20" stroke="#fef08a" stroke-width="2"/><line x1="40" y1="0" x2="40" y2="40" stroke="#fef08a" stroke-width="2.5"/><line x1="5" y1="20" x2="40" y2="40" stroke="#10b981" stroke-width="1.5" /><line x1="75" y1="20" x2="40" y2="40" stroke="#10b981" stroke-width="1.5" />
    <circle cx="40" cy="0" r="4.5" fill="#fef08a"/><circle cx="40" cy="0" r="2" fill="#ffffff"/><circle cx="5" cy="20" r="3.5" fill="#34d399"/><circle cx="75" cy="20" r="3.5" fill="#34d399"/><circle cx="40" cy="40" r="4.5" fill="#fef08a"/><circle cx="40" cy="40" r="2" fill="#ffffff"/><circle cx="40" cy="80" r="3" fill="#059669"/>
</svg>"""
    with open(os.path.join(pasta_saida, 'favicon.svg'), "w", encoding="utf-8") as f:
        f.write(svg_favicon)
    return svg_favicon


def rasterizar_favicon_png(pasta_saida):
    """Converte favicon.svg em PNG/ICO — fallback pra navegadores/crawlers
    antigos que não entendem favicon SVG (o link rel="icon" no <head>
    declara os dois, moderno primeiro). Usa svglib+reportlab (Python
    puro, sem depender de libs nativas tipo Cairo — que são um problema
    conhecido de instalar no Windows) só nesta função de build; não é
    dependência do site em si, só da geração.

    Gera:
      - favicon.ico (16/32/48px combinados — o formato mais compatível
        que existe, ainda o mínimo esperado por navegadores/crawlers
        muito antigos)
      - apple-touch-icon.png (180x180 — tamanho recomendado pela Apple
        pra ícone de atalho na tela inicial do iOS/Android)
      - logo-schema.png (512x512 — usado como "logo" no schema.org
        Organization; o Google recomenda uma imagem raster real, não
        SVG, com no mínimo 112x112px, pra aparecer no card de marca da
        busca)

    Se as libs de rasterização não estiverem instaladas, avisa e segue
    sem quebrar a geração (o favicon.svg sozinho já cobre navegador
    moderno + Google, que suporta SVG — o .ico/.png são reforço de
    compatibilidade, não bloqueio)."""
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
    except ImportError:
        print("⚠️  svglib/reportlab não instalados — pulando favicon.ico/apple-touch-icon.png (favicon.svg sozinho já funciona em navegador moderno e no Google, mas sem fallback pra crawler antigo). Rode: pip install svglib reportlab")
        return

    caminho_svg = os.path.join(pasta_saida, 'favicon.svg')

    def _renderizar_png(tamanho_px, caminho_saida):
        # Recarrega o SVG do zero a cada tamanho, em vez de reaproveitar
        # um único Drawing com scale()/scale(1/fator) pra "desfazer" —
        # essa abordagem parecia mais eficiente, mas Group.scale() do
        # reportlab EMPILHA a transformação em vez de substituí-la, e a
        # sequência scale/unscale repetida corrompia o estado interno de
        # clip-path do Drawing (achado real: quebrava com
        # "AttributeError: 'NoneType' object has no attribute 'moveTo'"
        # em _shape_to_pdf_path, mesmo depois de eu já ter descartado a
        # hipótese inicial de que o culpado fosse o filter="url(#glow)").
        # Recarregar do zero é mais lento (reparseia o SVG 5x), mas o
        # favicon só é gerado 1x por build do site inteiro — custo
        # irrelevante — e elimina a classe de bug por completo.
        desenho = svg2rlg(caminho_svg)
        fator = tamanho_px / desenho.width  # svg2rlg lê o viewBox (100x100) como width/height
        desenho.width = desenho.height = tamanho_px
        desenho.scale(fator, fator)
        renderPM.drawToFile(desenho, caminho_saida, fmt="PNG", bg=0x022c22)

    caminho_180 = os.path.join(pasta_saida, 'apple-touch-icon.png')
    caminho_512 = os.path.join(pasta_saida, 'logo-schema.png')
    _renderizar_png(180, caminho_180)
    _renderizar_png(512, caminho_512)

    from PIL import Image
    tamanhos_ico = [16, 32, 48]
    caminhos_tmp = []
    for tamanho in tamanhos_ico:
        caminho_tmp = os.path.join(pasta_saida, f'_favicon_tmp_{tamanho}.png')
        _renderizar_png(tamanho, caminho_tmp)
        caminhos_tmp.append(caminho_tmp)
    # .load() força o PIL a ler todos os pixels agora (em vez de leitura
    # preguiçosa do arquivo) e fecha o handle do arquivo em seguida —
    # sem isso, o Windows recusa o os.remove() logo abaixo com
    # PermissionError ("arquivo já está sendo usado por outro processo"),
    # porque o .save() do ICO ainda tinha os PNGs temporários abertos.
    imagens = []
    for c in caminhos_tmp:
        img = Image.open(c)
        img.load()
        imagens.append(img)
    imagens[0].save(
        os.path.join(pasta_saida, 'favicon.ico'),
        format='ICO',
        sizes=[(t, t) for t in tamanhos_ico],
        append_images=imagens[1:],
    )
    for c in caminhos_tmp:
        os.remove(c)
    print("✅ favicon.ico, apple-touch-icon.png e logo-schema.png gerados a partir de favicon.svg.")


def formatar_valor_curto(valor_imovel):
    """Ex: 200000 -> '200 mil' | 1500000 -> '1,5 milhão'. Usado no title/H1/meta
    para casar com a forma como as pessoas realmente digitam a busca."""
    if valor_imovel >= 1_000_000:
        milhoes = valor_imovel / 1_000_000
        # Achado real (21/set/2026, auditoria de SEO): com 1 casa decimal,
        # R$ 1.050.000, 1.100.000 e 1.150.000 viravam TODOS "1,1 milhões" —
        # 480 páginas com <title> e meta description idênticos (180 grupos
        # de 2-3 páginas), que o Google trata como quase-duplicata e
        # escolhe UMA pra mostrar. A grade anda de R$ 50 mil em R$ 50 mil,
        # então 2 casas decimais (sem zero à direita) deixam cada valor
        # único: 1,05 | 1,1 | 1,15 | 1,2 ...
        texto = f"{milhoes:.2f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{texto} milhão" if milhoes == 1 else f"{texto} milhões"
    milhares = int(round(valor_imovel / 1000))
    return f"{milhares} mil"


def formatar_reais(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def slug_comparacao(valor_imovel, anos):
    """Slug da página de comparação sem marca (ex: 300000, 30 ->
    'financiamento-imobiliario-300-mil-30-anos')."""
    return f"financiamento-imobiliario-{int(valor_imovel) // 1000}-mil-{anos}-anos"


def bancos_com_prazo(prazo_meses):
    """Bancos que realmente oferecem (pelo menos) esse prazo — a comparação
    nunca mostra um banco com prazo menor disfarçado de prazo maior."""
    return [b for b, regra in BANCOS.items() if regra["prazo_max"] >= prazo_meses]


def pagina_comparacao_existe(valor_imovel, anos):
    return (
        int(valor_imovel) in VALORES_COMPARACAO
        and anos in ANOS_COMPARACAO
        and len(bancos_com_prazo(anos * 12)) >= MIN_BANCOS_COMPARACAO
    )


def slug_hub_banco(banco):
    """Slug da página-hub do banco (ex: 'C6 Bank' -> 'banco-c6-bank'). Mesma
    convenção de normalização (lower + espaço->hífen) já usada em outros
    lugares do gerador (ancora_id do index, slug de banco no JS de
    ranking ao vivo) — mantém uma única forma de "slugificar banco" no
    projeto todo."""
    return f"banco-{banco.lower().replace(' ', '-')}"


def montar_titulo(banco_exib, valor_curto, prazo, anos):
    """Title curto (cabe no SERP, ~55-60 chars) com valor, prazo em meses E em
    anos logo no início — resolve buscas tipo '200 mil 20 anos' e '360 meses'."""
    nucleo = f"{banco_exib} {valor_curto} — {anos} anos ({prazo}x)"
    candidato = f"Simulador {nucleo} | Datalab Global"
    if len(candidato) <= 60:
        return candidato
    candidato = f"Simulador {nucleo}"
    if len(candidato) <= 60:
        return candidato
    return f"{banco_exib} {valor_curto} em {prazo} meses ({anos} anos)"


def gerar_paginas_pseo():
    caminho_csv = 'dados.csv'
    pasta_saida = 'paginas_seo'
    dominio = DOMINIO

    os.makedirs(pasta_saida, exist_ok=True)
    if not os.path.exists(caminho_csv):
        criar_csv_exemplo(caminho_csv)

    data_ultima_atualizacao = obter_data_ultima_atualizacao()
    data_ultima_atualizacao_br = date.fromisoformat(data_ultima_atualizacao).strftime('%d/%m/%Y')
    urls_sitemap = []
    links_por_banco = {}
    todas_as_paginas = []

    with open(caminho_csv, mode='r', encoding='utf-8') as arquivo:
        leitor_csv = list(csv.DictReader(arquivo, delimiter=';'))

        for linha in leitor_csv:
            banco = linha['banco']
            valor_imovel = float(linha['valor_imovel'])
            prazo_csv = int(linha['prazo'])
            slug_original = linha['slug']

            regra = obter_regra(banco)
            banco_exib = nome_exibicao(banco)
            prazo_correto = min(prazo_csv, regra["prazo_max"])

            if prazo_correto != prazo_csv:
                slug = slug_original.replace(f"-{prazo_csv}-meses", f"-{prazo_correto}-meses")
            else:
                slug = slug_original

            valor_amigavel = formatar_reais(valor_imovel)
            valor_curto = formatar_valor_curto(valor_imovel)
            anos_equivalentes = prazo_correto // 12

            pagina_info = {
                "banco": banco,
                "banco_exib": banco_exib,
                "slug": slug,
                "prazo_correto": prazo_correto,
                "anos_equivalentes": anos_equivalentes,
                "regra": regra,
                "valor_curto": valor_curto,
                "texto": f"{valor_amigavel} em {prazo_correto} meses ({anos_equivalentes} anos)",
                "linha_original": linha,
            }
            todas_as_paginas.append(pagina_info)

        # Deduplica por slug: quando o prazo do CSV excede o prazo_max do
        # banco (ex: 420 meses num banco com teto de 360), duas linhas do
        # CSV colapsam para a mesma URL final. Sem isso, a mesma página era
        # escrita 2x e entrava duplicada no sitemap.
        vistos = set()
        paginas_unicas = []
        for p in todas_as_paginas:
            if p["slug"] in vistos:
                continue
            vistos.add(p["slug"])
            paginas_unicas.append(p)
        todas_as_paginas = paginas_unicas

        # Lookup (banco, valor_imovel, prazo_correto) -> slug, usado pela
        # caixinha "Comparação com o Mercado" pra linkar direto pra página
        # equivalente do banco com menor CET, sem precisar adivinhar a URL.
        lookup_paginas = {
            (p['banco'], float(p['linha_original']['valor_imovel']), p['prazo_correto']): p['slug']
            for p in todas_as_paginas
        }

        for p in todas_as_paginas:
            links_por_banco.setdefault(p['banco'], []).append(p)

        # Ordena cada cluster de banco de forma estável -> permite montar um
        # ciclo de linkagem interna que garante que TODA página recebe pelo
        # menos 1 link de entrada (elimina o risco de páginas órfãs que a
        # amostragem 100% aleatória anterior não garantia).
        #
        # Achado real (06/set/2026, print do Rodolfo): isso ordenava pelo
        # SLUG (string) — "simulador-caixa-1000-mil-..." vem antes de
        # "simulador-caixa-150-mil-..." em ordem alfabética (comparação
        # char a char: '0' < '5'), então R$ 1.000.000 aparecia ANTES de
        # R$ 150.000 nos cards da home/hub. Corrigido pra ordenar pelo
        # valor numérico do imóvel e depois pelo prazo — o ciclo de
        # linkagem interna continua cobrindo toda página igual, só que
        # numa ordem que faz sentido pra quem lê.
        for banco in links_por_banco:
            links_por_banco[banco].sort(key=lambda p: (float(p["linha_original"]["valor_imovel"]), p["prazo_correto"]))

        # Taxa que o etl_taxas.py de fato gravou por último em dados.csv,
        # por banco — usada em vez do taxa_padrao estático de bancos.py em
        # toda comparação entre bancos (ver taxas_atuais_de/
        # comparar_todos_bancos). Calculado uma vez aqui, repassado pros
        # três lugares que comparam banco com banco.
        taxas_atuais_por_banco = taxas_atuais_de(links_por_banco)
        # Calculado uma única vez (não a cada página do loop abaixo — o
        # valor é o mesmo pra todas): a matriz que a caixinha "Comparação
        # com o Mercado" recalcula ao vivo em JS quando o visitante mexe
        # nos sliders.
        bancos_json_atual = construir_bancos_json(taxas_atuais_por_banco)

        termos_variados = [
            "Calculadora de financiamento", "Simulador de crédito", "Simulação de amortização",
            "Calcular taxas de juros", "Simulador imobiliário", "Comparador de empréstimo",
        ]

        for p in todas_as_paginas:
            linha = p["linha_original"]
            banco = p['banco']
            banco_exib = p['banco_exib']
            valor_imovel = float(linha['valor_imovel'])
            prazo = p['prazo_correto']
            anos = p['anos_equivalentes']
            slug = p['slug']
            regra = p['regra']
            valor_curto = p['valor_curto']
            valor_amigavel = formatar_reais(valor_imovel)

            prazo_max_banco = regra["prazo_max"]
            perc_entrada_minima = 1 - regra["ltv"]
            entrada_minima_valor = valor_imovel * perc_entrada_minima
            entrada_padrao = max(valor_imovel * 0.20, entrada_minima_valor)

            try:
                taxa_csv = linha.get('taxa', '')
                if not taxa_csv:
                    taxa = regra["taxa_padrao"]
                else:
                    taxa = float(str(taxa_csv).replace(',', '.'))
                    if taxa < 4.0:
                        taxa = ((1 + (taxa / 100)) ** 12 - 1) * 100
            except (ValueError, TypeError):
                taxa = regra["taxa_padrao"]

            taxa = round(taxa, 2)
            # Exibição sempre com 2 casas decimais fixas (11,25% em vez de
            # 11,2% quando o segundo dígito é zero) — evita inconsistência
            # visual quando duas taxas aparecem lado a lado no mesmo painel.
            taxa_fmt = f"{taxa:.2f}".replace('.', ',')

            vfinanciado_padrao = valor_imovel - entrada_padrao
            comparativo = calcular_sac_price(vfinanciado_padrao, prazo, taxa, valor_imovel)

            # Comparação com o mercado: qual dos 15 bancos teria o menor CET
            # pro MESMO valor de imóvel e prazo (cada um com sua própria
            # entrada mínima). Pro banco ATUAL, usa o CET já calculado acima
            # (que reflete a entrada de fato configurada nesta página) em vez
            # de recalcular com a entrada mínima — evita mostrar dois CETs
            # diferentes pro mesmo banco na mesma página.
            ranking_bancos = comparar_todos_bancos(valor_imovel, prazo, lookup_paginas, taxas_atuais_por_banco)
            for r in ranking_bancos:
                if r["banco"] == banco:
                    r["cet"] = comparativo["cet_sac"]
            ranking_bancos.sort(key=lambda r: r["cet"])

            # Caixinha "Dica: Faixa de CET do Mercado" — cabeçalho com selo
            # "DICA" + ícone de lâmpada em tamanho próprio, e uma barra de
            # faixa (menor CET que acompanhamos <-> maior) com um marcador
            # mostrando onde o banco desta página está posicionado. Trocamos
            # o antigo ranking nomeado (que citava o banco concorrente com
            # menor CET e linkava pra simulação DELE — ex: "Poupex") por essa
            # versão porque aquele formato mandava o visitante pra fora do
            # funil da Financia Tudo bem no momento de maior intenção de
            # conversão. A faixa ainda entrega o dado real (mostra que existe
            # variação relevante entre instituições, o que dá credibilidade
            # à dica), mas sem nomear concorrente nem linkar pra fora — o
            # CTA da caixinha aponta pra Financia Tudo.
            texto_comparacao_mercado = ""
            link_comparacao_html = ""
            if pagina_comparacao_existe(valor_imovel, anos):
                link_comparacao_html = (
                    f'<a href="{slug_comparacao(valor_imovel, anos)}" class="text-emerald-400 underline hover:text-emerald-300 '
                    f'block mt-3 text-xs font-semibold">Comparar {valor_curto} em {anos} anos em todos os bancos →</a>'
                )
            if ranking_bancos:
                cet_atual = comparativo['cet_sac']
                cet_atual_fmt = f"{cet_atual:.2f}".replace('.', ',')
                cet_min = ranking_bancos[0]["cet"]
                cet_max = ranking_bancos[-1]["cet"]
                cet_min_fmt = f"{cet_min:.2f}".replace('.', ',')
                cet_max_fmt = f"{cet_max:.2f}".replace('.', ',')

                marcador_pct = calcular_marcador_posicao_mercado(ranking_bancos, banco)

                grafico_html = f'''<div class="space-y-2" id="grafico_comparacao_mercado">
                    <div class="relative h-2 rounded-full bg-gradient-to-r from-emerald-500 via-amber-400 to-rose-500">
                        <div class="absolute top-1/2 h-4 w-4 rounded-full bg-white border-2 border-emerald-950 shadow-[0_0_0_3px_rgba(16,185,129,0.35)]" style="left:{marcador_pct}%; transform:translate(-50%,-50%)" title="{banco_exib}: {cet_atual_fmt}%"></div>
                    </div>
                    <div class="flex justify-between text-[10px] text-slate-400 uppercase tracking-wide">
                        <span>{cet_min_fmt}% menor CET</span>
                        <span>{cet_max_fmt}% maior CET</span>
                    </div>
                </div>'''

                cabecalho_html = f'''<div class="flex items-center gap-2 mb-4">
                    <span class="text-yellow-400 text-xl leading-none">{icone('lightbulb')}</span>
                    <span class="bg-emerald-500 text-slate-950 text-[9px] font-black px-2 py-0.5 rounded-full uppercase tracking-widest">Dica</span>
                    <span class="text-slate-300 text-[11px] font-bold uppercase tracking-widest">Faixa de CET no Mercado</span>
                    {tooltip('Simulamos o CET nas mesmas condições (mesmo valor de imóvel e prazo mais próximo permitido) em todos os bancos que acompanhamos, usando a entrada mínima exigida por cada um. A faixa mostra o menor e o maior CET encontrados, e o marcador indica onde o banco desta página está posicionado.')}
                </div>'''

                if marcador_pct <= 15:
                    texto_resumo = f'''O {banco_exib} está entre as condições <strong class="text-emerald-400">mais competitivas</strong> que acompanhamos ({cet_atual_fmt}% de CET, na faixa de {cet_min_fmt}% a {cet_max_fmt}% do mercado). Vale confirmar essa condição e agilizar a aprovação sem custo.
                        <a href="{LINK_FINANCIA_TUDO}" target="_blank" rel="noopener sponsored" class="text-emerald-400 underline hover:text-emerald-300 block mt-2 font-semibold">Falar com a Financia Tudo →</a>'''
                else:
                    texto_resumo = f'''Nas condições simuladas, o CET no mercado costuma variar entre <strong class="text-emerald-400">{cet_min_fmt}%</strong> e <strong class="text-emerald-400">{cet_max_fmt}%</strong> — aqui no {banco_exib} está em {cet_atual_fmt}%. Encontrar e negociar manualmente a melhor condição pode levar semanas de idas e vindas ao banco.
                        <a href="{LINK_FINANCIA_TUDO}" target="_blank" rel="noopener sponsored" class="text-emerald-400 underline hover:text-emerald-300 block mt-2 font-semibold">É esse trabalho que a Financia Tudo faz por você, sem custo →</a>'''

                # Card agora é FULL-WIDTH (fora das duas colunas da Zona A) —
                # por isso o conteúdo interno vira 2 colunas em telas médias+
                # (faixa à esquerda, resumo à direita), aproveitando a
                # largura extra em vez de empilhar tudo verticalmente.
                texto_comparacao_mercado = f'''<div class="bg-emerald-500/10 border border-emerald-500/30 rounded-2xl p-6 shadow-[0_0_25px_rgba(16,185,129,0.12)]">
                    {cabecalho_html}
                    <div class="flex flex-col md:flex-row md:items-center gap-6">
                        <div class="w-full md:w-3/5">{grafico_html}</div>
                        <div class="w-full md:w-2/5 md:border-l md:border-emerald-500/20 md:pl-6">
                            <p class="text-slate-300 text-xs font-light leading-relaxed" id="texto_resumo_mercado">{texto_resumo}</p>
                            {link_comparacao_html}
                        </div>
                    </div>
                </div>'''

            # Aporte único padrão da Zona de Amortização: antes era um valor fixo
            # de R$ 20.000 em toda página, o que fazia a "Economia Total de
            # Juros" parecer travada/pouco reativa quando o valor financiado
            # mudava muito de página pra página (ou via slider). Agora é 5% do
            # valor financiado desta página (arredondado pra R$ 1.000 mais
            # próximo, com piso de R$ 5.000), então o campo já nasce coerente
            # com a escala do financiamento simulado.
            aporte_padrao = max(5_000, round((vfinanciado_padrao * 0.05) / 1000) * 1000)
            aporte_padrao = min(aporte_padrao, int(vfinanciado_padrao)) if vfinanciado_padrao > 0 else 5_000
            aporte_padrao_fmt = formatar_reais(aporte_padrao)[3:]  # remove o prefixo "R$ "
            slider_amortizar_max = max(int(vfinanciado_padrao), aporte_padrao, 500_000)

            # Periodicidade padrão da amortização recorrente: a cada 6 meses
            # (2x/ano) é um ritmo comum de quem usa 13º/bônus pra amortizar,
            # e serve de ponto de partida neutro pro usuário ajustar.
            periodicidade_padrao = 6

            # LINKAGEM INTERNA (clusterização por banco, com cobertura garantida):
            # 1) link determinístico para a "próxima" página do mesmo banco no
            #    ciclo ordenado -> garante in-degree >= 1 para toda página do
            #    cluster (nenhuma fica órfã).
            # 2) completa até 4 links com amostragem aleatória dentro do MESMO
            #    banco (preserva a estratégia de silo/autoridade de tópico).
            # 3) só recorre a outro banco se o cluster tiver menos de 4 páginas.
            grupo_banco = links_por_banco[banco]
            n = len(grupo_banco)
            idx_atual = next(i for i, pag in enumerate(grupo_banco) if pag["slug"] == slug)

            # Achado real (26/set/2026, auditoria de SEO): o sorteio mudava a cada geração, então toda atualização mensal de
            # taxas reembaralhava os ~6.800 links internos do site inteiro — o Google revia um grafo de links diferente a
            # cada rodada. Sorteio com semente fixa por página: os mesmos links em toda geração.
            rng = random.Random(slug)
            paginas_sorteadas = []
            if n > 1:
                proximo = grupo_banco[(idx_atual + 1) % n]
                paginas_sorteadas.append(proximo)

            candidatos_mesmo_banco = [
                pag for pag in grupo_banco
                if pag["slug"] != slug and pag not in paginas_sorteadas
            ]
            faltam = 4 - len(paginas_sorteadas)
            if candidatos_mesmo_banco and faltam > 0:
                paginas_sorteadas.extend(
                    rng.sample(candidatos_mesmo_banco, min(faltam, len(candidatos_mesmo_banco)))
                )

            faltam = 4 - len(paginas_sorteadas)
            if faltam > 0:
                outras_paginas = [pag for pag in todas_as_paginas if pag["slug"] != slug and pag['banco'] != banco]
                if outras_paginas:
                    paginas_sorteadas.extend(rng.sample(outras_paginas, min(faltam, len(outras_paginas))))

            links_internos_html = ""
            for pag_sorteada in paginas_sorteadas:
                termo = rng.choice(termos_variados)
                links_internos_html += f"""
                <a href="{pag_sorteada['slug']}" class="block p-4 bg-white/5 rounded-xl border border-white/10 hover:border-emerald-500/50 hover:bg-white/10 transition-all">
                    <span class="text-xs text-emerald-500 font-bold uppercase tracking-wider block mb-1">{termo}</span>
                    <span class="text-sm text-slate-300 group-hover:text-white block">{pag_sorteada['banco_exib']} - {pag_sorteada['texto']}</span>
                </a>
                """

            # Achado real (27/set/2026, medição de texto + Search Console): duas páginas quaisquer eram 92% idênticas e as 3
            # perguntas frequentes eram as mesmas em toda página do banco (só o nome mudava). Cada página ganha uma análise
            # com as contas dela (prazo ±5 anos, +10% de entrada, renda) e perguntas com os números dela. Sem ranking nomeado
            # de bancos: foi retirado de propósito (ver "Caixinha Dica" acima) para não mandar o visitante ao concorrente.
            financiado_p = vfinanciado_padrao
            juros_sac = comparativo["total_sac"] - financiado_p
            juros_price = comparativo["total_price"] - financiado_p
            prazo_alt = prazo + 60 if prazo + 60 <= prazo_max_banco else (prazo - 60 if prazo - 60 >= 60 else None)
            frase_prazo_imovel = ""
            if prazo_alt:
                comp_alt = calcular_sac_price(financiado_p, prazo_alt, taxa)
                juros_alt = comp_alt["total_sac"] - financiado_p
                anos_alt = prazo_alt // 12
                if prazo_alt > prazo:
                    frase_prazo_imovel = (f"Esticar para {prazo_alt} meses ({anos_alt} anos) baixa a primeira parcela para "
                                          f"{formatar_reais(comp_alt['p1_sac'])}, mas soma {formatar_reais(juros_alt - juros_sac)} de juros.")
                else:
                    frase_prazo_imovel = (f"Encurtar para {prazo_alt} meses ({anos_alt} anos) sobe a primeira parcela para "
                                          f"{formatar_reais(comp_alt['p1_sac'])} e economiza {formatar_reais(juros_sac - juros_alt)} de juros.")
            perc_entrada_atual = entrada_padrao / valor_imovel
            entrada_mais = valor_imovel * min(perc_entrada_atual + 0.10, 0.9)
            comp_mais = calcular_sac_price(valor_imovel - entrada_mais, prazo, taxa)
            juros_mais = comp_mais["total_sac"] - (valor_imovel - entrada_mais)
            analise_html = (
                '<div class="mt-8 glass-panel p-8 md:p-10 rounded-3xl">'
                '<h2 class="text-xs font-bold text-slate-300 uppercase tracking-widest mb-1">Análise desta simulação</h2>'
                '<p class="text-slate-400 text-[11px] mb-6 pb-4 border-b border-white/10">As contas deste cenário, em números.</p>'
                f'<p class="text-slate-300 text-sm font-light leading-relaxed">Financiando {formatar_reais(financiado_p)} de um imóvel de '
                f'{valor_amigavel} em {prazo} meses ({anos} anos) no {banco_exib}, com entrada de {formatar_reais(entrada_padrao)}, '
                f'a primeira parcela na SAC é de <strong class="text-white font-medium">{formatar_reais(comparativo["p1_sac"])}</strong> '
                f'e cai até {formatar_reais(comparativo["pU_sac"])}; na PRICE, fica fixa em {formatar_reais(comparativo["p1_price"])}. '
                f'Os juros somam {formatar_reais(juros_sac)} na SAC e {formatar_reais(juros_price)} na PRICE: '
                f'{formatar_reais(comparativo["economia_sac"])} de diferença.</p>'
                + (f'<p class="text-slate-300 text-sm font-light leading-relaxed mt-3">{frase_prazo_imovel}</p>' if frase_prazo_imovel else '')
                + f'<p class="text-slate-300 text-sm font-light leading-relaxed mt-3">Com {round(min(perc_entrada_atual + 0.10, 0.9) * 100)}% '
                f'de entrada ({formatar_reais(entrada_mais)}) em vez de {round(perc_entrada_atual * 100)}%, a primeira parcela cai para '
                f'{formatar_reais(comp_mais["p1_sac"])} e você paga {formatar_reais(juros_sac - juros_mais)} a menos de juros. '
                f'Para a primeira parcela caber na regra de 30% de comprometimento, a renda familiar precisa ser de pelo menos '
                f'{formatar_reais(comparativo["renda_sugerida"])} por mês.</p>'
                '</div>'
            )

            faq_q1 = f"Qual a primeira parcela de {valor_curto} em {prazo} meses no {banco_exib}?"
            faq_a1 = (f"Com entrada de {formatar_reais(entrada_padrao)}, o valor financiado é {formatar_reais(financiado_p)}. Na tabela SAC, "
                      f"a primeira parcela é {formatar_reais(comparativo['p1_sac'])} e a última {formatar_reais(comparativo['pU_sac'])}; "
                      f"na PRICE, a parcela é fixa em {formatar_reais(comparativo['p1_price'])}, com a taxa estimada de {taxa_fmt}% ao ano.")
            faq_q2 = f"Quanto pago de juros financiando {valor_curto} em {anos} anos: SAC ou PRICE?"
            faq_a2 = (f"Na SAC, os juros somam {formatar_reais(juros_sac)} e o total pago é {formatar_reais(comparativo['total_sac'])}. "
                      f"Na PRICE, os juros somam {formatar_reais(juros_price)}. A SAC economiza {formatar_reais(comparativo['economia_sac'])}, "
                      f"mas começa com parcelas maiores.")
            faq_q3 = f"Qual renda preciso para financiar {valor_curto} no {banco_exib}?"
            faq_a3 = (f"Os bancos costumam limitar a parcela a 30% da renda bruta. Para a primeira parcela de "
                      f"{formatar_reais(comparativo['p1_sac'])} na SAC, a renda familiar precisa ser de pelo menos "
                      f"{formatar_reais(comparativo['renda_sugerida'])} por mês. Dá para somar a renda do cônjuge ou companheiro(a).")

            titulo_pagina = montar_titulo(banco_exib, valor_curto, prazo, anos)
            meta_description_completa = (
                f"Simule {valor_curto} de {regra['mod'].lower()} pelo {banco_exib} em {prazo} meses "
                f"({anos} anos). Taxa estimada de {taxa_fmt}% a.a., entrada mínima de {(perc_entrada_minima*100):.0f}%, "
                f"cálculo de amortização SAC e PRICE."
            )
            meta_description_curta = (
                f"Simule {valor_curto} de {regra['mod'].lower()} pelo {banco_exib} em {prazo} meses "
                f"({anos} anos). Taxa estimada de {taxa_fmt}% a.a., entrada mínima de {(perc_entrada_minima*100):.0f}%."
            )
            # Nunca corta no meio de uma palavra/frase: usa a versão completa se
            # couber em 160 caracteres (limite prático do Google), senão a curta.
            meta_description = meta_description_completa if len(meta_description_completa) <= 160 else meta_description_curta
            meta_keywords = (
                f"simulador de financiamento, calculadora de amortização, empréstimo imobiliário, "
                f"financiar imóvel {valor_curto}, calcular juros {banco_exib}, amortizar financiamento {banco_exib}, "
                f"{prazo} meses, {anos} anos, financiamento {anos} anos, Custo Efetivo Total, TR, Saldo Devedor"
            )
            url_canonica = f"{dominio}/{slug}"
            url_logo_banco = f"https://www.google.com/s2/favicons?domain={regra['dominio_favicon']}&sz=128"

            schema_faq = f'''{{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {{ "@type": "Question", "name": "{faq_q1}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_a1}" }} }},
        {{ "@type": "Question", "name": "{faq_q2}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_a2}" }} }},
        {{ "@type": "Question", "name": "{faq_q3}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_a3}" }} }}
      ]
    }}'''

            schema_breadcrumb = f'''{{
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{ "@type": "ListItem", "position": 1, "name": "Datalab Global", "item": "{dominio}/" }},
        {{ "@type": "ListItem", "position": 2, "name": "{banco_exib}", "item": "{dominio}/{slug_hub_banco(banco)}" }},
        {{ "@type": "ListItem", "position": 3, "name": "{valor_curto} em {prazo} meses ({anos} anos)", "item": "{url_canonica}" }}
      ]
    }}'''

            schema_software = f'''{{
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      "name": "Simulador de {regra['mod']} {banco_exib}",
      "applicationCategory": "FinanceApplication",
      "operatingSystem": "Web",
      "offers": {{ "@type": "Offer", "price": "0", "priceCurrency": "BRL" }},
      "url": "{url_canonica}",
      "dateModified": "{data_ultima_atualizacao}"
    }}'''

            # HowTo: schema explicitamente citado por engines de IA (AI
            # Overviews, ChatGPT, Perplexity) ao montar respostas passo-a-passo.
            schema_howto = f'''{{
      "@context": "https://schema.org",
      "@type": "HowTo",
      "name": "Como simular o {regra['mod'].lower()} do {banco_exib}",
      "step": [
        {{ "@type": "HowToStep", "name": "Informe o valor do imóvel", "text": "Digite ou arraste o slider até o valor do imóvel ou garantia que você quer financiar." }},
        {{ "@type": "HowToStep", "name": "Ajuste a entrada", "text": "Defina quanto você vai pagar à vista — o simulador trava automaticamente no mínimo exigido pelo {banco_exib} e no teto de mercado de 80%." }},
        {{ "@type": "HowToStep", "name": "Escolha prazo e sistema", "text": "Defina o prazo em meses (até {prazo_max_banco} no {banco_exib}) e escolha entre SAC ou PRICE." }},
        {{ "@type": "HowToStep", "name": "Veja o resultado e simule uma amortização extra", "text": "Confira parcelas e custo total, depois teste um valor de amortização extra para ver a economia de juros e a redução de prazo." }}
      ]
    }}'''

            html_content = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
{render_head_boilerplate(titulo_pagina, meta_description, url_canonica, dominio, [schema_faq, schema_breadcrumb, schema_software, schema_howto], meta_keywords, robots=(None if prazo in PRAZOS_INDEXAVEIS else 'noindex,follow'))}
</head>
<body class="antialiased flex flex-col">
    <nav class="border-b border-white/5 sticky top-0 z-50 backdrop-blur-2xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="/" class="flex items-center">
                    <img src="logo-full.png" alt="Datalab Global" width="122" height="48" class="h-12 md:h-16 w-auto drop-shadow-[0_0_15px_rgba(16,185,129,0.2)] hover:scale-105 transition-transform duration-300">
                </a>
                <div class="flex items-center gap-1">
                    <a href="/aprenda" aria-label="Aprenda" class="inline-flex items-center gap-1.5 -my-2.5 p-2.5 text-xs text-slate-400 hover:text-emerald-400 transition-colors">{icone('book-open')} <span class="hidden sm:inline">Aprenda</span></a>
                    <div class="hidden md:flex items-center">
                        <a href="{LINK_FINANCIA_TUDO}" target="_blank" rel="noopener sponsored" class="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-6 py-2.5 rounded-full font-bold transition-all text-sm flex items-center shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                            Fazer Análise Grátis {icone('arrow-right', 'ml-2 text-sm')}
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <header class="py-12 md:py-16 relative z-10 text-center">
        <!-- Link real (crawlável) pra página-hub do banco — não só uma menção
             no schema de breadcrumb. É o que dá à página-hub um in-degree de
             ~37 links (uma vez por página de simulação do banco), reforçando
             o cluster de autoridade temática por instituição. -->
        <a href="{slug_hub_banco(banco)}" class="inline-flex items-center gap-2.5 bg-white/5 border border-white/10 hover:border-emerald-500/40 hover:bg-white/10 rounded-full pl-2 pr-4 py-1.5 mb-6 transition-colors group">
            {favicon_com_fallback(url_logo_banco, banco_exib, "w-6 h-6")}
            <span class="text-xs font-bold text-slate-200 group-hover:text-emerald-400 tracking-wide transition-colors">{banco_exib}</span>
            <span class="text-[10px] text-slate-400 uppercase tracking-widest border-l border-white/10 pl-2">{regra['mod']}</span>
            <span class="text-[10px] text-emerald-500/70 group-hover:text-emerald-400 uppercase tracking-widest border-l border-white/10 pl-2 transition-colors">Ver taxas e condições →</span>
        </a>
        <h1 class="text-4xl md:text-5xl font-serif text-white mb-4 leading-tight px-4">
            Simulador {banco_exib}: {valor_curto} em {prazo} meses ({anos} anos)
        </h1>
        <p class="text-slate-400 text-base md:text-lg font-light tracking-wide max-w-3xl mx-auto px-4">
            Você está simulando um financiamento de <strong class="text-white font-medium">{valor_amigavel}</strong> pelo
            <strong class="text-white font-medium">{banco_exib}</strong>, em {prazo} meses (equivalente a
            <span id="label_anos" class="font-medium text-white">{anos} anos</span>), com entrada mínima de
            {(perc_entrada_minima*100):.0f}% e taxa estimada de {taxa_fmt}% a.a. Ajuste os valores abaixo para o seu caso.
        </p>
        <p class="text-slate-600 text-[10px] uppercase tracking-widest mt-4">Taxas atualizadas em {data_ultima_atualizacao_br} · {texto_fonte_taxa(banco)}</p>
    </header>

    <!-- Ritmo vertical entre zonas: cada zona abaixo declara seu próprio
         mt-* explícito (32px = mt-8 padrão, 64px = mt-16 antes de CTAs
         fortes/blocos educativos). Antes esse <main> tinha "space-y-8",
         que aplicava 32px fixos via CSS entre TODOS os filhos e vencia por
         ordem de cascata — isso anulava silenciosamente os mt-12/mt-16 que
         cada zona já declarava (auditoria confirmou: todo gap renderizava
         32px, mesmo onde o código "dizia" 48px/64px). Removido de propósito
         para o espaçamento realmente refletir o que cada zona pede. -->
    <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex-grow w-full relative z-10">

        <!-- ZONA A: O FINANCIAMENTO -->
        <div class="glass-panel p-8 md:p-10 rounded-3xl border-t border-slate-700/50 relative overflow-hidden">
            <h2 class="text-xs font-bold text-slate-300 uppercase tracking-widest mb-1 flex items-center relative z-10">
                {icone('invoice', 'mr-3')} 1. Estratégia
            </h2>
            <p class="text-slate-400 text-[11px] mb-8 pb-4 border-b border-white/10 relative z-10">Defina os parâmetros do seu financiamento {banco_exib.lower()}.</p>
            <div class="flex flex-col lg:flex-row lg:items-start gap-10 relative z-10">
                <div class="w-full lg:w-1/2 space-y-4">
                    <div class="bg-slate-800/60 p-5 rounded-2xl border border-white/10 shadow-md shadow-black/20 hover:border-emerald-500/30 transition-colors">
                        <div class="flex justify-between items-end mb-2">
                            <label class="text-[10px] font-semibold text-slate-400 uppercase tracking-widest flex items-center">
                                {icone('home', 'mr-1.5 text-slate-400')} Valor do Imóvel / Garantia
                                {tooltip('É o valor total do bem que você quer financiar. A partir dele calculamos a entrada mínima exigida pelo banco (regra de LTV) e o crédito liberado.')}
                            </label>
                            <input type="text" id="input_imovel" aria-label="Valor do imóvel em reais" class="currency-input w-40 text-right bg-transparent font-medium text-white text-2xl outline-none border-b border-transparent focus:border-emerald-500 transition-colors" value="">
                        </div>
                        <input type="range" id="slider_imovel" aria-label="Valor do imóvel" min="100000" max="2000000" step="10000" value="{valor_imovel}" class="w-full mt-2">
                    </div>
                    <div class="bg-slate-800/60 p-5 rounded-2xl border border-white/10 shadow-md shadow-black/20 hover:border-emerald-500/30 transition-colors">
                        <div class="flex justify-between items-end mb-2">
                            <label class="text-[10px] font-semibold text-slate-400 uppercase tracking-widest flex items-center">
                                {icone('percent', 'mr-1.5 text-slate-400')} Entrada / Margem Retida
                                {tooltip(f'Quanto você paga à vista de imediato. Todo banco exige um mínimo (aqui, {(perc_entrada_minima*100):.0f}% pela regra de LTV do {banco_exib}) e o mercado considera pouco usual passar de 80% — acima disso, geralmente compensa mais comprar à vista.')}
                            </label>
                            <input type="text" id="input_entrada" aria-label="Valor da entrada em reais" class="currency-input w-40 text-right bg-transparent font-medium text-white text-2xl outline-none border-b border-transparent focus:border-emerald-500 transition-colors" value="">
                        </div>
                        <input type="range" id="slider_entrada" aria-label="Valor da entrada" min="{int(entrada_minima_valor)}" max="1000000" step="5000" value="{int(entrada_padrao)}" class="w-full mt-2">
                        <p class="text-[9px] text-slate-400 mt-1 text-right">Mínimo exigido: {(perc_entrada_minima*100):.0f}% do valor</p>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-slate-800/60 p-5 rounded-2xl border border-white/10 shadow-md shadow-black/20 hover:border-emerald-500/30 transition-colors">
                            <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 flex items-center">
                                {icone('calendar', 'mr-1.5 text-slate-400')} Prazo
                                {tooltip(f'Quantidade de parcelas mensais do financiamento. O {banco_exib} permite no máximo {prazo_max_banco} meses ({prazo_max_banco // 12} anos) nessa modalidade.')}
                            </label>
                            <div class="flex items-center"><input type="number" id="input_prazo" aria-label="Prazo em meses" min="12" max="{prazo_max_banco}" class="w-full bg-transparent font-medium text-white text-lg outline-none" value="{prazo}"><span class="text-xs text-slate-400 ml-2">meses</span></div>
                            <p class="text-[9px] text-slate-400 mt-1">Equivale a <span id="hint_anos">{anos}</span> anos</p>
                        </div>
                        <div class="bg-slate-800/60 p-5 rounded-2xl border border-white/10 shadow-md shadow-black/20 hover:border-emerald-500/30 transition-colors">
                            <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 flex items-center">
                                {icone('trending-up', 'mr-1.5 text-slate-400')} Taxa Estimada
                                {tooltip('Taxa de juros anual estimada, aplicada mensalmente sobre o saldo devedor. É a "taxa de vitrine" — sua taxa final aprovada depende da sua análise de crédito.')}
                            </label>
                            <div class="flex items-center"><input type="number" id="input_taxa" aria-label="Taxa de juros ao ano" step="0.01" class="w-full bg-transparent font-medium text-white text-lg outline-none" value="{taxa}"><span class="text-xs text-slate-400 ml-2">% a.a.</span></div>
                        </div>
                    </div>
                    <div class="pt-2">
                        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center pl-2">
                            Sistema de Amortização
                            {tooltip('SAC: parcelas começam mais altas e caem com o tempo (amortização constante, menos juros no total). PRICE: parcelas fixas do início ao fim (mais previsível, porém mais juros no total).')}
                        </label>
                        <div class="flex bg-black/40 p-1 rounded-xl border border-white/5">
                            <label class="flex-1 text-center relative cursor-pointer"><input type="radio" name="sistema" value="SAC" class="peer sr-only" checked><div class="py-2 rounded-lg text-xs font-bold transition-all border border-transparent tracking-widest leading-tight">SAC<span class="block text-[9px] font-normal normal-case tracking-normal opacity-70 mt-0.5">parcela decrescente</span></div></label>
                            <label class="flex-1 text-center relative cursor-pointer"><input type="radio" name="sistema" value="PRICE" class="peer sr-only"><div class="py-2 rounded-lg text-xs font-bold transition-all border border-transparent tracking-widest leading-tight">PRICE<span class="block text-[9px] font-normal normal-case tracking-normal opacity-70 mt-0.5">parcela fixa</span></div></label>
                        </div>
                    </div>
                    <div class="bg-slate-800/60 p-5 rounded-2xl border border-white/10 shadow-md shadow-black/20 flex flex-wrap items-start justify-between gap-6">
                        <div>
                            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5 flex items-center">
                                CET Real (a.a.)
                                {tooltip('Custo Efetivo Total: os juros somados aos seguros obrigatórios (MIP e DFI) e à taxa de administração mensal. É o número mais honesto pra comparar o custo entre bancos diferentes.')}
                            </p>
                            <p class="text-white font-medium text-lg" id="res_cet">{f"{comparativo['cet_sac']:.2f}".replace('.', ',')}%</p>
                        </div>
                        <div>
                            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5 flex items-center">
                                Renda Sugerida
                                {tooltip('Os bancos costumam exigir que a parcela não ultrapasse 30% da renda bruta mensal. Você pode somar a sua renda com a do cônjuge ou companheiro(a) para compor esse valor.')}
                            </p>
                            <p class="text-white font-medium text-lg currency-input" id="res_renda">{formatar_reais(comparativo['renda_sugerida'])}</p>
                        </div>
                    </div>
                </div>
                <div class="w-full lg:w-1/2 bg-slate-950 rounded-2xl border border-emerald-500/20 shadow-inner flex flex-col relative overflow-hidden">
                    <div class="absolute top-0 right-0 w-32 h-32 bg-emerald-500 rounded-full blur-[60px] opacity-10"></div>
                    <div class="px-8 pt-6 pb-4 border-b border-white/5 relative z-10 flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></span>
                        <p class="text-emerald-400 text-[10px] font-bold uppercase tracking-widest">Resultado da Simulação</p>
                    </div>
                    <div class="p-8 flex-1 flex flex-col justify-center space-y-6 relative z-10">
                        <div class="grid grid-cols-1 gap-4">
                            <div><p class="text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-2">Primeira Parcela</p><p class="text-white text-3xl font-light tracking-tight currency-input break-words" id="res_p1">R$ 0,00</p></div>
                            <div><p class="text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-2">Última Parcela</p><p class="text-slate-300 text-2xl font-light tracking-tight currency-input break-words" id="res_pU">R$ 0,00</p></div>
                        </div>
                        <div class="pt-6 border-t border-white/5 grid grid-cols-1 gap-6">
                            <div><p class="text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-1.5">Crédito Liberado (Sem Juros)</p><p class="text-white font-medium text-lg currency-input" id="res_capital">R$ 0,00</p></div>
                            <div><p class="text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-1.5 flex items-center">Custo Total Final (Capital + Juros)</p><p class="text-white font-medium text-xl currency-input" id="res_total_pago">R$ 0,00</p></div>
                        </div>
                        <div class="pt-6 border-t border-white/5">
                            <p class="text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-3">Composição do custo total (cenário padrão)</p>
                            {svg_donut_capital_juros(vfinanciado_padrao, comparativo['total_sac'] - vfinanciado_padrao)}
                        </div>
                    </div>
                </div>
            </div>
            {(f'<div class="mt-8 relative z-10">{texto_comparacao_mercado}</div>' if texto_comparacao_mercado else '')}
        </div>

        <!-- ZONA B: A AMORTIZAÇÃO -->
        <div class="mt-8 glass-panel-emerald rounded-3xl p-8 md:p-10 relative overflow-hidden shadow-[0_10px_40px_rgba(16,185,129,0.1)] border-t border-emerald-500/30" id="card_amortizacao">
            <h2 class="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-8 border-b border-emerald-500/20 pb-4 relative z-10 flex items-center">
                {icone('bolt', 'mr-3')} 2. Valor a Amortizar (A Solução)
            </h2>
            <div class="flex flex-col lg:flex-row gap-10 relative z-10">
                <div class="w-full lg:w-1/2 flex flex-col justify-center">
                    <label class="text-[10px] font-bold text-slate-300 uppercase tracking-widest block mb-4 flex items-center">
                        Amortização Extra (Recorrente)
                        {tooltip('A maioria das pessoas não faz um único pagamento extra: faz vários, ao longo do tempo (ex: com o 13º ou bônus). Aqui você simula esse padrão — quanto, e a cada quantos meses.')}
                    </label>
                    <div class="relative mb-6">
                        <span class="absolute left-4 top-1/2 -translate-y-1/2 font-light text-emerald-500/50 text-3xl">R$</span>
                        <input type="text" id="input_amortizar" aria-label="Valor da amortização extra em reais" class="currency-input w-full bg-black/50 border border-emerald-500/30 rounded-2xl pl-16 pr-4 py-5 focus:border-emerald-400 font-medium text-emerald-400 text-4xl outline-none transition-all shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)]" value="{aporte_padrao_fmt}">
                    </div>
                    <input type="range" id="slider_amortizar" aria-label="Valor da amortização extra" min="0" max="{slider_amortizar_max}" step="5000" value="{aporte_padrao}" class="w-full mb-6">
                    <div class="bg-slate-800/60 p-4 rounded-2xl border border-white/10">
                        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 flex items-center">
                            {icone('repeat', 'mr-1.5 text-slate-400')} A Cada Quantos Meses?
                        </label>
                        <div class="flex items-center gap-3">
                            <input type="range" id="slider_periodicidade" aria-label="A cada quantos meses" min="1" max="24" step="1" value="{periodicidade_padrao}" class="w-full">
                            <span class="text-white font-medium text-sm whitespace-nowrap w-24 text-right" id="label_periodicidade">a cada {periodicidade_padrao} meses</span>
                        </div>
                    </div>
                </div>
                <div class="w-full lg:w-1/2 bg-black/40 border border-emerald-500/30 rounded-2xl p-8 backdrop-blur-sm text-center flex flex-col justify-center shadow-inner">
                    <div class="mb-8">
                        <p class="text-emerald-500/80 text-[10px] font-bold uppercase tracking-widest mb-3">Economia Total de Juros</p>
                        <p class="text-5xl md:text-6xl font-serif text-emerald-400 currency-input break-words" id="res_economia">R$ 0,00</p>
                    </div>
                    <div>
                        <p class="text-emerald-500 text-[10px] font-bold uppercase tracking-widest mb-2">Tempo Reduzido Em</p>
                        <p class="text-3xl md:text-4xl font-light text-white tracking-tight" id="res_impacto">0 Anos</p>
                        <div class="mt-5 w-full h-2 bg-slate-800 rounded-full relative overflow-hidden">
                            <div class="absolute left-0 top-0 h-full bg-slate-600 w-full"></div>
                            <div id="bar_novo_prazo" class="absolute left-0 top-0 h-full bg-emerald-500 transition-all duration-700" style="width: 100%;"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mt-8 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl p-6 relative z-10" id="box_recomendacao_sistema">
                <p class="text-emerald-400 text-[10px] font-bold uppercase tracking-widest mb-2 flex items-center">
                    {icone('lightbulb', 'mr-1.5')} Qual sistema combina com esse plano de amortização?
                    {tooltip('SAC já amortiza mais rápido no início, então cada aporte extra abate um saldo devedor menor. No PRICE, o saldo cai mais devagar no começo, então o mesmo aporte extra costuma abater mais juros — dependendo do quanto e com que frequência você amortiza, o resultado pode até inverter a recomendação padrão de "SAC é sempre melhor".')}
                </p>
                <p class="text-slate-300 text-sm font-light leading-relaxed" id="texto_recomendacao_sistema">Ajuste os valores acima para ver a recomendação.</p>
            </div>
        </div>

        <!-- ZONA COMPARATIVA: SAC vs PRICE COM NUMEROS REAIS (sem depender de JS) -->
        <div class="mt-8 bg-slate-900/40 border border-white/10 rounded-3xl p-8 md:p-10">
            <h2 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1 flex items-center">
                {icone('trending-up', 'mr-3 text-emerald-500')} Comparativo Real: SAC vs. PRICE
                {tooltip('CET = Custo Efetivo Total. É o custo real do financiamento por ano, somando juros + seguros obrigatórios (MIP e DFI) + taxa de administração — sempre maior que a taxa de juros anunciada, e é o número certo para comparar bancos entre si.')}
            </h2>
            <p class="text-slate-400 text-[11px] mb-6">
                Para {valor_curto} financiados pelo {banco_exib} em {prazo} meses, com entrada de {formatar_reais(entrada_padrao)} e taxa de {taxa_fmt}% a.a.:
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="bg-black/30 border {('border-emerald-500/40' if comparativo['total_sac'] <= comparativo['total_price'] else 'border-white/10')} rounded-2xl p-5 relative">
                    {('<span class="absolute -top-3 right-4 bg-emerald-500 text-slate-950 text-[9px] font-bold px-2.5 py-1 rounded-full uppercase tracking-widest shadow-lg">Mais econômico</span>' if comparativo['total_sac'] <= comparativo['total_price'] else '')}
                    <p class="text-white font-bold text-sm mb-3">Tabela SAC</p>
                    <div class="space-y-1.5 text-sm">
                        <div class="flex justify-between"><span class="text-slate-400">1ª parcela</span><span class="text-white currency-input">{formatar_reais(comparativo['p1_sac'])}</span></div>
                        <div class="flex justify-between"><span class="text-slate-400">Última parcela</span><span class="text-white currency-input">{formatar_reais(comparativo['pU_sac'])}</span></div>
                        <div class="flex justify-between pt-2 border-t border-white/10"><span class="text-slate-400">Total pago</span><span class="text-emerald-400 font-medium currency-input">{formatar_reais(comparativo['total_sac'])}</span></div>
                        <div class="flex justify-between"><span class="text-slate-400">CET estimado (a.a.)</span><span class="text-white">{f"{comparativo['cet_sac']:.2f}".replace('.', ',')}%</span></div>
                    </div>
                </div>
                <div class="bg-black/30 border {('border-emerald-500/40' if comparativo['total_price'] < comparativo['total_sac'] else 'border-white/10')} rounded-2xl p-5 relative">
                    {('<span class="absolute -top-3 right-4 bg-emerald-500 text-slate-950 text-[9px] font-bold px-2.5 py-1 rounded-full uppercase tracking-widest shadow-lg">Mais econômico</span>' if comparativo['total_price'] < comparativo['total_sac'] else '')}
                    <p class="text-white font-bold text-sm mb-3">Tabela PRICE</p>
                    <div class="space-y-1.5 text-sm">
                        <div class="flex justify-between"><span class="text-slate-400">Parcela fixa</span><span class="text-white currency-input">{formatar_reais(comparativo['p1_price'])}</span></div>
                        <div class="flex justify-between"><span class="text-slate-400">Última parcela</span><span class="text-white currency-input">{formatar_reais(comparativo['pU_price'])}</span></div>
                        <div class="flex justify-between pt-2 border-t border-white/10"><span class="text-slate-400">Total pago</span><span class="text-white font-medium currency-input">{formatar_reais(comparativo['total_price'])}</span></div>
                        <div class="flex justify-between"><span class="text-slate-400">CET estimado (a.a.)</span><span class="text-white">{f"{comparativo['cet_price']:.2f}".replace('.', ',')}%</span></div>
                    </div>
                </div>
            </div>
            <p class="text-slate-400 text-xs mt-4 text-center">
                Nesse cenário, escolher <strong class="text-emerald-400">SAC em vez de PRICE</strong> economiza aproximadamente
                <strong class="text-emerald-400 currency-input">{formatar_reais(comparativo['economia_sac'])}</strong> em juros ao longo do contrato.
            </p>
        </div>

        <!-- BANNER DE CONVERSÃO FINANCIA TUDO -->
        <div class="mt-16 bg-gradient-to-r from-emerald-600 to-emerald-900 rounded-3xl p-8 md:p-12 relative overflow-hidden shadow-[0_20px_50px_rgba(16,185,129,0.3)] border border-emerald-400/50">
            <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-[80px]"></div>
            <div class="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10">
                <div class="md:w-2/3 text-left">
                    <div class="flex items-center gap-3 mb-4">
                        <span class="bg-yellow-400 text-yellow-950 text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest">Parceria Oficial</span>
                        <span class="flex items-center text-emerald-200 text-xs font-medium">{icone('shield-check', 'mr-1')} 100% Seguro</span>
                    </div>
                    <h3 class="text-3xl font-serif text-white mb-3">Aprove o seu crédito no {banco_exib} sem sair de casa.</h3>
                    <p class="text-emerald-100 text-sm md:text-base font-light leading-relaxed">
                        Como parceiros credenciados, conectamos você diretamente à mesa de crédito para buscar as <strong>melhores taxas e condições de aprovação</strong>. Análise gratuita, rápida e sem compromisso.
                    </p>
                </div>
                <div class="md:w-1/3 w-full flex justify-center md:justify-end">
                    <a href="{LINK_FINANCIA_TUDO}" target="_blank" rel="noopener sponsored" class="group relative inline-flex items-center justify-center bg-white text-emerald-900 hover:bg-slate-100 font-black px-8 py-5 rounded-2xl transition-all shadow-2xl text-sm tracking-widest uppercase w-full text-center overflow-hidden">
                        <span class="relative z-10 flex items-center">Fazer Análise Grátis {icone('external-link', 'ml-3 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform')}</span>
                    </a>
                </div>
            </div>
        </div>


        {analise_html}

        <!-- ZONA E: GLOSSÁRIO / HUB DE AJUDA -->
        <div class="mt-16">
            <div class="flex items-center gap-3 mb-2 justify-center">
                {icone('book-open', 'text-emerald-500 text-xl')}
                <h3 class="text-2xl font-serif text-white text-center">Entenda os Termos Antes de Decidir</h3>
            </div>
            <p class="text-slate-400 text-sm text-center max-w-2xl mx-auto mb-8">
                Mais do que uma calculadora: reunimos aqui o que cada termo do seu financiamento {banco_exib.lower()} significa na prática.
            </p>
            <div class="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 md:gap-x-12 divide-y divide-white/10 md:divide-y-0">
                <div class="py-5 md:pt-0 md:border-b md:border-white/10">
                    <p class="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-2 flex items-center">{icone('percent', 'mr-2')} LTV (Loan-to-Value)</p>
                    <p class="text-slate-300 text-sm font-light leading-relaxed">É o percentual do valor do imóvel que o banco aceita financiar. No {banco_exib}, o LTV é de {(regra['ltv']*100):.0f}%, ou seja, sua entrada mínima é de {(perc_entrada_minima*100):.0f}%.</p>
                </div>
                <div class="py-5 md:pt-0 md:border-b md:border-white/10">
                    <p class="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-2 flex items-center">{icone('invoice', 'mr-2')} CET (Custo Efetivo Total)</p>
                    <p class="text-slate-300 text-sm font-light leading-relaxed">É o custo real do financiamento por ano, incluindo os juros, os seguros obrigatórios (contra morte/invalidez e contra danos no imóvel) e a taxinha mensal de manutenção — sempre maior que a taxa de juros anunciada. É o número certo pra comparar propostas de bancos diferentes.</p>
                </div>
                <div class="py-5 md:border-b md:border-white/10">
                    <p class="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-2 flex items-center">{icone('trending-up', 'mr-2')} Saldo Devedor</p>
                    <p class="text-slate-300 text-sm font-light leading-relaxed">É quanto você ainda deve ao banco em determinado momento (valor financiado menos o que já foi amortizado). É sobre ele que os juros do mês seguinte são calculados.</p>
                </div>
                <div class="py-5 md:border-b md:border-white/10">
                    <p class="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-2 flex items-center">{icone('bolt', 'mr-2')} Amortização Extra</p>
                    <p class="text-slate-300 text-sm font-light leading-relaxed">Pagamento fora do cronograma que abate diretamente o saldo devedor (não é uma parcela adiantada). Reduz os juros futuros e pode encurtar o prazo ou o valor das próximas parcelas.</p>
                </div>
                <div class="py-5 md:border-b md:border-white/10">
                    <p class="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-2 flex items-center">{icone('calendar', 'mr-2')} SAC vs. PRICE</p>
                    <p class="text-slate-300 text-sm font-light leading-relaxed">SAC amortiza um valor fixo por mês (parcelas decrescentes, menos juros no total). PRICE mantém a parcela fixa (mais previsível, mas mais juros ao longo do contrato).</p>
                </div>
                <div class="py-5 md:border-b md:border-white/10">
                    <p class="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-2 flex items-center">{icone('home', 'mr-2')} De Onde Vem essa Taxa</p>
                    <p class="text-slate-300 text-sm font-light leading-relaxed">A taxa de {taxa_fmt}% a.a. mostrada aqui é a taxa média efetivamente contratada pelo {banco_exib} no financiamento imobiliário com taxas de mercado, apurada mensalmente pelo Banco Central (BACEN) — não é uma taxa promocional "a partir de". Sua taxa final depende do seu relacionamento com o banco e da análise de crédito.</p>
                </div>
                <div class="py-5 pb-0 md:pb-0">
                    <p class="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-2 flex items-center">{icone('trending-up', 'mr-2')} TR (Taxa Referencial)</p>
                    <p class="text-slate-300 text-sm font-light leading-relaxed">Um índice que alguns bancos usam, além dos juros, para corrigir sua parcela mês a mês. Está próxima de zero há vários anos, mas pode voltar a subir — por isso a parcela combinada no contrato pode variar um pouco em relação à simulação daqui.</p>
                </div>
                <div class="py-5 pb-0 md:pb-0">
                    <p class="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-2 flex items-center">{icone('percent', 'mr-2')} Renda Mínima Necessária</p>
                    <p class="text-slate-300 text-sm font-light leading-relaxed">Os bancos não aprovam um financiamento cuja parcela ultrapasse 30% da sua renda familiar bruta mensal (a chamada regra de comprometimento de renda). Boa notícia: você pode somar a sua renda com a do cônjuge ou companheiro(a) para atingir esse limite.</p>
                </div>
            </div>
        </div>

        <!-- ZONA DE MONETIZAÇÃO (INFO PRODUTO) — deliberadamente longe do
             banner "Financia Tudo" (que fica logo após o comparativo
             SAC/PRICE), separada por todo o Glossário. Os dois eram dois
             CTAs fortes colados um no outro, competindo pela mesma atenção
             — agora cada um tem seu próprio momento na leitura da página. -->
        <div class="mt-16 bg-gradient-to-r from-emerald-900/40 to-slate-900 border border-emerald-500/30 p-8 md:p-10 rounded-3xl flex flex-col md:flex-row items-center gap-8 relative overflow-hidden">
            <div class="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 rounded-full blur-[80px]"></div>

            <div class="md:w-2/3 relative z-10 text-left">
                <span class="bg-emerald-500 text-slate-950 text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-widest mb-4 inline-block">Recomendado</span>
                <h3 class="text-2xl md:text-3xl font-serif text-white mb-3">Planilha de Amortização Inteligente</h3>
                <p class="text-slate-300 text-sm md:text-base font-light leading-relaxed mb-6">
                    Descubra o segredo matemático para quitar seu contrato de {prazo_max_banco} meses em menos de 5 anos. Uma ferramenta completa para simular cenários exatos, controlar suas parcelas e economizar centenas de milhares de reais em juros bancários.
                </p>
                <a href="https://go.hotmart.com/S107394856P" target="_blank" rel="noopener sponsored" class="inline-flex items-center justify-center bg-white text-slate-950 hover:bg-slate-200 font-bold px-8 py-4 rounded-xl transition-all shadow-[0_0_20px_rgba(255,255,255,0.1)] text-sm tracking-wide w-full md:w-auto">
                    Quero Baixar a Planilha {icone('download', 'ml-3')}
                </a>
            </div>

            <div class="md:w-1/3 flex justify-center relative z-10">
                <div class="w-32 h-40 bg-slate-800 rounded-xl border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.5)] flex items-center justify-center rotate-6 hover:rotate-0 transition-transform duration-500 relative">
                    <div class="absolute -top-3 -right-3 bg-emerald-500 text-slate-950 text-[10px] font-bold px-2 py-1 rounded-md shadow-lg">100% OFF</div>
                    <span class="text-6xl text-emerald-500 drop-shadow-[0_0_15px_rgba(16,185,129,0.5)]">{icone('file-excel')}</span>
                </div>
            </div>
        </div>

        <!-- ZONA C: LINKAGEM INTERNA -->
        <div class="mt-16 pt-8 border-t border-white/5">
            <h3 class="text-sm font-serif text-slate-400 mb-6 flex items-center justify-center">
                {icone('link', 'mr-2 text-emerald-500/50')} Veja Outras Simulações do {banco_exib}
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {links_internos_html}
            </div>
        </div>

        <!-- ZONA D: FAQ VISUAL -->
        <div class="mt-16 mb-8">
            <h3 class="text-2xl font-serif text-white mb-6 text-center">Perguntas Frequentes</h3>
            <div class="space-y-3 max-w-3xl mx-auto">
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h4 class="text-emerald-400 font-bold text-sm">{faq_q1}</h4>
                        <span class="faq-toggle-icon shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_a1}</p>
                </details>
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h4 class="text-emerald-400 font-bold text-sm">{faq_q2}</h4>
                        <span class="faq-toggle-icon shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_a2}</p>
                </details>
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h4 class="text-emerald-400 font-bold text-sm">{faq_q3}</h4>
                        <span class="faq-toggle-icon shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_a3}</p>
                </details>
            </div>
        </div>

    </main>

    <!-- FOOTER COM SUPORTE HUMANO DISCRETO -->
    <footer class="border-t border-white/5 py-8 mt-10">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p class="text-slate-600 text-xs mb-4">Datalab Global © Todos os direitos reservados. Marca de {EMPRESA_RODAPE}. <a href="https://www.datalabglobal.com/privacidade/" class="underline hover:text-emerald-500">Privacidade</a> · <a href="https://www.datalabglobal.com/termos/" class="underline hover:text-emerald-500">Termos</a></p>
            <div class="flex items-center justify-center gap-4">
                <a href="https://www.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Outros produtos Datalab</a>
                <a href="https://www.datalabglobal.com/pix-no-cartao/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Pix no cartão</a>
                <a href="https://dados.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Lente B2B: dados de empresas</a>
                <a href="/aprenda" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Aprenda</a>
                <a href="/sobre" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Sobre</a>
                <a href="{LINK_WHATSAPP_SUPORTE}" target="_blank" rel="noopener" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">
                    {icone('whatsapp', 'mr-1')} Falar com o suporte
                </a>
            </div>
        </div>
    </footer>

    <script>
        const REGRA_PRAZO_MAX = {prazo_max_banco};
        const REGRA_PERC_ENTRADA_MIN = {perc_entrada_minima};
        const BANCOS_JS = {bancos_json_atual};
        const BANCO_ATUAL_CHAVE = {json.dumps(banco, ensure_ascii=False)};
    </script>
    <script src="calculo.js"></script>
    <script>
        window.onload = function() {{
            initMask('input_imovel'); initMask('input_entrada'); initMask('input_amortizar');
            syncSliderInput('slider_imovel', 'input_imovel'); syncSliderInput('slider_entrada', 'input_entrada'); syncSliderInput('slider_amortizar', 'input_amortizar');
            document.getElementById('input_prazo').addEventListener('input', calcularTudo);
            document.getElementById('input_taxa').addEventListener('input', calcularTudo);
            document.getElementById('slider_periodicidade').addEventListener('input', calcularTudo);
            document.querySelectorAll('input[name="sistema"]').forEach(r => r.addEventListener('change', calcularTudo));
            document.getElementById('slider_imovel').value = {valor_imovel};
            document.getElementById('input_imovel').value = formatCurrency({valor_imovel});
            calcularTudo();
            ajustarTooltips();
        }};
    </script>
</body>
</html>'''
            caminho_arquivo = os.path.join(pasta_saida, f"{slug}.html")
            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                f.write(corrigir_concordancia(html_content))
            # só entra no sitemap o que é indexável (ver PRAZOS_INDEXAVEIS)
            if prazo in PRAZOS_INDEXAVEIS:
                urls_sitemap.append(url_canonica)

    # Páginas-hub por banco + página comparativa entre os 15 — capturam
    # buscas "guarda-chuva" (ex: "financiamento imobiliário caixa",
    # "taxa de juros itaú 2026", "comparar bancos financiamento imobiliário")
    # que as 560 páginas de simulação (caudas longas, valor+prazo exatos)
    # não alcançam sozinhas. Também reforçam o cluster de autoridade
    # temática por banco: cada página de simulação agora linka de volta
    # pro hub do seu banco (ver link real no cabeçalho, acima).
    urls_hub = gerar_hub_bancos(pasta_saida, links_por_banco, data_ultima_atualizacao, dominio, taxas_atuais_por_banco)
    url_comparador = gerar_comparador_bancos(pasta_saida, data_ultima_atualizacao, dominio, taxas_atuais_por_banco)
    urls_comparacao = gerar_paginas_comparacao(pasta_saida, dominio, data_ultima_atualizacao, taxas_atuais_por_banco, lookup_paginas)
    urls_comparacao += gerar_dados_abertos(pasta_saida, dominio, data_ultima_atualizacao)
    gerar_embed(pasta_saida, dominio, data_ultima_atualizacao, taxas_atuais_por_banco)
    urls_comparacao += gerar_pagina_incorporar(pasta_saida, dominio, data_ultima_atualizacao)
    urls_comparacao += gerar_pagina_imprensa(pasta_saida, dominio, data_ultima_atualizacao, taxas_atuais_por_banco)

    gerar_index_home(pasta_saida, links_por_banco, data_ultima_atualizacao)
    url_sobre = gerar_pagina_sobre(pasta_saida, dominio)
    urls_aprenda = [
        gerar_pagina_aprenda(art, pasta_saida, dominio, data_ultima_atualizacao)
        for art in ARTIGOS_APRENDA
    ]
    url_aprenda_hub = gerar_hub_aprenda(ARTIGOS_APRENDA, pasta_saida, dominio)
    gerar_sitemap(
        urls_sitemap + urls_hub + [url_comparador, url_sobre, url_aprenda_hub] + urls_comparacao + urls_aprenda,
        pasta_saida, dominio, data_ultima_atualizacao,
    )
    gerar_robots_txt(pasta_saida, dominio)
    with open(os.path.join(pasta_saida, "calculo.js"), "w", encoding="utf-8") as f:
        f.write(gerar_calculo_js())
    # Logo oficial (21/set/2026): logo-full.png, favicon*.png/.ico, apple-touch-icon.png, logo-schema.png e og-image.png sao
    # arquivos ESTATICOS comitados em paginas_seo/ (gerados a partir do logo original, ver projeto datalab-global-hub/
    # make_logo_assets.py). O logo.svg/favicon.svg desenhados a mao foram aposentados.
    # rasterizar_favicon_png() NÃO roda aqui: ela depende de
    # svglib/reportlab/pycairo (instaladas só localmente pra esta tarefa
    # pontual, não em requirements.txt) — colocar essa dependência no
    # pipeline automático mensal (.github/workflows/atualiza_taxas.yml,
    # ubuntu-latest) arriscaria quebrar o deploy inteiro por causa de um
    # asset que não muda mês a mês (o ícone da marca não depende da
    # taxa de juros). favicon.ico/apple-touch-icon.png/logo-schema.png
    # são gerados manualmente (rode rasterizar_favicon_png(pasta_saida)
    # à mão quando o desenho do ícone mudar) e ficam comitados como
    # arquivo estático em paginas_seo/, no mesmo espírito de _headers/
    # _redirects/404.html — esta função nunca sobrescreve nem apaga
    # esses 3 arquivos, só o favicon.svg (puro código, sem dependência
    # nova, seguro rodar sempre).
    gerar_llms_txt(pasta_saida, dominio, len(urls_sitemap), data_ultima_atualizacao)
    print(f"✅ {len(urls_sitemap)} páginas geradas em '{pasta_saida}/'.")
    print(f"✅ {len(urls_hub)} páginas-hub por banco + 1 página comparativa geradas.")


def gerar_hub_bancos(pasta_saida, links_por_banco, data_ultima_atualizacao, dominio, taxas_atuais=None):
    """Gera uma página-hub por banco (ex: banco-caixa.html): visão geral de
    taxa/entrada/prazo, posição do banco na faixa de CET do mercado, e um
    índice completo de todas as simulações daquele banco. Existe pra
    capturar buscas mais genéricas ("financiamento imobiliário caixa",
    "taxa de juros itaú 2026") que as páginas de simulação — otimizadas
    pra caudas longas tipo "simulador caixa 500 mil 30 anos" — não
    capturam sozinhas, e pra dar ao Google um "resumo" por banco que
    reforça o cluster de autoridade temática de cada silo.

    taxas_atuais: ver taxas_atuais_de/comparar_todos_bancos — sem isso o
    resumo da página (taxa exibida) e a faixa de posição no mercado
    ficavam com o taxa_padrao estático de bancos.py mesmo depois do ETL
    atualizar dados.csv (achado real, 06/set/2026: a taxa do Banco do
    Brasil aqui mostrava 11,69% enquanto a página de simulação individual
    já mostrava 14,42%, a taxa nova do BACEN).

    Retorna a lista de URLs geradas (pro sitemap)."""
    ano_atual = date.today().year
    # Cenário de referência único (igual em toda página-hub e na página
    # comparativa) pra a faixa de CET ser comparável entre bancos — sem
    # isso, cada hub mostraria uma faixa calculada num cenário diferente.
    VALOR_REF, PRAZO_REF = 500_000, 360
    ranking_ref = comparar_todos_bancos(VALOR_REF, PRAZO_REF, {}, taxas_atuais)
    cet_min_mercado = ranking_ref[0]["cet"] if ranking_ref else 0
    cet_max_mercado = ranking_ref[-1]["cet"] if ranking_ref else 0

    urls = []
    for banco, links in links_por_banco.items():
        regra = obter_regra(banco)
        banco_exib = nome_exibicao(banco)
        slug_hub = slug_hub_banco(banco)
        url_canonica = f"{dominio}/{slug_hub}"
        url_logo_banco = f"https://www.google.com/s2/favicons?domain={regra['dominio_favicon']}&sz=128"
        taxa_atual_banco = (taxas_atuais or {}).get(banco, regra["taxa_padrao"])
        taxa_fmt = f"{taxa_atual_banco:.2f}".replace('.', ',')
        entrada_min_pct = round((1 - regra['ltv']) * 100)
        prazo_max = regra['prazo_max']
        anos_max = prazo_max // 12

        cet_banco_ref = next((r["cet"] for r in ranking_ref if r["banco"] == banco), None)

        faixa_html = ""
        if cet_banco_ref is not None and cet_max_mercado > cet_min_mercado:
            marcador_pct = calcular_marcador_posicao_mercado(ranking_ref, banco)
            cet_banco_fmt = f"{cet_banco_ref:.2f}".replace('.', ',')
            cet_min_fmt = f"{cet_min_mercado:.2f}".replace('.', ',')
            cet_max_fmt = f"{cet_max_mercado:.2f}".replace('.', ',')
            faixa_html = f'''<div class="mt-8 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl p-6">
                <div class="flex items-center gap-2 mb-4">
                    <span class="text-yellow-400 text-xl leading-none">{icone('lightbulb')}</span>
                    <span class="bg-emerald-500 text-slate-950 text-[9px] font-black px-2 py-0.5 rounded-full uppercase tracking-widest">Dica</span>
                    <span class="text-slate-300 text-[11px] font-bold uppercase tracking-widest">Posição do {banco_exib} no Mercado</span>
                    {tooltip(f'CET simulado para {formatar_reais(VALOR_REF)} em {PRAZO_REF} meses, mesma condição usada em todos os bancos que acompanhamos, pra comparação justa.')}
                </div>
                <div class="space-y-2">
                    <div class="relative h-2 rounded-full bg-gradient-to-r from-emerald-500 via-amber-400 to-rose-500">
                        <div class="absolute top-1/2 h-4 w-4 rounded-full bg-white border-2 border-emerald-950 shadow-[0_0_0_3px_rgba(16,185,129,0.35)]" style="left:{marcador_pct}%; transform:translate(-50%,-50%)" title="{banco_exib}: {cet_banco_fmt}%"></div>
                    </div>
                    <div class="flex justify-between text-[10px] text-slate-400 uppercase tracking-wide">
                        <span>{cet_min_fmt}% menor CET</span>
                        <span>{cet_max_fmt}% maior CET</span>
                    </div>
                </div>
                <p class="text-slate-300 text-xs font-light leading-relaxed mt-4">
                    Pra {formatar_reais(VALOR_REF)} em {PRAZO_REF} meses, o CET do {banco_exib} fica em <strong class="text-emerald-400">{cet_banco_fmt}%</strong>, dentro de uma faixa de mercado que vai de {cet_min_fmt}% a {cet_max_fmt}%.
                    <a href="{LINK_FINANCIA_TUDO}" target="_blank" rel="noopener sponsored" class="text-emerald-400 underline hover:text-emerald-300 block mt-2 font-semibold">Peça uma análise gratuita com a Financia Tudo →</a>
                </p>
            </div>'''

        # Índice completo das simulações do banco, agrupado por prazo (cada
        # banco só tem 1-2 prazos distintos: 360 e/ou o prazo_max) e
        # ordenado por valor — mais fácil de escanear que a lista solta
        # usada no card compacto do index.html.
        por_prazo = {}
        for item in sorted(links, key=lambda p: float(p['linha_original']['valor_imovel'])):
            por_prazo.setdefault(item['prazo_correto'], []).append(item)

        blocos_prazo_html = ""
        for prazo_grupo in sorted(por_prazo.keys()):
            itens = por_prazo[prazo_grupo]
            anos_grupo = prazo_grupo // 12
            links_grid = "".join(f'''
                <a href="{item['slug']}" class="group flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10 hover:border-emerald-500/50 hover:bg-white/10 transition-all">
                    <span class="text-xs text-slate-300 group-hover:text-white">{formatar_reais(float(item['linha_original']['valor_imovel']))[3:]}</span>
                    <svg class="w-3 h-3 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                </a>''' for item in itens)
            blocos_prazo_html += f'''
            <div class="mt-6">
                <h3 class="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-3">{prazo_grupo} meses ({anos_grupo} anos)</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3">{links_grid}</div>
            </div>'''

        faq_q1 = f"Qual a taxa de juros do {regra['mod'].lower()} no {banco_exib}?"
        faq_a1 = f"A taxa padrão estimada do {banco_exib} é de {taxa_fmt}% ao ano, atualizada em {data_ultima_atualizacao}. A taxa final aprovada depende do seu relacionamento com o banco e da análise de crédito."
        faq_q2 = f"Qual a entrada mínima exigida pelo {banco_exib}?"
        faq_a2 = f"O {banco_exib} exige entrada mínima de {entrada_min_pct}% do valor do imóvel (LTV de {round(regra['ltv']*100)}%)."
        faq_q3 = f"Qual o prazo máximo de financiamento no {banco_exib}?"
        faq_a3 = f"O {banco_exib} financia em até {prazo_max} meses ({anos_max} anos)."

        # Achado real (20/set/2026, Search Console — Consultas dos últimos 28
        # dias): TODAS as consultas que já geram impressão pro simulador são
        # da forma "simulador <banco>" ("simulador inter", "simulador
        # sicredi", "simulador santander financiamento", "poupex
        # simulador"...). O <title> e o <h1> desta página de banco NÃO
        # continham a palavra "simulador" — na prática o título ao vivo era
        # o fallback "<Banco>: Taxas de Financiamento Imobiliário 2026",
        # porque a versão longa passava de 60 caracteres. A palavra que a
        # pessoa digita agora abre o título (e o H1), que é onde o Google
        # mais pesa relevância; o fallback sem marca continua existindo
        # pra nome de banco longo.
        titulo_pagina = f"Simulador {banco_exib}: Financiamento Imobiliário {ano_atual} | Datalab Global"
        if len(titulo_pagina) > 60:
            titulo_pagina = f"Simulador {banco_exib}: Financiamento Imobiliário {ano_atual}"
        meta_description = (
            f"Simulador de {regra['mod'].lower()} {banco_exib} em {ano_atual}: taxa de {taxa_fmt}% a.a., "
            f"entrada a partir de {entrada_min_pct}%, até {prazo_max} meses. Calcule parcela e CET."
        )[:160]

        schema_breadcrumb = f'''{{
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{ "@type": "ListItem", "position": 1, "name": "Datalab Global", "item": "{dominio}/" }},
        {{ "@type": "ListItem", "position": 2, "name": "{banco_exib}", "item": "{url_canonica}" }}
      ]
    }}'''
        schema_faq = f'''{{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {{ "@type": "Question", "name": "{faq_q1}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_a1}" }} }},
        {{ "@type": "Question", "name": "{faq_q2}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_a2}" }} }},
        {{ "@type": "Question", "name": "{faq_q3}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_a3}" }} }}
      ]
    }}'''

        html_hub = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
{render_head_boilerplate(titulo_pagina, meta_description, url_canonica, dominio, [schema_breadcrumb, schema_faq])}
</head>
<body class="antialiased flex flex-col min-h-screen">
    <nav class="border-b border-white/5 sticky top-0 z-50 backdrop-blur-2xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="/" class="flex items-center">
                    <img src="logo-full.png" alt="Datalab Global" width="122" height="48" class="h-12 md:h-16 w-auto drop-shadow-[0_0_15px_rgba(16,185,129,0.2)] hover:scale-105 transition-transform duration-300">
                </a>
                <div class="flex items-center gap-1">
                    <a href="/aprenda" aria-label="Aprenda" class="inline-flex items-center gap-1.5 -my-2.5 p-2.5 text-xs text-slate-400 hover:text-emerald-400 transition-colors">{icone('book-open')} <span class="hidden sm:inline">Aprenda</span></a>
                    <div class="hidden md:flex items-center">
                        <a href="{LINK_FINANCIA_TUDO}" target="_blank" rel="noopener sponsored" class="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-6 py-2.5 rounded-full font-bold transition-all text-sm flex items-center shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                            Fazer Análise Grátis {icone('arrow-right', 'ml-2 text-sm')}
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <header class="py-12 md:py-16 relative z-10 text-center">
        <div class="inline-flex items-center gap-2.5 bg-white/5 border border-white/10 rounded-full pl-2 pr-4 py-1.5 mb-6">
            {favicon_com_fallback(url_logo_banco, banco_exib, "w-6 h-6")}
            <span class="text-xs font-bold text-slate-200 tracking-wide">{banco_exib}</span>
            <span class="text-[10px] text-slate-400 uppercase tracking-widest border-l border-white/10 pl-2">{regra['mod']}</span>
        </div>
        <h1 class="text-3xl md:text-5xl font-serif text-white mb-4 leading-tight px-4">
            Simulador de Financiamento Imobiliário {banco_exib}: Taxas e Condições
        </h1>
        <p class="text-slate-400 text-base md:text-lg font-light tracking-wide max-w-3xl mx-auto px-4">
            Visão geral das condições do {banco_exib} — taxa de juros, entrada mínima e prazo — e o índice completo das nossas simulações prontas pra esse banco.
        </p>
        <p class="text-slate-600 text-[10px] uppercase tracking-widest mt-4">Taxas atualizadas em {date.fromisoformat(data_ultima_atualizacao).strftime('%d/%m/%Y')} · {texto_fonte_taxa(banco)}</p>
    </header>

    <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex-grow w-full relative z-10">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="glass-panel-emerald rounded-2xl p-6 text-center">
                <span class="text-emerald-400 text-2xl">{icone('percent')}</span>
                <p class="text-slate-400 text-[10px] uppercase tracking-widest mt-3 mb-1">Taxa de Juros</p>
                <p class="text-2xl font-serif text-white">{taxa_fmt}% <span class="text-sm text-slate-400 font-sans">a.a.</span></p>
            </div>
            <div class="glass-panel-emerald rounded-2xl p-6 text-center">
                <span class="text-emerald-400 text-2xl">{icone('trending-up')}</span>
                <p class="text-slate-400 text-[10px] uppercase tracking-widest mt-3 mb-1">Entrada Mínima</p>
                <p class="text-2xl font-serif text-white">{entrada_min_pct}%</p>
            </div>
            <div class="glass-panel-emerald rounded-2xl p-6 text-center">
                <span class="text-emerald-400 text-2xl">{icone('calendar')}</span>
                <p class="text-slate-400 text-[10px] uppercase tracking-widest mt-3 mb-1">Prazo Máximo</p>
                <p class="text-2xl font-serif text-white">{prazo_max}x <span class="text-sm text-slate-400 font-sans">({anos_max} anos)</span></p>
            </div>
        </div>

        {faixa_html}

        <div class="mt-16 pt-8 border-t border-white/5">
            <h2 class="text-sm font-serif text-slate-400 mb-2 flex items-center justify-center">
                {icone('link', 'mr-2 text-emerald-500/50')} Todas as Simulações do {banco_exib}
            </h2>
            <p class="text-slate-600 text-xs text-center max-w-xl mx-auto">Escolha um valor abaixo pra abrir o simulador completo, com cálculo de parcelas, CET e amortização.</p>
            {blocos_prazo_html}
        </div>

        <div class="mt-16 bg-gradient-to-r from-emerald-600 to-emerald-900 rounded-3xl p-8 md:p-12 relative overflow-hidden shadow-[0_20px_50px_rgba(16,185,129,0.3)] border border-emerald-400/50">
            <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-[80px]"></div>
            <div class="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10">
                <div class="md:w-2/3 text-left">
                    <div class="flex items-center gap-3 mb-4">
                        <span class="bg-yellow-400 text-yellow-950 text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest">Parceria Oficial</span>
                        <span class="flex items-center text-emerald-200 text-xs font-medium">{icone('shield-check', 'mr-1')} 100% Seguro</span>
                    </div>
                    <h3 class="text-3xl font-serif text-white mb-3">Aprove o seu crédito no {banco_exib} sem sair de casa.</h3>
                    <p class="text-emerald-100 text-sm md:text-base font-light leading-relaxed">
                        Como parceiros credenciados, conectamos você diretamente à mesa de crédito para buscar as <strong>melhores taxas e condições de aprovação</strong>. Análise gratuita, rápida e sem compromisso.
                    </p>
                </div>
                <div class="md:w-1/3 w-full flex justify-center md:justify-end">
                    <a href="{LINK_FINANCIA_TUDO}" target="_blank" rel="noopener sponsored" class="group relative inline-flex items-center justify-center bg-white text-emerald-900 hover:bg-slate-100 font-black px-8 py-5 rounded-2xl transition-all shadow-2xl text-sm tracking-widest uppercase w-full text-center overflow-hidden">
                        <span class="relative z-10 flex items-center">Fazer Análise Grátis {icone('external-link', 'ml-3 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform')}</span>
                    </a>
                </div>
            </div>
        </div>

        <div class="mt-16 mb-8">
            <h2 class="text-2xl font-serif text-white mb-6 text-center">Perguntas Frequentes</h2>
            <div class="space-y-3 max-w-3xl mx-auto">
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h3 class="text-emerald-400 font-bold text-sm">{faq_q1}</h3>
                        <span class="faq-toggle-icon shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_a1}</p>
                </details>
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h3 class="text-emerald-400 font-bold text-sm">{faq_q2}</h3>
                        <span class="faq-toggle-icon shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_a2}</p>
                </details>
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h3 class="text-emerald-400 font-bold text-sm">{faq_q3}</h3>
                        <span class="faq-toggle-icon shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_a3}</p>
                </details>
            </div>
            <p class="text-center mt-8">
                <a href="comparador-bancos" class="text-emerald-400 hover:text-emerald-300 underline text-sm">Ver comparativo entre os {len(BANCOS)} bancos que acompanhamos →</a>
            </p>
        </div>
    </main>

    <footer class="border-t border-white/5 py-8 mt-10">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p class="text-slate-600 text-xs mb-4">Datalab Global © Todos os direitos reservados. Marca de {EMPRESA_RODAPE}. <a href="https://www.datalabglobal.com/privacidade/" class="underline hover:text-emerald-500">Privacidade</a> · <a href="https://www.datalabglobal.com/termos/" class="underline hover:text-emerald-500">Termos</a></p>
            <div class="flex items-center justify-center gap-4">
                <a href="https://www.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Outros produtos Datalab</a>
                <a href="https://www.datalabglobal.com/pix-no-cartao/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Pix no cartão</a>
                <a href="https://dados.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Lente B2B: dados de empresas</a>
                <a href="/aprenda" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Aprenda</a>
                <a href="/sobre" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Sobre</a>
                <a href="{LINK_WHATSAPP_SUPORTE}" target="_blank" rel="noopener" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">
                    {icone('whatsapp', 'mr-1')} Falar com o suporte
                </a>
            </div>
        </div>
    </footer>

    <script src="calculo.js"></script>
    <script>
        window.addEventListener('DOMContentLoaded', ajustarTooltips);
    </script>
</body>
</html>'''

        with open(os.path.join(pasta_saida, f"{slug_hub}.html"), "w", encoding="utf-8") as f:
            f.write(corrigir_concordancia(html_hub))
        urls.append(url_canonica)

    return urls


# ---------------------------------------------------------------------------
# Histórico de taxas (BACEN) e dados abertos
#
# A série vem de historico_taxas.csv (ver historico_taxas.py): taxa média
# mensal efetivamente contratada por banco, modalidade 903201 do BACEN. Só
# bancos que o BACEN cobre — BRB e Poupex (taxa estimada) ficam de fora de
# propósito, para não redistribuir como dado oficial um número que não é.
# ---------------------------------------------------------------------------

MESES_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
MESES_PT_ABREV = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
FONTE_BACEN_URL = "https://www.bcb.gov.br/estatisticas/reporttxjuros?codigoSegmento=1&codigoModalidade=903201"
LICENCA_DADOS = "CC BY 4.0"
LICENCA_DADOS_URL = "https://creativecommons.org/licenses/by/4.0/deed.pt-br"
MESES_NA_TABELA_EVOLUCAO = 6


def carregar_historico():
    """Linhas do historico_taxas.csv (lista vazia se não existir)."""
    from historico_taxas import ler_historico
    return ler_historico()


def _rotulo_mes(inicio_periodo):
    ano, mes = inicio_periodo[:4], int(inicio_periodo[5:7])
    return f"{MESES_PT_ABREV[mes - 1]}/{ano[2:]}"


def _pct2(v):
    return f"{v:.2f}".replace(".", ",")


def _sinal_pp(v):
    return ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):.2f}".replace(".", ",")


def resumo_historico(historico):
    """Estrutura pronta pra renderizar: meses (mais antigos -> mais recentes),
    linhas por banco e a maior alta/queda. None se houver menos de 2 meses."""
    meses = sorted({r["inicio_periodo"] for r in historico})[-MESES_NA_TABELA_EVOLUCAO:]
    if len(meses) < 2:
        return None
    por_banco = {}
    for r in historico:
        if r["inicio_periodo"] in meses:
            por_banco.setdefault(r["banco"], {})[r["inicio_periodo"]] = r["taxa_aa"]
    linhas = []
    for banco, serie in por_banco.items():
        if meses[0] in serie and meses[-1] in serie:
            linhas.append({"banco": banco, "banco_exib": nome_exibicao(banco), "serie": serie,
                           "variacao": serie[meses[-1]] - serie[meses[0]], "atual": serie[meses[-1]]})
    if not linhas:
        return None
    linhas.sort(key=lambda x: x["atual"])
    return {"meses": meses, "linhas": linhas,
            "maior_queda": min(linhas, key=lambda x: x["variacao"]),
            "maior_alta": max(linhas, key=lambda x: x["variacao"])}


def html_evolucao_taxas(resumo):
    """Tabela banco x meses (taxa média contratada, % a.a.) + variação."""
    if not resumo:
        return ""
    cab = "".join(f'<th scope="col" class="px-2 py-2 text-right font-medium whitespace-nowrap">{_rotulo_mes(m)}</th>' for m in resumo["meses"])
    corpo = ""
    for x in resumo["linhas"]:
        celulas = ""
        for m in resumo["meses"]:
            valor = _pct2(x["serie"][m]) if m in x["serie"] else "–"
            celulas += f'<td class="px-2 py-2 text-right whitespace-nowrap">{valor}</td>'
        cor = "text-emerald-400" if x["variacao"] < 0 else "text-rose-400" if x["variacao"] > 0 else "text-slate-400"
        corpo += (f'<tr class="border-t border-white/5"><th scope="row" class="px-2 py-2 text-left font-medium text-white whitespace-nowrap">{x["banco_exib"]}</th>'
                  f'{celulas}<td class="px-2 py-2 text-right font-bold whitespace-nowrap {cor}">{_sinal_pp(x["variacao"])} p.p.</td></tr>')
    return f'''<section class="mt-16">
            <h2 class="text-2xl font-serif text-white mb-2">Como as taxas evoluíram nos últimos {len(resumo["meses"])} meses</h2>
            <p class="text-slate-400 text-xs font-light leading-relaxed mb-4">Taxa média mensal de juros efetivamente contratada no financiamento imobiliário (% ao ano), por banco, segundo o Banco Central. É a taxa praticada, não uma oferta: a sua proposta pode ser diferente.</p>
            <div class="overflow-x-auto rounded-xl border border-white/10">
                <table class="w-full text-xs text-slate-300">
                    <thead class="text-[10px] uppercase tracking-widest text-slate-400"><tr><th scope="col" class="px-2 py-2 text-left font-medium">Banco</th>{cab}<th scope="col" class="px-2 py-2 text-right font-medium whitespace-nowrap">Variação</th></tr></thead>
                    <tbody>{corpo}</tbody>
                </table>
            </div>
            <p class="text-slate-500 text-[11px] mt-3">Bancos que o BACEN não cobre nesta modalidade (BRB e Poupex) não entram na série. Fonte: <a href="{FONTE_BACEN_URL}" rel="noopener" class="underline">Banco Central do Brasil</a>.</p>
        </section>'''


def texto_variacao(resumo):
    """Frase com os números do período, pro FAQ (None sem histórico)."""
    if not resumo:
        return None
    m0, m1 = resumo["meses"][0], resumo["meses"][-1]
    q, a = resumo["maior_queda"], resumo["maior_alta"]
    frase = (f"Entre {_rotulo_mes(m0)} e {_rotulo_mes(m1)}, a maior queda na taxa média contratada foi a de {q['banco_exib']} "
             f"({_sinal_pp(q['variacao'])} p.p., de {_pct2(q['serie'][m0])}% para {_pct2(q['serie'][m1])}% a.a.)")
    if a["variacao"] > 0:
        frase += (f" e a maior alta, a de {a['banco_exib']} ({_sinal_pp(a['variacao'])} p.p., "
                  f"de {_pct2(a['serie'][m0])}% para {_pct2(a['serie'][m1])}% a.a.)")
    return frase + ". São médias mensais do Banco Central, não ofertas."


def gerar_dados_abertos(pasta_saida, dominio, data_ultima_atualizacao):
    """Publica a série histórica como dados abertos em /dados/ (CSV, JSON,
    datapackage.json e README.md) e a página /dados-abertos. Só linhas do
    BACEN. Retorna a lista de URLs de página (pro sitemap)."""
    historico = carregar_historico()
    if not historico:
        return []
    pasta_dados = os.path.join(pasta_saida, "dados")
    os.makedirs(pasta_dados, exist_ok=True)
    meses = sorted({r["inicio_periodo"] for r in historico})
    ini, fim = meses[0], max(r["fim_periodo"] for r in historico)
    campos = ["periodo_inicio", "periodo_fim", "instituicao", "taxa_juros_aa_pct"]
    linhas = [{"periodo_inicio": r["inicio_periodo"], "periodo_fim": r["fim_periodo"],
               "instituicao": nome_exibicao(r["banco"]), "taxa_juros_aa_pct": round(r["taxa_aa"], 2)} for r in historico]

    import csv as _csv
    with open(os.path.join(pasta_dados, "taxas-financiamento-imobiliario.csv"), "w", encoding="utf-8", newline="") as f:
        w = _csv.DictWriter(f, fieldnames=campos, lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)
    with open(os.path.join(pasta_dados, "taxas-financiamento-imobiliario.json"), "w", encoding="utf-8") as f:
        json.dump({
            "titulo": "Taxas médias de juros do financiamento imobiliário por banco (BACEN)",
            "fonte": FONTE_BACEN_URL, "licenca": LICENCA_DADOS, "atualizado_em": data_ultima_atualizacao,
            "organizacao": "Datalab Global", "dados": linhas,
        }, f, ensure_ascii=False, indent=1)

    url_pagina = f"{dominio}/dados-abertos"
    descricao = ("Taxa média mensal de juros efetivamente contratada no financiamento imobiliário (aquisição de imóveis, "
                 "pessoa física, taxa pré-fixada), por banco, em % ao ano, segundo o Banco Central do Brasil. "
                 f"Cobre {len(meses)} meses ({_rotulo_mes(ini)} a {_rotulo_mes(meses[-1])}) e {len({r['banco'] for r in historico})} instituições.")
    citacao = f"Datalab Global. Taxas médias de juros do financiamento imobiliário por banco (dados do BACEN). {url_pagina}, acesso em {{data}}."
    with open(os.path.join(pasta_dados, "datapackage.json"), "w", encoding="utf-8") as f:
        json.dump({
            "name": "taxas-financiamento-imobiliario", "title": "Taxas médias de juros do financiamento imobiliário por banco (BACEN)",
            "description": descricao, "licenses": [{"name": "CC-BY-4.0", "path": LICENCA_DADOS_URL, "title": LICENCA_DADOS}],
            "sources": [{"title": "Banco Central do Brasil — Taxas de juros por instituição financeira", "path": FONTE_BACEN_URL}],
            "contributors": [{"title": "Datalab Global", "role": "publisher", "path": f"{dominio}/"}],
            "resources": [{"name": "taxas", "path": "taxas-financiamento-imobiliario.csv", "format": "csv", "mediatype": "text/csv", "encoding": "utf-8",
                           "schema": {"fields": [
                               {"name": "periodo_inicio", "type": "date", "description": "Primeiro dia do mês de referência"},
                               {"name": "periodo_fim", "type": "date", "description": "Último dia do mês de referência"},
                               {"name": "instituicao", "type": "string", "description": "Banco (nome comercial)"},
                               {"name": "taxa_juros_aa_pct", "type": "number", "description": "Taxa média de juros contratada, % ao ano"}]}}],
        }, f, ensure_ascii=False, indent=1)
    with open(os.path.join(pasta_dados, "README.md"), "w", encoding="utf-8") as f:
        f.write(f"""# Taxas médias de juros do financiamento imobiliário por banco

{descricao}

- **Fonte original:** [Banco Central do Brasil]({FONTE_BACEN_URL}), modalidade 903201.
- **Licença:** {LICENCA_DADOS} ({LICENCA_DADOS_URL}). Pode usar, copiar e adaptar, citando a fonte.
- **Atualização:** mensal. Última atualização: {data_ultima_atualizacao}.
- **Arquivos:** `taxas-financiamento-imobiliario.csv`, `taxas-financiamento-imobiliario.json`, `datapackage.json`.
- **Colunas:** `periodo_inicio`, `periodo_fim`, `instituicao`, `taxa_juros_aa_pct`.
- **Limites:** são médias do que foi efetivamente contratado, não ofertas. BRB e Poupex não constam porque o BACEN não os cobre nesta modalidade.

## Como citar

{citacao.format(data="AAAA-MM-DD")}

Publicado por Datalab Global ({dominio}/), marca de {EMPRESA_RODAPE}.
""")

    schema_dataset = json.dumps({
        "@context": "https://schema.org", "@type": "Dataset",
        "name": "Taxas médias de juros do financiamento imobiliário por banco (BACEN)",
        "description": descricao, "url": url_pagina, "inLanguage": "pt-BR",
        "license": LICENCA_DADOS_URL, "isAccessibleForFree": True,
        "creator": {"@type": "Organization", "name": "Datalab Global", "url": f"{dominio}/"},
        "isBasedOn": FONTE_BACEN_URL, "dateModified": data_ultima_atualizacao,
        "temporalCoverage": f"{ini}/{fim}", "spatialCoverage": {"@type": "Country", "name": "Brasil"},
        "variableMeasured": ["Taxa média de juros contratada (% ao ano)"],
        "distribution": [
            {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": f"{dominio}/dados/taxas-financiamento-imobiliario.csv"},
            {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": f"{dominio}/dados/taxas-financiamento-imobiliario.json"},
        ],
    }, ensure_ascii=False)
    schema_breadcrumb = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Datalab Global", "item": f"{dominio}/"},
            {"@type": "ListItem", "position": 2, "name": "Dados abertos", "item": url_pagina},
        ],
    }, ensure_ascii=False)
    titulo_pagina = "Dados abertos: taxas de financiamento imobiliário por banco | Datalab Global"
    meta_description = f"Baixe grátis a série de {len(meses)} meses de taxas de juros do financiamento imobiliário por banco, do Banco Central, em CSV e JSON ({LICENCA_DADOS})."
    resumo = resumo_historico(historico)
    html_pagina = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
{render_head_boilerplate(titulo_pagina, meta_description, url_pagina, dominio, [schema_breadcrumb, schema_dataset])}
</head>
<body class="antialiased flex flex-col min-h-screen">
    {_nav_comparacao()}

    <header class="py-12 md:py-16 relative z-10 text-center">
        <h1 class="text-3xl md:text-5xl font-serif text-white mb-4 leading-tight px-4">Dados abertos: taxas de financiamento imobiliário</h1>
        <p class="text-slate-400 text-base md:text-lg font-light tracking-wide max-w-3xl mx-auto px-4">
            Série mensal de {len(meses)} meses, por banco, com dados do Banco Central. Livre para usar, com citação da fonte ({LICENCA_DADOS}).
        </p>
    </header>

    <main class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex-grow w-full relative z-10">
        <section>
            <h2 class="text-2xl font-serif text-white mb-3">Baixar</h2>
            <ul class="space-y-2 text-sm">
                <li><a href="dados/taxas-financiamento-imobiliario.csv" download class="text-emerald-400 underline">taxas-financiamento-imobiliario.csv</a> <span class="text-slate-400">· planilha (UTF-8, vírgula)</span></li>
                <li><a href="dados/taxas-financiamento-imobiliario.json" download class="text-emerald-400 underline">taxas-financiamento-imobiliario.json</a> <span class="text-slate-400">· para programação</span></li>
                <li><a href="dados/datapackage.json" download class="text-emerald-400 underline">datapackage.json</a> <span class="text-slate-400">· metadados (Frictionless Data)</span></li>
                <li><a href="dados/README.md" class="text-emerald-400 underline">README.md</a> <span class="text-slate-400">· descrição e como citar</span></li>
            </ul>
        </section>

        <section class="mt-10">
            <h2 class="text-2xl font-serif text-white mb-3">O que há nos dados</h2>
            <p class="text-slate-300 text-sm font-light leading-relaxed">{descricao}</p>
            <table class="w-full text-xs text-slate-300 mt-4 rounded-xl border border-white/10">
                <thead class="text-[10px] uppercase tracking-widest text-slate-400"><tr><th scope="col" class="px-3 py-2 text-left font-medium">Coluna</th><th scope="col" class="px-3 py-2 text-left font-medium">Descrição</th></tr></thead>
                <tbody>
                    <tr class="border-t border-white/5"><th scope="row" class="px-3 py-2 text-left font-mono font-normal">periodo_inicio</th><td class="px-3 py-2">Primeiro dia do mês de referência (AAAA-MM-DD)</td></tr>
                    <tr class="border-t border-white/5"><th scope="row" class="px-3 py-2 text-left font-mono font-normal">periodo_fim</th><td class="px-3 py-2">Último dia do mês de referência</td></tr>
                    <tr class="border-t border-white/5"><th scope="row" class="px-3 py-2 text-left font-mono font-normal">instituicao</th><td class="px-3 py-2">Banco (nome comercial)</td></tr>
                    <tr class="border-t border-white/5"><th scope="row" class="px-3 py-2 text-left font-mono font-normal">taxa_juros_aa_pct</th><td class="px-3 py-2">Taxa média de juros contratada, em % ao ano</td></tr>
                </tbody>
            </table>
            <p class="text-slate-400 text-xs font-light leading-relaxed mt-3">São médias do que foi efetivamente contratado, não ofertas: a sua proposta pode ser diferente. BRB e Poupex não constam porque o Banco Central não os cobre nesta modalidade.</p>
        </section>

        <section class="mt-10">
            <h2 class="text-2xl font-serif text-white mb-3">Como citar</h2>
            <p class="text-slate-300 text-sm font-light leading-relaxed bg-white/5 border border-white/10 rounded-xl p-4">{citacao.format(data="AAAA-MM-DD")}</p>
            <p class="text-slate-400 text-xs font-light mt-3">Licença <a href="{LICENCA_DADOS_URL}" rel="noopener" class="underline">{LICENCA_DADOS}</a>. Fonte original: <a href="{FONTE_BACEN_URL}" rel="noopener" class="underline">Banco Central do Brasil</a>. Atualizado em {date.fromisoformat(data_ultima_atualizacao).strftime('%d/%m/%Y')}.</p>
        </section>

        <section class="mt-10">
            <h2 class="text-2xl font-serif text-white mb-3">Exemplo em Python</h2>
            <pre class="bg-slate-900/60 border border-white/10 rounded-xl p-4 text-xs text-slate-300 overflow-x-auto"><code>import pandas as pd
df = pd.read_csv("{dominio}/dados/taxas-financiamento-imobiliario.csv", parse_dates=["periodo_inicio"])
df.pivot(index="periodo_inicio", columns="instituicao", values="taxa_juros_aa_pct").tail(6)</code></pre>
        </section>

        {html_evolucao_taxas(resumo)}

        <p class="mt-10 text-center text-xs text-slate-400"><a href="comparador-bancos" class="text-emerald-400 underline">Ver o comparativo de taxas entre os {len(BANCOS)} bancos →</a></p>
    </main>

    {_footer_comparacao()}
</body>
</html>'''
    with open(os.path.join(pasta_saida, "dados-abertos.html"), "w", encoding="utf-8") as f:
        f.write(corrigir_concordancia(html_pagina))
    return [url_pagina]



def gerar_comparador_bancos(pasta_saida, data_ultima_atualizacao, dominio, taxas_atuais=None):
    """Gera comparador-bancos.html: tabela com todos os bancos lado a lado
    (taxa, entrada mínima, prazo máximo, CET num cenário de referência
    único), ordenada por CET. Alvo de buscas tipo "comparar taxa
    financiamento imobiliário" / "menor taxa financiamento imobiliário
    {ano}" — termos que nenhuma página-hub ou de simulação, focadas num
    banco só, capturam sozinhas.

    taxas_atuais: ver taxas_atuais_de/comparar_todos_bancos — sem isso o
    comparador ficava com a taxa estática de bancos.py mesmo depois do
    ETL atualizar dados.csv (achado real, 06/set/2026)."""
    ano_atual = date.today().year
    d_atual = date.fromisoformat(data_ultima_atualizacao)
    mes_ano = f"{MESES_PT[d_atual.month - 1]} de {d_atual.year}"
    mes_ano_curto = f"{MESES_PT_ABREV[d_atual.month - 1]}/{d_atual.year}"
    resumo_hist = resumo_historico(carregar_historico())
    VALOR_REF, PRAZO_REF = 500_000, 360
    ranking_ref = comparar_todos_bancos(VALOR_REF, PRAZO_REF, {}, taxas_atuais)

    linhas_tabela = ""
    for i, r in enumerate(ranking_ref, start=1):
        regra = obter_regra(r["banco"])
        taxa_exibida = (taxas_atuais or {}).get(r["banco"], regra["taxa_padrao"])
        url_logo = f"https://www.google.com/s2/favicons?domain={regra['dominio_favicon']}&sz=128"
        cet_fmt = f"{r['cet']:.2f}".replace('.', ',')
        destaque = "bg-emerald-500/10 border-emerald-500/30" if i == 1 else "bg-white/5 border-white/10"
        medalha = f'<span class="text-emerald-400 font-bold text-xs">#{i}</span>' if i > 1 else f'<span class="text-yellow-400 font-bold text-xs">🏆 #1</span>'
        linhas_tabela += f'''
        <a href="{slug_hub_banco(r['banco'])}" class="grid grid-cols-[auto_1fr_auto_auto_auto] md:grid-cols-[auto_1fr_1fr_1fr_1fr] items-center gap-3 md:gap-6 p-4 rounded-xl border {destaque} hover:border-emerald-500/50 transition-all">
            <span class="w-8 text-center">{medalha}</span>
            <span class="flex items-center gap-2 min-w-0">
                {favicon_com_fallback(url_logo, r['banco_exib'], "w-6 h-6")}
                <span class="text-sm font-medium text-white truncate">{r['banco_exib']}</span>
            </span>
            <span class="text-right md:text-center text-xs text-slate-400">{taxa_exibida:.2f}%<span class="hidden md:inline"> a.a.</span></span>
            <span class="hidden md:block text-center text-xs text-slate-400">{r['entrada_perc']}% entrada</span>
            <span class="text-right text-sm font-bold text-emerald-400">{cet_fmt}% <span class="hidden md:inline text-[10px] text-slate-400 font-normal">CET</span></span>
        </a>'''

    url_canonica = f"{dominio}/comparador-bancos"
    # Mês no título e no H1: a busca real é "taxa de financiamento imobiliário
    # {mês} {ano}". Abreviado no <title> pra caber em 60 caracteres.
    titulo_pagina = f"Taxas de financiamento imobiliário por banco: {mes_ano_curto} | Datalab Global"
    meta_description = (
        f"Compare taxa, entrada mínima e CET de {len(ranking_ref)} bancos de financiamento imobiliário em {mes_ano} "
        f"e veja como as taxas evoluíram nos últimos meses."
    )[:160]

    schema_breadcrumb = f'''{{
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{ "@type": "ListItem", "position": 1, "name": "Datalab Global", "item": "{dominio}/" }},
        {{ "@type": "ListItem", "position": 2, "name": "Comparativo de Bancos", "item": "{url_canonica}" }}
      ]
    }}'''

    # Achado real (13/set/2026, auditoria de SEO — mesma sessão que revisou
    # o irmão de veículos): esta página (e a home, mais abaixo) não tinha
    # FAQPage, diferente da página individual e do hub por banco, que já
    # tinham. São exatamente as páginas de MAIS valor de SEO (termos de
    # cabeça, mais link equity) — cobertas agora, mesmo padrão (schema +
    # bloco visível <details>, nunca um sem o outro).
    faq_q1 = f"Qual banco tem a menor taxa de financiamento imobiliário em {ano_atual}?"
    faq_a1 = f"No comparativo acima, com cenário de referência de {formatar_reais(VALOR_REF)} em {PRAZO_REF} meses, {ranking_ref[0]['banco_exib']} aparece com o menor CET entre os {len(ranking_ref)} bancos que acompanhamos. O CET real do seu financiamento pode variar conforme o valor, prazo e entrada que você escolher."
    faq_q2 = "O que é CET e por que ele é melhor que só olhar a taxa de juros?"
    faq_a2 = "CET (Custo Efetivo Total) já soma juros, seguros obrigatórios (MIP e DFI) e taxa de administração — diferente da taxa de juros anunciada sozinha, ele mostra o custo real do financiamento por ano, e é o número certo pra comparar bancos entre si."
    faq_q3 = "Como vejo a simulação completa de um banco específico?"
    faq_a3 = "Clique no banco desejado na lista acima pra ver a página completa dele, com taxa, entrada mínima, prazo máximo e o simulador pra calcular sua parcela exata."

    texto_var = texto_variacao(resumo_hist)
    faq_q4 = "Como as taxas de financiamento imobiliário variaram nos últimos meses?"
    faq4_html = ""
    if texto_var:
        faq4_html = f'''
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h3 class="text-emerald-400 font-bold text-sm">{faq_q4}</h3>
                        <span class="faq-toggle-icon shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{texto_var}</p>
                </details>'''

    schema_faq = f'''{{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {{ "@type": "Question", "name": "{faq_q1}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_a1}" }} }},
        {{ "@type": "Question", "name": "{faq_q2}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_a2}" }} }},
        {{ "@type": "Question", "name": "{faq_q3}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_a3}" }} }}
      ]
    }}'''

    if texto_var:
        _obj_faq = json.loads(schema_faq)
        _obj_faq["mainEntity"].append({"@type": "Question", "name": faq_q4, "acceptedAnswer": {"@type": "Answer", "text": texto_var}})
        schema_faq = json.dumps(_obj_faq, ensure_ascii=False)

    html_comparador = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
{render_head_boilerplate(titulo_pagina, meta_description, url_canonica, dominio, [schema_breadcrumb, schema_faq])}
</head>
<body class="antialiased flex flex-col min-h-screen">
    <nav class="border-b border-white/5 sticky top-0 z-50 backdrop-blur-2xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="/" class="flex items-center">
                    <img src="logo-full.png" alt="Datalab Global" width="122" height="48" class="h-12 md:h-16 w-auto drop-shadow-[0_0_15px_rgba(16,185,129,0.2)] hover:scale-105 transition-transform duration-300">
                </a>
                <div class="flex items-center gap-1">
                    <a href="/aprenda" aria-label="Aprenda" class="inline-flex items-center gap-1.5 -my-2.5 p-2.5 text-xs text-slate-400 hover:text-emerald-400 transition-colors">{icone('book-open')} <span class="hidden sm:inline">Aprenda</span></a>
                    <div class="hidden md:flex items-center">
                        <a href="{LINK_FINANCIA_TUDO}" target="_blank" rel="noopener sponsored" class="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-6 py-2.5 rounded-full font-bold transition-all text-sm flex items-center shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                            Fazer Análise Grátis {icone('arrow-right', 'ml-2 text-sm')}
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <header class="py-12 md:py-16 relative z-10 text-center">
        <h1 class="text-3xl md:text-5xl font-serif text-white mb-4 leading-tight px-4">
            Taxas de financiamento imobiliário por banco em {mes_ano}
        </h1>
        <p class="text-slate-400 text-base md:text-lg font-light tracking-wide max-w-3xl mx-auto px-4">
            CET simulado para {formatar_reais(VALOR_REF)} em {PRAZO_REF} meses, na mesma condição para os {len(ranking_ref)} bancos e fintechs que acompanhamos — ordenado do menor pro maior custo efetivo total.
        </p>
        <p class="text-slate-600 text-[10px] uppercase tracking-widest mt-4">Taxas atualizadas em {date.fromisoformat(data_ultima_atualizacao).strftime('%d/%m/%Y')} · {texto_fonte_taxa()}</p>
    </header>

    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex-grow w-full relative z-10">
        <div class="flex items-center gap-2 mb-4 text-[11px] text-slate-400 uppercase tracking-widest px-4">
            <span class="w-8"></span><span class="flex-1">Banco</span><span class="hidden md:block flex-1 text-center">Taxa</span><span class="hidden md:block flex-1 text-center">Entrada</span><span class="flex-1 text-right">CET (referência)</span>
        </div>
        <div class="space-y-2">
            {linhas_tabela}
        </div>
        <p class="text-slate-400 text-xs font-light leading-relaxed mt-6 max-w-2xl">
            O CET (Custo Efetivo Total) já soma juros, seguros obrigatórios (MIP e DFI) e taxa de administração — é o número certo pra comparar bancos entre si, diferente da taxa de juros anunciada sozinha. Os valores acima são uma referência para {formatar_reais(VALOR_REF)} em {PRAZO_REF} meses; o CET real do seu financiamento depende do valor, prazo e entrada que você escolher — clique num banco acima pra ver as condições completas e simular o seu cenário.
        </p>

        <p class="text-slate-300 text-sm font-light leading-relaxed mt-6 max-w-2xl">
            Quer ver o comparativo para o seu valor e prazo? Consulte a <a href="financiamento-imobiliario" class="text-emerald-400 underline">tabela de financiamento imobiliário por valor e prazo</a>, de R$ 150 mil a R$ 1 milhão, em 10 a 35 anos.
        </p>

        {html_evolucao_taxas(resumo_hist)}

        <section class="mt-12">
            <h2 class="text-2xl font-serif text-white mb-3">Como calculamos e de onde vêm os dados</h2>
            <p class="text-slate-300 text-sm font-light leading-relaxed">
                As taxas vêm do relatório de taxas de juros por instituição financeira do Banco Central (modalidade "aquisição de imóveis, pessoa física, pré-fixada"): são médias do que cada banco efetivamente contratou, não ofertas. O CET é calculado por nós a partir dessa taxa, com seguros (MIP e DFI) e taxa de administração estimados, para o mesmo valor, prazo e a entrada mínima de cada banco. BRB e Poupex não constam no relatório do Banco Central nesta modalidade; para eles usamos uma estimativa de referências públicas de mercado.
                A série histórica está disponível em <a href="dados-abertos" class="text-emerald-400 underline">dados abertos</a> (CSV e JSON).
            </p>
        </section>

        <div class="mt-16 bg-gradient-to-r from-emerald-600 to-emerald-900 rounded-3xl p-8 md:p-12 relative overflow-hidden shadow-[0_20px_50px_rgba(16,185,129,0.3)] border border-emerald-400/50">
            <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-[80px]"></div>
            <div class="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10">
                <div class="md:w-2/3 text-left">
                    <div class="flex items-center gap-3 mb-4">
                        <span class="bg-yellow-400 text-yellow-950 text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest">Parceria Oficial</span>
                        <span class="flex items-center text-emerald-200 text-xs font-medium">{icone('shield-check', 'mr-1')} 100% Seguro</span>
                    </div>
                    <h3 class="text-3xl font-serif text-white mb-3">Não sabe qual banco escolher?</h3>
                    <p class="text-emerald-100 text-sm md:text-base font-light leading-relaxed">
                        A Financia Tudo compara as condições por você e negocia direto com a mesa de crédito — sem custo, sem compromisso.
                    </p>
                </div>
                <div class="md:w-1/3 w-full flex justify-center md:justify-end">
                    <a href="{LINK_FINANCIA_TUDO}" target="_blank" rel="noopener sponsored" class="group relative inline-flex items-center justify-center bg-white text-emerald-900 hover:bg-slate-100 font-black px-8 py-5 rounded-2xl transition-all shadow-2xl text-sm tracking-widest uppercase w-full text-center overflow-hidden">
                        <span class="relative z-10 flex items-center">Fazer Análise Grátis {icone('external-link', 'ml-3 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform')}</span>
                    </a>
                </div>
            </div>
        </div>

        <div class="mt-16 mb-8">
            <h2 class="text-2xl font-serif text-white mb-6 text-center">Perguntas Frequentes</h2>
            <div class="space-y-3 max-w-3xl mx-auto">
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h3 class="text-emerald-400 font-bold text-sm">{faq_q1}</h3>
                        <span class="faq-toggle-icon shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_a1}</p>
                </details>
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h3 class="text-emerald-400 font-bold text-sm">{faq_q2}</h3>
                        <span class="faq-toggle-icon shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_a2}</p>
                </details>
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h3 class="text-emerald-400 font-bold text-sm">{faq_q3}</h3>
                        <span class="faq-toggle-icon shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_a3}</p>
                </details>{faq4_html}
            </div>
        </div>
    </main>

    <footer class="border-t border-white/5 py-8 mt-10">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p class="text-slate-600 text-xs mb-4">Datalab Global © Todos os direitos reservados. Marca de {EMPRESA_RODAPE}. <a href="https://www.datalabglobal.com/privacidade/" class="underline hover:text-emerald-500">Privacidade</a> · <a href="https://www.datalabglobal.com/termos/" class="underline hover:text-emerald-500">Termos</a></p>
            <div class="flex items-center justify-center gap-4">
                <a href="https://www.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Outros produtos Datalab</a>
                <a href="https://www.datalabglobal.com/pix-no-cartao/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Pix no cartão</a>
                <a href="https://dados.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Lente B2B: dados de empresas</a>
                <a href="/aprenda" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Aprenda</a>
                <a href="/sobre" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Sobre</a>
                <a href="{LINK_WHATSAPP_SUPORTE}" target="_blank" rel="noopener" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">
                    {icone('whatsapp', 'mr-1')} Falar com o suporte
                </a>
            </div>
        </div>
    </footer>
</body>
</html>'''

    with open(os.path.join(pasta_saida, 'comparador-bancos.html'), "w", encoding="utf-8") as f:
        f.write(corrigir_concordancia(html_comparador))

    return url_canonica


# ---------------------------------------------------------------------------
# Páginas de comparação SEM marca de banco: "financiamento imobiliário de
# 300 mil em 30 anos" — todos os bancos lado a lado, mesma condição.
#
# Por que existem (auditoria de SEO, 29/out/2026): 76% das buscas que o
# Google mostrou citavam nome de banco ("simulador sicredi") e o CTR era
# zero — quem busca isso quer o simulador do próprio banco. A busca sem
# marca ("financiar 300 mil em 30 anos", "parcela de financiamento de 200
# mil em 20 anos") é onde um site neutro tem o que oferecer: o comparativo.
# Cada página traz números próprios (parcela, CET e total pago por banco para
# aquele valor e prazo), não troca de variável em texto.
# ---------------------------------------------------------------------------

_CACHE_LINHAS_COMPARACAO = {}


def _reais_inteiros(valor):
    return f"R$ {valor:,.0f}".replace(",", ".")


def _pct(valor):
    return f"{valor:.2f}".replace(".", ",")


def linhas_comparacao(valor_imovel, prazo_meses, taxas_atuais=None):
    """Uma linha por banco que oferece o prazo, ordenada por CET (SAC).
    Usa a ENTRADA MÍNIMA de cada banco (LTV próprio) e a taxa atual gravada
    pelo ETL — mesma regra de comparar_todos_bancos. Cacheada porque o índice
    e as páginas vizinhas reaproveitam os mesmos cenários."""
    chave = (float(valor_imovel), prazo_meses, tuple(sorted((taxas_atuais or {}).items())))
    if chave in _CACHE_LINHAS_COMPARACAO:
        return _CACHE_LINHAS_COMPARACAO[chave]
    linhas = []
    for banco in bancos_com_prazo(prazo_meses):
        regra = BANCOS[banco]
        taxa = (taxas_atuais or {}).get(banco, regra["taxa_padrao"])
        entrada = valor_imovel * (1 - regra["ltv"])
        financiado = valor_imovel - entrada
        r = calcular_sac_price(financiado, prazo_meses, taxa, valor_imovel)
        linhas.append({
            "banco": banco, "banco_exib": nome_exibicao(banco), "taxa": taxa,
            "entrada": entrada, "entrada_perc": round((1 - regra["ltv"]) * 100),
            "financiado": financiado, "p1_sac": r["p1_sac"], "p_price": r["p1_price"],
            "total_sac": r["total_sac"], "cet": r["cet_sac"], "renda": r["renda_sugerida"],
        })
    linhas.sort(key=lambda x: x["cet"])
    _CACHE_LINHAS_COMPARACAO[chave] = linhas
    return linhas


def _escolher_que_cabe(limite, *opcoes):
    for o in opcoes:
        if len(o) <= limite:
            return o
    return opcoes[-1][:limite].rsplit(" ", 1)[0]


def _nav_comparacao():
    return f'''<nav class="border-b border-white/5 sticky top-0 z-50 backdrop-blur-2xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="/" class="flex items-center">
                    <img src="logo-full.png" alt="Datalab Global" width="122" height="48" class="h-12 md:h-16 w-auto drop-shadow-[0_0_15px_rgba(16,185,129,0.2)] hover:scale-105 transition-transform duration-300">
                </a>
                <div class="flex items-center gap-1">
                    <a href="/aprenda" aria-label="Aprenda" class="inline-flex items-center gap-1.5 -my-2.5 p-2.5 text-xs text-slate-400 hover:text-emerald-400 transition-colors">{icone('book-open')} <span class="hidden sm:inline">Aprenda</span></a>
                    <div class="hidden md:flex items-center">
                        <a href="{LINK_FINANCIA_TUDO}" target="_blank" rel="noopener sponsored" class="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-6 py-2.5 rounded-full font-bold transition-all text-sm flex items-center">
                            Fazer Análise Grátis {icone('arrow-right', 'ml-2 text-sm')}
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </nav>'''


def _cta_comparacao(titulo):
    return f'''<div class="mt-16 bg-gradient-to-r from-emerald-600 to-emerald-900 rounded-3xl p-8 md:p-12 relative overflow-hidden border border-emerald-400/50">
            <div class="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10">
                <div class="md:w-2/3 text-left">
                    <div class="flex items-center gap-3 mb-4">
                        <span class="bg-yellow-400 text-yellow-950 text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest">Parceria Oficial</span>
                        <span class="flex items-center text-emerald-200 text-xs font-medium">{icone('shield-check', 'mr-1')} 100% Seguro</span>
                    </div>
                    <h3 class="text-3xl font-serif text-white mb-3">{titulo}</h3>
                    <p class="text-emerald-100 text-sm md:text-base font-light leading-relaxed">
                        A Financia Tudo compara as condições por você e negocia direto com a mesa de crédito — sem custo, sem compromisso. Podemos receber uma comissão do parceiro, sem custo extra pra você.
                    </p>
                </div>
                <div class="md:w-1/3 w-full flex justify-center md:justify-end">
                    <a href="{LINK_FINANCIA_TUDO}" target="_blank" rel="noopener sponsored" class="group inline-flex items-center justify-center bg-white text-emerald-900 hover:bg-slate-100 font-black px-8 py-5 rounded-2xl transition-all">
                        <span class="flex items-center">Fazer Análise Grátis {icone('external-link', 'ml-3')}</span>
                    </a>
                </div>
            </div>
        </div>'''


def _footer_comparacao():
    return f'''<footer class="border-t border-white/5 py-8 mt-10">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p class="text-slate-600 text-xs mb-4">Datalab Global © Todos os direitos reservados. Marca de {EMPRESA_RODAPE}. <a href="https://www.datalabglobal.com/privacidade/" class="underline hover:text-emerald-500">Privacidade</a> · <a href="https://www.datalabglobal.com/termos/" class="underline hover:text-emerald-500">Termos</a></p>
            <div class="flex flex-wrap items-center justify-center gap-4">
                <a href="https://www.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Outros produtos Datalab</a>
                <a href="https://www.datalabglobal.com/pix-no-cartao/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Pix no cartão</a>
                <a href="https://dados.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Lente B2B: dados de empresas</a>
                <a href="/aprenda" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Aprenda</a>
                <a href="/sobre" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Sobre</a>
            </div>
        </div>
    </footer>'''


def _faq_html(perguntas):
    blocos = ""
    for q, a in perguntas:
        blocos += f'''
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h3 class="text-emerald-400 font-bold text-sm">{q}</h3>
                        <span class="faq-toggle-icon shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{a}</p>
                </details>'''
    return blocos


def gerar_paginas_comparacao(pasta_saida, dominio, data_ultima_atualizacao, taxas_atuais, lookup_paginas):
    """Gera as páginas valor x prazo sem marca + o índice
    (financiamento-imobiliario.html). Retorna as URLs (pro sitemap)."""
    urls = []
    data_br = date.fromisoformat(data_ultima_atualizacao).strftime('%d/%m/%Y')
    url_indice = f"{dominio}/financiamento-imobiliario"

    for valor in VALORES_COMPARACAO:
        for anos in ANOS_COMPARACAO:
            if not pagina_comparacao_existe(valor, anos):
                continue
            prazo = anos * 12
            linhas = linhas_comparacao(valor, prazo, taxas_atuais)
            n = len(linhas)
            vc = formatar_valor_curto(valor)
            vf = formatar_reais(valor)
            slug = slug_comparacao(valor, anos)
            url_canonica = f"{dominio}/{slug}"

            menor_cet, maior_cet = linhas[0], linhas[-1]
            por_parcela = sorted(linhas, key=lambda x: x["p1_sac"])
            menor_p, maior_p = por_parcela[0], por_parcela[-1]
            price_min = min(x["p_price"] for x in linhas)
            price_max = max(x["p_price"] for x in linhas)
            nota_prazo = ""
            if n < len(BANCOS):
                nota_prazo = (f" Só {n} dos {len(BANCOS)} bancos que acompanhamos financiam em {anos} anos;"
                              f" os demais têm prazo máximo menor e ficam de fora desta comparação.")

            titulo_pagina = f"Financiamento imobiliário de {vc} em {anos} anos | Datalab Global"
            meta_description = _escolher_que_cabe(
                160,
                f"Financiar {vc} em {anos} anos: 1ª parcela de {_reais_inteiros(menor_p['p1_sac'])} a {_reais_inteiros(maior_p['p1_sac'])} e CET de {_pct(menor_cet['cet'])}% a {_pct(maior_cet['cet'])}% a.a. em {n} bancos.",
                f"Financiar {vc} em {anos} anos: 1ª parcela de {_reais_inteiros(menor_p['p1_sac'])} a {_reais_inteiros(maior_p['p1_sac'])} em {n} bancos.",
            )

            linhas_html = ""
            for i, x in enumerate(linhas, start=1):
                regra = BANCOS[x["banco"]]
                url_logo = f"https://www.google.com/s2/favicons?domain={regra['dominio_favicon']}&sz=128"
                slug_b = lookup_paginas.get((x["banco"], float(valor), prazo)) or slug_hub_banco(x["banco"])
                destaque = "bg-emerald-500/10 border-emerald-500/30" if i == 1 else "bg-white/5 border-white/10"
                medalha = '<span class="text-yellow-400 font-bold text-xs">#1</span>' if i == 1 else f'<span class="text-emerald-400 font-bold text-xs">#{i}</span>'
                linhas_html += f'''
        <a href="{slug_b}" class="grid grid-cols-[auto_1fr_auto_auto] md:grid-cols-[auto_1.4fr_1fr_1fr_1fr_1fr_1fr] items-center gap-3 md:gap-5 p-4 rounded-xl border {destaque} hover:border-emerald-500/50 transition-all">
            <span class="w-6 text-center">{medalha}</span>
            <span class="flex items-center gap-2 min-w-0">
                {favicon_com_fallback(url_logo, x['banco_exib'], "w-6 h-6")}
                <span class="text-sm font-medium text-white truncate">{x['banco_exib']}</span>
            </span>
            <span class="hidden md:block text-center text-xs text-slate-400">{_pct(x['taxa'])}% a.a.</span>
            <span class="hidden md:block text-center text-xs text-slate-400">{_reais_inteiros(x['entrada'])} <span class="text-slate-500">({x['entrada_perc']}%)</span></span>
            <span class="text-right md:text-center text-xs text-slate-300">{_reais_inteiros(x['p1_sac'])}</span>
            <span class="hidden md:block text-center text-xs text-slate-400">{_reais_inteiros(x['p_price'])}</span>
            <span class="text-right text-sm font-bold text-emerald-400">{_pct(x['cet'])}%</span>
        </a>'''

            # outros prazos para o mesmo valor
            outros_prazos = ""
            for a2 in ANOS_COMPARACAO:
                if a2 == anos or not pagina_comparacao_existe(valor, a2):
                    continue
                l2 = linhas_comparacao(valor, a2 * 12, taxas_atuais)
                outros_prazos += (f'<li><a href="{slug_comparacao(valor, a2)}" class="flex items-center justify-between gap-3 p-3 rounded-lg border border-white/10 hover:border-emerald-500/50 text-sm text-slate-300">'
                                  f'<span>{vc} em {a2} anos</span><span class="text-xs text-slate-400">1ª parcela a partir de {_reais_inteiros(min(x["p1_sac"] for x in l2))}</span></a></li>')
            # valores próximos no mesmo prazo
            vizinhos = ""
            for dv in (-100_000, -50_000, 50_000, 100_000):
                v2 = valor + dv
                if pagina_comparacao_existe(v2, anos):
                    l2 = linhas_comparacao(v2, prazo, taxas_atuais)
                    vizinhos += (f'<li><a href="{slug_comparacao(v2, anos)}" class="flex items-center justify-between gap-3 p-3 rounded-lg border border-white/10 hover:border-emerald-500/50 text-sm text-slate-300">'
                                 f'<span>{formatar_valor_curto(v2)} em {anos} anos</span><span class="text-xs text-slate-400">1ª parcela a partir de {_reais_inteiros(min(x["p1_sac"] for x in l2))}</span></a></li>')

            faq = [
                (f"Qual a parcela de um financiamento imobiliário de {vc} em {anos} anos?",
                 f"No sistema SAC, a primeira parcela de {vf} em {prazo} meses vai de {formatar_reais(menor_p['p1_sac'])} ({menor_p['banco_exib']}) a {formatar_reais(maior_p['p1_sac'])} ({maior_p['banco_exib']}), e diminui a cada mês. No sistema Price, a parcela é fixa e fica entre {formatar_reais(price_min)} e {formatar_reais(price_max)}. A diferença entre os bancos vem da taxa e da entrada mínima de cada um (quanto menor a entrada, maior o valor financiado)."),
                (f"Qual banco tem o menor CET para financiar {vc} em {anos} anos?",
                 f"Na nossa simulação, {menor_cet['banco_exib']} tem o menor CET ({_pct(menor_cet['cet'])}% a.a.) e {maior_cet['banco_exib']} o maior ({_pct(maior_cet['cet'])}% a.a.). O CET soma juros, seguros (MIP e DFI) e taxa de administração; é a melhor medida para comparar bancos. O valor final da sua proposta depende da análise de crédito."),
                (f"Que renda preciso para financiar {vc} em {anos} anos?",
                 f"Os bancos costumam limitar a parcela a 30% da renda bruta. Para a primeira parcela de {formatar_reais(menor_cet['p1_sac'])} ({menor_cet['banco_exib']}, o menor CET), isso dá uma renda familiar de pelo menos {formatar_reais(menor_cet['renda'])}.{nota_prazo}"),
            ]
            schema_faq = json.dumps({
                "@context": "https://schema.org", "@type": "FAQPage",
                "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq],
            }, ensure_ascii=False)
            schema_breadcrumb = json.dumps({
                "@context": "https://schema.org", "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Datalab Global", "item": f"{dominio}/"},
                    {"@type": "ListItem", "position": 2, "name": "Financiamento imobiliário por valor e prazo", "item": url_indice},
                    {"@type": "ListItem", "position": 3, "name": f"{vc} em {anos} anos", "item": url_canonica},
                ],
            }, ensure_ascii=False)
            schema_artigo = json.dumps({
                "@context": "https://schema.org", "@type": "WebPage", "url": url_canonica,
                "name": f"Financiamento imobiliário de {vc} em {anos} anos",
                "dateModified": data_ultima_atualizacao,
                "isPartOf": {"@type": "WebSite", "url": f"{dominio}/", "name": "Datalab Global"},
                "about": {"@type": "FinancialProduct", "name": "Financiamento imobiliário"},
            }, ensure_ascii=False)

            html_pagina = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
{render_head_boilerplate(titulo_pagina, meta_description, url_canonica, dominio, [schema_breadcrumb, schema_faq, schema_artigo])}
</head>
<body class="antialiased flex flex-col min-h-screen">
    {_nav_comparacao()}

    <header class="py-12 md:py-16 relative z-10 text-center">
        <p class="text-emerald-400 text-xs uppercase tracking-widest mb-3 px-4"><a href="financiamento-imobiliario" class="hover:underline">Financiamento imobiliário por valor e prazo</a></p>
        <h1 class="text-3xl md:text-5xl font-serif text-white mb-4 leading-tight px-4">
            Financiamento imobiliário de {vc} em {anos} anos
        </h1>
        <p class="text-slate-400 text-base md:text-lg font-light tracking-wide max-w-3xl mx-auto px-4">
            Parcela e CET para financiar {vf} em {prazo} meses, com a entrada mínima de cada um dos {n} bancos, ordenado do menor pro maior custo efetivo total.
        </p>
        <p class="text-slate-600 text-[10px] uppercase tracking-widest mt-4">Taxas atualizadas em {data_br} · {texto_fonte_taxa()}</p>
    </header>

    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex-grow w-full relative z-10">
        <div class="flex items-center gap-2 mb-4 text-[11px] text-slate-400 uppercase tracking-widest px-4">
            <span class="w-6"></span><span class="flex-1">Banco</span><span class="hidden md:block flex-1 text-center">Taxa</span><span class="hidden md:block flex-1 text-center">Entrada mín.</span><span class="flex-1 text-right md:text-center">1ª parcela (SAC)</span><span class="hidden md:block flex-1 text-center">Parcela (Price)</span><span class="flex-1 text-right">CET</span>
        </div>
        <div class="space-y-2">
            {linhas_html}
        </div>
        <p class="text-slate-400 text-xs font-light leading-relaxed mt-6 max-w-2xl">
            Cada linha leva à simulação completa do banco, onde você ajusta valor, entrada e prazo. A 1ª parcela do SAC considera juros e amortização; o CET inclui também seguros (MIP e DFI) e taxa de administração estimados. Valores de referência: a proposta final depende da análise de crédito de cada banco.{nota_prazo}
        </p>

        <section class="mt-12">
            <h2 class="text-2xl font-serif text-white mb-3">Resumo para {vc} em {anos} anos</h2>
            <p class="text-slate-300 text-sm font-light leading-relaxed">
                Financiando {vf} em {prazo} meses, a primeira parcela (SAC) vai de <strong class="text-white">{formatar_reais(menor_p['p1_sac'])}</strong> em {menor_p['banco_exib']} a <strong class="text-white">{formatar_reais(maior_p['p1_sac'])}</strong> em {maior_p['banco_exib']}.
                O menor CET é de {menor_cet['banco_exib']} ({_pct(menor_cet['cet'])}% a.a.) e o maior, de {maior_cet['banco_exib']} ({_pct(maior_cet['cet'])}% a.a.).
                No menor CET, o total pago no SAC é {formatar_reais(menor_cet['total_sac'])} para {formatar_reais(menor_cet['financiado'])} financiados, com entrada de {formatar_reais(menor_cet['entrada'])}.
            </p>
        </section>

        <section class="mt-10 grid md:grid-cols-2 gap-8">
            <div>
                <h2 class="text-lg font-serif text-white mb-3">Mesmo valor, outros prazos</h2>
                <ul class="space-y-2">{outros_prazos}</ul>
            </div>
            <div>
                <h2 class="text-lg font-serif text-white mb-3">Mesmo prazo, valores próximos</h2>
                <ul class="space-y-2">{vizinhos}</ul>
            </div>
        </section>

        {_cta_comparacao("Não sabe qual banco escolher?")}

        <div class="mt-16 mb-8">
            <h2 class="text-2xl font-serif text-white mb-6 text-center">Perguntas Frequentes</h2>
            <div class="space-y-3 max-w-3xl mx-auto">{_faq_html(faq)}
            </div>
        </div>
        <p class="text-center text-xs text-slate-400"><a href="comparador-bancos" class="text-emerald-400 underline">Ver o comparativo geral de taxas entre os {len(BANCOS)} bancos →</a></p>
    </main>

    {_footer_comparacao()}
</body>
</html>'''
            with open(os.path.join(pasta_saida, f"{slug}.html"), "w", encoding="utf-8") as f:
                f.write(corrigir_concordancia(html_pagina))
            urls.append(url_canonica)

    urls.append(gerar_indice_comparacao(pasta_saida, dominio, data_ultima_atualizacao, taxas_atuais))
    return urls


def gerar_indice_comparacao(pasta_saida, dominio, data_ultima_atualizacao, taxas_atuais):
    """Índice (financiamento-imobiliario.html): tabela valor x prazo com a 1ª
    parcela do banco de menor CET em cada cenário, cada célula levando à
    página de comparação. É útil por si só (uma tabela de parcelas que o
    usuário consulta) e dá a todas as páginas valor x prazo um pai comum."""
    data_br = date.fromisoformat(data_ultima_atualizacao).strftime('%d/%m/%Y')
    url_canonica = f"{dominio}/financiamento-imobiliario"
    titulo_pagina = "Financiamento imobiliário: parcela por valor e prazo | Datalab Global"
    meta_description = (
        f"Tabela de financiamento imobiliário de {formatar_valor_curto(VALORES_COMPARACAO[0])} a "
        f"{formatar_valor_curto(VALORES_COMPARACAO[-1])} em 10 a 35 anos: parcela inicial e CET comparados em até {len(BANCOS)} bancos."
    )
    anos_validos = [a for a in ANOS_COMPARACAO if len(bancos_com_prazo(a * 12)) >= MIN_BANCOS_COMPARACAO]
    cab = "".join(f'<th scope="col" class="px-3 py-2 text-right font-medium">{a} anos</th>' for a in anos_validos)
    corpo = ""
    for valor in VALORES_COMPARACAO:
        celulas = ""
        for a in anos_validos:
            l = linhas_comparacao(valor, a * 12, taxas_atuais)
            celulas += (f'<td class="px-3 py-2 text-right"><a href="{slug_comparacao(valor, a)}" class="text-emerald-400 hover:underline">'
                        f'{_reais_inteiros(min(x["p1_sac"] for x in l))}</a></td>')
        corpo += f'<tr class="border-t border-white/5"><th scope="row" class="px-3 py-2 text-left font-medium text-white">{formatar_valor_curto(valor)}</th>{celulas}</tr>'

    faq = [
        ("Como ler esta tabela?",
         "Cada célula mostra a primeira parcela (sistema SAC) do banco com o menor CET para aquele valor de imóvel e prazo, já considerando a entrada mínima exigida por cada banco. Clique para ver todos os bancos lado a lado."),
        ("Por que a coluna de 35 anos tem menos bancos?",
         "Nem todo banco financia em 35 anos. Na coluna de 35 anos entram só os bancos com prazo máximo de 420 meses; nos demais prazos entram todos os que acompanhamos."),
    ]
    schema_faq = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq],
    }, ensure_ascii=False)
    schema_breadcrumb = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Datalab Global", "item": f"{dominio}/"},
            {"@type": "ListItem", "position": 2, "name": "Financiamento imobiliário por valor e prazo", "item": url_canonica},
        ],
    }, ensure_ascii=False)

    html_indice = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
{render_head_boilerplate(titulo_pagina, meta_description, url_canonica, dominio, [schema_breadcrumb, schema_faq])}
</head>
<body class="antialiased flex flex-col min-h-screen">
    {_nav_comparacao()}

    <header class="py-12 md:py-16 relative z-10 text-center">
        <h1 class="text-3xl md:text-5xl font-serif text-white mb-4 leading-tight px-4">
            Financiamento imobiliário: parcela por valor e prazo
        </h1>
        <p class="text-slate-400 text-base md:text-lg font-light tracking-wide max-w-3xl mx-auto px-4">
            Primeira parcela do banco com o menor CET para cada valor de imóvel e prazo. Escolha um cenário para comparar todos os bancos.
        </p>
        <p class="text-slate-600 text-[10px] uppercase tracking-widest mt-4">Taxas atualizadas em {data_br} · {texto_fonte_taxa()}</p>
    </header>

    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex-grow w-full relative z-10">
        <div class="overflow-x-auto rounded-xl border border-white/10">
            <table class="w-full text-sm text-slate-300">
                <thead class="text-[11px] uppercase tracking-widest text-slate-400"><tr><th scope="col" class="px-3 py-2 text-left font-medium">Imóvel</th>{cab}</tr></thead>
                <tbody>{corpo}</tbody>
            </table>
        </div>
        <p class="text-slate-400 text-xs font-light leading-relaxed mt-6 max-w-2xl">
            Valores de referência no sistema SAC, com a entrada mínima de cada banco. A proposta final depende da análise de crédito. Para o comparativo geral de taxas, veja o <a href="comparador-bancos" class="text-emerald-400 underline">comparativo entre bancos</a>; para simular com os seus números, escolha um banco na <a href="/" class="text-emerald-400 underline">página inicial</a>.
        </p>

        {_cta_comparacao("Quer ajuda para escolher?")}

        <div class="mt-16 mb-8">
            <h2 class="text-2xl font-serif text-white mb-6 text-center">Perguntas Frequentes</h2>
            <div class="space-y-3 max-w-3xl mx-auto">{_faq_html(faq)}
            </div>
        </div>
    </main>

    {_footer_comparacao()}
</body>
</html>'''
    with open(os.path.join(pasta_saida, "financiamento-imobiliario.html"), "w", encoding="utf-8") as f:
        f.write(corrigir_concordancia(html_indice))
    return url_canonica



# ---------------------------------------------------------------------------
# Simulador incorporável (/embed), página "como incorporar" (/incorporar) e
# página de imprensa (/imprensa).
#
# Por que existem (auditoria de SEO, 29/out/2026): o site é novo e quase não tem
# links. Calculadora incorporável e fatos citáveis são dos poucos jeitos de ganhar
# links sem contato com ninguém: blogs e imobiliárias usam a calculadora e dão
# crédito; jornalistas encontram os números prontos e a forma de citar.
# ---------------------------------------------------------------------------

_JS_CALCULO_EMBED = """// <calc>
function calcularFinanciamento(valorFinanciado, meses, taxaAnualPct) {
  var i = (taxaAnualPct / 100) / 12;
  var amort = valorFinanciado / meses;
  var p1 = amort + valorFinanciado * i;
  var pU = amort * (1 + i);
  var price = i > 0 ? valorFinanciado * (i * Math.pow(1 + i, meses)) / (Math.pow(1 + i, meses) - 1) : amort;
  return {p1: p1, pU: pU, price: price,
          jurosSac: valorFinanciado * i * (meses + 1) / 2, jurosPrice: price * meses - valorFinanciado};
}
// </calc>"""

_TEMPLATE_EMBED = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Simulador de financiamento imobiliário | Datalab Global</title>
<meta name="description" content="Simulador de financiamento imobiliário incorporável: parcela SAC e Price com a taxa média de cada banco.">
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="__DOMINIO__/incorporar">
<link rel="icon" href="/favicon.ico?v=20261012" sizes="any">
<link rel="icon" href="/favicon-32.png?v=20261012" type="image/png" sizes="32x32">
<style>
*{box-sizing:border-box}body{margin:0;padding:14px;font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#0b1220;color:#e2e8f0}
h1{font-size:16px;margin:0 0 10px;font-weight:700}label{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#94a3b8;margin:10px 0 4px}
select,input{width:100%;padding:9px 10px;border-radius:8px;border:1px solid #334155;background:#111b2e;color:#f8fafc;font-size:14px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}.res{margin-top:14px;padding:12px;border-radius:10px;background:#0f2a24;border:1px solid #14b8a6}
.res b{display:block;font-size:20px;color:#5eead4}.res small{color:#94a3b8}.k{display:flex;justify-content:space-between;gap:8px;padding:4px 0;border-top:1px solid #1e3a34}.k:first-of-type{border-top:0}
.nota{margin-top:10px;font-size:11px;color:#94a3b8}.nota a{color:#5eead4}
</style>
</head>
<body>
<h1>Simule seu financiamento imobiliário</h1>
<label for="banco">Banco</label><select id="banco"></select>
<div class="row"><div><label for="valor">Valor do imóvel (R$)</label><input id="valor" type="number" min="50000" step="10000" value="500000" inputmode="numeric"></div>
<div><label for="prazo">Prazo</label><select id="prazo"></select></div></div>
<label for="entrada">Entrada (R$) <span id="minimo" style="text-transform:none;letter-spacing:0"></span></label><input id="entrada" type="number" min="0" step="5000" inputmode="numeric">
<div class="res" aria-live="polite">
<small>1ª parcela (SAC)</small><b id="p1">–</b>
<div class="k"><span>Última parcela (SAC)</span><span id="pU">–</span></div>
<div class="k"><span>Parcela fixa (Price)</span><span id="price">–</span></div>
<div class="k"><span>Juros totais (SAC)</span><span id="juros">–</span></div>
<div class="k"><span>Valor financiado</span><span id="fin">–</span></div></div>
<p class="nota" id="nota"></p>
<p class="nota">Simulação educativa, sem seguros e tarifas; não é oferta de crédito. Simulador por <a href="__DOMINIO__/" target="_blank" rel="noopener">Datalab Global</a>.</p>
<script>
__JS_CALCULO__
var BANCOS = __BANCOS_JSON__;
var fmt = new Intl.NumberFormat('pt-BR', {style: 'currency', currency: 'BRL', maximumFractionDigits: 0});
var el = function (id) { return document.getElementById(id); };
BANCOS.forEach(function (b, i) { var o = document.createElement('option'); o.value = i; o.textContent = b.nome + ' (' + b.taxa.toFixed(2).replace('.', ',') + '% a.a.)'; el('banco').appendChild(o); });
function atualizarPrazos() {
  var b = BANCOS[el('banco').value], atual = el('prazo').value; el('prazo').innerHTML = '';
  [10, 15, 20, 25, 30, 35].forEach(function (a) { if (a * 12 <= b.prazoMax) { var o = document.createElement('option'); o.value = a * 12; o.textContent = a + ' anos'; el('prazo').appendChild(o); } });
  el('prazo').value = (atual && Array.prototype.some.call(el('prazo').options, function (o) { return o.value === atual; })) ? atual : String(Math.min(360, b.prazoMax));
}
function calcular(ajustarEntrada) {
  var b = BANCOS[el('banco').value], valor = Math.max(0, parseFloat(el('valor').value) || 0);
  var min = valor * (1 - b.ltv);
  el('minimo').textContent = '(mín. ' + fmt.format(min) + ')';
  if (ajustarEntrada || !el('entrada').value) el('entrada').value = Math.round(Math.max(valor * 0.2, min));
  var entrada = Math.min(valor, Math.max(min, parseFloat(el('entrada').value) || 0)), fin = valor - entrada, meses = parseInt(el('prazo').value, 10);
  if (fin <= 0 || !meses) { ['p1','pU','price','juros','fin'].forEach(function (id) { el(id).textContent = '–'; }); return; }
  var r = calcularFinanciamento(fin, meses, b.taxa);
  el('p1').textContent = fmt.format(r.p1); el('pU').textContent = fmt.format(r.pU); el('price').textContent = fmt.format(r.price);
  el('juros').textContent = fmt.format(r.jurosSac); el('fin').textContent = fmt.format(fin);
  el('nota').textContent = 'Taxa média: ' + b.nome + ', ' + b.taxa.toFixed(2).replace('.', ',') + '% a.a. (Banco Central, __DATA_BR__).';
}
el('banco').addEventListener('change', function () { atualizarPrazos(); calcular(true); });
el('prazo').addEventListener('change', function () { calcular(false); });
el('valor').addEventListener('input', function () { calcular(true); });
el('entrada').addEventListener('input', function () { calcular(false); });
atualizarPrazos(); calcular(true);
</script>
</body>
</html>"""


def gerar_embed(pasta_saida, dominio, data_ultima_atualizacao, taxas_atuais):
    """/embed: simulador mínimo, sem dependências, pra ser usado em <iframe>."""
    data_br = date.fromisoformat(data_ultima_atualizacao).strftime('%d/%m/%Y')
    html_embed = (_TEMPLATE_EMBED
                  .replace("__JS_CALCULO__", _JS_CALCULO_EMBED)
                  .replace("__BANCOS_JSON__", construir_bancos_json(taxas_atuais or {}))
                  .replace("__DOMINIO__", dominio)
                  .replace("__DATA_BR__", data_br))
    with open(os.path.join(pasta_saida, "embed.html"), "w", encoding="utf-8") as f:
        f.write(html_embed)


def gerar_pagina_incorporar(pasta_saida, dominio, data_ultima_atualizacao):
    url = f"{dominio}/incorporar"
    codigo = (f'<iframe src="{dominio}/embed" title="Simulador de financiamento imobiliário" '
              f'width="100%" height="560" style="border:0;max-width:520px" loading="lazy"></iframe>\n'
              f'<p style="font-size:12px">Simulador por <a href="{dominio}/">Datalab Global</a></p>')
    codigo_html = codigo.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    perguntas = [
        ("O simulador para incorporar é gratuito?",
         "Sim. Basta copiar o código acima e colar no HTML da sua página. Pedimos apenas que mantenha o link de crédito para a Datalab Global."),
        ("Preciso me cadastrar ou usar alguma biblioteca?",
         "Não. É um iframe: sem cadastro, sem chave de API, sem JavaScript no seu site e sem cookies."),
        ("As taxas dos bancos ficam atualizadas?",
         "Sim. O simulador usa a taxa média mensal de cada banco, segundo o Banco Central, e é atualizado por nós todo mês, sem você precisar mexer no seu site."),
        ("O que o simulador calcula?",
         "A primeira e a última parcela no sistema SAC, a parcela fixa na tabela Price, os juros totais e o valor financiado, respeitando a entrada mínima e o prazo máximo de cada banco. Não inclui seguros nem tarifas."),
    ]
    schema_faq = json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in perguntas]}, ensure_ascii=False)
    schema_bc = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Datalab Global", "item": f"{dominio}/"},
        {"@type": "ListItem", "position": 2, "name": "Simulador para incorporar", "item": url}]}, ensure_ascii=False)
    titulo = "Simulador de financiamento imobiliário para site (grátis) | Datalab Global"
    meta = "Incorpore grátis um simulador de financiamento imobiliário no seu site, com taxas atualizadas dos bancos. Copie o código e cole: sem cadastro."
    html_pagina = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
{render_head_boilerplate(titulo, meta, url, dominio, [schema_bc, schema_faq])}
</head>
<body class="antialiased flex flex-col min-h-screen">
    {_nav_comparacao()}
    <header class="py-12 md:py-16 relative z-10 text-center">
        <h1 class="text-3xl md:text-5xl font-serif text-white mb-4 leading-tight px-4">Simulador de financiamento imobiliário para o seu site</h1>
        <p class="text-slate-400 text-base md:text-lg font-light tracking-wide max-w-3xl mx-auto px-4">Copie o código, cole na sua página e pronto: um simulador de parcela com a taxa média atualizada de cada banco, grátis e sem cadastro.</p>
    </header>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex-grow w-full relative z-10">
        <section class="grid md:grid-cols-2 gap-8 items-start">
            <div>
                <h2 class="text-2xl font-serif text-white mb-3">Veja como fica</h2>
                <iframe src="embed" title="Simulador de financiamento imobiliário" width="100%" height="560" style="border:0;max-width:520px;border-radius:12px" loading="lazy"></iframe>
            </div>
            <div>
                <h2 class="text-2xl font-serif text-white mb-3">Copie o código</h2>
                <textarea readonly rows="7" onclick="this.select()" class="w-full bg-slate-900/60 border border-white/10 rounded-xl p-3 text-xs text-slate-300 font-mono" aria-label="Código para incorporar o simulador">{codigo_html}</textarea>
                <ol class="mt-4 space-y-2 text-sm text-slate-300 list-decimal list-inside">
                    <li>Clique no código e copie (Ctrl+C).</li>
                    <li>Cole no HTML da página onde o simulador deve aparecer.</li>
                    <li>Mantenha o link "Simulador por Datalab Global" logo abaixo.</li>
                </ol>
                <p class="mt-4 text-xs text-slate-400">Taxas médias do Banco Central, atualizadas todo mês. Simulação educativa: não é oferta de crédito. Os <a href="dados-abertos" class="text-emerald-400 underline">dados abertos</a> por trás do simulador estão disponíveis em CSV e JSON.</p>
            </div>
        </section>
        <section class="mt-16">
            <h2 class="text-2xl font-serif text-white mb-6 text-center">Perguntas Frequentes</h2>
            <div class="space-y-3 max-w-3xl mx-auto">{_faq_html(perguntas)}
            </div>
        </section>
        <p class="mt-10 text-center text-xs text-slate-400"><a href="financiamento-imobiliario" class="text-emerald-400 underline">Tabela de financiamento por valor e prazo</a> · <a href="comparador-bancos" class="text-emerald-400 underline">Comparativo de taxas entre bancos</a></p>
    </main>
    {_footer_comparacao()}
</body>
</html>'''
    with open(os.path.join(pasta_saida, "incorporar.html"), "w", encoding="utf-8") as f:
        f.write(corrigir_concordancia(html_pagina))
    return [url]


def gerar_pagina_imprensa(pasta_saida, dominio, data_ultima_atualizacao, taxas_atuais):
    """/imprensa: fatos citáveis calculados dos dados reais (mudam sozinhos a
    cada atualização), metodologia, logos, como citar e contato."""
    url = f"{dominio}/imprensa"
    data_br = date.fromisoformat(data_ultima_atualizacao).strftime('%d/%m/%Y')
    historico = carregar_historico()
    fatos = []
    if historico:
        meses = sorted({r["inicio_periodo"] for r in historico})
        ult = meses[-1]
        do_mes = sorted((r for r in historico if r["inicio_periodo"] == ult), key=lambda r: r["taxa_aa"])
        if do_mes:
            lo, hi = do_mes[0], do_mes[-1]
            fatos.append(f"Em {MESES_PT[int(ult[5:7]) - 1]} de {ult[:4]}, a taxa média contratada no financiamento imobiliário foi de {_pct2(lo['taxa_aa'])}% ao ano em {nome_exibicao(lo['banco'])}, a menor entre os {len(do_mes)} bancos com dado do Banco Central, e de {_pct2(hi['taxa_aa'])}% ao ano em {nome_exibicao(hi['banco'])}, a maior.")
        resumo = resumo_historico(historico)
        if resumo:
            q, a = resumo["maior_queda"], resumo["maior_alta"]
            m0, m1 = resumo["meses"][0], resumo["meses"][-1]
            fatos.append(f"Entre {_rotulo_mes(m0)} e {_rotulo_mes(m1)}, a maior queda foi a de {q['banco_exib']} ({_sinal_pp(q['variacao'])} ponto percentual) e a maior alta, a de {a['banco_exib']} ({_sinal_pp(a['variacao'])} ponto percentual).")
        fatos.append(f"A série histórica cobre {len(meses)} meses ({_rotulo_mes(meses[0])} a {_rotulo_mes(meses[-1])}) e está disponível em dados abertos, sob licença {LICENCA_DADOS}.")
    l500 = linhas_comparacao(500_000, 360, taxas_atuais)
    p_lo, p_hi = min(l500, key=lambda x: x["p1_sac"]), max(l500, key=lambda x: x["p1_sac"])
    fatos.append(f"Para financiar um imóvel de R$ 500 mil em 30 anos, com a entrada mínima de cada banco, a primeira parcela (sistema SAC) vai de {formatar_reais(p_lo['p1_sac'])} ({p_lo['banco_exib']}) a {formatar_reais(p_hi['p1_sac'])} ({p_hi['banco_exib']}), e o CET estimado, de {_pct(min(x['cet'] for x in l500))}% a {_pct(max(x['cet'] for x in l500))}% ao ano.")
    fatos_html = "".join(f'<li class="mb-3">{f}</li>' for f in fatos)
    citacao = f"Datalab Global. {{titulo}}. {url}, acesso em AAAA-MM-DD."
    schema_bc = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Datalab Global", "item": f"{dominio}/"},
        {"@type": "ListItem", "position": 2, "name": "Imprensa", "item": url}]}, ensure_ascii=False)
    schema_page = json.dumps({"@context": "https://schema.org", "@type": "WebPage", "url": url, "name": "Imprensa e dados para citação",
        "dateModified": data_ultima_atualizacao, "about": {"@type": "Organization", "name": "Datalab Global", "url": "https://www.datalabglobal.com/"}}, ensure_ascii=False)
    titulo = "Imprensa: dados de financiamento imobiliário para citar | Datalab Global"
    meta = "Números atualizados de taxas e parcelas de financiamento imobiliário, metodologia, logos e como citar a Datalab Global. Dados abertos (CC BY 4.0)."
    html_pagina = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
{render_head_boilerplate(titulo, meta, url, dominio, [schema_bc, schema_page])}
</head>
<body class="antialiased flex flex-col min-h-screen">
    {_nav_comparacao()}
    <header class="py-12 md:py-16 relative z-10 text-center">
        <h1 class="text-3xl md:text-5xl font-serif text-white mb-4 leading-tight px-4">Imprensa e dados para citação</h1>
        <p class="text-slate-400 text-base md:text-lg font-light tracking-wide max-w-3xl mx-auto px-4">Números prontos, metodologia aberta e a forma de citar. Atualizado em {data_br}.</p>
    </header>
    <main class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex-grow w-full relative z-10">
        <section>
            <h2 class="text-2xl font-serif text-white mb-3">Números para citar</h2>
            <ul class="text-slate-300 text-sm font-light leading-relaxed list-disc list-inside">{fatos_html}</ul>
            <p class="text-slate-400 text-xs mt-2">Calculados automaticamente a partir dos dados do Banco Central; mudam a cada atualização. As taxas são médias do que foi efetivamente contratado, não ofertas.</p>
        </section>
        <section class="mt-10">
            <h2 class="text-2xl font-serif text-white mb-3">Metodologia</h2>
            <p class="text-slate-300 text-sm font-light leading-relaxed">As taxas vêm do relatório de taxas de juros por instituição financeira do Banco Central (modalidade 903201). O CET é calculado por nós (TIR do fluxo completo, com seguros MIP e DFI e taxa de administração estimados) para o mesmo valor, prazo e a entrada mínima de cada banco. BRB e Poupex não constam no relatório do Banco Central nesta modalidade; para eles usamos uma estimativa, sinalizada nas páginas. Detalhes e série completa em <a href="dados-abertos" class="text-emerald-400 underline">dados abertos</a>.</p>
        </section>
        <section class="mt-10">
            <h2 class="text-2xl font-serif text-white mb-3">Sobre a Datalab Global</h2>
            <p class="text-slate-300 text-sm font-light leading-relaxed">A Datalab Global é uma marca de {EMPRESA_RODAPE}. Cria ferramentas gratuitas de dados e de simulação de crédito. As simulações são educativas e não constituem oferta de crédito. Conheça a <a href="sobre" class="text-emerald-400 underline">página Sobre</a>.</p>
        </section>
        <section class="mt-10">
            <h2 class="text-2xl font-serif text-white mb-3">Logos e imagens</h2>
            <ul class="text-sm space-y-2"><li><a href="logo-full.png" download class="text-emerald-400 underline">Logo completo (PNG)</a></li><li><a href="logo-schema.png" download class="text-emerald-400 underline">Ícone (PNG, 512 px)</a></li><li><a href="og-image.png" download class="text-emerald-400 underline">Imagem de compartilhamento (PNG)</a></li></ul>
        </section>
        <section class="mt-10">
            <h2 class="text-2xl font-serif text-white mb-3">Como citar</h2>
            <p class="text-slate-300 text-sm font-light leading-relaxed bg-white/5 border border-white/10 rounded-xl p-4">{citacao.format(titulo="Taxas de financiamento imobiliário por banco (dados do Banco Central)")}</p>
            <p class="text-slate-400 text-xs mt-3">Dados sob licença <a href="{LICENCA_DADOS_URL}" rel="noopener" class="underline">{LICENCA_DADOS}</a>: pode usar e adaptar, citando a fonte com link.</p>
        </section>
        <section class="mt-10">
            <h2 class="text-2xl font-serif text-white mb-3">Contato</h2>
            <p class="text-slate-300 text-sm font-light">E-mail: <a href="mailto:contato@datalabglobal.com" class="text-emerald-400 underline">contato@datalabglobal.com</a></p>
        </section>
        <p class="mt-10 text-center text-xs text-slate-400"><a href="comparador-bancos" class="text-emerald-400 underline">Comparativo de taxas</a> · <a href="financiamento-imobiliario" class="text-emerald-400 underline">Parcela por valor e prazo</a> · <a href="incorporar" class="text-emerald-400 underline">Simulador para o seu site</a></p>
    </main>
    {_footer_comparacao()}
</body>
</html>'''
    with open(os.path.join(pasta_saida, "imprensa.html"), "w", encoding="utf-8") as f:
        f.write(corrigir_concordancia(html_pagina))
    return [url]



def gerar_index_home(pasta_saida, links_por_banco, data_ultima_atualizacao):
    # Achado real (27/set/2026, revisão de SEO/desempenho): cada um dos ~1.680 links da home levava um <svg> de seta
    # próprio — a home tinha 1,1 MB de HTML. A seta vira um caractere (›) e as ~10 classes repetidas em cada link viram
    # uma classe só (.lk), definida uma vez: mesmo visual, uma fração do peso.
    blocos_html = """<style>
        .lk{display:flex;align-items:center;justify-content:space-between;padding:.75rem;border-radius:.5rem;border:1px solid transparent;transition:background-color .15s,border-color .15s}
        .lk:hover{background:rgba(255,255,255,.05);border-color:rgba(255,255,255,.1)}
        .lk span:first-child{font-size:.75rem;line-height:1rem;font-weight:300;color:#cbd5e1}
        .lk:hover span:first-child{color:#fff}
        .lk span:last-child{color:#10b981;font-size:.875rem;line-height:1}
        </style>"""
    for banco, links in links_por_banco.items():
        regra = obter_regra(banco)
        banco_exib = nome_exibicao(banco)
        url_logo = f"https://www.google.com/s2/favicons?domain={regra['dominio_favicon']}&sz=128"
        ancora_id = banco.lower().replace(" ", "-")
        links_html = "".join(
            f'<li><a href="{item["slug"]}" class="lk"><span>{item["texto"]}</span><span aria-hidden="true">›</span></a></li>'
            for item in links
        )

        blocos_html += f'''
        <div id="{ancora_id}" class="bg-slate-900/40 backdrop-blur-md rounded-2xl shadow-2xl border border-white/5 overflow-hidden transition-all duration-300 hover:border-emerald-500/30 hover:shadow-[0_0_30px_rgba(16,185,129,0.1)] scroll-mt-24">
            <a href="{slug_hub_banco(banco)}" class="group/h2 border-b border-white/5 px-6 py-5 flex items-center gap-4 bg-black/40 hover:bg-black/60 transition-colors">
                {favicon_com_fallback(url_logo, banco_exib)}
                <h2 class="text-xl font-serif text-white tracking-wide group-hover/h2:text-emerald-400 transition-colors">{banco_exib}</h2>
                <span class="ml-auto text-[10px] text-slate-400 group-hover/h2:text-emerald-400 uppercase tracking-widest transition-colors">Ver taxas →</span>
            </a>
            <div class="p-4">
                <ul class="space-y-1 h-64 overflow-y-auto pr-2 custom-scrollbar">
                    {links_html}
                </ul>
            </div>
        </div>
        '''

    url_home = f"{DOMINIO}/"
    descricao_home = f"Simule seu financiamento imobiliário em meses ou anos, compare parcela e CET entre {len(BANCOS)} bancos e veja quanto economiza antecipando parcelas."

    schema_website = f'''{{
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "Datalab Global",
      "url": "{url_home}",
      "publisher": {{"@type": "Organization", "@id": "https://www.datalabglobal.com/#organization", "name": "Datalab Global", "url": "https://www.datalabglobal.com/"}},
      "dateModified": "{data_ultima_atualizacao}"
    }}'''

    # Schema "Logo" (achado real, 06/set/2026: sem isso, junto do favicon
    # que não existia, o Google mostrava o domínio cru + ícone genérico
    # em vez do nome/ícone da marca — ver print do usuário comparando com
    # o resultado de outro site). Formato exato recomendado pela
    # documentação do Google (developers.google.com/search/docs/appearance/
    # structured-data/logo): Organization com "logo" apontando pra uma
    # imagem RASTER real (não SVG) de pelo menos 112x112px — por isso
    # aponta pro logo-schema.png (512x512) gerado por
    # rasterizar_favicon_png, não pro favicon.svg.
    # Achado real (12/set/2026, pedido do usuário depois de pesquisa sobre
    # E-E-A-T/YMYL — conteúdo financeiro é avaliado pelo Google com padrão
    # mais alto de confiança do que conteúdo comum): "founder" e
    # "contactPoint" são sinais legíveis por máquina de que existe gente
    # real, com contato real, por trás do site — não só um domínio
    # anônimo gerando página automática. Rodolfo Delfino é o fundador
    # real da Datalab Global (confirmado pelo próprio usuário); e-mail é
    # o contato real usado pelo domínio (Google Workspace configurado em
    # datalabglobal.com). Ver também gerar_pagina_sobre(), que reforça o
    # mesmo Person como schema próprio na página /sobre.
    schema_organization = f'''{{
      "@context": "https://schema.org",
      "@type": "Organization",
      "@id": "https://www.datalabglobal.com/#organization",
      "name": "Datalab Global",
      "url": "https://www.datalabglobal.com/",
      "logo": "{DOMINIO}/logo-schema.png",
      "founder": {{"@type": "Person", "name": "Rodolfo Delfino"}},
      "contactPoint": {{"@type": "ContactPoint", "email": "contato@datalabglobal.com", "contactType": "customer service"}}
    }}'''

    titulo_home = "Simulador de Financiamento Imobiliário: Parcela e CET 2026 | Datalab Global"
    # og:title/twitter:title deliberadamente mais curto que o <title> —
    # comportamento original de antes do render_head_boilerplate existir,
    # preservado explicitamente aqui (achado da auditoria: a extração
    # tinha igualado os dois sem querer, mudando o texto que aparece ao
    # compartilhar a home no Facebook/LinkedIn/Twitter).
    titulo_home_social = "Simulador de Financiamento e Amortização | Datalab Global"

    # Achado real (13/set/2026, auditoria de SEO): a home era a única
    # página de alto valor sem FAQPage (individual, hub e agora
    # comparador-bancos já tinham) — corrigida aqui com perguntas
    # genéricas sobre o produto como um todo, não sobre um banco
    # específico (essas já são respondidas nas páginas de banco).
    faq_home_q1 = "Como funciona o simulador de financiamento imobiliário da Datalab?"
    faq_home_a1 = "Você escolhe o banco, vê a taxa real dele e simula a parcela pro valor, prazo e entrada que quiser — incluindo quanto você economiza fazendo amortizações extras. Os dados de taxa vêm direto do Banco Central e são atualizados periodicamente."
    faq_home_q2 = "As taxas mostradas são reais ou só uma estimativa de marketing?"
    faq_home_a2 = "São a taxa padrão estimada de cada banco pra essa modalidade, com base em dados públicos — não é uma taxa promocional de vitrine. Sua taxa final aprovada depende do seu relacionamento com o banco e da análise de crédito."
    faq_home_q3 = "O simulador cobra alguma coisa pra usar?"
    faq_home_a3 = "Não, simular é 100% gratuito. A Datalab é remunerada pelo correspondente bancário quando você pede uma análise por aqui — isso não muda o valor da sua parcela nem qual banco você escolhe."

    schema_faq_home = f'''{{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {{ "@type": "Question", "name": "{faq_home_q1}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_home_a1}" }} }},
        {{ "@type": "Question", "name": "{faq_home_q2}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_home_a2}" }} }},
        {{ "@type": "Question", "name": "{faq_home_q3}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_home_a3}" }} }}
      ]
    }}'''

    html_home = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
{render_head_boilerplate(titulo_home, descricao_home, url_home, DOMINIO, [schema_website, schema_organization, schema_faq_home], titulo_social=titulo_home_social)}
</head>
<body class="antialiased min-h-screen flex flex-col">
    <nav class="border-b border-white/5 sticky top-0 z-50 backdrop-blur-2xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="/" class="flex items-center">
                    <img src="logo-full.png" alt="Datalab Global" width="122" height="48" class="h-12 md:h-16 w-auto drop-shadow-[0_0_15px_rgba(16,185,129,0.2)] hover:scale-105 transition-transform duration-300">
                </a>
                <a href="/aprenda" aria-label="Aprenda" class="inline-flex items-center gap-1.5 -my-2.5 p-2.5 text-xs text-slate-400 hover:text-emerald-400 transition-colors">{icone('book-open')} <span class="hidden sm:inline">Aprenda</span></a>
            </div>
        </div>
    </nav>
    <div class="py-24 md:py-32 text-center px-4 relative overflow-hidden flex-grow">
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-emerald-500/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>
        <h1 class="text-4xl md:text-6xl font-serif text-white mb-6 leading-tight max-w-4xl mx-auto">
            Simulador de Financiamento Imobiliário
        </h1>
        <p class="text-slate-400 text-lg md:text-xl font-light tracking-wide max-w-2xl mx-auto">
            Selecione a instituição financeira abaixo e descubra quanto você economiza ao fazer amortizações — em qualquer prazo, de meses a anos.
        </p>
        <a href="comparador-bancos" class="inline-flex items-center gap-2 mt-6 text-emerald-400 hover:text-emerald-300 text-sm font-medium underline underline-offset-4">
            Ou veja o comparativo de taxas entre os {len(BANCOS)} bancos {icone('arrow-right', 'text-xs')}
        </a>
        <a href="financiamento-imobiliario" class="inline-flex items-center gap-2 mt-3 ml-0 sm:ml-6 text-emerald-400 hover:text-emerald-300 text-sm font-medium underline underline-offset-4">
            Ou consulte a parcela por valor e prazo {icone('arrow-right', 'text-xs')}
        </a>
    </div>
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-32 relative z-10 w-full">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {blocos_html}
        </div>

        <div class="mt-16 mb-8">
            <h2 class="text-2xl font-serif text-white mb-6 text-center">Perguntas Frequentes</h2>
            <div class="space-y-3 max-w-3xl mx-auto">
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h3 class="text-emerald-400 font-bold text-sm">{faq_home_q1}</h3>
                        <span class="faq-toggle-icon shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_home_a1}</p>
                </details>
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h3 class="text-emerald-400 font-bold text-sm">{faq_home_q2}</h3>
                        <span class="faq-toggle-icon shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_home_a2}</p>
                </details>
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h3 class="text-emerald-400 font-bold text-sm">{faq_home_q3}</h3>
                        <span class="faq-toggle-icon shrink-0 text-slate-400 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_home_a3}</p>
                </details>
            </div>
        </div>
    </main>
    <footer class="border-t border-white/5 py-8">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p class="text-slate-600 text-xs mb-4">Datalab Global © Todos os direitos reservados. Marca de {EMPRESA_RODAPE}. <a href="https://www.datalabglobal.com/privacidade/" class="underline hover:text-emerald-500">Privacidade</a> · <a href="https://www.datalabglobal.com/termos/" class="underline hover:text-emerald-500">Termos</a></p>
            <div class="flex items-center justify-center gap-4">
                <a href="https://www.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Outros produtos Datalab</a>
                <a href="https://www.datalabglobal.com/pix-no-cartao/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Pix no cartão</a>
                <a href="https://dados.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Lente B2B: dados de empresas</a>
                <a href="/aprenda" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Aprenda</a>
                <a href="/sobre" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Sobre</a>
                <a href="{LINK_WHATSAPP_SUPORTE}" target="_blank" rel="noopener" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">
                    {icone('whatsapp', 'mr-1')} Falar com o suporte
                </a>
            </div>
        </div>
    </footer>
</body>
</html>'''
    with open(os.path.join(pasta_saida, 'index.html'), "w", encoding="utf-8") as f:
        f.write(corrigir_concordancia(html_home))


def gerar_pagina_sobre(pasta_saida, dominio):
    """Página institucional "Sobre" — achado real (12/set/2026, pesquisa
    de práticas atuais do Google pedida pelo usuário): conteúdo
    financeiro (YMYL — "Your Money or Your Life") é avaliado com padrão
    de confiança mais alto que conteúdo comum, e "Author entities, Person
    Schema, e presença no Knowledge Graph são sinais de confiança cada
    vez mais importantes" pra esse tipo de conteúdo. Até esta página, o
    site não tinha NENHUM lugar que dissesse quem está por trás dele —
    só o texto genérico de rodapé "Datalab Global". Conteúdo (fundador,
    missão, contato) é o texto real fornecido pelo usuário, não
    inventado — nunca fabricar razão social/CNPJ/endereço que não foram
    confirmados."""
    url_canonica = f"{dominio}/sobre"
    titulo_pagina = "Sobre a Datalab Global | Simulador de Financiamento Imobiliário"
    meta_description = (
        "Conheça a Datalab Global, criada por Rodolfo Delfino para resolver problemas reais com dados e IA, "
        "incluindo este simulador de financiamento imobiliário."
    )

    schema_sobre = f'''{{
      "@context": "https://schema.org",
      "@type": "AboutPage",
      "url": "{url_canonica}",
      "mainEntity": {{
        "@type": "Organization",
        "@id": "https://www.datalabglobal.com/#organization",
        "name": "Datalab Global",
        "url": "https://www.datalabglobal.com/",
        "founder": {{"@type": "Person", "name": "Rodolfo Delfino"}},
        "contactPoint": {{"@type": "ContactPoint", "email": "contato@datalabglobal.com", "contactType": "customer service"}}
      }}
    }}'''

    corpo = f'''<main class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24 relative z-10 w-full">
        <h1 class="text-3xl md:text-5xl font-serif text-white mb-8 leading-tight">Sobre a Datalab Global</h1>

        <div class="glass-panel rounded-2xl p-6 md:p-10 space-y-6 text-slate-300 leading-relaxed">
            <p>A Datalab Global foi criada por <strong class="text-white">Rodolfo Delfino</strong> com um objetivo direto: usar dados e as melhores técnicas de inteligência artificial disponíveis hoje para facilitar a vida das pessoas. Isso já tomou forma de produtos bem diferentes entre si — de SaaS a jogos, de relatórios a sistemas de ERP — mas todos guiados pela mesma pergunta: <strong class="text-emerald-400">qual dor podemos resolver hoje?</strong></p>

            <p>Este simulador de financiamento imobiliário nasceu dessa mesma lógica. Em vez de taxa promocional de material de marketing, usamos a taxa média <strong class="text-white">real</strong> apurada pelo Banco Central do Brasil — atualizada periodicamente, a mesma fonte que qualquer analista de crédito consultaria. O objetivo é simples: você saber, antes de entrar num banco, quanto um financiamento realmente custa.</p>

            <div class="border-t border-white/10 pt-6">
                <h2 class="font-serif text-xl text-white mb-3">Como funciona a Datalab Global</h2>
                <p>Este site é mantido por indicação: quando você pede uma análise gratuita através dos nossos parceiros credenciados, podemos receber uma comissão — sem nenhum custo extra pra você. Não somos um banco nem instituição financeira, e nenhuma simulação aqui é uma oferta de crédito; é uma estimativa educativa baseada em dados reais de mercado.</p>
            </div>

            <div class="border-t border-white/10 pt-6">
                <h2 class="font-serif text-xl text-white mb-3">Contato</h2>
                <p>
                    E-mail: <a href="mailto:contato@datalabglobal.com" class="text-emerald-400 hover:text-emerald-300 underline">contato@datalabglobal.com</a><br>
                    WhatsApp: <a href="{LINK_WHATSAPP_SUPORTE}" target="_blank" rel="noopener" class="text-emerald-400 hover:text-emerald-300 underline">falar com o suporte</a>
                </p>
            </div>
        </div>

        <div class="flex flex-wrap gap-3 mt-8">
            <a href="/" class="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-6 py-3 rounded-full font-bold text-sm transition-all">Ir pro simulador</a>
            <a href="comparador-bancos" class="border border-white/10 hover:border-emerald-500/50 px-6 py-3 rounded-full font-bold text-sm transition-all">Ver comparativo de bancos</a>
        </div>
    </main>'''

    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
{render_head_boilerplate(titulo_pagina, meta_description, url_canonica, dominio, [schema_sobre])}
</head>
<body class="antialiased min-h-screen flex flex-col">
    <nav class="border-b border-white/5 sticky top-0 z-50 backdrop-blur-2xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="/" class="flex items-center">
                    <img src="logo-full.png" alt="Datalab Global" width="122" height="48" class="h-12 md:h-16 w-auto drop-shadow-[0_0_15px_rgba(16,185,129,0.2)] hover:scale-105 transition-transform duration-300">
                </a>
                <a href="/aprenda" aria-label="Aprenda" class="inline-flex items-center gap-1.5 -my-2.5 p-2.5 text-xs text-slate-400 hover:text-emerald-400 transition-colors">{icone('book-open')} <span class="hidden sm:inline">Aprenda</span></a>
            </div>
        </div>
    </nav>
    {corpo}
    <footer class="border-t border-white/5 py-8 mt-10">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p class="text-slate-600 text-xs mb-4">Datalab Global © Todos os direitos reservados. Marca de {EMPRESA_RODAPE}. <a href="https://www.datalabglobal.com/privacidade/" class="underline hover:text-emerald-500">Privacidade</a> · <a href="https://www.datalabglobal.com/termos/" class="underline hover:text-emerald-500">Termos</a></p>
            <div class="flex items-center justify-center gap-4">
                <a href="https://www.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Outros produtos Datalab</a>
                <a href="https://www.datalabglobal.com/pix-no-cartao/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Pix no cartão</a>
                <a href="https://dados.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Lente B2B: dados de empresas</a>
                <a href="/aprenda" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Aprenda</a>
                <a href="/sobre" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Sobre</a>
                <a href="{LINK_WHATSAPP_SUPORTE}" target="_blank" rel="noopener" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">
                    {icone('whatsapp', 'mr-1')} Falar com o suporte
                </a>
            </div>
        </div>
    </footer>
</body>
</html>'''
    with open(os.path.join(pasta_saida, 'sobre.html'), "w", encoding="utf-8") as f:
        f.write(html)
    return url_canonica


def gerar_pagina_aprenda(art, pasta_saida, dominio, data_atualizacao):
    """Página de conteúdo evergreen (educativo, sem calculadora) — segunda
    camada de profundidade de conteúdo, mesmo padrão implementado em
    paralelo no projeto irmão de veículos (13/set/2026, pedido explícito
    do usuário depois da auditoria de SEO): o site só tinha página de
    CÁLCULO, nenhuma prova de conhecimento real por trás da calculadora
    — isso pesa no Helpful Content (avaliado no domínio inteiro) e na
    experiência de quem busca "o que é CET" sem estar pronto pra simular
    ainda. `art` é um dict de ARTIGOS_APRENDA (slug, títulos, corpo,
    CTA) — Article schema (headline = o próprio tema, não inventado) +
    link de volta pro simulador/comparador relevante no fim."""
    url_canonica = f"{dominio}/{art['slug']}"
    schema_article = f'''{{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{art['titulo_h1']}",
      "url": "{url_canonica}",
      "author": {{"@type": "Organization", "name": "Datalab Global"}},
      "publisher": {{
        "@type": "Organization", "name": "Datalab Global",
        "logo": {{"@type": "ImageObject", "url": "{dominio}/logo-schema.png"}}
      }},
      "dateModified": "{data_atualizacao}",
      "mainEntityOfPage": "{url_canonica}"
    }}'''

    corpo = f'''<main class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24 relative z-10 w-full">
        <h1 class="text-3xl md:text-5xl font-serif text-white mb-8 leading-tight">{art['titulo_h1']}</h1>
        <div class="glass-panel rounded-2xl p-6 md:p-10 space-y-6 text-slate-300 leading-relaxed">
            {art['corpo_html']}
        </div>
        <div class="flex flex-wrap gap-3 mt-8">
            <a href="{art['cta_href']}" class="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-6 py-3 rounded-full font-bold text-sm transition-all">{art['cta_texto']}</a>
            <a href="aprenda" class="border border-white/10 hover:border-emerald-500/50 px-6 py-3 rounded-full font-bold text-sm transition-all">Ver todos os artigos</a>
        </div>
    </main>'''

    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
{render_head_boilerplate(art['titulo_pagina'], art['meta_description'], url_canonica, dominio, [schema_article])}
</head>
<body class="antialiased min-h-screen flex flex-col">
    <nav class="border-b border-white/5 sticky top-0 z-50 backdrop-blur-2xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="/" class="flex items-center">
                    <img src="logo-full.png" alt="Datalab Global" width="122" height="48" class="h-12 md:h-16 w-auto drop-shadow-[0_0_15px_rgba(16,185,129,0.2)] hover:scale-105 transition-transform duration-300">
                </a>
                <a href="/aprenda" aria-label="Aprenda" class="inline-flex items-center gap-1.5 -my-2.5 p-2.5 text-xs text-slate-400 hover:text-emerald-400 transition-colors">{icone('book-open')} <span class="hidden sm:inline">Aprenda</span></a>
            </div>
        </div>
    </nav>
    {corpo}
    <footer class="border-t border-white/5 py-8 mt-10">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p class="text-slate-600 text-xs mb-4">Datalab Global © Todos os direitos reservados. Marca de {EMPRESA_RODAPE}. <a href="https://www.datalabglobal.com/privacidade/" class="underline hover:text-emerald-500">Privacidade</a> · <a href="https://www.datalabglobal.com/termos/" class="underline hover:text-emerald-500">Termos</a></p>
            <div class="flex items-center justify-center gap-4">
                <a href="https://www.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Outros produtos Datalab</a>
                <a href="https://www.datalabglobal.com/pix-no-cartao/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Pix no cartão</a>
                <a href="https://dados.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Lente B2B: dados de empresas</a>
                <a href="/aprenda" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Aprenda</a>
                <a href="/sobre" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Sobre</a>
                <a href="{LINK_WHATSAPP_SUPORTE}" target="_blank" rel="noopener" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">
                    {icone('whatsapp', 'mr-1')} Falar com o suporte
                </a>
            </div>
        </div>
    </footer>
</body>
</html>'''
    with open(os.path.join(pasta_saida, f"{art['slug']}.html"), "w", encoding="utf-8") as f:
        f.write(html)
    return url_canonica


def gerar_hub_aprenda(artigos, pasta_saida, dominio):
    """Índice /aprenda listando os artigos evergreen — único caminho de
    navegação normal (clicando) até eles além do link no rodapé, mesmo
    cuidado já tomado com as páginas de simulação (conteúdo só alcançável
    via sitemap.xml é órfão de verdade pro visitante humano)."""
    url_canonica = f"{dominio}/aprenda"
    cards_html = "\n".join(
        f'''<a href="{a['slug']}" class="glass-panel rounded-2xl p-6 hover:border-emerald-500/40 transition-all group">
            <h2 class="font-serif text-lg font-bold mb-2 group-hover:text-emerald-400 transition-colors">{a['titulo_h1']}</h2>
            <p class="text-sm text-slate-400">{a['resumo_card']}</p>
        </a>'''
        for a in artigos
    )
    corpo = f'''<main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24 relative z-10 w-full">
        <h1 class="text-3xl md:text-5xl font-serif text-white mb-2 leading-tight">Aprenda sobre financiamento imobiliário</h1>
        <p class="text-slate-400 text-sm mb-10">Guias educativos, sem juridiquês, pra você entender o que está simulando antes de decidir.</p>
        <div class="grid sm:grid-cols-2 gap-4">{cards_html}</div>
    </main>'''
    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
{render_head_boilerplate("Aprenda: guias sobre financiamento imobiliário | Datalab Global", "Guias sobre financiamento imobiliário: SAC x Price, CET, IOF, amortização, FGTS, LTV e consórcio, explicados sem juridiquês e com dados do Banco Central.", url_canonica, dominio, [])}
</head>
<body class="antialiased min-h-screen flex flex-col">
    <nav class="border-b border-white/5 sticky top-0 z-50 backdrop-blur-2xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="/" class="flex items-center">
                    <img src="logo-full.png" alt="Datalab Global" width="122" height="48" class="h-12 md:h-16 w-auto drop-shadow-[0_0_15px_rgba(16,185,129,0.2)] hover:scale-105 transition-transform duration-300">
                </a>
                <a href="/aprenda" aria-label="Aprenda" class="inline-flex items-center gap-1.5 -my-2.5 p-2.5 text-xs text-slate-400 hover:text-emerald-400 transition-colors">{icone('book-open')} <span class="hidden sm:inline">Aprenda</span></a>
            </div>
        </div>
    </nav>
    {corpo}
    <footer class="border-t border-white/5 py-8 mt-10">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p class="text-slate-600 text-xs mb-4">Datalab Global © Todos os direitos reservados. Marca de {EMPRESA_RODAPE}. <a href="https://www.datalabglobal.com/privacidade/" class="underline hover:text-emerald-500">Privacidade</a> · <a href="https://www.datalabglobal.com/termos/" class="underline hover:text-emerald-500">Termos</a></p>
            <div class="flex items-center justify-center gap-4">
                <a href="https://www.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Outros produtos Datalab</a>
                <a href="https://www.datalabglobal.com/pix-no-cartao/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Pix no cartão</a>
                <a href="https://dados.datalabglobal.com/" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Lente B2B: dados de empresas</a>
                <a href="/aprenda" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Aprenda</a>
                <a href="/sobre" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">Sobre</a>
                <a href="{LINK_WHATSAPP_SUPORTE}" target="_blank" rel="noopener" class="inline-flex items-center justify-center text-slate-400 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">
                    {icone('whatsapp', 'mr-1')} Falar com o suporte
                </a>
            </div>
        </div>
    </footer>
</body>
</html>'''
    with open(os.path.join(pasta_saida, 'aprenda.html'), "w", encoding="utf-8") as f:
        f.write(html)
    return url_canonica


# Conteúdo evergreen (educativo) — 2ª camada de profundidade além das
# páginas de cálculo, ver docstring de gerar_pagina_aprenda(). Baseado em
# definição técnica real e estabelecida (BACEN, legislação do IOF/FGTS,
# mesma terminologia já usada no glossário de cada página do site) —
# nunca inventado. Aprovado pelo usuário (13/set/2026) como a lista de
# 6 temas antes de escrever.
ARTIGOS_APRENDA = [
    {
        "slug": "aprenda-sac-x-price",
        "titulo_h1": "SAC x Price no financiamento imobiliário: qual tabela escolher",
        "titulo_pagina": "SAC x Price no financiamento imobiliário | Datalab Global",
        "meta_description": "SAC (parcela decrescente) ou Price (parcela fixa)? Entenda a diferença no financiamento imobiliário e qual combina mais com o seu planejamento.",
        "resumo_card": "Parcela que começa alta e cai com o tempo, ou parcela fixa do início ao fim? As duas opções que todo financiamento imobiliário oferece.",
        "corpo_html": '''<p>No financiamento imobiliário brasileiro, você normalmente escolhe entre dois sistemas de amortização: <strong class="text-white">SAC</strong> (Sistema de Amortização Constante) e <strong class="text-white">Tabela Price</strong> (sistema francês). Os dois calculam juros sobre o saldo devedor, mas organizam as parcelas de um jeito bem diferente.</p>
        <div class="border-t border-white/10 pt-6">
            <h2 class="font-serif text-xl text-white mb-3">SAC: parcela decrescente</h2>
            <p>No SAC, o valor amortizado é <strong class="text-white">constante</strong> todo mês — mas como os juros incidem sobre um saldo devedor que vai encolhendo, a parcela total começa mais alta e vai diminuindo mês a mês até o fim do contrato. Quem escolhe SAC costuma pagar mais no começo, mas menos no total ao longo do financiamento.</p>
        </div>
        <div class="border-t border-white/10 pt-6">
            <h2 class="font-serif text-xl text-white mb-3">Price: parcela fixa</h2>
            <p>Na Tabela Price, a parcela é <strong class="text-white">igual</strong> do primeiro ao último mês — só a proporção entre juros e amortização dentro dela muda com o tempo (mais juros no início, mais amortização no fim). É mais previsível pro seu orçamento mensal, mas o total pago em juros ao longo do contrato costuma ser um pouco maior que no SAC.</p>
        </div>
        <div class="border-t border-white/10 pt-6">
            <h2 class="font-serif text-xl text-white mb-3">Qual escolher</h2>
            <p>Se sua renda é mais apertada agora e tende a crescer com o tempo, o SAC pode pesar demais logo no início. Se você prefere previsibilidade total no valor da parcela, a Price facilita o planejamento. Não existe "certo" — depende do seu momento financeiro e de quanto você valoriza pagar menos juros no total versus ter uma parcela sempre igual.</p>
        </div>''',
        "cta_href": "comparador-bancos",
        "cta_texto": "Comparar bancos e simular",
    },
    {
        "slug": "aprenda-cet-iof-financiamento-imobiliario",
        "titulo_h1": "CET e IOF no financiamento imobiliário: o que entra na conta",
        "titulo_pagina": "CET e IOF no financiamento imobiliário | Datalab Global",
        "meta_description": "O que é o CET no financiamento imobiliário: juros, seguros MIP e DFI, taxa de administração e IOF. É o número certo para comparar bancos.",
        "resumo_card": "O custo real por trás da taxa anunciada: juros, seguros obrigatórios e taxa de administração, tudo somado num só número.",
        "corpo_html": '''<p>CET — Custo Efetivo Total — é o custo real e completo do financiamento imobiliário, expresso em percentual ao ano. Diferente da taxa de juros anunciada isoladamente, o CET soma <strong class="text-white">tudo</strong> que você efetivamente paga: a taxa de juros em si, os seguros obrigatórios (MIP, que cobre morte e invalidez, e DFI, que cobre danos ao imóvel) e a taxa de administração cobrada pelo banco.</p>
        <div class="border-t border-white/10 pt-6">
            <h2 class="font-serif text-xl text-white mb-3">Onde entra o IOF</h2>
            <p>O IOF (Imposto sobre Operações Financeiras) também incide sobre o financiamento imobiliário, cobrado uma única vez na contratação — diferente do IOF de outras modalidades de crédito, no financiamento imobiliário residencial a alíquota tende a ser bem menor, já que a legislação trata essa modalidade de forma diferenciada. Ainda assim, ele entra na conta do CET, então você não precisa calcular nada à parte.</p>
        </div>
        <div class="border-t border-white/10 pt-6">
            <h2 class="font-serif text-xl text-white mb-3">Por que comparar pelo CET, não pela taxa</h2>
            <p>Dois bancos podem anunciar taxas de juros parecidas e cobrar seguros e tarifas bem diferentes — o CET é o único número que já soma tudo isso, e por isso é a referência certa pra comparar propostas de bancos diferentes de forma justa. O CET mostrado neste simulador usa a taxa real apurada pelo Banco Central; sua taxa final aprovada ainda depende do seu relacionamento com o banco e da sua análise de crédito.</p>
        </div>''',
        "cta_href": "comparador-bancos",
        "cta_texto": "Comparar CET entre bancos",
    },
    {
        "slug": "aprenda-amortizacao-extraordinaria",
        "titulo_h1": "Amortização extraordinária: como reduzir prazo ou parcela do financiamento imobiliário",
        "titulo_pagina": "Amortização extraordinária no financiamento imobiliário | Datalab Global",
        "meta_description": "Como um pagamento extra reduz o saldo devedor do financiamento imobiliário e quando vale mais a pena diminuir o prazo ou o valor da parcela.",
        "resumo_card": "Um pagamento fora do cronograma que ataca o saldo devedor direto — e pode cortar anos inteiros de financiamento.",
        "corpo_html": '''<p>Amortização extraordinária é um pagamento feito <strong class="text-white">fora</strong> do cronograma normal de parcelas, com o objetivo específico de abater o saldo devedor do financiamento imobiliário — não é uma parcela adiantada, é um valor que reduz diretamente quanto você ainda deve ao banco.</p>
        <div class="border-t border-white/10 pt-6">
            <h2 class="font-serif text-xl text-white mb-3">Por que isso economiza mais do que parece</h2>
            <p>Como os juros de um financiamento imobiliário incidem sobre o saldo devedor a cada mês, reduzir esse saldo mais cedo significa pagar juros sobre um valor menor em todos os meses seguintes — pelo resto de um contrato que pode durar 20, 30 anos. Num prazo tão longo, o efeito acumulado de uma amortização feita cedo é bem maior do que parece à primeira vista.</p>
        </div>
        <div class="border-t border-white/10 pt-6">
            <h2 class="font-serif text-xl text-white mb-3">Reduzir prazo ou reduzir parcela?</h2>
            <p>Ao amortizar, o banco costuma oferecer duas opções: manter a parcela igual e encurtar quantos meses faltam, ou manter o prazo original e diminuir o valor da parcela. Reduzir o prazo geralmente economiza mais juros no total ao longo de todo o contrato — mas reduzir a parcela alivia mais o orçamento mês a mês, o que pode fazer mais sentido dependendo do seu momento financeiro.</p>
        </div>''',
        "cta_href": "comparador-bancos",
        "cta_texto": "Simular meu financiamento",
    },
    {
        "slug": "aprenda-fgts-financiamento-imobiliario",
        "titulo_h1": "FGTS no financiamento imobiliário: como usar pra entrada ou amortização",
        "titulo_pagina": "FGTS no financiamento imobiliário: como usar | Datalab Global",
        "meta_description": "Como usar o FGTS no financiamento imobiliário: dar entrada, amortizar o saldo devedor a cada 2 anos ou quitar parte das parcelas. Veja as regras.",
        "resumo_card": "O saldo que a maioria dos trabalhadores CLT já tem guardado — e pode usar pra pagar menos juros no financiamento.",
        "corpo_html": '''<p>O FGTS (Fundo de Garantia do Tempo de Serviço) pode ser usado de mais de uma forma dentro de um financiamento imobiliário residencial, desde que o imóvel e o comprador atendam às regras do programa — normalmente, o imóvel precisa ser residencial urbano e usado pra moradia própria, e o comprador não pode ter outro financiamento ativo pelo Sistema Financeiro de Habitação.</p>
        <div class="border-t border-white/10 pt-6">
            <h2 class="font-serif text-xl text-white mb-3">As formas de uso mais comuns</h2>
            <p>Você pode usar o FGTS pra dar parte da <strong class="text-white">entrada</strong> na compra, reduzindo o valor que precisa ser financiado (e, por consequência, o total de juros pagos). Também é possível usar o saldo pra <strong class="text-white">amortizar</strong> o saldo devedor a cada período (geralmente a cada 2 anos), ou pra complementar/quitar parcelas em situações específicas, como desemprego.</p>
        </div>
        <div class="border-t border-white/10 pt-6">
            <h2 class="font-serif text-xl text-white mb-3">Por que isso muda sua simulação</h2>
            <p>Quanto mais entrada você conseguir dar — usando FGTS ou não — menor o valor financiado, e menor o CET total pago em juros ao longo do contrato. Vale simular seu financiamento aqui já considerando o saldo de FGTS que você pretende usar como parte da entrada, pra ver o efeito real na sua parcela.</p>
        </div>''',
        "cta_href": "comparador-bancos",
        "cta_texto": "Simular com entrada + FGTS",
    },
    {
        "slug": "aprenda-ltv-financiamento-imobiliario",
        "titulo_h1": "LTV (Loan-to-Value): o que é e como afeta sua taxa de juros",
        "titulo_pagina": "O que é LTV no financiamento imobiliário? | Datalab Global",
        "meta_description": "O que é LTV (Loan-to-Value) no financiamento imobiliário: a proporção entre valor financiado e valor do imóvel e por que mais entrada reduz a taxa.",
        "resumo_card": "A proporção entre quanto você financia e quanto vale o imóvel — e por que ela pesa direto na taxa que o banco te oferece.",
        "corpo_html": '''<p>LTV — Loan-to-Value — é a proporção entre o valor financiado e o valor total do imóvel. Um LTV de 80%, por exemplo, significa que o banco está financiando 80% do valor do imóvel, e você está entrando com os outros 20% como entrada.</p>
        <div class="border-t border-white/10 pt-6">
            <h2 class="font-serif text-xl text-white mb-3">Por que o banco olha pra isso</h2>
            <p>Quanto maior o LTV (ou seja, quanto menor a sua entrada em relação ao valor do imóvel), maior o risco que o banco assume — se o financiamento não for pago, o imóvel pode valer menos que o saldo devedor. Por isso, bancos costumam oferecer taxas de juros melhores pra quem tem um LTV menor, ou seja, pra quem dá uma entrada maior.</p>
        </div>
        <div class="border-t border-white/10 pt-6">
            <h2 class="font-serif text-xl text-white mb-3">O que isso significa na prática</h2>
            <p>Cada banco tem seu próprio LTV máximo (o quanto ele aceita financiar) e sua própria política de taxa por faixa de LTV — é por isso que aumentar sua entrada, mesmo que pareça pouco, pode te colocar numa faixa de taxa melhor, além de reduzir o valor total financiado. Vale simular com valores de entrada diferentes pra ver esse efeito na sua taxa e na sua parcela.</p>
        </div>''',
        "cta_href": "comparador-bancos",
        "cta_texto": "Simular com entrada diferente",
    },
    {
        "slug": "aprenda-financiamento-x-consorcio-imobiliario",
        "titulo_h1": "Financiamento x Consórcio imobiliário: qual a diferença",
        "titulo_pagina": "Financiamento x Consórcio imobiliário: diferenças | Datalab Global",
        "meta_description": "Financiamento ou consórcio de imóvel? Compare quem entra primeiro no imóvel, quem paga juros e quando cada modalidade faz mais sentido.",
        "resumo_card": "Um te dá o imóvel agora com juros; o outro é mais barato, mas sem data certa. Veja qual combina com seu momento.",
        "corpo_html": '''<p>Financiamento e consórcio resolvem o mesmo problema — comprar um imóvel sem pagar tudo à vista — de formas bem diferentes, e a escolha certa depende principalmente de uma coisa: você precisa do imóvel <strong class="text-white">agora</strong>, ou pode esperar?</p>
        <div class="border-t border-white/10 pt-6">
            <h2 class="font-serif text-xl text-white mb-3">Financiamento: imóvel já, com juros</h2>
            <p>No financiamento, o banco libera o valor, você compra o imóvel de imediato, e paga de volta em parcelas (SAC ou Price) com juros — é o que este simulador calcula. A certeza de já poder morar ou usar o imóvel tem um custo: o CET (juros + seguros + taxas) que você vê em cada simulação.</p>
        </div>
        <div class="border-t border-white/10 pt-6">
            <h2 class="font-serif text-xl text-white mb-3">Consórcio: sem juros, mas sem data certa</h2>
            <p>No consórcio, você entra num grupo de pessoas que pagam mensalidades numa espécie de poupança coletiva, sem juros — só correção monetária e uma taxa de administração. Você só recebe a carta de crédito pra comprar o imóvel quando é sorteado ou dá um lance vencedor num dos encontros mensais do grupo, o que pode acontecer logo no início ou só perto do fim do prazo contratado. O custo total costuma ser menor que o do financiamento, em troca de não saber exatamente quando o imóvel sai do papel.</p>
        </div>
        <div class="border-t border-white/10 pt-6">
            <h2 class="font-serif text-xl text-white mb-3">Qual escolher</h2>
            <p>Se você precisa do imóvel pra morar logo, o financiamento resolve isso — o CET é, na prática, o preço de não esperar. Se você tem flexibilidade de tempo e quer pagar menos no total, o consórcio tende a sair mais barato.</p>
        </div>''',
        "cta_href": "comparador-bancos",
        "cta_texto": "Simular financiamento imobiliário",
    },
]


def gerar_calculo_js():
    """Achado real (13/set/2026, PageSpeed Insights: "Reduza o JavaScript
    não usado", 149 KiB — eco do mesmo achado já resolvido no projeto
    irmão de veículos): as ~330 linhas de JS do simulador (calculadora +
    comparação de mercado + tooltips) estavam coladas INLINE em cada uma
    das 1680 páginas individuais — o navegador baixava e reparseava a
    MESMA cópia a cada navegação entre páginas, sem nenhum benefício de
    cache. Extraído pro mesmo padrão do irmão (um único calculo.js
    referenciado por <script src>, baixado e cacheado uma vez só): o
    texto abaixo é o JS REAL extraído de uma página já gerada (não
    retranscrito à mão — zero risco de erro de transcrição numa função
    financeira). Só o que é genuinamente igual em toda página fica aqui;
    REGRA_PRAZO_MAX/REGRA_PERC_ENTRADA_MIN/BANCOS_JS/BANCO_ATUAL_CHAVE
    (dados específicos de cada página) e o window.onload (que usa o
    valor inicial do slider desta página) continuam inline, curtos, só
    com o que varia de fato."""
    return '''// Gerado por gerador.py (gerar_calculo_js) — não editar à mão
// sem também atualizar as páginas que dependem dele.

        function unformatCurrency(val) { return typeof val === 'number' ? val : Number(val.replace(/\\D/g, '')) / 100; }
        function formatCurrency(val) { return (val).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
        function initMask(inputId) { const input = document.getElementById(inputId); let rawVal = unformatCurrency(input.value); if(rawVal > 0) input.value = formatCurrency(rawVal); input.addEventListener('input', function(e) { let raw = unformatCurrency(e.target.value); e.target.value = formatCurrency(raw); }); }

        // Atualiza um número de resultado com um pulso de cor quando o valor
        // muda de verdade (evita reiniciar a animação em toda chamada de
        // calcularTudo(), inclusive quando o número não mudou nada).
        function atualizarValor(id, texto) {
            const el = document.getElementById(id);
            if (!el || el.innerText === texto) return;
            el.innerText = texto;
            el.classList.remove('valor-pulse');
            void el.offsetWidth; // força reflow, senão o navegador não reinicia a animação
            el.classList.add('valor-pulse');
        }

        function syncSliderInput(sliderId, inputId) {
            const slider = document.getElementById(sliderId);
            const input = document.getElementById(inputId);
            slider.addEventListener('input', function() { input.value = formatCurrency(Number(this.value)); calcularTudo(); });
            input.addEventListener('blur', function() { let val = unformatCurrency(this.value); slider.value = val; calcularTudo(); });
        }

        // CET (Custo Efetivo Total) real via TIR (bisseção), espelhando o mesmo
        // cálculo do Python (gerador.py / calcular_cet_real): soma juros +
        // seguro MIP (sobre saldo devedor) + seguro DFI (sobre valor do imóvel)
        // + taxa de administração mensal, e resolve a taxa mensal que zera o
        // valor presente do fluxo de caixa.
        function calcularCET(vFinanciado, prazoMeses, taxaMensal, vImovel, sistema) {
            if (vFinanciado <= 0 || prazoMeses <= 0) return 0;
            const TAXA_MIP_MENSAL = 0.00030, TAXA_DFI_MENSAL = 0.000129, TAXA_ADMIN_MENSAL = 25.00;
            let saldo = vFinanciado, pmtPrice = 0;
            if (sistema === 'PRICE') {
                pmtPrice = (taxaMensal > 0)
                    ? vFinanciado * (taxaMensal * Math.pow(1 + taxaMensal, prazoMeses)) / (Math.pow(1 + taxaMensal, prazoMeses) - 1)
                    : vFinanciado / prazoMeses;
            }
            const fluxo = [];
            for (let m = 0; m < prazoMeses; m++) {
                const juros = saldo * taxaMensal;
                const amortizacao = (sistema === 'SAC') ? (vFinanciado / prazoMeses) : (pmtPrice - juros);
                const seguroMip = saldo * TAXA_MIP_MENSAL;
                const seguroDfi = vImovel * TAXA_DFI_MENSAL;
                fluxo.push(amortizacao + juros + seguroMip + seguroDfi + TAXA_ADMIN_MENSAL);
                saldo -= amortizacao;
            }
            const vpl = (r) => {
                let total = -vFinanciado;
                for (let i = 0; i < fluxo.length; i++) total += fluxo[i] / Math.pow(1 + r, i + 1);
                return total;
            };
            let lo = 0, hi = 0.05;
            for (let i = 0; i < 60; i++) {
                const mid = (lo + hi) / 2;
                if (vpl(mid) > 0) lo = mid; else hi = mid;
            }
            const tirMensal = (lo + hi) / 2;
            return (Math.pow(1 + tirMensal, 12) - 1) * 100;
        }

        // Simula amortização extra RECORRENTE (não um pagamento único): a
        // cada `periodicidade` meses, abate `aporte` do saldo devedor,
        // parando quando o saldo zera ou o prazo original acaba. É assim
        // que a maioria das pessoas amortiza na prática (várias vezes, ex:
        // com 13º/bônus), em vez de um único aporte grande no meio do
        // contrato.
        function simularComAmortizacaoRecorrente(vFinanciado, prazoMeses, taxaMensal, sistema, aporte, periodicidade, pmtPriceFixo) {
            let saldo = vFinanciado, jurosTotal = 0, meses = 0;
            while (saldo > 0.005 && meses < prazoMeses) {
                meses++;
                let juros = saldo * taxaMensal; jurosTotal += juros;
                let amortizacaoBase = (sistema === 'SAC') ? (vFinanciado / prazoMeses) : (pmtPriceFixo - juros);
                if (amortizacaoBase > saldo) amortizacaoBase = saldo;
                saldo -= amortizacaoBase;
                if (aporte > 0 && periodicidade > 0 && saldo > 0 && meses % periodicidade === 0) {
                    const abate = Math.min(aporte, saldo);
                    saldo -= abate;
                }
            }
            return { jurosTotal, meses };
        }

        // Recalcula o ranking dos 15 bancos AO VIVO pro valor/prazo que o
        // visitante está simulando agora (não mais o cenário padrão fixo
        // da página). Espelha comparar_todos_bancos() do gerador.py: cada
        // banco usa sua PRÓPRIA entrada mínima (LTV) e sua PRÓPRIA taxa
        // padrão — só o banco desta página usa a taxa/CET que o visitante
        // está vendo na tela agora (cetAtualLive), pra nunca mostrar dois
        // números diferentes do mesmo banco na mesma página.
        function calcularRankingBancosLive(vImovelLive, prazoLive, cetAtualLive) {
            const resultados = [];
            for (const b of BANCOS_JS) {
                const prazoB = Math.min(prazoLive, b.prazoMax);
                const entradaB = vImovelLive * (1 - b.ltv);
                const vFinanciadoB = vImovelLive - entradaB;
                if (vFinanciadoB <= 0) continue;

                const ehAtual = (b.chave === BANCO_ATUAL_CHAVE);
                const taxaMensalB = (b.taxa / 100) / 12;
                const cetB = ehAtual ? cetAtualLive : calcularCET(vFinanciadoB, prazoB, taxaMensalB, vImovelLive, 'SAC');

                // Reconstrói a URL da página equivalente pelo MESMO padrão de
                // slug usado na geração (simulador-{banco}-{valor}-mil-{prazo}-meses),
                // "encaixando" o valor/prazo ao vivo na grade real de páginas
                // geradas (múltiplos de R$50mil entre 150mil-1,5mi; prazo 360
                // ou 420, o que existir pra esse banco) — assim o link NUNCA
                // aponta pra uma URL que não existe, mesmo fora da grade.
                const valorGrade = Math.min(1500000, Math.max(150000, Math.round(vImovelLive / 50000) * 50000));
                const candidatosPrazo = [360, 420].filter(p => p <= b.prazoMax);
                const prazoGrade = candidatosPrazo.reduce((melhor, p) =>
                    Math.abs(p - prazoLive) < Math.abs(melhor - prazoLive) ? p : melhor, candidatosPrazo[0] || b.prazoMax);
                const slugBanco = b.chave.toLowerCase().replace(/\\s+/g, '-');
                const slug = candidatosPrazo.length
                    ? `simulador-${slugBanco}-${Math.round(valorGrade / 1000)}-mil-${prazoGrade}-meses`
                    : null;

                resultados.push({
                    chave: b.chave, nome: b.nome, cet: cetB, ehAtual,
                    entradaPerc: Math.round((1 - b.ltv) * 100), slug,
                });
            }
            resultados.sort((a, b) => a.cet - b.cet);
            return resultados;
        }

        // Espelha o bloco Python "Faixa de CET no Mercado" (e
        // calcular_marcador_posicao_mercado): a posição do marcador é
        // interpolação linear do CET real do banco atual contra o
        // mínimo/máximo real da faixa (valor, não ranking) — testado e
        // revertido de "fração do ranking" no mesmo dia (07/set/2026), a
        // pedido do usuário: com todo marcador igualmente espaçado a
        // barra perdia a noção de o quanto os bancos realmente se
        // aproximam ou distanciam uns dos outros em taxa — ver docstring
        // da função Python irmã pro raciocínio completo. Só precisa do
        // menor/maior CET do ranking pros rótulos das pontas (não mais
        // do nome de cada banco), e o CTA sempre aponta pra Financia
        // Tudo — nunca pra um concorrente.
        function renderizarComparacaoMercado(vImovelLive, prazoLive, cetAtualLive, nomeBancoAtual) {
            const elGrafico = document.getElementById('grafico_comparacao_mercado');
            const elTexto = document.getElementById('texto_resumo_mercado');
            if (!elGrafico || !elTexto) return; // página sem ranking (nenhum banco elegível na geração)

            // "a Caixa", "a Poupex": artigo feminino (flag "fem" vem de bancos.py via BANCOS_JS)
            const bancoFem = !!(BANCOS_JS.find(b => b.nome === nomeBancoAtual) || {}).fem;

            const ranking = calcularRankingBancosLive(vImovelLive, prazoLive, cetAtualLive);
            if (ranking.length === 0) return;

            const cetMin = ranking[0].cet;
            const cetMax = ranking[ranking.length - 1].cet;
            const spread = cetMax - cetMin;
            let marcadorPct = spread > 0 ? Math.round(((cetAtualLive - cetMin) / spread) * 100) : 50;
            marcadorPct = Math.max(2, Math.min(98, marcadorPct));

            const cetAtualFmt = cetAtualLive.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            const cetMinFmt = cetMin.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            const cetMaxFmt = cetMax.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});

            elGrafico.innerHTML = `
                <div class="relative h-2 rounded-full bg-gradient-to-r from-emerald-500 via-amber-400 to-rose-500">
                    <div class="absolute top-1/2 h-4 w-4 rounded-full bg-white border-2 border-emerald-950 shadow-[0_0_0_3px_rgba(16,185,129,0.35)]" style="left:${marcadorPct}%; transform:translate(-50%,-50%)" title="${nomeBancoAtual}: ${cetAtualFmt}%"></div>
                </div>
                <div class="flex justify-between text-[10px] text-slate-400 uppercase tracking-wide">
                    <span>${cetMinFmt}% menor CET</span>
                    <span>${cetMaxFmt}% maior CET</span>
                </div>`;

            const hrefFinanciaTudo = 'https://app.financiatudo.com.br/financiamento-de-imoveis/chave/8940d282b765cbf97b6df55fd1eb0b52b18b2f6e';

            if (marcadorPct <= 15) {
                elTexto.innerHTML = `${bancoFem ? 'A' : 'O'} ${nomeBancoAtual} está entre as condições <strong class="text-emerald-400">mais competitivas</strong> que acompanhamos (${cetAtualFmt}% de CET, na faixa de ${cetMinFmt}% a ${cetMaxFmt}% do mercado). Vale confirmar essa condição e agilizar a aprovação sem custo.
                    <a href="${hrefFinanciaTudo}" target="_blank" rel="noopener sponsored" class="text-emerald-400 underline hover:text-emerald-300 block mt-2 font-semibold">Falar com a Financia Tudo →</a>`;
            } else {
                elTexto.innerHTML = `Nas condições simuladas, o CET no mercado costuma variar entre <strong class="text-emerald-400">${cetMinFmt}%</strong> e <strong class="text-emerald-400">${cetMaxFmt}%</strong> — aqui ${bancoFem ? 'na' : 'no'} ${nomeBancoAtual} está em ${cetAtualFmt}%. Encontrar e negociar manualmente a melhor condição pode levar semanas de idas e vindas ao banco.
                    <a href="${hrefFinanciaTudo}" target="_blank" rel="noopener sponsored" class="text-emerald-400 underline hover:text-emerald-300 block mt-2 font-semibold">É esse trabalho que a Financia Tudo faz por você, sem custo →</a>`;
            }
        }

        function calcularTudo() {
            const vImovel = unformatCurrency(document.getElementById('input_imovel').value);
            let entrada = unformatCurrency(document.getElementById('input_entrada').value);

            // TRAVA 1: ENTRADA NÃO PODE SER MENOR QUE O MÍNIMO E NÃO PODE PASSAR DE 80% DO IMÓVEL
            const entradaMinimaReal = vImovel * REGRA_PERC_ENTRADA_MIN;
            const entradaMaximaReal = vImovel * 0.80; // Regra de Sanidade de Mercado (80% máx de entrada)

            if (entrada < entradaMinimaReal) {
                entrada = entradaMinimaReal;
                document.getElementById('input_entrada').value = formatCurrency(entrada);
            } else if (entrada > entradaMaximaReal) {
                entrada = entradaMaximaReal;
                document.getElementById('input_entrada').value = formatCurrency(entrada);
            }

            document.getElementById('slider_entrada').min = entradaMinimaReal;
            document.getElementById('slider_entrada').max = entradaMaximaReal;
            document.getElementById('slider_entrada').value = entrada;

            const taxaAnualRaw = document.getElementById('input_taxa').value.toString().replace(',', '.');
            const taxaAnual = parseFloat(taxaAnualRaw) || 0;
            const taxa = (taxaAnual / 100) / 12;

            let prazoOrig = parseInt(document.getElementById('input_prazo').value) || 0;
            if (prazoOrig > REGRA_PRAZO_MAX) {
                prazoOrig = REGRA_PRAZO_MAX;
                document.getElementById('input_prazo').value = prazoOrig;
            }

            let anosEquivalentes = Math.floor(prazoOrig / 12);
            document.getElementById('hint_anos').innerText = anosEquivalentes;
            document.getElementById('label_anos').innerText = anosEquivalentes + " anos";

            const sistema = document.querySelector('input[name="sistema"]:checked').value;
            const vFinanciado = vImovel - entrada;

            // TRAVA 2 (CORRIGIDA): a amortização extra nunca pode passar do
            // SALDO DEVEDOR real (valor do imóvel - entrada). Antes o teto
            // era "entradaMaximaReal - entrada", que é sempre MENOR que o
            // saldo devedor e impedia simulações válidas de quitação quase
            // total, contrariando a regra de negócio original.
            let aporteRecorrente = unformatCurrency(document.getElementById('input_amortizar').value);
            let amortizacaoMaxima = vFinanciado;
            if (amortizacaoMaxima < 0) amortizacaoMaxima = 0;

            if (aporteRecorrente > amortizacaoMaxima) {
                aporteRecorrente = amortizacaoMaxima;
                document.getElementById('input_amortizar').value = formatCurrency(aporteRecorrente);
            }
            document.getElementById('slider_amortizar').max = amortizacaoMaxima;
            document.getElementById('slider_amortizar').value = aporteRecorrente;

            const periodicidade = parseInt(document.getElementById('slider_periodicidade').value) || 1;
            document.getElementById('label_periodicidade').innerText = 'a cada ' + periodicidade + (periodicidade === 1 ? ' mês' : ' meses');

            if (vFinanciado <= 0 || prazoOrig <= 0) return;

            let saldoTrad = vFinanciado; let jurosTotalTrad = 0; let p1Trad = 0; let pUTrad = 0; let pmtPriceTrad = 0;

            // Parcela fixa do PRICE independe do sistema selecionado na tela —
            // calculada sempre, porque a recomendação SAC vs. PRICE (mais
            // abaixo) precisa simular os dois sistemas com o mesmo plano de
            // amortização, não só o que está marcado no momento.
            if (taxa > 0) { pmtPriceTrad = vFinanciado * (taxa * Math.pow(1 + taxa, prazoOrig)) / (Math.pow(1 + taxa, prazoOrig) - 1);
            } else { pmtPriceTrad = vFinanciado / prazoOrig; }

            for (let m = 1; m <= prazoOrig; m++) {
                let juros = saldoTrad * taxa; jurosTotalTrad += juros;
                let amortizacaoBase = (sistema === 'SAC') ? (vFinanciado / prazoOrig) : (pmtPriceTrad - juros);
                let parcelaMensal = amortizacaoBase + juros;
                if (m === 1) p1Trad = parcelaMensal;
                if (m === prazoOrig) pUTrad = parcelaMensal;
                saldoTrad -= amortizacaoBase;
            }

            const resultadoNovo = simularComAmortizacaoRecorrente(vFinanciado, prazoOrig, taxa, sistema, aporteRecorrente, periodicidade, pmtPriceTrad);
            const jurosTotalNovo = resultadoNovo.jurosTotal;
            const mesesNovo = resultadoNovo.meses;

            const economiaJuros = jurosTotalTrad - jurosTotalNovo;
            const mesesEliminados = Math.max(0, prazoOrig - mesesNovo);
            const totalDesembolsado = vFinanciado + jurosTotalTrad;
            const cfg = {style:'currency',currency:'BRL'};
            atualizarValor('res_p1', p1Trad.toLocaleString('pt-BR', cfg));
            atualizarValor('res_pU', pUTrad.toLocaleString('pt-BR', cfg));
            atualizarValor('res_capital', vFinanciado.toLocaleString('pt-BR', cfg));
            atualizarValor('res_total_pago', totalDesembolsado.toLocaleString('pt-BR', cfg));
            atualizarValor('res_economia', economiaJuros.toLocaleString('pt-BR', cfg));

            const cetReal = calcularCET(vFinanciado, prazoOrig, taxa, vImovel, sistema);
            atualizarValor('res_cet', cetReal.toLocaleString('pt-BR', {minimumFractionDigits:2, maximumFractionDigits:2}) + '%');
            const rendaSugerida = Math.ceil((p1Trad / 0.30) / 50) * 50;
            atualizarValor('res_renda', rendaSugerida.toLocaleString('pt-BR', cfg));

            let anos = Math.floor(mesesEliminados / 12); let meses = mesesEliminados % 12; let textoTempo = "";
            if (anos > 0) textoTempo += anos + (anos === 1 ? " Ano" : " Anos");
            if (anos > 0 && meses > 0) textoTempo += " e ";
            if (meses > 0 || (anos === 0 && meses === 0)) textoTempo += meses + (meses === 1 ? " Mês" : " Meses");
            if (textoTempo === "") textoTempo = "0 Meses";
            atualizarValor('res_impacto', textoTempo);
            let pctNovoPrazo = (mesesNovo / prazoOrig) * 100;
            document.getElementById('bar_novo_prazo').style.width = pctNovoPrazo + '%';

            // Recomendação SAC vs. PRICE PARA ESSE PLANO DE AMORTIZAÇÃO:
            // simula os dois sistemas do zero (independente do que está
            // marcado na tela) com o mesmo aporte recorrente, e recomenda o
            // que gera menos juros totais nesse cenário específico. Com
            // amortização frequente, o resultado pode inverter a regra
            // padrão de "SAC é sempre mais barato" — no PRICE o saldo
            // devedor cai mais devagar no início, então o mesmo aporte
            // extra abate uma fatia maior de juros futuros.
            const simSac = simularComAmortizacaoRecorrente(vFinanciado, prazoOrig, taxa, 'SAC', aporteRecorrente, periodicidade, pmtPriceTrad);
            const simPrice = simularComAmortizacaoRecorrente(vFinanciado, prazoOrig, taxa, 'PRICE', aporteRecorrente, periodicidade, pmtPriceTrad);
            const elTextoRecomendacao = document.getElementById('texto_recomendacao_sistema');
            if (aporteRecorrente <= 0) {
                elTextoRecomendacao.innerHTML = 'Informe um valor de amortização acima para ver qual sistema — SAC ou PRICE — te economiza mais juros com esse plano de aportes.';
            } else {
                const diferenca = Math.abs(simSac.jurosTotal - simPrice.jurosTotal);
                const melhorSistema = (simSac.jurosTotal <= simPrice.jurosTotal) ? 'SAC' : 'PRICE';
                const diferencaFmt = diferenca.toLocaleString('pt-BR', cfg);
                elTextoRecomendacao.innerHTML = 'Amortizando ' + formatCurrency(aporteRecorrente) + ' a cada ' + periodicidade + (periodicidade === 1 ? ' mês' : ' meses') + ', o <strong class="text-emerald-400">' + melhorSistema + '</strong> te economiza aproximadamente <strong class="text-emerald-400">' + diferencaFmt + '</strong> em juros nesse cenário, contra o outro sistema.';
            }

            // A caixinha "Comparação com o Mercado" precisa ser recalculada
            // aqui também — sempre ANCORADA em SAC (não no toggle SAC/PRICE
            // da tela), pra ficar na mesma régua que os outros 14 bancos,
            // que também são sempre comparados em SAC. Sem isso, o gráfico
            // e o texto da caixinha ficavam "presos" no cenário padrão da
            // página, divergindo do que os campos acima já mostravam assim
            // que o visitante mexia em qualquer slider.
            const cetSacAtual = calcularCET(vFinanciado, prazoOrig, taxa, vImovel, 'SAC');
            const nomeBancoAtual = (BANCOS_JS.find(b => b.chave === BANCO_ATUAL_CHAVE) || {}).nome || BANCO_ATUAL_CHAVE;
            renderizarComparacaoMercado(vImovel, prazoOrig, cetSacAtual, nomeBancoAtual);
        }

        function ajustarTooltips() {
            const margem = 8;
            // Achado real (06/set/2026, auditoria do projeto irmão de
            // veículos): usar window.innerWidth aqui deixava o balão
            // estourando a tela mesmo com ajustarTooltips() já rodando no
            // window.onload — confirmado ao vivo (Playwright/navegador
            // real, viewport 375px: scrollWidth 414 > clientWidth 375,
            // tooltip do CET estourando). Causa: esta página tem
            // overflow-x:hidden no <body>, e nesse caso window.innerWidth
            // pode devolver um valor MAIOR que a área realmente visível.
            // document.documentElement.clientWidth é a largura real
            // renderizada e não sofre desse problema.
            const larguraTela = document.documentElement.clientWidth;
            document.querySelectorAll('.tooltip-box').forEach(box => {
                const metade = box.offsetWidth / 2;
                box.style.setProperty('--tt-shift', (-metade) + 'px');
                const r = box.getBoundingClientRect();
                let shift = 0;
                if (r.right > larguraTela - margem) shift = (larguraTela - margem) - r.right;
                else if (r.left < margem) shift = margem - r.left;
                if (shift !== 0) box.style.setProperty('--tt-shift', (-metade + shift).toFixed(0) + 'px');
            });
        }
        window.addEventListener('resize', ajustarTooltips);
        // A posição do ícone pode mudar depois do primeiro cálculo (ex: a
        // fonte do Google Fonts carrega depois e reflui o texto ao redor).
        // Recalcula de novo assim que as fontes terminam de carregar, pra
        // não travar um deslocamento calculado com o layout ainda "errado".
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(ajustarTooltips).catch(() => {});
        }'''


def gerar_sitemap(urls, pasta_saida, dominio, data_ultima_atualizacao):
    # lastmod = data REAL da última mudança de taxa (não a data do deploy).
    # Ver obter_data_ultima_atualizacao(): "lastmod sempre = hoje" é tratado
    # pelo Google como sinal de frescor falso.
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml_content += f"  <url>\n    <loc>{dominio}/</loc>\n    <lastmod>{data_ultima_atualizacao}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>\n"
    for url in urls:
        xml_content += f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{data_ultima_atualizacao}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>\n"
    xml_content += '</urlset>'
    with open(os.path.join(pasta_saida, 'sitemap.xml'), "w", encoding="utf-8") as f:
        f.write(xml_content)


def gerar_robots_txt(pasta_saida, dominio):
    # "Allow: /" cobre todo mundo, incluindo os crawlers de IA (GPTBot,
    # ClaudeBot, PerplexityBot, Google-Extended etc.) — listamos alguns
    # explicitamente só por clareza/documentação, o efeito é o mesmo do "*".
    conteudo = (
        "User-agent: *\n"
        "Allow: /\n\n"
        "User-agent: GPTBot\n"
        "Allow: /\n\n"
        "User-agent: ClaudeBot\n"
        "Allow: /\n\n"
        "User-agent: PerplexityBot\n"
        "Allow: /\n\n"
        "User-agent: Google-Extended\n"
        "Allow: /\n\n"
        f"Sitemap: {dominio}/sitemap.xml\n"
    )
    with open(os.path.join(pasta_saida, 'robots.txt'), "w", encoding="utf-8") as f:
        f.write(conteudo)


def gerar_llms_txt(pasta_saida, dominio, total_paginas, data_ultima_atualizacao):
    """llms.txt: padrão emergente (2025+) que resume o site pra engines de
    IA/LLM que buscam contexto rápido antes de citar uma página — análogo
    ao robots.txt, mas descritivo em vez de regra de acesso."""
    # Lista de bancos montada a partir de BANCOS (não hardcoded) — achado
    # real (06/set/2026): esse texto ainda citava os 4 bancos de home
    # equity (C6 Bank, Bari, Cash Me, Daycoval) removidos do produto,
    # igual ao "mais de 15 bancos" que já tinha sido corrigido na home.
    lista_bancos = ", ".join(dados["nome_exibicao"] for dados in BANCOS.values())
    conteudo = f"""# Datalab Global

> Hub financeiro com simuladores de financiamento imobiliário para {len(BANCOS)} instituições brasileiras ({lista_bancos}). Calcula parcelas nos sistemas SAC e PRICE, e simula a economia de juros ao antecipar amortizações.

Dados atualizados em: {data_ultima_atualizacao}
Total de páginas de simulação: {total_paginas}

## Páginas
- [Home / lista de bancos]({dominio}/)
- [Comparativo de taxas entre os {len(BANCOS)} bancos]({dominio}/comparador-bancos)
- [Financiamento imobiliário: parcela por valor e prazo]({dominio}/financiamento-imobiliario)
- [Dados abertos: taxas de financiamento por banco, série mensal em CSV e JSON]({dominio}/dados-abertos)
- [Simulador de financiamento para incorporar no seu site (grátis)]({dominio}/incorporar)
- [Imprensa: números atualizados para citar]({dominio}/imprensa)
- [Sitemap completo]({dominio}/sitemap.xml)

## Sobre os dados
Taxas de juros, LTV (percentual mínimo de entrada) e prazo máximo são específicos de cada instituição financeira e atualizados mensalmente. Cada página de simulador (padrão de URL: /simulador-{{banco}}-{{valor}}-mil-{{prazo}}-meses, sem extensão) traz cálculo de parcelas, custo total e comparativo real entre os sistemas SAC e PRICE para o cenário daquele banco/valor/prazo específico.
"""
    with open(os.path.join(pasta_saida, 'llms.txt'), "w", encoding="utf-8") as f:
        f.write(conteudo)


if __name__ == "__main__":
    gerar_paginas_pseo()
