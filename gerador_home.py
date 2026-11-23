"""Monta o HTML da home nova (ver layout_home.py). Chamado por gerador.gerar_index_home(), que passa o que vem do resto do gerador
(taxas, datas, guias, medição) num dicionário: este módulo não importa gerador.py (seria um ciclo).

O estado inicial (banco "média dos bancos", imóvel R$ 500 mil, entrada R$ 100 mil, 30 anos, SAC) já vem escrito no HTML, com a conta de
calculo_home.py: a página tem números reais sem JavaScript, e o JavaScript refaz a mesma conta ao carregar (os testes comparam).
Python 3.10: sem f-string aninhado.
"""
import html
import json
import statistics

import calculo_home as C
import layout_home as L

PADRAO = {"banco": "mercado", "imovel": 500_000, "entrada": 100_000, "anos": 30, "sistema": "sac"}
LTV_MERCADO = 0.80
PRAZO_MERCADO = 420
ENTRADA_MAX_PCT = 0.9

TITULO = "Simulador de Financiamento Imobiliário: Parcela e CET 2026"
DESCRICAO = ("Simule o financiamento imobiliário: parcela SAC e Price, CET e economia pagando a mais, "
             "com a taxa média de cada banco (Banco Central). Grátis.")

FAQ = [
    ("Como funciona o simulador de financiamento imobiliário da Datalab?",
     "Você informa o valor do imóvel, a entrada e o prazo, escolhe um banco e vê a parcela, o custo total e o CET com a taxa média dele. "
     "Também dá para simular quanto você economiza pagando a mais ou usar a taxa de uma proposta que você já recebeu. As taxas vêm do Banco Central e são atualizadas todo mês."),
    ("As taxas mostradas são reais ou só uma estimativa de marketing?",
     "São a taxa média efetivamente contratada por cada banco no mês, divulgada pelo Banco Central, e não uma taxa promocional de vitrine. "
     "BRB e Poupex não constam nessa série; para eles usamos uma estimativa de mercado, identificada como tal. A sua taxa final depende da análise de crédito e do imóvel."),
    ("O simulador cobra alguma coisa?",
     "Não. Simular é gratuito e não pede cadastro. Só se você decidir pedir uma proposta é que informa dados pessoais, em um formulário de um parceiro de crédito. "
     "A simulação não é oferta nem compromisso."),
    ("Por que a parcela do banco pode ser diferente da que aparece aqui?",
     "A conta usa a taxa média do banco, sem TR, e estima o CET com seguros e tarifa de mercado. O banco define a taxa para o seu perfil, o seguro pela sua idade e o valor pela avaliação do imóvel. "
     "Use a simulação para comparar e entender a ordem de grandeza, e confirme as condições na proposta."),
]


def brl(v):
    return "R$ " + format(int(v + 0.5), ",").replace(",", ".")


def pct(v, casas=2):
    return format(v, "." + str(casas) + "f").replace(".", ",") + "%"


def _esc(t):
    return html.escape(t, quote=True)


MESES_CURTOS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def _quita(hoje, meses):
    """Mesma conta do home.js: hoje + meses + 2 (primeira parcela no mês seguinte ao da contratação)."""
    m = hoje.month - 1 + meses + 2
    return "%s/%d" % (MESES_CURTOS[m % 12], hoje.year + m // 12)


def _ceil1000(v):
    import math
    return int(math.ceil(v / 1000.0) * 1000)


def mercado(bancos):
    return {"t": round(statistics.median([b["t"] for b in bancos]), 2), "l": LTV_MERCADO, "p": PRAZO_MERCADO}


def dados_json(ctx):
    bancos = ctx["bancos"]
    return {"bancos": bancos, "mercado": mercado(bancos), "ref": ctx["ref_curto"], "atualizado": ctx["atualizado_br"], "padrao": PADRAO}


def linhas_bancos(bancos, imovel, entrada, anos, sistema):
    """Mesma regra do home.js: entrada no mínimo do banco, prazo no máximo do banco, ordenado pelo CET."""
    out = []
    meses = anos * 12
    for b in bancos:
        m = min(meses, b["p"])
        e = max(entrada, _ceil1000(imovel * (1 - b["l"])))
        e = min(e, imovel - 10_000)
        r = C.simular(imovel, e, m / 12, b["t"], sistema)
        out.append((b, r, m < meses or e > entrada))
    out.sort(key=lambda x: x[1]["cet"])
    return out


def html_bancos(linhas, sistema, banco_sel):
    partes = []
    for b, r, ajuste in linhas:
        classe = "bk us" if b["k"] == banco_sel else "bk"
        partes.append(
            '<li class="%s"><a class="bk-n" href="/%s">%s</a><span class="bk-t num">%s a.a.</span>'
            '<span class="bk-p num"><b>%s</b><small>%s</small></span><span class="bk-c num"><b>%s</b><small>CET a.a.</small></span>%s</li>'
            % (classe, b["h"], _esc(b["n"]), pct(b["t"]), brl(r["p1"]), "1ª parcela" if sistema == "sac" else "parcela", pct(r["cet"]),
               '<span class="bk-aj">entrada ou prazo ajustados ao limite do banco</span>' if ajuste else ""))
    return "".join(partes)


def defaults(ctx):
    """Valores do estado inicial, já formatados como o JavaScript formata."""
    bancos = ctx["bancos"]
    mk = mercado(bancos)
    p = PADRAO
    imovel, entrada, anos, sis = p["imovel"], p["entrada"], p["anos"], p["sistema"]
    r = C.simular(imovel, entrada, anos, mk["t"], sis)
    i = r["i"]
    meses = r["meses"]
    linhas = C.amortizacao_anual(r["financiado"], i, meses, sis)
    pago1 = linhas[0]["juros"] + linhas[0]["amortizacao"]
    pj1 = int((linhas[0]["juros"] / pago1) * 100 + 0.5)
    pj = r["juros"] / r["total"]
    emin = _ceil1000(imovel * (1 - mk["l"]))
    emax = int((imovel * ENTRADA_MAX_PCT) // 1000 * 1000)
    corpo = "".join('<tr><th scope="row">%d</th><td>%s</td><td>%s</td><td>%s</td></tr>' % (x["ano"], brl(x["juros"]), brl(x["amortizacao"]), brl(x["saldo"])) for x in linhas)
    total = '<tr><th scope="row">Total</th><td>%s</td><td>%s</td><td></td></tr>' % (brl(sum(x["juros"] for x in linhas)), brl(r["financiado"]))
    am_resumo = ("No primeiro ano, %s dos %s que você paga são juros (%d%%). "
                 "No SAC a amortização é a mesma todo mês: a parcela cai porque os juros caem." % (brl(linhas[0]["juros"]), brl(pago1), pj1))
    ult = "A parcela cai todo mês, até %s na última." % brl(r["pu"])
    v = {
        "D_BANCO_FONTE": "mediana dos bancos, BCB " + ctx["ref_curto"],
        "D_BANCO_NOME": "Média dos bancos",
        "D_BANCO_HINT": "Taxa de %s ao ano (%s ao mês). Entrada mínima de 20%% e prazo de até 35 anos." % (pct(mk["t"]), pct(i * 100)),
        "D_IMOVEL": format(imovel, ",").replace(",", "."), "V_IMOVEL": str(imovel), "D_IMOVEL_RS": brl(imovel),
        "D_ENTRADA": format(entrada, ",").replace(",", "."), "V_ENTRADA": str(entrada), "V_ENTRADA_MIN": str(emin), "V_ENTRADA_MAX": str(emax),
        "D_ENTRADA_PCT": "%d%% do imóvel" % round(entrada / imovel * 100),
        "D_ENTRADA_MIN": "R$ %d mil" % (emin // 1000), "D_ENTRADA_MAX": "R$ %d mil" % (emax // 1000),
        "V_PRAZO": str(anos), "V_PRAZO_MAX": "35", "V_QUANDO_MAX": str(anos - 1),
        "D_KICKER": "1ª parcela estimada", "D_PARCELA": brl(r["p1"]),
        "D_SUB": "em %d meses · taxa %s a.a." % (meses, pct(mk["t"])),
        "D_ULT_HIDDEN": "", "D_ULT": ult,
        "D_TOTAL": brl(r["total"]), "D_CET": pct(r["cet"]),
        "D_CK_SAC": "checked", "D_CK_PRICE": "", "D_HINT_SIS": "Cai todo mês e paga menos juros no total.",
        "D_RESUMO": "Você financia %s e paga %s no total: %s a mais em juros." % (brl(r["financiado"]), brl(r["total"]), brl(r["juros"])),
        "D_PCT_JUROS": str(int(pj * 100 + 0.5)), "D_ROSCA_P": "%.1f" % ((1 - pj) * 289.0265),
        "D_L_CRED": brl(r["financiado"]), "D_L_JUROS": brl(r["juros"]),
        "D_BARRA": "%.1f" % min(100.0, r["ltv"] * 100), "D_LTV_MARCA": "%.1f" % min(99.0, mk["l"] * 100),
        "D_FIN_LINHA": "%s · %d%%" % (brl(r["financiado"]), round(r["ltv"] * 100)),
        "D_LIMITE_ROT": "Limite do banco (%d%%)" % round(mk["l"] * 100), "D_LIMITE": brl(imovel * mk["l"]),
        "D_K_QUITA": _quita(ctx["hoje"], meses), "D_K_QUITA_S": "%d parcelas, se contratar este mês" % meses,
        "D_K_JURO1": "R$ " + format(r["juros"] / r["financiado"], ".2f").replace(".", ","),
        "D_K_RENDA": brl(r["renda"]),
        "D_K_NOTA": "Taxas: média contratada em %s (Banco Central), atualizadas em %s. Estimativa, não é oferta. Renda: a 1ª parcela dividida por 30%%, conta nossa, não é análise de crédito."
                    % (ctx["ref_curto"], ctx["atualizado_br"]),
        "D_BANCOS": html_bancos(linhas_bancos(bancos, imovel, entrada, anos, sis), sis, None),
        "D_BK_NOTA": "Taxas: média contratada em %s (Banco Central); BRB e Poupex são estimativas de mercado. CET com seguros e tarifa estimados, só para comparar." % ctx["ref_curto"],
        "D_AMORT_PCT": "%d%%" % pj1, "D_AMORT_RESUMO": am_resumo,
        "D_AMORT_CAP": "Parcela que cai: juros, amortização e saldo devedor no fim de cada ano",
        "D_AMORT_LINHAS": corpo, "D_AMORT_TOTAL": total,
        "D_AMORT_NOTA": "Conta com a taxa de %s ao ano (efetiva), amortização constante (SAC), sem TR, seguros, tarifas nem IOF." % pct(mk["t"]),
        "D_AM_TAXA": pct(mk["t"]),
    }
    return v, r


def _nav(itens):
    return "".join('<a href="%s">%s</a>' % (u, t) for u, t in itens)


def _lis(itens):
    return "".join('<li><a href="%s">%s</a></li>' % (u, t) for u, t in itens)


def _cartoes(guias):
    return "".join('<a class="card" href="/%s"><h3>%s</h3>%s<span class="go">Ler o guia →</span></a>' % (g["slug"], _esc(g["titulo"]), _esc(g["resumo"])) for g in guias)


def _faq_html():
    return "".join("<details><summary>%s</summary><p>%s</p></details>" % (_esc(q), _esc(a)) for q, a in FAQ)


def _json_ld(ctx):
    dom = ctx["dominio"]
    org = {"@context": "https://schema.org", "@type": "Organization", "@id": "https://www.datalabglobal.com/#organization", "name": "Datalab Global",
           "url": "https://www.datalabglobal.com/", "logo": dom + "/logo-schema.png", "sameAs": ["https://huggingface.co/datalabglobal"],
           "founder": {"@type": "Person", "name": "Rodolfo Delfino", "sameAs": ["https://github.com/rldelfino", "https://www.kaggle.com/rodolfodelfino", "https://www.linkedin.com/in/rodolfo-leal-delfino"]},
           "contactPoint": {"@type": "ContactPoint", "email": ctx["email"], "contactType": "customer service"}}
    site = {"@context": "https://schema.org", "@type": "WebSite", "name": "Datalab Global", "url": dom + "/",
            "publisher": {"@type": "Organization", "@id": "https://www.datalabglobal.com/#organization", "name": "Datalab Global", "url": "https://www.datalabglobal.com/"},
            "dateModified": ctx["atualizado_iso"]}
    app = {"@context": "https://schema.org", "@type": "WebApplication", "name": "Simulador de financiamento imobiliário", "url": dom + "/",
           "applicationCategory": "FinanceApplication", "operatingSystem": "Web", "inLanguage": "pt-BR",
           "offers": {"@type": "Offer", "price": "0", "priceCurrency": "BRL"},
           "publisher": {"@type": "Organization", "@id": "https://www.datalabglobal.com/#organization", "name": "Datalab Global"}}
    faq = {"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}
    return "".join('<script type="application/ld+json">%s</script>\n' % json.dumps(b, ensure_ascii=False) for b in (site, org, app, faq))


def montar_home(ctx):
    """Devolve (html, valores_padrao_calculados)."""
    v, r = defaults(ctx)
    dom = ctx["dominio"]
    ver = ctx["versao"]
    cabeca = (
        '<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<meta name=\"description\" content=\"%s\">\n<link rel=\"canonical\" href=\"%s/\">\n"
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n<link rel="icon" href="/favicon.ico?v=%s" sizes="any">\n'
        '<link rel="icon" href="/favicon-32.png?v=%s" type="image/png" sizes="32x32">\n<link rel="icon" href="/favicon-192.png?v=%s" type="image/png" sizes="192x192">\n'
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=%s">\n'
        '<meta property="og:type" content="website">\n<meta property="og:locale" content="pt_BR">\n<meta property="og:site_name" content="Datalab Global">\n'
        '<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n<meta property="og:url" content="%s/">\n<meta property="og:image" content="%s/og-image.png?v=%s">\n'
        '<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:title" content="%s">\n<meta name="twitter:description" content="%s">\n<meta name="twitter:image" content="%s/og-image.png?v=%s">\n'
        '<meta name="theme-color" content="#020617">\n'
        '<link rel="preload" href="/fonts/playfair-display-latin.woff2" as="font" type="font/woff2" crossorigin>\n<link rel="preload" href="/fonts/inter-latin.woff2" as="font" type="font/woff2" crossorigin>\n'
        '<link rel="stylesheet" href="/home.css?v=%s">\n<link rel="alternate" type="application/atom+xml" title="%s" href="/feed.xml">\n%s%s</head>\n'
        % (TITULO, _esc(DESCRICAO), dom, ctx["icones_v"], ctx["icones_v"], ctx["icones_v"], ctx["icones_v"], TITULO, _esc(DESCRICAO), dom, dom, ver,
           TITULO, _esc(DESCRICAO), dom, ver, ver, ctx["titulo_feed"], _json_ld(ctx), "".join(ctx["medicao"])))
    marcadores = {
        "LOGO": L.LOGO,
        "NAV": _nav(ctx["nav"]), "NAVMOBILE": _nav([("/#simulador", "Simular")] + ctx["nav"]),
        "FOOT_ENTENDA": _lis(ctx["foot_entenda"]), "FOOT_DADOS": _lis(ctx["foot_dados"]), "FOOT_LEGAL": _lis(ctx["foot_legal"]), "FOOT_OUTROS": _lis(ctx["foot_outros"]),
        "ATUALIZADO": ctx["atualizado_br"], "FONTE_TAXAS": _esc(ctx["fonte_taxas"]), "RAZAO": ctx["razao"], "CNPJ": ctx["cnpj"], "EMAIL": ctx["email"],
        "CARTOES": _cartoes(ctx["guias"]), "FAQ": _faq_html(), "PARCEIRO": ctx["parceiro"], "URL_PRIVACIDADE": ctx["url_privacidade"],
    }
    marcadores.update(v)
    main = L.MAIN
    topo = L.CABECALHO
    rodape = L.RODAPE
    corpo = '<body>\n' + topo + '\n<main id="conteudo" class="wrap">\n' + main + '</main>\n\n' + rodape
    dados = '<script type="application/json" id="dados-home">' + json.dumps(dados_json(ctx), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>\n"
    scripts = dados + '<script defer src="/calculo_home.js?v=%s"></script>\n<script defer src="/home.js?v=%s"></script>\n<script defer src="/menu.js?v=%s"></script>\n</body>\n</html>\n' % (ver, ver, ver)
    pagina = cabeca + corpo + scripts
    # os marcadores mais longos primeiro (D_IMOVEL_RS antes de D_IMOVEL, V_ENTRADA_MIN antes de V_ENTRADA...)
    for chave in sorted(marcadores, key=len, reverse=True):
        pagina = pagina.replace("@@" + chave + "@@", marcadores[chave])
    return pagina, v
