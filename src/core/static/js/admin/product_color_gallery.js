(function () {
  /**
   * Кружечок → клас rs-gallery-on на панелі цього color_id.
   * Alpine лише показує вкладку «Фото» (x-show activeTab); колір фільтрує цей скрипт.
   * color_id при збереженні ставить сервер (окремий formset на колір).
   */
  var STORAGE_KEY = "rossa.galleryActiveColor";
  var activeId = "";

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

  function panels() {
    return Array.prototype.slice.call(
      document.querySelectorAll("[data-rs-gallery-panel]")
    );
  }

  function photosTabOpen() {
    try {
      var stack = document.body._x_dataStack;
      if (stack && stack[0] && typeof stack[0].activeTab === "string") {
        return stack[0].activeTab === "color_images";
      }
    } catch (err) {}
    return (window.location.hash || "") === "#color_images";
  }

  function applyFilter(colorId) {
    activeId = String(colorId || "");
    rememberColor(activeId);
    var onPhotos = photosTabOpen();

    panels().forEach(function (panel) {
      var match =
        activeId !== "" &&
        String(panel.getAttribute("data-rs-gallery-panel")) === activeId;
      panel.classList.toggle("rs-gallery-on", match);
      panel.setAttribute("data-rs-on", match ? "1" : "0");

      // Alpine x-show ставить inline display на ВСІ панелі вкладки.
      // Неактивний колір знову ховаємо інлайном ПІСЛЯ Alpine.
      if (!match) {
        panel.style.setProperty("display", "none");
      } else if (onPhotos) {
        panel.style.removeProperty("display");
      }
    });
  }

  function syncAfterAlpine() {
    applyFilter(activeId);
  }

  function init() {
    var root = document.querySelector(".rs-color-gallery[data-rs-color-gallery]");
    if (!root || root.getAttribute("data-rs-bound") === "1") return;
    if (!document.getElementById("rs-product-color-swatches")) return;

    var swatches = readSwatches();
    var swatchesEl = root.querySelector("[data-rs-color-swatches]");
    var labelEl = root.querySelector("[data-rs-color-active-label]");
    if (!swatchesEl) return;

    root.setAttribute("data-rs-bound", "1");

    if (!swatches.length) {
      swatchesEl.innerHTML = "";
      if (labelEl) {
        labelEl.hidden = true;
        labelEl.textContent = "";
      }
      applyFilter("");
      return;
    }

    activeId = recalledColor(swatches);
    swatchesEl.innerHTML = "";

    function updateLabel() {
      if (!labelEl) return;
      var current = null;
      for (var i = 0; i < swatches.length; i++) {
        if (String(swatches[i].id) === activeId) {
          current = swatches[i];
          break;
        }
      }
      if (!current) {
        labelEl.hidden = true;
        labelEl.textContent = "";
        return;
      }
      labelEl.hidden = false;
      labelEl.textContent =
        "Зараз відкрито: " +
        current.name +
        " — фото лише цього кольору (як на сайті в галереї).";
    }

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
        applyFilter(activeId);
        updateLabel();
        swatchesEl.querySelectorAll(".rs-color-gallery__swatch").forEach(function (el) {
          var on = el.getAttribute("data-color-id") === activeId;
          el.classList.toggle("is-active", on);
          el.setAttribute("aria-selected", on ? "true" : "false");
        });
      });
      swatchesEl.appendChild(btn);
    });

    applyFilter(activeId);
    updateLabel();

    // Після перемикання вкладок Unfold/Alpine знову показує всі панелі —
    // повторно залишаємо лише активний колір.
    document.body.addEventListener(
      "click",
      function (event) {
        var tab = event.target.closest("[x-on\\:click*='activeTab'], a[href^='#']");
        if (!tab) return;
        window.setTimeout(syncAfterAlpine, 0);
        window.setTimeout(syncAfterAlpine, 50);
        window.setTimeout(syncAfterAlpine, 200);
      },
      true
    );

    window.setTimeout(syncAfterAlpine, 100);
    window.setTimeout(syncAfterAlpine, 500);
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
