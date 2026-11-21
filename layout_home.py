"""HTML da home nova (simulador no estilo do 006: tema escuro, vidro, cartões por campo, painel de resultado, faixa de 3 números,
"já tem uma proposta?", pagar a mais e tela de confirmação antes do parceiro). Os marcadores @@NOME@@ são trocados por gerador.py.

Sem atributo style nem script inline (a CSP da home não permite). Os desenhos são SVG com atributos; a lógica fica em src/home.js
e a conta em src/calculo_home.js. Python 3.10: sem f-string aninhado (este arquivo nem usa f-string).
"""
from logo import LOGO

CABECALHO = """<a href="#conteudo" class="skip">Ir para o conteúdo</a>
<header class="top">
  <div class="wrap">
    <div class="marca">
      <a href="https://www.datalabglobal.com/" class="brand" aria-label="Datalab Global, site principal">@@LOGO@@<span class="wm"><b>Datalab</b><i>GLOBAL</i></span></a>
      <a href="/" class="prod" aria-label="Simulador de financiamento imobiliário, página inicial">Imóvel</a>
    </div>
    <nav class="m" aria-label="Principal">@@NAV@@</nav>
    <div class="free"><span class="dot"></span>Simulação gratuita</div>
    <details class="menu">
      <summary>Menu</summary>
      <nav aria-label="Menu">@@NAVMOBILE@@</nav>
    </details>
  </div>
</header>
"""

RODAPE = """<footer class="rod">
  <div class="wrap">
    <div class="cols">
      <div>
        <div class="marca">
          <a href="https://www.datalabglobal.com/" class="brand" aria-label="Datalab Global, site principal">@@LOGO@@<span class="wm"><b>Datalab</b><i>GLOBAL</i></span></a>
          <a href="/" class="prod" aria-label="Simulador de financiamento imobiliário, página inicial">Imóvel</a>
        </div>
        <p>Simulador de financiamento imobiliário: parcela SAC e Price, CET e economia pagando a mais, com a taxa média de cada banco.</p>
      </div>
      <nav aria-label="Entenda"><h2>Entenda</h2><ul>@@FOOT_ENTENDA@@</ul></nav>
      <nav aria-label="Dados"><h2>Dados</h2><ul>@@FOOT_DADOS@@</ul></nav>
      <nav aria-label="Legal"><h2>Legal</h2><ul>@@FOOT_LEGAL@@</ul></nav>
      <nav aria-label="Outros simuladores da Datalab Global"><h2>Outros simuladores</h2><ul>@@FOOT_OUTROS@@</ul></nav>
    </div>
    <div class="base">
      <p>Taxas atualizadas em @@ATUALIZADO@@. @@FONTE_TAXAS@@</p>
      <p>Datalab Global é marca de @@RAZAO@@, CNPJ @@CNPJ@@. Contato: <a href="mailto:@@EMAIL@@">@@EMAIL@@</a>.</p>
      <p>A simulação é uma estimativa, não é proposta de crédito. O crédito depende de análise e aprovação, sem garantia de aprovação.</p>
    </div>
  </div>
</footer>
"""

MAIN = """  <section class="hero">
    <h1>Simulador de financiamento <em>imobiliário</em></h1>
    <p>Veja a parcela, o custo total e o CET com a taxa média de cada banco, e quanto você economiza pagando a mais.</p>
    <div class="fine">Grátis · sem cadastro · estimativa, não proposta</div>
  </section>

  <div class="grid" id="simulador">
    <section class="panel" aria-labelledby="t-cenario">
      <h2 id="t-cenario">Seu financiamento</h2>
      <div class="f">
        <label for="btn-banco" id="lb-banco">Banco <span id="banco-fonte">@@D_BANCO_FONTE@@</span></label>
        <div class="inp combo sel" id="combo-banco">
          <button type="button" class="cbtn" id="btn-banco" aria-haspopup="listbox" aria-expanded="false" aria-controls="lista-banco" aria-labelledby="lb-banco btn-banco"><span id="banco-nome">@@D_BANCO_NOME@@</span><svg viewBox="0 0 12 8" width="12" height="8" aria-hidden="true"><path d="M1 1.5l5 5 5-5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
          <ul class="opts" id="lista-banco" role="listbox" aria-labelledby="lb-banco" hidden></ul>
        </div>
        <div class="hint" id="banco-hint">@@D_BANCO_HINT@@</div>
      </div>
      <div class="f">
        <label for="campo-imovel">Valor do imóvel <span>aproximado</span></label>
        <div class="inp"><span class="pre">R$</span><input id="campo-imovel" type="text" inputmode="numeric" autocomplete="off" value="@@D_IMOVEL@@" class="num"></div>
        <input id="range-imovel" type="range" aria-label="Valor do imóvel, controle deslizante" min="100000" max="3000000" step="10000" value="@@V_IMOVEL@@">
        <div class="slabel"><span>R$ 100 mil</span><span>R$ 3 milhões</span></div>
      </div>
      <div class="f">
        <label for="campo-entrada">Entrada <span id="entrada-pct">@@D_ENTRADA_PCT@@</span></label>
        <div class="inp"><span class="pre">R$</span><input id="campo-entrada" type="text" inputmode="numeric" autocomplete="off" value="@@D_ENTRADA@@" class="num"></div>
        <input id="range-entrada" type="range" aria-label="Entrada, controle deslizante" min="@@V_ENTRADA_MIN@@" max="@@V_ENTRADA_MAX@@" step="5000" value="@@V_ENTRADA@@">
        <div class="slabel"><span id="min-entrada">@@D_ENTRADA_MIN@@</span><span id="max-entrada">@@D_ENTRADA_MAX@@</span></div>
        <div class="hint warn" id="msg-ajuste" hidden></div>
      </div>
      <div class="f">
        <label for="campo-prazo">Prazo <span id="prazo-faixa">de 5 a @@V_PRAZO_MAX@@ anos</span></label>
        <div class="inp combo" id="combo-prazo">
          <input id="campo-prazo" type="text" inputmode="numeric" autocomplete="off" value="@@V_PRAZO@@" class="num" role="combobox" aria-autocomplete="none" aria-expanded="false" aria-controls="lista-prazo" aria-describedby="msg-prazo" aria-label="Prazo em anos: escolha na lista ou digite">
          <em>anos</em>
          <button type="button" class="caret" id="btn-prazo" aria-label="Abrir a lista de prazos" aria-haspopup="listbox" aria-controls="lista-prazo"><svg viewBox="0 0 12 8" width="12" height="8" aria-hidden="true"><path d="M1 1.5l5 5 5-5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
          <ul class="opts" id="lista-prazo" role="listbox" aria-label="Prazos disponíveis" hidden></ul>
        </div>
        <input id="range-prazo" type="range" aria-label="Prazo em anos, controle deslizante" min="5" max="@@V_PRAZO_MAX@@" step="1" value="@@V_PRAZO@@">
        <div class="slabel"><span>5 anos</span><span id="max-prazo">@@V_PRAZO_MAX@@ anos</span></div>
        <div class="hint warn" id="msg-prazo" hidden></div>
      </div>
      <details class="outra" id="det-taxa">
        <summary>Já tem uma proposta? Use a taxa dela</summary>
        <div class="oi">
          <label for="campo-taxa-prop">Taxa da proposta <span>% ao ano</span></label>
          <div class="inp"><input id="campo-taxa-prop" type="text" inputmode="decimal" autocomplete="off" placeholder="ex.: 10,99" class="num" aria-describedby="msg-taxa-prop"><em>% a.a.</em></div>
          <label class="ck" for="ck-taxa-nominal"><input type="checkbox" id="ck-taxa-nominal"> É a taxa nominal (juros do mês = taxa ÷ 12)</label>
          <div class="hint" id="msg-taxa-prop">Deixe em branco para usar a taxa média do banco. Se a proposta mostra “taxa nominal” e “taxa efetiva”, use a efetiva ou marque a caixa acima ao digitar a nominal. A conta não inclui a TR.</div>
        </div>
      </details>
    </section>

    <section class="panel resp" id="resultado" aria-labelledby="t-resultado" aria-live="polite">
      <h2 class="kicker kres" id="t-resultado">Resultado da simulação</h2>
      <div class="res">
        <div>
          <div class="kicker" id="r-kicker">@@D_KICKER@@</div>
          <div class="big num"><span id="r-parcela">@@D_PARCELA@@</span> <small>/mês</small></div>
          <div class="dim" id="r-sub">@@D_SUB@@</div>
          <div class="dim ult" id="r-ultima" @@D_ULT_HIDDEN@@>@@D_ULT@@</div>
          <hr class="sep">
          <div class="dim lab">Total estimado ao final</div>
          <div class="mid num" id="r-total">@@D_TOTAL@@</div>
          <div class="dim">CET estimado: <b class="num" id="r-cet">@@D_CET@@</b> ao ano · <a href="/metodologia">como calculamos</a></div>
        </div>
        <div class="ctx sis">
          <div class="t" id="lb-sistema">Tipo de parcela</div>
          <div class="seg s2" role="radiogroup" aria-labelledby="lb-sistema">
            <input type="radio" name="sistema" id="sis-sac" value="sac" @@D_CK_SAC@@><label for="sis-sac">SAC <small>parcela cai</small></label>
            <input type="radio" name="sistema" id="sis-price" value="price" @@D_CK_PRICE@@><label for="sis-price">Price <small>parcela fixa</small></label>
          </div>
          <div class="hint" id="hint-sistema">@@D_HINT_SIS@@</div>
        </div>
      </div>
      <div class="callout"><p id="r-resumo">@@D_RESUMO@@</p></div>
      <div class="rosca">
        <svg viewBox="0 0 120 120" width="120" height="120" role="img" id="rosca-svg" aria-label="Do total pago, @@D_PCT_JUROS@@% é juros">
          <circle cx="60" cy="60" r="46" fill="none" stroke="#e3a96b" stroke-width="14"/>
          <circle id="rosca-cred" cx="60" cy="60" r="46" fill="none" stroke="#10b981" stroke-width="14" stroke-dasharray="@@D_ROSCA_P@@ 289.03" transform="rotate(-90 60 60)"/>
          <text x="60" y="61" text-anchor="middle" class="rc-n" id="rosca-pct">@@D_PCT_JUROS@@%</text>
          <text x="60" y="77" text-anchor="middle" class="rc-t">em juros</text>
        </svg>
        <div class="rc-l">
          <div class="kicker">Para onde vai o total</div>
          <div class="lg"><span><s></s>Financiado</span><b class="num" id="rosca-cred-v">@@D_L_CRED@@</b></div>
          <div class="lg"><span><s class="jr"></s>Juros</span><b class="num" id="rosca-juros-v">@@D_L_JUROS@@</b></div>
        </div>
      </div>
      <div class="rodape-res">
        <div class="cta">
          <div><strong>Faça sua proposta</strong><span class="s">Com um parceiro de crédito · sem compromisso</span></div>
          <button type="button" class="btn" id="btn-cta">Consultar opções →</button>
        </div>
        <div class="fine2">Estimativa: a taxa final e a aprovação dependem da análise de crédito e do imóvel.</div>
        <div class="copiar"><button type="button" id="btn-copiar">Copiar o link desta simulação</button><span id="msg-copiado" role="status"></span></div>
      </div>
    </section>
  </div>

  <div class="uso" aria-label="Quanto do valor do imóvel é financiado">
    <div class="uso-t"><span class="t">Valor do imóvel</span><b class="v num" id="c-imovel">@@D_IMOVEL_RS@@</b></div>
    <div class="uso-b"><svg class="bar" id="bar-ltv" width="100%" height="12" role="img" aria-label="Quanto do valor do imóvel é financiado">
            <rect width="100%" height="12" rx="6" fill="rgba(255,255,255,.1)"/><rect id="bar-fill" width="@@D_BARRA@@%" height="12" rx="6" fill="#10b981"/><rect id="bar-mark" x="@@D_LTV_MARCA@@%" y="-3" width="2" height="18" fill="#e2e8f0"/>
          </svg></div>
    <div class="uso-l">
      <div class="lg"><span><s></s>Financiado</span><b class="num" id="c-fin">@@D_FIN_LINHA@@</b></div>
      <div class="lg"><span><s class="lim"></s><span id="c-limite-rot">@@D_LIMITE_ROT@@</span></span><b class="num" id="c-limite">@@D_LIMITE@@</b></div>
    </div>
  </div>

  <div class="kpis" aria-label="Três números para ler o custo">
    <div class="kp"><span class="t">Quita por volta de</span><b class="num" id="k-quita">@@D_K_QUITA@@</b><small id="k-quita-s">@@D_K_QUITA_S@@</small></div>
    <div class="kp"><span class="t">Cada R$ 1 financiado custa</span><b class="num" id="k-juro1">@@D_K_JURO1@@</b><small>de juros até o fim</small></div>
    <div class="kp"><span class="t">Renda para a parcela</span><b class="num" id="k-renda">@@D_K_RENDA@@</b><small>por mês, parcela de até 30% da renda</small></div>
  </div>
  <p class="hint kpn" id="k-nota">@@D_K_NOTA@@</p>

  <section class="blk" id="bancos" aria-labelledby="t-bancos">
    <div class="kicker">Comparação</div>
    <h2 id="t-bancos">O mesmo financiamento em cada banco</h2>
    <p class="lead">Mesmo imóvel, mesmo prazo e a taxa média de cada banco, do menor para o maior CET. A entrada e o prazo são ajustados ao limite de cada banco. Toque no nome para ver as condições dele.</p>
    <div class="panel bks">
      <ol class="bk-lista" id="bk-lista">@@D_BANCOS@@</ol>
    </div>
    <div class="note"><b>Sobre estes números.</b> <span id="bk-nota">@@D_BK_NOTA@@</span> Veja também o <a href="/comparador-bancos">comparador de bancos</a> e a <a href="/financiamento-imobiliario">parcela por valor e prazo</a>.</div>
  </section>

  <section class="blk amsec" id="amortizacao" aria-labelledby="t-amort">
    <div class="kicker">Pagar antes</div>
    <h2 id="t-amort">Pagar antes pode poupar milhares de reais</h2>
    <p class="lead amlead">No começo do contrato, boa parte da parcela é juros. Quando você paga um valor a mais, a dívida em que os juros incidem diminui: você termina antes e paga menos. Veja quanto isso vale no seu cenário.</p>
    <div class="split amwhy">
      <div class="split-t">
        <h3 class="sub"><span class="n" aria-hidden="true">1</span>Os juros vêm primeiro</h3>
        <div class="giga num"><span id="amort-pct">@@D_AMORT_PCT@@</span><small>da parcela do 1º ano é juros</small></div>
        <p class="lead" id="amort-resumo">@@D_AMORT_RESUMO@@</p>
      </div>
      <div class="panel graf">
        <div class="leg"><span><s class="jr"></s>Juros do ano</span><span><s></s>Amortização do ano</span><span><s class="ln"></s>Saldo devedor</span></div>
        <svg id="amort-graf" viewBox="0 0 640 220" preserveAspectRatio="none" role="img" aria-label="Gráfico: juros e amortização de cada ano e saldo devedor"></svg>
        <div class="eixo"><span>Ano 1</span><span id="amort-ano-fim">Ano @@V_PRAZO@@</span></div>
      </div>
    </div>

    <details class="amort amsim" id="det-amsim">
      <summary>Simular: pagar a mais todo mês ou amortizar de uma vez</summary>
      <div class="panel amx">
        <h3 class="sub"><span class="n" aria-hidden="true">2</span>Quanto você poupa pagando a mais</h3>
        <p class="amsub">Escolha o valor e o momento. Quanto mais cedo, maior a economia.</p>
        <div class="amin">
          <div class="f">
            <label for="campo-extra">Pagar a mais todo mês <span>além da parcela</span></label>
            <div class="inp"><span class="pre">R$</span><input id="campo-extra" type="text" inputmode="numeric" autocomplete="off" value="500" class="num"><em>/mês</em></div>
          </div>
          <div class="f">
            <label for="campo-unico">Amortização única <span>um valor de uma vez</span></label>
            <div class="inp"><span class="pre">R$</span><input id="campo-unico" type="text" inputmode="numeric" autocomplete="off" value="20.000" class="num"></div>
          </div>
          <div class="f">
            <label for="range-quando">Quando fazer a única <span id="quando-rot">daqui a 1 ano</span></label>
            <input id="range-quando" type="range" min="0" max="@@V_QUANDO_MAX@@" step="1" value="1" aria-describedby="quando-rot">
          </div>
        </div>
        <div class="amcards" id="am-cartoes"></div>
        <p class="qtxt" id="am-texto"></p>
      </div>
      <div class="amdicas">
        <div class="amd"><h4>Prazo ou parcela?</h4><p>Reduzir o prazo costuma poupar mais juros: as últimas parcelas somem. Reduzir a parcela dá folga no orçamento do mês. Escolha pelo que você precisa agora.</p></div>
        <div class="amd"><h4>Veja o que o contrato diz</h4><p>Pergunte ao banco como pedir a amortização, se há valor mínimo ou tarifa e se o abatimento reduz o prazo ou a parcela. O Código de Defesa do Consumidor (art. 52, § 2º) prevê a liquidação antecipada com redução proporcional dos juros. Leia mais no <a href="/aprenda-amortizacao-extraordinaria">guia de amortização</a>.</p></div>
        <div class="amd"><h4>Compare com outro uso do dinheiro</h4><p>Amortizar equivale a render a taxa da dívida: <b id="am-taxa-aa">@@D_AM_TAXA@@</b> ao ano nesta simulação. Compare com o que o mesmo dinheiro renderia, já descontados impostos, e mantenha uma reserva de emergência. Não é recomendação de investimento.</p></div>
      </div>
    </details>

    <details class="amort" id="det-amort">
      <summary>Ver a amortização ano a ano</summary>
      <div class="tw"><table id="tab-amort">
        <caption id="amort-cap">@@D_AMORT_CAP@@</caption>
        <thead><tr><th scope="col">Ano</th><th scope="col">Juros</th><th scope="col">Amortização</th><th scope="col">Saldo devedor</th></tr></thead>
        <tbody id="amort-corpo">@@D_AMORT_LINHAS@@</tbody>
        <tfoot id="amort-rodape">@@D_AMORT_TOTAL@@</tfoot>
      </table></div>
      <div class="hint" id="amort-nota">@@D_AMORT_NOTA@@</div>
    </details>
  </section>

  <section class="blk" aria-labelledby="t-guias">
    <div class="kicker">Guias</div>
    <h2 id="t-guias">Entenda antes de decidir</h2>
    <div class="cols3">@@CARTOES@@</div>
  </section>

  <section class="blk split faqs" aria-labelledby="t-faq">
    <div class="split-t">
      <div class="kicker">Dúvidas</div>
      <h2 id="t-faq">Perguntas frequentes</h2>
    </div>
    <div class="faq">@@FAQ@@</div>
  </section>

  <dialog id="dlg-confirma" aria-labelledby="dlg-titulo">
    <h3 id="dlg-titulo">Antes de continuar</h3>
    <p>Você vai preencher um formulário de um <b>parceiro de crédito</b>, que analisa o seu pedido. A página dele mostra o nome da empresa.</p>
    <ul>
      <li>Valor do imóvel, entrada e prazo aproximados, e o banco que você prefere.</li>
      <li>Dados pessoais e de renda, e documentos do imóvel mais adiante.</li>
      <li>O parceiro pode consultar bureaus de crédito, conforme o aviso dele.</li>
      <li>Simular aqui não é aprovação, e a taxa final depende da análise.</li>
      <li>Você não é obrigado a contratar.</li>
    </ul>
    <p class="dim">Veja a <a href="@@URL_PRIVACIDADE@@">política de privacidade</a> e <a href="/metodologia">como calculamos</a>.</p>
    <div class="row"><a class="btn" id="a-parceiro" href="@@PARCEIRO@@" target="_blank" rel="noopener sponsored">Continuar para o parceiro →</a><button type="button" class="ghost" id="btn-voltar">Voltar e ajustar</button></div>
  </dialog>
"""
