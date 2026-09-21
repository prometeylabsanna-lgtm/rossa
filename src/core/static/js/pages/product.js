(function () {
  const modal = document.querySelector("[data-order-modal]");
  if (!modal) return;

  function bindOpeners() {
    document.querySelectorAll("[data-open-order]").forEach((btn) => {
      if (btn.dataset.bound === "1") return;
      btn.dataset.bound = "1";
      btn.addEventListener("click", () => {
        modal.classList.add("is-open");
        const first = modal.querySelector("input:not([type=hidden])");
        if (first) first.focus();
      });
    });
  }

  bindOpeners();
  document.body.addEventListener("htmx:afterSwap", bindOpeners);

  modal.addEventListener("click", (event) => {
    if (event.target === modal || event.target.closest("[data-close-modal]")) {
      modal.classList.remove("is-open");
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") modal.classList.remove("is-open");
  });
})();
