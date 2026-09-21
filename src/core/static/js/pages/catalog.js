(function () {
  document.addEventListener("change", function (event) {
    const select = event.target.closest("[data-sort]");
    if (!select) return;
    const form = select.closest("form");
    if (form) form.submit();
  });
})();
