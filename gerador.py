import os
import csv
import random

# --- MOTOR DE REGRAS GLOBAL DA PLATAFORMA ---
REGRAS_BANCOS = {
    "Caixa": {"ltv": 0.80, "prazo_max": 420, "mod": "Financiamento Imobiliário", "taxa_padrao": 11.49},
    "Banco do Brasil": {"ltv": 0.80, "prazo_max": 420, "mod": "Financiamento Imobiliário", "taxa_padrao": 11.69},
    "Santander": {"ltv": 0.80, "prazo_max": 420, "mod": "Financiamento Imobiliário", "taxa_padrao": 13.39},
    "BRB": {"ltv": 0.80, "prazo_max": 420, "mod": "Financiamento Imobiliário", "taxa_padrao": 11.25},
    "Poupex": {"ltv": 0.90, "prazo_max": 420, "mod": "Financiamento Imobiliário", "taxa_padrao": 10.80},
    "Itau": {"ltv": 0.80, "prazo_max": 360, "mod": "Financiamento Imobiliário", "taxa_padrao": 13.09},
    "Itaú": {"ltv": 0.80, "prazo_max": 360, "mod": "Financiamento Imobiliário", "taxa_padrao": 13.09},
    "Bradesco": {"ltv": 0.80, "prazo_max": 360, "mod": "Financiamento Imobiliário", "taxa_padrao": 13.50},
    "Banco Inter": {"ltv": 0.80, "prazo_max": 360, "mod": "Financiamento Imobiliário", "taxa_padrao": 9.50},
    "Sicredi": {"ltv": 0.80, "prazo_max": 360, "mod": "Financiamento Imobiliário", "taxa_padrao": 11.50},
    "Sicoob": {"ltv": 0.80, "prazo_max": 360, "mod": "Financiamento Imobiliário", "taxa_padrao": 11.50},
    "Banrisul": {"ltv": 0.75, "prazo_max": 360, "mod": "Financiamento Imobiliário", "taxa_padrao": 11.60},
    "C6 Bank": {"ltv": 0.60, "prazo_max": 240, "mod": "Crédito com Garantia de Imóvel", "taxa_padrao": 13.50},
    "Bari": {"ltv": 0.60, "prazo_max": 360, "mod": "Crédito com Garantia de Imóvel", "taxa_padrao": 15.25},
    "Cash Me": {"ltv": 0.60, "prazo_max": 360, "mod": "Crédito com Garantia de Imóvel", "taxa_padrao": 16.63},
    "Daycoval": {"ltv": 0.60, "prazo_max": 360, "mod": "Crédito com Garantia de Imóvel", "taxa_padrao": 16.63}
}

LINK_FINANCIA_TUDO = "https://app.financiatudo.com.br/financiamento-de-imoveis/chave/8940d282b765cbf97b6df55fd1eb0b52b18b2f6e"

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

def gerar_paginas_pseo():
    caminho_csv = 'dados.csv'
    pasta_saida = 'paginas_seo'
    dominio = 'https://datalabglobal.com' 
    
    os.makedirs(pasta_saida, exist_ok=True)
    if not os.path.exists(caminho_csv):
        criar_csv_exemplo(caminho_csv)

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
            
            regra = REGRAS_BANCOS.get(banco, {"ltv": 0.80, "prazo_max": 360, "mod": "Financiamento Imobiliário", "taxa_padrao": 11.99})
            prazo_correto = min(prazo_csv, regra["prazo_max"])
            
            if prazo_correto != prazo_csv:
                slug = slug_original.replace(f"-{prazo_csv}-meses", f"-{prazo_correto}-meses")
            else:
                slug = slug_original
                
            valor_amigavel = f"R$ {valor_imovel:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            anos_equivalentes = prazo_correto // 12
            
            pagina_info = {
                "banco": banco,
                "slug": slug,
                "prazo_correto": prazo_correto,
                "anos_equivalentes": anos_equivalentes,
                "regra": regra,
                "texto": f"Simular {valor_amigavel} em {prazo_correto} meses ({anos_equivalentes} anos)",
                "linha_original": linha
            }
            todas_as_paginas.append(pagina_info)
            
            if banco not in links_por_banco:
                links_por_banco[banco] = []
            links_por_banco[banco].append(pagina_info)

        termos_variados = [
            "Calculadora de financiamento", "Simulador de crédito", "Simulação de amortização",
            "Calcular taxas de juros", "Simulador imobiliário", "Comparador de empréstimo"
        ]

        for p in todas_as_paginas:
            linha = p["linha_original"]
            banco = p['banco']
            valor_imovel = float(linha['valor_imovel'])
            prazo = p['prazo_correto'] 
            anos = p['anos_equivalentes']
            slug = p['slug']
            regra = p['regra']
            
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

            # LÓGICA DE CLUSTERIZAÇÃO SEO: Prioriza links do mesmo banco
            paginas_candidatas = [pag for pag in todas_as_paginas if pag["slug"] != slug and pag['banco'] == banco]
            # Se não tiver 4 paginas do mesmo banco, pega aleatorias para completar
            if len(paginas_candidatas) < 4:
                outras_paginas = [pag for pag in todas_as_paginas if pag["slug"] != slug and pag['banco'] != banco]
                paginas_candidatas.extend(random.sample(outras_paginas, min(4 - len(paginas_candidatas), len(outras_paginas))))
            
            paginas_sorteadas = random.sample(paginas_candidatas, min(4, len(paginas_candidatas)))
            
            links_internos_html = ""
            for pag_sorteada in paginas_sorteadas:
                termo = random.choice(termos_variados)
                links_internos_html += f"""
                <a href="{pag_sorteada['slug']}.html" class="block p-4 bg-white/5 rounded-xl border border-white/10 hover:border-emerald-500/50 hover:bg-white/10 transition-all">
                    <span class="text-xs text-emerald-500 font-bold uppercase tracking-wider block mb-1">{termo}</span>
                    <span class="text-sm text-slate-300 group-hover:text-white block">{pag_sorteada['banco']} - {pag_sorteada['texto'].replace('Simular ', '')}</span>
                </a>
                """
            
            faq_q1 = f"Vale a pena amortizar o {regra['mod'].lower()} no {banco}?"
            faq_a1 = f"Sim! Ao fazer amortizações extras no {banco}, você reduz diretamente o saldo devedor. Isso significa que você foge dos juros compostos cobrados ao longo dos {prazo} meses ({anos} anos), podendo economizar milhares de reais e quitar muito antes do previsto."
            faq_q2 = f"Qual a diferença entre a Tabela SAC e PRICE na simulação do {banco}?"
            faq_a2 = f"Na Tabela SAC, a amortização é constante e o valor das parcelas do {banco} diminui com o tempo. Já na Tabela PRICE, as parcelas são fixas do início ao fim do contrato. A escolha ideal depende do seu planejamento financeiro mensal."
            faq_q3 = f"É possível simular o crédito com a taxa atual de {taxa}% a.a.?"
            faq_a3 = f"Nossa calculadora já utiliza a taxa de juros anual estimada em {taxa}% ao ano para o {banco}. Você pode ajustar os valores de entrada (margem de garantia) e prazo no simulador acima para ver o Custo Efetivo Total (CET) aproximado para o seu perfil e solicitar uma análise."

            html_content = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calculadora e Simulador de {regra['mod']} | {banco} | {prazo} meses ({anos} anos)</title>
    <meta name="description" content="Simule seu {regra['mod'].lower()} pela {banco} em até {prazo} meses (ou {anos} anos). Calcule juros, saldo devedor, amortização e empréstimo com a taxa de {taxa}% ao ano.">
    <meta name="keywords" content="simulador de financiamento, calculadora de amortização, empréstimo imobiliário, calcular juros {banco}, amortizar financiamento {banco}, {prazo} meses, {anos} anos, Custo Efetivo Total, TR, Saldo Devedor">
    <link rel="canonical" href="{dominio}/{slug}.html" />
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5414184968223405" crossorigin="anonymous"></script>

    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {{ "@type": "Question", "name": "{faq_q1}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_a1}" }} }},
        {{ "@type": "Question", "name": "{faq_q2}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_a2}" }} }},
        {{ "@type": "Question", "name": "{faq_q3}", "acceptedAnswer": {{ "@type": "Answer", "text": "{faq_a3}" }} }}
      ]
    }}
    </script>
    
    <style>
        body {{ font-family: 'Inter', sans-serif; background: #020617; background-image: radial-gradient(at 80% 0%, #1e293b 0px, transparent 50%), radial-gradient(at 0% 100%, #0f172a 0px, transparent 50%); color: #f8fafc; min-height: 100vh; overflow-x: hidden; }}
        h1, h2, h3, .font-serif {{ font-family: 'Playfair Display', serif; }}
        .glass-panel {{ background: rgba(15, 23, 42, 0.4); backdrop-filter: blur(25px); border: 1px solid rgba(255, 255, 255, 0.05); box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.8); }}
        .glass-panel-emerald {{ background: rgba(4, 47, 46, 0.4); backdrop-filter: blur(25px); border: 1px solid rgba(16, 185, 129, 0.2); box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.8); }}
        input[type=range] {{ -webkit-appearance: none; appearance: none; width: 100%; height: 6px; background: rgba(255,255,255,0.05); border-radius: 9999px; outline: none; }}
        input[type=range]::-webkit-slider-thumb {{ -webkit-appearance: none; appearance: none; width: 26px; height: 26px; border-radius: 50%; background: radial-gradient(circle at 50% 0%, #cbd5e1, #64748b); cursor: pointer; border: 1px solid #334155; }}
        input[type="radio"]:checked + div {{ background: linear-gradient(145deg, #10b981, #047857); color: white; }}
        input[type="radio"]:not(:checked) + div {{ background-color: transparent; color: #64748b; }}
        .currency-input {{ font-variant-numeric: tabular-nums; text-shadow: 0 0 10px rgba(255,255,255,0.2); }}
    </style>
</head>
<body class="antialiased flex flex-col">
    <nav class="border-b border-white/5 sticky top-0 z-50 backdrop-blur-2xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="index.html" class="flex items-center">
                    <img src="logo.svg" alt="Datalab Global" class="h-12 md:h-16 w-auto drop-shadow-[0_0_15px_rgba(16,185,129,0.2)] hover:scale-105 transition-transform duration-300">
                </a>
                <div class="hidden md:flex items-center space-x-3">
                    <a href="{LINK_FINANCIA_TUDO}" target="_blank" class="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-6 py-2.5 rounded-full font-bold transition-all text-sm flex items-center shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                        Fazer Análise Grátis <i class="fa-solid fa-arrow-right ml-2 text-sm"></i>
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <header class="py-12 md:py-16 relative z-10 text-center">
        <h1 class="text-4xl md:text-5xl font-serif text-white mb-4 leading-tight">Simulador de {regra['mod']}</h1>
        <p class="text-slate-400 text-base md:text-lg font-light tracking-wide max-w-3xl mx-auto px-4">
            Ajuste os valores para o banco <strong class="text-white font-medium">{banco}</strong> e descubra quanto você economiza adiantando parcelas do seu crédito de <span id="label_anos" class="font-medium text-white">{anos} anos</span>.
        </p>
    </header>

    <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex-grow w-full relative z-10 space-y-8">

        <!-- ZONA A: O FINANCIAMENTO -->
        <div class="glass-panel p-8 md:p-10 rounded-3xl border-t border-slate-700/50">
            <h2 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-8 border-b border-white/10 pb-4 flex items-center">
                <i class="fa-solid fa-file-invoice-dollar mr-3"></i> 1. Estratégia
            </h2>
            <div class="flex flex-col lg:flex-row gap-10">
                <div class="w-full lg:w-1/2 space-y-4">
                    <div class="bg-slate-900/40 p-4 rounded-2xl border border-white/5">
                        <div class="flex justify-between items-end mb-2">
                            <label class="text-[10px] font-semibold text-slate-400 uppercase tracking-widest">Valor do Imóvel / Garantia</label>
                            <input type="text" id="input_imovel" class="currency-input w-40 text-right bg-transparent font-medium text-white text-2xl outline-none border-b border-transparent focus:border-emerald-500 transition-colors" value="">
                        </div>
                        <input type="range" id="slider_imovel" min="100000" max="2000000" step="10000" value="{valor_imovel}" class="w-full mt-2">
                    </div>
                    <div class="bg-slate-900/40 p-4 rounded-2xl border border-white/5">
                        <div class="flex justify-between items-end mb-2">
                            <label class="text-[10px] font-semibold text-slate-400 uppercase tracking-widest">Entrada / Margem Retida</label>
                            <input type="text" id="input_entrada" class="currency-input w-40 text-right bg-transparent font-medium text-white text-2xl outline-none border-b border-transparent focus:border-emerald-500 transition-colors" value="">
                        </div>
                        <input type="range" id="slider_entrada" min="{int(entrada_minima_valor)}" max="1000000" step="5000" value="{int(entrada_padrao)}" class="w-full mt-2">
                        <p class="text-[9px] text-slate-500 mt-1 text-right">Mínimo exigido: {(perc_entrada_minima*100):.0f}% do valor</p>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-slate-900/40 p-4 rounded-2xl border border-white/5">
                            <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 block">Prazo</label>
                            <div class="flex items-center"><input type="number" id="input_prazo" min="12" max="{prazo_max_banco}" class="w-full bg-transparent font-medium text-white text-lg outline-none" value="{prazo}"><span class="text-xs text-slate-500 ml-2">meses</span></div>
                            <p class="text-[9px] text-slate-500 mt-1">Equivale a <span id="hint_anos">{anos}</span> anos</p>
                        </div>
                        <div class="bg-slate-900/40 p-4 rounded-2xl border border-white/5">
                            <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 block">Taxa Estimada</label>
                            <div class="flex items-center"><input type="number" id="input_taxa" step="0.01" class="w-full bg-transparent font-medium text-white text-lg outline-none" value="{taxa}"><span class="text-xs text-slate-500 ml-2">% a.a.</span></div>
                        </div>
                    </div>
                    <div class="pt-2">
                        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 block pl-2">Sistema de Amortização</label>
                        <div class="flex bg-black/40 p-1 rounded-xl border border-white/5">
                            <label class="flex-1 text-center relative cursor-pointer"><input type="radio" name="sistema" value="SAC" class="peer sr-only" checked><div class="py-2.5 rounded-lg text-xs font-bold transition-all border border-transparent tracking-widest">SAC</div></label>
                            <label class="flex-1 text-center relative cursor-pointer"><input type="radio" name="sistema" value="PRICE" class="peer sr-only"><div class="py-2.5 rounded-lg text-xs font-bold transition-all border border-transparent tracking-widest">PRICE</div></label>
                        </div>
                    </div>
                </div>
                <div class="w-full lg:w-1/2 bg-slate-950 rounded-2xl p-8 border border-white/5 shadow-inner flex flex-col justify-center space-y-8 relative overflow-hidden">
                    <div class="absolute top-0 right-0 w-32 h-32 bg-slate-800 rounded-full blur-[50px] opacity-50"></div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 relative z-10">
                        <div><p class="text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-2">Primeira Parcela</p><p class="text-white text-3xl font-light tracking-tight currency-input" id="res_p1">R$ 0,00</p></div>
                        <div><p class="text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-2">Última Parcela</p><p class="text-slate-300 text-2xl font-light tracking-tight mt-1 currency-input" id="res_pU">R$ 0,00</p></div>
                    </div>
                    <div class="pt-6 border-t border-white/5 grid grid-cols-1 gap-6 relative z-10">
                        <div><p class="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-1.5">Crédito Liberado (Sem Juros)</p><p class="text-white font-medium text-lg currency-input" id="res_capital">R$ 0,00</p></div>
                        <div><p class="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-1.5 flex items-center">Custo Total Final (Capital + Juros)</p><p class="text-white font-medium text-xl currency-input" id="res_total_pago">R$ 0,00</p></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ZONA B: A AMORTIZAÇÃO -->
        <div class="glass-panel-emerald rounded-3xl p-8 md:p-10 relative overflow-hidden shadow-[0_10px_40px_rgba(16,185,129,0.1)] border-t border-emerald-500/30" id="card_amortizacao">
            <h2 class="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-8 border-b border-emerald-500/20 pb-4 relative z-10 flex items-center">
                <i class="fa-solid fa-bolt mr-3"></i> 2. Valor a Amortizar (A Solução)
            </h2>
            <div class="flex flex-col lg:flex-row gap-10 relative z-10">
                <div class="w-full lg:w-1/2 flex flex-col justify-center">
                    <label class="text-[10px] font-bold text-slate-300 uppercase tracking-widest block mb-4">Amortização Extra (Pagamento Único)</label>
                    <div class="relative mb-6">
                        <span class="absolute left-4 top-1/2 -translate-y-1/2 font-light text-emerald-500/50 text-3xl">R$</span>
                        <input type="text" id="input_amortizar" class="currency-input w-full bg-black/50 border border-emerald-500/30 rounded-2xl pl-16 pr-4 py-5 focus:border-emerald-400 font-medium text-emerald-400 text-4xl outline-none transition-all shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)]" value="20.000,00">
                    </div>
                    <input type="range" id="slider_amortizar" min="0" max="500000" step="5000" value="20000" class="w-full">
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

        <!-- BANNER DE CONVERSÃO FINANCIA TUDO (SUA NOVA ISCA DE VENDAS) -->
        <div class="mt-12 bg-gradient-to-r from-emerald-600 to-emerald-900 rounded-3xl p-8 md:p-12 relative overflow-hidden shadow-[0_20px_50px_rgba(16,185,129,0.3)] border border-emerald-400/50">
            <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-[80px]"></div>
            <div class="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10">
                <div class="md:w-2/3 text-left">
                    <div class="flex items-center gap-3 mb-4">
                        <span class="bg-yellow-400 text-yellow-950 text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest">Parceria Oficial</span>
                        <span class="flex items-center text-emerald-200 text-xs font-medium"><i class="fa-solid fa-shield-halved mr-1"></i> 100% Seguro</span>
                    </div>
                    <h3 class="text-3xl font-serif text-white mb-3">Aprove o seu crédito no {banco} sem sair de casa.</h3>
                    <p class="text-emerald-100 text-sm md:text-base font-light leading-relaxed">
                        Como parceiros credenciados, conectamos você diretamente à mesa de crédito para buscar as <strong>melhores taxas e condições de aprovação</strong>. Análise gratuita, rápida e sem compromisso.
                    </p>
                </div>
                <div class="md:w-1/3 w-full flex justify-center md:justify-end">
                    <a href="{LINK_FINANCIA_TUDO}" target="_blank" class="group relative inline-flex items-center justify-center bg-white text-emerald-900 hover:bg-slate-100 font-black px-8 py-5 rounded-2xl transition-all shadow-2xl text-sm tracking-widest uppercase w-full text-center overflow-hidden">
                        <span class="relative z-10 flex items-center">Fazer Análise Grátis <i class="fa-solid fa-arrow-up-right-from-square ml-3 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform"></i></span>
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
                <a href="https://go.hotmart.com/S107394856P" target="_blank" class="inline-flex items-center justify-center bg-white text-slate-950 hover:bg-slate-200 font-bold px-8 py-4 rounded-xl transition-all shadow-[0_0_20px_rgba(255,255,255,0.1)] text-sm tracking-wide w-full md:w-auto">
                    Quero Baixar a Planilha <i class="fa-solid fa-download ml-3"></i>
                </a>
            </div>
            
            <div class="md:w-1/3 flex justify-center relative z-10">
                <div class="w-32 h-40 bg-slate-800 rounded-xl border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.5)] flex items-center justify-center rotate-6 hover:rotate-0 transition-transform duration-500 relative">
                    <div class="absolute -top-3 -right-3 bg-emerald-500 text-slate-950 text-[10px] font-bold px-2 py-1 rounded-md shadow-lg">100% OFF</div>
                    <i class="fa-solid fa-file-excel text-6xl text-emerald-500 drop-shadow-[0_0_15px_rgba(16,185,129,0.5)]"></i>
                </div>
            </div>
        </div>

        <!-- ZONA C: LINKAGEM INTERNA -->
        <div class="mt-16 pt-8 border-t border-white/5">
            <h3 class="text-sm font-serif text-slate-400 mb-6 flex items-center justify-center">
                <i class="fa-solid fa-link mr-2 text-emerald-500/50"></i> Veja Outras Simulações
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {links_internos_html}
            </div>
        </div>

        <!-- ZONA D: FAQ VISUAL -->
        <div class="mt-16 mb-8">
            <h3 class="text-2xl font-serif text-white mb-6 text-center">Perguntas Frequentes</h3>
            <div class="space-y-4 max-w-3xl mx-auto">
                <div class="bg-white/5 border border-white/10 p-5 rounded-xl"><h4 class="text-emerald-400 font-bold text-sm mb-2">{faq_q1}</h4><p class="text-slate-300 text-sm font-light leading-relaxed">{faq_a1}</p></div>
                <div class="bg-white/5 border border-white/10 p-5 rounded-xl"><h4 class="text-emerald-400 font-bold text-sm mb-2">{faq_q2}</h4><p class="text-slate-300 text-sm font-light leading-relaxed">{faq_a2}</p></div>
                <div class="bg-white/5 border border-white/10 p-5 rounded-xl"><h4 class="text-emerald-400 font-bold text-sm mb-2">{faq_q3}</h4><p class="text-slate-300 text-sm font-light leading-relaxed">{faq_a3}</p></div>
            </div>
        </div>

    </main>

    <!-- FOOTER COM SUPORTE HUMANO DISCRETO -->
    <footer class="border-t border-white/5 py-8 mt-10">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p class="text-slate-600 text-xs mb-4">Datalab Global © Todos os direitos reservados.</p>
            <a href="https://wa.me/5527995051571?text=Ol%C3%A1%2C%20preciso%20de%20ajuda%20com%20o%20simulador" target="_blank" class="inline-flex items-center justify-center text-slate-500 hover:text-emerald-500 text-[10px] tracking-widest uppercase transition-colors">
                <i class="fa-brands fa-whatsapp mr-1"></i> Falar com o suporte
            </a>
        </div>
    </footer>

    <script>
        const REGRA_PRAZO_MAX = {prazo_max_banco};
        const REGRA_PERC_ENTRADA_MIN = {perc_entrada_minima};
        
        function unformatCurrency(val) {{ return typeof val === 'number' ? val : Number(val.replace(/\D/g, '')) / 100; }}
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
            
            // TRAVA 1: ENTRADA NÃO PODE SER MENOR QUE O MÍNIMO NEM MAIOR QUE O IMÓVEL
            const entradaMinimaReal = vImovel * REGRA_PERC_ENTRADA_MIN;
            if (entrada < entradaMinimaReal) {{
                entrada = entradaMinimaReal;
                document.getElementById('input_entrada').value = formatCurrency(entrada);
            }}
            if (entrada >= vImovel) {{
                // Se o cara tentar dar 100% de entrada, a gente limita a 99% pra não quebrar a matemática do financiamento
                entrada = vImovel * 0.99;
                document.getElementById('input_entrada').value = formatCurrency(entrada);
            }}
            
            document.getElementById('slider_entrada').min = entradaMinimaReal;
            document.getElementById('slider_entrada').max = vImovel * 0.99;
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
            
            // TRAVA 2: AMORTIZAÇÃO NÃO PODE SER MAIOR QUE O CRÉDITO LIBERADO
            let aporteUnico = unformatCurrency(document.getElementById('input_amortizar').value);
            if (aporteUnico > vFinanciado) {{
                aporteUnico = vFinanciado;
                document.getElementById('input_amortizar').value = formatCurrency(aporteUnico);
            }}
            document.getElementById('slider_amortizar').max = vFinanciado;
            document.getElementById('slider_amortizar').value = aporteUnico;

            if (vFinanciado <= 0 || prazoOrig <= 0) return;

            let saldoTrad = vFinanciado; let jurosTotalTrad = 0; let p1Trad = 0; let pUTrad = 0; let pmtPriceTrad = 0;
            
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
            urls_sitemap.append(f"{dominio}/{slug}.html")
            paginas_geradas += 1

    gerar_index_home(pasta_saida, links_por_banco)
    gerar_sitemap(urls_sitemap, pasta_saida)
    gerar_robots_txt(pasta_saida, dominio)
    gerar_logo_svg(pasta_saida)

def gerar_index_home(pasta_saida, links_por_banco):
    dominios_bancos = {
        "Caixa": "caixa.gov.br", "Banco do Brasil": "bb.com.br", "Itau": "itau.com.br",
        "Bradesco": "bradesco.com.br", "Santander": "santander.com.br", "Banco Inter": "bancointer.com.br",
        "Banrisul": "banrisul.com.br", "BRB": "brb.com.br", "Sicredi": "sicredi.com.br",
        "Sicoob": "sicoob.com.br", "C6 Bank": "c6bank.com.br", "Poupex": "poupex.com.br",
        "Bari": "bancobari.com.br", "Cash Me": "cashme.com.br", "Daycoval": "daycoval.com.br"
    }
    blocos_html = ""
    for banco, links in links_por_banco.items():
        dominio_banco = dominios_bancos.get(banco, "google.com")
        url_logo = f"https://www.google.com/s2/favicons?domain={dominio_banco}&sz=128"
        links_html = "".join([f'''
            <li>
                <a href="{item["slug"]}.html" class="group flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-colors border border-transparent hover:border-white/10">
                    <span class="text-xs font-light text-slate-300 group-hover:text-white">{item["texto"]}</span>
                    <svg class="w-3 h-3 text-emerald-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                </a>
            </li>
        ''' for item in links])
        
        blocos_html += f'''
        <div class="bg-slate-900/40 backdrop-blur-md rounded-2xl shadow-2xl border border-white/5 overflow-hidden transition-all duration-300 hover:border-emerald-500/30 hover:shadow-[0_0_30px_rgba(16,185,129,0.1)]">
            <div class="border-b border-white/5 px-6 py-5 flex items-center gap-4 bg-black/40">
                <img src="{url_logo}" alt="Logo {banco}" class="w-7 h-7 rounded object-contain">
                <h2 class="text-xl font-serif text-white tracking-wide">{banco}</h2>
            </div>
            <div class="p-4">
                <ul class="space-y-1 h-64 overflow-y-auto pr-2 custom-scrollbar">
                    {links_html}
                </ul>
            </div>
        </div>
        '''

    html_home = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulador de Financiamento e Amortização | Datalab Global</title>
    <meta name="description" content="A ferramenta definitiva para simular seu financiamento imobiliário e descobrir quanto economizar antecipando parcelas.">
    
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5414184968223405" crossorigin="anonymous"></script>

    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; background: #020617; background-image: radial-gradient(at 80% 0%, #1e293b 0px, transparent 50%), radial-gradient(at 0% 100%, #0f172a 0px, transparent 50%); color: #f8fafc; }}
        h1, h2, .font-serif {{ font-family: 'Playfair Display', serif; }}
        .text-gold {{ background: linear-gradient(135deg, #fef08a 0%, #d97706 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .custom-scrollbar::-webkit-scrollbar {{ width: 4px; }}
        .custom-scrollbar::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.05); border-radius: 4px; }}
        .custom-scrollbar::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.2); border-radius: 4px; }}
    </style>
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
            Simulador de Financiamento
        </h1>
        <p class="text-slate-400 text-lg md:text-xl font-light tracking-wide max-w-2xl mx-auto">
            Selecione a instituição financeira abaixo e descubra quanto você economiza ao fazer amortizações.
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

def gerar_sitemap(urls, pasta_saida):
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml_content += f"  <url>\n    <loc>{url}</loc>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>\n"
    xml_content += '</urlset>'
    with open(os.path.join(pasta_saida, 'sitemap.xml'), "w", encoding="utf-8") as f:
        f.write(xml_content)

def gerar_robots_txt(pasta_saida, dominio):
    conteudo = f"User-agent: *\nAllow: /\n\nSitemap: {dominio}/sitemap.xml\n"
    with open(os.path.join(pasta_saida, 'robots.txt'), "w", encoding="utf-8") as f:
        f.write(conteudo)

if __name__ == "__main__":
    gerar_paginas_pseo()