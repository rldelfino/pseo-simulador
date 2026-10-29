# Simulador de Financiamento Imobiliário — Datalab Global

Site estático (HTML gerado por Python) com simuladores de financiamento imobiliário,
comparativos de taxas entre bancos e dados abertos. No ar em
**https://simulador.datalabglobal.com**, publicado pelo Cloudflare Pages.

- **Simulador por banco e prazo:** parcela, SAC x Price, CET e simulação de amortização.
- **Comparação sem marca de banco:** [financiamento imobiliário por valor e prazo](https://simulador.datalabglobal.com/financiamento-imobiliario).
- **Taxas por banco, mês a mês:** [comparador de bancos](https://simulador.datalabglobal.com/comparador-bancos).
- **Dados abertos:** [/dados-abertos](https://simulador.datalabglobal.com/dados-abertos).

## Dados abertos

A série mensal de taxas médias de juros do financiamento imobiliário por banco, do
Banco Central do Brasil (modalidade 903201), está em [`paginas_seo/dados/`](paginas_seo/dados):

| Arquivo | Conteúdo |
|---|---|
| `taxas-financiamento-imobiliario.csv` | Série mensal por banco (UTF-8, vírgula) |
| `taxas-financiamento-imobiliario.json` | Mesma série em JSON |
| `datapackage.json` | Metadados ([Frictionless Data](https://frictionlessdata.io)) |
| `README.md` | Descrição, limites e como citar |

Licença dos dados: **CC BY 4.0** (uso livre, citando a fonte). São médias do que foi
efetivamente contratado, não ofertas. BRB e Poupex não constam porque o Banco Central não
os cobre nesta modalidade.

## Como funciona

1. `etl_taxas.py` busca as taxas atuais (API pública do BACEN) e atualiza `dados.csv`.
2. `historico_taxas.py` acrescenta os meses novos a `historico_taxas.csv`.
3. `gerador.py` gera as páginas em `paginas_seo/` (a partir de `dados.csv` e `bancos.py`).
4. `npm run build:css` compila o Tailwind em `paginas_seo/styles.css`.
5. `indexnow.py` avisa o Bing das páginas atualizadas.

O workflow `.github/workflows/atualiza_taxas.yml` roda tudo isso no dia 5 de cada mês.

## Rodar localmente

```bash
pip install -r requirements-dev.txt
python gerador.py          # gera paginas_seo/
npm install && npm run build:css
python -m pytest           # testes (use Python 3.10, o mesmo do CI)
```

Para incluir um banco novo basta uma entrada em `bancos.py`.

## Sobre

Mantido pela [Datalab Global](https://www.datalabglobal.com), marca de
Satori Soluções Comerciais LTDA (CNPJ 63.998.502/0001-73). As simulações são educativas e
não constituem oferta de crédito.
