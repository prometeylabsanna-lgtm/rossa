(function () {
  const header = document.querySelector("[data-header]");
  if (header) {
    const onScroll = () => header.classList.toggle("is-scrolled", window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  const burger = document.querySelector("[data-burger]");
  const mobile = document.querySelector("[data-mobile-nav]");
  const mqDesktop = window.matchMedia("(min-width: 1024px)");

  const setNavOpen = (open) => {
    if (!burger || !mobile) return;
    if (mqDesktop.matches) open = false;
    mobile.classList.toggle("is-open", open);
    burger.classList.toggle("is-open", open);
    burger.setAttribute("aria-expanded", open ? "true" : "false");
    document.body.classList.toggle("is-nav-open", open);
  };

  if (burger && mobile) {
    burger.addEventListener("click", () => {
      setNavOpen(!mobile.classList.contains("is-open"));
    });
    mobile.querySelectorAll("[data-mobile-close]").forEach((el) => {
      el.addEventListener("click", () => setNavOpen(false));
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") setNavOpen(false);
    });
    mqDesktop.addEventListener("change", () => {
      if (mqDesktop.matches) setNavOpen(false);
    });
  }

  document.querySelectorAll("[data-acc]").forEach((acc) => {
    const toggle = acc.querySelector("[data-acc-toggle]");
    const panel = acc.querySelector("[data-acc-panel]");
    if (!toggle || !panel) return;
    toggle.addEventListener("click", () => {
      const open = !acc.classList.contains("is-open");
      acc.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      if (open) panel.removeAttribute("hidden");
      else panel.setAttribute("hidden", "");
    });
  });

  const searchToggle = document.querySelector("[data-search-toggle]");
  const searchPanel = document.querySelector("[data-search-panel]");
  if (searchToggle && searchPanel) {
    searchToggle.addEventListener("click", () => {
      searchPanel.classList.toggle("is-open");
      const input = searchPanel.querySelector("input");
      if (searchPanel.classList.contains("is-open") && input) input.focus();
    });
    document.addEventListener("click", (event) => {
      if (!searchPanel.contains(event.target) && !searchToggle.contains(event.target)) {
        searchPanel.classList.remove("is-open");
      }
    });
  }

  document.querySelectorAll("[data-mega]").forEach((item) => {
    const links = item.querySelectorAll("[data-mega-cat]");
    const img = item.querySelector("[data-mega-preview]");
    links.forEach((link) => {
      link.addEventListener("mouseenter", () => {
        if (img && link.dataset.preview) img.src = link.dataset.preview;
        links.forEach((el) => el.classList.remove("is-current"));
        link.classList.add("is-current");
      });
    });
  });
})();
