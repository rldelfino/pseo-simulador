// Gerado por gerador.py (gerar_calculo_js) — não editar à mão
// sem também atualizar as páginas que dependem dele.

        function unformatCurrency(val) { return typeof val === 'number' ? val : Number(val.replace(/\D/g, '')) / 100; }
        function formatCurrency(val) { return (val).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
        function initMask(inputId) { const input = document.getElementById(inputId); let rawVal = unformatCurrency(input.value); if(rawVal > 0) input.value = formatCurrency(rawVal); input.addEventListener('input', function(e) { let raw = unformatCurrency(e.target.value); e.target.value = formatCurrency(raw); }); }

        // Atualiza um número de resultado com um pulso de cor quando o valor
        // muda de verdade (evita reiniciar a animação em toda chamada de
        // calcularTudo(), inclusive quando o número não mudou nada).
        function atualizarValor(id, texto) {
            const el = document.getElementById(id);
            if (!el || el.innerText === texto) return;
            el.innerText = texto;
            el.classList.remove('valor-pulse');
            void el.offsetWidth; // força reflow, senão o navegador não reinicia a animação
            el.classList.add('valor-pulse');
        }

        function syncSliderInput(sliderId, inputId) {
            const slider = document.getElementById(sliderId);
            const input = document.getElementById(inputId);
            slider.addEventListener('input', function() { input.value = formatCurrency(Number(this.value)); calcularTudo(); });
            input.addEventListener('blur', function() { let val = unformatCurrency(this.value); slider.value = val; calcularTudo(); });
        }

        // CET (Custo Efetivo Total) real via TIR (bisseção), espelhando o mesmo
        // cálculo do Python (gerador.py / calcular_cet_real): soma juros +
        // seguro MIP (sobre saldo devedor) + seguro DFI (sobre valor do imóvel)
        // + taxa de administração mensal, e resolve a taxa mensal que zera o
        // valor presente do fluxo de caixa.
        function calcularCET(vFinanciado, prazoMeses, taxaMensal, vImovel, sistema) {
            if (vFinanciado <= 0 || prazoMeses <= 0) return 0;
            const TAXA_MIP_MENSAL = 0.00030, TAXA_DFI_MENSAL = 0.000129, TAXA_ADMIN_MENSAL = 25.00;
            let saldo = vFinanciado, pmtPrice = 0;
            if (sistema === 'PRICE') {
                pmtPrice = (taxaMensal > 0)
                    ? vFinanciado * (taxaMensal * Math.pow(1 + taxaMensal, prazoMeses)) / (Math.pow(1 + taxaMensal, prazoMeses) - 1)
                    : vFinanciado / prazoMeses;
            }
            const fluxo = [];
            for (let m = 0; m < prazoMeses; m++) {
                const juros = saldo * taxaMensal;
                const amortizacao = (sistema === 'SAC') ? (vFinanciado / prazoMeses) : (pmtPrice - juros);
                const seguroMip = saldo * TAXA_MIP_MENSAL;
                const seguroDfi = vImovel * TAXA_DFI_MENSAL;
                fluxo.push(amortizacao + juros + seguroMip + seguroDfi + TAXA_ADMIN_MENSAL);
                saldo -= amortizacao;
            }
            const vpl = (r) => {
                let total = -vFinanciado;
                for (let i = 0; i < fluxo.length; i++) total += fluxo[i] / Math.pow(1 + r, i + 1);
                return total;
            };
            let lo = 0, hi = 0.05;
            for (let i = 0; i < 60; i++) {
                const mid = (lo + hi) / 2;
                if (vpl(mid) > 0) lo = mid; else hi = mid;
            }
            const tirMensal = (lo + hi) / 2;
            return (Math.pow(1 + tirMensal, 12) - 1) * 100;
        }

        // Simula amortização extra RECORRENTE (não um pagamento único): a
        // cada `periodicidade` meses, abate `aporte` do saldo devedor,
        // parando quando o saldo zera ou o prazo original acaba. É assim
        // que a maioria das pessoas amortiza na prática (várias vezes, ex:
        // com 13º/bônus), em vez de um único aporte grande no meio do
        // contrato.
        function simularComAmortizacaoRecorrente(vFinanciado, prazoMeses, taxaMensal, sistema, aporte, periodicidade, pmtPriceFixo) {
            let saldo = vFinanciado, jurosTotal = 0, meses = 0;
            while (saldo > 0.005 && meses < prazoMeses) {
                meses++;
                let juros = saldo * taxaMensal; jurosTotal += juros;
                let amortizacaoBase = (sistema === 'SAC') ? (vFinanciado / prazoMeses) : (pmtPriceFixo - juros);
                if (amortizacaoBase > saldo) amortizacaoBase = saldo;
                saldo -= amortizacaoBase;
                if (aporte > 0 && periodicidade > 0 && saldo > 0 && meses % periodicidade === 0) {
                    const abate = Math.min(aporte, saldo);
                    saldo -= abate;
                }
            }
            return { jurosTotal, meses };
        }

        // Recalcula o ranking dos 15 bancos AO VIVO pro valor/prazo que o
        // visitante está simulando agora (não mais o cenário padrão fixo
        // da página). Espelha comparar_todos_bancos() do gerador.py: cada
        // banco usa sua PRÓPRIA entrada mínima (LTV) e sua PRÓPRIA taxa
        // padrão — só o banco desta página usa a taxa/CET que o visitante
        // está vendo na tela agora (cetAtualLive), pra nunca mostrar dois
        // números diferentes do mesmo banco na mesma página.
        function calcularRankingBancosLive(vImovelLive, prazoLive, cetAtualLive) {
            const resultados = [];
            for (const b of BANCOS_JS) {
                const prazoB = Math.min(prazoLive, b.prazoMax);
                const entradaB = vImovelLive * (1 - b.ltv);
                const vFinanciadoB = vImovelLive - entradaB;
                if (vFinanciadoB <= 0) continue;

                const ehAtual = (b.chave === BANCO_ATUAL_CHAVE);
                const taxaMensalB = (b.taxa / 100) / 12;
                const cetB = ehAtual ? cetAtualLive : calcularCET(vFinanciadoB, prazoB, taxaMensalB, vImovelLive, 'SAC');

                // Reconstrói a URL da página equivalente pelo MESMO padrão de
                // slug usado na geração (simulador-{banco}-{valor}-mil-{prazo}-meses),
                // "encaixando" o valor/prazo ao vivo na grade real de páginas
                // geradas (múltiplos de R$50mil entre 150mil-1,5mi; prazo 360
                // ou 420, o que existir pra esse banco) — assim o link NUNCA
                // aponta pra uma URL que não existe, mesmo fora da grade.
                const valorGrade = Math.min(1500000, Math.max(150000, Math.round(vImovelLive / 50000) * 50000));
                const candidatosPrazo = [360, 420].filter(p => p <= b.prazoMax);
                const prazoGrade = candidatosPrazo.reduce((melhor, p) =>
                    Math.abs(p - prazoLive) < Math.abs(melhor - prazoLive) ? p : melhor, candidatosPrazo[0] || b.prazoMax);
                const slugBanco = b.chave.toLowerCase().replace(/\s+/g, '-');
                const slug = candidatosPrazo.length
                    ? `simulador-${slugBanco}-${Math.round(valorGrade / 1000)}-mil-${prazoGrade}-meses`
                    : null;

                resultados.push({
                    chave: b.chave, nome: b.nome, cet: cetB, ehAtual,
                    entradaPerc: Math.round((1 - b.ltv) * 100), slug,
                });
            }
            resultados.sort((a, b) => a.cet - b.cet);
            return resultados;
        }

        // Espelha o bloco Python "Faixa de CET no Mercado" (e
        // calcular_marcador_posicao_mercado): a posição do marcador é
        // interpolação linear do CET real do banco atual contra o
        // mínimo/máximo real da faixa (valor, não ranking) — testado e
        // revertido de "fração do ranking" no mesmo dia (07/set/2026), a
        // pedido do usuário: com todo marcador igualmente espaçado a
        // barra perdia a noção de o quanto os bancos realmente se
        // aproximam ou distanciam uns dos outros em taxa — ver docstring
        // da função Python irmã pro raciocínio completo. Só precisa do
        // menor/maior CET do ranking pros rótulos das pontas (não mais
        // do nome de cada banco), e o CTA sempre aponta pra Financia
        // Tudo — nunca pra um concorrente.
        function renderizarComparacaoMercado(vImovelLive, prazoLive, cetAtualLive, nomeBancoAtual) {
            const elGrafico = document.getElementById('grafico_comparacao_mercado');
            const elTexto = document.getElementById('texto_resumo_mercado');
            if (!elGrafico || !elTexto) return; // página sem ranking (nenhum banco elegível na geração)

            const ranking = calcularRankingBancosLive(vImovelLive, prazoLive, cetAtualLive);
            if (ranking.length === 0) return;

            const cetMin = ranking[0].cet;
            const cetMax = ranking[ranking.length - 1].cet;
            const spread = cetMax - cetMin;
            let marcadorPct = spread > 0 ? Math.round(((cetAtualLive - cetMin) / spread) * 100) : 50;
            marcadorPct = Math.max(2, Math.min(98, marcadorPct));

            const cetAtualFmt = cetAtualLive.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            const cetMinFmt = cetMin.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            const cetMaxFmt = cetMax.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});

            elGrafico.innerHTML = `
                <div class="relative h-2 rounded-full bg-gradient-to-r from-emerald-500 via-amber-400 to-rose-500">
                    <div class="absolute top-1/2 h-4 w-4 rounded-full bg-white border-2 border-emerald-950 shadow-[0_0_0_3px_rgba(16,185,129,0.35)]" style="left:${marcadorPct}%; transform:translate(-50%,-50%)" title="${nomeBancoAtual}: ${cetAtualFmt}%"></div>
                </div>
                <div class="flex justify-between text-[10px] text-slate-500 uppercase tracking-wide">
                    <span>${cetMinFmt}% menor CET</span>
                    <span>${cetMaxFmt}% maior CET</span>
                </div>`;

            const hrefFinanciaTudo = 'https://app.financiatudo.com.br/financiamento-de-imoveis/chave/8940d282b765cbf97b6df55fd1eb0b52b18b2f6e';

            if (marcadorPct <= 15) {
                elTexto.innerHTML = `O ${nomeBancoAtual} está entre as condições <strong class="text-emerald-400">mais competitivas</strong> que acompanhamos (${cetAtualFmt}% de CET, na faixa de ${cetMinFmt}% a ${cetMaxFmt}% do mercado). Vale confirmar essa condição e agilizar a aprovação sem custo.
                    <a href="${hrefFinanciaTudo}" target="_blank" rel="noopener sponsored" class="text-emerald-400 underline hover:text-emerald-300 block mt-2 font-semibold">Falar com a Financia Tudo →</a>`;
            } else {
                elTexto.innerHTML = `Nas condições simuladas, o CET no mercado costuma variar entre <strong class="text-emerald-400">${cetMinFmt}%</strong> e <strong class="text-emerald-400">${cetMaxFmt}%</strong> — aqui no ${nomeBancoAtual} está em ${cetAtualFmt}%. Encontrar e negociar manualmente a melhor condição pode levar semanas de idas e vindas ao banco.
                    <a href="${hrefFinanciaTudo}" target="_blank" rel="noopener sponsored" class="text-emerald-400 underline hover:text-emerald-300 block mt-2 font-semibold">É esse trabalho que a Financia Tudo faz por você, sem custo →</a>`;
            }
        }

        function calcularTudo() {
            const vImovel = unformatCurrency(document.getElementById('input_imovel').value);
            let entrada = unformatCurrency(document.getElementById('input_entrada').value);

            // TRAVA 1: ENTRADA NÃO PODE SER MENOR QUE O MÍNIMO E NÃO PODE PASSAR DE 80% DO IMÓVEL
            const entradaMinimaReal = vImovel * REGRA_PERC_ENTRADA_MIN;
            const entradaMaximaReal = vImovel * 0.80; // Regra de Sanidade de Mercado (80% máx de entrada)

            if (entrada < entradaMinimaReal) {
                entrada = entradaMinimaReal;
                document.getElementById('input_entrada').value = formatCurrency(entrada);
            } else if (entrada > entradaMaximaReal) {
                entrada = entradaMaximaReal;
                document.getElementById('input_entrada').value = formatCurrency(entrada);
            }

            document.getElementById('slider_entrada').min = entradaMinimaReal;
            document.getElementById('slider_entrada').max = entradaMaximaReal;
            document.getElementById('slider_entrada').value = entrada;

            const taxaAnualRaw = document.getElementById('input_taxa').value.toString().replace(',', '.');
            const taxaAnual = parseFloat(taxaAnualRaw) || 0;
            const taxa = (taxaAnual / 100) / 12;

            let prazoOrig = parseInt(document.getElementById('input_prazo').value) || 0;
            if (prazoOrig > REGRA_PRAZO_MAX) {
                prazoOrig = REGRA_PRAZO_MAX;
                document.getElementById('input_prazo').value = prazoOrig;
            }

            let anosEquivalentes = Math.floor(prazoOrig / 12);
            document.getElementById('hint_anos').innerText = anosEquivalentes;
            document.getElementById('label_anos').innerText = anosEquivalentes + " anos";

            const sistema = document.querySelector('input[name="sistema"]:checked').value;
            const vFinanciado = vImovel - entrada;

            // TRAVA 2 (CORRIGIDA): a amortização extra nunca pode passar do
            // SALDO DEVEDOR real (valor do imóvel - entrada). Antes o teto
            // era "entradaMaximaReal - entrada", que é sempre MENOR que o
            // saldo devedor e impedia simulações válidas de quitação quase
            // total, contrariando a regra de negócio original.
            let aporteRecorrente = unformatCurrency(document.getElementById('input_amortizar').value);
            let amortizacaoMaxima = vFinanciado;
            if (amortizacaoMaxima < 0) amortizacaoMaxima = 0;

            if (aporteRecorrente > amortizacaoMaxima) {
                aporteRecorrente = amortizacaoMaxima;
                document.getElementById('input_amortizar').value = formatCurrency(aporteRecorrente);
            }
            document.getElementById('slider_amortizar').max = amortizacaoMaxima;
            document.getElementById('slider_amortizar').value = aporteRecorrente;

            const periodicidade = parseInt(document.getElementById('slider_periodicidade').value) || 1;
            document.getElementById('label_periodicidade').innerText = 'a cada ' + periodicidade + (periodicidade === 1 ? ' mês' : ' meses');

            if (vFinanciado <= 0 || prazoOrig <= 0) return;

            let saldoTrad = vFinanciado; let jurosTotalTrad = 0; let p1Trad = 0; let pUTrad = 0; let pmtPriceTrad = 0;

            // Parcela fixa do PRICE independe do sistema selecionado na tela —
            // calculada sempre, porque a recomendação SAC vs. PRICE (mais
            // abaixo) precisa simular os dois sistemas com o mesmo plano de
            // amortização, não só o que está marcado no momento.
            if (taxa > 0) { pmtPriceTrad = vFinanciado * (taxa * Math.pow(1 + taxa, prazoOrig)) / (Math.pow(1 + taxa, prazoOrig) - 1);
            } else { pmtPriceTrad = vFinanciado / prazoOrig; }

            for (let m = 1; m <= prazoOrig; m++) {
                let juros = saldoTrad * taxa; jurosTotalTrad += juros;
                let amortizacaoBase = (sistema === 'SAC') ? (vFinanciado / prazoOrig) : (pmtPriceTrad - juros);
                let parcelaMensal = amortizacaoBase + juros;
                if (m === 1) p1Trad = parcelaMensal;
                if (m === prazoOrig) pUTrad = parcelaMensal;
                saldoTrad -= amortizacaoBase;
            }

            const resultadoNovo = simularComAmortizacaoRecorrente(vFinanciado, prazoOrig, taxa, sistema, aporteRecorrente, periodicidade, pmtPriceTrad);
            const jurosTotalNovo = resultadoNovo.jurosTotal;
            const mesesNovo = resultadoNovo.meses;

            const economiaJuros = jurosTotalTrad - jurosTotalNovo;
            const mesesEliminados = Math.max(0, prazoOrig - mesesNovo);
            const totalDesembolsado = vFinanciado + jurosTotalTrad;
            const cfg = {style:'currency',currency:'BRL'};
            atualizarValor('res_p1', p1Trad.toLocaleString('pt-BR', cfg));
            atualizarValor('res_pU', pUTrad.toLocaleString('pt-BR', cfg));
            atualizarValor('res_capital', vFinanciado.toLocaleString('pt-BR', cfg));
            atualizarValor('res_total_pago', totalDesembolsado.toLocaleString('pt-BR', cfg));
            atualizarValor('res_economia', economiaJuros.toLocaleString('pt-BR', cfg));

            const cetReal = calcularCET(vFinanciado, prazoOrig, taxa, vImovel, sistema);
            atualizarValor('res_cet', cetReal.toLocaleString('pt-BR', {minimumFractionDigits:2, maximumFractionDigits:2}) + '%');
            const rendaSugerida = Math.ceil((p1Trad / 0.30) / 50) * 50;
            atualizarValor('res_renda', rendaSugerida.toLocaleString('pt-BR', cfg));

            let anos = Math.floor(mesesEliminados / 12); let meses = mesesEliminados % 12; let textoTempo = "";
            if (anos > 0) textoTempo += anos + (anos === 1 ? " Ano" : " Anos");
            if (anos > 0 && meses > 0) textoTempo += " e ";
            if (meses > 0 || (anos === 0 && meses === 0)) textoTempo += meses + (meses === 1 ? " Mês" : " Meses");
            if (textoTempo === "") textoTempo = "0 Meses";
            atualizarValor('res_impacto', textoTempo);
            let pctNovoPrazo = (mesesNovo / prazoOrig) * 100;
            document.getElementById('bar_novo_prazo').style.width = pctNovoPrazo + '%';

            // Recomendação SAC vs. PRICE PARA ESSE PLANO DE AMORTIZAÇÃO:
            // simula os dois sistemas do zero (independente do que está
            // marcado na tela) com o mesmo aporte recorrente, e recomenda o
            // que gera menos juros totais nesse cenário específico. Com
            // amortização frequente, o resultado pode inverter a regra
            // padrão de "SAC é sempre mais barato" — no PRICE o saldo
            // devedor cai mais devagar no início, então o mesmo aporte
            // extra abate uma fatia maior de juros futuros.
            const simSac = simularComAmortizacaoRecorrente(vFinanciado, prazoOrig, taxa, 'SAC', aporteRecorrente, periodicidade, pmtPriceTrad);
            const simPrice = simularComAmortizacaoRecorrente(vFinanciado, prazoOrig, taxa, 'PRICE', aporteRecorrente, periodicidade, pmtPriceTrad);
            const elTextoRecomendacao = document.getElementById('texto_recomendacao_sistema');
            if (aporteRecorrente <= 0) {
                elTextoRecomendacao.innerHTML = 'Informe um valor de amortização acima para ver qual sistema — SAC ou PRICE — te economiza mais juros com esse plano de aportes.';
            } else {
                const diferenca = Math.abs(simSac.jurosTotal - simPrice.jurosTotal);
                const melhorSistema = (simSac.jurosTotal <= simPrice.jurosTotal) ? 'SAC' : 'PRICE';
                const diferencaFmt = diferenca.toLocaleString('pt-BR', cfg);
                elTextoRecomendacao.innerHTML = 'Amortizando ' + formatCurrency(aporteRecorrente) + ' a cada ' + periodicidade + (periodicidade === 1 ? ' mês' : ' meses') + ', o <strong class="text-emerald-400">' + melhorSistema + '</strong> te economiza aproximadamente <strong class="text-emerald-400">' + diferencaFmt + '</strong> em juros nesse cenário, contra o outro sistema.';
            }

            // A caixinha "Comparação com o Mercado" precisa ser recalculada
            // aqui também — sempre ANCORADA em SAC (não no toggle SAC/PRICE
            // da tela), pra ficar na mesma régua que os outros 14 bancos,
            // que também são sempre comparados em SAC. Sem isso, o gráfico
            // e o texto da caixinha ficavam "presos" no cenário padrão da
            // página, divergindo do que os campos acima já mostravam assim
            // que o visitante mexia em qualquer slider.
            const cetSacAtual = calcularCET(vFinanciado, prazoOrig, taxa, vImovel, 'SAC');
            const nomeBancoAtual = (BANCOS_JS.find(b => b.chave === BANCO_ATUAL_CHAVE) || {}).nome || BANCO_ATUAL_CHAVE;
            renderizarComparacaoMercado(vImovel, prazoOrig, cetSacAtual, nomeBancoAtual);
        }

        function ajustarTooltips() {
            const margem = 8;
            // Achado real (06/set/2026, auditoria do projeto irmão de
            // veículos): usar window.innerWidth aqui deixava o balão
            // estourando a tela mesmo com ajustarTooltips() já rodando no
            // window.onload — confirmado ao vivo (Playwright/navegador
            // real, viewport 375px: scrollWidth 414 > clientWidth 375,
            // tooltip do CET estourando). Causa: esta página tem
            // overflow-x:hidden no <body>, e nesse caso window.innerWidth
            // pode devolver um valor MAIOR que a área realmente visível.
            // document.documentElement.clientWidth é a largura real
            // renderizada e não sofre desse problema.
            const larguraTela = document.documentElement.clientWidth;
            document.querySelectorAll('.tooltip-box').forEach(box => {
                const metade = box.offsetWidth / 2;
                box.style.setProperty('--tt-shift', (-metade) + 'px');
                const r = box.getBoundingClientRect();
                let shift = 0;
                if (r.right > larguraTela - margem) shift = (larguraTela - margem) - r.right;
                else if (r.left < margem) shift = margem - r.left;
                if (shift !== 0) box.style.setProperty('--tt-shift', (-metade + shift).toFixed(0) + 'px');
            });
        }
        window.addEventListener('resize', ajustarTooltips);
        // A posição do ícone pode mudar depois do primeiro cálculo (ex: a
        // fonte do Google Fonts carrega depois e reflui o texto ao redor).
        // Recalcula de novo assim que as fontes terminam de carregar, pra
        // não travar um deslocamento calculado com o layout ainda "errado".
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(ajustarTooltips).catch(() => {});
        }