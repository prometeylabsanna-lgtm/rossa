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
      const image = card.querySelector("[data-card-image]");
      const swatches = card.querySelectorAll("[data-swatch]");
      if (!image || !swatches.length) return;
      swatches.forEach((swatch) => {
        swatch.addEventListener("click", (event) => {
          event.preventDefault();
          event.stopPropagation();
          const src = swatch.dataset.image;
          if (!src) return;
          swatches.forEach((s) => s.classList.toggle("is-active", s === swatch));
          image.src = src;
          if (swatch.dataset.srcset) {
            image.srcset = swatch.dataset.srcset;
          }
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
