/* Conta do simulador da home. Espelha calculo_home.py (os testes comparam as duas). Sem DOM: só números. */
(function (raiz) {
  'use strict';
  var MIP = 0.00030, DFI = 0.000129, ADMIN = 25.0, RENDA = 0.30;

  function taxaMensal(aaPct, nominal) {
    return nominal ? aaPct / 100 / 12 : Math.pow(1 + aaPct / 100, 1 / 12) - 1;
  }
  function pmt(v, i, n) {
    if (n <= 0) return 0;
    return i > 0 ? v * (i * Math.pow(1 + i, n)) / (Math.pow(1 + i, n) - 1) : v / n;
  }

  function cet(fin, meses, i, imovel, sistema) {
    if (fin <= 0 || meses <= 0) return 0;
    var saldo = fin, fixa = sistema === 'price' ? pmt(fin, i, meses) : 0, fluxo = [];
    for (var m = 0; m < meses; m++) {
      var j = saldo * i, a = sistema === 'sac' ? fin / meses : fixa - j;
      fluxo.push(a + j + saldo * MIP + imovel * DFI + ADMIN);
      saldo -= a;
    }
    function vpl(r) {
      var t = -fin, f = 1 / (1 + r), d = 1;
      for (var k = 0; k < fluxo.length; k++) { d *= f; t += fluxo[k] * d; }
      return t;
    }
    var lo = 0, hi = 0.05;
    for (var n = 0; n < 60; n++) { var mid = (lo + hi) / 2; if (vpl(mid) > 0) lo = mid; else hi = mid; }
    var tir = (lo + hi) / 2;
    return Math.round((Math.pow(1 + tir, 12) - 1) * 10000) / 100;
  }

  function simular(imovel, entrada, anos, aaPct, sistema, nominal) {
    var meses = Math.round(anos * 12), fin = Math.max(0, imovel - entrada), i = taxaMensal(aaPct, nominal);
    var amort = meses ? fin / meses : 0, jurosSac = 0, saldo = fin;
    for (var m = 0; m < meses; m++) { jurosSac += saldo * i; saldo -= amort; }
    var p1, pu, juros;
    if (sistema === 'sac') { p1 = amort + fin * i; pu = amort * (1 + i); juros = jurosSac; }
    else { p1 = pu = pmt(fin, i, meses); juros = p1 * meses - fin; }
    return {
      meses: meses, financiado: fin, i: i, p1: p1, pu: pu, total: fin + juros, juros: juros,
      cet: cet(fin, meses, i, imovel, sistema),
      renda: fin > 0 ? Math.ceil((p1 / RENDA) / 50) * 50 : 0,
      ltv: imovel ? fin / imovel : 0
    };
  }

  function amortizarAntes(fin, i, meses, sistema, extra, unico, mesUnico, modo) {
    var saldo = fin, amort = meses ? fin / meses : 0, fixa = pmt(fin, i, meses), juros = 0, m = 0;
    var nova = sistema === 'price' ? fixa : amort + saldo * i;
    while (saldo > 0.005 && m < meses * 2) {
      if (unico > 0 && m === mesUnico) {
        saldo -= unico;
        if (saldo <= 0.005) { saldo = 0; break; }
        if (modo === 'parcela') { var resta = Math.max(1, meses - m); amort = saldo / resta; fixa = pmt(saldo, i, resta); }
        nova = sistema === 'price' ? fixa : amort + saldo * i;
      }
      var j = saldo * i;
      juros += j;
      var a = sistema === 'sac' ? Math.min(amort, saldo) : Math.min(fixa - j, saldo);
      a = Math.min(a + extra, saldo);
      saldo -= a;
      m += 1;
    }
    return { juros: juros, meses: m, parcelaNova: nova };
  }

  function amortizacaoAnual(fin, i, meses, sistema) {
    var saldo = fin, amort = meses ? fin / meses : 0, fixa = pmt(fin, i, meses), linhas = [], jA = 0, aA = 0;
    for (var m = 1; m <= meses; m++) {
      var j = saldo * i, a = sistema === 'sac' ? amort : fixa - j;
      jA += j; aA += a; saldo -= a;
      if (m % 12 === 0 || m === meses) { linhas.push({ ano: Math.floor((m + 11) / 12), juros: jA, amortizacao: aA, saldo: Math.max(saldo, 0) }); jA = 0; aA = 0; }
    }
    return linhas;
  }

  var brlInt = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
  function brl(v) { return 'R$ ' + brlInt.format(Math.round(v)); }
  function pct(v, casas) { return v.toLocaleString('pt-BR', { minimumFractionDigits: casas === undefined ? 2 : casas, maximumFractionDigits: casas === undefined ? 2 : casas }) + '%'; }

  var api = { taxaMensal: taxaMensal, pmt: pmt, cet: cet, simular: simular, amortizarAntes: amortizarAntes, amortizacaoAnual: amortizacaoAnual, brl: brl, pct: pct };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  raiz.DatalabImovel = api;
})(typeof window !== 'undefined' ? window : globalThis);
