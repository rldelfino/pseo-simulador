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
                "texto": f"Investimento de {valor_amigavel} em {prazo} meses"
            })

            html_content = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Desbloqueie o Poder do Seu Patrimônio | {banco} | Simulador Datalab</title>
    <meta name="description" content="A arte de financiar com inteligência pela {banco}. Planeje o futuro e descubra quantos anos de vida você recupera.">
    <link rel="canonical" href="{dominio}/{slug}.html" />
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ 
            font-family: 'Inter', sans-serif; 
            background: radial-gradient(circle at top right, #1e293b, #020617);
            color: #f8fafc;
            min-height: 100vh;
        }}
        
        h1, h2, .font-serif {{ font-family: 'Playfair Display', serif; }}
        
        /* Glassmorphism Panels */
        .glass-panel {{
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }}

        /* Gold Text Gradient */
        .text-gold {{
            background: linear-gradient(to right, #fbbf24, #d97706);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        /* Metallic Sliders */
        input[type=range] {{
            -webkit-appearance: none; appearance: none; width: 100%; height: 4px; background: rgba(255,255,255,0.1); border-radius: 9999px; outline: none;
        }}
        input[type=range]::-webkit-slider-thumb {{
            -webkit-appearance: none; appearance: none; width: 24px; height: 24px; border-radius: 50%; 
            background: linear-gradient(145deg, #f1f5f9, #94a3b8);
            cursor: pointer; 
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5), inset 0 2px 4px rgba(255,255,255,0.8); 
            border: 1px solid #475569; transition: transform 0.15s ease;
        }}
        input[type=range]::-webkit-slider-thumb:hover {{ transform: scale(1.1); box-shadow: 0 0 15px rgba(251, 191, 36, 0.4); }}
        
        /* Elegant Radios */
        input[type="radio"]:checked + div {{ background: linear-gradient(145deg, #10b981, #059669); color: white; border-color: transparent; box-shadow: 0 0 15px rgba(16,185,129,0.3); }}
        input[type="radio"]:not(:checked) + div {{ background-color: rgba(255,255,255,0.05); color: #94a3b8; border-color: rgba(255,255,255,0.1); }}
        input[type="radio"]:not(:checked) + div:hover {{ border-color: rgba(255,255,255,0.3); color: white; }}
        
        .currency-input {{ font-variant-numeric: tabular-nums; }}
        
        /* Aura Glow */
        .aura-glow {{ position: relative; }}
        .aura-glow::before {{
            content: ''; position: absolute; top: -2px; left: -2px; right: -2px; bottom: -2px;
            background: linear-gradient(45deg, #fbbf24, #10b981, #fbbf24);
            z-index: -1; border-radius: inherit; filter: blur(12px); opacity: 0.15; transition: opacity 0.5s ease;
        }}
    </style>
</head>
<body class="antialiased flex flex-col">
    <!-- Navbar Premium -->
    <nav class="border-b border-white/10 sticky top-0 z-50 backdrop-blur-xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="index.html" class="flex items-center space-x-3">
                    <div class="w-10 h-10 rounded-full flex items-center justify-center border border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.2)] text-amber-500">
                        <i class="fa-solid fa-gem"></i>
                    </div>
                    <span class="font-serif text-2xl tracking-wide text-white">Simulador <span class="text-gold">Datalab</span></span>
                </a>
                <div class="hidden md:flex items-center space-x-3">
                    <a id="btn_wa_nav" href="#" target="_blank" class="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-900 px-6 py-2.5 rounded-full font-bold transition-all text-sm flex items-center shadow-lg">
                        <i class="fa-brands fa-whatsapp mr-2 text-lg"></i> Agendar Consultoria Privada
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Header Elegante -->
    <header class="py-16 md:py-24 relative overflow-hidden">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
            <h1 class="text-4xl md:text-6xl font-serif text-white mb-6 leading-tight">
                Desbloqueie o Poder do Seu <span class="text-gold">Patrimônio</span>
            </h1>
            <p class="text-slate-400 text-lg md:text-xl font-light tracking-wide">
                A Arte de Financiar com Inteligência. Planeje o futuro, viva o presente.<br>
                Uma estratégia sob medida pela <strong class="text-white font-medium">{banco}</strong>.
            </p>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex-grow w-full">
        <div class="flex flex-col lg:flex-row gap-8 lg:gap-12 items-start">
            
            <!-- PAINEL ESQUERDO: CONTROLES DE PRECISÃO -->
            <div class="w-full lg:w-5/12 space-y-6">
                
                <!-- Bloco 1: Estratégia de Aquisição -->
                <div class="glass-panel p-8 rounded-3xl space-y-8">
                    <div class="flex justify-between items-center border-b border-white/10 pb-4">
                        <span class="text-xs font-bold text-slate-400 uppercase tracking-[0.2em]">Estratégia de Aquisição</span>
                        <i class="fa-solid fa-chess-knight text-amber-500"></i>
                    </div>

                    <div>
                        <div class="flex justify-between items-end mb-2">
                            <label class="text-xs font-semibold text-slate-300 uppercase tracking-widest">Investimento Total do Sonho</label>
                            <input type="text" id="input_imovel" class="currency-input w-40 text-right bg-transparent font-light text-white text-2xl outline-none border-b border-white/20 focus:border-amber-500 transition-colors" value="">
                        </div>
                        <input type="range" id="slider_imovel" min="100000" max="2000000" step="10000" value="{valor_imovel}" class="w-full mt-4">
                    </div>

                    <div>
                        <div class="flex justify-between items-end mb-2">
                            <label class="text-xs font-semibold text-slate-300 uppercase tracking-widest">Sua Entrada Estratégica</label>
                            <input type="text" id="input_entrada" class="currency-input w-40 text-right bg-transparent font-light text-white text-2xl outline-none border-b border-white/20 focus:border-amber-500 transition-colors" value="">
                        </div>
                        <input type="range" id="slider_entrada" min="0" max="1000000" step="5000" value="{int(entrada_padrao)}" class="w-full mt-4">
                    </div>

                    <div class="grid grid-cols-2 gap-6">
                        <div>
                            <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 block">Horizonte de Tempo</label>
                            <div class="flex items-center border-b border-white/20 pb-1">
                                <input type="number" id="input_prazo" class="w-full bg-transparent font-medium text-white text-lg outline-none" value="{prazo}">
                                <span class="text-xs text-slate-500 font-medium ml-2">meses</span>
                            </div>
                        </div>
                        <div>
                            <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 block">Taxa (Custo de Oportunidade)</label>
                            <div class="flex items-center border-b border-white/20 pb-1">
                                <input type="number" id="input_taxa" step="0.01" class="w-full bg-transparent font-medium text-white text-lg outline-none" value="{taxa}">
                                <span class="text-xs text-slate-500 font-medium ml-2">% a.m.</span>
                            </div>
                        </div>
                    </div>

                    <div>
                        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 block">Engenharia Financeira</label>
                        <div class="flex bg-black/20 p-1.5 rounded-xl border border-white/5">
                            <label class="flex-1 text-center relative cursor-pointer">
                                <input type="radio" name="sistema" value="SAC" class="peer sr-only" checked>
                                <div class="py-2.5 rounded-lg text-xs font-bold transition-all border border-transparent tracking-widest">SAC</div>
                            </label>
                            <label class="flex-1 text-center relative cursor-pointer">
                                <input type="radio" name="sistema" value="PRICE" class="peer sr-only">
                                <div class="py-2.5 rounded-lg text-xs font-bold transition-all border border-transparent tracking-widest">PRICE</div>
                            </label>
                        </div>
                    </div>
                </div>

                <!-- Bloco 2: Otimização de Riqueza -->
                <div class="glass-panel p-8 rounded-3xl space-y-8 relative overflow-hidden">
                    <div class="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl"></div>
                    
                    <div class="flex justify-between items-center border-b border-white/10 pb-4 relative z-10">
                        <span class="text-xs font-bold text-emerald-400 uppercase tracking-[0.2em]">Otimização de Riqueza</span>
                        <i class="fa-solid fa-arrow-trend-up text-emerald-400"></i>
                    </div>

                    <div class="relative z-10">
                        <label class="text-[10px] font-bold text-slate-300 uppercase tracking-widest block mb-3">Aporte Extraordinário</label>
                        <div class="relative mb-4">
                            <span class="absolute left-4 top-1/2 -translate-y-1/2 font-light text-slate-400 text-xl">R$</span>
                            <input type="text" id="input_amortizar" class="currency-input w-full bg-black/30 border border-white/10 rounded-2xl pl-12 pr-4 py-4 focus:bg-black/50 focus:border-emerald-500 font-light text-white text-2xl outline-none transition-all shadow-inner" value="10.000,00">
                        </div>
                        <input type="range" id="slider_amortizar" min="1000" max="100000" step="1000" value="10000" class="w-full">
                    </div>

                    <div class="relative z-10">
                        <div class="flex justify-between items-end mb-2">
                            <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Etapa Atual</label>
                            <span class="text-sm font-medium text-white" id="display_pagas">14 / {prazo} meses</span>
                        </div>
                        <input type="range" id="slider_pagas" min="1" max="{prazo-1}" step="1" value="14" class="w-full mt-2">
                    </div>

                    <div class="relative z-10">
                        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 block">Seu Foco Estratégico</label>
                        <div class="flex bg-black/20 p-1.5 rounded-xl border border-white/5">
                            <label class="flex-1 text-center relative cursor-pointer">
                                <input type="radio" name="objetivo" value="prazo" class="peer sr-only" checked>
                                <div class="py-2.5 rounded-lg text-xs font-bold transition-all border border-transparent tracking-widest">Liberdade (Tempo)</div>
                            </label>
                            <label class="flex-1 text-center relative cursor-pointer">
                                <input type="radio" name="objetivo" value="parcela" class="peer sr-only">
                                <div class="py-2.5 rounded-lg text-xs font-bold transition-all border border-transparent tracking-widest">Fluxo (Parcela)</div>
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            <!-- PAINEL DIREITO: NARRATIVA DE RESULTADO -->
            <div class="w-full lg:w-7/12 lg:sticky lg:top-28 space-y-6">
                
                <div class="glass-panel rounded-3xl p-8 lg:p-12 aura-glow relative overflow-hidden">
                    
                    <!-- Seção 1: Cenário Base -->
                    <h2 class="text-xs font-bold text-slate-400 uppercase tracking-[0.2em] mb-8 flex items-center">
                        <span class="w-2 h-2 bg-slate-500 rounded-full mr-3"></span> Cenário Tradicional
                    </h2>
                    
                    <div class="grid grid-cols-2 gap-8 mb-10">
                        <div>
                            <p class="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-2">Esforço Mensal Inicial</p>
                            <p class="text-white text-3xl font-light tracking-tight" id="res_p1_orig">R$ 0,00</p>
                        </div>
                        <div>
                            <p class="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-2">Custo Total em Vida</p>
                            <p class="text-white text-3xl font-light tracking-tight" id="res_total_orig">R$ 0,00</p>
                        </div>
                    </div>

                    <!-- Divisor Luxuoso -->
                    <div class="flex items-center justify-center py-4 my-2">
                        <div class="h-px bg-gradient-to-r from-transparent via-amber-500/50 to-transparent w-full"></div>
                        <div class="absolute bg-slate-900 border border-amber-500/30 px-4 py-1.5 rounded-full text-amber-500 text-[10px] font-bold tracking-widest uppercase shadow-[0_0_10px_rgba(245,158,11,0.2)]">
                            A Mágica da Antecipação
                        </div>
                    </div>

                    <!-- Seção 2: O Triunfo -->
                    <div class="pt-8 text-center relative z-10">
                        <p class="text-[10px] font-bold text-emerald-400 uppercase tracking-[0.3em] mb-4">Sua Economia Total em Vida</p>
                        <p class="text-6xl md:text-7xl font-serif text-emerald-400 mb-6 drop-shadow-[0_0_15px_rgba(16,185,129,0.3)]" id="res_economia">R$ 0,00</p>
                        
                        <!-- A "Esfera de Impacto" de Vida (Convertida para Texto Elegante) -->
                        <div class="inline-block bg-black/40 border border-emerald-500/20 px-8 py-5 rounded-2xl mb-8 backdrop-blur-sm">
                            <p class="text-white text-3xl font-light tracking-tight" id="res_impacto">0 Anos</p>
                            <p class="text-emerald-500/80 text-xs font-bold mt-1 uppercase tracking-widest" id="sub_impacto">De vida recuperados (Sem Dívida)</p>
                        </div>

                        <div class="bg-white/5 border border-white/10 p-5 rounded-xl mx-auto max-w-md">
                            <p id="frase_humana" class="text-sm font-light text-slate-300 leading-relaxed">
                                Acelerando o pagamento, você liberta o seu futuro.
                            </p>
                            <p id="retorno_multiplo" class="text-xs font-semibold text-amber-400 mt-2 tracking-wide">
                                O ROI Invisível: Cada R$ 1,00 aportado retorna R$ 0,00 para você.
                            </p>
                        </div>
                    </div>
                </div>

                <!-- CTA Comercial Elite -->
                <div class="glass-panel border-amber-500/20 rounded-3xl p-8 flex flex-col sm:flex-row items-center justify-between shadow-[0_10px_30px_rgba(245,158,11,0.05)]">
                    <div class="mb-5 sm:mb-0 sm:pr-6 text-center sm:text-left">
                        <h4 class="text-white font-serif text-xl mb-1">Pronto para assumir o controle?</h4>
                        <p class="text-slate-400 text-xs font-light">Solicite um mapa financeiro oficial e confidencial para o seu perfil.</p>
                    </div>
                    <a id="btn_wa_cta" href="#" target="_blank" class="shrink-0 bg-white text-slate-950 hover:bg-slate-200 font-bold px-8 py-4 rounded-xl transition-all shadow-[0_0_20px_rgba(255,255,255,0.1)] text-sm tracking-wide w-full sm:w-auto text-center">
                        Agendar Consultoria <i class="fa-solid fa-arrow-right ml-2"></i>
                    </a>
                </div>
            </div>
        </div>
    </main>

    <script>
        const bancoNome = "{banco}";
        const SEU_WHATSAPP = "5527995051571";
        const totalPrazoContrato = {prazo};

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

        initMask('input_imovel');
        initMask('input_entrada');
        initMask('input_amortizar');

        function syncSliderInput(sliderId, inputId, isCurrency = true) {{
            const slider = document.getElementById(sliderId);
            const input = document.getElementById(inputId);

            slider.addEventListener('input', function() {{
                if(isCurrency) {{
                    input.value = formatCurrency(Number(this.value));
                }} else {{
                    input.value = this.value;
                }}
                if(sliderId === 'slider_pagas') {{
                    document.getElementById('display_pagas').innerText = this.value + " / " + document.getElementById('input_prazo').value + " meses";
                }}
                calcularTudo();
            }});

            input.addEventListener('blur', function() {{
                let val = isCurrency ? unformatCurrency(this.value) : Number(this.value);
                slider.value = val;
                calcularTudo();
            }});
        }}

        syncSliderInput('slider_imovel', 'input_imovel', true);
        syncSliderInput('slider_entrada', 'input_entrada', true);
        syncSliderInput('slider_amortizar', 'input_amortizar', true);

        const sliderPagas = document.getElementById('slider_pagas');
        const displayPagas = document.getElementById('display_pagas');
        sliderPagas.addEventListener('input', function() {{
            displayPagas.innerText = this.value + " / " + document.getElementById('input_prazo').value + " meses";
            calcularTudo();
        }});

        function atualizaMaxPagas() {{
            const prazoAtual = parseInt(document.getElementById('input_prazo').value) || 0;
            const pagas = document.getElementById('slider_pagas');
            pagas.max = Math.max(1, prazoAtual - 1);
            if (parseInt(pagas.value) > parseInt(pagas.max)) {{
                pagas.value = pagas.max;
            }}
            document.getElementById('display_pagas').innerText = pagas.value + " / " + prazoAtual + " meses";
            calcularTudo();
        }}

        document.getElementById('input_prazo').addEventListener('input', atualizaMaxPagas);
        document.getElementById('input_taxa').addEventListener('input', calcularTudo);
        document.querySelectorAll('input[name="sistema"]').forEach(r => r.addEventListener('change', calcularTudo));
        document.querySelectorAll('input[name="objetivo"]').forEach(r => r.addEventListener('change', calcularTudo));

        function atualizarLinksWhatsapp(vImovel, entrada, valorAmortizar, economiaJuros) {{
            const textoNav = `Olá! Gostaria de agendar uma consultoria privada sobre financiamento inteligente pela ${{bancoNome}}.`;

            const textoCta = `Olá! Realizei um planejamento no Simulador Datalab e gostaria de solicitar minha análise oficial:\n\n` +
                `• Banco: ${{bancoNome}}\n` +
                `• Investimento: R$ ${{formatCurrency(vImovel)}}\n` +
                `• Entrada: R$ ${{formatCurrency(entrada)}}\n` +
                `• Aporte Extra: R$ ${{formatCurrency(valorAmortizar)}}\n` +
                `• Economia Gerada: R$ ${{formatCurrency(economiaJuros)}}\n\n` +
                `Podemos agendar um horário?`;

            document.getElementById('btn_wa_nav').href = `https://wa.me/${{SEU_WHATSAPP}}?text=${{encodeURIComponent(textoNav)}}`;
            document.getElementById('btn_wa_cta').href = `https://wa.me/${{SEU_WHATSAPP}}?text=${{encodeURIComponent(textoCta)}}`;
        }}

        function calcularTudo() {{
            const vImovel = unformatCurrency(document.getElementById('input_imovel').value);
            const entrada = unformatCurrency(document.getElementById('input_entrada').value);
            const taxa = (parseFloat(document.getElementById('input_taxa').value) || 0) / 100;
            const prazo = parseInt(document.getElementById('input_prazo').value) || 0;
            const sistema = document.querySelector('input[name="sistema"]:checked').value;
            const parcelasPagas = parseInt(document.getElementById('slider_pagas').value) || 0;
            const valorAmortizar = unformatCurrency(document.getElementById('input_amortizar').value);
            const objetivo = document.querySelector('input[name="objetivo"]:checked').value;

            const vFinanciado = vImovel - entrada;
            if (vFinanciado <= 0 || prazo <= 0) return;

            // 1. CÁLCULO ORIGINAL
            let p1Orig = 0, pUOrig = 0, jurosOrig = 0, amortMensal = 0, pmtOrig = 0;
            
            if (sistema === 'SAC') {{
                amortMensal = vFinanciado / prazo;
                p1Orig = amortMensal + (vFinanciado * taxa);
                pUOrig = amortMensal + (amortMensal * taxa);
                jurosOrig = (((vFinanciado * taxa) + (amortMensal * taxa)) * prazo) / 2;
            }} else {{
                pmtOrig = vFinanciado * (taxa * Math.pow(1 + taxa, prazo)) / (Math.pow(1 + taxa, prazo) - 1);
                p1Orig = pmtOrig;
                pUOrig = pmtOrig;
                jurosOrig = (pmtOrig * prazo) - vFinanciado;
            }}
            
            const totalPagoOrig = vFinanciado + jurosOrig;

            // 2. STATUS ATUAL
            let saldoDevedorAtual = 0;
            if (sistema === 'SAC') {{
                saldoDevedorAtual = Math.max(0, vFinanciado - (parcelasPagas * amortMensal));
            }} else {{
                saldoDevedorAtual = Math.max(0, vFinanciado * Math.pow(1 + taxa, parcelasPagas) - pmtOrig * (Math.pow(1 + taxa, parcelasPagas) - 1) / taxa);
            }}

            let saldoAposAmort = Math.max(0, saldoDevedorAtual - valorAmortizar);
            let parcelasRestantesOrig = Math.max(0, prazo - parcelasPagas);
            
            // 3. CÁLCULO DA AMORTIZAÇÃO
            let economiaJuros = 0;
            let parcelasEliminadas = 0;

            if (valorAmortizar > 0 && parcelasRestantesOrig > 0 && saldoAposAmort > 0) {{
                if (objetivo === 'prazo') {{
                    if (sistema === 'SAC') {{
                        let novasParcelasRestantes = Math.ceil(saldoAposAmort / amortMensal);
                        parcelasEliminadas = parcelasRestantesOrig - novasParcelasRestantes;
                        let jurosSem = (saldoDevedorAtual * taxa * (parcelasRestantesOrig + 1)) / 2;
                        let jurosCom = (saldoAposAmort * taxa * (novasParcelasRestantes + 1)) / 2;
                        economiaJuros = Math.max(0, jurosSem - jurosCom);
                    }} else {{
                        let num = pmtOrig / (pmtOrig - taxa * saldoAposAmort);
                        let novasParcelasRestantes = (num > 0) ? Math.ceil(Math.log(num) / Math.log(1 + taxa)) : 0;
                        parcelasEliminadas = parcelasRestantesOrig - novasParcelasRestantes;
                        let jurosSem = (pmtOrig * parcelasRestantesOrig) - saldoDevedorAtual;
                        let jurosCom = (pmtOrig * novasParcelasRestantes) - saldoAposAmort;
                        economiaJuros = Math.max(0, jurosSem - jurosCom);
                    }}
                }} else {{
                    if (sistema === 'SAC') {{
                        let novaAmort = saldoAposAmort / parcelasRestantesOrig;
                        let novaP1 = novaAmort + (saldoAposAmort * taxa);
                        let jurosSem = (saldoDevedorAtual * taxa * (parcelasRestantesOrig + 1)) / 2;
                        let jurosCom = (saldoAposAmort * taxa * (parcelasRestantesOrig + 1)) / 2;
                        economiaJuros = Math.max(0, jurosSem - jurosCom);
                    }} else {{
                        let novaPmt = saldoAposAmort * (taxa * Math.pow(1 + taxa, parcelasRestantesOrig)) / (Math.pow(1 + taxa, parcelasRestantesOrig) - 1);
                        let jurosSem = (pmtOrig * parcelasRestantesOrig) - saldoDevedorAtual;
                        let jurosCom = (novaPmt * parcelasRestantesOrig) - saldoAposAmort;
                        economiaJuros = Math.max(0, jurosSem - jurosCom);
                    }}
                }}
            }}

            const retornoMultiplo = valorAmortizar > 0 ? (economiaJuros / valorAmortizar).toFixed(2) : "0.00";
            const cfg = {{style:'currency',currency:'BRL'}};
            
            // Textos Base
            document.getElementById('res_p1_orig').innerText = p1Orig.toLocaleString('pt-BR', cfg);
            document.getElementById('res_total_orig').innerText = totalPagoOrig.toLocaleString('pt-BR', cfg);
            document.getElementById('res_economia').innerText = economiaJuros.toLocaleString('pt-BR', cfg);

            // MÁGICA DOS ANOS E MESES
            if(objetivo === 'prazo') {{
                let anos = Math.floor(parcelasEliminadas / 12);
                let meses = parcelasEliminadas % 12;
                let textoTempo = "";
                
                if (anos > 0) textoTempo += anos + (anos === 1 ? " Ano" : " Anos");
                if (anos > 0 && meses > 0) textoTempo += " e ";
                if (meses > 0 || (anos === 0 && meses === 0)) textoTempo += meses + (meses === 1 ? " Mês" : " Meses");

                document.getElementById('res_impacto').innerText = textoTempo;
                document.getElementById('sub_impacto').innerText = "De vida recuperados (Sem Dívida)";
                document.getElementById('frase_humana').innerText = `O verdadeiro luxo é o tempo. Você recuperou ${{textoTempo}} de liberdade financeira.`;
            }} else {{
                document.getElementById('res_impacto').innerText = "Fluxo de Caixa";
                document.getElementById('sub_impacto').innerText = "Oxigênio mensal libertado";
                document.getElementById('frase_humana').innerText = `Você reduz drasticamente o peso das suas obrigações mensais, ganhando paz de espírito.`;
            }}

            document.getElementById('retorno_multiplo').innerText = `O ROI Invisível: Cada R$ 1,00 aportado devolve R$ ${{retornoMultiplo.replace('.', ',')}} para você.`;

            // Atualiza Aura
            const card = document.querySelector('.aura-glow');
            if (economiaJuros > 0) {{
                card.style.setProperty('--tw-shadow-color', 'rgba(16, 185, 129, 0.2)');
                card.style.boxShadow = 'var(--tw-ring-offset-shadow, 0 0 #0000), var(--tw-ring-shadow, 0 0 #0000), 0 0 40px var(--tw-shadow-color)';
            }} else {{
                card.style.boxShadow = '0 25px 50px -12px rgba(0, 0, 0, 0.5)';
            }}

            atualizarLinksWhatsapp(vImovel, entrada, valorAmortizar, economiaJuros);
        }}

        window.onload = function() {{
            document.getElementById('slider_imovel').value = {valor_imovel};
            document.getElementById('input_imovel').value = formatCurrency({valor_imovel});
            document.getElementById('slider_entrada').value = {int(entrada_padrao)};
            document.getElementById('input_entrada').value = formatCurrency({int(entrada_padrao)});
            document.getElementById('display_pagas').innerText = "14 / " + document.getElementById('input_prazo').value + " meses";
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
        "Caixa": "caixa.gov.br",
        "Banco do Brasil": "bb.com.br",
        "Itau": "itau.com.br",
        "Bradesco": "bradesco.com.br",
        "Santander": "santander.com.br",
        "Banco Inter": "bancointer.com.br",
        "Banrisul": "banrisul.com.br",
        "BRB": "brb.com.br",
        "Sicredi": "sicredi.com.br",
        "Sicoob": "sicoob.com.br",
        "C6 Bank": "c6bank.com.br",
        "Poupex": "poupex.com.br"
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
                    <svg class="w-3 h-3 text-slate-600 group-hover:text-amber-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                </a>
            </li>
        ''' for item in links])
        
        blocos_html += f'''
        <div class="bg-white/5 backdrop-blur-md rounded-2xl shadow-2xl border border-white/10 overflow-hidden transition-all duration-300 hover:border-amber-500/30 hover:shadow-[0_0_30px_rgba(245,158,11,0.1)]">
            <div class="border-b border-white/10 px-6 py-5 flex items-center gap-4 bg-black/20">
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
    <title>Desbloqueie o Poder do Seu Patrimônio | Simulador Datalab</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; background: radial-gradient(circle at top right, #1e293b, #020617); color: #f8fafc; }}
        h1, h2, .font-serif {{ font-family: 'Playfair Display', serif; }}
        .text-gold {{ background: linear-gradient(to right, #fbbf24, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .custom-scrollbar::-webkit-scrollbar {{ width: 4px; }}
        .custom-scrollbar::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.05); border-radius: 4px; }}
        .custom-scrollbar::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.2); border-radius: 4px; }}
    </style>
</head>
<body class="antialiased min-h-screen">
    <nav class="border-b border-white/10 sticky top-0 z-50 backdrop-blur-xl bg-slate-950/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="index.html" class="flex items-center space-x-3">
                    <div class="w-10 h-10 rounded-full flex items-center justify-center border border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.2)] text-amber-500">
                        <i class="fa-solid fa-gem"></i>
                    </div>
                    <span class="font-serif text-2xl tracking-wide text-white">Simulador <span class="text-gold">Datalab</span></span>
                </a>
            </div>
        </div>
    </nav>
    <div class="py-24 md:py-32 text-center px-4 relative overflow-hidden">
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-emerald-500/10 rounded-full blur-[100px] -z-10"></div>
        <h1 class="text-4xl md:text-6xl font-serif text-white mb-6 leading-tight max-w-4xl mx-auto">
            A Arte de Financiar com <span class="text-gold">Inteligência</span>.
        </h1>
        <p class="text-slate-400 text-lg md:text-xl font-light tracking-wide max-w-2xl mx-auto">
            Selecione a instituição financeira abaixo e descubra quantos anos de vida você pode recuperar através do planejamento estratégico.
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