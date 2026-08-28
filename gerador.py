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
            
            if banco not in links_por_banco:
                links_por_banco[banco] = []
            links_por_banco[banco].append({
                "slug": slug,
                "texto": f"Imóvel de {valor_amigavel} em {prazo} meses"
            })

            entrada_padrao = valor_imovel * 0.20 

            html_content = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calculadora de Financiamento e Amortização {banco} | ImobSimula</title>
    <meta name="description" content="Simule o financiamento imobiliário e amortização extraordinária pela {banco} para imóveis de {valor_amigavel}. Descubra quantas parcelas você reduz adiantando valores.">
    <link rel="canonical" href="{dominio}/{slug}.html" />
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>body {{ font-family: 'Inter', sans-serif; }} input[type="radio"]:checked + div {{ border-color: #f97316; background-color: #fff7ed; }}</style>
</head>
<body class="bg-slate-50 text-slate-800 antialiased">
    <nav class="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="index.html" class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-orange-500 rounded-2xl flex items-center justify-center text-white font-bold text-xl shadow-md">
                        <i class="fa-solid fa-calculator"></i>
                    </div>
                    <span class="text-2xl font-black tracking-tight text-slate-900">Imob<span class="text-orange-500">Simula</span></span>
                </a>
                <div class="hidden lg:flex space-x-8 text-sm font-semibold text-slate-600">
                    <a href="index.html" class="hover:text-orange-500 transition-colors">Início</a>
                    <a href="#" class="hover:text-orange-500 transition-colors">Simulador de Amortização</a>
                    <a href="#" class="hover:text-orange-500 transition-colors">Contato</a>
                </div>
                <div class="hidden md:flex items-center space-x-4">
                    <button class="bg-orange-500 hover:bg-orange-600 text-white px-5 py-2.5 rounded-full font-bold shadow-md transition-all text-sm flex items-center">
                        <i class="fa-brands fa-whatsapp mr-2 text-base"></i> Falar com Especialista
                    </button>
                </div>
            </div>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
            <div class="text-xs font-semibold text-slate-500 flex items-center space-x-2">
                <a href="index.html" class="hover:text-orange-500">Home</a> <span>/</span>
                <span class="text-slate-400">Calculadoras</span> <span>/</span>
                <span class="text-slate-800">Amortização {banco}</span>
            </div>
        </div>

        <div class="flex flex-col lg:flex-row gap-8 items-start">
            <div class="w-full lg:w-2/3 space-y-6">
                <div>
                    <h1 class="text-3xl md:text-4xl font-black text-slate-900 mb-3 tracking-tight">Financiamento & Amortização <span class="text-orange-500">{banco}</span></h1>
                    <p class="text-slate-500 text-base font-medium">Calcule as parcelas iniciais e veja o impacto exato ao amortizar valores extras no seu contrato.</p>
                </div>

                <!-- Painel 1: Dados do Financiamento -->
                <div class="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
                    <h2 class="text-xl font-bold text-slate-800 mb-6 flex items-center"><i class="fa-solid fa-house-circle-check text-orange-500 mr-3"></i> 1. Dados do Contrato</h2>
                    <div class="space-y-6">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div><label class="block text-sm font-semibold text-slate-700 mb-2">Valor do Imóvel (R$)</label><input type="number" id="valor_imovel" value="{valor_imovel}" class="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3.5 focus:bg-white focus:ring-2 focus:ring-orange-500 font-bold text-slate-900 text-lg outline-none"></div>
                            <div><label class="block text-sm font-semibold text-slate-700 mb-2">Entrada (R$)</label><input type="number" id="entrada" value="{int(entrada_padrao)}" class="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3.5 focus:bg-white focus:ring-2 focus:ring-orange-500 font-bold text-slate-900 text-lg outline-none"></div>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div><label class="block text-sm font-semibold text-slate-700 mb-2">Prazo Total (Meses)</label><input type="number" id="prazo" value="{prazo}" class="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3.5 focus:bg-white focus:ring-2 focus:ring-orange-500 font-bold text-slate-900 text-lg outline-none"></div>
                            <div><label class="block text-sm font-semibold text-slate-700 mb-2">Taxa de Juros (% a.m.)</label><input type="number" id="taxa" value="{taxa}" step="0.01" class="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3.5 focus:bg-white focus:ring-2 focus:ring-orange-500 font-bold text-slate-900 text-lg outline-none"></div>
                        </div>
                        <div>
                            <label class="block text-sm font-semibold text-slate-700 mb-3">Sistema de Amortização</label>
                            <div class="grid grid-cols-2 gap-4">
                                <label class="relative cursor-pointer"><input type="radio" name="sistema" value="SAC" class="sr-only" checked><div class="border-2 border-slate-200 rounded-2xl p-4 transition-all duration-200"><div class="flex items-center justify-between mb-1"><span class="font-bold text-slate-900">Tabela SAC</span><i class="fa-solid fa-circle-check text-orange-500 hidden check-icon"></i></div><p class="text-xs text-slate-500 font-medium">Parcelas decrescentes</p></div></label>
                                <label class="relative cursor-pointer"><input type="radio" name="sistema" value="PRICE" class="sr-only"><div class="border-2 border-slate-200 rounded-2xl p-4 transition-all duration-200"><div class="flex items-center justify-between mb-1"><span class="font-bold text-slate-900">Tabela PRICE</span><i class="fa-solid fa-circle-check text-orange-500 hidden check-icon"></i></div><p class="text-xs text-slate-500 font-medium">Parcelas fixas</p></div></label>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Painel 2: Amortização Extraordinária -->
                <div class="bg-orange-50/50 p-8 rounded-3xl border border-orange-100 shadow-sm">
                    <h2 class="text-xl font-bold text-slate-800 mb-6 flex items-center"><i class="fa-solid fa-bolt text-orange-500 mr-3"></i> 2. Simulação de Amortização Extra</h2>
                    <div class="space-y-6">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label class="block text-sm font-semibold text-slate-700 mb-2">Parcelas Já Pagas</label>
                                <input type="number" id="parcelas_pagas" value="14" class="w-full bg-white border border-slate-200 rounded-2xl px-4 py-3.5 focus:ring-2 focus:ring-orange-500 font-bold text-slate-900 text-lg outline-none">
                            </div>
                            <div>
                                <label class="block text-sm font-semibold text-slate-700 mb-2">Valor Extra para Adiantar (R$)</label>
                                <input type="number" id="valor_amortizar" value="10000" class="w-full bg-white border border-slate-200 rounded-2xl px-4 py-3.5 focus:ring-2 focus:ring-orange-500 font-bold text-slate-900 text-lg outline-none">
                            </div>
                        </div>
                        <div>
                            <label class="block text-sm font-semibold text-slate-700 mb-2">Objetivo da Amortização</label>
                            <select id="tipo_amortizacao" class="w-full bg-white border border-slate-200 rounded-2xl px-4 py-3.5 focus:ring-2 focus:ring-orange-500 font-bold text-slate-900 text-base outline-none">
                                <option value="prazo">Reduzir Número de Parcelas (Reduzir Prazo)</option>
                                <option value="parcela">Reduzir Valor da Parcela Mensal</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Resumo e Impacto Financeiro -->
            <div class="w-full lg:w-1/3 lg:sticky lg:top-28">
                <div class="bg-white p-7 rounded-3xl border border-slate-200 shadow-xl shadow-slate-200/50 space-y-6">
                    <h3 class="text-lg font-bold text-slate-900 border-b border-slate-100 pb-4">Resultado do Financiamento</h3>
                    
                    <div>
                        <p class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Primeira Parcela Original</p>
                        <p id="res_primeira" class="text-3xl font-black text-slate-800 tracking-tight">R$ 0,00</p>
                    </div>

                    <div class="bg-emerald-50 border border-emerald-200 p-5 rounded-2xl space-y-3">
                        <h4 class="text-xs font-bold text-emerald-800 uppercase tracking-wider flex items-center">
                            <i class="fa-solid fa-piggy-bank mr-2 text-base text-emerald-600"></i> Impacto da Amortização
                        </h4>
                        <div>
                            <p id="label_impacto" class="text-xs text-emerald-700 font-semibold mb-1">Parcelas Eliminadas</p>
                            <p id="res_impacto" class="text-3xl font-black text-emerald-600 tracking-tight">0 parcelas</p>
                        </div>
                        <div class="pt-2 border-t border-emerald-200/60">
                            <p class="text-xs text-emerald-700 font-semibold mb-1">Economia Estimada de Juros</p>
                            <p id="res_economia" class="text-xl font-extrabold text-emerald-700">R$ 0,00</p>
                        </div>
                    </div>

                    <div class="pt-2 space-y-3">
                        <button id="btn_calcular" class="w-full bg-slate-900 text-white font-bold py-4 rounded-2xl hover:bg-slate-800 transition-colors shadow-md">Recalcular Amortização</button>
                        <button class="w-full bg-emerald-500 text-white font-bold py-4 rounded-2xl hover:bg-emerald-600 transition-colors shadow-md flex items-center justify-center"><i class="fa-brands fa-whatsapp mr-2 text-lg"></i> Receber Estratégia</button>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        document.querySelectorAll('input[type="radio"]').forEach(radio => {{ radio.addEventListener('change', function() {{ document.querySelectorAll('.check-icon').forEach(i => i.classList.add('hidden')); if(this.checked) this.nextElementSibling.querySelector('.check-icon').classList.remove('hidden'); }}); }});
        document.querySelector('input[name="sistema"]:checked').nextElementSibling.querySelector('.check-icon').classList.remove('hidden');
        
        window.onload = function() {{ document.getElementById('btn_calcular').click(); }};
        
        document.getElementById('btn_calcular').addEventListener('click', function() {{
            const vImovel = parseFloat(document.getElementById('valor_imovel').value) || 0;
            const entrada = parseFloat(document.getElementById('entrada').value) || 0;
            const taxa = (parseFloat(document.getElementById('taxa').value) || 0) / 100;
            const prazo = parseInt(document.getElementById('prazo').value) || 0;
            const sistema = document.querySelector('input[name="sistema"]:checked').value;
            
            const parcelasPagas = parseInt(document.getElementById('parcelas_pagas').value) || 0;
            const valorAmortizar = parseFloat(document.getElementById('valor_amortizar').value) || 0;
            const tipoAmortizacao = document.getElementById('tipo_amortizacao').value;

            const vFinanciado = vImovel - entrada;
            if (vFinanciado <= 0 || prazo <= 0) return;

            // 1. Cálculo do Financiamento Base
            let p1 = 0;
            let amortizacaoMensalOrig = 0;
            let pmtOrig = 0;

            if (sistema === 'SAC') {{
                amortizacaoMensalOrig = vFinanciado / prazo;
                p1 = amortizacaoMensalOrig + (vFinanciado * taxa);
            }} else {{
                pmtOrig = vFinanciado * (taxa * Math.pow(1 + taxa, prazo)) / (Math.pow(1 + taxa, prazo) - 1);
                p1 = pmtOrig;
            }}

            // 2. Saldo Devedor Atual após parcelas pagas
            let saldoDevedorAtual = 0;
            if (sistema === 'SAC') {{
                saldoDevedorAtual = Math.max(0, vFinanciado - (parcelasPagas * amortizacaoMensalOrig));
            }} else {{
                saldoDevedorAtual = Math.max(0, vFinanciado * Math.pow(1 + taxa, parcelasPagas) - pmtOrig * (Math.pow(1 + taxa, parcelasPagas) - 1) / taxa);
            }}

            // 3. Aplicação da Amortização Extra
            let saldoAposAmort = Math.max(0, saldoDevedorAtual - valorAmortizar);
            let parcelasRestantesOrig = Math.max(0, prazo - parcelasPagas);
            let impactoTexto = "";
            let economiaJuros = 0;

            if (valorAmortizar > 0 && parcelasRestantesOrig > 0) {{
                if (tipoAmortizacao === 'prazo') {{
                    if (sistema === 'SAC') {{
                        let novasParcelasRestantes = Math.ceil(saldoAposAmort / amortizacaoMensalOrig);
                        let eliminadas = parcelasRestantesOrig - novasParcelasRestantes;
                        impactoTexto = `${{Math.max(0, eliminadas)}} parcelas a menos`;

                        // Juros sem amortizar vs com amortizar
                        let jurosSem = (saldoDevedorAtual * taxa * (parcelasRestantesOrig + 1)) / 2;
                        let jurosCom = (saldoAposAmort * taxa * (novasParcelasRestantes + 1)) / 2;
                        economiaJuros = Math.max(0, jurosSem - jurosCom);
                    }} else {{
                        let num = pmtOrig / (pmtOrig - taxa * saldoAposAmort);
                        let novasParcelasRestantes = (num > 0) ? Math.ceil(Math.log(num) / Math.log(1 + taxa)) : 0;
                        let eliminadas = parcelasRestantesOrig - novasParcelasRestantes;
                        impactoTexto = `${{Math.max(0, eliminadas)}} parcelas a menos`;
                        
                        let jurosSem = (pmtOrig * parcelasRestantesOrig) - saldoDevedorAtual;
                        let jurosCom = (pmtOrig * novasParcelasRestantes) - saldoAposAmort;
                        economiaJuros = Math.max(0, jurosSem - jurosCom);
                    }}
                    document.getElementById('label_impacto').innerText = "Prazo Eliminado";
                }} else {{
                    // Redução do valor da parcela
                    if (sistema === 'SAC') {{
                        let novaAmortizacao = saldoAposAmort / parcelasRestantesOrig;
                        let novaP1 = novaAmortizacao + (saldoAposAmort * taxa);
                        let diff = p1 - novaP1;
                        impactoTexto = `Redução de R$ ${{diff.toFixed(2)}}/mês`;
                        
                        let jurosSem = (saldoDevedorAtual * taxa * (parcelasRestantesOrig + 1)) / 2;
                        let jurosCom = (saldoAposAmort * taxa * (parcelasRestantesOrig + 1)) / 2;
                        economiaJuros = Math.max(0, jurosSem - jurosCom);
                    }} else {{
                        let novaPmt = saldoAposAmort * (taxa * Math.pow(1 + taxa, parcelasRestantesOrig)) / (Math.pow(1 + taxa, parcelasRestantesOrig) - 1);
                        let diff = pmtOrig - novaPmt;
                        impactoTexto = `Redução de R$ ${{diff.toFixed(2)}}/mês`;
                        
                        let jurosSem = (pmtOrig * parcelasRestantesOrig) - saldoDevedorAtual;
                        let jurosCom = (novaPmt * parcelasRestantesOrig) - saldoAposAmort;
                        economiaJuros = Math.max(0, jurosSem - jurosCom);
                    }}
                    document.getElementById('label_impacto').innerText = "Nova Parcela Reduzida";
                }}
            }} else {{
                impactoTexto = "0 parcelas";
            }}

            const config = {{style:'currency',currency:'BRL'}};
            document.getElementById('res_primeira').innerText = p1.toLocaleString('pt-BR', config);
            document.getElementById('res_impacto').innerText = impactoTexto;
            document.getElementById('res_economia').innerText = economiaJuros.toLocaleString('pt-BR', config);
        }});
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
    print(f"\n🚀 Sucesso! {paginas_geradas} simuladores com amortização extra foram gerados.")

def gerar_index_home(pasta_saida, links_por_banco):
    blocos_html = ""
    for banco, links in links_por_banco.items():
        links_html = "".join([f'<li><a href="{item["slug"]}.html" class="text-slate-600 hover:text-orange-500 font-medium text-xs block py-1 transition-colors border-b border-slate-50"><i class="fa-solid fa-angle-right text-[10px] text-orange-400 mr-1.5"></i> {item["texto"]}</a></li>' for item in links])
        
        blocos_html += f'''
        <div class="banco-card bg-white p-6 rounded-3xl shadow-sm border border-slate-200 hover:shadow-md transition-all">
            <div class="flex items-center space-x-3 mb-4 border-b border-slate-100 pb-3">
                <div class="w-8 h-8 bg-orange-100 rounded-xl flex items-center justify-center text-orange-600 font-bold text-sm">
                    <i class="fa-solid fa-building-columns"></i>
                </div>
                <h2 class="text-lg font-extrabold text-slate-800">{banco}</h2>
            </div>
            <ul class="space-y-1 h-56 overflow-y-auto pr-2 custom-scrollbar">
                {links_html}
            </ul>
        </div>
        '''

    html_home = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ImobSimula | Portal de Financiamento e Amortização Imobiliária</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body class="bg-slate-50 text-slate-800 antialiased">
    <nav class="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <a href="index.html" class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-orange-500 rounded-2xl flex items-center justify-center text-white font-bold text-xl shadow-md"><i class="fa-solid fa-calculator"></i></div>
                    <span class="text-2xl font-black tracking-tight text-slate-900">Imob<span class="text-orange-500">Simula</span></span>
                </a>
            </div>
        </div>
    </nav>
    <div class="bg-slate-900 py-16 text-center px-4">
        <h1 class="text-3xl md:text-5xl font-black text-white mb-4">Simulador de Amortização Extraordinária</h1>
        <p class="text-slate-400 text-base max-w-2xl mx-auto mb-8">Descubra quanto você economiza de juros ao adiantar parcelas no seu banco.</p>
    </div>
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div id="grid_bancos" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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