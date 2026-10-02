(function () {
  var IMAGE_NAME_RE = /\.(jpe?g|png|gif|webp|avif|svg)$/i;
  // Один файл: запас під інші поля форми в межах ліміту Vercel ≈ 4.5 МБ.
  var MAX_FILE_BYTES = 2.5 * 1024 * 1024;
  var MAX_EDGE = 1600;

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
        if (item.value !== val) {
          item.el.value = item.value;
        }
      }
    });
  }

  function loadImage(file) {
    return new Promise(function (resolve, reject) {
      var url = URL.createObjectURL(file);
      var img = new Image();
      img.onload = function () {
        URL.revokeObjectURL(url);
        resolve(img);
      };
      img.onerror = function () {
        URL.revokeObjectURL(url);
        reject(new Error("image load failed"));
      };
      img.src = url;
    });
  }

  function canvasToBlob(canvas, type, quality) {
    return new Promise(function (resolve) {
      canvas.toBlob(function (blob) {
        resolve(blob);
      }, type, quality);
    });
  }

  function compressImage(file) {
    if (!file || file.size <= MAX_FILE_BYTES) {
      return Promise.resolve(file);
    }
    if (!file.type || file.type.indexOf("image/") !== 0 || file.type === "image/svg+xml") {
      return Promise.resolve(file);
    }
    return loadImage(file).then(function (img) {
      var w = img.naturalWidth || img.width;
      var h = img.naturalHeight || img.height;
      if (!w || !h) return file;
      var scale = Math.min(1, MAX_EDGE / Math.max(w, h));
      var cw = Math.max(1, Math.round(w * scale));
      var ch = Math.max(1, Math.round(h * scale));
      var canvas = document.createElement("canvas");
      canvas.width = cw;
      canvas.height = ch;
      var ctx = canvas.getContext("2d");
      if (!ctx) return file;
      ctx.drawImage(img, 0, 0, cw, ch);
      var type = file.type === "image/png" ? "image/png" : "image/jpeg";
      var quality = type === "image/jpeg" ? 0.82 : undefined;
      return canvasToBlob(canvas, type, quality).then(function (blob) {
        if (!blob || blob.size >= file.size) return file;
        var base = (file.name || "image").replace(/\.[^.]+$/, "");
        var ext = type === "image/png" ? ".png" : ".jpg";
        return new File([blob], base + ext, { type: type, lastModified: Date.now() });
      });
    }).catch(function () {
      return file;
    });
  }

  function assignFile(input, file) {
    try {
      var dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
    } catch (err) {
      // Safari старих версій — лишаємо оригінал
    }
  }

  function showPreview(wrap, file) {
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
      var mb = (file.size / (1024 * 1024)).toFixed(1);
      hint.textContent = "Обрано файл: " + file.name + " (" + mb + " МБ)";
      hint.hidden = false;
    }
  }

  function bindInput(input) {
    if (input.dataset.cmsImageBound) return;
    input.dataset.cmsImageBound = "1";
    input.setAttribute("autocomplete", "off");
    input.addEventListener("change", function () {
      var file = input.files && input.files[0];
      var wrap = input.closest("[data-cms-image]");
      if (!wrap || !file) return;
      if (file.type && file.type.indexOf("image/") !== 0) return;
      var slide = input.closest(".rs-cms__slide") || wrap.closest(".rs-cms-field") || wrap;
      var snapshot = snapshotTextFields(slide);

      compressImage(file).then(function (next) {
        if (next.size > MAX_FILE_BYTES) {
          window.alert(
            "Фото занадто велике (" +
              (next.size / (1024 * 1024)).toFixed(1) +
              " МБ). Стисніть до ≈2.5 МБ — інакше збереження на Vercel впаде з 413."
          );
          input.value = "";
          return;
        }
        if (next !== file) {
          assignFile(input, next);
        }
        showPreview(wrap, next);
        restoreIfFilename(snapshot, file.name);
        restoreIfFilename(snapshot, next.name);
        window.setTimeout(function () {
          restoreIfFilename(snapshot, file.name);
          restoreIfFilename(snapshot, next.name);
        }, 0);
        window.setTimeout(function () {
          restoreIfFilename(snapshot, file.name);
          restoreIfFilename(snapshot, next.name);
        }, 50);
      });
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
