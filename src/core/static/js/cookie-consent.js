/**
 * Cookie consent: банер + GTM лише після «Прийняти».
 * Значення: all | necessary (localStorage + cookie).
 */
(function () {
  var STORAGE_KEY = "rossa_cookie_consent";
  var COOKIE_MAX_AGE = 60 * 60 * 24 * 365;

  function readStorage() {
    try {
      return localStorage.getItem(STORAGE_KEY) || "";
    } catch (_err) {
      return "";
    }
  }

  function readCookie() {
    var match = document.cookie.match(
      new RegExp("(?:^|; )" + STORAGE_KEY.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "=([^;]*)")
    );
    return match ? decodeURIComponent(match[1]) : "";
  }

  function getConsent() {
    var value = readStorage() || readCookie();
    return value === "all" || value === "necessary" ? value : "";
  }

  function setConsent(value) {
    try {
      localStorage.setItem(STORAGE_KEY, value);
    } catch (_err) {
      /* private mode */
    }
    document.cookie =
      STORAGE_KEY +
      "=" +
      encodeURIComponent(value) +
      ";path=/;max-age=" +
      COOKIE_MAX_AGE +
      ";SameSite=Lax";
  }

  function loadGtm(id) {
    if (!id || window.__rossaGtmLoaded) return;
    if (!/^GTM-[A-Z0-9]+$/.test(id)) return;
    window.__rossaGtmLoaded = true;
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
      "gtm.start": new Date().getTime(),
      event: "gtm.js",
    });
    var first = document.getElementsByTagName("script")[0];
    var script = document.createElement("script");
    script.async = true;
    script.src = "https://www.googletagmanager.com/gtm.js?id=" + encodeURIComponent(id);
    if (first && first.parentNode) {
      first.parentNode.insertBefore(script, first);
    } else {
      document.head.appendChild(script);
    }
  }

  function hideBanner(banner) {
    if (!banner) return;
    banner.hidden = true;
    document.body.classList.remove("has-cookie-banner");
  }

  function showBanner(banner) {
    if (!banner) return;
    banner.hidden = false;
    document.body.classList.add("has-cookie-banner");
  }

  function init() {
    var banner = document.querySelector("[data-cookie-banner]");
    if (!banner) return;
    var gtmId = (banner.getAttribute("data-gtm-id") || "").trim();
    var consent = getConsent();

    if (consent === "all") {
      loadGtm(gtmId);
      hideBanner(banner);
      return;
    }
    if (consent === "necessary") {
      hideBanner(banner);
      return;
    }

    showBanner(banner);

    var acceptBtn = banner.querySelector("[data-cookie-accept]");
    var necessaryBtn = banner.querySelector("[data-cookie-necessary]");

    if (acceptBtn) {
      acceptBtn.addEventListener("click", function () {
        setConsent("all");
        loadGtm(gtmId);
        hideBanner(banner);
      });
    }
    if (necessaryBtn) {
      necessaryBtn.addEventListener("click", function () {
        setConsent("necessary");
        hideBanner(banner);
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
