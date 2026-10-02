(function () {
  function parseJsonAttr(el, name, fallback) {
    var raw = el.getAttribute(name) || "";
    if (!raw) return fallback;
    try {
      return JSON.parse(raw);
    } catch (err) {
      return fallback;
    }
  }

  function bindRoot(root) {
    if (root.getAttribute("data-cms-form-bound") === "1") return;
    root.setAttribute("data-cms-form-bound", "1");

    var input = root.querySelector("[data-cms-form-input]");
    var list = root.querySelector("[data-cms-form-list]");
    var schema = parseJsonAttr(root, "data-cms-form-schema", { rows: [] });
    var items = parseJsonAttr(root, "data-cms-form-items", {});
    if (!items || typeof items !== "object") items = {};

    function ensureRow(key) {
      if (!items[key] || typeof items[key] !== "object") {
        items[key] = {
          label_uk: "",
          label_ru: "",
          placeholder_uk: "",
          placeholder_ru: "",
        };
      }
    }

    function sync() {
      input.value = JSON.stringify(items);
    }

    function fieldControl(rowKey, attr, labelText) {
      var wrap = document.createElement("div");
      wrap.className = "rs-cms-json__field";
      var label = document.createElement("label");
      label.textContent = labelText;
      var control = document.createElement("input");
      control.type = "text";
      control.value = items[rowKey][attr] || "";
      control.addEventListener("input", function () {
        items[rowKey][attr] = control.value;
        sync();
      });
      wrap.appendChild(label);
      wrap.appendChild(control);
      return wrap;
    }

    function render() {
      list.innerHTML = "";
      (schema.rows || []).forEach(function (row) {
        var key = row.key;
        ensureRow(key);

        var card = document.createElement("div");
        card.className = "rs-cms-json__item";

        var title = document.createElement("p");
        title.className = "rs-cms-form-copy__title";
        title.textContent = row.title || key;
        card.appendChild(title);

        var fieldsWrap = document.createElement("div");
        fieldsWrap.className = "rs-cms-json__fields rs-cms-form-copy__grid";
        fieldsWrap.appendChild(fieldControl(key, "label_uk", "Підпис (укр)"));
        fieldsWrap.appendChild(fieldControl(key, "label_ru", "Підпис (рос)"));
        if (row.has_placeholder) {
          fieldsWrap.appendChild(fieldControl(key, "placeholder_uk", "Підказка (укр)"));
          fieldsWrap.appendChild(fieldControl(key, "placeholder_ru", "Підказка (рос)"));
        }
        card.appendChild(fieldsWrap);
        list.appendChild(card);
      });
      sync();
    }

    render();
  }

  function init() {
    document.querySelectorAll("[data-cms-form-copy]").forEach(bindRoot);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
