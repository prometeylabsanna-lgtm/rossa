(() => {
  const root = document.querySelector("[data-hero-slider]");
  if (!root) return;

  const slides = Array.from(root.querySelectorAll("[data-hero-slide]"));
  if (slides.length < 2) return;

  const dots = Array.from(root.querySelectorAll("[data-hero-dot]"));
  const prevBtn = root.querySelector("[data-hero-prev]");
  const nextBtn = root.querySelector("[data-hero-next]");
  const delay = Number(root.dataset.autoplay || 0);
  let index = slides.findIndex((slide) => slide.classList.contains("is-active"));
  if (index < 0) index = 0;
  let timer = null;
  let touching = false;

  const setActive = (next) => {
    index = (next + slides.length) % slides.length;
    slides.forEach((slide, i) => {
      const on = i === index;
      slide.classList.toggle("is-active", on);
      slide.setAttribute("aria-hidden", on ? "false" : "true");
    });
    dots.forEach((dot, i) => {
      const on = i === index;
      dot.classList.toggle("is-active", on);
      if (on) dot.setAttribute("aria-current", "true");
      else dot.removeAttribute("aria-current");
    });
  };

  const stop = () => {
    if (timer) {
      window.clearInterval(timer);
      timer = null;
    }
  };

  const start = () => {
    if (!delay || touching || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    stop();
    timer = window.setInterval(() => setActive(index + 1), delay);
  };

  prevBtn?.addEventListener("click", () => {
    setActive(index - 1);
    start();
  });
  nextBtn?.addEventListener("click", () => {
    setActive(index + 1);
    start();
  });
  dots.forEach((dot) => {
    dot.addEventListener("click", () => {
      setActive(Number(dot.dataset.heroDot) || 0);
      start();
    });
  });

  root.addEventListener("mouseenter", stop);
  root.addEventListener("mouseleave", start);
  root.addEventListener("focusin", stop);
  root.addEventListener("focusout", start);

  let touchX = 0;
  root.addEventListener(
    "touchstart",
    (e) => {
      touching = true;
      stop();
      touchX = e.changedTouches[0].clientX;
    },
    { passive: true },
  );
  root.addEventListener(
    "touchend",
    (e) => {
      const dx = e.changedTouches[0].clientX - touchX;
      if (Math.abs(dx) > 40) setActive(index + (dx < 0 ? 1 : -1));
      touching = false;
      start();
    },
    { passive: true },
  );

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stop();
    else start();
  });

  setActive(index);
  start();
})();
