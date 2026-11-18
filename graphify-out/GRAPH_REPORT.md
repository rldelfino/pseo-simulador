# Graph Report - 002-pseo-simulador-imovel  (2026-11-13)

## Corpus Check
- 11 files · ~10,587,779 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 3, .css 2, .csv 1)

## Summary
- 182 nodes · 303 edges · 13 communities (8 shown, 5 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `93d89ec0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_calculos.py
- test_paginas_geradas.py
- etl_taxas.py
- gerador.py
- gerar_hub_bancos
- calculo.js
- icone
- package.json
- tooltip
- rasterizar_favicon_png
- calcular_marcador_posicao_mercado
- gerar_favicon_svg

## God Nodes (most connected - your core abstractions)
1. `gerar_paginas_pseo()` - 29 edges
2. `gerar_hub_bancos()` - 13 edges
3. `icone()` - 12 edges
4. `comparar_todos_bancos()` - 11 edges
5. `calcular_cet_real()` - 10 edges
6. `calcular_sac_price()` - 10 edges
7. `gerar_comparador_bancos()` - 10 edges
8. `obter_regra()` - 9 edges
9. `render_head_boilerplate()` - 9 edges
10. `gerar_index_home()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `test_cet_zero_quando_nao_ha_financiamento()` --calls--> `calcular_cet_real()`  [EXTRACTED]
  tests/test_calculos.py → gerador.py
- `test_price_parcela_e_fixa()` --calls--> `calcular_sac_price()`  [EXTRACTED]
  tests/test_calculos.py → gerador.py
- `test_renda_sugerida_so_aparece_com_valor_imovel()` --calls--> `calcular_sac_price()`  [EXTRACTED]
  tests/test_calculos.py → gerador.py
- `test_ranking_bancos_respeita_prazo_maximo_de_cada_banco()` --calls--> `comparar_todos_bancos()`  [EXTRACTED]
  tests/test_calculos.py → gerador.py
- `test_ranking_bancos_vem_ordenado_por_cet()` --calls--> `comparar_todos_bancos()`  [EXTRACTED]
  tests/test_calculos.py → gerador.py

## Import Cycles
- None detected.

## Communities (13 total, 5 thin omitted)

### Community 0 - "test_calculos.py"
Cohesion: 0.08
Nodes (17): calcular_cet_real(), calcular_sac_price(), comparar_todos_bancos(), test_cet_e_sempre_maior_que_a_taxa_nominal(), test_cet_escala_com_a_taxa_nominal(), test_cet_sac_e_price_ficam_proximos_mas_nao_iguais(), test_cet_zero_quando_nao_ha_financiamento(), test_formatar_reais_sempre_duas_casas_decimais() (+9 more)

### Community 1 - "test_paginas_geradas.py"
Cohesion: 0.08
Nodes (13): _arquivos_html(), _slugs_validos(), test_ads_txt_autoriza_o_publisher_certo(), test_dominio_correto_em_todas_as_paginas(), test_headers_tem_hsts_e_libera_beacon_do_cloudflare_analytics(), test_home_tem_schema_organization_com_logo(), test_html_sem_tags_desbalanceadas(), test_nenhum_html_sobrando_em_url_publica() (+5 more)

### Community 2 - "etl_taxas.py"
Cohesion: 0.08
Nodes (10): normalizar_chave(), _buscar_bacen_json(), _buscar_html_tabela(), _buscar_taxas_nas_fontes(), _carregar_cache(), _extrair_conteudo_ou_avisar_schema(), _extrair_taxa_da_tabela(), _normalizar_nome_instituicao() (+2 more)

### Community 3 - "gerador.py"
Cohesion: 0.12
Nodes (12): construir_bancos_json(), criar_csv_exemplo(), formatar_valor_curto(), gerar_calculo_js(), gerar_llms_txt(), gerar_paginas_pseo(), gerar_robots_txt(), gerar_sitemap() (+4 more)

### Community 4 - "gerar_hub_bancos"
Cohesion: 0.24
Nodes (8): nome_exibicao(), obter_regra(), favicon_com_fallback(), formatar_reais(), gerar_comparador_bancos(), gerar_hub_bancos(), gerar_index_home(), slug_hub_banco()

### Community 5 - "calculo.js"
Cohesion: 0.36
Nodes (10): atualizarValor(), calcularCET(), calcularRankingBancosLive(), calcularTudo(), formatCurrency(), initMask(), renderizarComparacaoMercado(), simularComAmortizacaoRecorrente() (+2 more)

### Community 6 - "icone"
Cohesion: 0.24
Nodes (5): gerar_hub_aprenda(), gerar_pagina_aprenda(), gerar_pagina_sobre(), render_head_boilerplate(), icone()

### Community 7 - "package.json"
Cohesion: 0.20
Nodes (9): description, devDependencies, tailwindcss, name, private, scripts, build:css, version (+1 more)

## Knowledge Gaps
- **7 isolated node(s):** `name`, `private`, `version`, `description`, `build:css` (+2 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 85 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `gerar_paginas_pseo()` connect `gerador.py` to `test_calculos.py`, `gerar_hub_bancos`, `icone`, `tooltip`, `calcular_marcador_posicao_mercado`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `calcular_cet_real()` connect `test_calculos.py` to `gerador.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_calculos.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08067226890756303 - nodes in this community are weakly interconnected._
- **Should `test_paginas_geradas.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07954545454545454 - nodes in this community are weakly interconnected._
- **Should `etl_taxas.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07862903225806452 - nodes in this community are weakly interconnected._
- **Should `gerador.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12318840579710146 - nodes in this community are weakly interconnected._