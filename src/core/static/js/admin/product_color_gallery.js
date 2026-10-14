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
    if (!colorId) return;
    var input = colorInput(row);
    if (input) input.value = String(colorId);
    row.setAttribute("data-rs-color-id", String(colorId));
  }

  function clearRowColor(row) {
    var input = colorInput(row);
    if (input) input.value = "";
    row.removeAttribute("data-rs-color-id");
  }

  function rowColorId(row) {
    var fromAttr = row.getAttribute("data-rs-color-id");
    if (fromAttr) return String(fromAttr);
    var input = colorInput(row);
    if (input && input.value) return String(input.value);
    return "";
  }

  function rowHasNewFile(row) {
    var fileInput = row.querySelector('input[type="file"]');
    return !!(fileInput && fileInput.files && fileInput.files.length);
  }

  function setRowVisible(row, show) {
    row.hidden = !show;
    row.classList.toggle("rs-color-row-hidden", !show);
    row.style.display = show ? "" : "none";
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
    var activeId = swatches.length ? String(swatches[0].id) : "";

    function rows() {
      return Array.prototype.slice.call(
        group.querySelectorAll("table tbody.form-group")
      );
    }

    function applyFilter(nextId) {
      activeId = String(nextId);
      group.setAttribute("data-active-color", activeId);

      rows().forEach(function (row) {
        var isEmpty = row.classList.contains("empty-form");
        var isOriginal = row.classList.contains("original");

        if (isEmpty) {
          setRowColor(row, activeId);
          return;
        }

        // Збережені рядки: лише показати/сховати, колір НЕ міняти
        if (isOriginal) {
          var ocid = rowColorId(row);
          if (ocid) row.setAttribute("data-rs-color-id", ocid);
          setRowVisible(row, ocid === activeId);
          return;
        }

        // Новий рядок з вибраним файлом: колір уже «запечатаний», лише фільтр
        if (rowHasNewFile(row)) {
          var ncid = rowColorId(row) || activeId;
          setRowColor(row, ncid);
          setRowVisible(row, String(ncid) === activeId);
          return;
        }

        // Порожній плейсхолдер — під активний кружечок
        setRowColor(row, activeId);
        setRowVisible(row, true);
      });

      group.querySelectorAll("th.column-color, td.field-color").forEach(function (el) {
        el.style.display = "none";
      });
    }

    function stampFileRow(fileInput) {
      var row = fileInput.closest("tbody.form-group");
      if (!row || row.classList.contains("original") || row.classList.contains("empty-form")) {
        return;
      }
      var cid = group.getAttribute("data-active-color") || activeId;
      if (cid) setRowColor(row, cid);
    }

    function syncBeforeSubmit() {
      rows().forEach(function (row) {
        if (row.classList.contains("empty-form")) {
          clearRowColor(row);
          return;
        }
        // Збережені фото — не чіпати color у POST
        if (row.classList.contains("original")) {
          return;
        }
        if (rowHasNewFile(row)) {
          var cid = rowColorId(row) || group.getAttribute("data-active-color") || activeId;
          if (cid) setRowColor(row, cid);
          return;
        }
        // Порожній extra без файлу — прибрати color, щоб Django його ігнорував
        clearRowColor(row);
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

    // Одразу при виборі файлу — прив’язати активний колір
    group.addEventListener("change", function (event) {
      var t = event.target;
      if (!t || t.type !== "file") return;
      stampFileRow(t);
      window.setTimeout(function () {
        applyFilter(activeId);
      }, 0);
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
