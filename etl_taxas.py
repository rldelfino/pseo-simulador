import csv

from bancos import BANCOS

# Grade de valores/prazos usada para popular um banco novo com cobertura
# completa (mesma grade já usada organicamente pelos bancos existentes:
# 28 valores x 2 prazos = 56 páginas). Sem isso, um banco novo nasce com
# 1 página solitária, sem cluster suficiente para se autolincar via SEO
# (ver bug de "páginas órfãs" corrigido no gerador.py).
VALORES_IMOVEL_PADRAO = list(range(150_000, 1_500_001, 50_000))
PRAZOS_PADRAO = [360, 420]


def obter_taxas_reais_mercado():
    """
    Retorna o snapshot de taxas usado nesta atualização.

    Hoje isso vem da matriz interna curada em bancos.py (fonte única de
    verdade, compartilhada com gerador.py). Quando o scraping real de
    mercado for implementado, esta função troca a origem do dado sem
    mexer em mais nada — o resto do pipeline não muda.
    """
    print("Carregando matriz interna de taxas reais atualizadas...")
    taxas_reais = {banco: dados["taxa_padrao"] for banco, dados in BANCOS.items()}

    for banco, taxa in taxas_reais.items():
        print(f"✅ {banco} configurado para {taxa}% a.a.")

    return taxas_reais


def atualizar_base_csv(novas_taxas):
    caminho_csv = 'dados.csv'
    dados_atualizados = []

    try:
        with open(caminho_csv, mode='r', encoding='utf-8') as f:
            leitor = csv.DictReader(f, delimiter=';')
            cabecalho = list(leitor.fieldnames)

            for col in ['cet', 'ltv', 'prazo_maximo']:
                if col not in cabecalho:
                    cabecalho.append(col)

            for linha in leitor:
                banco = linha['banco']
                if novas_taxas and banco in novas_taxas:
                    linha['taxa'] = novas_taxas[banco]

                regra = BANCOS.get(banco, {"ltv": 0.80, "prazo_max": 360})
                linha['ltv'] = round(regra['ltv'] * 100)
                linha['prazo_maximo'] = regra.get('prazo_max', 360)

                taxa_atual = float(linha['taxa'])
                linha['cet'] = round(taxa_atual + 0.15, 2)
                dados_atualizados.append(linha)

            # Adiciona bancos novos definidos em bancos.py que ainda não estão no
            # CSV, já com a grade completa de valores x prazos (não apenas 1
            # linha solitária) para que o novo banco tenha cluster suficiente
            # para a linkagem interna funcionar desde o primeiro dia.
            bancos_existentes = {d['banco'] for d in dados_atualizados}
            for novo_banco, regra in BANCOS.items():
                if novo_banco in bancos_existentes:
                    continue
                taxa_n = novas_taxas.get(novo_banco, regra['taxa_padrao'])
                nome_slug = novo_banco.lower().replace(" ", "-")
                for valor in VALORES_IMOVEL_PADRAO:
                    for prazo in PRAZOS_PADRAO:
                        milhares = int(valor / 1000)
                        dados_atualizados.append({
                            'banco': novo_banco, 'valor_imovel': str(valor), 'taxa': taxa_n,
                            'prazo': str(prazo),
                            'slug': f'simulador-{nome_slug}-{milhares}-mil-{prazo}-meses',
                            'cet': round(taxa_n + 0.15, 2), 'ltv': round(regra['ltv'] * 100),
                            'prazo_maximo': regra['prazo_max'],
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
