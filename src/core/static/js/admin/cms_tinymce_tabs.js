(function () {
  function refreshTiny() {
    if (!window.tinymce || !window.tinymce.editors) return;
    window.tinymce.editors.forEach(function (ed) {
      try {
        ed.dispatch("ResizeEditor");
        if (ed.iframeElement) {
          ed.iframeElement.style.width = "100%";
        }
      } catch (err) {}
    });
  }

  document.addEventListener("click", function (event) {
    var tab = event.target.closest("[role='tab'], .unfold-tab-list a, .unfold-tab-list button");
    if (!tab) return;
    window.setTimeout(refreshTiny, 80);
    window.setTimeout(refreshTiny, 250);
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      window.setTimeout(refreshTiny, 400);
    });
  } else {
    window.setTimeout(refreshTiny, 400);
  }
})();
