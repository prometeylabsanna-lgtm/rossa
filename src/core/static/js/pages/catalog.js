(function () {
  function submitFilterForm(el) {
    const form = el.closest("form");
    if (form) form.submit();
  }

  document.addEventListener("change", function (event) {
    const auto = event.target.closest("[data-filter-auto], [data-sort]");
    if (!auto) return;
    submitFilterForm(auto);
  });
})();
