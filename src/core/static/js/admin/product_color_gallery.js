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

  function colorInputs(group) {
    return Array.prototype.slice.call(
      group.querySelectorAll(
        'input[name*="color_images-"][name$="-color"], select[name*="color_images-"][name$="-color"]'
      )
    ).filter(function (input) {
      return input.name.indexOf("__prefix__") === -1;
    });
  }

  function rowForInput(input) {
    return input.closest("tbody") || input.closest("tr") || input.closest(".inline-related");
  }

  function hasPrimaryKey(row) {
    var idInput = row.querySelector('input[name$="-id"]');
    return !!(idInput && idInput.value);
  }

  function initGallery(root) {
    if (!root || root.getAttribute("data-rs-bound") === "1") return;
    root.setAttribute("data-rs-bound", "1");

    var swatches = readSwatches();
    var swatchesEl = root.querySelector("[data-rs-color-swatches]");
    var hintEl = root.querySelector("[data-rs-color-hint]");
    var activeLabel = root.querySelector("[data-rs-color-active-label]");
    var group =
      document.getElementById("color_images-group") ||
      root.closest("[data-inline-type='tabular']") ||
      root.parentElement;
    if (!group || !swatchesEl) return;

    var table = group.querySelector("table");
    var addRow = group.querySelector(".add-row");

    function hideColorColumn() {
      group.querySelectorAll("th.column-color, td.field-color, .field-color").forEach(function (cell) {
        cell.classList.add("rs-color-col-hidden");
      });
    }

    function setVisible(row, show) {
      if (!row) return;
      row.classList.toggle("rs-color-row-hidden", !show);
      row.hidden = !show;
      // запас для старих WebKit, де hidden на tbody ігнорується
      row.style.display = show ? "" : "none";
    }

    function applyFilter(activeId) {
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

      colorInputs(group).forEach(function (input) {
        var row = rowForInput(input);
        if (!row || row.classList.contains("empty-form")) return;

        var cid = String(input.value || "");
        // Не перетираємо колір уже збережених рядків.
        if (!cid && !hasPrimaryKey(row)) {
          input.value = String(activeId);
          cid = String(activeId);
        }
        setVisible(row, cid === String(activeId));
      });

      var tmpl = group.querySelector(
        'input[name="color_images-__prefix__-color"], select[name="color_images-__prefix__-color"]'
      );
      if (tmpl) tmpl.value = String(activeId);

      // empty-form tbody
      var emptyTbody = group.querySelector("tbody.empty-form");
      if (emptyTbody) {
        var emptyColor = emptyTbody.querySelector(
          'input[name$="-color"], select[name$="-color"]'
        );
        if (emptyColor) emptyColor.value = String(activeId);
      }

      hideColorColumn();
    }

    if (!swatches.length) {
      if (hintEl) hintEl.hidden = false;
      if (table) table.classList.add("rs-color-row-hidden");
      if (addRow) addRow.classList.add("rs-color-row-hidden");
      swatchesEl.innerHTML = "";
      if (activeLabel) activeLabel.hidden = true;
      return;
    }

    if (hintEl) hintEl.hidden = true;
    if (table) table.classList.remove("rs-color-row-hidden");
    if (addRow) addRow.classList.remove("rs-color-row-hidden");

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
        applyFilter(activeId);
      });
      swatchesEl.appendChild(btn);
    });

    var debounce = null;
    if (window.MutationObserver && table) {
      var observer = new MutationObserver(function () {
        window.clearTimeout(debounce);
        debounce = window.setTimeout(function () {
          applyFilter(activeId);
        }, 30);
      });
      observer.observe(table, { childList: true, subtree: true });
    }

    group.addEventListener("click", function (event) {
      if (!event.target.closest(".add-row a, a.add-row, .inline-add")) return;
      window.setTimeout(function () {
        applyFilter(activeId);
      }, 50);
    });

    applyFilter(activeId);
  }

  function ensureMount() {
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
