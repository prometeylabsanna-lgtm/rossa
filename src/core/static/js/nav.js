(function () {
  const header = document.querySelector("[data-header]");
  if (header) {
    const onScroll = () => header.classList.toggle("is-scrolled", window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  const burger = document.querySelector("[data-burger]");
  const mobile = document.querySelector("[data-mobile-nav]");
  if (burger && mobile) {
    burger.addEventListener("click", () => {
      const open = mobile.classList.toggle("is-open");
      burger.classList.toggle("is-open", open);
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

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
