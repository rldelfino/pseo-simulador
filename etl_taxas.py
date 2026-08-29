import csv
import requests
from bs4 import BeautifulSoup

def extrair_taxas_consolidador():
    # URL fictícia de exemplo (substitua pela URL do portal escolhido, ex: InfoMoney, MelhorTaxa)
    url = "https://exemplo-portal-financeiro.com.br/taxas-financiamento-imobiliario"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    # try:
    #     resposta = requests.get(url, headers=headers)
    #     soup = BeautifulSoup(resposta.text, 'html.parser')
    #     Lógica de extração baseada nas classes HTML da tabela do site alvo iria aqui...
    # except Exception as e:
    #     print(f"Erro na extração: {e}")

    # Para este exemplo funcional, simulamos as taxas atualizadas capturadas via scraping
    novas_taxas = {
        "Caixa": 0.81,
        "Itau": 0.86,
        "Bradesco": 0.84,
        # ... outros bancos ...
    }
    return novas_taxas

def atualizar_base_csv(novas_taxas):
    caminho_csv = 'dados.csv'
    dados_atualizados = []
    
    # 1. Lê os dados atuais
    with open(caminho_csv, mode='r', encoding='utf-8') as f:
        leitor = csv.DictReader(f, delimiter=';')
        cabecalho = leitor.fieldnames
        for linha in leitor:
            banco = linha['banco']
            if banco in novas_taxas:
                linha['taxa'] = novas_taxas[banco] # Atualiza a taxa
            dados_atualizados.append(linha)

    # 2. Sobrescreve com as novas taxas
    with open(caminho_csv, mode='w', newline='', encoding='utf-8') as f:
        escritor = csv.DictWriter(f, fieldnames=cabecalho, delimiter=';')
        escritor.writeheader()
        escritor.writerows(dados_atualizados)
    
    print("✅ CSV atualizado com as taxas do mês!")

if __name__ == "__main__":
    taxas = extrair_taxas_consolidador()
    atualizar_base_csv(taxas)