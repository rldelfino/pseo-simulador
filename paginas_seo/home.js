/* Interface do simulador da home. Só textContent e atributos SVG (nada de innerHTML). Depende de calculo_home.js (window.DatalabImovel)
   e dos dados dos bancos em <script type="application/json" id="dados-home">.
   Sem cookies e sem dado pessoal: o simulador não envia nada para fora, só mede o uso (banco e prazo) no Umami, sem identificar ninguém. */
(function () {
  'use strict';
  var H = window.DatalabImovel;
  var tag = document.getElementById('dados-home');
  if (!H || !tag) return;
  var D;
  try { D = JSON.parse(tag.textContent); } catch (e) { return; }

  var IMOVEL_MIN = 100000, IMOVEL_MAX = 3000000, ENTRADA_MAX = 0.9, PRAZO_MIN = 5;
  var estado = { banco: D.padrao.banco, imovel: D.padrao.imovel, entrada: D.padrao.entrada, anos: D.padrao.anos, sistema: D.padrao.sistema,
    taxaProp: 0, nominal: false, extra: 500, unico: 20000, quando: 1 };
  var usou = false, usouTaxaProp = false, usouAmort = false, abriuAmort = false, desenhos = 0, timerUrl = null, timerCopiado = null;
  var BRL_NUM = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
  var NS = 'http://www.w3.org/2000/svg', CIRC = 289.0265;
  var MESES_CURTOS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

  function $(id) { return document.getElementById(id); }
  function clamp(v, a, b) { return Math.min(b, Math.max(a, v)); }
  function limpar(no) { while (no.firstChild) no.removeChild(no.firstChild); }
  function evento(nome, dados) { try { if (window.umami && window.umami.track) window.umami.track(nome, dados); } catch (e) { /* medição nunca quebra o simulador */ } }
  function el(tag2, classe, texto) { var e = document.createElement(tag2); if (classe) e.className = classe; if (texto !== undefined) e.textContent = texto; return e; }
  function svgEl(tag2, atributos) { var e = document.createElementNS(NS, tag2); Object.keys(atributos).forEach(function (k) { e.setAttribute(k, String(atributos[k])); }); return e; }
  function mil(v) { return v >= 1000000 ? (v / 1000000).toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + ' milhões' : 'R$ ' + Math.round(v / 1000) + ' mil'; }
  function pct1(v) { return H.pct(v, 1); }
  function lerNumero(texto) {
    var t = String(texto).replace(/[^\d.,]/g, '');
    if (t.indexOf(',') >= 0) t = t.replace(/\./g, '').replace(',', '.');
    else if (/\.\d{3}(\.|$)/.test(t)) t = t.replace(/\./g, '');
    var n = Number(t);
    return isFinite(n) ? n : 0;
  }
  function preencherRange(r, valor) {
    var min = Number(r.min), max = Number(r.max), v = clamp(valor, min, max);
    r.value = v;
    // sem style inline (a CSP não permite): uma regra de CSS por inteiro de 0 a 100, escolhida por data-p
    r.setAttribute('data-p', String(Math.round(max > min ? ((v - min) / (max - min)) * 100 : 0)));
  }

  // ---- banco, taxa e limites ----
  function acharBanco(k) {
    if (k === 'mercado') return { k: 'mercado', n: 'Média dos bancos', t: D.mercado.t, l: D.mercado.l, p: D.mercado.p, f: 'media' };
    for (var x = 0; x < D.bancos.length; x++) if (D.bancos[x].k === k) return D.bancos[x];
    return acharBanco('mercado');
  }
  function banco() { return acharBanco(estado.banco); }
  function taxaPropria() { return estado.taxaProp >= 3 && estado.taxaProp <= 40; }
  function taxaAA() { return taxaPropria() ? estado.taxaProp : banco().t; }
  function pctEntradaMin() { return 1 - banco().l; }
  function entradaMin() { return Math.ceil((estado.imovel * pctEntradaMin()) / 1000) * 1000; }
  function entradaMax() { return Math.floor((estado.imovel * ENTRADA_MAX) / 1000) * 1000; }
  function prazoMaxAnos() { return Math.floor(banco().p / 12); }
  function ent() { return clamp(estado.entrada, entradaMin(), entradaMax()); }
  function sac() { return estado.sistema === 'sac'; }

  function ajustar() {
    estado.imovel = clamp(estado.imovel, IMOVEL_MIN, IMOVEL_MAX);
    estado.anos = clamp(Math.round(estado.anos), PRAZO_MIN, prazoMaxAnos());
    return ent() !== estado.entrada;
  }

  function fonteBanco(b) {
    if (b.f === 'bcb') return 'média contratada, BCB ' + D.ref;
    if (b.f === 'media') return 'mediana dos bancos, BCB ' + D.ref;
    return 'estimativa de mercado';
  }

  // ---- desenhos ----
  function desenharRosca(r, sem) {
    var pj = !sem && r.total > 0 ? r.juros / r.total : 0;
    $('rosca-cred').setAttribute('stroke-dasharray', (sem ? 0 : (1 - pj) * CIRC).toFixed(1) + ' ' + CIRC.toFixed(2));
    $('rosca-pct').textContent = sem ? '—' : Math.round(pj * 100) + '%';
    $('rosca-cred-v').textContent = sem ? '—' : H.brl(r.financiado);
    $('rosca-juros-v').textContent = sem ? '—' : H.brl(r.juros);
    $('rosca-svg').setAttribute('aria-label', sem ? 'Sem simulação' : 'Do total pago, ' + Math.round(pj * 100) + '% é juros');
  }

  function desenharGraf(linhas, fin, parcelaAno) {
    var g = $('amort-graf');
    limpar(g);
    var n = linhas.length, W = 640, Hh = 220, topo = 12, base = Hh - 4, util = base - topo, slot = W / n, larg = Math.max(4, slot * 0.68);
    var pontos = ['0,' + (base - util).toFixed(1)];
    linhas.forEach(function (x, k) {
      var x0 = k * slot + (slot - larg) / 2, hA = (x.amortizacao / parcelaAno) * util, hJ = (x.juros / parcelaAno) * util;
      g.appendChild(svgEl('rect', { 'class': 'g-a', x: x0.toFixed(1), y: (base - hA).toFixed(1), width: larg.toFixed(1), height: Math.max(0, hA).toFixed(1) }));
      g.appendChild(svgEl('rect', { 'class': 'g-j', x: x0.toFixed(1), y: (base - hA - hJ).toFixed(1), width: larg.toFixed(1), height: Math.max(0, hJ).toFixed(1) }));
      pontos.push(((k + 1) * slot).toFixed(1) + ',' + (base - (x.saldo / fin) * util).toFixed(1));
    });
    g.appendChild(svgEl('polyline', { 'class': 'g-s', points: pontos.join(' ') }));
    $('amort-ano-fim').textContent = 'Ano ' + n;
    g.setAttribute('aria-label', 'Gráfico: no ano 1, ' + H.brl(linhas[0].juros) + ' de juros e ' + H.brl(linhas[0].amortizacao) + ' de amortização; no ano ' + n + ', ' +
      H.brl(linhas[n - 1].juros) + ' de juros e ' + H.brl(linhas[n - 1].amortizacao) + ' de amortização. O saldo devedor cai até zero.');
  }

  function celula(tag2, texto, escopo) { var c = el(tag2, '', texto); if (escopo) c.setAttribute('scope', escopo); return c; }

  function desenharAmort(r, i, meses, sem) {
    var corpo = $('amort-corpo'), rodape = $('amort-rodape');
    limpar(corpo); limpar(rodape);
    if (sem) { $('amort-resumo').textContent = 'Ajuste o valor do imóvel ou a entrada para ver a amortização.'; $('amort-pct').textContent = '—'; $('amort-nota').textContent = ''; limpar($('amort-graf')); return; }
    var linhas = H.amortizacaoAnual(r.financiado, i, meses, estado.sistema);
    var j1 = linhas[0].juros, pago = linhas[0].juros + linhas[0].amortizacao, pj = Math.round((j1 / pago) * 100);
    $('amort-pct').textContent = pj + '%';
    desenharGraf(linhas, r.financiado, pago);
    $('amort-resumo').textContent = 'No primeiro ano, ' + H.brl(j1) + ' dos ' + H.brl(pago) + ' que você paga são juros (' + pj + '%). ' +
      (sac() ? 'No SAC a amortização é a mesma todo mês: a parcela cai porque os juros caem.' : 'A parcela é fixa: com o tempo ela amortiza mais a dívida e os juros caem.');
    $('amort-cap').textContent = sac() ? 'Parcela que cai: juros, amortização e saldo devedor no fim de cada ano' : 'Parcela fixa: juros, amortização e saldo devedor no fim de cada ano';
    var juros = 0;
    linhas.forEach(function (x) {
      var tr = el('tr');
      tr.appendChild(celula('th', String(x.ano), 'row'));
      tr.appendChild(celula('td', H.brl(x.juros)));
      tr.appendChild(celula('td', H.brl(x.amortizacao)));
      tr.appendChild(celula('td', H.brl(x.saldo)));
      corpo.appendChild(tr);
      juros += x.juros;
    });
    var t = el('tr');
    t.appendChild(celula('th', 'Total', 'row')); t.appendChild(celula('td', H.brl(juros))); t.appendChild(celula('td', H.brl(r.financiado))); t.appendChild(celula('td', ''));
    rodape.appendChild(t);
    $('amort-nota').textContent = 'Conta com a taxa de ' + H.pct(taxaAA()) + ' ao ano' + (estado.nominal && taxaPropria() ? ' (nominal)' : ' (efetiva)') + ', ' +
      (sac() ? 'amortização constante (SAC)' : 'parcela fixa (Price)') + ', sem TR, seguros, tarifas nem IOF.';
  }

  function dur(m) {
    var a = Math.floor(m / 12), r = m % 12, p = [];
    if (a) p.push(a + (a === 1 ? ' ano' : ' anos'));
    if (r) p.push(r + (r === 1 ? ' mês' : ' meses'));
    return p.length ? p.join(' e ') : '0 mês';
  }
  function rotQuando(q) { return q === 0 ? 'no início, antes da 1ª parcela' : 'daqui a ' + q + (q === 1 ? ' ano' : ' anos'); }
  function cartaoAm(titulo, big, linhas, melhor) {
    var d = el('div', 'amc' + (melhor ? ' best' : ''));
    if (melhor) d.appendChild(el('span', 'tg', 'Maior economia'));
    d.appendChild(el('h4', '', titulo));
    d.appendChild(el('div', 'big num', big));
    d.appendChild(el('div', 'bl', 'a menos em juros'));
    var ul = el('ul');
    linhas.forEach(function (l) { ul.appendChild(el('li', '', l)); });
    d.appendChild(ul);
    return d;
  }

  function desenharPagarMais(r, i, meses, sem) {
    var cartoes = $('am-cartoes'), texto = $('am-texto');
    limpar(cartoes);
    var maxQ = Math.max(0, estado.anos - 1);
    estado.quando = clamp(estado.quando, 0, maxQ);
    var rq = $('range-quando');
    rq.min = '0'; rq.max = String(maxQ);
    preencherRange(rq, estado.quando);
    $('quando-rot').textContent = rotQuando(estado.quando);
    $('am-taxa-aa').textContent = H.pct(taxaAA());
    if (sem) { texto.textContent = 'Ajuste o valor do imóvel ou a entrada para simular.'; return; }
    var s = estado.sistema, extra = Math.max(0, estado.extra), unico = Math.max(0, estado.unico), mq = estado.quando * 12;
    if (!(extra > 0) && !(unico > 0)) { texto.textContent = 'Digite um valor mensal ou uma amortização única para ver a economia.'; return; }
    var base = H.amortizarAntes(r.financiado, i, meses, s, 0, 0, mq, 'prazo'), lista = [];
    function tempo(res) { return ['Quita ' + dur(base.meses - res.meses) + ' antes', 'Termina em ' + dur(res.meses) + ', em vez de ' + dur(base.meses)]; }
    var quando = estado.quando === 0 ? 'no início' : rotQuando(estado.quando);
    if (extra > 0) { var rE = H.amortizarAntes(r.financiado, i, meses, s, extra, 0, 0, 'prazo'); lista.push({ t: 'Pagando ' + H.brl(extra) + ' a mais por mês', p: base.juros - rE.juros, l: tempo(rE) }); }
    if (unico > 0) {
      var rP = H.amortizarAntes(r.financiado, i, meses, s, 0, unico, mq, 'prazo'), rC = H.amortizarAntes(r.financiado, i, meses, s, 0, unico, mq, 'parcela');
      lista.push({ t: 'Única de ' + H.brl(unico) + ' ' + quando + ', reduzindo o prazo', p: base.juros - rP.juros, l: rP.meses <= mq ? ['Quita a dívida inteira'] : tempo(rP) });
      lista.push({ t: 'Única de ' + H.brl(unico) + ' ' + quando + ', reduzindo a parcela', p: base.juros - rC.juros,
        l: rC.meses <= mq ? ['Quita a dívida inteira'] : ['A parcela cai de ' + H.brl(base.parcelaNova) + ' para ' + H.brl(rC.parcelaNova), 'O prazo continua o mesmo'] });
    }
    if (extra > 0 && unico > 0) {
      var rJ = H.amortizarAntes(r.financiado, i, meses, s, extra, unico, mq, 'prazo');
      lista.unshift({ t: 'Os dois juntos, reduzindo o prazo', p: base.juros - rJ.juros, l: rJ.meses <= mq ? ['Quita a dívida inteira'] : tempo(rJ) });
    }
    var melhor = 0;
    lista.forEach(function (c, k) { if (c.p > lista[melhor].p) melhor = k; });
    lista.forEach(function (c, k) { cartoes.appendChild(cartaoAm(c.t, H.brl(c.p), c.l, lista.length > 1 && k === melhor)); });
    texto.textContent = 'Valores em reais de hoje: não descontam o que esse dinheiro renderia em outra aplicação nem tarifas do banco. Confirme no contrato como o abatimento é aplicado.';
  }

  // lista "o mesmo financiamento em cada banco", do menor para o maior CET
  function desenharBancos() {
    var ul = $('bk-lista'), meses = estado.anos * 12, linhas = [];
    limpar(ul);
    D.bancos.forEach(function (b) {
      var m = Math.min(meses, b.p), e = Math.max(ent(), Math.ceil((estado.imovel * (1 - b.l)) / 1000) * 1000);
      var t = taxaPropria() ? taxaAA() : b.t;
      var r = H.simular(estado.imovel, Math.min(e, estado.imovel - 10000), m / 12, t, estado.sistema, taxaPropria() && estado.nominal);
      linhas.push({ b: b, r: r, ajuste: m < meses || e > ent() });
    });
    linhas.sort(function (a, c) { return a.r.cet - c.r.cet; });
    linhas.forEach(function (x) {
      var li = el('li', 'bk' + (x.b.k === estado.banco ? ' us' : ''));
      var a = el('a', 'bk-n', x.b.n);
      a.href = '/' + x.b.h;
      li.appendChild(a);
      var t = el('span', 'bk-t num', H.pct(taxaPropria() ? taxaAA() : x.b.t) + ' a.a.');
      li.appendChild(t);
      var p = el('span', 'bk-p num');
      p.appendChild(el('b', '', H.brl(x.r.p1)));
      p.appendChild(el('small', '', sac() ? '1ª parcela' : 'parcela'));
      li.appendChild(p);
      var c = el('span', 'bk-c num');
      c.appendChild(el('b', '', H.pct(x.r.cet)));
      c.appendChild(el('small', '', 'CET a.a.'));
      li.appendChild(c);
      if (x.ajuste) li.appendChild(el('span', 'bk-aj', 'entrada ou prazo ajustados ao limite do banco'));
      ul.appendChild(li);
    });
    $('bk-nota').textContent = taxaPropria() ? 'Todos os bancos usam a taxa da sua proposta (' + H.pct(taxaAA()) + ' a.a.): a diferença que sobra vem de entrada mínima e prazo máximo.'
      : 'Taxas: média contratada em ' + D.ref + ' (Banco Central); BRB e Poupex são estimativas de mercado. CET com seguros e tarifa estimados, só para comparar.';
  }

  function enderecoDaSimulacao(absoluto) {
    var q = [];
    q.push('v=' + Math.round(estado.imovel)); q.push('e=' + Math.round(ent())); q.push('p=' + estado.anos);
    q.push('b=' + encodeURIComponent(estado.banco)); q.push('s=' + estado.sistema);
    if (taxaPropria()) { q.push('t=' + String(estado.taxaProp).replace('.', ',')); if (estado.nominal) q.push('n=1'); }
    return (absoluto ? window.location.origin : '') + '/?' + q.join('&') + '#simulador';
  }
  function lerEndereco() {
    var p;
    try { p = new URLSearchParams(window.location.search); } catch (e) { return; }
    var v = lerNumero(p.get('v') || ''), e2 = lerNumero(p.get('e') || ''), pz = Math.round(lerNumero(p.get('p') || '')), b = p.get('b') || '', s = p.get('s') || '', t = lerNumero(p.get('t') || '');
    if (v >= IMOVEL_MIN && v <= IMOVEL_MAX) estado.imovel = v;
    if (e2 > 0) estado.entrada = e2;
    if (pz >= PRAZO_MIN && pz <= 35) estado.anos = pz;
    if (b === 'mercado' || D.bancos.some(function (x) { return x.k === b; })) estado.banco = b;
    if (s === 'sac' || s === 'price') estado.sistema = s;
    if (t >= 3 && t <= 40) { estado.taxaProp = t; estado.nominal = p.get('n') === '1'; }
  }
  function atualizarEndereco() {
    clearTimeout(timerUrl);
    timerUrl = setTimeout(function () { try { window.history.replaceState(null, '', enderecoDaSimulacao(false)); } catch (e) { /* sem histórico: o botão de copiar continua valendo */ } }, 400);
  }
  async function copiarLink() {
    var url = enderecoDaSimulacao(true), ok = false;
    try { window.history.replaceState(null, '', enderecoDaSimulacao(false)); } catch (e) { /* ignora */ }
    try { if (navigator.clipboard && navigator.clipboard.writeText) { await navigator.clipboard.writeText(url); ok = true; } } catch (e) { /* plano B abaixo */ }
    if (!ok) {
      try {
        var t = document.createElement('textarea');
        t.value = url; t.setAttribute('readonly', ''); t.className = 'sr';
        document.body.appendChild(t); t.select(); ok = document.execCommand('copy'); document.body.removeChild(t);
      } catch (e) { ok = false; }
    }
    var msg = $('msg-copiado');
    msg.textContent = ok ? 'Link copiado. Quem abrir vê esta mesma simulação.' : 'Não deu para copiar sozinho. O link já está na barra de endereço do navegador.';
    clearTimeout(timerCopiado);
    timerCopiado = setTimeout(function () { msg.textContent = ''; }, 4000);
    evento('copiou-link', { banco: estado.banco, prazo: estado.anos });
  }

  function desenhar(foco) {
    var ajustou = ajustar(), b = banco(), meses = estado.anos * 12, aa = taxaAA();
    var sem = estado.imovel - ent() < 1;
    var nominal = taxaPropria() && estado.nominal;
    var i = H.taxaMensal(aa, nominal);
    var r = H.simular(estado.imovel, ent(), estado.anos, aa, estado.sistema, nominal);

    $('banco-nome').textContent = estado.banco === 'mercado' ? b.n : b.n;
    $('banco-fonte').textContent = taxaPropria() ? 'taxa da sua proposta' : fonteBanco(b);
    $('banco-hint').textContent = taxaPropria() ? 'A conta usa a taxa da proposta (' + H.pct(aa) + ' a.a.). Entrada mínima ' + Math.round(pctEntradaMin() * 100) + '% e prazo até ' + prazoMaxAnos() + ' anos, do banco escolhido.'
      : 'Taxa de ' + H.pct(aa) + ' ao ano (' + H.pct(i * 100) + ' ao mês). Entrada mínima de ' + Math.round(pctEntradaMin() * 100) + '% e prazo de até ' + prazoMaxAnos() + ' anos.' + (b.f === 'est' ? ' Sem dado do Banco Central para este banco.' : '');
    if (foco !== 'imovel') $('campo-imovel').value = BRL_NUM.format(estado.imovel);
    if (foco !== 'entrada') $('campo-entrada').value = BRL_NUM.format(ent());
    if (foco !== 'prazo') $('campo-prazo').value = String(estado.anos);
    preencherRange($('range-imovel'), estado.imovel);
    var re = $('range-entrada');
    re.min = String(entradaMin()); re.max = String(Math.max(entradaMin(), entradaMax()));
    preencherRange(re, ent());
    $('min-entrada').textContent = mil(Number(re.min)); $('max-entrada').textContent = mil(Number(re.max));
    $('entrada-pct').textContent = Math.round((ent() / estado.imovel) * 100) + '% do imóvel';
    var rp = $('range-prazo');
    rp.max = String(prazoMaxAnos()); preencherRange(rp, estado.anos);
    $('max-prazo').textContent = prazoMaxAnos() + ' anos';
    $('prazo-faixa').textContent = 'de ' + PRAZO_MIN + ' a ' + prazoMaxAnos() + ' anos';
    marcarPrazos();
    $('sis-' + estado.sistema).checked = true;
    $('hint-sistema').textContent = sac() ? 'Cai todo mês e paga menos juros no total.' : 'Parcela igual todo mês.';
    var aviso = $('msg-ajuste');
    if (ajustou && foco !== 'entrada') { aviso.hidden = false; aviso.textContent = 'Ajustamos a entrada para ' + (ent() === entradaMin() ? 'o mínimo de ' : 'o máximo de ') + H.brl(ent()) + '.'; }
    else if (!ajustou) aviso.hidden = true;

    $('r-kicker').textContent = sac() ? '1ª parcela estimada' : 'Parcela estimada';
    var ult = $('r-ultima');
    ult.hidden = !(sac() && !sem);
    if (!ult.hidden) ult.textContent = 'A parcela cai todo mês, até ' + H.brl(r.pu) + ' na última.';
    $('r-parcela').textContent = sem ? '—' : H.brl(r.p1);
    $('r-sub').textContent = 'em ' + meses + ' meses · taxa ' + H.pct(aa) + ' a.a.' + (taxaPropria() ? ' (sua proposta)' : '');
    $('r-total').textContent = sem ? '—' : H.brl(r.total);
    $('r-cet').textContent = sem ? '—' : H.pct(r.cet);
    $('r-resumo').textContent = sem ? 'Reduza a entrada para ver o custo.' : 'Você financia ' + H.brl(r.financiado) + ' e paga ' + H.brl(r.total) + ' no total: ' + H.brl(r.juros) + ' a mais em juros.';
    $('btn-cta').disabled = sem;
    desenharRosca(r, sem);

    $('c-imovel').textContent = H.brl(estado.imovel);
    $('bar-fill').setAttribute('width', Math.min(100, r.ltv * 100).toFixed(1) + '%');
    $('bar-mark').setAttribute('x', Math.min(99, b.l * 100).toFixed(1) + '%');
    $('c-fin').textContent = H.brl(r.financiado) + ' · ' + Math.round(r.ltv * 100) + '%';
    $('c-limite-rot').textContent = 'Limite do banco (' + Math.round(b.l * 100) + '%)';
    $('c-limite').textContent = H.brl(estado.imovel * b.l);

    // faixa de três números
    if (sem) { $('k-quita').textContent = '—'; $('k-quita-s').textContent = ''; $('k-juro1').textContent = '—'; $('k-renda').textContent = '—'; }
    else {
      var d = new Date();
      d.setMonth(d.getMonth() + meses + 2);
      $('k-quita').textContent = MESES_CURTOS[d.getMonth()] + '/' + d.getFullYear();
      $('k-quita-s').textContent = meses + ' parcelas, se contratar este mês';
      $('k-juro1').textContent = 'R$ ' + (r.juros / r.financiado).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      $('k-renda').textContent = H.brl(r.renda);
    }
    $('k-nota').textContent = 'Taxas: média contratada em ' + D.ref + ' (Banco Central), atualizadas em ' + D.atualizado + '. Estimativa, não é oferta. Renda: ' + (sac() ? 'a 1ª parcela' : 'a parcela') + ' dividida por 30%, conta nossa, não é análise de crédito.';

    var fo = $('campo-taxa-prop');
    if (foco !== 'taxaprop') fo.value = estado.taxaProp > 0 ? String(estado.taxaProp).replace('.', ',') : '';
    $('ck-taxa-nominal').checked = estado.nominal;
    var mt = $('msg-taxa-prop');
    if (estado.taxaProp > 0 && !taxaPropria()) { mt.textContent = 'Use uma taxa entre 3% e 40% ao ano. Enquanto isso, a conta usa a taxa média do banco.'; mt.className = 'hint warn'; }
    else { mt.textContent = taxaPropria() ? 'Conta com a taxa da sua proposta' + (estado.nominal ? ', nominal: juros do mês = ' + H.pct(estado.taxaProp / 12) + '.' : ', efetiva ao ano: juros do mês = ' + H.pct(H.taxaMensal(estado.taxaProp, false) * 100) + '.') : 'Deixe em branco para usar a taxa média do banco. Se a proposta mostra “taxa nominal” e “taxa efetiva”, use a efetiva ou marque a caixa acima ao digitar a nominal. A conta não inclui a TR.'; mt.className = 'hint'; }

    desenharAmort(r, i, meses, sem);
    desenharPagarMais(r, i, meses, sem);
    desenharBancos();
    desenhos += 1;
    if (desenhos > 1) atualizarEndereco();
  }

  function interagiu() { if (usou) return; usou = true; evento('usou-simulador-imovel', { banco: estado.banco, prazo: estado.anos }); }
  function mexeuTaxaProp() { if (usouTaxaProp) return; usouTaxaProp = true; evento('usou-taxa-propria', { prazo: estado.anos }); }
  function mexeuAmort() { if (usouAmort) return; usouAmort = true; evento('simulou-amortizacao', { prazo: estado.anos }); }

  function ligarCampo(id, chave, minimo, foco, aoMexer) {
    var c = $(id), mexeu = aoMexer || interagiu;
    c.addEventListener('input', function (e) { var v = lerNumero(e.target.value); if (v >= minimo) { estado[chave] = v; mexeu(); desenhar(foco); } });
    c.addEventListener('blur', function (e) { estado[chave] = lerNumero(e.target.value); mexeu(); desenhar(); });
    c.addEventListener('keydown', function (e) { if (e.key === 'Enter') e.target.blur(); });
  }

  // ---- listas suspensas (banco e prazo): combobox ARIA, sem <select> ----
  var marcarPrazos = function () {};
  function ligarBanco() {
    var btn = $('btn-banco'), lista = $('lista-banco'), caixa = $('combo-banco'), ativo = 0, itens = [{ k: 'mercado', n: 'Média dos bancos', t: D.mercado.t }].concat(D.bancos);
    itens.forEach(function (b, k) {
      var li = el('li');
      li.id = 'banco-op-' + k; li.setAttribute('role', 'option'); li.setAttribute('data-k', b.k);
      li.appendChild(el('span', '', b.n));
      li.appendChild(el('small', '', H.pct(b.t) + ' a.a.'));
      lista.appendChild(li);
    });
    function aberta() { return !lista.hidden; }
    function marcar(k) {
      ativo = k;
      Array.prototype.forEach.call(lista.children, function (li, n) { li.setAttribute('aria-selected', li.getAttribute('data-k') === estado.banco ? 'true' : 'false'); li.className = n === k ? 'ativo' : ''; });
      var cur = $('banco-op-' + k);
      if (cur) {
        btn.setAttribute('aria-activedescendant', cur.id);
        if (cur.offsetTop < lista.scrollTop) lista.scrollTop = cur.offsetTop;
        else if (cur.offsetTop + cur.offsetHeight > lista.scrollTop + lista.clientHeight) lista.scrollTop = cur.offsetTop + cur.offsetHeight - lista.clientHeight;
      }
    }
    function indice() { for (var n = 0; n < itens.length; n++) if (itens[n].k === estado.banco) return n; return 0; }
    function abrir() { lista.hidden = false; btn.setAttribute('aria-expanded', 'true'); caixa.className = 'inp combo sel aberto'; marcar(indice()); }
    function fechar() { lista.hidden = true; btn.setAttribute('aria-expanded', 'false'); btn.removeAttribute('aria-activedescendant'); caixa.className = 'inp combo sel'; }
    function escolher(k) { estado.banco = itens[k].k; interagiu(); fechar(); desenhar(); evento('escolheu-banco', { banco: estado.banco }); }
    btn.addEventListener('click', function () { if (aberta()) fechar(); else abrir(); });
    btn.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); if (!aberta()) { abrir(); return; } marcar(clamp(ativo + (e.key === 'ArrowDown' ? 1 : -1), 0, itens.length - 1)); }
      else if (e.key === 'Enter' && aberta()) { e.preventDefault(); escolher(ativo); }
      else if (e.key === 'Escape' && aberta()) { e.preventDefault(); fechar(); }
      else if (e.key === 'Tab') fechar();
    });
    lista.addEventListener('mousedown', function (e) { e.preventDefault(); });
    lista.addEventListener('click', function (e) { var li = e.target.closest ? e.target.closest('li') : null; if (li) escolher(Number(li.id.replace('banco-op-', ''))); });
    document.addEventListener('click', function (e) { if (aberta() && !caixa.contains(e.target)) fechar(); });
  }

  function ligarPrazo() {
    var c = $('campo-prazo'), msg = $('msg-prazo'), lista = $('lista-prazo'), caixa = $('combo-prazo'), btn = $('btn-prazo'), ativo = 0;
    for (var a = PRAZO_MIN; a <= 35; a++) {
      var li = el('li');
      li.id = 'prazo-op-' + a; li.setAttribute('role', 'option'); li.setAttribute('data-v', String(a));
      li.appendChild(el('span', '', a + ' anos'));
      li.appendChild(el('small', '', (a * 12) + ' meses'));
      lista.appendChild(li);
    }
    marcarPrazos = function () {
      Array.prototype.forEach.call(lista.children, function (li2) {
        var v = Number(li2.getAttribute('data-v'));
        li2.hidden = v > prazoMaxAnos();
        li2.setAttribute('aria-selected', v === estado.anos ? 'true' : 'false');
      });
    };
    function aberta() { return !lista.hidden; }
    function marcar(v) {
      ativo = v;
      Array.prototype.forEach.call(lista.children, function (li2) { li2.className = Number(li2.getAttribute('data-v')) === v ? 'ativo' : ''; });
      var cur = $('prazo-op-' + v);
      if (cur) {
        c.setAttribute('aria-activedescendant', cur.id);
        if (cur.offsetTop < lista.scrollTop) lista.scrollTop = cur.offsetTop;
        else if (cur.offsetTop + cur.offsetHeight > lista.scrollTop + lista.clientHeight) lista.scrollTop = cur.offsetTop + cur.offsetHeight - lista.clientHeight;
      }
    }
    function abrir() {
      lista.hidden = false; c.setAttribute('aria-expanded', 'true'); caixa.className = 'inp combo aberto'; marcarPrazos(); marcar(estado.anos);
      var cur = $('prazo-op-' + estado.anos);
      if (cur) lista.scrollTop = Math.max(0, cur.offsetTop - lista.clientHeight / 2 + cur.offsetHeight / 2);
    }
    function fechar() { lista.hidden = true; c.setAttribute('aria-expanded', 'false'); c.removeAttribute('aria-activedescendant'); caixa.className = 'inp combo'; }
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && aberta()) fechar(); });
    function escolher(v) { estado.anos = v; msg.hidden = true; interagiu(); fechar(); desenhar(); }
    c.addEventListener('input', function (e) {
      var v = Math.round(lerNumero(e.target.value));
      if (aberta()) fechar();
      if (v >= PRAZO_MIN && v <= prazoMaxAnos()) { estado.anos = v; msg.hidden = true; interagiu(); desenhar('prazo'); }
    });
    c.addEventListener('blur', function (e) {
      var v = Math.round(lerNumero(e.target.value)), max = prazoMaxAnos();
      if (v >= PRAZO_MIN && v <= max) msg.hidden = true;
      else { v = clamp(v > 0 ? v : estado.anos, PRAZO_MIN, max); msg.hidden = false; msg.textContent = 'O prazo vai de ' + PRAZO_MIN + ' a ' + max + ' anos neste banco. Ajustamos para ' + v + ' anos.'; }
      estado.anos = v; interagiu(); desenhar();
    });
    c.addEventListener('keydown', function (e) {
      var max = prazoMaxAnos();
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); if (!aberta()) { abrir(); return; } marcar(clamp(ativo + (e.key === 'ArrowDown' ? 1 : -1), PRAZO_MIN, max)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (aberta()) escolher(ativo); else e.target.blur(); }
      else if (e.key === 'Escape') { if (aberta()) { e.preventDefault(); fechar(); } }
      else if (e.key === 'Tab') fechar();
    });
    btn.addEventListener('mousedown', function (e) { e.preventDefault(); });
    btn.addEventListener('click', function () { if (aberta()) fechar(); else abrir(); });
    lista.addEventListener('mousedown', function (e) { e.preventDefault(); });
    lista.addEventListener('click', function (e) { var li2 = e.target.closest ? e.target.closest('li') : null; if (li2) escolher(Number(li2.getAttribute('data-v'))); });
    document.addEventListener('click', function (e) { if (aberta() && !caixa.contains(e.target)) fechar(); });
    $('range-prazo').addEventListener('input', function (e) { estado.anos = Number(e.target.value); msg.hidden = true; interagiu(); desenhar(); });
  }

  function iniciar() {
    lerEndereco();
    if (taxaPropria()) $('det-taxa').open = true;
    ligarCampo('campo-imovel', 'imovel', IMOVEL_MIN, 'imovel');
    ligarCampo('campo-entrada', 'entrada', 1000, 'entrada');
    ligarCampo('campo-extra', 'extra', 1, 'extra', mexeuAmort);
    ligarCampo('campo-unico', 'unico', 1, 'unico', mexeuAmort);
    $('range-imovel').addEventListener('input', function (e) { estado.imovel = Number(e.target.value); interagiu(); desenhar(); });
    $('range-entrada').addEventListener('input', function (e) { estado.entrada = Number(e.target.value); interagiu(); desenhar(); });
    $('range-quando').addEventListener('input', function (e) { estado.quando = Number(e.target.value); mexeuAmort(); desenhar(); });
    ligarBanco();
    ligarPrazo();
    $('btn-copiar').addEventListener('click', copiarLink);
    Array.prototype.forEach.call(document.querySelectorAll('input[name="sistema"]'), function (rd) {
      rd.addEventListener('change', function (e) { estado.sistema = e.target.value; interagiu(); desenhar(); });
    });
    $('campo-taxa-prop').addEventListener('input', function (e) { estado.taxaProp = lerNumero(e.target.value); mexeuTaxaProp(); desenhar('taxaprop'); });
    $('campo-taxa-prop').addEventListener('blur', function () { desenhar(); });
    $('campo-taxa-prop').addEventListener('keydown', function (e) { if (e.key === 'Enter') e.target.blur(); });
    $('ck-taxa-nominal').addEventListener('change', function (e) { estado.nominal = e.target.checked; mexeuTaxaProp(); desenhar(); });
    $('det-amsim').addEventListener('toggle', function (e) { if (e.target.open && !abriuAmort) { abriuAmort = true; evento('abriu-amortizacao', { prazo: estado.anos }); } });

    var dlg = $('dlg-confirma');
    function devolverFoco() { try { $('btn-cta').focus({ preventScroll: true }); } catch (e) { /* ignora */ } }
    function fechar() { if (typeof dlg.close === 'function') dlg.close(); else { dlg.removeAttribute('open'); devolverFoco(); } }
    $('btn-cta').addEventListener('click', function () {
      evento('abriu-confirmacao', { banco: estado.banco, prazo: estado.anos });
      if (typeof dlg.showModal === 'function') dlg.showModal(); else dlg.setAttribute('open', '');
    });
    dlg.addEventListener('close', devolverFoco);
    $('btn-voltar').addEventListener('click', fechar);
    dlg.addEventListener('click', function (e) {
      if (e.target !== dlg) return;
      var r = dlg.getBoundingClientRect();
      if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) fechar();
    });
    $('a-parceiro').addEventListener('click', function () { evento('cta-parceiro', { banco: estado.banco, prazo: estado.anos }); });
    desenhar();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
})();
