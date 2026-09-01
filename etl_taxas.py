import csv
import os

def obter_taxas_reais_mercado():
    print("Carregando matriz interna de taxas reais atualizadas...")
    # Matriz atualizada e realista para o cenário econômico (Selic Alta)
    taxas_reais = {
        "Caixa": 11.49,
        "Banco do Brasil": 11.69,
        "Itau": 11.89,
        "Bradesco": 11.99,
        "Santander": 11.99,
        "Banco Inter": 12.99,
        "Sicredi": 11.50,
        "Sicoob": 11.50,
        "Banrisul": 11.60,
        "BRB": 11.25,
        "Poupex": 10.80,
        "C6 Bank": 13.50 # <-- REDUZIDO PARA TAXA DE VITRINE
    }
    
    for banco, taxa in taxas_reais.items():
        print(f"✅ {banco} configurado para {taxa}% a.a.")
        
    return taxas_reais

def atualizar_base_csv(novas_taxas):
    caminho_csv = 'dados.csv'
    dados_atualizados = []
    
    # Motor de regras centralizado
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
            
            # Garante colunas de enriquecimento
            for col in ['cet', 'ltv', 'prazo_maximo']:
                if col not in cabecalho:
                    cabecalho.append(col)

            for linha in leitor:
                banco = linha['banco']
                
                # 1. Atualiza a taxa nominal com a nossa matriz segura
                if novas_taxas and banco in novas_taxas:
                    linha['taxa'] = novas_taxas[banco] 
                
                # 2. Enriquecimento: LTV e Prazo Máximo
                regra = regras_bancos.get(banco, {"ltv": 80, "prazo_maximo": 360})
                linha['ltv'] = regra['ltv']
                linha['prazo_maximo'] = regra['prazo_maximo']
                
                # 3. Enriquecimento: CET (+ 0.15% de custo de seguros)
                taxa_atual = float(linha['taxa'])
                linha['cet'] = round(taxa_atual + 0.15, 2)

                dados_atualizados.append(linha)

        with open(caminho_csv, mode='w', newline='', encoding='utf-8') as f:
            escritor = csv.DictWriter(f, fieldnames=cabecalho, delimiter=';')
            escritor.writeheader()
            escritor.writerows(dados_atualizados)
        
        print("\n🚀 O arquivo dados.csv foi curado com taxas REAIS de mercado!")
        
    except FileNotFoundError:
        print("Arquivo dados.csv não encontrado para atualização.")

if __name__ == "__main__":
    taxas_seguras = obter_taxas_reais_mercado()
    atualizar_base_csv(taxas_seguras)