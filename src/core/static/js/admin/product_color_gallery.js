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

  function rowColorInput(row) {
    return row.querySelector('input[name$="-color"], select[name$="-color"]');
  }

  function rowColorId(row) {
    var input = rowColorInput(row);
    return input ? String(input.value || "") : "";
  }

  function setRowColorId(row, colorId) {
    var input = rowColorInput(row);
    if (input) input.value = String(colorId);
  }

  function isEmptyForm(row) {
    return row.classList.contains("empty-form");
  }

  function initGallery(root) {
    if (!root || root.getAttribute("data-rs-bound") === "1") return;
    root.setAttribute("data-rs-bound", "1");

    var swatches = readSwatches();
    var swatchesEl = root.querySelector("[data-rs-color-swatches]");
    var hintEl = root.querySelector("[data-rs-color-hint]");
    var activeLabel = root.querySelector("[data-rs-color-active-label]");
    var group = root.closest("[data-inline-type='tabular']") || root.parentElement;
    if (!group || !swatchesEl) return;

    var table = group.querySelector("table");
    var addRow = group.querySelector(".add-row");

    function dataRows() {
      return Array.prototype.slice
        .call(group.querySelectorAll("tbody"))
        .filter(function (row) {
          return !isEmptyForm(row) && row.querySelector('input[name$="-color"], select[name$="-color"]');
        });
    }

    function emptyTemplate() {
      return group.querySelector("tbody.empty-form");
    }

    function hideColorColumn() {
      group.querySelectorAll("th, td").forEach(function (cell) {
        if (
          cell.classList.contains("column-color") ||
          cell.classList.contains("field-color")
        ) {
          cell.style.display = "none";
        }
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
      btn.addEventListener("click", function () {
        activeId = String(item.id);
        swatchesEl.querySelectorAll(".rs-color-gallery__swatch").forEach(function (el) {
          var on = el.getAttribute("data-color-id") === activeId;
          el.classList.toggle("is-active", on);
          el.setAttribute("aria-selected", on ? "true" : "false");
        });
        applyFilter();
      });
      swatchesEl.appendChild(btn);
    });

    function applyFilter() {
      var current = null;
      for (var i = 0; i < swatches.length; i++) {
        if (String(swatches[i].id) === activeId) {
          current = swatches[i];
          break;
        }
      }
      if (activeLabel) {
        activeLabel.hidden = !current;
        activeLabel.textContent = current ? "Фото для кольору: " + current.name : "";
      }

      dataRows().forEach(function (row) {
        var cid = rowColorId(row);
        if (!cid) {
          setRowColorId(row, activeId);
          cid = activeId;
        }
        row.style.display = cid === activeId ? "" : "none";
      });

      var tmpl = emptyTemplate();
      if (tmpl) setRowColorId(tmpl, activeId);
      hideColorColumn();
    }

    if (window.MutationObserver) {
      var observer = new MutationObserver(function () {
        applyFilter();
      });
      var tableBodyParent = table || group;
      observer.observe(tableBodyParent, { childList: true, subtree: true });
    }

    applyFilter();
  }

  function ensureMount() {
    // Fallback, якщо Unfold не підхопив template_before.
    if (document.querySelector("[data-rs-color-gallery]")) return;
    var group = document.getElementById("color_images-group");
    if (!group) return;
    var fieldset = group.querySelector("fieldset") || group;
    var mount = document.createElement("div");
    mount.className = "rs-color-gallery";
    mount.setAttribute("data-rs-color-gallery", "");
    mount.innerHTML =
      '<div class="rs-color-gallery__bar">' +
      '<span class="rs-color-gallery__label">Колір галереї</span>' +
      '<div class="rs-color-gallery__swatches" data-rs-color-swatches role="tablist"></div>' +
      "</div>" +
      '<p class="rs-color-gallery__hint" data-rs-color-hint hidden></p>' +
      '<p class="rs-color-gallery__active" data-rs-color-active-label hidden></p>';
    var table = fieldset.querySelector("table");
    if (table) fieldset.insertBefore(mount, table);
    else fieldset.appendChild(mount);
  }

  function boot() {
    ensureMount();
    document.querySelectorAll("[data-rs-color-gallery]").forEach(initGallery);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
