(function () {
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

  function setRowColor(row, colorId) {
    var input = row.querySelector(
      'input[name*="color_images-"][name$="-color"], select[name*="color_images-"][name$="-color"]'
    );
    if (input) input.value = String(colorId);
    row.setAttribute("data-rs-color-id", String(colorId));
  }

  function rowHasImage(row) {
    var fileInput = row.querySelector('input[type="file"]');
    if (fileInput && fileInput.files && fileInput.files.length) return true;
    if (row.querySelector(".field-image a[href], .field-image img[src]")) return true;
    return false;
  }

  function initGallery(root) {
    if (!root || root.getAttribute("data-rs-bound") === "1") return;

    // json_script може з’явитись пізніше за Media JS — чекаємо
    if (!document.getElementById("rs-product-color-swatches")) return;

    var swatches = readSwatches();
    var swatchesEl = root.querySelector("[data-rs-color-swatches]");
    var hintEl = root.querySelector("[data-rs-color-hint]");
    var activeLabel = root.querySelector("[data-rs-color-active-label]");
    var group =
      document.getElementById("color_images-group") ||
      root.closest("[data-rs-color-gallery-group]") ||
      root.closest("[data-inline-type='tabular']");
    if (!group || !swatchesEl) return;

    root.setAttribute("data-rs-bound", "1");

    var table = group.querySelector("table");
    var addRow = group.querySelector(".add-row");

    function rows() {
      return Array.prototype.slice.call(
        group.querySelectorAll("table tbody.form-group")
      );
    }

    function applyFilter(activeId) {
      group.setAttribute("data-active-color", String(activeId));

      var current = null;
      for (var i = 0; i < swatches.length; i++) {
        if (String(swatches[i].id) === String(activeId)) {
          current = swatches[i];
          break;
        }
      }
      if (activeLabel) {
        activeLabel.hidden = !current;
        activeLabel.textContent = current
          ? "Фото для кольору: " + current.name + " — можна додати кілька слайдів"
          : "";
      }

      rows().forEach(function (row) {
        var isEmpty = row.classList.contains("empty-form");
        var isOriginal = row.classList.contains("original");
        var cid = String(row.getAttribute("data-rs-color-id") || "");

        // empty-form — шаблон для клону; лишаємо прихованим, лише проставляємо color
        if (isEmpty) {
          setRowColor(row, activeId);
          return;
        }

        // Порожній плейсхолдер (без збереженого фото) — завжди під активний колір
        if (!isOriginal && !rowHasImage(row)) {
          setRowColor(row, activeId);
          row.hidden = false;
          row.classList.remove("rs-color-row-hidden");
          row.style.display = "";
          return;
        }

        if (!cid) {
          setRowColor(row, activeId);
          cid = String(activeId);
        }

        var show = cid === String(activeId);
        row.hidden = !show;
        row.classList.toggle("rs-color-row-hidden", !show);
        row.style.display = show ? "" : "none";
      });

      // Заголовок колонки color
      group.querySelectorAll("th.column-color, td.field-color").forEach(function (el) {
        el.style.display = "none";
      });
    }

    if (!swatches.length) {
      if (hintEl) hintEl.hidden = false;
      if (table) table.style.display = "none";
      if (addRow) addRow.style.display = "none";
      swatchesEl.innerHTML = "";
      if (activeLabel) activeLabel.hidden = true;
      return;
    }

    if (hintEl) hintEl.hidden = true;
    if (table) table.style.display = "";
    if (addRow) addRow.style.display = "";

    var activeId = String(swatches[0].id);
    swatchesEl.innerHTML = "";

    swatches.forEach(function (item, index) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "rs-color-gallery__swatch" + (index === 0 ? " is-active" : "");
      btn.setAttribute("role", "tab");
      btn.setAttribute("data-color-id", String(item.id));
      btn.setAttribute("title", item.name || "");
      btn.setAttribute("aria-label", item.name || String(item.id));
      btn.setAttribute("aria-selected", index === 0 ? "true" : "false");
      btn.style.backgroundColor = item.hex || "#ccc";
      btn.addEventListener("click", function (event) {
        event.preventDefault();
        activeId = String(item.id);
        swatchesEl.querySelectorAll(".rs-color-gallery__swatch").forEach(function (el) {
          var on = el.getAttribute("data-color-id") === activeId;
          el.classList.toggle("is-active", on);
          el.setAttribute("aria-selected", on ? "true" : "false");
        });
        applyFilter(activeId);
      });
      swatchesEl.appendChild(btn);
    });

    // Після «Додати ще» Django клонує empty-form — оновлюємо фільтр
    group.addEventListener("click", function (event) {
      if (!event.target.closest(".add-row a, a.add-row, .inline-add")) return;
      window.setTimeout(function () {
        applyFilter(activeId);
      }, 60);
    });

    if (window.MutationObserver && table) {
      var timer = null;
      var observer = new MutationObserver(function () {
        window.clearTimeout(timer);
        timer = window.setTimeout(function () {
          applyFilter(activeId);
        }, 40);
      });
      observer.observe(table, { childList: true, subtree: false });
    }

    applyFilter(activeId);
  }

  function boot() {
    document.querySelectorAll("[data-rs-color-gallery]").forEach(initGallery);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
  // json_script / Unfold-вкладка можуть з’явитись пізніше
  window.setTimeout(boot, 200);
  window.setTimeout(boot, 800);
})();
