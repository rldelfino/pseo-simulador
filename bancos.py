"""
Fonte única de verdade das regras de negócio por instituição financeira.

Tanto o etl_taxas.py (atualização mensal de taxas) quanto o gerador.py
(geração das páginas pSEO) importam deste módulo. Isso elimina a
duplicação que existia antes (regras hardcoded em dois arquivos
diferentes, que podiam divergir silenciosamente).

Para adicionar um banco novo: basta uma entrada aqui. Nada mais precisa
ser tocado em etl_taxas.py ou gerador.py.
"""

import unicodedata

# chave = identidade estável do banco (sem acento, usada em slugs/CSV/URLs)
# nome_exibicao = como o nome aparece no texto (com acento, gramaticalmente correto)
BANCOS = {
    "Caixa": {
        "nome_exibicao": "Caixa",
        "taxa_padrao": 11.49, "ltv": 0.80, "prazo_max": 420,
        "mod": "Financiamento Imobiliário", "dominio_favicon": "caixa.gov.br",
    },
    "Banco do Brasil": {
        "nome_exibicao": "Banco do Brasil",
        "taxa_padrao": 11.69, "ltv": 0.80, "prazo_max": 420,
        "mod": "Financiamento Imobiliário", "dominio_favicon": "bb.com.br",
    },
    "Santander": {
        "nome_exibicao": "Santander",
        # Corrigido de 13.39 para 11.69 — mesma correção de metodologia do
        # Banco Inter (taxa típica de mercado, não uma estimativa alta
        # demais). Fonte: comparativo de mercado, ago/2026.
        "taxa_padrao": 11.69, "ltv": 0.80, "prazo_max": 420,
        "mod": "Financiamento Imobiliário", "dominio_favicon": "santander.com.br",
    },
    "BRB": {
        "nome_exibicao": "BRB",
        "taxa_padrao": 11.25, "ltv": 0.80, "prazo_max": 420,
        "mod": "Financiamento Imobiliário", "dominio_favicon": "brb.com.br",
    },
    "Poupex": {
        "nome_exibicao": "Poupex",
        "taxa_padrao": 10.80, "ltv": 0.90, "prazo_max": 420,
        "mod": "Financiamento Imobiliário", "dominio_favicon": "poupex.com.br",
    },
    "Itau": {
        "nome_exibicao": "Itaú",
        # Corrigido de 13.09 para 11.60 (mesma correção de metodologia).
        "taxa_padrao": 11.60, "ltv": 0.80, "prazo_max": 360,
        "mod": "Financiamento Imobiliário", "dominio_favicon": "itau.com.br",
    },
    "Bradesco": {
        "nome_exibicao": "Bradesco",
        # Corrigido de 13.50 para 11.70 (mesma correção de metodologia).
        "taxa_padrao": 11.70, "ltv": 0.80, "prazo_max": 360,
        "mod": "Financiamento Imobiliário", "dominio_favicon": "bradesco.com.br",
    },
    "Banco Inter": {
        "nome_exibicao": "Banco Inter",
        # Corrigido de 9.50 (taxa mínima "a partir de" anunciada pelo Inter,
        # sujeita a aprovação de crédito) para 13.76 — taxa típica/realista
        # de mercado, na mesma metodologia usada pros demais bancos da
        # matriz (que já usam a taxa padrão típica, não a promocional
        # mínima). Fonte: comparativo de mercado, ago/2026.
        "taxa_padrao": 13.76, "ltv": 0.80, "prazo_max": 360,
        "mod": "Financiamento Imobiliário", "dominio_favicon": "bancointer.com.br",
    },
    "Sicredi": {
        "nome_exibicao": "Sicredi",
        "taxa_padrao": 11.50, "ltv": 0.80, "prazo_max": 360,
        "mod": "Financiamento Imobiliário", "dominio_favicon": "sicredi.com.br",
    },
    "Sicoob": {
        "nome_exibicao": "Sicoob",
        "taxa_padrao": 11.50, "ltv": 0.80, "prazo_max": 360,
        "mod": "Financiamento Imobiliário", "dominio_favicon": "sicoob.com.br",
    },
    "Banrisul": {
        "nome_exibicao": "Banrisul",
        "taxa_padrao": 11.60, "ltv": 0.75, "prazo_max": 360,
        "mod": "Financiamento Imobiliário", "dominio_favicon": "banrisul.com.br",
    },
    "C6 Bank": {
        "nome_exibicao": "C6 Bank",
        "taxa_padrao": 13.50, "ltv": 0.60, "prazo_max": 240,
        "mod": "Crédito com Garantia de Imóvel", "dominio_favicon": "c6bank.com.br",
    },
    "Bari": {
        "nome_exibicao": "Bari",
        "taxa_padrao": 15.25, "ltv": 0.60, "prazo_max": 360,
        "mod": "Crédito com Garantia de Imóvel", "dominio_favicon": "bancobari.com.br",
    },
    "Cash Me": {
        "nome_exibicao": "Cash Me",
        "taxa_padrao": 16.63, "ltv": 0.60, "prazo_max": 360,
        "mod": "Crédito com Garantia de Imóvel", "dominio_favicon": "cashme.com.br",
    },
    "Daycoval": {
        "nome_exibicao": "Daycoval",
        "taxa_padrao": 16.63, "ltv": 0.60, "prazo_max": 360,
        "mod": "Crédito com Garantia de Imóvel", "dominio_favicon": "daycoval.com.br",
    },
}

REGRA_FALLBACK = {
    "nome_exibicao": None, "taxa_padrao": 11.99, "ltv": 0.80,
    "prazo_max": 360, "mod": "Financiamento Imobiliário", "dominio_favicon": "google.com",
}


def normalizar_chave(nome):
    """Remove acentos/caixa para permitir lookup tolerante (ex: 'Itaú' -> 'Itau')."""
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii")
    return sem_acento.strip()


_INDICE_NORMALIZADO = {normalizar_chave(k): k for k in BANCOS}


def obter_regra(nome_banco):
    """Busca a regra do banco tolerando variações de acentuação (Itau/Itaú)."""
    if nome_banco in BANCOS:
        return BANCOS[nome_banco]
    chave_normalizada = normalizar_chave(nome_banco)
    if chave_normalizada in _INDICE_NORMALIZADO:
        return BANCOS[_INDICE_NORMALIZADO[chave_normalizada]]
    regra = dict(REGRA_FALLBACK)
    regra["nome_exibicao"] = nome_banco
    return regra


def nome_exibicao(nome_banco):
    regra = obter_regra(nome_banco)
    return regra["nome_exibicao"] or nome_banco
