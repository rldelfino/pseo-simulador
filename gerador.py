import os
import csv

def criar_csv_exemplo(caminho_csv):
    cabecalho = ['banco', 'valor_imovel', 'taxa', 'prazo', 'slug']
    dados = [
        ['Caixa', '300000', '0.80', '360', 'simulador-caixa-300-mil-360-meses'],
        ['Itau', '500000', '0.85', '360', 'simulador-itau-500-mil-360-meses']
    ]
    with open(caminho_csv, mode='w', newline='', encoding='utf-8') as arquivo:
        writer = csv.writer(arquivo, delimiter=';')
        writer.writerow(cabecalho)
        writer.writerows(dados)

def gerar_paginas_pseo():
    caminho_csv = 'dados.csv'
    pasta_saida = 'paginas_seo'
    dominio = 'https://datalabglobal.com' 
    
    os.makedirs(pasta_saida, exist_ok=True)
    if not os.path.exists(caminho_csv):
        criar_csv_exemplo(caminho_csv)

    urls_sitemap = []
    links_por_banco = {}

    with open(caminho_csv, mode='r', encoding='utf-8') as arquivo:
        leitor_csv = csv.DictReader(arquivo, delimiter=';')
        
        paginas_geradas = 0
        for linha in leitor_csv:
            banco = linha['banco']
            valor_imovel = float(linha['valor_imovel'])
            taxa = float(linha['taxa'])
            prazo = int(linha['prazo'])
            slug = linha['slug']
            
            valor_amigavel = f"R$ {valor_imovel:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            entrada_padrao = valor_imovel * 0.20 
            
            if banco not in links_por_banco:
                links_por_banco[banco] = []
            links_por_banco[banco].append({
                "slug": slug,
                "texto": f"Simular {valor_amigavel} em {prazo} meses"
            })

            html_content = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulador de Financiamento | {banco} | Simulador Datalab</title>
    <meta name="description" content="Simule seu financiamento imobiliário pela {banco}. Planeje o futuro e descubra quanto economiza adiantando parcelas.">
    <link rel="canonical" href="{dominio}/{slug}.html" />
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ 
            font-family: 'Inter', sans-serif; 
            background: #020617;
            background-image: radial-gradient(at 80% 0%, #1e293b 0px, transparent 50%), radial-gradient(at 0% 100%, #0f172a 0px, transparent 50%);
            color: #f8fafc;
            min-height: 100vh;
            overflow-x: hidden;
        }}
        
        h1, h2, .font-serif {{ font-family: 'Playfair Display', serif; }}
        
        /* Glass Panels */
        .glass-panel {{
            background: rgba(15, 23, 42, 0.4);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }}
        
        .glass-panel-emerald {{
            background: rgba(4, 47, 46, 0.4);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(16, 185, 129, 0.2);
            box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(16, 185, 129, 0.2);
        }}

        .text-gold {{
            background: linear-gradient(135deg, #fef08a 0%, #d97706 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        /* Machined Aluminum Knobs */
        input[type=range] {{
            -webkit-appearance: none; appearance: none; width: 100%; height: 6px; 
            background: rgba(255,255,255,0.05); border-radius: 9999px; outline: none;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
        }}
        input[type=range]::-webkit-slider-thumb {{
            -webkit-appearance: none; appearance: none; width: 26px; height: 26px; border-radius: 50%; 
            background: radial-gradient(circle at 50% 0%, #cbd5e1, #64748b);
            cursor: pointer; 
            box-shadow: 0 5px 10px rgba(0,0,0,0.5), inset 0 2px 2px rgba(255,255,255,0.9), inset 0 -2px 5px rgba(0,0,0,0.3);
            border: 1px solid #334155; transition: transform 0.1s ease;
        }}
        input[type=range]::-webkit-slider-thumb:active {{ transform: scale(0.95); }}
        
        /* Elegant Radios */
        input[type="radio"]:checked + div {{ background: linear-gradient(145deg, #10b981, #047857); color: white; border-color: transparent; box-shadow: 0 0 20px rgba(16,185,129,0.2); }}
        input[type="radio"]:not(:checked) + div {{ background-color: transparent; color: #64748b; border-color: transparent; }}
        input[type="radio"]:not(:checked) + div:hover {{ color: white; }}
        
        .currency-input {{ font-variant-numeric: tabular-nums; }}
        
        /* Emerald Particles */
        .particle {{
            position: fixed; width: 4px; height: 4px; background-color: #10b981; border-radius: 50%;
            box-shadow: 0 0 10px #10b981, 0 0 20px #34d399; pointer-events: none; z-index: 9999;
            animation: floatParticle 1s ease-out forwards;
        }}
        @keyframes floatParticle {{
            0% {{ transform: translate(0, 0) scale(1); opacity: 1; }}
            100% {{ transform: translate(var(--tx), var(--ty)) scale(0); opacity: 0; }}
        }}

        /* Aura Glow */
        .aura-glow {{ position: relative; }}
        .aura-glow::before {{
            content: ''; position: absolute; top: -1px; left: -1px; right: -1px; bottom: -1px;
            background: linear-gradient(45deg, rgba(16,185,129,0.1), rgba(16,185,129,0.5), rgba(16,185,129,0.1));
            z-index: -1; border-radius: inherit; filter: blur(10px); opacity: 0; transition: opacity 0.5s ease;
        }}
        .aura-active::before {{ opacity: 1; }}
    </style>
</head>
<body class="antialiased flex flex-col">
    <!-- Navbar Premium -->
    <nav class="border-b border-white/5 sticky top-0 z-50 backdrop-blur-2xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="index.html" class="flex items-center space-x-3">
                    <div class="w-10 h-10 rounded-full flex items-center justify-center border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.2)] text-emerald-500">
                        <i class="fa-solid fa-calculator"></i>
                    </div>
                    <span class="font-serif text-2xl tracking-wide text-white">Simulador <span class="text-emerald-400">Datalab</span></span>
                </a>
                <div class="hidden md:flex items-center space-x-3">
                    <a id="btn_wa_nav" href="#" target="_blank" class="bg-white hover:bg-slate-200 text-slate-900 px-6 py-2.5 rounded-full font-bold transition-all text-sm flex items-center shadow-lg">
                        <i class="fa-brands fa-whatsapp mr-2 text-lg text-emerald-500"></i> Falar com Especialista
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <header class="py-12 md:py-16 relative z-10 text-center">
        <h1 class="text-4xl md:text-5xl font-serif text-white mb-4 leading-tight">
            Simulador de Financiamento
        </h1>
        <p class="text-slate-400 text-base md:text-lg font-light tracking-wide max-w-3xl mx-auto">
            Ajuste os valores para o banco <strong class="text-white font-medium">{banco}</strong> e descubra quanto você economiza ao fazer amortizações.
        </p>
    </header>

    <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex-grow w-full relative z-10 space-y-8">
        
        <!-- ZONA A: O FINANCIAMENTO (A DÍVIDA) -->
        <div class="glass-panel p-8 md:p-10 rounded-3xl">
            <h2 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-8 border-b border-white/10 pb-4 flex items-center">
                <i class="fa-solid fa-file-invoice-dollar mr-3"></i> 1. Estratégia de Financiamento (Cenário Base)
            </h2>
            
            <div class="flex flex-col lg:flex-row gap-10">
                <!-- Inputs Frios -->
                <div class="w-full lg:w-1/2 space-y-6">
                    <div>
                        <div class="flex justify-between items-end mb-2">
                            <label class="text-[10px] font-semibold text-slate-400 uppercase tracking-widest">Total Financiado</label>
                            <input type="text" id="input_imovel" class="currency-input w-40 text-right bg-transparent font-medium text-white text-2xl outline-none border-b border-white/20 focus:border-emerald-500 transition-colors" value="">
                        </div>
                        <input type="range" id="slider_imovel" min="100000" max="2000000" step="10000" value="{valor_imovel}" class="w-full mt-2">
                    </div>

                    <div>
                        <div class="flex justify-between items-end mb-2">
                            <label class="text-[10px] font-semibold text-slate-400 uppercase tracking-widest">Entrada do Financiamento</label>
                            <input type="text" id="input_entrada" class="currency-input w-40 text-right bg-transparent font-medium text-white text-2xl outline-none border-b border-white/20 focus:border-emerald-500 transition-colors" value="">
                        </div>
                        <input type="range" id="slider_entrada" min="0" max="1000000" step="5000" value="{int(entrada_padrao)}" class="w-full mt-2">
                    </div>

                    <div class="grid grid-cols-2 gap-6">
                        <div>
                            <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 block">Prazo</label>
                            <div class="flex items-center border-b border-white/10 pb-1">
                                <input type="number" id="input_prazo" class="w-full bg-transparent font-medium text-white text-lg outline-none" value="{prazo}">
                                <span class="text-xs text-slate-500 ml-2">meses</span>
                            </div>
                        </div>
                        <div>
                            <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 block">Taxa Estimada</label>
                            <div class="flex items-center border-b border-white/10 pb-1">
                                <input type="number" id="input_taxa" step="0.01" class="w-full bg-transparent font-medium text-white text-lg outline-none" value="{taxa}">
                                <span class="text-xs text-slate-500 ml-2">% a.m.</span>
                            </div>
                        </div>
                    </div>
                    
                    <div>
                        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 block">Sistema de Amortização</label>
                        <div class="flex bg-black/40 p-1 rounded-xl border border-white/5">
                            <label class="flex-1 text-center relative cursor-pointer">
                                <input type="radio" name="sistema" value="SAC" class="peer sr-only" checked>
                                <div class="py-2 rounded-lg text-xs font-bold transition-all border border-transparent tracking-widest">SAC</div>
                            </label>
                            <label class="flex-1 text-center relative cursor-pointer">
                                <input type="radio" name="sistema" value="PRICE" class="peer sr-only">
                                <div class="py-2 rounded-lg text-xs font-bold transition-all border border-transparent tracking-widest">PRICE</div>
                            </label>
                        </div>
                    </div>
                </div>

                <!-- Outputs Analíticos da Dívida -->
                <div class="w-full lg:w-1/2 bg-black/20 rounded-2xl p-8 border border-white/5 flex flex-col justify-center space-y-8">
                    <div class="grid grid-cols-2 gap-6">
                        <div>
                            <p class="text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-2">Primeira Parcela</p>
                            <p class="text-white text-3xl font-light tracking-tight" id="res_p1">R$ 0,00</p>
                        </div>
                        <div>
                            <p class="text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-2">Última Parcela</p>
                            <p class="text-slate-300 text-2xl font-light tracking-tight mt-1" id="res_pU">R$ 0,00</p>
                        </div>
                    </div>
                    
                    <div class="pt-6 border-t border-white/5 grid grid-cols-1 gap-6">
                        <div>
                            <p class="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-1.5">Total da Dívida (Sem Juros)</p>
                            <p class="text-white font-medium text-lg" id="res_capital">R$ 0,00</p>
                        </div>
                        <div>
                            <p class="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-1.5 flex items-center">
                                Custo Total Final (Capital + Juros) <i class="fa-solid fa-triangle-exclamation text-amber-500/50 ml-2"></i>
                            </p>
                            <p class="text-white font-medium text-xl" id="res_total_pago">R$ 0,00</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ZONA B: A AMORTIZAÇÃO (O REMÉDIO) -->
        <div class="glass-panel-emerald rounded-3xl p-8 md:p-10 aura-glow relative overflow-hidden" id="card_amortizacao">
            <div class="absolute right-0 top-0 w-64 h-64 bg-emerald-500/20 rounded-full blur-[80px] pointer-events-none"></div>
            
            <h2 class="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-8 border-b border-emerald-500/20 pb-4 relative z-10 flex items-center">
                <i class="fa-solid fa-bolt mr-3"></i> 2. Valor a Amortizar (A Solução)
            </h2>
            
            <div class="flex flex-col lg:flex-row gap-10 relative z-10">
                <!-- Input de Ação -->
                <div class="w-full lg:w-1/2 flex flex-col justify-center">
                    <label class="text-[10px] font-bold text-slate-300 uppercase tracking-widest block mb-4">
                        Amortização Extra Mensal
                    </label>
                    <div class="relative mb-6">
                        <span class="absolute left-4 top-1/2 -translate-y-1/2 font-light text-emerald-500/50 text-3xl">R$</span>
                        <input type="text" id="input_amortizar" class="currency-input w-full bg-black/50 border border-emerald-500/30 rounded-2xl pl-16 pr-4 py-5 focus:border-emerald-400 font-medium text-emerald-400 text-4xl outline-none transition-all shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)]" value="1.000,00">
                    </div>
                    <input type="range" id="slider_amortizar" min="0" max="20000" step="100" value="1000" class="w-full">
                    <p class="text-[10px] text-slate-500 mt-4 text-center tracking-wide">Deslize para ver o impacto no seu futuro</p>
                </div>

                <!-- Outputs de Ganho (Aura) -->
                <div class="w-full lg:w-1/2 bg-black/40 border border-emerald-500/30 rounded-2xl p-8 backdrop-blur-sm shadow-[inset_0_0_20px_rgba(16,185,129,0.1)] text-center flex flex-col justify-center">
                    <div class="mb-8">
                        <p class="text-emerald-500/80 text-[10px] font-bold uppercase tracking-widest mb-3">Economia Total de Juros</p>
                        <p class="text-5xl md:text-6xl font-serif text-emerald-400 drop-shadow-[0_0_15px_rgba(16,185,129,0.3)]" id="res_economia">R$ 0,00</p>
                    </div>

                    <div>
                        <p class="text-emerald-500 text-[10px] font-bold uppercase tracking-widest mb-2">Tempo de Financiamento Reduzido Em</p>
                        <p class="text-3xl md:text-4xl font-light text-white tracking-tight" id="res_impacto">0 Anos e 0 Meses</p>
                        
                        <!-- Mini Timeline Visual -->
                        <div class="mt-5 w-full h-2 bg-slate-800 rounded-full relative overflow-hidden">
                            <div class="absolute left-0 top-0 h-full bg-slate-600 w-full"></div>
                            <div id="bar_novo_prazo" class="absolute left-0 top-0 h-full bg-emerald-500 transition-all duration-700" style="width: 100%;"></div>
                        </div>
                        <div class="flex justify-between mt-2 text-[9px] font-bold text-slate-500 uppercase tracking-widest">
                            <span>Hoje</span>
                            <span class="text-emerald-500" id="label_novo_prazo">Novo Fim</span>
                            <span>Fim Original</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- CTA Final -->
        <div class="text-center pt-4">
            <a id="btn_wa_cta" href="#" target="_blank" class="inline-flex items-center justify-center bg-white text-slate-900 hover:bg-slate-200 font-bold px-10 py-5 rounded-2xl transition-all shadow-[0_10px_30px_rgba(255,255,255,0.1)] text-sm tracking-wide w-full md:w-auto">
                Solicitar Análise Gratuita no WhatsApp <i class="fa-solid fa-arrow-right ml-3"></i>
            </a>
        </div>
    </main>

    <script>
        const bancoNome = "{banco}";
        const SEU_WHATSAPP = "5527995051571";
        
        function unformatCurrency(val) {{
            if (typeof val === 'number') return val;
            return Number(val.replace(/\D/g, '')) / 100;
        }}

        function formatCurrency(val) {{
            return (val).toLocaleString('pt-BR', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
        }}

        function initMask(inputId) {{
            const input = document.getElementById(inputId);
            let rawVal = unformatCurrency(input.value);
            if(rawVal > 0) input.value = formatCurrency(rawVal);
            input.addEventListener('input', function(e) {{
                let raw = unformatCurrency(e.target.value);
                e.target.value = formatCurrency(raw);
            }});
        }}

        // Particle Effect Engine
        function spawnParticle() {{
            const btn = document.getElementById('slider_amortizar');
            const rect = btn.getBoundingClientRect();
            
            const p = document.createElement('div');
            p.className = 'particle';
            
            const startX = rect.left + (rect.width * (btn.value / btn.max));
            const startY = rect.top + (rect.height / 2);
            p.style.left = startX + 'px';
            p.style.top = startY + 'px';
            
            const tx = (Math.random() * 200) + 100 + 'px';
            const ty = (Math.random() * -100) - 50 + 'px';
            p.style.setProperty('--tx', tx);
            p.style.setProperty('--ty', ty);
            
            document.body.appendChild(p);
            setTimeout(() => p.remove(), 1000);
        }}

        function syncSliderInput(sliderId, inputId) {{
            const slider = document.getElementById(sliderId);
            const input = document.getElementById(inputId);

            slider.addEventListener('input', function() {{
                input.value = formatCurrency(Number(this.value));
                if(sliderId === 'slider_amortizar') spawnParticle();
                calcularTudo();
            }});

            input.addEventListener('blur', function() {{
                let val = unformatCurrency(this.value);
                slider.value = val;
                calcularTudo();
            }});
        }}

        function atualizarLinksWhatsapp(vImovel, entrada, valorAmortizarMensal, economiaJuros, anosLivre) {{
            const textoNav = `Olá! Gostaria de tirar dúvidas sobre financiamento de imóveis pela ${{bancoNome}}.`;
            const textoCta = `Olá! Fiz uma simulação no Simulador Datalab e gostaria de uma análise:\n\n` +
                `• Banco: ${{bancoNome}}\n` +
                `• Total Financiado: R$ ${{formatCurrency(vImovel)}}\n` +
                `• Entrada: R$ ${{formatCurrency(entrada)}}\n` +
                `• Amortização Extra: R$ ${{formatCurrency(valorAmortizarMensal)}}/mês\n` +
                `• Economia Gerada: R$ ${{formatCurrency(economiaJuros)}}\n` +
                `• Tempo Reduzido: ${{anosLivre}}\n\n` +
                `Podemos conversar?`;

            document.getElementById('btn_wa_nav').href = `https://wa.me/${{SEU_WHATSAPP}}?text=${{encodeURIComponent(textoNav)}}`;
            document.getElementById('btn_wa_cta').href = `https://wa.me/${{SEU_WHATSAPP}}?text=${{encodeURIComponent(textoCta)}}`;
        }}

        function calcularTudo() {{
            const vImovel = unformatCurrency(document.getElementById('input_imovel').value);
            const entrada = unformatCurrency(document.getElementById('input_entrada').value);
            const taxa = (parseFloat(document.getElementById('input_taxa').value) || 0) / 100;
            const prazoOrig = parseInt(document.getElementById('input_prazo').value) || 0;
            const sistema = document.querySelector('input[name="sistema"]:checked').value;
            
            const aporteMensal = unformatCurrency(document.getElementById('input_amortizar').value);
            
            // Total financiado (Matematicamente)
            const vFinanciado = vImovel - entrada;
            
            if (vFinanciado <= 0 || prazoOrig <= 0) return;

            // CENÁRIO 1: FINANCIAMENTO NORMAL
            let saldoTrad = vFinanciado;
            let jurosTotalTrad = 0;
            let p1Trad = 0;
            let pUTrad = 0;
            let pmtPriceTrad = 0;

            if (sistema === 'PRICE') {{
                pmtPriceTrad = vFinanciado * (taxa * Math.pow(1 + taxa, prazoOrig)) / (Math.pow(1 + taxa, prazoOrig) - 1);
            }}

            for (let m = 1; m <= prazoOrig; m++) {{
                let juros = saldoTrad * taxa;
                jurosTotalTrad += juros;
                
                let amortizacaoBase = (sistema === 'SAC') ? (vFinanciado / prazoOrig) : (pmtPriceTrad - juros);
                let parcelaMensal = amortizacaoBase + juros;
                
                if (m === 1) p1Trad = parcelaMensal;
                if (m === prazoOrig) pUTrad = parcelaMensal;
                
                saldoTrad -= amortizacaoBase;
            }}

            // CENÁRIO 2: COM AMORTIZAÇÃO EXTRA MENSAL
            let saldoNovo = vFinanciado;
            let jurosTotalNovo = 0;
            let mesesNovo = 0;

            while (saldoNovo > 0 && mesesNovo < prazoOrig) {{
                let juros = saldoNovo * taxa;
                jurosTotalNovo += juros;
                
                let amortizacaoBase = 0;
                if (sistema === 'SAC') {{
                    amortizacaoBase = vFinanciado / prazoOrig;
                }} else {{
                    amortizacaoBase = pmtPriceTrad - juros;
                }}

                let abatimentoTotal = amortizacaoBase + aporteMensal;
                if (abatimentoTotal > saldoNovo) abatimentoTotal = saldoNovo;

                saldoNovo -= abatimentoTotal;
                mesesNovo++;
            }}

            // RESULTADOS FINAIS
            const economiaJuros = jurosTotalTrad - jurosTotalNovo;
            const mesesEliminados = Math.max(0, prazoOrig - mesesNovo);
            const totalDesembolsado = vFinanciado + jurosTotalTrad; 

            const cfg = {{style:'currency',currency:'BRL'}};
            document.getElementById('res_p1').innerText = p1Trad.toLocaleString('pt-BR', cfg);
            document.getElementById('res_pU').innerText = pUTrad.toLocaleString('pt-BR', cfg);
            document.getElementById('res_capital').innerText = vFinanciado.toLocaleString('pt-BR', cfg);
            document.getElementById('res_total_pago').innerText = totalDesembolsado.toLocaleString('pt-BR', cfg);
            document.getElementById('res_economia').innerText = economiaJuros.toLocaleString('pt-BR', cfg);

            let anos = Math.floor(mesesEliminados / 12);
            let meses = mesesEliminados % 12;
            let textoTempo = "";
            if (anos > 0) textoTempo += anos + (anos === 1 ? " Ano" : " Anos");
            if (anos > 0 && meses > 0) textoTempo += " e ";
            if (meses > 0 || (anos === 0 && meses === 0)) textoTempo += meses + (meses === 1 ? " Mês" : " Meses");
            if (textoTempo === "") textoTempo = "0 Meses";
            
            document.getElementById('res_impacto').innerText = textoTempo;

            // Barra de Tempo
            let pctNovoPrazo = (mesesNovo / prazoOrig) * 100;
            document.getElementById('bar_novo_prazo').style.width = pctNovoPrazo + '%';

            // Ativa o Glow
            const cardAmortizacao = document.getElementById('card_amortizacao');
            if (economiaJuros > 0) {{
                cardAmortizacao.classList.add('aura-active');
            }} else {{
                cardAmortizacao.classList.remove('aura-active');
            }}

            atualizarLinksWhatsapp(vImovel, entrada, aporteMensal, economiaJuros, textoTempo);
        }}

        window.onload = function() {{
            initMask('input_imovel');
            initMask('input_entrada');
            initMask('input_amortizar');
            
            syncSliderInput('slider_imovel', 'input_imovel');
            syncSliderInput('slider_entrada', 'input_entrada');
            syncSliderInput('slider_amortizar', 'input_amortizar');

            document.getElementById('input_prazo').addEventListener('input', calcularTudo);
            document.getElementById('input_taxa').addEventListener('input', calcularTudo);
            document.querySelectorAll('input[name="sistema"]').forEach(r => r.addEventListener('change', calcularTudo));

            document.getElementById('slider_imovel').value = {valor_imovel};
            document.getElementById('input_imovel').value = formatCurrency({valor_imovel});
            document.getElementById('slider_entrada').value = {int(entrada_padrao)};
            document.getElementById('input_entrada').value = formatCurrency({int(entrada_padrao)});
            
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

def gerar_index_home(pasta_saida, links_por_banco):
    dominios_bancos = {
        "Caixa": "caixa.gov.br", "Banco do Brasil": "bb.com.br", "Itau": "itau.com.br",
        "Bradesco": "bradesco.com.br", "Santander": "santander.com.br", "Banco Inter": "bancointer.com.br",
        "Banrisul": "banrisul.com.br", "BRB": "brb.com.br", "Sicredi": "sicredi.com.br",
        "Sicoob": "sicoob.com.br", "C6 Bank": "c6bank.com.br", "Poupex": "poupex.com.br"
    }

    blocos_html = ""
    for banco, links in links_por_banco.items():
        dominio_banco = dominios_bancos.get(banco, "google.com")
        url_logo = f"https://www.google.com/s2/favicons?domain={dominio_banco}&sz=128"

        links_html = "".join([f'''
            <li>
                <a href="{item["slug"]}.html" class="group flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-colors border border-transparent hover:border-white/10">
                    <span class="text-xs font-light text-slate-300 group-hover:text-white">
                        {item["texto"]}
                    </span>
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
    <title>Simulador de Financiamento | Simulador Datalab</title>
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
<body class="antialiased min-h-screen">
    <nav class="border-b border-white/5 sticky top-0 z-50 backdrop-blur-2xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="index.html" class="flex items-center space-x-3">
                    <div class="w-10 h-10 rounded-full flex items-center justify-center border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.2)] text-emerald-500">
                        <i class="fa-solid fa-calculator"></i>
                    </div>
                    <span class="font-serif text-2xl tracking-wide text-white">Simulador <span class="text-emerald-400">Datalab</span></span>
                </a>
            </div>
        </div>
    </nav>
    <div class="py-24 md:py-32 text-center px-4 relative overflow-hidden">
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-emerald-500/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>
        <h1 class="text-4xl md:text-6xl font-serif text-white mb-6 leading-tight max-w-4xl mx-auto">
            Simulador de Financiamento
        </h1>
        <p class="text-slate-400 text-lg md:text-xl font-light tracking-wide max-w-2xl mx-auto">
            Selecione a instituição financeira abaixo e descubra quanto você economiza ao fazer amortizações.
        </p>
    </div>
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-32 relative z-10">
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

if __name__ == "__main__":
    gerar_paginas_pseo()