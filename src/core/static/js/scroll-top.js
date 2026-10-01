(function () {
  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function initScrollTop() {
    const btn = document.querySelector("[data-scroll-top]");
    if (!btn || btn.dataset.bound === "1") return;
    btn.dataset.bound = "1";

    const showAfter = Number(btn.getAttribute("data-show-after") || 420);

    const update = () => {
      const longPage = document.documentElement.scrollHeight > window.innerHeight + 240;
      const scrolled = window.scrollY > showAfter;
      btn.classList.toggle("is-visible", longPage && scrolled);
    };

    btn.addEventListener("click", (event) => {
      event.preventDefault();
      const topEl = document.getElementById("top") || document.body;
      if (prefersReducedMotion()) {
        window.scrollTo(0, 0);
        return;
      }
      window.scrollTo({ top: 0, left: 0, behavior: "smooth" });
      if (topEl && typeof topEl.focus === "function") {
        topEl.setAttribute("tabindex", "-1");
        topEl.focus({ preventScroll: true });
      }
    });

    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initScrollTop);
  } else {
    initScrollTop();
  }
})();
