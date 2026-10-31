---
license: cc-by-4.0
language:
- pt
pretty_name: Taxas de financiamento imobiliário por banco (Brasil, BACEN)
size_categories:
- n<1K
task_categories:
- tabular-regression
tags:
- finance
- brazil
- interest-rates
- real-estate
---

# Taxas médias de juros do financiamento imobiliário por banco (BACEN)

Taxa média mensal de juros efetivamente contratada no financiamento imobiliário (aquisição de imóveis, pessoa física, taxa pré-fixada), por banco, em % ao ano, segundo o Banco Central do Brasil. Cobre 24 meses (out/24 a set/26) e 9 instituições.

## Colunas
- `periodo_inicio`, `periodo_fim`: primeiro e último dia do mês de referência.
- `instituicao`: banco.
- `taxa_juros_aa_pct`: taxa média efetivamente contratada, em % ao ano.

## Cobertura
outubro de 2024 a setembro de 2026; 9 instituições: Banco Inter, Banco do Brasil, Banrisul, Bradesco, Caixa, Itaú, Santander, Sicoob, Sicredi.

## Fonte e licença
Banco Central do Brasil (API pública de taxas de juros, modalidade 903201). Licença CC BY 4.0: cite "Datalab Global (https://simulador.datalabglobal.com/dados-abertos)". Atualizado todo mês.
