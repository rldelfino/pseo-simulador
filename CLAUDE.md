# Simulador de Financiamento Imobiliário — Datalab Global (002)

Idioma: português do Brasil. Estilo: curto, sem jargão, números reais, dizer o que NÃO foi verificado. Site: https://simulador.datalabglobal.com (Cloudflare Pages, saída `paginas_seo/` commitada; repo `rldelfino/pseo-simulador`).

## Regras fixas
- **Graphify primeiro**: `graphify update .` e `graphify query "..."` antes de ler arquivo/grep. Não commitar `graphify-out/`.
- Sem gastar dinheiro, sem postar nem mandar mensagem a pessoas, sem CPF/telefone em log/teste/arquivo, sem segredo em arquivo.
- Fluxo: branch a partir de `main` atualizado, PR, **nunca push direto no `main`**; quem mescla é a sessão principal. Python 3.10 no CI (sem f-string aninhado); testes: `python -m pytest -q`.
- **Home nova** (20/11/2026): sem `style=` nem script inline (CSP própria só para `/` em `paginas_seo/_headers`), mensagem agnóstica sobre o parceiro ("um parceiro de crédito"), sem texto de remuneração, sem nome do parceiro. O link do parceiro (`LINK_FINANCIA_TUDO` em `gerador.py`) só existe no botão da tela de confirmação. As demais páginas ainda usam Tailwind, CSP antiga e o texto antigo de divulgação (148 páginas citam comissão; decisão do dono).
- Taxa mensal = `(1 + a.a.)^(1/12) − 1` (a do BCB é efetiva). Nunca dividir por 12, exceto na taxa **nominal** que a pessoa digita de uma proposta. Corrigido em 20/11/2026 (parcelas eram ~5% altas).
- Paleta: verde esmeralda `#10b981` (imobiliário); Home Equity azul-petróleo, Auto Equity âmbar, Condomínio terracota, veículos azul, Pix roxo.

## Comandos
- Gerar: `python gerador.py` (lê `dados.csv`, `historico_taxas.csv`; escreve `paginas_seo/`, copia `src/home.css`, `src/home.js`, `src/calculo_home.js`, `src/menu.js`). Tailwind das demais páginas: `npm run build:css`.
- Redirecionamentos: `python conferir_redirects.py` (limites do Cloudflare, loops, destinos, cobertura).
- Taxas: `python etl_taxas.py`, `python historico_taxas.py`; robô em `.github/workflows/atualiza_taxas.yml` (dias 5 e 20).
- Conferência dos números contra o BCB ao vivo: `python conferir_numeros.py` (escreve `CONFERENCIA-NUMEROS.md`).
- Testes: `python -m pytest -q`. Navegador (fora do CI, precisa do Playwright com Chromium e WebKit): `python testar_navegador.py` (home de ponta a ponta, 4 perfis, com os cabeçalhos do `_headers` via `servidor_local.py`) e `python testar_aleatorio.py [semente]` (sessões aleatórias contra `calculo_home.py`).
- Marca (logo, favicon, ícones, og-image): `python gerar_icones.py` (Playwright + Pillow; desenho em `logo.py`).

## Arquivos da home
`layout_home.py` (HTML), `gerador_home.py` (montagem e valores iniciais), `calculo_home.py` (conta de referência) = `src/calculo_home.js` (testado Python x JS por Node), `src/home.js`, `src/home.css`. O estado inicial (média dos bancos, R$ 500 mil, entrada R$ 100 mil, 30 anos, SAC) vem escrito no HTML.

## Estado (20/11/2026)
- PR da correção da taxa mensal e PR do template novo da home abertos (não mesclados).
- **Enxugamento aplicado (20/11/2026)**: o sitemap caiu de 167 para 61 URLs. A grade `simulador-<banco>-<valor>-<prazo>` (1.680 páginas) não é mais gerada (`GERAR_GRADE_SIMULADOR = False`); comparação sem marca ficou com 10 páginas (`VALORES_COMPARACAO` x `ANOS_COMPARACAO`), renda com 4 (`VALORES_RENDA`) e taxas mês a mês só nos 12 meses recentes. `limpar_paginas_obsoletas()` apaga do disco o que o gerador não escreve mais; as URLs removidas têm 301 em `paginas_seo/_redirects` (conferir com `python conferir_redirects.py`). Os hubs linkam a home preenchida (`/?v=&e=&p=&b=&s=`). Detalhes e dados: `AVALIACAO-SUBPAGINAS.md`. Reavaliar indexação em 4 a 6 semanas.
- Arquivo do Yandex Webmaster: `paginas_seo/yandex_90c15c3be650b0ed.html` (não é apagado pelo gerador). NÃO verificado: o Cloudflare Pages pode responder 308 de `.html` para a URL sem extensão; conferir no Yandex depois do deploy.
- NÃO verificado: se o formulário do parceiro aceita pré-preenchimento (abre limpo); iPhone físico; taxas de BRB e Poupex (o BCB não cobre; vêm de blog/estático); texto jurídico da seção de amortização.
