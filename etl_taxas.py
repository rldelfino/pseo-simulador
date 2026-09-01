import csv
import requests
from bs4 import BeautifulSoup
import re

def extrair_taxas_idinheiro():
    # URL oficial de ranking imobiliário do iDinheiro
    url = "https://www.idinheiro.com.br/financiamentos/imobiliario/melhor-taxa-financiamento-imobiliario/"
    
    # Simulando um navegador real para não ser bloqueado
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    print("Iniciando a varredura de taxas no portal iDinheiro...")
    novas_taxas = {}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() 
        
        soup = BeautifulSoup(response.text, 'html.parser')
        texto_pagina = soup.get_text(separator=' ', strip=True)
        
        # Mapeamento dos bancos e as expressões regulares (Regex) para achar a taxa a.m.
        mapa_buscas = {
            "Caixa": r"Caixa(?: Econômica Federal)?.*?(\d+,\d+)%\s*a\.m\.",
            "Banco do Brasil": r"Banco do Brasil.*?(\d+,\d+)%\s*a\.m\.",
            "Itau": r"Itaú.*?(\d+,\d+)%\s*a\.m\.",
            "Bradesco": r"Bradesco.*?(\d+,\d+)%\s*a\.m\.",
            "Santander": r"Santander.*?(\d+,\d+)%\s*a\.m\.",
            "Banco Inter": r"Banco Inter.*?(\d+,\d+)%\s*a\.m\.",
            "Sicredi": r"Sicredi.*?(\d+,\d+)%\s*a\.m\."
        }
        
        for banco, padrao in mapa_buscas.items():
            resultado = re.search(padrao, texto_pagina, re.IGNORECASE)
            if resultado:
                # Transforma a string "0,86" no float matemático 0.86
                taxa_mensal = float(resultado.group(1).replace(',', '.'))
                
                # REVISÃO: Converte a taxa MENSAL para a taxa ANUAL EQUIVALENTE
                # Fórmula: ((1 + taxa_mensal/100)^12 - 1) * 100
                taxa_anual = ((1 + (taxa_mensal / 100)) ** 12 - 1) * 100
                
                # Arredonda para 2 casas decimais e salva
                novas_taxas[banco] = round(taxa_anual, 2)
                print(f"✅ {banco} atualizado: {taxa_mensal}% a.m. -> {round(taxa_anual, 2)}% a.a.")
            else:
                print(f"⚠️ Taxa não encontrada para {banco} na leitura de hoje.")
                
    except Exception as e:
        print(f"❌ Erro ao acessar o iDinheiro: {e}")
        
    return novas_taxas

def atualizar_base_csv(novas_taxas):
    caminho_csv = 'dados.csv'
    dados_atualizados = []
    
    # REVISÃO: Motor de regras centralizado com todos os 12 bancos (Taxas reais 2026 - Selic ~14.25%)
    regras_bancos = {
        "Caixa": {"ltv": 80, "prazo_maximo": 420},
        "Banco do Brasil": {"ltv": 80, "prazo_maximo": 420},
        "Santander": {"ltv": 80, "prazo_maximo": 420},
        "BRB": {"ltv": 80, "prazo_maximo": 420},
        "Poupex": {"ltv": 90, "prazo_maximo": 420},
        "Itau": {"ltv": 80, "prazo_maximo": 360},
        "Bradesco": {"ltv": 80, "prazo_maximo": 360},
        "Banco Inter": {"ltv": 80, "prazo_maximo": 360},
        "Sicredi": {"ltv": 80, "prazo_maximo": 360},
        "Sicoob": {"ltv": 80, "prazo_maximo": 360},
        "Banrisul": {"ltv": 75, "prazo_maximo": 360},
        "C6 Bank": {"ltv": 60, "prazo_maximo": 240}
    }
    
    try:
        with open(caminho_csv, mode='r', encoding='utf-8') as f:
            leitor = csv.DictReader(f, delimiter=';')
            cabecalho = list(leitor.fieldnames)
            
            # Garante que as novas colunas existam no cabeçalho
            colunas_enriquecimento = ['cet', 'ltv', 'prazo_maximo']
            for col in colunas_enriquecimento:
                if col not in cabecalho:
                    cabecalho.append(col)

            for linha in leitor:
                banco = linha['banco']
                
                # 1. Atualiza a taxa nominal SE o robô encontrou uma nova
                if novas_taxas and banco in novas_taxas:
                    linha['taxa'] = novas_taxas[banco] 
                
                # 2. Enriquecimento: LTV e Prazo Máximo
                regra = regras_bancos.get(banco, {"ltv": 80, "prazo_maximo": 360})
                linha['ltv'] = regra['ltv']
                linha['prazo_maximo'] = regra['prazo_maximo']
                
                # 3. Enriquecimento: CET (Calculamos a taxa nominal + 0.15% de custo médio de seguros)
                try:
                    taxa_atual = float(str(linha['taxa']).replace(',', '.'))
                except ValueError:
                    taxa_atual = 11.99 # Taxa fallback de segurança
                    
                linha['cet'] = round(taxa_atual + 0.15, 2)

                dados_atualizados.append(linha)

        # Salva o arquivo CSV atualizado com as novas colunas
        with open(caminho_csv, mode='w', newline='', encoding='utf-8') as f:
            escritor = csv.DictWriter(f, fieldnames=cabecalho, delimiter=';')
            escritor.writeheader()
            escritor.writerows(dados_atualizados)
        
        print("\n🚀 O arquivo dados.csv foi enriquecido e reescrito com sucesso (AGORA COM TAXAS ANUAIS)!")
        
    except FileNotFoundError:
        print("Arquivo dados.csv não encontrado para atualização.")

if __name__ == "__main__":
    taxas = extrair_taxas_idinheiro()
    atualizar_base_csv(taxas)