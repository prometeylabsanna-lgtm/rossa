(function () {
  let observer = null;
  let drawObserver = null;

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function revealNow(el) {
    el.classList.add("is-visible");
    if (observer) observer.unobserve(el);
  }

  function revealInView() {
    const vh = window.innerHeight;
    document.querySelectorAll(".reveal:not(.is-visible)").forEach((el) => {
      const rect = el.getBoundingClientRect();
      if (rect.top < vh && rect.bottom > 0) revealNow(el);
    });
  }

  function drawNow(el) {
    if (el.classList.contains("is-drawn")) return;
    // Double rAF so the browser paints scale(0) before the keyframes start.
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        el.classList.add("is-drawn");
      });
    });
    if (drawObserver) drawObserver.unobserve(el);
  }

  function initDrawDividers() {
    if (drawObserver) {
      drawObserver.disconnect();
      drawObserver = null;
    }

    const targets = document.querySelectorAll("[data-draw-dividers]");
    if (!targets.length) return;

    if (prefersReducedMotion()) {
      targets.forEach((el) => el.classList.add("is-drawn"));
      return;
    }

    drawObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          drawNow(entry.target);
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.2 }
    );

    targets.forEach((el) => {
      if (el.classList.contains("is-drawn")) return;
      drawObserver.observe(el);
      const rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight * 0.92 && rect.bottom > 0) {
        drawNow(el);
      }
    });
  }

  function initReveal() {
    if (observer) {
      observer.disconnect();
      observer = null;
    }

    if (prefersReducedMotion()) {
      document.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-visible"));
      initDrawDividers();
      return;
    }

    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          revealNow(entry.target);
        });
      },
      { rootMargin: "0px 0px -6% 0px", threshold: 0.01 }
    );

    document.querySelectorAll(".reveal:not(.is-visible)").forEach((el) => {
      const delay = el.dataset.revealDelay;
      if (delay) el.style.setProperty("--reveal-delay", `${delay}ms`);
      observer.observe(el);
    });

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        revealInView();
        initDrawDividers();
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initReveal);
  } else {
    initReveal();
  }

  document.addEventListener("htmx:afterSwap", initReveal);
  document.addEventListener("htmx:historyRestore", initReveal);
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) initReveal();
  });
})();
