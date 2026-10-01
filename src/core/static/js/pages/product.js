(function () {
  const modal = document.querySelector("[data-order-modal]");
  if (!modal) return;

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

  bindOpeners(document);
  document.body.addEventListener("htmx:afterSwap", (event) => {
    bindOpeners(event.target);
    if (modal.classList.contains("is-open")) {
      syncOrderForm();
    }
  });

  modal.addEventListener("click", (event) => {
    if (event.target === modal || event.target.closest("[data-close-modal]")) {
      modal.classList.remove("is-open");
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") modal.classList.remove("is-open");
  });
})();
