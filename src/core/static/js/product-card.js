(function () {
  function paintHex() {
    document.querySelectorAll("[data-hex]").forEach((el) => {
      el.style.backgroundColor = el.dataset.hex;
    });
  }

  function bindCards(root) {
    (root || document).querySelectorAll("[data-product-card]").forEach((card) => {
      if (card.dataset.bound === "1") return;
      card.dataset.bound = "1";
      const images = card.querySelectorAll("[data-card-image]");
      const swatches = card.querySelectorAll("[data-swatch]");
      swatches.forEach((swatch) => {
        swatch.addEventListener("click", (event) => {
          event.preventDefault();
          event.stopPropagation();
          const id = swatch.dataset.swatch;
          swatches.forEach((s) => s.classList.toggle("is-active", s === swatch));
          images.forEach((img) => {
            img.hidden = img.dataset.cardImage !== id;
          });
        });
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    paintHex();
    bindCards(document);
  });
  document.body.addEventListener("htmx:afterSwap", function (event) {
    paintHex();
    bindCards(event.target);
  });
})();
