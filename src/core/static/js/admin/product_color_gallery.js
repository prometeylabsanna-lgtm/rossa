(function () {
  /**
   * Кружечки лише змінюють Alpine.store('rsGallery').id.
   * Видимість панелей — x-show у color_gallery_tabular.html
   * (activeTab == color_images && store.id == colorId).
   * color_id на збереженні ставить сервер (окремий formset на колір).
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
    if (
      saved &&
      swatches.some(function (s) {
        return String(s.id) === String(saved);
      })
    ) {
      return String(saved);
    }
    return swatches.length ? String(swatches[0].id) : "";
  }

  function setGalleryColor(colorId) {
    var id = String(colorId || "");
    rememberColor(id);
    if (window.Alpine && Alpine.store("rsGallery")) {
      Alpine.store("rsGallery").id = id;
      return;
    }
    // Alpine ще не готовий — store створить alpine:init у change_form
    document.addEventListener("alpine:init", function () {
      if (Alpine.store("rsGallery")) {
        Alpine.store("rsGallery").id = id;
      }
    });
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
      setGalleryColor("");
      return;
    }

    var activeId = recalledColor(swatches);
    setGalleryColor(activeId);
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
        setGalleryColor(activeId);
        swatchesEl.querySelectorAll(".rs-color-gallery__swatch").forEach(function (el) {
          var on = el.getAttribute("data-color-id") === activeId;
          el.classList.toggle("is-active", on);
          el.setAttribute("aria-selected", on ? "true" : "false");
        });
      });
      swatchesEl.appendChild(btn);
    });
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
