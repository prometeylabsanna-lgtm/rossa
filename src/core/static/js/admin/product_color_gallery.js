(function () {
  /**
   * Кружечки лише показують/ховають панель formset кольору.
   * color_id на сервері ставить окремий formset (save_new) — як у 569b534.
   * Немає привʼязки файлу до кольору через hidden/JS.
   */
  var STORAGE_KEY = "rossa.galleryActiveColor";

  function readSwatches() {
    var el = document.getElementById("rs-product-color-swatches");
    if (!el) return [];
    try {
      var data = JSON.parse(el.textContent || "[]");
      return Array.isArray(data) ? data : [];
    } catch (err) {
      return [];
    }
  }

  function rememberColor(colorId) {
    try {
      window.sessionStorage.setItem(STORAGE_KEY, String(colorId));
    } catch (err) {}
  }

  function recalledColor(swatches) {
    var saved = "";
    try {
      saved = window.sessionStorage.getItem(STORAGE_KEY) || "";
    } catch (err) {
      saved = "";
    }
    if (saved && swatches.some(function (s) { return String(s.id) === String(saved); })) {
      return String(saved);
    }
    return swatches.length ? String(swatches[0].id) : "";
  }

  function panels() {
    return Array.prototype.slice.call(
      document.querySelectorAll("[data-rs-gallery-panel]")
    );
  }

  function setTableVisible(table, show) {
    if (!table) return;
    table.hidden = !show;
    table.setAttribute("aria-hidden", show ? "false" : "true");
    table.style.display = show ? "" : "none";
  }

  function applyFilter(activeId) {
    panels().forEach(function (panel) {
      var show =
        String(panel.getAttribute("data-rs-gallery-panel")) === String(activeId);
      setTableVisible(panel.querySelector("[data-rs-gallery-table]"), show);
    });
    rememberColor(activeId);
  }

  function init() {
    var root = document.querySelector(".rs-color-gallery[data-rs-color-gallery]");
    if (!root || root.getAttribute("data-rs-bound") === "1") return;
    if (!document.getElementById("rs-product-color-swatches")) return;

    var swatches = readSwatches();
    var swatchesEl = root.querySelector("[data-rs-color-swatches]");
    if (!swatchesEl) return;

    root.setAttribute("data-rs-bound", "1");

    if (!swatches.length) {
      swatchesEl.innerHTML = "";
      panels().forEach(function (panel) {
        setTableVisible(panel.querySelector("[data-rs-gallery-table]"), false);
      });
      return;
    }

    var activeId = recalledColor(swatches);
    swatchesEl.innerHTML = "";

    swatches.forEach(function (item) {
      var id = String(item.id);
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className =
        "rs-color-gallery__swatch" + (id === activeId ? " is-active" : "");
      btn.setAttribute("role", "tab");
      btn.setAttribute("data-color-id", id);
      btn.setAttribute("title", item.name || "");
      btn.setAttribute("aria-label", item.name || id);
      btn.setAttribute("aria-selected", id === activeId ? "true" : "false");
      btn.style.backgroundColor = item.hex || "#ccc";
      btn.addEventListener("click", function (event) {
        event.preventDefault();
        activeId = id;
        swatchesEl.querySelectorAll(".rs-color-gallery__swatch").forEach(function (el) {
          var on = el.getAttribute("data-color-id") === activeId;
          el.classList.toggle("is-active", on);
          el.setAttribute("aria-selected", on ? "true" : "false");
        });
        applyFilter(activeId);
      });
      swatchesEl.appendChild(btn);
    });

    applyFilter(activeId);
  }

  function boot() {
    init();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
  window.setTimeout(boot, 200);
  window.setTimeout(boot, 800);
})();
