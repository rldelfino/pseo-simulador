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
                "texto": f"Imóvel de {valor_amigavel} em {prazo} meses"
            })

            html_content = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simule Financiamento e Amortização | {banco} | Simulador Datalab</title>
    <meta name="description" content="Simule seu financiamento pela {banco}. Planeje o futuro e descubra o impacto da amortização.">
    <link rel="canonical" href="{dominio}/{slug}.html" />
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ 
            font-family: 'Inter', sans-serif; 
            background: #0f172a;
            color: #f8fafc;
            min-height: 100vh;
        }}
        
        .glass-panel {{
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
        }}

        input[type=range] {{
            -webkit-appearance: none; appearance: none; width: 100%; height: 6px; 
            background: rgba(255,255,255,0.1); border-radius: 9999px; outline: none;
        }}
        input[type=range]::-webkit-slider-thumb {{
            -webkit-appearance: none; appearance: none; width: 22px; height: 22px; border-radius: 50%; 
            background: #10b981;
            cursor: pointer; 
            border: 2px solid #ffffff; transition: transform 0.1s ease;
        }}
        input[type=range]::-webkit-slider-thumb:active {{ transform: scale(0.95); }}
        
        input[type="radio"]:checked + div {{ background: #10b981; color: white; border-color: transparent; }}
        input[type="radio"]:not(:checked) + div {{ background-color: rgba(255,255,255,0.05); color: #94a3b8; border-color: rgba(255,255,255,0.1); }}
        input[type="radio"]:not(:checked) + div:hover {{ background-color: rgba(255,255,255,0.1); color: white; }}
        
        .currency-input {{ font-variant-numeric: tabular-nums; }}
    </style>
</head>
<body class="antialiased flex flex-col">
    <!-- Navbar -->
    <nav class="border-b border-white/10 sticky top-0 z-50 backdrop-blur-xl bg-slate-900/80">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16 items-center">
                <a href="index.html" class="flex items-center space-x-3">
                    <div class="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center text-white font-bold text-sm">
                        <i class="fa-solid fa-calculator"></i>
                    </div>
                    <span class="font-bold text-xl tracking-tight text-white">Simulador <span class="text-emerald-400">Datalab</span></span>
                </a>
                <div class="hidden md:flex items-center space-x-3">
                    <a id="btn_wa_nav" href="#" target="_blank" class="bg-white hover:bg-slate-200 text-slate-900 px-5 py-2 rounded-lg font-bold transition-all text-sm flex items-center">
                        <i class="fa-brands fa-whatsapp mr-2 text-lg text-emerald-500"></i> Falar com Especialista
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <header class="py-12 relative z-10 text-center">
        <h1 class="text-3xl md:text-5xl font-black text-white mb-4 tracking-tight">
            Simulador de Financiamento
        </h1>
        <p class="text-slate-400 text-base md:text-lg max-w-2xl mx-auto">
            Ajuste os valores para o banco <strong class="text-white">{banco}</strong> e descubra quanto você economiza ao fazer amortizações.
        </p>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex-grow w-full relative z-10">
        <div class="flex flex-col lg:flex-row gap-8 items-start">
            
            <!-- PAINEL ESQUERDO: CONTROLES -->
            <div class="w-full lg:w-5/12 space-y-6">
                
                <!-- Bloco 1: Financiamento -->
                <div class="glass-panel p-6 md:p-8 rounded-2xl space-y-6">
                    <div class="flex justify-between items-center border-b border-white/10 pb-4">
                        <span class="text-sm font-bold text-slate-300 uppercase tracking-wider">Estratégia de Financiamento</span>
                    </div>

                    <div>
                        <div class="flex justify-between items-end mb-2">
                            <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Valor do Imóvel</label>
                            <input type="text" id="input_imovel" class="currency-input w-40 text-right bg-transparent font-bold text-white text-xl outline-none border-b border-white/20 focus:border-emerald-500 transition-colors" value="">
                        </div>
                        <input type="range" id="slider_imovel" min="100000" max="2000000" step="10000" value="{valor_imovel}" class="w-full mt-2">
                    </div>

                    <div>
                        <div class="flex justify-between items-end mb-2">
                            <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Entrada do Financiamento</label>
                            <input type="text" id="input_entrada" class="currency-input w-40 text-right bg-transparent font-bold text-white text-xl outline-none border-b border-white/20 focus:border-emerald-500 transition-colors" value="">
                        </div>
                        <input type="range" id="slider_entrada" min="0" max="1000000" step="5000" value="{int(entrada_padrao)}" class="w-full mt-2">
                    </div>

                    <div class="grid grid-cols-2 gap-6">
                        <div>
                            <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1 block">Prazo</label>
                            <div class="flex items-center border-b border-white/20 pb-1">
                                <input type="number" id="input_prazo" class="w-full bg-transparent font-bold text-white text-lg outline-none" value="{prazo}">
                                <span class="text-xs text-slate-500 ml-2">meses</span>
                            </div>
                        </div>
                        <div>
                            <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1 block">Taxa Estimada</label>
                            <div class="flex items-center border-b border-white/20 pb-1">
                                <input type="number" id="input_taxa" step="0.01" class="w-full bg-transparent font-bold text-white text-lg outline-none" value="{taxa}">
                                <span class="text-xs text-slate-500 ml-2">% a.m.</span>
                            </div>
                        </div>
                    </div>
                    
                    <div>
                        <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 block">Sistema de Amortização</label>
                        <div class="flex bg-slate-900/50 p-1 rounded-lg border border-white/10">
                            <label class="flex-1 text-center relative cursor-pointer">
                                <input type="radio" name="sistema" value="SAC" class="peer sr-only" checked>
                                <div class="py-2 rounded-md text-sm font-bold transition-all">SAC</div>
                            </label>
                            <label class="flex-1 text-center relative cursor-pointer">
                                <input type="radio" name="sistema" value="PRICE" class="peer sr-only">
                                <div class="py-2 rounded-md text-sm font-bold transition-all">PRICE</div>
                            </label>
                        </div>
                    </div>
                </div>

                <!-- Bloco 2: Amortização -->
                <div class="glass-panel p-6 md:p-8 rounded-2xl space-y-6 border-emerald-500/30 bg-emerald-900/10">
                    <div class="flex justify-between items-center border-b border-emerald-500/20 pb-4">
                        <span class="text-sm font-bold text-emerald-400 uppercase tracking-wider">Valor a Amortizar</span>
                    </div>

                    <div>
                        <label class="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-3">Amortização Extra Mensal</label>
                        <div class="relative mb-4">
                            <span class="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-emerald-500/50 text-xl">R$</span>
                            <input type="text" id="input_amortizar" class="currency-input w-full bg-slate-900/80 border border-emerald-500/30 rounded-xl pl-12 pr-4 py-3 focus:border-emerald-400 font-bold text-emerald-400 text-2xl outline-none transition-all" value="1.000,00">
                        </div>
                        <input type="range" id="slider_amortizar" min="0" max="20000" step="100" value="1000" class="w-full">
                    </div>
                </div>
            </div>

            <!-- PAINEL DIREITO: RESULTADOS CLAROS -->
            <div class="w-full lg:w-7/12 space-y-6">
                
                <!-- Card 1: Financiamento -->
                <div class="glass-panel rounded-2xl p-6 md:p-8">
                    <h2 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-6 border-b border-white/10 pb-3">
                        Números do Financiamento
                    </h2>
                    
                    <div class="grid grid-cols-2 gap-6 mb-6">
                        <div>
                            <p class="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">Primeira Parcela</p>
                            <p class="text-white text-3xl font-bold tracking-tight" id="res_p1">R$ 0,00</p>
                        </div>
                        <div>
                            <p class="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">Última Parcela</p>
                            <p class="text-slate-300 text-2xl font-semibold tracking-tight mt-1" id="res_pU">R$ 0,00</p>
                        </div>
                    </div>
                    
                    <div class="bg-slate-800/50 rounded-xl p-4 border border-white/5 grid grid-cols-2 gap-4">
                        <div>
                            <p class="text-slate-500 text-[10px] font-bold uppercase tracking-wider mb-1">Total Financiado (Sem Juros)</p>
                            <p class="text-white font-semibold" id="res_capital">R$ 0,00</p>
                        </div>
                        <div>
                            <p class="text-slate-500 text-[10px] font-bold uppercase tracking-wider mb-1">Custo Total (Capital + Juros)</p>
                            <p class="text-white font-bold" id="res_total_pago">R$ 0,00</p>
                        </div>
                    </div>
                </div>

                <!-- Card 2: Amortização -->
                <div class="bg-emerald-950/40 backdrop-blur-md border border-emerald-500/30 rounded-2xl p-6 md:p-8">
                    <h2 class="text-xs font-bold text-emerald-500 uppercase tracking-widest mb-6 border-b border-emerald-500/20 pb-3">
                        Resultado da Amortização
                    </h2>
                    
                    <div class="text-center mb-8">
                        <p class="text-emerald-500/80 text-xs font-bold uppercase tracking-wider mb-2">Economia Total de Juros</p>
                        <p class="text-5xl md:text-6xl font-black text-emerald-400 tracking-tight" id="res_economia">R$ 0,00</p>
                    </div>

                    <div class="bg-emerald-900/40 rounded-xl p-5 border border-emerald-500/20 text-center">
                        <p class="text-emerald-500 text-[10px] font-bold uppercase tracking-wider mb-1">Tempo de Financiamento Reduzido Em</p>
                        <p class="text-3xl font-bold text-white tracking-tight" id="res_impacto">0 Anos e 0 Meses</p>
                        <p id="retorno_multiplo" class="text-emerald-400 text-xs font-semibold mt-3">Cada R$ 1,00 extra amortizado gera R$ 0,00 de economia.</p>
                    </div>
                </div>

                <!-- CTA -->
                <div class="mt-6">
                    <a id="btn_wa_cta" href="#" target="_blank" class="w-full flex items-center justify-center bg-white hover:bg-slate-200 text-slate-900 font-bold px-6 py-4 rounded-xl transition-all text-base">
                        Solicitar Análise Gratuita no WhatsApp
                    </a>
                </div>

            </div>
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

        function syncSliderInput(sliderId, inputId) {{
            const slider = document.getElementById(sliderId);
            const input = document.getElementById(inputId);

            slider.addEventListener('input', function() {{
                input.value = formatCurrency(Number(this.value));
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
            const textoCta = `Olá! Fiz uma simulação no site e gostaria de uma análise:\n\n` +
                `• Banco: ${{bancoNome}}\n` +
                `• Valor do Imóvel: R$ ${{formatCurrency(vImovel)}}\n` +
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

            const retornoMultiplo = aporteMensal > 0 ? (economiaJuros / (aporteMensal * mesesNovo)).toFixed(2) : "0,00";
            document.getElementById('retorno_multiplo').innerText = `Cada R$ 1,00 extra amortizado gera R$ ${{retornoMultiplo.replace('.', ',')}} de economia.`;

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
        <div class="bg-slate-800/50 rounded-xl shadow-lg border border-slate-700 overflow-hidden transition-all duration-300 hover:border-emerald-500/50">
            <div class="border-b border-slate-700 px-6 py-4 flex items-center gap-4 bg-slate-900/50">
                <img src="{url_logo}" alt="Logo {banco}" class="w-6 h-6 rounded bg-white p-0.5 object-contain">
                <h2 class="text-lg font-bold text-white">{banco}</h2>
            </div>
            <div class="p-3">
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
    <title>Simulador Datalab | Financiamento Imobiliário</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; background: #0f172a; color: #f8fafc; }}
        .custom-scrollbar::-webkit-scrollbar {{ width: 6px; }}
        .custom-scrollbar::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.05); border-radius: 4px; }}
        .custom-scrollbar::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.2); border-radius: 4px; }}
    </style>
</head>
<body class="antialiased min-h-screen">
    <nav class="border-b border-white/10 sticky top-0 z-50 bg-slate-900/80 backdrop-blur-xl">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16 items-center">
                <a href="index.html" class="flex items-center space-x-3">
                    <div class="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center text-white font-bold text-sm">
                        <i class="fa-solid fa-calculator"></i>
                    </div>
                    <span class="font-bold text-xl tracking-tight text-white">Simulador <span class="text-emerald-400">Datalab</span></span>
                </a>
            </div>
        </div>
    </nav>
    <div class="py-20 text-center px-4 relative">
        <h1 class="text-4xl md:text-5xl font-black text-white mb-4">
            Simulador de Financiamento
        </h1>
        <p class="text-slate-400 text-lg max-w-2xl mx-auto">
            Selecione o banco desejado e descubra o impacto real das amortizações no seu financiamento.
        </p>
    </div>
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-32">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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