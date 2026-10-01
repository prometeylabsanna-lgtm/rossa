(function () {
  function initBackFloat() {
    const btn = document.querySelector("[data-back-float]");
    if (!btn || btn.dataset.bound === "1") return;
    btn.dataset.bound = "1";

    const fallback = btn.getAttribute("data-fallback") || "/";
    const showAfter = Number(btn.getAttribute("data-show-after") || 480);

    const update = () => {
      const longPage = document.documentElement.scrollHeight > window.innerHeight + 240;
      const scrolled = window.scrollY > showAfter;
      btn.classList.toggle("is-visible", longPage && scrolled);
    };

    btn.addEventListener("click", (event) => {
      event.preventDefault();
      if (window.history.length > 1) {
        window.history.back();
        return;
      }
      window.location.href = fallback;
    });

    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  document.addEventListener("DOMContentLoaded", initBackFloat);
})();
