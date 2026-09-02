"""
⚠️ SCRIPT DE BOOTSTRAP — NÃO RODAR EM PRODUÇÃO.

Este script existiu para criar o dados.csv PELA PRIMEIRA VEZ, com taxas
fictícias (0.75 etc.) como placeholder. Hoje o dados.csv é a base viva,
curada com taxas reais de mercado e mantida pelo etl_taxas.py (que lê o
bancos.py como fonte única de verdade). Rodar este script de novo
SOBRESCREVE o dados.csv real com a grade antiga de bootstrap e destrói
os dados de produção — só existe aqui por histórico/referência.
"""
import csv


def criar_base_de_dados():
    bancos = [
        {"nome": "Caixa", "taxa": 0.75},
        {"nome": "Banco do Brasil", "taxa": 0.79},
        {"nome": "Itau", "taxa": 0.85},
        {"nome": "Bradesco", "taxa": 0.83},
        {"nome": "Santander", "taxa": 0.89},
        {"nome": "Banco Inter", "taxa": 0.82},
        {"nome": "Banrisul", "taxa": 0.84},
        {"nome": "BRB", "taxa": 0.78},
        {"nome": "Sicredi", "taxa": 0.81},
        {"nome": "Sicoob", "taxa": 0.80},
        {"nome": "C6 Bank", "taxa": 0.86},
        {"nome": "Poupex", "taxa": 0.77}
    ]

    # Valores de R$ 100.000 a R$ 2.000.000
    valores_imovel = range(100000, 2000001, 50000) 
    prazos = [120, 180, 240, 360, 420]

    caminho_csv = 'dados.csv'

    with open(caminho_csv, mode='w', newline='', encoding='utf-8') as arquivo:
        writer = csv.writer(arquivo, delimiter=';')
        writer.writerow(['banco', 'valor_imovel', 'taxa', 'prazo', 'slug'])

        contador = 0
        for banco in bancos:
            for valor in valores_imovel:
                for prazo in prazos:
                    nome = banco["nome"]
                    taxa = banco["taxa"]
                    
                    nome_banco_slug = nome.lower().replace(" ", "-")
                    milhares = int(valor / 1000)
                    slug = f"simulador-{nome_banco_slug}-{milhares}-mil-{prazo}-meses"

                    writer.writerow([nome, valor, taxa, prazo, slug])
                    contador += 1

    print(f"✅ Base de dados gerada com {contador} combinações prontas.")

if __name__ == "__main__":
    criar_base_de_dados()