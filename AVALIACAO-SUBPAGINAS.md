# Avaliação das subpáginas do simulador imobiliário

**Status: recomendação aprovada pelo dono e aplicada em 20/11/2026 (PR do enxugamento).** O texto abaixo é a avaliação original, feita antes de apagar qualquer coisa. O que mudou depois: o mapa de 301 foi para `paginas_seo/_redirects` (138 regras: 119 estáticas e 19 com curinga) e `proposta-redirects-subpaginas.txt` foi removido; `conferir_redirects.py` e `tests/test_redirects.py` conferem limites, destinos, loops e cobertura das 1.799 páginas removidas.

Feita em 20/11/2026, **sem apagar nem redirecionar nada**. Dados do Search Console (propriedade de domínio `sc-domain:datalabglobal.com`, atualização do relatório de indexação em 15/11/2026; desempenho dos últimos 3 meses, filtrado por `simulador.datalabglobal.com`) e medições nos arquivos gerados em `paginas_seo/`.

## Conclusão em três linhas

1. **Enxugar, não deletar tudo.** O Google não indexou quase nada do que o site tem em volume: das 167 URLs do sitemap, **1 está indexada** (`/comparador-bancos`), 24 foram rastreadas e recusadas, 141 nem foram rastreadas.
2. **Os cliques que existiram (14 em 3 meses) vieram todos das páginas `simulador-<banco>-<valor>-<prazo>`**, hoje em `noindex`. Nenhuma outra página do site recebeu clique.
3. Recomendo: **tirar a grade combinatória** (≈ 1.680 + 98 + 8 + 13 páginas), **manter ~60 páginas com função própria** e esperar 4 a 6 semanas para medir antes de decidir mais cortes.

## Dados

### Indexação (Search Console, 15/11/2026)

| Recorte | Indexadas | Não indexadas |
|---|---|---|
| Domínio inteiro (todos os subdomínios) | 1,55 mil | 17,5 mil |
| Só o sitemap `simulador.datalabglobal.com` (167 URLs) | **1** | **165** |

No recorte do simulador, os 165 se dividem em:

| Motivo | URLs | O que são |
|---|---|---|
| Detectada, mas não indexada (nunca rastreadas) | **141** | 108 comparações `financiamento-imobiliario-N-mil-M-anos`, 12 `renda-para-financiar-imovel-N-mil`, 11 `taxas-financiamento-imobiliario-<mês>`, 8 guias `aprenda-*`, `/imprensa`, `/incorporar` |
| Rastreada, mas não indexada | **24** | a home, os 11 hubs `banco-*`, o índice de renda, o índice de taxas, `taxas-...-setembro-2026`, `/dados-abertos`, `/financiamento-imobiliario`, 5 guias `aprenda-*`, `/sobre` e mais 1 |
| Indexada | **1** | `/comparador-bancos` (rastreada em 03/11) |

Domínio inteiro, motivos (inclui os outros subdomínios, não dá para separar): redirecionamento 3.346, 404 956, canônica alternativa 20, rastreada mas não indexada 9.671, `noindex` 804, 4xx 2, soft 404 1, erro 5xx 96, detectada mas não indexada 2.617.

Histórico do mesmo sitemap: o gráfico de páginas indexadas chegou a ~1,7 mil no início de setembro e foi caindo até 1; coincide com as mudanças já feitas no gerador (páginas de 420 meses de bancos de 360 viraram 301/404, grade para `noindex` e fora do sitemap em 13/11). A relação de causa não foi testada.

### Desempenho (3 meses, host `simulador.`)

| | Cliques | Impressões | Páginas com impressão |
|---|---|---|---|
| Total | **14** | **2,2 mil** (CTR 0,6%, posição média 17,9) | 483 |
| `simulador-*` (grade, hoje `noindex`) | 14 | ~2,18 mil | 477 |
| Todas as outras (hubs, guias, comparador, etc.) | **0** | 11 | 6 (`banco-caixa` 4, `sobre` 2, `banco-daycoval` 2, `banco-sicredi` 2, `banco-itau` 1) |

O pico foi de 30/08 a 03/09 (5 a 6 cliques por dia) e depois some. O comparador, único indexado, **não aparece com impressão** nesse período. Fonte do pico: páginas de 420 meses de bancos que só oferecem 360 (já corrigido no gerador).

## Qualidade (medido nos HTML gerados)

Texto visível, sem scripts. Similaridade = interseção/união de sequências de 5 palavras entre pares de páginas do mesmo tipo (300 pares sorteados).

| Tipo | Páginas | Palavras (mediana) | Similaridade mediana (máx.) | Observação |
|---|---|---|---|---|
| Home (nova) | 1 | 2.025 | — | texto próprio |
| Hub por banco `banco-*` | 11 | 1.074 | **0,55** (0,61) | números próprios do banco, mas mais da metade do texto é igual entre hubs |
| Comparação `financiamento-imobiliario-N-mil-M-anos` | 108 | 990 | **0,45** (0,61) | só muda valor, prazo e a tabela de bancos |
| Renda `renda-para-financiar-imovel-N-mil` | 12 | 736 | 0,35 (0,43) | número próprio (renda mínima), texto curto |
| Taxas mês a mês | 25 (13 indexáveis, 12 `noindex`) | 448 | 0,36 (0,44) | dado novo todo mês, texto curto |
| Guias `aprenda-*` | 12 | 637 (453 a 987) | **0,06** (0,11) | conteúdo próprio, é o que menos se repete |
| Grade `simulador-*` (`noindex`) | 1.680 | 2.318 | **0,58** (0,66) | duplicação em massa: 11 bancos x 28 valores x 6 prazos |

SEO técnico dos ~170 HTML (conferido): nenhum título acima de 60 caracteres, nenhuma descrição acima de 160, nenhuma página sem canonical, sem H1 ou com título repetido; JSON-LD presente (mediana de 1 a 4 blocos por tipo); os 13 meses antigos de taxas e toda a grade estão em `noindex,follow`. Ou seja: **o problema não é HTML mal feito, é volume e repetição**.

## Canibalização

- Dentro da grade (`simulador-*`) e entre as 108 comparações, as páginas disputam a mesma busca ("financiar R$ X em Y anos") com texto quase igual: o Google rastreou o padrão e não indexou nem a home (13/11).
- Hubs, comparador e home disputam "financiamento imobiliário <banco>" e "comparar bancos". **Não dá para medir canibalização por consulta**: as páginas não têm impressões suficientes. Tratar como risco, não como fato.

## As subpáginas ajudam a conversão?

- **Tráfego:** 0 cliques em 3 meses para qualquer página que não seja da grade. Hoje elas não trazem visita.
- **Conversão:** **não medi** (as métricas de clique no botão do parceiro estão no Umami, que não consultei). Sem visita, o efeito só poderia vir de navegação interna depois da home, e o caminho curto (home com simulador completo + tabela de bancos) já cobre isso.
- A home nova passa a ter o simulador, a tabela do mesmo financiamento em cada banco (com link para os hubs) e a tela de confirmação antes do parceiro: o papel que as páginas por valor faziam.

## Recomendação: **enxugar**

| Grupo | Hoje | Proposta | Por quê |
|---|---|---|---|
| Grade `simulador-<banco>-<valor>-<prazo>` | ~1.680 (`noindex`) | **301 para o hub do banco** (11 regras) e parar de gerar | duplicação 0,58, 0 tráfego atual, o simulador novo da home faz o mesmo |
| Comparação sem marca | 108 | **manter 10** (200, 300, 400, 500 e 700 mil x 20 e 30 anos); 98 vão por 301 para a mais próxima | intenção real ("financiar 300 mil em 30 anos"), mas 0 rastreadas e 0,45 de repetição |
| Renda para financiar | 12 + índice | **manter índice + 4** (200, 300, 500, 800 mil); 8 por 301 | número próprio, texto curto |
| Taxas mês a mês | 25 + índice | manter índice + 12 meses indexáveis; os 13 antigos (`noindex`) por 301 ao índice | dado fresco é o ativo; arquivos velhos só gastam rastreio |
| Hubs por banco | 11 | **manter**; reescrever ~40% do texto para tirar a repetição (hoje 0,55) | intenção por banco existe; falta texto próprio |
| Comparador, home, guias `aprenda-*` (12 + hub), dados abertos, metodologia, sobre, imprensa, incorporar, análise do mês | ~30 | **manter** | função própria; guias são o conteúdo menos repetido (0,06) |

Resultado: sitemap de **167 para ~60 URLs**; arquivos em `paginas_seo/` de ~1.890 para ~200 (a conta exata depende do que o gerador deixar de escrever).

Isso **não garante** indexação: o domínio é novo (setembro) e tem pouca autoridade, e a recusa pode vir mais de qualidade do que de quantidade. O corte tira o motivo mais óbvio (padrão combinatório) e concentra o rastreio. Reavaliar em 4 a 6 semanas.

### Mapa de redirecionamentos 301 (proposto, não aplicado)

Aplicado em [`paginas_seo/_redirects`](paginas_seo/_redirects) (119 regras estáticas + 19 com curinga, contando as 8 dos bancos de home equity que já existiam). Resumo:

| Origem | Destino |
|---|---|
| `/simulador-<banco>-*` (11 bancos) | `/banco-<banco>` |
| `/financiamento-imobiliario-V-mil-A-anos` (98 não mantidas) | a mantida mais próxima (valor mais próximo de 200/300/400/500/700 mil; prazos 10 a 25 anos → 20, 30 e 35 → 30) |
| `/renda-para-financiar-imovel-V-mil` (8 não mantidas) | a mantida mais próxima (200/300/500/800 mil) |
| `/taxas-financiamento-imobiliario-<mês>-<ano>` (13 antigas, `noindex`) | `/taxas-financiamento-imobiliario` |

Cloudflare Pages: limites de 2.000 regras estáticas e 100 com curinga; ficamos em 119 e 19. As antigas de 420→360 meses foram absorvidas pela regra `/simulador-<banco>-*` (um salto só, direto ao hub). Já existem 301 para os 4 bancos de home equity removidos (`/simulador-c6-bank-*` etc.).

## O que muda no SEO se aprovar

- `gerador.py`: parar de gerar a grade (`gerar_paginas_pseo` e `dados.csv` com ~1.848 linhas), reduzir `VALORES_COMPARACAO`/`ANOS_COMPARACAO`, `ENTRADAS_RENDA`/valores de renda, e `MESES_INDEXAVEIS_MENSAL`; `etl_taxas.py` deixa de gerar `slug` por página.
- **Sitemap** (`gerar_sitemap`): ~60 URLs; `lastmod_manifest.json` perde as chaves removidas.
- **Canonical**: sem mudança nas mantidas; as removidas somem (301, não canonical cruzado).
- **Links internos**: hubs deixam de listar `links_destaque` da grade (apontar para a home com `?b=<banco>`); páginas de comparação deixam de linkar vizinhas removidas (`html_vizinhas`); `GUIAS_RELACIONADOS`, rodapés e `_nav_comparacao` conferidos; a home já linka os 11 hubs.
- **`llms.txt` e `llms-full.txt`**: tirar o padrão `/simulador-{banco}-{valor}-mil-{prazo}-meses` e o "Total de páginas de simulação".
- **Feed** (`feed.xml`): não muda (só posts mensais).
- **JSON-LD / breadcrumbs**: somem com as páginas; conferir o `isPartOf` e os `BreadcrumbList` das páginas mantidas (o comparador e o índice de comparação não têm `ItemList`).
- **Dados abertos / publicação** (`publicacao/*`, Kaggle, Hugging Face, dados.gov.br): descrições citam o site; não dependem das páginas removidas, mas revisar o texto e o número de páginas.
- **IndexNow** (`indexnow.py`): avisar as URLs que passaram a 301.
- **Testes**: `tests/test_paginas_geradas.py`, `test_comparacao_sem_marca.py`, `test_guias_novos.py` e `test_lastmod_e_fontes.py` têm contagens e padrões da grade; ajustar.
- **Search Console**: reenviar o sitemap; não precisa da ferramenta de remoção (301 resolve).
- **Embed** (`/embed`) e `/incorporar`: independentes da grade.

## Revisão de SEO das páginas que ficam

Conferido nos HTML gerados (não corrigi nada além do que está no PR da home):

- Títulos ≤ 60: **ok** em todas (máximo 59). Descrições ≤ 160: **ok** (máximo 157). Canonical, H1 único e JSON-LD: **ok**. `noindex` nas finas: **ok** (13 meses antigos).
- **A corrigir se mantiver:** (1) hubs com 55% de texto repetido, (2) comparações e renda com texto curto e igual entre si, (3) **148 páginas citam comissão do parceiro** (rodapé de divulgação, `/metodologia`, FAQ) e **1.839 nomeiam a "Financia Tudo"** nos botões, o que contraria a regra de mensagem agnóstica; a home nova já não tem esse texto. Decisão do dono (o aviso de divulgação também é uma boa prática de transparência).

## O que NÃO foi verificado

- Conversão por página (Umami não consultado) e consultas (queries) por página.
- Se o Google indexaria as páginas mantidas depois do corte (só se sabe medindo).
- Dados do Bing Webmaster e Yandex.
- O 24º URL "rastreada, mas não indexada" (o Search Console só mostrou 23 por texto); os totais por motivo foram lidos da tela, não exportados.
- Domínio inteiro: não separei o que é do simulador, veículos, empréstimo e dados B2B.
