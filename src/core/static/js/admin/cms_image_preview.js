(function () {
  var IMAGE_NAME_RE = /\.(jpe?g|png|gif|webp|avif|svg)$/i;

  function snapshotTextFields(root) {
    var out = [];
    if (!root) return out;
    root.querySelectorAll("input[type='text'], input:not([type]), textarea").forEach(function (el) {
      if (el.disabled || el.readOnly) return;
      if (el.getAttribute("data-cms-image-input") != null) return;
      out.push({ el: el, value: el.value });
    });
    return out;
  }

  function restoreIfFilename(snapshot, fileName) {
    if (!fileName) return;
    snapshot.forEach(function (item) {
      var val = (item.el.value || "").trim();
      if (!val) return;
      if (val === fileName || val.indexOf(fileName) !== -1 || IMAGE_NAME_RE.test(val)) {
        // лише якщо значення змінилося на імʼя файлу після вибору фото
        if (item.value !== val) {
          item.el.value = item.value;
        }
      }
    });
  }

  function bindInput(input) {
    if (input.dataset.cmsImageBound) return;
    input.dataset.cmsImageBound = "1";
    input.setAttribute("autocomplete", "off");
    input.addEventListener("change", function () {
      var file = input.files && input.files[0];
      var wrap = input.closest("[data-cms-image]");
      if (!wrap) return;
      var slide = input.closest(".rs-cms__slide") || wrap.closest(".rs-cms-field") || wrap;
      var snapshot = snapshotTextFields(slide);
      var frame = wrap.querySelector(".rs-cms-image__frame");
      var img = wrap.querySelector("[data-cms-image-preview]");
      var placeholder = wrap.querySelector("[data-cms-image-placeholder]");
      if (!img) {
        img = document.createElement("img");
        img.className = "rs-cms-image__preview";
        img.setAttribute("data-cms-image-preview", "");
        img.alt = "";
        if (frame) frame.insertBefore(img, frame.firstChild);
        else wrap.insertBefore(img, wrap.firstChild);
      }
      var clearBox = wrap.querySelector("[data-cms-image-clear]");
      if (!file) return;
      if (file.type && file.type.indexOf("image/") !== 0) return;
      if (img.dataset.objectUrl) {
        URL.revokeObjectURL(img.dataset.objectUrl);
      }
      var url = URL.createObjectURL(file);
      img.dataset.objectUrl = url;
      img.src = url;
      img.hidden = false;
      img.classList.remove("is-empty");
      if (frame) frame.classList.remove("is-empty");
      if (placeholder) placeholder.hidden = true;
      if (clearBox) clearBox.checked = false;
      var hint = wrap.querySelector("[data-cms-image-name]");
      if (hint) {
        hint.textContent = "Обрано файл: " + file.name;
        hint.hidden = false;
      }
      // Chrome інколи підставляє імʼя файлу в сусіднє text-поле
      restoreIfFilename(snapshot, file.name);
      window.setTimeout(function () {
        restoreIfFilename(snapshot, file.name);
      }, 0);
      window.setTimeout(function () {
        restoreIfFilename(snapshot, file.name);
      }, 50);
    });
  }

  function bindClear(box) {
    if (box.dataset.cmsImageClearBound) return;
    box.dataset.cmsImageClearBound = "1";
    box.addEventListener("change", function () {
      var wrap = box.closest("[data-cms-image]");
      if (!wrap) return;
      var frame = wrap.querySelector(".rs-cms-image__frame");
      var img = wrap.querySelector("[data-cms-image-preview]");
      var placeholder = wrap.querySelector("[data-cms-image-placeholder]");
      var hint = wrap.querySelector("[data-cms-image-name]");
      if (!img) return;
      img.hidden = box.checked;
      if (frame) frame.classList.toggle("is-empty", box.checked);
      if (placeholder) placeholder.hidden = !box.checked;
      if (hint && box.checked) {
        hint.hidden = true;
        hint.textContent = "";
      }
    });
  }

  function init() {
    document.querySelectorAll("input[type=file][accept='image/*'], [data-cms-image-input]").forEach(bindInput);
    document.querySelectorAll("[data-cms-image-clear]").forEach(bindClear);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
