(function () {
  // Vercel Function body ≈ 4.5 МБ; залишаємо запас на multipart-оверхед.
  var MAX_BYTES = 3.5 * 1024 * 1024;

  function formatMb(bytes) {
    return (bytes / (1024 * 1024)).toFixed(1);
  }

  function estimateFormBytes(form) {
    var total = 0;
    var fd;
    try {
      fd = new FormData(form);
    } catch (err) {
      return 0;
    }
    fd.forEach(function (value) {
      if (value && typeof value === "object" && typeof value.size === "number") {
        total += value.size;
        return;
      }
      total += new Blob([String(value == null ? "" : value)]).size;
    });
    return total;
  }

  function hasHeavyDataUri(form) {
    var found = false;
    form.querySelectorAll("textarea").forEach(function (el) {
      var v = el.value || "";
      if (v.indexOf("data:image") !== -1 && v.length > 200000) {
        found = true;
      }
    });
    if (window.tinymce && window.tinymce.editors) {
      window.tinymce.editors.forEach(function (ed) {
        try {
          var html = ed.getContent() || "";
          if (html.indexOf("data:image") !== -1 && html.length > 200000) {
            found = true;
          }
        } catch (err) {}
      });
    }
    return found;
  }

  function bindForm(form) {
    if (!form || form.getAttribute("data-cms-payload-bound") === "1") return;
    form.setAttribute("data-cms-payload-bound", "1");
    form.addEventListener("submit", function (event) {
      if (window.tinymce && window.tinymce.triggerSave) {
        try {
          window.tinymce.triggerSave();
        } catch (err) {}
      }
      if (hasHeavyDataUri(form)) {
        event.preventDefault();
        event.stopPropagation();
        window.alert(
          "У текстових полях є великі зображення (data:image). " +
            "Видаліть вставлені картинки з опису — на Vercel ліміт тіла запиту ≈ 4.5 МБ."
        );
        return;
      }
      var size = estimateFormBytes(form);
      if (size <= MAX_BYTES) return;
      event.preventDefault();
      event.stopPropagation();
      window.alert(
        "Запит занадто великий (" +
          formatMb(size) +
          " МБ). На Vercel ліміт ≈ 4.5 МБ.\n" +
          "Приберіть великі фото / вставлені в текст картинки або стисніть файли (≈2 МБ кожне)."
      );
    });
  }

  function init() {
    if (window.location.pathname.indexOf("/admin/") !== 0) return;
    document.querySelectorAll("form").forEach(bindForm);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
