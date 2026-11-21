/* Menu do celular da home (um <details>): toque fora, num link ou Esc fecham. Sem JavaScript o menu continua abrindo e fechando. */
(function () {
  'use strict';
  var d = document.querySelector('header details');
  if (!d) return;
  document.addEventListener('click', function (e) {
    if (!d.open) return;
    // toque num link também fecha (um link para a própria página, como /#simulador, não recarrega e deixaria o menu aberto)
    if (!d.contains(e.target) || (e.target.closest && e.target.closest('nav a'))) d.open = false;
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape' || !d.open) return;
    d.open = false;
    var s = d.querySelector('summary');
    if (s) s.focus();
  });
})();
