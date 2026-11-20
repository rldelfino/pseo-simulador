# Conferência dos números — 20/11/2026

## 1. Taxas por banco x Banco Central

Período mais recente do BCB: 2026-10-01.

| Banco | dados.csv (a.a.) | BCB a.a. | BCB a.m. | (1+a.m.)^12-1 | Último mês em historico_taxas.csv | Fonte no cache | Situação |
|---|---|---|---|---|---|---|---|
| Caixa | 11,97 | 11,97 | 0,95 | 12,01 | 2026-10 = 11,97 | BCB | confere |
| Banco do Brasil | 14,42 | 14,42 | 1,13 | 14,44 | 2026-10 = 14,42 | BCB | confere |
| Santander | 12,32 | 12,32 | 0,97 | 12,28 | 2026-10 = 12,32 | BCB | confere |
| BRB | 11,36 | — | — | — | — | blog/estimativa | sem linha no BCB (modalidade não cobre): NÃO verificável aqui |
| Poupex | 10,80 | — | — | — | — | bancos.py (estático) | sem linha no BCB (modalidade não cobre): NÃO verificável aqui |
| Itau | 12,22 | 12,22 | 0,97 | 12,28 | 2026-10 = 12,22 | BCB | confere |
| Bradesco | 12,27 | 12,27 | 0,97 | 12,28 | 2026-10 = 12,27 | BCB | confere |
| Banco Inter | 12,97 | 12,97 | 1,02 | 12,95 | 2026-10 = 12,97 | BCB | confere |
| Sicredi | 12,23 | 12,23 | 0,97 | 12,28 | 2026-10 = 12,23 | BCB | confere |
| Sicoob | 10,93 | 10,93 | 0,87 | 10,95 | 2026-10 = 10,93 | BCB | confere |
| Banrisul | 10,49 | 10,49 | 0,83 | 10,43 | 2026-10 = 10,49 | BCB | confere |

## 2. Conta: PRICE e SAC recalculados do zero

| Financiado | Prazo | Taxa a.a. | PRICE (fórmula) | PRICE (site) | SAC 1ª (fórmula) | SAC 1ª (site) | SAC total (tabela) | SAC total (site) |
|---|---|---|---|---|---|---|---|---|
| 400000 | 360 | 11,97 | 3918.34 | 3918.34 | 4897.61 | 4897.61 | 1083463.75 | 1083463.75 |
| 250000 | 120 | 12,32 | 3539.90 | 3539.90 | 4515.54 | 4515.54 | 397148.60 | 397148.60 |
| 900000 | 420 | 14,42 | 10251.73 | 10251.73 | 12302.70 | 12302.70 | 3038647.49 | 3038647.49 |
| 150000 | 180 | 10,00 | 1572.59 | 1572.59 | 2029.45 | 2029.45 | 258248.96 | 258248.96 |
| 640000 | 300 | 12,97 | 6862.67 | 6862.67 | 8670.61 | 8670.61 | 1623859.80 | 1623859.80 |

Maior diferença entre a fórmula e o site: R$ 0.000000.

Efeito da correção (Caixa, R$ 400 mil, 360 meses, 11,97% a.a.): a taxa mensal passou de 0.9975% (a.a. ÷ 12) para 0.9466% (equivalente composta, igual ao 0,95% a.m. que o próprio BCB publica); a parcela PRICE caiu de R$ 4105.22 para R$ 3918.34 (-4.6%).

## 3. Datas de atualização

- ultima_atualizacao_taxas.txt: 2026-11-20 (dia em que o robô gravou as taxas).
- Datas mostradas em banco-caixa.html: 20/11/2026.
- Último mês no histórico: 2026-10-01.
- Lembrete: o site diz "taxas atualizadas em <dia do robô>", mas a taxa é a média do mês fechado do BCB (o mês anterior ao do robô). O texto já fala em "média de mês/ano"; conferir se nenhum trecho chama a taxa de "de hoje".

