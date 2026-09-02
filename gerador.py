import os
import csv
import random
from datetime import date, datetime

from bancos import BANCOS, obter_regra, nome_exibicao
from icones import icone, tooltip

LINK_FINANCIA_TUDO = "https://app.financiatudo.com.br/financiamento-de-imoveis/chave/8940d282b765cbf97b6df55fd1eb0b52b18b2f6e"
DOMINIO = 'https://datalabglobal.com'
ARQUIVO_ULTIMA_ATUALIZACAO = 'ultima_atualizacao_taxas.txt'


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


def calcular_sac_price(valor_financiado, prazo_meses, taxa_anual):
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

    return {
        "p1_sac": p1_sac, "pU_sac": pU_sac, "total_sac": valor_financiado + juros_total_sac,
        "p1_price": pmt_price, "pU_price": pmt_price, "total_price": valor_financiado + juros_total_price,
        "economia_sac": juros_total_price - juros_total_sac,
    }


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


def formatar_valor_curto(valor_imovel):
    """Ex: 200000 -> '200 mil' | 1500000 -> '1,5 milhão'. Usado no title/H1/meta
    para casar com a forma como as pessoas realmente digitam a busca."""
    if valor_imovel >= 1_000_000:
        milhoes = valor_imovel / 1_000_000
        texto = f"{milhoes:.1f}".replace(".0", "").replace(".", ",")
        return f"{texto} milhão" if milhoes == 1 else f"{texto} milhões"
    milhares = int(round(valor_imovel / 1000))
    return f"{milhares} mil"


def formatar_reais(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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

        for p in todas_as_paginas:
            links_por_banco.setdefault(p['banco'], []).append(p)

        # Ordena cada cluster de banco de forma estável -> permite montar um
        # ciclo de linkagem interna que garante que TODA página recebe pelo
        # menos 1 link de entrada (elimina o risco de páginas órfãs que a
        # amostragem 100% aleatória anterior não garantia).
        for banco in links_por_banco:
            links_por_banco[banco].sort(key=lambda p: p["slug"])

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

            vfinanciado_padrao = valor_imovel - entrada_padrao
            comparativo = calcular_sac_price(vfinanciado_padrao, prazo, taxa)

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
                    random.sample(candidatos_mesmo_banco, min(faltam, len(candidatos_mesmo_banco)))
                )

            faltam = 4 - len(paginas_sorteadas)
            if faltam > 0:
                outras_paginas = [pag for pag in todas_as_paginas if pag["slug"] != slug and pag['banco'] != banco]
                if outras_paginas:
                    paginas_sorteadas.extend(random.sample(outras_paginas, min(faltam, len(outras_paginas))))

            links_internos_html = ""
            for pag_sorteada in paginas_sorteadas:
                termo = random.choice(termos_variados)
                links_internos_html += f"""
                <a href="{pag_sorteada['slug']}.html" class="block p-4 bg-white/5 rounded-xl border border-white/10 hover:border-emerald-500/50 hover:bg-white/10 transition-all">
                    <span class="text-xs text-emerald-500 font-bold uppercase tracking-wider block mb-1">{termo}</span>
                    <span class="text-sm text-slate-300 group-hover:text-white block">{pag_sorteada['banco_exib']} - {pag_sorteada['texto']}</span>
                </a>
                """

            faq_q1 = f"Vale a pena amortizar o {regra['mod'].lower()} no {banco_exib}?"
            faq_a1 = f"Sim! Ao fazer amortizações extras no {banco_exib}, você reduz diretamente o saldo devedor. Isso significa que você foge dos juros compostos cobrados ao longo dos {prazo} meses ({anos} anos), podendo economizar milhares de reais e quitar muito antes do previsto."
            faq_q2 = f"Qual a diferença entre a Tabela SAC e PRICE na simulação do {banco_exib}?"
            faq_a2 = f"Na Tabela SAC, a amortização é constante e o valor das parcelas do {banco_exib} diminui com o tempo. Já na Tabela PRICE, as parcelas são fixas do início ao fim do contrato. A escolha ideal depende do seu planejamento financeiro mensal."
            faq_q3 = f"É possível simular {valor_curto} em {anos} anos ({prazo} meses) com a taxa atual de {taxa}% a.a.?"
            faq_a3 = f"Sim. Nossa calculadora já utiliza a taxa de juros anual estimada em {taxa}% ao ano para o {banco_exib}, aplicada a um financiamento de {valor_amigavel} em {prazo} meses (equivalente a {anos} anos). Você pode ajustar os valores de entrada (margem de garantia) e prazo no simulador acima para ver o Custo Efetivo Total (CET) aproximado para o seu perfil e solicitar uma análise."

            titulo_pagina = montar_titulo(banco_exib, valor_curto, prazo, anos)
            meta_description_completa = (
                f"Simule {valor_curto} de {regra['mod'].lower()} pelo {banco_exib} em {prazo} meses "
                f"({anos} anos). Taxa estimada de {taxa}% a.a., entrada mínima de {(perc_entrada_minima*100):.0f}%, "
                f"cálculo de amortização SAC e PRICE."
            )
            meta_description_curta = (
                f"Simule {valor_curto} de {regra['mod'].lower()} pelo {banco_exib} em {prazo} meses "
                f"({anos} anos). Taxa estimada de {taxa}% a.a., entrada mínima de {(perc_entrada_minima*100):.0f}%."
            )
            # Nunca corta no meio de uma palavra/frase: usa a versão completa se
            # couber em 160 caracteres (limite prático do Google), senão a curta.
            meta_description = meta_description_completa if len(meta_description_completa) <= 160 else meta_description_curta
            meta_keywords = (
                f"simulador de financiamento, calculadora de amortização, empréstimo imobiliário, "
                f"financiar imóvel {valor_curto}, calcular juros {banco_exib}, amortizar financiamento {banco_exib}, "
                f"{prazo} meses, {anos} anos, financiamento {anos} anos, Custo Efetivo Total, TR, Saldo Devedor"
            )
            url_canonica = f"{dominio}/{slug}.html"
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
        {{ "@type": "ListItem", "position": 1, "name": "Datalab Global", "item": "{dominio}/index.html" }},
        {{ "@type": "ListItem", "position": 2, "name": "{banco_exib}", "item": "{dominio}/index.html#{banco.lower().replace(' ', '-')}" }},
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
      "name": "Como simular o financiamento {regra['mod'].lower()} do {banco_exib}",
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
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo_pagina}</title>
    <meta name="description" content="{meta_description}">
    <meta name="keywords" content="{meta_keywords}">
    <link rel="canonical" href="{url_canonica}" />

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="dns-prefetch" href="https://pagead2.googlesyndication.com">

    <meta property="og:type" content="website">
    <meta property="og:locale" content="pt_BR">
    <meta property="og:site_name" content="Datalab Global">
    <meta property="og:title" content="{titulo_pagina}">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:url" content="{url_canonica}">
    <meta property="og:image" content="{dominio}/logo.svg">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{titulo_pagina}">
    <meta name="twitter:description" content="{meta_description}">
    <meta name="twitter:image" content="{dominio}/logo.svg">

    <link rel="stylesheet" href="styles.css">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5414184968223405" crossorigin="anonymous"></script>

    <script type="application/ld+json">
    {schema_faq}
    </script>
    <script type="application/ld+json">
    {schema_breadcrumb}
    </script>
    <script type="application/ld+json">
    {schema_software}
    </script>
    <script type="application/ld+json">
    {schema_howto}
    </script>
</head>
<body class="antialiased flex flex-col">
    <nav class="border-b border-white/5 sticky top-0 z-50 backdrop-blur-2xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="index.html" class="flex items-center">
                    <img src="logo.svg" alt="Datalab Global" class="h-12 md:h-16 w-auto drop-shadow-[0_0_15px_rgba(16,185,129,0.2)] hover:scale-105 transition-transform duration-300">
                </a>
                <div class="hidden md:flex items-center space-x-3">
                    <a href="{LINK_FINANCIA_TUDO}" target="_blank" rel="noopener sponsored" class="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-6 py-2.5 rounded-full font-bold transition-all text-sm flex items-center shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                        Fazer Análise Grátis {icone('arrow-right', 'ml-2 text-sm')}
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <header class="py-12 md:py-16 relative z-10 text-center">
        <div class="inline-flex items-center gap-2.5 bg-white/5 border border-white/10 rounded-full pl-2 pr-4 py-1.5 mb-6">
            {favicon_com_fallback(url_logo_banco, banco_exib, "w-6 h-6")}
            <span class="text-xs font-bold text-slate-200 tracking-wide">{banco_exib}</span>
            <span class="text-[10px] text-slate-500 uppercase tracking-widest border-l border-white/10 pl-2">{regra['mod']}</span>
        </div>
        <h1 class="text-4xl md:text-5xl font-serif text-white mb-4 leading-tight px-4">
            Simulador {banco_exib}: {valor_curto} em {prazo} meses ({anos} anos)
        </h1>
        <p class="text-slate-400 text-base md:text-lg font-light tracking-wide max-w-3xl mx-auto px-4">
            Você está simulando um financiamento de <strong class="text-white font-medium">{valor_amigavel}</strong> pelo
            <strong class="text-white font-medium">{banco_exib}</strong>, em {prazo} meses (equivalente a
            <span id="label_anos" class="font-medium text-white">{anos} anos</span>), com entrada mínima de
            {(perc_entrada_minima*100):.0f}% e taxa estimada de {taxa}% a.a. Ajuste os valores abaixo para o seu caso.
        </p>
        <p class="text-slate-600 text-[10px] uppercase tracking-widest mt-4">Taxas atualizadas em {data_ultima_atualizacao_br}</p>
    </header>

    <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex-grow w-full relative z-10 space-y-8">

        <!-- ZONA A: O FINANCIAMENTO -->
        <div class="glass-panel p-8 md:p-10 rounded-3xl border-t border-slate-700/50 relative overflow-hidden">
            <h2 class="text-xs font-bold text-slate-300 uppercase tracking-widest mb-1 flex items-center relative z-10">
                {icone('invoice', 'mr-3')} 1. Estratégia
            </h2>
            <p class="text-slate-500 text-[11px] mb-8 pb-4 border-b border-white/10 relative z-10">Defina os parâmetros do seu financiamento {banco_exib.lower()}.</p>
            <div class="flex flex-col lg:flex-row gap-10 relative z-10">
                <div class="w-full lg:w-1/2 space-y-4">
                    <div class="bg-slate-800/60 p-5 rounded-2xl border border-white/10 shadow-md shadow-black/20 hover:border-emerald-500/30 transition-colors">
                        <div class="flex justify-between items-end mb-2">
                            <label class="text-[10px] font-semibold text-slate-400 uppercase tracking-widest flex items-center">
                                {icone('home', 'mr-1.5 text-slate-500')} Valor do Imóvel / Garantia
                                {tooltip('É o valor total do bem que você quer financiar. A partir dele calculamos a entrada mínima exigida pelo banco (regra de LTV) e o crédito liberado.')}
                            </label>
                            <input type="text" id="input_imovel" class="currency-input w-40 text-right bg-transparent font-medium text-white text-2xl outline-none border-b border-transparent focus:border-emerald-500 transition-colors" value="">
                        </div>
                        <input type="range" id="slider_imovel" min="100000" max="2000000" step="10000" value="{valor_imovel}" class="w-full mt-2">
                    </div>
                    <div class="bg-slate-800/60 p-5 rounded-2xl border border-white/10 shadow-md shadow-black/20 hover:border-emerald-500/30 transition-colors">
                        <div class="flex justify-between items-end mb-2">
                            <label class="text-[10px] font-semibold text-slate-400 uppercase tracking-widest flex items-center">
                                {icone('percent', 'mr-1.5 text-slate-500')} Entrada / Margem Retida
                                {tooltip(f'Quanto você paga à vista de imediato. Todo banco exige um mínimo (aqui, {(perc_entrada_minima*100):.0f}% pela regra de LTV do {banco_exib}) e o mercado considera pouco usual passar de 80% — acima disso, geralmente compensa mais comprar à vista.')}
                            </label>
                            <input type="text" id="input_entrada" class="currency-input w-40 text-right bg-transparent font-medium text-white text-2xl outline-none border-b border-transparent focus:border-emerald-500 transition-colors" value="">
                        </div>
                        <input type="range" id="slider_entrada" min="{int(entrada_minima_valor)}" max="1000000" step="5000" value="{int(entrada_padrao)}" class="w-full mt-2">
                        <p class="text-[9px] text-slate-500 mt-1 text-right">Mínimo exigido: {(perc_entrada_minima*100):.0f}% do valor</p>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-slate-800/60 p-5 rounded-2xl border border-white/10 shadow-md shadow-black/20 hover:border-emerald-500/30 transition-colors">
                            <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 flex items-center">
                                {icone('calendar', 'mr-1.5 text-slate-500')} Prazo
                                {tooltip(f'Quantidade de parcelas mensais do financiamento. O {banco_exib} permite no máximo {prazo_max_banco} meses ({prazo_max_banco // 12} anos) nessa modalidade.')}
                            </label>
                            <div class="flex items-center"><input type="number" id="input_prazo" min="12" max="{prazo_max_banco}" class="w-full bg-transparent font-medium text-white text-lg outline-none" value="{prazo}"><span class="text-xs text-slate-500 ml-2">meses</span></div>
                            <p class="text-[9px] text-slate-500 mt-1">Equivale a <span id="hint_anos">{anos}</span> anos</p>
                        </div>
                        <div class="bg-slate-800/60 p-5 rounded-2xl border border-white/10 shadow-md shadow-black/20 hover:border-emerald-500/30 transition-colors">
                            <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 flex items-center">
                                {icone('trending-up', 'mr-1.5 text-slate-500')} Taxa Estimada
                                {tooltip('Taxa de juros anual estimada, aplicada mensalmente sobre o saldo devedor. É a "taxa de vitrine" — sua taxa final aprovada depende da sua análise de crédito.')}
                            </label>
                            <div class="flex items-center"><input type="number" id="input_taxa" step="0.01" class="w-full bg-transparent font-medium text-white text-lg outline-none" value="{taxa}"><span class="text-xs text-slate-500 ml-2">% a.a.</span></div>
                        </div>
                    </div>
                    <div class="pt-2">
                        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center pl-2">
                            Sistema de Amortização
                            {tooltip('SAC: parcelas começam mais altas e caem com o tempo (amortização constante, menos juros no total). PRICE: parcelas fixas do início ao fim (mais previsível, porém mais juros no total).')}
                        </label>
                        <div class="flex bg-black/40 p-1 rounded-xl border border-white/5">
                            <label class="flex-1 text-center relative cursor-pointer"><input type="radio" name="sistema" value="SAC" class="peer sr-only" checked><div class="py-2.5 rounded-lg text-xs font-bold transition-all border border-transparent tracking-widest">SAC</div></label>
                            <label class="flex-1 text-center relative cursor-pointer"><input type="radio" name="sistema" value="PRICE" class="peer sr-only"><div class="py-2.5 rounded-lg text-xs font-bold transition-all border border-transparent tracking-widest">PRICE</div></label>
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
                            <div><p class="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-1.5">Crédito Liberado (Sem Juros)</p><p class="text-white font-medium text-lg currency-input" id="res_capital">R$ 0,00</p></div>
                            <div><p class="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-1.5 flex items-center">Custo Total Final (Capital + Juros)</p><p class="text-white font-medium text-xl currency-input" id="res_total_pago">R$ 0,00</p></div>
                        </div>
                        <div class="pt-6 border-t border-white/5">
                            <p class="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-3">Composição do custo total (cenário padrão)</p>
                            {svg_donut_capital_juros(vfinanciado_padrao, comparativo['total_sac'] - vfinanciado_padrao)}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ZONA B: A AMORTIZAÇÃO -->
        <div class="glass-panel-emerald rounded-3xl p-8 md:p-10 relative overflow-hidden shadow-[0_10px_40px_rgba(16,185,129,0.1)] border-t border-emerald-500/30" id="card_amortizacao">
            <h2 class="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-8 border-b border-emerald-500/20 pb-4 relative z-10 flex items-center">
                {icone('bolt', 'mr-3')} 2. Valor a Amortizar (A Solução)
            </h2>
            <div class="flex flex-col lg:flex-row gap-10 relative z-10">
                <div class="w-full lg:w-1/2 flex flex-col justify-center">
                    <label class="text-[10px] font-bold text-slate-300 uppercase tracking-widest block mb-4">Amortização Extra (Pagamento Único)</label>
                    <div class="relative mb-6">
                        <span class="absolute left-4 top-1/2 -translate-y-1/2 font-light text-emerald-500/50 text-3xl">R$</span>
                        <input type="text" id="input_amortizar" class="currency-input w-full bg-black/50 border border-emerald-500/30 rounded-2xl pl-16 pr-4 py-5 focus:border-emerald-400 font-medium text-emerald-400 text-4xl outline-none transition-all shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)]" value="{aporte_padrao_fmt}">
                    </div>
                    <input type="range" id="slider_amortizar" min="0" max="{slider_amortizar_max}" step="5000" value="{aporte_padrao}" class="w-full">
                </div>
                <div class="w-full lg:w-1/2 bg-black/40 border border-emerald-500/30 rounded-2xl p-8 backdrop-blur-sm text-center flex flex-col justify-center shadow-inner">
                    <div class="mb-8">
                        <p class="text-emerald-500/80 text-[10px] font-bold uppercase tracking-widest mb-3">Economia Total de Juros</p>
                        <p class="text-5xl md:text-6xl font-serif text-emerald-400 currency-input" id="res_economia">R$ 0,00</p>
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
        </div>

        <!-- ZONA COMPARATIVA: SAC vs PRICE COM NUMEROS REAIS (sem depender de JS) -->
        <div class="mt-8 bg-slate-900/40 border border-white/10 rounded-3xl p-8 md:p-10">
            <h2 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1 flex items-center">
                {icone('trending-up', 'mr-3 text-emerald-500')} Comparativo Real: SAC vs. PRICE
            </h2>
            <p class="text-slate-500 text-[11px] mb-6">
                Para {valor_curto} financiados pelo {banco_exib} em {prazo} meses, com entrada de {formatar_reais(entrada_padrao)} e taxa de {taxa}% a.a.:
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="bg-black/30 border {('border-emerald-500/40' if comparativo['total_sac'] <= comparativo['total_price'] else 'border-white/10')} rounded-2xl p-5 relative">
                    {('<span class="absolute -top-3 right-4 bg-emerald-500 text-slate-950 text-[9px] font-bold px-2.5 py-1 rounded-full uppercase tracking-widest shadow-lg">Mais econômico</span>' if comparativo['total_sac'] <= comparativo['total_price'] else '')}
                    <p class="text-white font-bold text-sm mb-3">Tabela SAC</p>
                    <div class="space-y-1.5 text-sm">
                        <div class="flex justify-between"><span class="text-slate-400">1ª parcela</span><span class="text-white currency-input">{formatar_reais(comparativo['p1_sac'])}</span></div>
                        <div class="flex justify-between"><span class="text-slate-400">Última parcela</span><span class="text-white currency-input">{formatar_reais(comparativo['pU_sac'])}</span></div>
                        <div class="flex justify-between pt-2 border-t border-white/10"><span class="text-slate-400">Total pago</span><span class="text-emerald-400 font-medium currency-input">{formatar_reais(comparativo['total_sac'])}</span></div>
                    </div>
                </div>
                <div class="bg-black/30 border {('border-emerald-500/40' if comparativo['total_price'] < comparativo['total_sac'] else 'border-white/10')} rounded-2xl p-5 relative">
                    {('<span class="absolute -top-3 right-4 bg-emerald-500 text-slate-950 text-[9px] font-bold px-2.5 py-1 rounded-full uppercase tracking-widest shadow-lg">Mais econômico</span>' if comparativo['total_price'] < comparativo['total_sac'] else '')}
                    <p class="text-white font-bold text-sm mb-3">Tabela PRICE</p>
                    <div class="space-y-1.5 text-sm">
                        <div class="flex justify-between"><span class="text-slate-400">Parcela fixa</span><span class="text-white currency-input">{formatar_reais(comparativo['p1_price'])}</span></div>
                        <div class="flex justify-between"><span class="text-slate-400">Última parcela</span><span class="text-white currency-input">{formatar_reais(comparativo['pU_price'])}</span></div>
                        <div class="flex justify-between pt-2 border-t border-white/10"><span class="text-slate-400">Total pago</span><span class="text-white font-medium currency-input">{formatar_reais(comparativo['total_price'])}</span></div>
                    </div>
                </div>
            </div>
            <p class="text-slate-400 text-xs mt-4 text-center">
                Nesse cenário, escolher <strong class="text-emerald-400">SAC em vez de PRICE</strong> economiza aproximadamente
                <strong class="text-emerald-400 currency-input">{formatar_reais(comparativo['economia_sac'])}</strong> em juros ao longo do contrato.
            </p>
        </div>

        <!-- BANNER DE CONVERSÃO FINANCIA TUDO -->
        <div class="mt-12 bg-gradient-to-r from-emerald-600 to-emerald-900 rounded-3xl p-8 md:p-12 relative overflow-hidden shadow-[0_20px_50px_rgba(16,185,129,0.3)] border border-emerald-400/50">
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

        <!-- ZONA DE MONETIZAÇÃO (INFO PRODUTO) -->
        <div class="mt-8 bg-gradient-to-r from-emerald-900/40 to-slate-900 border border-emerald-500/30 p-8 md:p-10 rounded-3xl flex flex-col md:flex-row items-center gap-8 relative overflow-hidden">
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

        <!-- ZONA E: GLOSSÁRIO / HUB DE AJUDA -->
        <div class="mt-16">
            <div class="flex items-center gap-3 mb-2 justify-center">
                {icone('book-open', 'text-emerald-500 text-xl')}
                <h3 class="text-2xl font-serif text-white text-center">Entenda os Termos Antes de Decidir</h3>
            </div>
            <p class="text-slate-500 text-sm text-center max-w-2xl mx-auto mb-8">
                Mais do que uma calculadora: reunimos aqui o que cada termo do seu financiamento {banco_exib.lower()} significa na prática.
            </p>
            <div class="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 md:gap-x-12 divide-y divide-white/10 md:divide-y-0">
                <div class="py-5 md:pt-0 md:border-b md:border-white/10">
                    <p class="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-2 flex items-center">{icone('percent', 'mr-2')} LTV (Loan-to-Value)</p>
                    <p class="text-slate-300 text-sm font-light leading-relaxed">É o percentual do valor do imóvel que o banco aceita financiar. No {banco_exib}, o LTV é de {(regra['ltv']*100):.0f}%, ou seja, sua entrada mínima é de {(perc_entrada_minima*100):.0f}%.</p>
                </div>
                <div class="py-5 md:pt-0 md:border-b md:border-white/10">
                    <p class="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-2 flex items-center">{icone('invoice', 'mr-2')} CET (Custo Efetivo Total)</p>
                    <p class="text-slate-300 text-sm font-light leading-relaxed">É o custo real do financiamento, somando juros, tarifas e seguros — sempre maior que a taxa de juros anunciada. Use-o para comparar propostas de bancos diferentes de forma justa.</p>
                </div>
                <div class="py-5 md:border-b md:border-white/10">
                    <p class="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-2 flex items-center">{icone('trending-up', 'mr-2')} Saldo Devedor</p>
                    <p class="text-slate-300 text-sm font-light leading-relaxed">É quanto você ainda deve ao banco em determinado momento (valor financiado menos o que já foi amortizado). É sobre ele que os juros do mês seguinte são calculados.</p>
                </div>
                <div class="py-5 md:border-b md:border-white/10">
                    <p class="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-2 flex items-center">{icone('bolt', 'mr-2')} Amortização Extra</p>
                    <p class="text-slate-300 text-sm font-light leading-relaxed">Pagamento fora do cronograma que abate diretamente o saldo devedor (não é uma parcela adiantada). Reduz os juros futuros e pode encurtar o prazo ou o valor das próximas parcelas.</p>
                </div>
                <div class="py-5 pb-0 md:pb-0">
                    <p class="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-2 flex items-center">{icone('calendar', 'mr-2')} SAC vs. PRICE</p>
                    <p class="text-slate-300 text-sm font-light leading-relaxed">SAC amortiza um valor fixo por mês (parcelas decrescentes, menos juros no total). PRICE mantém a parcela fixa (mais previsível, mas mais juros ao longo do contrato).</p>
                </div>
                <div class="py-5 pb-0 md:pb-0">
                    <p class="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-2 flex items-center">{icone('home', 'mr-2')} Taxa de Vitrine</p>
                    <p class="text-slate-300 text-sm font-light leading-relaxed">A taxa de {taxa}% a.a. mostrada aqui é a taxa padrão anunciada pelo {banco_exib}. Sua taxa final depende do seu relacionamento com o banco e da análise de crédito.</p>
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
                        <span class="faq-toggle-icon shrink-0 text-slate-500 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_a1}</p>
                </details>
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h4 class="text-emerald-400 font-bold text-sm">{faq_q2}</h4>
                        <span class="faq-toggle-icon shrink-0 text-slate-500 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_a2}</p>
                </details>
                <details class="group bg-white/5 border border-white/10 rounded-xl overflow-hidden open:border-emerald-500/30 transition-colors">
                    <summary class="cursor-pointer list-none p-5 flex items-center justify-between gap-4">
                        <h4 class="text-emerald-400 font-bold text-sm">{faq_q3}</h4>
                        <span class="faq-toggle-icon shrink-0 text-slate-500 group-open:rotate-45 transition-transform text-lg leading-none">+</span>
                    </summary>
                    <p class="text-slate-300 text-sm font-light leading-relaxed px-5 pb-5">{faq_a3}</p>
                </details>
            </div>
        </div>

    </main>

    <!-- FOOTER COM SUPORTE HUMANO DISCRETO -->
    <footer class="border-t border-white/5 py-8 mt-10">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p class="text-slate-600 text-xs mb-4">Datalab Global © Todos os direitos reservados.</p>
            <a href="{LINK_WHATSAPP_SUPORTE}" target="_blank" rel="noopener" class="inline-flex items-center justify-center text-slate-500 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">
                {icone('whatsapp', 'mr-1')} Falar com o suporte
            </a>
        </div>
    </footer>

    <script>
        const REGRA_PRAZO_MAX = {prazo_max_banco};
        const REGRA_PERC_ENTRADA_MIN = {perc_entrada_minima};

        function unformatCurrency(val) {{ return typeof val === 'number' ? val : Number(val.replace(/\\D/g, '')) / 100; }}
        function formatCurrency(val) {{ return (val).toLocaleString('pt-BR', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }}); }}
        function initMask(inputId) {{ const input = document.getElementById(inputId); let rawVal = unformatCurrency(input.value); if(rawVal > 0) input.value = formatCurrency(rawVal); input.addEventListener('input', function(e) {{ let raw = unformatCurrency(e.target.value); e.target.value = formatCurrency(raw); }}); }}

        function syncSliderInput(sliderId, inputId) {{
            const slider = document.getElementById(sliderId);
            const input = document.getElementById(inputId);
            slider.addEventListener('input', function() {{ input.value = formatCurrency(Number(this.value)); calcularTudo(); }});
            input.addEventListener('blur', function() {{ let val = unformatCurrency(this.value); slider.value = val; calcularTudo(); }});
        }}

        function calcularTudo() {{
            const vImovel = unformatCurrency(document.getElementById('input_imovel').value);
            let entrada = unformatCurrency(document.getElementById('input_entrada').value);

            // TRAVA 1: ENTRADA NÃO PODE SER MENOR QUE O MÍNIMO E NÃO PODE PASSAR DE 80% DO IMÓVEL
            const entradaMinimaReal = vImovel * REGRA_PERC_ENTRADA_MIN;
            const entradaMaximaReal = vImovel * 0.80; // Regra de Sanidade de Mercado (80% máx de entrada)

            if (entrada < entradaMinimaReal) {{
                entrada = entradaMinimaReal;
                document.getElementById('input_entrada').value = formatCurrency(entrada);
            }} else if (entrada > entradaMaximaReal) {{
                entrada = entradaMaximaReal;
                document.getElementById('input_entrada').value = formatCurrency(entrada);
            }}

            document.getElementById('slider_entrada').min = entradaMinimaReal;
            document.getElementById('slider_entrada').max = entradaMaximaReal;
            document.getElementById('slider_entrada').value = entrada;

            const taxaAnualRaw = document.getElementById('input_taxa').value.toString().replace(',', '.');
            const taxaAnual = parseFloat(taxaAnualRaw) || 0;
            const taxa = (taxaAnual / 100) / 12;

            let prazoOrig = parseInt(document.getElementById('input_prazo').value) || 0;
            if (prazoOrig > REGRA_PRAZO_MAX) {{
                prazoOrig = REGRA_PRAZO_MAX;
                document.getElementById('input_prazo').value = prazoOrig;
            }}

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
            let aporteUnico = unformatCurrency(document.getElementById('input_amortizar').value);
            let amortizacaoMaxima = vFinanciado;
            if (amortizacaoMaxima < 0) amortizacaoMaxima = 0;

            if (aporteUnico > amortizacaoMaxima) {{
                aporteUnico = amortizacaoMaxima;
                document.getElementById('input_amortizar').value = formatCurrency(aporteUnico);
            }}
            document.getElementById('slider_amortizar').max = amortizacaoMaxima;
            document.getElementById('slider_amortizar').value = aporteUnico;

            if (vFinanciado <= 0 || prazoOrig <= 0) return;

            let saldoTrad = vFinanciado; let jurosTotalTrad = 0; let p1Trad = 0; let pUTrad = 0; let pmtPriceTrad = 0;

            // CÁLCULO TRADICIONAL
            if (sistema === 'PRICE') {{
                if (taxa > 0) {{ pmtPriceTrad = vFinanciado * (taxa * Math.pow(1 + taxa, prazoOrig)) / (Math.pow(1 + taxa, prazoOrig) - 1);
                }} else {{ pmtPriceTrad = vFinanciado / prazoOrig; }}
            }}

            for (let m = 1; m <= prazoOrig; m++) {{
                let juros = saldoTrad * taxa; jurosTotalTrad += juros;
                let amortizacaoBase = (sistema === 'SAC') ? (vFinanciado / prazoOrig) : (pmtPriceTrad - juros);
                let parcelaMensal = amortizacaoBase + juros;
                if (m === 1) p1Trad = parcelaMensal;
                if (m === prazoOrig) pUTrad = parcelaMensal;
                saldoTrad -= amortizacaoBase;
            }}

            let saldoNovo = vFinanciado; let jurosTotalNovo = 0; let mesesNovo = 0;
            saldoNovo -= aporteUnico;

            if (saldoNovo > 0) {{
                while (saldoNovo > 0 && mesesNovo < prazoOrig) {{
                    let juros = saldoNovo * taxa; jurosTotalNovo += juros;
                    let amortizacaoBase = (sistema === 'SAC') ? (vFinanciado / prazoOrig) : (pmtPriceTrad - juros);

                    let abatimentoTotal = amortizacaoBase;
                    if (abatimentoTotal > saldoNovo) abatimentoTotal = saldoNovo;
                    saldoNovo -= abatimentoTotal; mesesNovo++;
                }}
            }} else {{ mesesNovo = 0; jurosTotalNovo = 0; }}

            const economiaJuros = jurosTotalTrad - jurosTotalNovo;
            const mesesEliminados = Math.max(0, prazoOrig - mesesNovo);
            const totalDesembolsado = vFinanciado + jurosTotalTrad;
            const cfg = {{style:'currency',currency:'BRL'}};
            document.getElementById('res_p1').innerText = p1Trad.toLocaleString('pt-BR', cfg);
            document.getElementById('res_pU').innerText = pUTrad.toLocaleString('pt-BR', cfg);
            document.getElementById('res_capital').innerText = vFinanciado.toLocaleString('pt-BR', cfg);
            document.getElementById('res_total_pago').innerText = totalDesembolsado.toLocaleString('pt-BR', cfg);
            document.getElementById('res_economia').innerText = economiaJuros.toLocaleString('pt-BR', cfg);

            let anos = Math.floor(mesesEliminados / 12); let meses = mesesEliminados % 12; let textoTempo = "";
            if (anos > 0) textoTempo += anos + (anos === 1 ? " Ano" : " Anos");
            if (anos > 0 && meses > 0) textoTempo += " e ";
            if (meses > 0 || (anos === 0 && meses === 0)) textoTempo += meses + (meses === 1 ? " Mês" : " Meses");
            if (textoTempo === "") textoTempo = "0 Meses";
            document.getElementById('res_impacto').innerText = textoTempo;
            let pctNovoPrazo = (mesesNovo / prazoOrig) * 100;
            document.getElementById('bar_novo_prazo').style.width = pctNovoPrazo + '%';
        }}

        window.onload = function() {{
            initMask('input_imovel'); initMask('input_entrada'); initMask('input_amortizar');
            syncSliderInput('slider_imovel', 'input_imovel'); syncSliderInput('slider_entrada', 'input_entrada'); syncSliderInput('slider_amortizar', 'input_amortizar');
            document.getElementById('input_prazo').addEventListener('input', calcularTudo);
            document.getElementById('input_taxa').addEventListener('input', calcularTudo);
            document.querySelectorAll('input[name="sistema"]').forEach(r => r.addEventListener('change', calcularTudo));
            document.getElementById('slider_imovel').value = {valor_imovel};
            document.getElementById('input_imovel').value = formatCurrency({valor_imovel});
            calcularTudo();
        }};
    </script>
</body>
</html>'''
            caminho_arquivo = os.path.join(pasta_saida, f"{slug}.html")
            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                f.write(html_content)
            urls_sitemap.append(url_canonica)

    gerar_index_home(pasta_saida, links_por_banco, data_ultima_atualizacao)
    gerar_sitemap(urls_sitemap, pasta_saida, dominio, data_ultima_atualizacao)
    gerar_robots_txt(pasta_saida, dominio)
    gerar_logo_svg(pasta_saida)
    gerar_llms_txt(pasta_saida, dominio, len(urls_sitemap), data_ultima_atualizacao)
    print(f"✅ {len(urls_sitemap)} páginas geradas em '{pasta_saida}/'.")


def gerar_index_home(pasta_saida, links_por_banco, data_ultima_atualizacao):
    blocos_html = ""
    for banco, links in links_por_banco.items():
        regra = obter_regra(banco)
        banco_exib = nome_exibicao(banco)
        url_logo = f"https://www.google.com/s2/favicons?domain={regra['dominio_favicon']}&sz=128"
        ancora_id = banco.lower().replace(" ", "-")
        links_html = "".join([f'''
            <li>
                <a href="{item["slug"]}.html" class="group flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-colors border border-transparent hover:border-white/10">
                    <span class="text-xs font-light text-slate-300 group-hover:text-white">{item["texto"]}</span>
                    <svg class="w-3 h-3 text-emerald-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                </a>
            </li>
        ''' for item in links])

        blocos_html += f'''
        <div id="{ancora_id}" class="bg-slate-900/40 backdrop-blur-md rounded-2xl shadow-2xl border border-white/5 overflow-hidden transition-all duration-300 hover:border-emerald-500/30 hover:shadow-[0_0_30px_rgba(16,185,129,0.1)] scroll-mt-24">
            <div class="border-b border-white/5 px-6 py-5 flex items-center gap-4 bg-black/40">
                {favicon_com_fallback(url_logo, banco_exib)}
                <h2 class="text-xl font-serif text-white tracking-wide">{banco_exib}</h2>
            </div>
            <div class="p-4">
                <ul class="space-y-1 h-64 overflow-y-auto pr-2 custom-scrollbar">
                    {links_html}
                </ul>
            </div>
        </div>
        '''

    url_home = f"{DOMINIO}/index.html"
    descricao_home = "A ferramenta definitiva para simular seu financiamento imobiliário em meses ou anos e descobrir quanto economizar antecipando parcelas, com taxas reais de mais de 15 instituições financeiras."

    schema_website = f'''{{
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "Datalab Global",
      "url": "{url_home}",
      "dateModified": "{data_ultima_atualizacao}"
    }}'''

    html_home = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulador de Financiamento e Amortização (Meses ou Anos) | Datalab Global</title>
    <meta name="description" content="{descricao_home}">
    <link rel="canonical" href="{url_home}" />

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

    <meta property="og:type" content="website">
    <meta property="og:locale" content="pt_BR">
    <meta property="og:site_name" content="Datalab Global">
    <meta property="og:title" content="Simulador de Financiamento e Amortização | Datalab Global">
    <meta property="og:description" content="{descricao_home}">
    <meta property="og:url" content="{url_home}">
    <meta property="og:image" content="{DOMINIO}/logo.svg">
    <meta name="twitter:card" content="summary">

    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5414184968223405" crossorigin="anonymous"></script>

    <link rel="stylesheet" href="styles.css">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <script type="application/ld+json">
    {schema_website}
    </script>
</head>
<body class="antialiased min-h-screen flex flex-col">
    <nav class="border-b border-white/5 sticky top-0 z-50 backdrop-blur-2xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="index.html" class="flex items-center">
                    <img src="logo.svg" alt="Datalab Global" class="h-12 md:h-16 w-auto drop-shadow-[0_0_15px_rgba(16,185,129,0.2)] hover:scale-105 transition-transform duration-300">
                </a>
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
    </div>
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-32 relative z-10 w-full">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {blocos_html}
        </div>
    </main>
</body>
</html>'''
    with open(os.path.join(pasta_saida, 'index.html'), "w", encoding="utf-8") as f:
        f.write(html_home)


def gerar_sitemap(urls, pasta_saida, dominio, data_ultima_atualizacao):
    # lastmod = data REAL da última mudança de taxa (não a data do deploy).
    # Ver obter_data_ultima_atualizacao(): "lastmod sempre = hoje" é tratado
    # pelo Google como sinal de frescor falso.
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml_content += f"  <url>\n    <loc>{dominio}/index.html</loc>\n    <lastmod>{data_ultima_atualizacao}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>\n"
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
    conteudo = f"""# Datalab Global

> Hub financeiro com simuladores de financiamento imobiliário para mais de 15 instituições brasileiras (Caixa, Banco do Brasil, Itaú, Bradesco, Santander, Banco Inter, Sicredi, Sicoob, Banrisul, BRB, Poupex, C6 Bank, Bari, Cash Me, Daycoval). Calcula parcelas nos sistemas SAC e PRICE, e simula a economia de juros ao antecipar amortizações.

Dados atualizados em: {data_ultima_atualizacao}
Total de páginas de simulação: {total_paginas}

## Páginas
- [Home / lista de bancos]({dominio}/index.html)
- [Sitemap completo]({dominio}/sitemap.xml)

## Sobre os dados
Taxas de juros, LTV (percentual mínimo de entrada) e prazo máximo são específicos de cada instituição financeira e atualizados mensalmente. Cada página de simulador (padrão de URL: /simulador-{{banco}}-{{valor}}-mil-{{prazo}}-meses.html) traz cálculo de parcelas, custo total e comparativo real entre os sistemas SAC e PRICE para o cenário daquele banco/valor/prazo específico.
"""
    with open(os.path.join(pasta_saida, 'llms.txt'), "w", encoding="utf-8") as f:
        f.write(conteudo)


if __name__ == "__main__":
    gerar_paginas_pseo()
