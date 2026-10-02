(function () {
  var STORAGE_KEY = "rs-cms-lang";
  var LANGS = ["uk", "ru"];
  var LABELS = { uk: "Українська", ru: "Російська" };

  function langFromName(name) {
    if (!name) return "";
    if (/_uk$/.test(name)) return "uk";
    if (/_ru$/.test(name)) return "ru";
    return "";
  }

  function fieldNameFromClass(el) {
    var cls = (el && el.className) || "";
    var m = String(cls).match(/(?:^|\s)(?:field|column)-([a-z0-9_]+)/i);
    return m ? m[1] : "";
  }

  function closestField(el) {
    var td = el.closest("td.field-tabular, td[class*='field-']");
    if (td) return td;
    return el.closest(".rs-cms-field")
      || el.closest(".form-row")
      || el.closest("[class*='field-']")
      || el.parentElement;
  }

  function markMatchingHeader(cell, lang) {
    if (!cell || cell.tagName !== "TD") return;
    var name = fieldNameFromClass(cell);
    if (!name) return;
    var table = cell.closest("table");
    if (!table) return;
    var th = table.querySelector("th.column-" + name);
    if (th && lang) th.setAttribute("data-cms-lang", lang);
  }

  function markFields() {
    document.querySelectorAll("input, textarea, select").forEach(function (el) {
      var lang = langFromName(el.getAttribute("name") || "");
      if (!lang) return;
      el.setAttribute("data-cms-lang", lang);
      var wrap = closestField(el);
      if (wrap) {
        wrap.setAttribute("data-cms-lang", lang);
        markMatchingHeader(wrap, lang);
      }
    });

    document.querySelectorAll("label[for]").forEach(function (label) {
      var id = label.getAttribute("for");
      if (!id) return;
      var input = document.getElementById(id);
      if (!input) return;
      var lang = langFromName(input.getAttribute("name") || id);
      if (!lang) return;
      var wrap = closestField(label);
      if (wrap) wrap.setAttribute("data-cms-lang", lang);
    });
  }

  function ensureToolbar() {
    if (document.querySelector("[data-cms-langs]")) return;
    var contentTab = document.querySelector(".tab-content, #content-main, .rs-cms");
    if (!contentTab) return;
    if (!document.querySelector("[data-cms-lang='uk'], [data-cms-lang='ru'], input[name$='_uk'], textarea[name$='_uk']")) {
      return;
    }
    var bar = document.createElement("div");
    bar.className = "rs-cms-langs";
    bar.setAttribute("data-cms-langs", "");
    bar.setAttribute("role", "tablist");
    bar.setAttribute("aria-label", "Мова текстів");
    LANGS.forEach(function (code) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "rs-cms-langs__btn";
      btn.setAttribute("data-cms-lang-btn", code);
      btn.setAttribute("role", "tab");
      btn.textContent = LABELS[code] || code;
      bar.appendChild(btn);
    });
    var form = document.querySelector("#content-main form, form");
    var anchor = document.querySelector(".unfold-tab-list, [role='tablist']") || form;
    if (anchor && anchor.parentNode) {
      anchor.parentNode.insertBefore(bar, anchor.nextSibling || anchor);
    } else if (form && form.parentNode) {
      form.parentNode.insertBefore(bar, form);
    }
  }

  function applyLang(lang) {
    if (LANGS.indexOf(lang) === -1) lang = "uk";
    document.body.classList.remove("cms-lang-uk", "cms-lang-ru");
    document.body.classList.add("cms-lang-" + lang);
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch (err) {}
    document.querySelectorAll("[data-cms-lang-btn]").forEach(function (btn) {
      var active = btn.getAttribute("data-cms-lang-btn") === lang;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
  }

  function bind() {
    markFields();
    ensureToolbar();
    var saved = "uk";
    try {
      saved = localStorage.getItem(STORAGE_KEY) || "uk";
    } catch (err) {}
    applyLang(saved);
    document.querySelectorAll("[data-cms-lang-btn]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        applyLang(btn.getAttribute("data-cms-lang-btn"));
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
})();
