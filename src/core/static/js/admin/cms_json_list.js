(function () {
  function csrfToken() {
    var input = document.querySelector("input[name=csrfmiddlewaretoken]");
    if (input && input.value) return input.value;
    var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function parseJsonAttr(el, name, fallback) {
    var raw = el.getAttribute(name) || "";
    if (!raw) return fallback;
    try {
      return JSON.parse(raw);
    } catch (err) {
      return fallback;
    }
  }

  function emptyItem(schema) {
    var item = {};
    (schema.fields || []).forEach(function (field) {
      item[field.key] = "";
    });
    return item;
  }

  function bindRoot(root) {
    if (root.getAttribute("data-cms-json-bound") === "1") return;
    root.setAttribute("data-cms-json-bound", "1");

    var input = root.querySelector("[data-cms-json-input]");
    var list = root.querySelector("[data-cms-json-list]");
    var addBtn = root.querySelector("[data-cms-json-add]");
    var schema = parseJsonAttr(root, "data-cms-json-schema", { fields: [] });
    var uploadTo = root.getAttribute("data-cms-json-upload") || schema.upload_to || "";
    var items = parseJsonAttr(root, "data-cms-json-items", []);
    if (!Array.isArray(items)) items = [];

    function sync() {
      input.value = JSON.stringify(items);
    }

    function move(index, delta) {
      var next = index + delta;
      if (next < 0 || next >= items.length) return;
      var tmp = items[index];
      items[index] = items[next];
      items[next] = tmp;
      render();
    }

    function removeAt(index) {
      items.splice(index, 1);
      render();
    }

    function uploadFile(file, index, statusEl) {
      if (!file || !uploadTo) return;
      statusEl.textContent = "Завантаження…";
      var body = new FormData();
      body.append("file", file);
      body.append("upload_to", uploadTo);
      fetch("/admin/cms-upload/", {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken() },
        body: body,
        credentials: "same-origin",
      })
        .then(function (res) {
          return res.json().then(function (data) {
            if (!res.ok) throw new Error((data && data.error) || "Помилка завантаження");
            return data;
          });
        })
        .then(function (data) {
          items[index].image = data.url || "";
          statusEl.textContent = "Завантажено";
          render();
        })
        .catch(function (err) {
          statusEl.textContent = err.message || "Не вдалося завантажити";
        });
    }

    function render() {
      list.innerHTML = "";
      items.forEach(function (item, index) {
        var card = document.createElement("div");
        card.className = "rs-cms-json__item";

        var toolbar = document.createElement("div");
        toolbar.className = "rs-cms-json__toolbar";

        function mkBtn(label, className, onClick) {
          var btn = document.createElement("button");
          btn.type = "button";
          btn.className = "rs-cms-json__btn" + (className ? " " + className : "");
          btn.textContent = label;
          btn.addEventListener("click", onClick);
          toolbar.appendChild(btn);
        }

        mkBtn("↑", "", function () { move(index, -1); });
        mkBtn("↓", "", function () { move(index, 1); });
        mkBtn("Видалити", "is-danger", function () { removeAt(index); });

        card.appendChild(toolbar);

        var fieldsWrap = document.createElement("div");
        fieldsWrap.className = "rs-cms-json__fields";

        (schema.fields || []).forEach(function (field) {
          if (field.type === "image") {
            var preview = document.createElement("div");
            preview.className = "rs-cms-json__preview" + (item.image ? "" : " is-empty");
            if (item.image) {
              var img = document.createElement("img");
              img.src = item.image;
              img.alt = "";
              img.width = 160;
              img.height = 110;
              preview.appendChild(img);
            }
            fieldsWrap.appendChild(preview);

            var fileLabel = document.createElement("label");
            fileLabel.className = "rs-cms-json__btn";
            fileLabel.textContent = item.image ? "Замінити фото" : "Завантажити фото";
            var fileInput = document.createElement("input");
            fileInput.type = "file";
            fileInput.accept = "image/*";
            fileInput.className = "rs-cms-json__file";
            var status = document.createElement("span");
            status.className = "rs-cms-json__status";
            fileInput.addEventListener("change", function () {
              var file = fileInput.files && fileInput.files[0];
              uploadFile(file, index, status);
            });
            fileLabel.appendChild(fileInput);
            fieldsWrap.appendChild(fileLabel);
            fieldsWrap.appendChild(status);
            return;
          }

          var wrap = document.createElement("div");
          wrap.className = "rs-cms-json__field";
          var label = document.createElement("label");
          label.textContent = field.label || field.key;
          var control;
          if (field.type === "textarea") {
            control = document.createElement("textarea");
            control.rows = 4;
          } else if (field.type === "select") {
            control = document.createElement("select");
            var blank = document.createElement("option");
            blank.value = "";
            blank.textContent = "— оберіть —";
            control.appendChild(blank);
            (field.choices || []).forEach(function (choice) {
              var opt = document.createElement("option");
              opt.value = choice.value || "";
              opt.textContent = choice.label || choice.value || "";
              control.appendChild(opt);
            });
          } else {
            control = document.createElement("input");
            control.type = "text";
          }
          control.value = item[field.key] || "";
          control.addEventListener("input", function () {
            items[index][field.key] = control.value;
            sync();
          });
          control.addEventListener("change", function () {
            items[index][field.key] = control.value;
            sync();
          });
          wrap.appendChild(label);
          wrap.appendChild(control);
          fieldsWrap.appendChild(wrap);
        });

        card.appendChild(fieldsWrap);
        list.appendChild(card);
      });
      sync();
    }

    addBtn.addEventListener("click", function () {
      items.push(emptyItem(schema));
      render();
    });

    render();
  }

  function init() {
    document.querySelectorAll("[data-cms-json]").forEach(bindRoot);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
