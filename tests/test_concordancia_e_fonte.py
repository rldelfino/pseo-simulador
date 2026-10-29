"""
Concordância de gênero dos bancos femininos ("a Caixa", "a Poupex") e
rótulo de fonte da taxa por banco — achados da auditoria de SEO de
29/out/2026 (ver comentários em bancos.py e gerador.py).

A parte que lê paginas_seo/ roda só se a pasta já foi gerada
(python gerador.py); as funções puras rodam sempre.
"""
import json
import os
import re

import pytest

from bancos import BANCOS, corrigir_concordancia, eh_feminino

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_SAIDA = os.path.join(RAIZ, "paginas_seo")


@pytest.mark.parametrize("entrada, esperado", [
    ("pelo Caixa em 24 meses", "pela Caixa em 24 meses"),
    ("O Caixa permite até 420 meses", "A Caixa permite até 420 meses"),
    ("aqui no Poupex está em 12%", "aqui na Poupex está em 12%"),
    ("do Caixa e do Itaú", "da Caixa e do Itaú"),
    ("No Poupex", "Na Poupex"),
    ("ao Caixa", "à Caixa"),
    # não pode tocar em banco masculino, slug ou nome composto
    ("pelo Sicredi e o Banco do Brasil", "pelo Sicredi e o Banco do Brasil"),
    ("/simulador-caixa-150-mil-120-meses", "/simulador-caixa-150-mil-120-meses"),
    ("Imobiliário Caixa", "Imobiliário Caixa"),
])
def test_corrigir_concordancia(entrada, esperado):
    assert corrigir_concordancia(entrada) == esperado


def test_bancos_femininos_existem_em_bancos():
    assert eh_feminino("Caixa") and eh_feminino("Poupex")
    assert not eh_feminino("Itau") and not eh_feminino("Sicredi")
    assert all(b in BANCOS for b in ("Caixa", "Poupex"))


@pytest.mark.skipif(not os.path.isdir(PASTA_SAIDA), reason="paginas_seo/ não gerada")
def test_paginas_nao_tem_artigo_masculino_diante_de_banco_feminino():
    ruim = re.compile(r"\b(pelo|do|no|ao|o)\s+(Caixa|Poupex)\b", re.IGNORECASE)
    erros = []
    for nome in os.listdir(PASTA_SAIDA):
        if not nome.endswith(".html"):
            continue
        with open(os.path.join(PASTA_SAIDA, nome), encoding="utf-8") as f:
            texto = f.read()
        for m in ruim.finditer(texto):
            if m.group(2) in ("Caixa", "Poupex"):
                erros.append((nome, m.group(0)))
    assert not erros, erros[:5]


@pytest.mark.skipif(not os.path.isdir(PASTA_SAIDA), reason="paginas_seo/ não gerada")
def test_rodape_nao_atribui_ao_bacen_taxa_que_nao_e_do_bacen():
    cache_path = os.path.join(RAIZ, "taxas_cache.json")
    cache = json.load(open(cache_path, encoding="utf-8")) if os.path.exists(cache_path) else {}
    nao_bacen = [b for b in BANCOS if "bcb.gov.br" not in str(cache.get(b, {}).get("fonte", ""))]
    for banco in nao_bacen:
        slug = banco.lower().replace(" ", "-")
        alvo = os.path.join(PASTA_SAIDA, f"banco-{slug}.html")
        if not os.path.exists(alvo):
            continue
        texto = open(alvo, encoding="utf-8").read()
        assert "Fonte: Banco Central do Brasil (BACEN)<" not in texto, banco
        assert "não é taxa oficial do BACEN" in texto, banco


@pytest.mark.skipif(not os.path.isdir(PASTA_SAIDA), reason="paginas_seo/ não gerada")
def test_rodape_mostra_identidade_da_empresa():
    # mesmo texto já publicado no hub (www.datalabglobal.com): site YMYL
    # precisa dizer quem está por trás; e nenhum placeholder pode vazar.
    faltando = []
    for nome in os.listdir(PASTA_SAIDA):
        if not nome.endswith(".html") or nome == "404.html":
            continue
        texto = open(os.path.join(PASTA_SAIDA, nome), encoding="utf-8").read()
        assert "{EMPRESA_RODAPE}" not in texto, nome
        if "CNPJ 63.998.502/0001-73" not in texto:
            faltando.append(nome)
    assert not faltando, faltando[:5]
