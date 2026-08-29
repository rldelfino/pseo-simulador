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
        # O iDinheiro costuma escrever: "11,54% a.a. (ou 0,91% a.m.)"
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
    if not novas_taxas:
        print("Nenhuma taxa nova para atualizar. Mantendo base original.")
        return

    caminho_csv = 'dados.csv'
    dados_atualizados = []
    
    # 1. Lê a base atual e substitui pelas novas taxas
    try:
        with open(caminho_csv, mode='r', encoding='utf-8') as f:
            leitor = csv.DictReader(f, delimiter=';')
            cabecalho = leitor.fieldnames
            for linha in leitor:
                banco = linha['banco']
                # Atualiza a taxa só se o banco estiver no dicionário que raspamos
                if banco in novas_taxas:
                    linha['taxa'] = novas_taxas[banco] 
                dados_atualizados.append(linha)

        # 2. Salva o arquivo CSV atualizado
        with open(caminho_csv, mode='w', newline='', encoding='utf-8') as f:
            escritor = csv.DictWriter(f, fieldnames=cabecalho, delimiter=';')
            escritor.writeheader()
            escritor.writerows(dados_atualizados)
        
        print("\n🚀 O arquivo dados.csv foi reescrito com sucesso com os juros do mês!")
        
    except FileNotFoundError:
        print("Arquivo dados.csv não encontrado para atualização.")

if __name__ == "__main__":
    taxas = extrair_taxas_idinheiro()
    atualizar_base_csv(taxas)