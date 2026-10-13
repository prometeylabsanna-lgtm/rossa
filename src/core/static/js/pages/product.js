(function () {
  const modal = document.querySelector("[data-order-modal]");

  function formatPrice(value) {
    const n = Number(value);
    if (!Number.isFinite(n)) return String(value || "");
    return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  }

  function readOrderSource() {
    const source = document.querySelector("[data-order-source]");
    if (!source) return null;
    return {
      product_name: source.dataset.productName || "",
      product_slug: source.dataset.productSlug || "",
      fabric_name: source.dataset.fabricName || "",
      shade_name: source.dataset.shadeName || "",
      sku: source.dataset.sku || "",
      price: source.dataset.price || "",
      price_label: source.dataset.priceLabel || formatPrice(source.dataset.price || ""),
    };
  }

  function setField(form, name, value) {
    const input = form.querySelector(`[name="${name}"]`);
    if (input) input.value = value;
  }

  function setText(root, selector, value, fallback) {
    const el = root.querySelector(selector);
    if (!el) return;
    el.textContent = value || fallback || "—";
  }

  function syncOrderForm() {
    if (!modal) return false;
    const form = modal.querySelector("[data-order-form]") || modal.querySelector("#order-form");
    if (!form) return false;
    const data = readOrderSource();
    if (!data) return false;

    setField(form, "product_name", data.product_name);
    setField(form, "product_slug", data.product_slug);
    setField(form, "fabric_name", data.fabric_name);
    setField(form, "shade_name", data.shade_name);
    setField(form, "sku", data.sku);
    setField(form, "price", data.price);

    setText(form, "[data-order-title]", data.product_name);
    setText(form, "[data-order-price-view]", data.price_label || formatPrice(data.price));
    setText(form, "[data-order-fabric-view]", data.fabric_name, "—");
    setText(form, "[data-order-shade-view]", data.shade_name, "—");
    return true;
  }

  function bindOpeners(root) {
    if (!modal) return;
    (root || document).querySelectorAll("[data-open-order]").forEach((btn) => {
      if (btn.dataset.bound === "1") return;
      btn.dataset.bound = "1";
      btn.addEventListener("click", () => {
        if (btn.disabled) return;
        if (!syncOrderForm()) return;
        modal.classList.add("is-open");
        const first = modal.querySelector("input:not([type=hidden])");
        if (first) first.focus();
      });
    });
  }

  function paintHex(root) {
    (root || document).querySelectorAll("[data-hex]").forEach((el) => {
      el.style.backgroundColor = el.dataset.hex;
    });
  }

  function updateFabricColorQuery(pdp, colorId) {
    pdp.querySelectorAll(".chips a.chip").forEach((link) => {
      try {
        const url = new URL(link.getAttribute("href") || "", window.location.href);
        url.searchParams.set("color", colorId);
        const next = `${url.pathname}${url.search}`;
        link.setAttribute("href", next);
        if (link.hasAttribute("hx-get")) link.setAttribute("hx-get", next);
      } catch (_err) {
        /* ignore bad href */
      }
    });
  }

  function showPdpSlide(pdp, colorId, slideIndex) {
    const id = String(colorId);
    const slides = pdp.querySelectorAll(`[data-pdp-image="${id}"]`);
    if (!slides.length) return;
    const next = ((slideIndex % slides.length) + slides.length) % slides.length;
    pdp.querySelectorAll("[data-pdp-image]").forEach((img) => {
      const sameColor = img.dataset.pdpImage === id;
      const sameSlide = Number(img.dataset.pdpSlide || 0) === next;
      img.hidden = !(sameColor && sameSlide);
    });
    pdp.querySelectorAll(`[data-pdp-thumbs-color="${id}"] [data-pdp-thumb-slide]`).forEach((thumb) => {
      thumb.classList.toggle("is-active", Number(thumb.dataset.pdpThumbSlide) === next);
    });
    pdp.dataset.slideIndex = String(next);
  }

  function selectPdpColor(pdp, colorId, shadeName) {
    const id = String(colorId);
    pdp.querySelectorAll("[data-pdp-swatch]").forEach((swatch) => {
      const active = swatch.dataset.pdpSwatch === id;
      swatch.classList.toggle("is-active", active);
      swatch.setAttribute("aria-pressed", active ? "true" : "false");
    });
    pdp.querySelectorAll("[data-pdp-thumbs]").forEach((thumbs) => {
      thumbs.hidden = thumbs.dataset.pdpThumbsColor !== id;
    });

    showPdpSlide(pdp, id, 0);

    const source = pdp.querySelector("[data-order-source]");
    if (source && shadeName) source.dataset.shadeName = shadeName;

    updateFabricColorQuery(pdp, id);

    try {
      const url = new URL(window.location.href);
      url.searchParams.set("color", id);
      window.history.replaceState({}, "", url.pathname + url.search);
    } catch (_err) {
      /* ignore */
    }
  }

  function bindPdpSwipe(pdp) {
    const stage = pdp.querySelector("[data-pdp-stage]");
    if (!stage || stage.dataset.swipeBound === "1") return;
    stage.dataset.swipeBound = "1";

    let startX = 0;
    let startY = 0;
    let tracking = false;

    stage.addEventListener(
      "touchstart",
      (event) => {
        if (event.touches.length !== 1) return;
        const touch = event.touches[0];
        startX = touch.clientX;
        startY = touch.clientY;
        tracking = true;
      },
      { passive: true }
    );

    stage.addEventListener(
      "touchend",
      (event) => {
        if (!tracking) return;
        tracking = false;
        const touch = event.changedTouches[0];
        if (!touch) return;
        const dx = touch.clientX - startX;
        const dy = touch.clientY - startY;
        if (Math.abs(dx) < 40 || Math.abs(dx) < Math.abs(dy)) return;
        const activeSwatch = pdp.querySelector("[data-pdp-swatch].is-active");
        const colorId = activeSwatch ? activeSwatch.dataset.pdpSwatch : null;
        if (!colorId) return;
        const slides = pdp.querySelectorAll(`[data-pdp-image="${colorId}"]`);
        if (slides.length < 2) return;
        const current = Number(pdp.dataset.slideIndex || 0);
        showPdpSlide(pdp, colorId, current + (dx < 0 ? 1 : -1));
      },
      { passive: true }
    );
  }

  function bindPdpColors(root) {
    const scope = root && root.querySelector ? root : document;
    const pdps = [];
    if (scope.matches && scope.matches("#pdp-config")) pdps.push(scope);
    scope.querySelectorAll("#pdp-config").forEach((el) => pdps.push(el));

    pdps.forEach((pdp) => {
      if (pdp.dataset.colorsBound === "1") return;
      pdp.dataset.colorsBound = "1";
      paintHex(pdp);
      pdp.dataset.slideIndex = "0";
      bindPdpSwipe(pdp);

      pdp.addEventListener("click", (event) => {
        const swatch = event.target.closest("[data-pdp-swatch]");
        const thumb = event.target.closest("[data-pdp-thumb-slide]");
        if (swatch && pdp.contains(swatch)) {
          event.preventDefault();
          selectPdpColor(pdp, swatch.dataset.pdpSwatch, swatch.dataset.shadeName || "");
          return;
        }
        if (thumb && pdp.contains(thumb)) {
          event.preventDefault();
          const thumbs = thumb.closest("[data-pdp-thumbs]");
          const colorId = thumbs ? thumbs.dataset.pdpThumbsColor : null;
          if (!colorId) return;
          showPdpSlide(pdp, colorId, Number(thumb.dataset.pdpThumbSlide || 0));
        }
      });
    });
  }

  bindOpeners(document);
  bindPdpColors(document);

  document.body.addEventListener("htmx:afterSwap", (event) => {
    bindOpeners(event.target);
    bindPdpColors(event.target);
    if (modal && modal.classList.contains("is-open")) {
      syncOrderForm();
    }
  });

  if (modal) {
    modal.addEventListener("click", (event) => {
      if (event.target === modal || event.target.closest("[data-close-modal]")) {
        modal.classList.remove("is-open");
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") modal.classList.remove("is-open");
    });
  }
})();
