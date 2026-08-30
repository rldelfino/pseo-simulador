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
        response.raise_for_status() # Verifica se a página carregou com sucesso
        
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
                # Transforma a string "0,62" no float matemático 0.62
                taxa_str = resultado.group(1).replace(',', '.')
                novas_taxas[banco] = float(taxa_str)
                print(f"✅ {banco} atualizado: {taxa_str}% a.m.")
            else:
                print(f"⚠️ Taxa não encontrada para {banco} na leitura de hoje.")
                
    except Exception as e:
        print(f"❌ Erro ao acessar o iDinheiro: {e}")
        
    return novas_taxas

def atualizar_base_csv(novas_taxas):
    caminho_csv = 'dados.csv'
    dados_atualizados = []
    
    # Dicionário de regras de negócio de mercado para enriquecimento
    regras_bancos = {
        "Caixa": {"ltv": 80, "prazo_maximo": 420},
        "Banco do Brasil": {"ltv": 80, "prazo_maximo": 420},
        "Santander": {"ltv": 80, "prazo_maximo": 420},
        "Itau": {"ltv": 82, "prazo_maximo": 360},
        "Bradesco": {"ltv": 80, "prazo_maximo": 360},
        "Banco Inter": {"ltv": 70, "prazo_maximo": 360},
        "Sicredi": {"ltv": 80, "prazo_maximo": 360}
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
                
                # 2. Enriquecimento: LTV e Prazo Máximo (usa o padrão de 80%/360 se o banco não estiver na lista)
                regra = regras_bancos.get(banco, {"ltv": 80, "prazo_maximo": 360})
                linha['ltv'] = regra['ltv']
                linha['prazo_maximo'] = regra['prazo_maximo']
                
                # 3. Enriquecimento: CET (Calculamos a taxa nominal + 0.15% de custo médio de seguros)
                taxa_atual = float(linha['taxa'])
                linha['cet'] = round(taxa_atual + 0.15, 2)

                dados_atualizados.append(linha)

        # Salva o arquivo CSV atualizado com as novas colunas
        with open(caminho_csv, mode='w', newline='', encoding='utf-8') as f:
            escritor = csv.DictWriter(f, fieldnames=cabecalho, delimiter=';')
            escritor.writeheader()
            escritor.writerows(dados_atualizados)
        
        print("\n🚀 O arquivo dados.csv foi enriquecido e reescrito com sucesso!")
        
    except FileNotFoundError:
        print("Arquivo dados.csv não encontrado para atualização.")

if __name__ == "__main__":
    taxas = extrair_taxas_idinheiro()
    # O script roda a atualização mesmo se 'taxas' estiver vazio, 
    # justamente para forçar a criação das novas colunas (CET, LTV) no CSV!
    atualizar_base_csv(taxas)