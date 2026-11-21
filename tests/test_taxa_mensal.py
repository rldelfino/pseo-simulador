"""A taxa anual do Banco Central é efetiva (juros compostos): a taxa mensal é (1 + a.a.)^(1/12) - 1, não a.a. / 12.

Conferido em 20/11/2026 na API do BCB (modalidade 903201, outubro/2026): Caixa 0,95% a.m. = 11,97% a.a.; Banco do Brasil 1,13% a.m. = 14,42% a.a.
Dividir por 12 dava 0,9975% a.m. para a Caixa e inflava a parcela em cerca de 5%.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gerador import calcular_sac_price, taxa_mensal_equivalente


@pytest.mark.parametrize("aa, am_bcb", [(11.97, 0.95), (14.42, 1.13), (10.93, 0.87), (12.97, 1.02)])
def test_taxa_mensal_bate_com_a_mensal_publicada_pelo_bcb(aa, am_bcb):
    assert round(taxa_mensal_equivalente(aa) * 100, 2) == pytest.approx(am_bcb, abs=0.011)


def test_composta_de_volta_da_a_taxa_anual():
    assert (1 + taxa_mensal_equivalente(11.97)) ** 12 - 1 == pytest.approx(0.1197, abs=1e-12)


def test_price_pela_formula_fechada():
    fin, n, aa = 400_000, 360, 11.97
    i = (1 + aa / 100) ** (1 / 12) - 1
    esperado = fin * i / (1 - (1 + i) ** -n)
    assert calcular_sac_price(fin, n, aa)["p1_price"] == pytest.approx(esperado, rel=1e-12)
    assert esperado == pytest.approx(3918.34, abs=0.01)  # com a.a./12 dava R$ 4.105,22
