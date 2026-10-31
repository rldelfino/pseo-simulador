"""
Guias novos de /aprenda (31/out/2026): portabilidade, ITBI e cartório, passo a
passo e documentos, Minha Casa Minha Vida, imóvel na planta e seguros (MIP/DFI).

Cada fato foi conferido em fonte oficial antes de ser escrito e a fonte aparece
no próprio texto, em "Fontes". Regra que muda (MCMV, limite do FGTS) leva a data
da conferência. Os exemplos numéricos usam o mesmo cálculo do simulador
(calcular_sac_price) e são hipotéticos: as taxas não são oferta.

montar_guias(calc, reais) recebe as funções do gerador (evita import circular).
"""

DATA_CONFERIDO = "31/10/2026"
_H2 = '<div class="border-t border-white/10 pt-6">\n            <h2 class="font-serif text-xl text-white mb-3">{t}</h2>\n            {c}\n        </div>'
_LINK = 'class="text-emerald-400 underline"'


def _a(href, texto, externo=False):
    extra = ' target="_blank" rel="noopener"' if externo else ""
    return f'<a href="{href}" {_LINK}{extra}>{texto}</a>'


def _sec(titulo, *paragrafos):
    return _H2.format(t=titulo, c="\n            ".join(f"<p>{p}</p>" for p in paragrafos))


def _lista(titulo, itens, intro=""):
    lis = "".join(f"<li>{i}</li>" for i in itens)
    corpo = (f"<p>{intro}</p>\n            " if intro else "") + f'<ul class="list-disc pl-6 space-y-2">{lis}</ul>'
    return _H2.format(t=titulo, c=corpo)


def _fontes(links):
    lis = "".join(f"<li>{_a(h, t, True)}</li>" for h, t in links)
    return _H2.format(t="Fontes", c=f'<ul class="list-disc pl-6 space-y-1 text-sm">{lis}</ul>')


def _b(t):
    return f'<strong class="text-white">{t}</strong>'


def montar_guias(calc, reais):
    p = lambda v: f"{v:.2f}".replace(".", ",")

    # ---------------------------------------------------------------- 1
    saldo, meses, t_atual, t_nova = 300_000, 240, 12.5, 10.5
    a, n = calc(saldo, meses, t_atual), calc(saldo, meses, t_nova)
    j_a, j_n = a["total_sac"] - saldo, n["total_sac"] - saldo
    portab = {
        "slug": "aprenda-portabilidade-financiamento-imobiliario",
        "titulo_h1": "Portabilidade do financiamento imobiliário: como trocar de banco sem refinanciar do zero",
        "titulo_pagina": "Portabilidade de financiamento imobiliário | Datalab Global",
        "meta_description": "Como funciona a portabilidade do financiamento imobiliário, o que a regra do Banco Central garante, quando compensa e o que pedir ao banco.",
        "resumo_card": "Levar o saldo devedor para outro banco que ofereça condições melhores: o que a regra permite, quanto pode economizar e o que perguntar antes.",
        "corpo_html": "\n        ".join([
            "<p>Portabilidade é o direito de transferir o seu financiamento para outra instituição financeira que ofereça condições melhores, sem precisar quitar a dívida com recursos próprios. O novo banco paga o saldo devedor ao banco original e o seu contrato passa a ser com ele. A regra vale para o crédito imobiliário e é definida pelo Conselho Monetário Nacional e pelo Banco Central.</p>",
            _sec("O que a regra garante",
                 f"Pela regulamentação, o novo financiamento {_b('não pode ser maior que o saldo devedor')} nem {_b('ter prazo maior que o prazo que falta')} no contrato original. Na prática, você não sai da portabilidade com dinheiro novo no bolso nem alonga a dívida: o que muda é a taxa e as condições. A troca de informações e a transferência de recursos entre os dois bancos é feita por sistema eletrônico, e esses custos não podem ser repassados a você (o Banco Central registra essa vedação no Voto CMN 67/2023).",
                 f"O banco original tem até {_b('5 dias úteis')} para responder à solicitação e pode, nesse prazo, apresentar uma contraproposta para manter você como cliente. Compare com a proposta do novo banco; você não é obrigado a aceitar a contraproposta."),
            _sec("Quando costuma compensar",
                 f"A conta é simples: compare as parcelas e o total de juros do que falta pagar. Um exemplo hipotético, calculado como o simulador calcula: um saldo devedor de {reais(saldo)}, com {meses} meses restantes, na SAC. A {p(t_atual)}% ao ano, a primeira parcela é de {reais(a['p1_sac'])} e os juros que faltam somam {reais(j_a)}. A {p(t_nova)}% ao ano, a primeira parcela cai para {reais(n['p1_sac'])} e os juros somam {reais(j_n)}: {_b(reais(j_a - j_n) + ' a menos')} até o fim do contrato. Esses números não são oferta de nenhum banco: servem para mostrar o tamanho do efeito de dois pontos de taxa.",
                 "Quanto mais cedo no contrato e quanto maior o saldo, maior a economia possível, porque os juros da SAC incidem sobre o saldo devedor. Perto do fim do contrato, o saldo é pequeno e a diferença tende a não compensar o trabalho."),
            _lista("O que pedir e conferir antes de decidir", [
                "O saldo devedor atualizado e o prazo restante, pedidos ao banco atual.",
                "A proposta do novo banco por escrito, com o CET (custo efetivo total) e não só a taxa de juros: seguros e tarifas pesam na conta. Veja " + _a("aprenda-cet-iof-financiamento-imobiliario", "o que entra no CET") + ".",
                "Se há custos de avaliação do imóvel, de registro e de averbação da nova garantia no cartório, e quem paga cada um.",
                "O sistema de amortização do novo contrato (SAC ou Price) e se a primeira parcela cabe no seu orçamento. A " + _a("renda-para-financiar-imovel", "renda mínima por valor") + " ajuda a conferir.",
                "O seguro: o novo banco vai exigir apólice nova ou aceita a que você já tem? A escolha da seguradora está explicada em " + _a("aprenda-seguro-mip-dfi-financiamento-imobiliario", "seguros do financiamento") + "."]),
            _sec("Como pedir",
                 "O pedido é feito no banco que vai receber o financiamento (o proponente), que cuida da comunicação com o banco atual. Cada instituição tem a própria página e canal; a Caixa, por exemplo, mantém uma página específica sobre portabilidade de crédito imobiliário. Depois da aprovação, a quitação da dívida antiga e a troca da garantia sobre o imóvel (hipoteca ou alienação fiduciária) são formalizadas e averbadas no cartório de registro de imóveis."),
            _sec("Para simular", f"Para comparar o seu cenário atual com uma proposta nova, use o {_a('comparador-bancos', 'comparador de bancos')}: informe o saldo como valor financiado e o prazo restante, e veja parcela, juros totais e CET lado a lado. As taxas médias de cada mês estão em {_a('taxas-financiamento-imobiliario', 'taxas mês a mês')}."),
            _fontes([
                ("https://www.gov.br/mj/pt-br/assuntos/noticias/comeca-a-vigorar-a-portabilidade-eletronica-de-credito", "Ministério da Justiça: regras da portabilidade eletrônica de crédito"),
                ("https://normativos.bcb.gov.br/Votos/CMN/202367/Voto_do_CMN_67_2023.pdf", "Banco Central: Voto CMN 67/2023 (custos não repassados ao devedor)"),
                ("https://www.caixa.gov.br/voce/habitacao/portabilidade-credito-imobiliario/Paginas/default.aspx", "Caixa: portabilidade de crédito imobiliário (exemplo de canal)"),
            ]) + f'\n        <p class="text-xs text-slate-500">Regras conferidas em {DATA_CONFERIDO}. A Resolução CMN 5.057/2022 consolida a portabilidade; confirme o texto vigente em normativos.bcb.gov.br.</p>',
        ]),
        "cta_href": "comparador-bancos",
        "cta_texto": "Comparar com uma proposta nova",
    }

    # ---------------------------------------------------------------- 2
    valor_ex, aliq_ex = 500_000, 2.0
    itbi_ex = valor_ex * aliq_ex / 100
    itbi = {
        "slug": "aprenda-itbi-cartorio-custos-compra-imovel",
        "titulo_h1": "ITBI e custos de cartório: quanto pagar além da entrada ao comprar um imóvel",
        "titulo_pagina": "ITBI e custos de cartório do imóvel | Datalab Global",
        "meta_description": "O que é o ITBI, quem define a alíquota, como entram o registro e as custas do cartório, e por que esses custos ficam fora do financiamento.",
        "resumo_card": "Imposto da prefeitura e custas do cartório: despesas que o comprador paga além da entrada e que precisam entrar no planejamento.",
        "corpo_html": "\n        ".join([
            "<p>Ao comprar um imóvel, além da entrada e das parcelas, há despesas pagas uma única vez: o imposto de transmissão (ITBI) e as custas do cartório para registrar o imóvel e o contrato. Elas variam por cidade e por estado e costumam ficar de fora do valor financiado, então precisam estar no seu caixa antes de assinar.</p>",
            _sec("O que é o ITBI e quem define o valor",
                 f"O ITBI (Imposto sobre Transmissão de Bens Imóveis) é cobrado na compra e venda de imóvel e é de {_b('competência municipal')}: a Constituição atribui aos municípios o imposto sobre a transmissão onerosa de bens imóveis (art. 156, II). Por isso não existe uma alíquota única no país: cada prefeitura define a sua em lei própria, a base de cálculo e as regras de pagamento.",
                 f"Em muitos municípios, a base é o valor venal do imóvel ou o valor da compra, o que for maior. Algumas prefeituras também têm {_b('alíquota reduzida para a parte financiada')} pelo sistema de habitação; a de São Paulo, por exemplo, publica as regras e o cálculo no site da Secretaria da Fazenda. Como isso muda de cidade para cidade e ao longo do tempo, confirme na prefeitura do município do imóvel."),
            _sec("Quanto isso pesa: uma conta de exemplo",
                 f"Só como aritmética, com uma alíquota hipotética de {p(aliq_ex)}%: sobre um imóvel de {reais(valor_ex)}, o ITBI seria de {reais(itbi_ex)}. Essa alíquota não é a de nenhuma cidade em particular; o valor real depende do município, da base de cálculo e de eventual redução para a parte financiada. Ao planejar, peça o valor exato à prefeitura (muitas emitem a guia pela internet)."),
            _sec("Registro e custas do cartório",
                 f"Depois de pagar o ITBI, o comprador registra a escritura ou o contrato no {_b('cartório de registro de imóveis')}, e é o registro que transfere a propriedade. Os valores cobrados pelos cartórios são os {_b('emolumentos')}, e quem fixa a tabela são os {_b('Estados e o Distrito Federal')}, dentro das normas gerais da Lei federal 10.169/2000. As tabelas são publicadas no diário oficial de cada estado e ficam à vista no cartório. Na prática, o custo muda de estado para estado, conforme o valor do imóvel e o tipo de ato.",
                 "Em geral, o pagamento do ITBI é exigido antes do registro: sem a guia quitada, o cartório não faz a transferência. Peça um orçamento do cartório antes de contratar, para saber o total."),
            _sec("E no financiamento?",
                 "No financiamento, o contrato com o banco também precisa ser registrado. A Caixa informa em seu roteiro de financiamento que os signatários devem registrar o contrato no cartório e apresentá-lo ao banco em até 30 dias após a assinatura, e que o ITBI e as custas cartorárias são despesas do comprador. O valor é liberado ao vendedor depois da apresentação do registro. Outros bancos têm roteiros semelhantes, com prazos e detalhes próprios: confirme no seu contrato."),
            _lista("Como se preparar", [
                "Reserve, além da entrada, um valor para ITBI, registro, avaliação do imóvel e eventual despesa com documentos.",
                "Peça à prefeitura o valor do ITBI e ao cartório o orçamento do registro antes de fechar o negócio.",
                "Confirme se existe alíquota reduzida do ITBI para a parte financiada na sua cidade.",
                "Inclua esse caixa no planejamento: " + _a("renda-para-financiar-imovel", "veja a renda necessária") + " e " + _a("aprenda-ltv-financiamento-imobiliario", "como a entrada é calculada") + "."]),
            _fontes([
                ("https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm", "Constituição Federal, art. 156, II (ITBI é municipal)"),
                ("https://www.planalto.gov.br/ccivil_03/leis/l10169.htm", "Lei federal 10.169/2000 (emolumentos fixados pelos Estados e pelo DF)"),
                ("https://prefeitura.sp.gov.br/web/fazenda/w/servicos/itbi/2513", "Prefeitura de São Paulo: cálculo do ITBI (exemplo de regra municipal)"),
                ("https://www2.recife.pe.gov.br/noticias/22/03/2018/secretaria-de-financas-reforca-importancia-de-registro-imobiliario-em-cartorio", "Prefeitura do Recife: ITBI pago é condição para o registro (exemplo)"),
                ("https://www.caixa.gov.br/voce/habitacao/financiamento/aquisicao-imovel-novo/Paginas/default.aspx", "Caixa: etapas do financiamento, registro e despesas do comprador"),
            ]) + f'\n        <p class="text-xs text-slate-500">Conferido em {DATA_CONFERIDO}. Alíquotas e tabelas mudam: confirme na prefeitura e no cartório.</p>',
        ]),
        "cta_href": "renda-para-financiar-imovel",
        "cta_texto": "Ver a renda necessária",
    }

    # ---------------------------------------------------------------- 3
    passo = {
        "slug": "aprenda-passo-a-passo-financiar-imovel-documentos",
        "titulo_h1": "Passo a passo para financiar um imóvel: etapas e documentos",
        "titulo_pagina": "Passo a passo para financiar um imóvel | Datalab Global",
        "meta_description": "As etapas do financiamento imobiliário, da simulação ao registro, e a lista de documentos do comprador, do vendedor e do imóvel.",
        "resumo_card": "Simulação, análise de crédito, avaliação, assinatura e registro: o caminho completo e os documentos que o banco pede.",
        "corpo_html": "\n        ".join([
            "<p>Financiar um imóvel é um processo com etapas bem definidas. Conhecê-las antes evita surpresas de prazo e de documento. O roteiro abaixo segue o que a Caixa publica em seu site; outros bancos têm etapas parecidas, com nomes, canais e prazos próprios.</p>",
            _lista("As cinco etapas", [
                f"{_b('Simulação e proposta.')} Você simula, escolhe as condições e solicita o financiamento pelo aplicativo, por um correspondente ou na agência. Simular antes, com o seu valor, entrada e prazo, evita pedir um crédito que não cabe na renda.",
                f"{_b('Análise de crédito.')} O banco avalia a documentação do comprador, do vendedor e do imóvel para aprovar e liberar o crédito.",
                f"{_b('Avaliação do imóvel.')} Um engenheiro credenciado pelo banco faz a vistoria, com agendamento prévio, para confirmar que o imóvel atende às condições para servir de garantia do financiamento.",
                f"{_b('Assinatura do contrato.')} Concluídas as avaliações, o contrato é assinado na agência.",
                f"{_b('Registro e liberação.')} O contrato é registrado no cartório de registro de imóveis e apresentado ao banco; só então o valor é liberado ao vendedor. Os custos de ITBI e cartório são do comprador (veja " + _a("aprenda-itbi-cartorio-custos-compra-imovel", "ITBI e custos de cartório") + ")."]),
            _lista("Documentos pedidos ao comprador", [
                "Documento oficial de identificação com foto e CPF.",
                "Comprovante de renda e comprovante de residência.",
                "Comprovante de estado civil.",
                "Se for usar o FGTS: carteira de trabalho, extrato do FGTS e o recibo de entrega da declaração de Imposto de Renda. Veja " + _a("aprenda-fgts-financiamento-imobiliario", "como o FGTS pode entrar") + "."],
                 "Na lista básica publicada pela Caixa:"),
            _lista("Documentos do vendedor e do imóvel", [
                "Do vendedor: identificação com foto, CPF, comprovante de residência e de estado civil (e pacto antenupcial, se houver).",
                "Do imóvel: certidão de inteiro teor da matrícula.",
                "O banco pode pedir documentos adicionais, conforme o caso. Confira a lista atual com a instituição."]),
            _sec("Onde o simulador entra",
                 f"Antes de pedir o crédito, defina três números: o valor do imóvel, quanto você dá de entrada e em quantos anos quer pagar. Com eles, veja a primeira parcela e o CET no {_a('comparador-bancos', 'comparador de bancos')}, e confira se a renda cobre a parcela em {_a('renda-para-financiar-imovel', 'renda para financiar')}. Os bancos costumam limitar a primeira parcela a 30% da renda bruta familiar, uma regra de mercado explicada em {_a('metodologia', 'metodologia')}."),
            _sec("Dicas para não travar no meio",
                 "Junte os documentos do vendedor e do imóvel cedo: a certidão da matrícula e as certidões do vendedor costumam ser o que mais atrasa. Agende a avaliação assim que o crédito for aprovado. Planeje o caixa para o ITBI e o registro, que são pagos à parte. E guarde o prazo de registro do contrato: a Caixa informa que o contrato deve ser apresentado registrado em até 30 dias após a assinatura."),
            _lista("Erros comuns que atrasam ou encarecem o processo", [
                "Pedir o crédito sem simular: a parcela aprovada pode não caber no orçamento ao longo dos anos. Teste valores de entrada e prazo antes.",
                "Usar toda a reserva na entrada e ficar sem caixa para ITBI, registro e mudança.",
                "Comparar só a taxa de juros: o custo efetivo total inclui seguros e tarifa. Compare propostas pelo CET.",
                "Deixar para depois a documentação do vendedor e do imóvel, que depende de cartórios e de terceiros.",
                "Ignorar que dá para somar a renda do cônjuge ou companheiro(a) quando a renda de uma pessoa só não cobre a parcela."]),
            _sec("Como definir a entrada",
                 f"A entrada é o que você paga com recursos próprios (ou FGTS) e o que sobra é o valor financiado. Cada banco tem um percentual máximo de financiamento, o LTV, e a entrada mínima é o que falta para chegar ao valor do imóvel (veja {_a('aprenda-ltv-financiamento-imobiliario', 'LTV')}). Entrada maior significa parcela menor e menos juros no total; entrada menor deixa o financiamento mais acessível agora, mas mais caro ao longo do contrato. O simulador de cada página mostra esse efeito ao mover o campo de entrada."),
            _fontes([
                ("https://www.caixa.gov.br/voce/habitacao/financiamento/aquisicao-imovel-novo/Paginas/default.aspx", "Caixa: etapas do financiamento habitacional"),
                ("https://www.caixa.gov.br/Downloads/habitacao-documentos-gerais/Lista_docs_definitiva.pdf", "Caixa: documentação básica para solicitação de crédito imobiliário"),
            ]) + f'\n        <p class="text-xs text-slate-500">Conferido em {DATA_CONFERIDO}. A lista e as etapas de cada banco podem ser diferentes e mudam; confirme com a instituição escolhida.</p>',
        ]),
        "cta_href": "comparador-bancos",
        "cta_texto": "Simular antes de pedir o crédito",
    }

    # ---------------------------------------------------------------- 4
    mcmv = {
        "slug": "aprenda-minha-casa-minha-vida-faixas-limites",
        "titulo_h1": "Minha Casa, Minha Vida: faixas de renda, valor do imóvel e como consultar",
        "titulo_pagina": "Minha Casa Minha Vida: faixas e limites | Datalab Global",
        "meta_description": "As faixas de renda do Minha Casa, Minha Vida, os tetos de valor do imóvel vigentes (Portaria 333/2026) e onde confirmar as regras atuais.",
        "resumo_card": "Quem pode usar o programa, os limites de renda e de valor do imóvel por faixa, e onde confirmar as regras antes de decidir.",
        "corpo_html": "\n        ".join([
            "<p>O Minha Casa, Minha Vida é o programa habitacional do governo federal que oferece condições especiais de financiamento a famílias de menor renda e, desde 2025, também à classe média. Os limites de renda e de valor do imóvel mudam por portaria, por isso este guia traz a data da conferência e aponta onde confirmar as regras vigentes.</p>",
            _lista(f"Faixas urbanas (renda bruta familiar mensal), conferido em {DATA_CONFERIDO}", [
                f"{_b('Faixa 1:')} até R$ 3.200.",
                f"{_b('Faixa 2:')} de R$ 3.200,01 a R$ 5.000.",
                f"{_b('Faixa 3:')} de R$ 5.000,01 a R$ 9.600.",
                f"{_b('Faixa 4 (classe média):')} de R$ 9.600,01 a R$ 13.000."],
                 "Segundo a Portaria MCID nº 333, de 30 de março de 2026, e a divulgação oficial do governo federal:"),
            _lista("Valor máximo do imóvel", [
                f"{_b('Faixas 3 e 4:')} o teto do valor do imóvel é de R$ 400 mil na Faixa 3 e de R$ 600 mil na Faixa 4 (antes, R$ 350 mil e R$ 500 mil).",
                f"{_b('Faixas 1 e 2:')} o teto varia conforme a localidade, entre R$ 210 mil e R$ 275 mil."],
                 "Os limites de valor dependem da faixa e, nas faixas 1 e 2, do município:"),
            _sec("Como consultar as regras atuais",
                 f"Como as faixas e os tetos são atualizados por portaria, confirme sempre na fonte: a página do programa no Ministério das Cidades e a página do Minha Casa, Minha Vida na Caixa, que também permite simular e iniciar o pedido. Páginas e matérias antigas ainda circulam com valores de anos anteriores (por exemplo, o limite da Faixa 1 do lançamento de 2023), então verifique a data de qualquer informação que encontrar."),
            _sec("O que muda na simulação",
                 f"As condições do programa (taxa de juros, subsídio para as faixas mais baixas, seguros e regras de enquadramento) seguem regras próprias, definidas pelo governo federal e pelo agente financeiro, e não são as mesmas do financiamento de mercado. As taxas e simulações deste site usam as {_a('taxas-financiamento-imobiliario', 'taxas médias de mercado do Banco Central')}, então servem de comparação: se o seu imóvel e a sua renda se enquadram no programa, peça a simulação do MCMV ao banco e compare com a de mercado, pelo CET e pela primeira parcela."),
            _sec("Como saber se a renda cobre",
                 f"Mesmo no programa, a parcela precisa caber na renda. Para ter uma ordem de grandeza, veja a {_a('renda-para-financiar-imovel', 'renda mínima por valor do imóvel')} e entenda a diferença entre {_a('aprenda-sac-x-price', 'SAC e Price')}. Em geral, os requisitos incluem não ser proprietário de imóvel residencial e não ter financiamento ativo no sistema de habitação, mas cada faixa tem as próprias exigências: confirme as condições do seu caso na Caixa ou no portal do programa."),
            _lista("Passo a passo para confirmar o seu caso", [
                "Some a renda bruta mensal de todas as pessoas da família que vão compor o financiamento e veja em qual faixa você se enquadra.",
                "Consulte o valor máximo do imóvel para a sua faixa e, nas faixas 1 e 2, para o município onde o imóvel fica.",
                "Entre na página do programa na Caixa (ou no banco que opera o MCMV) e faça a simulação com as condições do programa.",
                "Compare com a simulação de mercado pelo CET e pela primeira parcela, não só pela taxa.",
                "Confirme os requisitos do seu caso: por exemplo, em geral não ser proprietário de imóvel residencial e não ter financiamento ativo no sistema de habitação."]),
            _sec("Subsídio e financiamento",
                 "Segundo o Ministério das Cidades, o programa combina financiamento com condições específicas e, nas faixas de renda mais baixas, subsídio; a Faixa 4, voltada à classe média, é financiamento do programa, sem a produção subsidiada das faixas iniciais. Os percentuais de juros e de subsídio mudam conforme a faixa, a região e as decisões do governo para o programa, por isso não os reproduzimos aqui: peça a simulação oficial."),
            _fontes([
                ("https://www.gov.br/cidades/pt-br/acesso-a-informacao/institucional/base-juridica/portarias/2026/PORTARIAMCIDN333DE30DEMARODE2026PORTARIAMCIDN333DE30DEMARODE2026DOUImprensaNacional.pdf", "Portaria MCID nº 333, de 30 de março de 2026 (Diário Oficial da União)"),
                ("https://www.gov.br/secom/pt-br/acompanhe-a-secom/noticias/2026/04/nova-portaria-atualiza-limites-de-renda-bruta-familiar-admitidos-para-familias-atendidas-pelo-minha-casa-minha-vida", "Secom/Governo Federal: nova portaria atualiza limites de renda"),
                ("https://www.gov.br/cidades/pt-br/assuntos/materias/programa-minha-casa-minha-vida", "Ministério das Cidades: programa Minha Casa, Minha Vida"),
                ("https://www.caixa.gov.br/voce/habitacao/minha-casa-minha-vida/Paginas/default.aspx", "Caixa: Minha Casa, Minha Vida"),
            ]) + f'\n        <p class="text-xs text-slate-500">Regras conferidas em {DATA_CONFERIDO}. Portarias novas podem alterar faixas e tetos: a fonte oficial prevalece sobre este texto.</p>',
        ]),
        "cta_href": "renda-para-financiar-imovel",
        "cta_texto": "Ver a renda necessária",
    }

    # ---------------------------------------------------------------- 5
    planta = {
        "slug": "aprenda-imovel-na-planta-incc-juros-de-obra",
        "titulo_h1": "Imóvel na planta: INCC, juros de obra e quando o financiamento entra",
        "titulo_pagina": "Imóvel na planta: INCC e juros de obra | Datalab Global",
        "meta_description": "Como funcionam as parcelas de um imóvel na planta, o que é o INCC, os juros de obra e quando começa o financiamento bancário.",
        "resumo_card": "Antes da entrega, as parcelas são corrigidas pelo INCC; depois, o financiamento começa a amortizar. Entenda cada fase e o que conferir no contrato.",
        "corpo_html": "\n        ".join([
            "<p>Comprar na planta (ou em construção) é diferente de comprar um imóvel pronto: o pagamento acontece em duas fases, antes e depois da entrega das chaves, e cada uma tem um custo e um risco diferentes. Entender essa divisão ajuda a comparar propostas e a não se surpreender com parcelas que mudam.</p>",
            _sec("Fase 1: durante a obra",
                 f"Enquanto o imóvel é construído, as parcelas pagas à construtora costumam ser corrigidas pelo {_b('INCC')} (Índice Nacional de Custo da Construção), calculado pela FGV IBRE. Ele acompanha os custos de construção residencial, com um grupo de materiais, equipamentos e serviços e outro de mão de obra, medidos em sete capitais. Como o índice varia todo mês, o valor das parcelas e o saldo a pagar sobem ao longo da obra. Em setembro de 2026, por exemplo, o INCC-M subiu 0,25% no mês e 6,61% em 12 meses (dado da FGV, conferido em {DATA_CONFERIDO}; consulte o número do mês na FGV).",
                 "Nesta fase, o valor final do imóvel não é o de tabela: ele inclui a correção. Pergunte à construtora qual é o índice contratado (INCC, IPCA ou outro), se há teto de correção e como a correção é aplicada ao saldo."),
            _sec("Fase 2: juros de obra e financiamento bancário",
                 f"Quando o comprador financia pelo banco ainda durante a obra, o dinheiro é {_b('liberado à construtora conforme o avanço da obra')}, e os juros e a atualização incidem sobre o valor já liberado, não sobre o total contratado (a cartilha da Caixa sobre juros na fase de obras descreve esse mecanismo). Por isso, esses encargos crescem à medida que a obra avança. O pagamento do principal (a amortização) só começa depois da conclusão da obra e da averbação do imóvel na matrícula, com o habite-se.",
                 "Nos financiamentos com liberação em etapas, esses juros e encargos são cobrados enquanto o imóvel ainda não está pronto, e é o que se costuma chamar de juros de obra. Confira no contrato o que é cobrado, quando começa, como é calculado e em que dia é debitado."),
            _sec("Fase 3: depois da entrega",
                 f"Com o imóvel pronto e averbado, o saldo é financiado e entra no sistema normal de amortização, com parcelas em SAC ou Price (veja {_a('aprenda-sac-x-price', 'SAC x Price')}). É nesse momento que a simulação do {_a('comparador-bancos', 'comparador de bancos')} passa a valer: o valor a financiar é o saldo que restar e o prazo é o contratado com o banco. Em alguns casos, o banco faz o repasse do saldo devedor da construtora; a aprovação do crédito é do banco, e ele pode recusar, por isso confirme a aprovação antes da entrega."),
            _sec("Um exemplo de como a correção pesa",
                 f"Só como aritmética, com números hipotéticos: se o saldo a pagar à construtora fosse de R$ 200.000 e o INCC acumulasse 6,61% em 12 meses, o saldo corrigido seria de R$ 213.220 antes de qualquer pagamento do período. Quanto mais longa a obra e maior o saldo a pagar depois da entrada, maior o efeito. Por isso vale perguntar quanto do preço é pago antes da entrega e quanto fica para o financiamento."),
            _lista("O que conferir no contrato", [
                "O índice de correção das parcelas (INCC, IPCA ou outro) e se existe limite.",
                "A data prevista de entrega e as consequências de atraso.",
                "Quando começam os juros de obra, como são calculados e quem paga.",
                "A partir de quando o financiamento bancário é contratado e a taxa prevista para essa fase.",
                "O CET do financiamento final, não só a taxa: veja " + _a("aprenda-cet-iof-financiamento-imobiliario", "o que entra no CET") + ".",
                "A exigência de quitação com recursos próprios: na fase de obra, a Caixa informa que a quitação antecipada só é possível com recursos próprios, sem usar o FGTS."]),
            _fontes([
                ("https://www.caixa.gov.br/Downloads/habitacao-documentos-gerais/Cartilha_Juros_Fase_de_Obras.pdf", "Caixa: juros na fase de obras"),
                ("https://www.caixa.gov.br/Downloads/habitacao-documentos-gerais/cartilha-habitacao-PF-construcao-conclusao-reforma-ampliacao-de-unidades-habitacionais.pdf", "Caixa: cartilha de construção, conclusão, reforma e ampliação"),
                ("https://www.caixa.gov.br/voce/habitacao/construcao/Paginas/default.aspx", "Caixa: financiamento para construção"),
                ("https://portalibre.fgv.br/en/ncci", "FGV IBRE: INCC"),
                ("https://crecies.gov.br/saiba-como-e-feita-a-correcao-das-parcelas-do-financiamento-imobiliario/", "CRECI-ES: correção das parcelas do imóvel na planta pelo INCC"),
                ("https://portal.fgv.br/noticias/incc-m-setembro-2026", "FGV: INCC-M de setembro de 2026"),
            ]) + f'\n        <p class="text-xs text-slate-500">Conferido em {DATA_CONFERIDO}. As regras da fase de obra variam por banco, programa e contrato; o contrato assinado e a planilha de CET prevalecem sobre este texto.</p>',
        ]),
        "cta_href": "comparador-bancos",
        "cta_texto": "Simular o financiamento do saldo",
    }

    # ---------------------------------------------------------------- 6
    fin, imov, prazo, taxa = 400_000, 500_000, 360, 11.5
    r = calc(fin, prazo, taxa, imov)
    ef = ((1 + taxa / 100 / 12) ** 12 - 1) * 100
    mip1, dfi, adm = fin * 0.0003, imov * 0.000129, 25.0
    seguros = {
        "slug": "aprenda-seguro-mip-dfi-financiamento-imobiliario",
        "titulo_h1": "Seguro MIP e DFI no financiamento imobiliário: o que cobrem e como reduzir o CET",
        "titulo_pagina": "Seguro MIP e DFI do financiamento | Datalab Global",
        "meta_description": "O que são os seguros MIP e DFI, por que são obrigatórios, se você pode escolher a seguradora e como isso afeta o CET do financiamento.",
        "resumo_card": "Os dois seguros obrigatórios do financiamento, o que cobrem, o que a Susep diz sobre a escolha da seguradora e como pesam no CET.",
        "corpo_html": "\n        ".join([
            "<p>Todo financiamento imobiliário tem dois seguros no meio das parcelas: o MIP e o DFI. Eles fazem parte do custo mensal e entram no CET, por isso dois bancos com a mesma taxa de juros podem ter parcelas e custo total diferentes.</p>",
            _sec("O que cobrem",
                 f"O {_b('MIP')} (Morte e Invalidez Permanente) quita ou abate a dívida se o mutuário morrer ou ficar inválido. O {_b('DFI')} (Danos Físicos ao Imóvel) cobre danos ao imóvel financiado, como incêndio e desabamento. A regulamentação do seguro habitacional exige coberturas de morte e invalidez permanente e/ou de danos físicos ao imóvel, conforme o financiamento; a Caixa informa que a contratação de DFI e MIP é obrigatória nos financiamentos habitacionais."),
            _sec("Posso escolher a seguradora?",
                 f"Em geral, sim. A Susep, órgão que regula o setor, informa que o seguro habitacional não precisa ser contratado com o próprio banco financiador: você pode contratá-lo com ele ou com outra seguradora autorizada a operar, desde que a apólice atenda às exigências do contrato. Para comparar propostas, existe o {_b('CESH')} (Custo Efetivo do Seguro Habitacional), calculado conforme as regras da Susep: peça-o ao banco e à seguradora. Antes de trocar, confirme com o banco os requisitos da apólice e o prazo para aceitá-la."),
            _sec("Como o simulador estima o peso dos seguros",
                 f"O CET que você vê no simulador é calculado por TIR e inclui estimativas de mercado: MIP de 0,030% do saldo devedor por mês, DFI de 0,0129% do valor do imóvel por mês e tarifa de administração de R$ 25 por mês. Esses valores variam por banco, idade e seguradora; usamos uma estimativa única para poder comparar. Um exemplo: financiando {reais(fin)} de um imóvel de {reais(imov)} em {prazo} meses a {p(taxa)}% ao ano, na SAC, o primeiro mês tem cerca de {reais(mip1)} de MIP, {reais(dfi)} de DFI e {reais(adm)} de tarifa, somando {reais(mip1 + dfi + adm)} além de juros e amortização. A taxa de {p(taxa)}% ao ano equivale a {p(ef)}% ao ano efetivos, e o CET calculado é de {p(r['cet_sac'])}% ao ano: a diferença são os seguros e a tarifa.",
                 "Como o MIP incide sobre o saldo devedor, ele pesa mais no começo e diminui com o tempo; o DFI incide sobre o valor do imóvel e é fixo. Veja a metodologia completa em " + _a("metodologia", "como calculamos") + "."),
            _sec("Quando o seguro é cobrado",
                 "Os seguros são cobrados todo mês, junto com a parcela, durante todo o contrato. Por isso entram no fluxo de pagamentos que gera o CET: um seguro mais caro por mês, mesmo com taxa de juros igual, aumenta o custo efetivo total e o valor final pago."),
            _lista("Como reduzir o CET", [
                "Compare propostas pelo CET, não só pela taxa: " + _a("aprenda-cet-iof-financiamento-imobiliario", "o que entra no CET") + ".",
                "Peça o CESH e cotações de outras seguradoras autorizadas e veja se o banco aceita a apólice.",
                "Aumente a entrada: um financiamento menor reduz juros e o MIP, que incide sobre o saldo. Veja " + _a("aprenda-ltv-financiamento-imobiliario", "LTV") + ".",
                "Considere prazo menor, se a parcela couber: menos juros e menos seguro acumulado.",
                "Faça amortizações extras: o saldo cai e o MIP cai junto. Veja " + _a("aprenda-amortizacao-extraordinaria", "amortização extraordinária") + ".",
                "Se já financia, avalie a " + _a("aprenda-portabilidade-financiamento-imobiliario", "portabilidade") + " para um contrato com seguro e tarifas melhores."]),
            _lista("Perguntas para fazer ao banco antes de assinar", [
                "Qual o valor mensal do MIP e do DFI no primeiro ano e como ele muda ao longo do contrato?",
                "O banco aceita a apólice de outra seguradora? Quais exigências a apólice precisa cumprir e em quanto tempo ela é aceita?",
                "Qual o CESH das opções oferecidas?",
                "Qual a tarifa de administração mensal e se ela é reajustada?",
                "Os seguros estão destacados na planilha de evolução da dívida?"]),
            _fontes([
                ("https://www.gov.br/susep/pt-br/assuntos/meu-futuro-seguro/seguros-previdencia-e-capitalizacao/seguros/seguro-habitacional", "Susep: seguro habitacional"),
                ("https://www.caixa.gov.br/voce/habitacao/perguntas-frequentes-novos-financiamentos/Paginas/default.aspx", "Caixa: perguntas frequentes sobre financiamento (seguros DFI e MIP)"),
                ("https://www2.susep.gov.br/safe/scripts/bnweb/bnmapi.exe?router=upload%2F26564", "CNSP/Susep: norma do seguro habitacional (CESH)"),
            ]) + f'\n        <p class="text-xs text-slate-500">Conferido em {DATA_CONFERIDO}. As alíquotas do simulador são estimativas; a sua apólice e o seu contrato definem os valores reais.</p>',
        ]),
        "cta_href": "comparador-bancos",
        "cta_texto": "Comparar CET entre bancos",
    }

    return [portab, itbi, passo, mcmv, planta, seguros]
