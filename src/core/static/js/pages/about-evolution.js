(function () {
  'use strict';

  var SELECTOR = '[data-evolution-gallery]';

  function itemHeight(item) {
    var img = item.querySelector('img');
    if (!img) return 0;
    var width = item.clientWidth;
    if (!width) return 0;

    if (img.naturalWidth && img.naturalHeight) {
      return width * (img.naturalHeight / img.naturalWidth);
    }

    var attrW = parseFloat(img.getAttribute('width'));
    var attrH = parseFloat(img.getAttribute('height'));
    if (attrW > 0 && attrH > 0) {
      return width * (attrH / attrW);
    }
    return 0;
  }

  function sizeGallery(gallery) {
    var items = gallery.querySelectorAll('.evolution-gallery__item');
    if (!items.length) return;

    gallery.classList.remove('is-sized');
    gallery.style.removeProperty('--evolution-item-h');

    var minH = Infinity;
    for (var i = 0; i < items.length; i += 1) {
      var h = itemHeight(items[i]);
      if (h > 0 && h < minH) minH = h;
    }
    if (!isFinite(minH) || minH <= 0) return;

    gallery.style.setProperty('--evolution-item-h', Math.round(minH) + 'px');
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
