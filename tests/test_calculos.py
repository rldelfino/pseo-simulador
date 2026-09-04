"""
Testes de regressão pro motor de cálculo (gerador.py) e pra matriz de
bancos (bancos.py).

Por que isso existe: ao longo do desenvolvimento, vários bugs sutis de
cálculo/dado só foram achados por inspeção manual de páginas geradas (o
aporte fixo de amortização que não escalava com o financiamento, o CET
formatado sem a segunda casa decimal, o Banco Inter com a taxa mínima
promocional em vez da taxa típica, a caixinha de comparação de mercado que
ficava "congelada" no cenário padrão). Esses testes não substituem a
inspeção visual pra mudanças de design, mas travam a MATEMÁTICA — o tipo
de bug que é fácil de reintroduzir sem perceber ao mexer em outra coisa.

Rodar com: python3 -m pytest tests/ -v
(precisa estar na raiz do projeto, pois os módulos importados usam paths
relativos como 'dados.csv').
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gerador import calcular_cet_real, calcular_sac_price, comparar_todos_bancos, formatar_reais
from bancos import BANCOS


# ---------------------------------------------------------------------------
# calcular_cet_real
# ---------------------------------------------------------------------------

def test_cet_e_sempre_maior_que_a_taxa_nominal():
    """CET soma juros + seguros + taxa de administração — matematicamente
    tem que ficar acima da taxa de juros pura, sempre. Se isso falhar, a
    fórmula do CET quebrou (ex: um sinal trocado, um custo zerado)."""
    taxa_anual = 11.69
    cet = calcular_cet_real(400_000, 360, taxa_anual, 500_000, 'SAC')
    assert cet > taxa_anual


def test_cet_zero_quando_nao_ha_financiamento():
    assert calcular_cet_real(0, 360, 11.0, 500_000) == 0.0
    assert calcular_cet_real(400_000, 0, 11.0, 500_000) == 0.0


def test_cet_sac_e_price_ficam_proximos_mas_nao_iguais():
    """SAC e PRICE têm perfis de amortização diferentes, então o CET dos
    dois deve divergir (mesmo pouco) — se vierem idênticos, a função está
    ignorando o parâmetro `sistema`."""
    cet_sac = calcular_cet_real(400_000, 360, 11.69, 500_000, 'SAC')
    cet_price = calcular_cet_real(400_000, 360, 11.69, 500_000, 'PRICE')
    assert cet_sac != cet_price
    assert abs(cet_sac - cet_price) < 2.0  # divergência plausível, não descontrolada


def test_cet_escala_com_a_taxa_nominal():
    """Regressão direta do bug do Banco Inter: se a taxa nominal sobe, o
    CET tem que subir junto — nunca pode "ficar preso" independente da
    taxa de entrada."""
    cet_baixo = calcular_cet_real(400_000, 360, 9.50, 500_000, 'SAC')
    cet_alto = calcular_cet_real(400_000, 360, 13.76, 500_000, 'SAC')
    assert cet_alto > cet_baixo


# ---------------------------------------------------------------------------
# calcular_sac_price
# ---------------------------------------------------------------------------

def test_sac_tem_menos_juros_totais_que_price():
    """Verdade matemática conhecida: em SAC a amortização é constante e o
    saldo devedor cai mais rápido no início, então o total de juros pagos
    é sempre menor ou igual ao do PRICE (parcela fixa)."""
    r = calcular_sac_price(400_000, 360, 11.69)
    assert r["total_sac"] <= r["total_price"]
    assert r["economia_sac"] >= 0


def test_sac_primeira_parcela_maior_que_ultima():
    """Em SAC, a amortização é fixa e os juros caem mês a mês — logo a
    parcela é decrescente."""
    r = calcular_sac_price(400_000, 360, 11.69)
    assert r["p1_sac"] > r["pU_sac"]


def test_price_parcela_e_fixa():
    r = calcular_sac_price(400_000, 360, 11.69)
    assert r["p1_price"] == r["pU_price"]


def test_renda_sugerida_so_aparece_com_valor_imovel():
    sem_imovel = calcular_sac_price(400_000, 360, 11.69)
    assert "renda_sugerida" not in sem_imovel

    com_imovel = calcular_sac_price(400_000, 360, 11.69, valor_imovel=500_000)
    assert "renda_sugerida" in com_imovel
    assert "cet_sac" in com_imovel and "cet_price" in com_imovel


def test_renda_sugerida_cobre_pelo_menos_30_por_cento_da_parcela():
    """A regra de comprometimento de renda diz que a parcela não pode
    passar de 30% da renda — logo renda_sugerida * 0.30 tem que ser >= à
    primeira parcela SAC (a suposta pior parcela usada como referência)."""
    r = calcular_sac_price(400_000, 360, 11.69, valor_imovel=500_000)
    assert r["renda_sugerida"] * 0.30 >= r["p1_sac"]


# ---------------------------------------------------------------------------
# comparar_todos_bancos
# ---------------------------------------------------------------------------

def test_ranking_bancos_vem_ordenado_por_cet():
    ranking = comparar_todos_bancos(500_000, 360, lookup_paginas={})
    cets = [r["cet"] for r in ranking]
    assert cets == sorted(cets)


def test_ranking_bancos_cobre_todos_os_bancos_elegiveis():
    """Todo banco com LTV < 100% deveria aparecer no ranking pra um valor
    de imóvel razoável (nenhum banco tem entrada mínima >= 100%)."""
    ranking = comparar_todos_bancos(500_000, 360, lookup_paginas={})
    bancos_no_ranking = {r["banco"] for r in ranking}
    assert bancos_no_ranking == set(BANCOS.keys())


def test_ranking_bancos_respeita_prazo_maximo_de_cada_banco():
    ranking = comparar_todos_bancos(500_000, 999, lookup_paginas={})
    for r in ranking:
        prazo_max_banco = BANCOS[r["banco"]]["prazo_max"]
        assert r["prazo"] <= prazo_max_banco


# ---------------------------------------------------------------------------
# formatar_reais
# ---------------------------------------------------------------------------

def test_formatar_reais_sempre_duas_casas_decimais():
    """Regressão do bug de formatação: str(round(x,2)) derrubava o zero à
    direita (12.70 virava '12.7'). formatar_reais precisa sempre devolver
    2 casas decimais."""
    assert formatar_reais(1000) == "R$ 1.000,00"
    assert formatar_reais(1000.7) == "R$ 1.000,70"


# ---------------------------------------------------------------------------
# bancos.py — trava de regressão pras correções de taxa desta sessão
# ---------------------------------------------------------------------------

def test_taxas_corrigidas_nao_regridem_para_o_valor_antigo():
    """Trava específica: Inter, Santander, Itaú e Bradesco tiveam a taxa
    corrigida de um valor promocional/alto demais pra taxa típica de
    mercado. Se algum desses voltar ao valor antigo (ex: um merge mal
    resolvido), este teste avisa antes de ir pra produção."""
    valores_antigos_incorretos = {
        "Banco Inter": 9.50,
        "Santander": 13.39,
        "Itau": 13.09,
        "Bradesco": 13.50,
    }
    for banco, taxa_antiga in valores_antigos_incorretos.items():
        assert BANCOS[banco]["taxa_padrao"] != taxa_antiga, (
            f"{banco} voltou pra taxa antiga incorreta ({taxa_antiga}%) — "
            f"verifique se um merge não sobrescreveu a correção."
        )


def test_todo_banco_tem_taxa_plausivel():
    for banco, dados in BANCOS.items():
        taxa = dados["taxa_padrao"]
        assert 5.0 <= taxa <= 25.0, f"{banco} com taxa implausível: {taxa}%"
        assert 0 < dados["ltv"] <= 1.0, f"{banco} com LTV implausível: {dados['ltv']}"
        assert dados["prazo_max"] > 0
