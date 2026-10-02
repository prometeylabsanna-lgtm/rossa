(function () {
  'use strict';

  var SELECTOR = '[data-evolution-gallery]';

  function imageMetrics(img) {
    var nw = img.naturalWidth;
    var nh = img.naturalHeight;
    if (!(nw > 0 && nh > 0)) {
      nw = parseFloat(img.getAttribute('width')) || 0;
      nh = parseFloat(img.getAttribute('height')) || 0;
    }
    if (!(nw > 0 && nh > 0)) return null;
    return { w: nw, h: nh, area: nw * nh, ar: nw / nh };
  }

  function sizeGallery(gallery) {
    var items = gallery.querySelectorAll('.evolution-gallery__item');
    if (!items.length) return;

    gallery.classList.remove('is-sized');
    gallery.style.removeProperty('--evolution-item-ar');
    gallery.style.removeProperty('--evolution-item-h');

    var largest = null;
    for (var i = 0; i < items.length; i += 1) {
      var img = items[i].querySelector('img');
      if (!img) continue;
      var m = imageMetrics(img);
      if (!m) continue;
      if (!largest || m.area > largest.area) largest = m;
    }
    if (!largest) return;

    gallery.style.setProperty('--evolution-item-ar', String(largest.ar));
    gallery.classList.add('is-sized');
  }

  function bindGallery(gallery) {
    var frame = 0;
    function schedule() {
      if (frame) cancelAnimationFrame(frame);
      frame = requestAnimationFrame(function () {
        frame = 0;
        sizeGallery(gallery);
      });
    }

    var imgs = gallery.querySelectorAll('img');
    for (var i = 0; i < imgs.length; i += 1) {
      imgs[i].addEventListener('load', schedule, { passive: true });
      imgs[i].addEventListener('error', schedule, { passive: true });
    }

    schedule();

    if (typeof ResizeObserver !== 'undefined') {
      var ro = new ResizeObserver(schedule);
      ro.observe(gallery);
    } else {
      window.addEventListener('resize', schedule, { passive: true });
      window.addEventListener('orientationchange', schedule, { passive: true });
    }
  }

  function init() {
    var galleries = document.querySelectorAll(SELECTOR);
    for (var i = 0; i < galleries.length; i += 1) {
      bindGallery(galleries[i]);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
