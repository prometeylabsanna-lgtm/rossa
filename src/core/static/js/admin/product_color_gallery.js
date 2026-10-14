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

  function colorInput(row) {
    return row.querySelector(
      'input[name*="color_images-"][name$="-color"], select[name*="color_images-"][name$="-color"]'
    );
  }

  function setRowColor(row, colorId) {
    var input = colorInput(row);
    if (input) input.value = String(colorId);
    row.setAttribute("data-rs-color-id", String(colorId));
  }

  function clearRowColor(row) {
    var input = colorInput(row);
    if (input) input.value = "";
    row.removeAttribute("data-rs-color-id");
  }

  function rowHasImage(row) {
    var fileInput = row.querySelector('input[type="file"]');
    if (fileInput && fileInput.files && fileInput.files.length) return true;
    if (row.querySelector(".field-image a[href], .field-image img[src]:not([hidden])")) {
      return true;
    }
    return false;
  }

  function initGallery(root) {
    if (!root || root.getAttribute("data-rs-bound") === "1") return;

    if (!document.getElementById("rs-product-color-swatches")) return;

    var swatches = readSwatches();
    var swatchesEl = root.querySelector("[data-rs-color-swatches]");
    var group =
      document.getElementById("color_images-group") ||
      root.closest("[data-rs-color-gallery-group]") ||
      root.closest("[data-inline-type='tabular']");
    if (!group || !swatchesEl) return;

    root.setAttribute("data-rs-bound", "1");

    var table = group.querySelector("table");
    var addRow = group.querySelector(".add-row");
    var form = group.closest("form");

    function rows() {
      return Array.prototype.slice.call(
        group.querySelectorAll("table tbody.form-group")
      );
    }

    function applyFilter(activeId) {
      group.setAttribute("data-active-color", String(activeId));

      rows().forEach(function (row) {
        var isEmpty = row.classList.contains("empty-form");
        var isOriginal = row.classList.contains("original");
        var cid = String(row.getAttribute("data-rs-color-id") || "");

        if (isEmpty) {
          setRowColor(row, activeId);
          return;
        }

        // Порожній плейсхолдер — під активний колір
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

      group.querySelectorAll("th.column-color, td.field-color").forEach(function (el) {
        el.style.display = "none";
      });
    }

    function syncBeforeSubmit() {
      var activeId = group.getAttribute("data-active-color") || "";
      rows().forEach(function (row) {
        if (row.classList.contains("empty-form")) {
          clearRowColor(row);
          return;
        }
        if (row.classList.contains("original")) {
          return;
        }
        if (!rowHasImage(row)) {
          // Порожній extra-рядок з проставленим color ламає збереження (image required).
          clearRowColor(row);
          return;
        }
        var cid = row.getAttribute("data-rs-color-id") || activeId;
        if (!row.hidden && !row.classList.contains("rs-color-row-hidden") && activeId) {
          cid = activeId;
        }
        if (cid) setRowColor(row, cid);
      });
    }

    if (!swatches.length) {
      if (table) table.style.display = "none";
      if (addRow) addRow.style.display = "none";
      swatchesEl.innerHTML = "";
      return;
    }

    if (table) table.style.display = "";
    if (addRow) addRow.style.display = "";

    var activeId = String(swatches[0].id);
    var hash = (window.location.hash || "").replace(/^#/, "");
    if (hash.indexOf("color_images") === 0) {
      // лишаємо перший колір; користувач клікає кружечок
    }
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

    if (form && form.getAttribute("data-rs-gallery-submit") !== "1") {
      form.setAttribute("data-rs-gallery-submit", "1");
      form.addEventListener("submit", syncBeforeSubmit);
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
  window.setTimeout(boot, 200);
  window.setTimeout(boot, 800);
})();
