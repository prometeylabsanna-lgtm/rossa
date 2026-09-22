/**
 * Parallax via transform: translateY — iOS Safari safe.
 * Disabled when prefers-reduced-motion is set.
 */
(function () {
  let rafId = null;

  function initParallax() {
    if (rafId !== null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const sections = Array.from(document.querySelectorAll("[data-parallax]"));
    if (!sections.length) return;

    let lastScroll = -1;

    function tick() {
      const scrollY = window.scrollY;

      if (scrollY !== lastScroll) {
        lastScroll = scrollY;

        sections.forEach((section) => {
          const bg = section.querySelector("[data-parallax-bg]");
          if (!bg) return;

          const rect = section.getBoundingClientRect();
          if (rect.bottom < -200 || rect.top > window.innerHeight + 200) return;

          const speed = parseFloat(section.dataset.parallaxSpeed || "0.3");
          const sectionMid = rect.top + rect.height / 2;
          const viewportMid = window.innerHeight / 2;
          const offset = (sectionMid - viewportMid) * speed;

          bg.style.transform = `translateY(${offset.toFixed(2)}px)`;
        });
      }

      rafId = requestAnimationFrame(tick);
    }

    rafId = requestAnimationFrame(tick);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initParallax);
  } else {
    initParallax();
  }

  document.addEventListener("htmx:afterSwap", initParallax);
  document.addEventListener("htmx:historyRestore", initParallax);
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) initParallax();
  });
})();
