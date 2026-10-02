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

  function selectPdpColor(pdp, colorId, shadeName) {
    const id = String(colorId);
    pdp.querySelectorAll("[data-pdp-image]").forEach((img) => {
      img.hidden = img.dataset.pdpImage !== id;
    });
    pdp.querySelectorAll("[data-pdp-swatch]").forEach((swatch) => {
      const active = swatch.dataset.pdpSwatch === id;
      swatch.classList.toggle("is-active", active);
      swatch.setAttribute("aria-pressed", active ? "true" : "false");
    });
    pdp.querySelectorAll("[data-pdp-thumb]").forEach((thumb) => {
      thumb.classList.toggle("is-active", thumb.dataset.pdpThumb === id);
    });

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

  function bindPdpColors(root) {
    const scope = root && root.querySelector ? root : document;
    const pdps = [];
    if (scope.matches && scope.matches("#pdp-config")) pdps.push(scope);
    scope.querySelectorAll("#pdp-config").forEach((el) => pdps.push(el));

    pdps.forEach((pdp) => {
      if (pdp.dataset.colorsBound === "1") return;
      pdp.dataset.colorsBound = "1";
      paintHex(pdp);

      pdp.addEventListener("click", (event) => {
        const swatch = event.target.closest("[data-pdp-swatch]");
        const thumb = event.target.closest("[data-pdp-thumb]");
        const trigger = swatch || thumb;
        if (!trigger || !pdp.contains(trigger)) return;
        event.preventDefault();
        const id = swatch
          ? swatch.dataset.pdpSwatch
          : thumb.dataset.pdpThumb;
        const shadeName = swatch
          ? swatch.dataset.shadeName || ""
          : (pdp.querySelector(`[data-pdp-swatch="${id}"]`) || {}).dataset?.shadeName || "";
        selectPdpColor(pdp, id, shadeName);
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
