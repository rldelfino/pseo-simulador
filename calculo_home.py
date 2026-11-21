"""Conta de referência da home (simulador novo). `src/calculo_home.js` faz a mesma conta no navegador; os testes comparam as duas.

Regras (as mesmas do resto do site, ver /metodologia):
- A taxa anual é efetiva (a do Banco Central é anualizada por juros compostos): taxa mensal = (1 + a.a.)^(1/12) - 1.
  Se a pessoa digita a taxa NOMINAL de uma proposta, a taxa mensal é a.a. / 12.
- SAC: amortização constante; PRICE: parcela fixa. Sem TR, sem IOF.
- CET por TIR do fluxo, com seguro MIP (0,030% do saldo por mês), DFI (0,0129% do valor do imóvel por mês) e tarifa de R$ 25/mês.
- Renda sugerida: primeira parcela / 30%, arredondada para cima ao múltiplo de R$ 50.
Independente de gerador.py (a home é gerada por ele, então importar o contrário criaria um ciclo). Python 3.10.
"""
import math

TAXA_MIP_MENSAL = 0.00030
TAXA_DFI_MENSAL = 0.000129
TARIFA_ADMIN_MENSAL = 25.0
RENDA_COMPROMETIDA = 0.30


def taxa_mensal(taxa_aa_pct, nominal=False):
    if nominal:
        return taxa_aa_pct / 100 / 12
    return (1 + taxa_aa_pct / 100) ** (1 / 12) - 1


def pmt(valor, i, n):
    if n <= 0:
        return 0.0
    if i > 0:
        return valor * (i * (1 + i) ** n) / ((1 + i) ** n - 1)
    return valor / n


def cet(financiado, meses, i, imovel, sistema):
    """CET em % ao ano (TIR do fluxo completo), duas casas, igual a gerador.calcular_cet_real."""
    if financiado <= 0 or meses <= 0:
        return 0.0
    saldo = financiado
    fixa = pmt(financiado, i, meses) if sistema == "price" else 0.0
    fluxo = []
    for _ in range(meses):
        juros = saldo * i
        amort = financiado / meses if sistema == "sac" else fixa - juros
        fluxo.append(amort + juros + saldo * TAXA_MIP_MENSAL + imovel * TAXA_DFI_MENSAL + TARIFA_ADMIN_MENSAL)
        saldo -= amort

    def vpl(r):
        total = -financiado
        f = 1.0 / (1 + r)
        d = 1.0
        for cf in fluxo:
            d *= f
            total += cf * d
        return total

    lo, hi = 0.0, 0.05
    for _ in range(60):
        mid = (lo + hi) / 2
        if vpl(mid) > 0:
            lo = mid
        else:
            hi = mid
    tir = (lo + hi) / 2
    return round(((1 + tir) ** 12 - 1) * 100, 2)


def simular(imovel, entrada, anos, taxa_aa_pct, sistema="sac", nominal=False):
    """Devolve os números do cenário. `entrada` em reais (já limitada pelo chamador ao mínimo do banco)."""
    meses = int(round(anos * 12))
    financiado = max(0.0, imovel - entrada)
    i = taxa_mensal(taxa_aa_pct, nominal)
    amort = financiado / meses if meses else 0.0
    juros_sac = 0.0
    saldo = financiado
    for _ in range(meses):
        juros_sac += saldo * i
        saldo -= amort
    if sistema == "sac":
        p1 = amort + financiado * i
        pu = amort * (1 + i)
        juros = juros_sac
    else:
        p1 = pu = pmt(financiado, i, meses)
        juros = p1 * meses - financiado
    return {
        "meses": meses, "financiado": financiado, "i": i, "p1": p1, "pu": pu,
        "total": financiado + juros, "juros": juros,
        "cet": cet(financiado, meses, i, imovel, sistema),
        "renda": math.ceil((p1 / RENDA_COMPROMETIDA) / 50) * 50 if financiado > 0 else 0,
        "ltv": financiado / imovel if imovel else 0.0,
    }


def amortizar_antes(financiado, i, meses, sistema, extra, unico, mes_unico, modo):
    """Efeito de pagar a mais: `extra` por mês (a partir da 1ª parcela) e/ou `unico` de uma vez no começo do mês `mes_unico`
    (0 = antes da 1ª parcela). modo 'prazo' mantém a amortização (SAC) ou a parcela (PRICE) e encurta o contrato;
    'parcela' recalcula a parcela para o prazo que sobrou. Devolve juros totais, meses até quitar e a parcela depois do pagamento único."""
    saldo = float(financiado)
    amort = financiado / meses if meses else 0.0
    fixa = pmt(financiado, i, meses)
    juros_tot = 0.0
    m = 0
    nova = fixa if sistema == "price" else amort + saldo * i
    while saldo > 0.005 and m < meses * 2:
        if unico > 0 and m == mes_unico:
            saldo -= unico
            if saldo <= 0.005:
                saldo = 0.0
                break
            if modo == "parcela":
                resta = max(1, meses - m)
                amort = saldo / resta
                fixa = pmt(saldo, i, resta)
            nova = fixa if sistema == "price" else amort + saldo * i
        j = saldo * i
        juros_tot += j
        a = min(amort, saldo) if sistema == "sac" else min(fixa - j, saldo)
        a = min(a + extra, saldo)
        saldo -= a
        m += 1
    return {"juros": juros_tot, "meses": m, "parcela_nova": nova}


def amortizacao_anual(financiado, i, meses, sistema):
    """Por ano: juros pagos, amortização e saldo devedor no fim do ano (parcelas mensais, sem pagar a mais)."""
    saldo = float(financiado)
    amort = financiado / meses if meses else 0.0
    fixa = pmt(financiado, i, meses)
    linhas = []
    juros_a = amort_a = 0.0
    for m in range(1, meses + 1):
        j = saldo * i
        a = amort if sistema == "sac" else fixa - j
        juros_a += j
        amort_a += a
        saldo -= a
        if m % 12 == 0 or m == meses:
            linhas.append({"ano": (m + 11) // 12, "juros": juros_a, "amortizacao": amort_a, "saldo": max(saldo, 0.0)})
            juros_a = amort_a = 0.0
    return linhas
