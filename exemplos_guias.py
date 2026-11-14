"""
Exemplos calculados para os guias de /aprenda que eram só texto (13/nov/2026).

Por que existe: o Google pergunta se o conteúdo traz "análise original" e "valor substancial em relação às outras
páginas"; o Bing diz que páginas finas perdem elegibilidade. Os números abaixo saem do MESMO cálculo do simulador
(calcular_sac_price e calcular_cet_real), então são conferíveis e não existem em guia de ninguém. São hipotéticos:
a taxa é um exemplo, não oferta, e o cálculo não inclui seguros e tarifas (exceto no CET, que os inclui por
estimativa de mercado).

montar_exemplos(calc, reais) recebe as funções do gerador (evita import circular) e devolve {slug: html}.
"""
from guias_novos import _H2, _a, _b

TAXA = 11.5  # % ao ano, exemplo


def _pct(v):
    return f"{v:.2f}".replace(".", ",")


def _sac_com_extra(saldo, prazo, taxa_aa, mes_extra, extra, modo):
    """SAC com um pagamento extra logo após a parcela `mes_extra`. modo 'prazo' mantém a amortização mensal e
    encurta o contrato; 'parcela' mantém o prazo e reduz as parcelas seguintes. Devolve (juros_totais, meses, 1ª parcela depois)."""
    i = (taxa_aa / 100) / 12
    amort = saldo / prazo
    juros = 0.0
    for _ in range(mes_extra):
        juros += saldo * i
        saldo -= amort
    saldo -= extra
    if modo == "prazo":
        restantes = int(-(-(saldo / amort - 1e-9) // 1))  # tolerância: evita 300,00000000000006 virar 301
        primeira = amort + saldo * i
        for _ in range(restantes):
            juros += saldo * i
            saldo = max(saldo - amort, 0.0)
        return juros, mes_extra + restantes, primeira
    restantes = prazo - mes_extra
    novo = saldo / restantes
    primeira = novo + saldo * i
    for _ in range(restantes):
        juros += saldo * i
        saldo -= novo
    return juros, prazo, primeira


def montar_exemplos(calc, reais):
    ex = {}

    # ---- SAC x Price
    r = calc(300_000, 360, TAXA)
    ex["aprenda-sac-x-price"] = _H2.format(t="Exemplo calculado: R$ 300 mil em 30 anos", c=(
        f"<p>Um exemplo hipotético, calculado como o simulador calcula (sem seguros e tarifas): financiar {_b('R$ 300.000')} em "
        f"{_b('360 meses')} a {_b(_pct(TAXA) + '% ao ano')}.</p>"
        f'<ul class="list-disc pl-6 space-y-2">'
        f"<li>{_b('SAC:')} a primeira parcela é de {_b(reais(r['p1_sac']))} e cai todo mês até {_b(reais(r['pU_sac']))} na última. Total pago: {reais(r['total_sac'])}.</li>"
        f"<li>{_b('Price:')} a parcela é de {_b(reais(r['p1_price']))} do primeiro ao último mês. Total pago: {reais(r['total_price'])}.</li>"
        f"</ul>"
        f"<p>Na prática: a primeira parcela do SAC é {_b(reais(r['p1_sac'] - r['p1_price']))} maior que a da Price, mas o SAC custa "
        f"{_b(reais(r['economia_sac']))} a menos em juros ao longo do contrato. Se a parcela inicial do SAC não cabe no orçamento, a Price pode "
        f"ser a única que o banco aprova; veja a {_a('renda-para-financiar-imovel', 'renda mínima por valor')} e simule o seu caso no "
        f"{_a('comparador-bancos', 'comparador de bancos')}.</p>"))

    # ---- LTV
    linhas = []
    for ltv in (70, 80):
        fin = 500_000 * ltv / 100
        c = calc(fin, 360, TAXA)
        linhas.append(f"<li>{_b(f'LTV de {ltv}%:')} entrada de {_b(reais(500_000 - fin))}, financiamento de {reais(fin)}. "
                      f"Primeira parcela (SAC): {reais(c['p1_sac'])}; total pago: {reais(c['total_sac'])}.</li>")
    ex["aprenda-ltv-financiamento-imobiliario"] = _H2.format(t="Exemplo calculado: imóvel de R$ 500 mil", c=(
        f"<p>Um exemplo hipotético, calculado como o simulador calcula (360 meses a {_pct(TAXA)}% ao ano, SAC, sem seguros e tarifas). "
        f"Quanto maior o LTV, menor a entrada, mas maior a parcela e o total de juros:</p>"
        f'<ul class="list-disc pl-6 space-y-2">{"".join(linhas)}</ul>'
        f"<p>A cota que cada banco financia varia com o sistema e com a política da instituição; confirme no banco antes de planejar a entrada. "
        f"Para ver o seu valor, use o {_a('comparador-bancos', 'comparador de bancos')}.</p>"))

    # ---- Amortização extraordinária
    s, n, k, extra = 300_000, 360, 24, 30_000
    base = calc(s, n, TAXA)
    j_base = base["total_sac"] - s
    j_prazo, m_prazo, p_prazo = _sac_com_extra(s, n, TAXA, k, extra, "prazo")
    j_parc, m_parc, p_parc = _sac_com_extra(s, n, TAXA, k, extra, "parcela")
    ex["aprenda-amortizacao-extraordinaria"] = _H2.format(t="Exemplo calculado: R$ 30 mil a mais depois de 2 anos", c=(
        f"<p>Um exemplo hipotético (SAC, {_b('R$ 300.000')} em {_b('360 meses')} a {_pct(TAXA)}% ao ano, sem seguros e tarifas). Sem amortizar, "
        f"você paga {_b(reais(j_base))} de juros. Depois de pagar a 24ª parcela, você coloca {_b(reais(extra))} a mais:</p>"
        f'<ul class="list-disc pl-6 space-y-2">'
        f"<li>{_b('Reduzindo o prazo:')} o contrato termina em {_b(f'{m_prazo} meses')} (em vez de 360), a parcela segue no mesmo ritmo e os juros caem para "
        f"{reais(j_prazo)}, uma economia de {_b(reais(j_base - j_prazo))}.</li>"
        f"<li>{_b('Reduzindo a parcela:')} o prazo fica em 360 meses, a parcela seguinte cai para {_b(reais(p_parc))} e os juros caem para "
        f"{reais(j_parc)}, uma economia de {_b(reais(j_base - j_parc))}.</li></ul>"
        f"<p>Encurtar o prazo economiza mais juros; reduzir a parcela alivia o orçamento mensal. Confirme com o banco como ele aplica o abatimento."
        f" A simulação de amortização está em qualquer {_a('comparador-bancos', 'simulação do site')}.</p>"))

    # ---- CET
    c = calc(400_000, 360, TAXA, 500_000)
    ex["aprenda-cet-iof-financiamento-imobiliario"] = _H2.format(t="Exemplo calculado: da taxa de juros ao CET", c=(
        f"<p>Um exemplo hipotético com o cálculo do simulador: imóvel de {_b('R$ 500.000')}, financiamento de {_b('R$ 400.000')} em "
        f"{_b('360 meses')} com taxa de juros de {_b(_pct(TAXA) + '% ao ano')}. Somando seguro MIP, seguro DFI e tarifa de administração (valores "
        f"estimados de mercado, que variam por banco e por pessoa), o CET fica em {_b(_pct(c['cet_sac']) + '% ao ano')} no SAC e "
        f"{_b(_pct(c['cet_price']) + '% ao ano')} na Price.</p>"
        f"<p>Ou seja, o custo real é {_b(_pct(c['cet_sac'] - TAXA) + ' pontos percentuais')} acima da taxa anunciada. É por isso que a comparação "
        f"entre bancos deve ser feita pelo CET que consta na proposta, e não só pela taxa de juros.</p>"))
    return ex
