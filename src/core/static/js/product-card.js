(function () {
  function paintHex() {
    document.querySelectorAll("[data-hex]").forEach((el) => {
      el.style.backgroundColor = el.dataset.hex;
    });
  }

  function showSlide(gallery, index) {
    const slides = gallery.querySelectorAll("[data-card-slide]");
    if (!slides.length) return;
    const next = ((index % slides.length) + slides.length) % slides.length;
    slides.forEach((slide, i) => {
      slide.hidden = i !== next;
    });
    gallery.querySelectorAll(".card__dot").forEach((dot, i) => {
      dot.classList.toggle("is-active", i === next);
    });
    gallery.dataset.slideIndex = String(next);
  }

  function activeGallery(card) {
    return card.querySelector("[data-card-gallery]:not([hidden])");
  }

  function bindSwipe(card, media) {
    let startX = 0;
    let startY = 0;
    let tracking = false;
    let swiped = false;

    media.addEventListener(
      "touchstart",
      (event) => {
        if (event.touches.length !== 1) return;
        const touch = event.touches[0];
        startX = touch.clientX;
        startY = touch.clientY;
        tracking = true;
        swiped = false;
      },
      { passive: true }
    );

    media.addEventListener(
      "touchmove",
      (event) => {
        if (!tracking || event.touches.length !== 1) return;
        const touch = event.touches[0];
        const dx = touch.clientX - startX;
        const dy = touch.clientY - startY;
        if (Math.abs(dx) > 12 && Math.abs(dx) > Math.abs(dy)) {
          swiped = true;
        }
      },
      { passive: true }
    );

    media.addEventListener(
      "touchend",
      (event) => {
        if (!tracking) return;
        tracking = false;
        const touch = event.changedTouches[0];
        if (!touch) return;
        const dx = touch.clientX - startX;
        const dy = touch.clientY - startY;
        if (Math.abs(dx) < 40 || Math.abs(dx) < Math.abs(dy)) return;
        const gallery = activeGallery(card);
        if (!gallery) return;
        const slides = gallery.querySelectorAll("[data-card-slide]");
        if (slides.length < 2) return;
        const current = Number(gallery.dataset.slideIndex || 0);
        showSlide(gallery, current + (dx < 0 ? 1 : -1));
        swiped = true;
      },
      { passive: true }
    );

    media.addEventListener(
      "click",
      (event) => {
        if (!swiped) return;
        event.preventDefault();
        event.stopPropagation();
        swiped = false;
      },
      true
    );
  }

  function bindCards(root) {
    (root || document).querySelectorAll("[data-product-card]").forEach((card) => {
      if (card.dataset.bound === "1") return;
      card.dataset.bound = "1";

      const media = card.querySelector("[data-card-media]");
      const galleries = card.querySelectorAll("[data-card-gallery]");
      const swatches = card.querySelectorAll("[data-swatch]");

      galleries.forEach((gallery) => {
        gallery.dataset.slideIndex = "0";
      });

      if (media && galleries.length) {
        bindSwipe(card, media);
      }

      if (!swatches.length || !galleries.length) return;

      swatches.forEach((swatch) => {
        swatch.addEventListener("click", (event) => {
          event.preventDefault();
          event.stopPropagation();
          const id = swatch.dataset.swatch;
          swatches.forEach((s) => s.classList.toggle("is-active", s === swatch));
          galleries.forEach((gallery) => {
            const active = gallery.dataset.cardGallery === id;
            gallery.hidden = !active;
            if (active) showSlide(gallery, 0);
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
