// Tema claro/noite e botão "Copiar" nos blocos de código.

(function () {
  const raiz = document.documentElement;

  document.querySelectorAll("[data-alternar-tema]").forEach(function (botao) {
    botao.addEventListener("click", function () {
      const escuroAgora =
        raiz.dataset.theme === "dark" ||
        (!raiz.dataset.theme &&
          window.matchMedia("(prefers-color-scheme: dark)").matches);
      const novo = escuroAgora ? "light" : "dark";
      raiz.dataset.theme = novo;
      try {
        localStorage.setItem("tema", novo);
      } catch (e) {}
    });
  });

  document.querySelectorAll(".texto-post pre").forEach(function (bloco) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "botao-copiar";
    botao.textContent = "Copiar";
    botao.addEventListener("click", function () {
      const codigo = bloco.querySelector("code");
      const texto = codigo ? codigo.textContent : "";
      navigator.clipboard.writeText(texto).then(function () {
        botao.textContent = "Copiado";
        setTimeout(function () { botao.textContent = "Copiar"; }, 1500);
      });
    });
    bloco.appendChild(botao);
  });
})();
