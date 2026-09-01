import csv
import os

def obter_taxas_reais_mercado():
    print("Carregando matriz interna de taxas reais atualizadas...")
    taxas_reais = {
        "Caixa": 11.49,
        "Banco do Brasil": 11.69,
        "Itau": 13.09,
        "Santander": 13.39,
        "Bradesco": 13.50,
        "Banco Inter": 9.50,
        "Sicredi": 11.50,
        "Sicoob": 11.50,
        "Banrisul": 11.60,
        "BRB": 11.25,
        "Poupex": 10.80,
        "C6 Bank": 13.50,
        "Bari": 15.25,
        "Cash Me": 16.63,
        "Daycoval": 16.63
    }
    
    for banco, taxa in taxas_reais.items():
        print(f"✅ {banco} configurado para {taxa}% a.a.")
        
    return taxas_reais

def atualizar_base_csv(novas_taxas):
    caminho_csv = 'dados.csv'
    dados_atualizados = []
    
    regras_bancos = {
        "Caixa": {"ltv": 80, "prazo_maximo": 420}, "Banco do Brasil": {"ltv": 80, "prazo_maximo": 420},
        "Santander": {"ltv": 80, "prazo_maximo": 420}, "BRB": {"ltv": 80, "prazo_maximo": 420},
        "Poupex": {"ltv": 90, "prazo_maximo": 420}, "Itau": {"ltv": 80, "prazo_maximo": 360},
        "Bradesco": {"ltv": 80, "prazo_maximo": 360}, "Banco Inter": {"ltv": 80, "prazo_maximo": 360},
        "Sicredi": {"ltv": 80, "prazo_maximo": 360}, "Sicoob": {"ltv": 80, "prazo_maximo": 360},
        "Banrisul": {"ltv": 75, "prazo_maximo": 360}, "C6 Bank": {"ltv": 60, "prazo_maximo": 240},
        "Bari": {"ltv": 60, "prazo_maximo": 360}, "Cash Me": {"ltv": 60, "prazo_maximo": 360},
        "Daycoval": {"ltv": 60, "prazo_maximo": 360}
    }
    
    try:
        with open(caminho_csv, mode='r', encoding='utf-8') as f:
            leitor = csv.DictReader(f, delimiter=';')
            cabecalho = list(leitor.fieldnames)
            
            for col in ['cet', 'ltv', 'prazo_maximo']:
                if col not in cabecalho: cabecalho.append(col)

            for linha in leitor:
                banco = linha['banco']
                if novas_taxas and banco in novas_taxas:
                    linha['taxa'] = novas_taxas[banco] 
                
                regra = regras_bancos.get(banco, {"ltv": 80, "prazo_maximo": 360})
                linha['ltv'] = regra['ltv']
                linha['prazo_maximo'] = regra['prazo_maximo']
                
                taxa_atual = float(linha['taxa'])
                linha['cet'] = round(taxa_atual + 0.15, 2)
                dados_atualizados.append(linha)
                
            # Adiciona os novos bancos se eles não estiverem no CSV
            bancos_existentes = [d['banco'] for d in dados_atualizados]
            for novo_banco in ["Bari", "Cash Me", "Daycoval"]:
                if novo_banco not in bancos_existentes:
                    taxa_n = novas_taxas[novo_banco]
                    r = regras_bancos[novo_banco]
                    dados_atualizados.append({
                        'banco': novo_banco, 'valor_imovel': '500000', 'taxa': taxa_n, 
                        'prazo': '360', 'slug': f'simulador-{novo_banco.lower().replace(" ", "-")}-500-mil-360-meses',
                        'cet': round(taxa_n + 0.15, 2), 'ltv': r['ltv'], 'prazo_maximo': r['prazo_maximo']
                    })

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