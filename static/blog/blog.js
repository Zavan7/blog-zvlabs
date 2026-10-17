/* Tema (dia/noite), botão "Copiar" dos blocos de código e fechamento do
   painel de inscrição. Veio do protótipo sem a troca de vista e o filtro,
   que no Django são rotas e ?assunto= no servidor. O tema salvo é aplicado
   antes, por um script curto no <head> do base.html, para não piscar. */
(function () {
  var raiz = document.documentElement;

  function atual() {
    return raiz.dataset.tema ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'noite' : 'dia');
  }

  function rotular() {
    document.querySelectorAll('[data-tema-botao]').forEach(function (b) {
      b.textContent = atual() === 'noite' ? 'Tema claro' : 'Tema escuro';
    });
  }

  // Sem JS o botão não faria nada, então ele só aparece aqui.
  if (navigator.clipboard) {
    document.querySelectorAll('[data-copiar]').forEach(function (b) {
      b.hidden = false;
    });
  }

  document.addEventListener('click', function (ev) {
    var botaoTema = ev.target.closest('[data-tema-botao]');
    if (botaoTema) {
      var novo = atual() === 'noite' ? 'dia' : 'noite';
      raiz.dataset.tema = novo;
      try { localStorage.setItem('zv-tema', novo); } catch (e) {}
      rotular();
      return;
    }

    var copiar = ev.target.closest('[data-copiar]');
    if (copiar) {
      var figura = copiar.closest('.codigo');
      var texto = Array.prototype.map.call(
        figura.querySelectorAll('.l'),
        function (l) { return l.textContent; }
      ).join('\n');
      navigator.clipboard.writeText(texto).then(function () {
        copiar.textContent = 'Copiado';
        setTimeout(function () { copiar.textContent = 'Copiar'; }, 1500);
      });
    }
  });

  var inscrever = document.querySelector('[data-inscrever]');
  if (inscrever) {
    document.addEventListener('click', function (ev) {
      if (inscrever.open && !inscrever.contains(ev.target)) { inscrever.open = false; }
    });
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && inscrever.open) {
        inscrever.open = false;
        inscrever.querySelector('summary').focus();
      }
    });
  }

  rotular();
})();
