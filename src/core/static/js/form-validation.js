/**
 * Публічні lead-форми: маска UA-телефону, live-валідація імені, blur телефону.
 * Кнопка активна; при submit — фокус на перше поле з помилкою.
 */
(function () {
  var PHONE_MAX_DIGITS = 12; // 380 + 9

  function msg(form, key, fallback) {
    return (form && form.getAttribute("data-msg-" + key)) || fallback || "";
  }

  function ensureHint(control) {
    var wrap = control.closest(".form__field") || control.parentElement;
    if (!wrap) return null;
    var hint = wrap.querySelector("[data-field-error]");
    if (!hint) {
      hint = document.createElement("p");
      hint.className = "form__error";
      hint.setAttribute("data-field-error", "");
      hint.hidden = true;
      wrap.appendChild(hint);
    }
    return hint;
  }

  function setState(control, ok, text) {
    if (!control) return;
    control.classList.remove("is-invalid", "is-valid");
    if (ok === true) control.classList.add("is-valid");
    if (ok === false) control.classList.add("is-invalid");
    var hint = ensureHint(control);
    if (!hint) return;
    if (ok === false && text) {
      hint.textContent = text;
      hint.hidden = false;
    } else {
      hint.textContent = "";
      hint.hidden = true;
    }
  }

  function digitsOnly(value) {
    return String(value || "").replace(/\D/g, "");
  }

  function normalizePhoneDigits(raw) {
    var d = digitsOnly(raw);
    if (!d) return "";
    if (d[0] === "0") d = "38" + d;
    else if (d.indexOf("380") === 0) d = d;
    else if (d.indexOf("80") === 0) d = "3" + d;
    else if (d.indexOf("38") === 0) d = d;
    else d = "380" + d.replace(/^380/, "");
    if (d.indexOf("380") !== 0) {
      d = ("380" + d).slice(0, PHONE_MAX_DIGITS);
    }
    return d.slice(0, PHONE_MAX_DIGITS);
  }

  function formatPhoneMask(digits) {
    var d = normalizePhoneDigits(digits);
    // після 38 — до 10 цифр національного номера
    var rest = d.indexOf("38") === 0 ? d.slice(2) : d;
    var out = "+38";
    if (!rest.length) return out;
    out += " (";
    out += rest.slice(0, 3);
    if (rest.length < 3) return out;
    out += ")";
    if (rest.length === 3) return out;
    out += " " + rest.slice(3, 6);
    if (rest.length <= 6) return out;
    out += " - " + rest.slice(6, 8);
    if (rest.length <= 8) return out;
    out += " - " + rest.slice(8, 10);
    return out;
  }

  function isPhoneComplete(value) {
    var d = normalizePhoneDigits(value);
    return d.length === 12 && d.indexOf("380") === 0;
  }

  // Літери (кирилиця / латиниця) без \p{L} — сумісність з iOS Safari
  var NAME_PART =
    "[A-Za-zÀ-ÖØ-öø-ÿЀ-ӿҐґЄєІіЇї]";
  var NAME_RE = new RegExp(
    "^" + NAME_PART + "+(?:[-'’ʼ\\s]+" + NAME_PART + "+)*$"
  );

  function hasNameForbidden(value) {
    if (!value) return false;
    if (/\d/.test(value)) return true;
    return !NAME_RE.test(String(value).trim().replace(/\s+/g, " "));
  }

  function isNameValid(value) {
    var text = String(value || "").trim().replace(/\s+/g, " ");
    if (!text) return false;
    return NAME_RE.test(text);
  }

  function isEmailValid(value) {
    var text = String(value || "").trim();
    if (!text) return false;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(text);
  }

  function validateControl(form, control, opts) {
    opts = opts || {};
    var kind = control.getAttribute("data-validate");
    if (!kind) return true;
    var required = control.required || control.getAttribute("aria-required") === "true";
    var value = control.type === "checkbox" ? control.checked : String(control.value || "").trim();

    if (kind === "name") {
      if (!value) {
        if (opts.allowEmpty) {
          setState(control, null, "");
          return true;
        }
        setState(control, false, msg(form, "required", "Поле обов’язкове для заповнення"));
        return false;
      }
      if (hasNameForbidden(value) || !isNameValid(value)) {
        setState(
          control,
          false,
          msg(
            form,
            "name",
            "Ім’я не може містити цифри або спецсимволи. Будь ласка, використовуйте лише букви"
          )
        );
        return false;
      }
      setState(control, true, "");
      return true;
    }

    if (kind === "phone") {
      if (!value || value === "+38" || value === "+38 (") {
        if (opts.allowEmpty) {
          setState(control, null, "");
          return true;
        }
        setState(control, false, msg(form, "required", "Поле обов’язкове для заповнення"));
        return false;
      }
      if (!isPhoneComplete(value)) {
        if (opts.allowEmpty && !opts.force) {
          setState(control, null, "");
          return true;
        }
        setState(
          control,
          false,
          msg(
            form,
            "phone",
            "Введіть коректний номер мобільного телефону у форматі +380 (XX) XXX-XX-XX"
          )
        );
        return false;
      }
      setState(control, true, "");
      return true;
    }

    if (kind === "email") {
      if (!value) {
        if (!required || opts.allowEmpty) {
          setState(control, null, "");
          return true;
        }
        setState(control, false, msg(form, "required", "Поле обов’язкове для заповнення"));
        return false;
      }
      if (!isEmailValid(value)) {
        setState(control, false, msg(form, "email", "Введіть коректний e-mail"));
        return false;
      }
      setState(control, true, "");
      return true;
    }

    if (kind === "required") {
      if (!value) {
        if (opts.allowEmpty) {
          setState(control, null, "");
          return true;
        }
        setState(control, false, msg(form, "required", "Поле обов’язкове для заповнення"));
        return false;
      }
      setState(control, true, "");
      return true;
    }

    return true;
  }

  function validateForm(form) {
    var controls = form.querySelectorAll("[data-validate]");
    var firstInvalid = null;
    controls.forEach(function (control) {
      var ok = validateControl(form, control, { force: true });
      if (!ok && !firstInvalid) firstInvalid = control;
    });

    var consent = form.querySelector('input[name="consent"]');
    if (consent && consent.type === "checkbox" && !consent.checked) {
      setState(consent, false, msg(form, "required", "Поле обов’язкове для заповнення"));
      if (!firstInvalid) firstInvalid = consent;
    }

    var fulfillment = form.querySelectorAll('input[name="fulfillment"]');
    if (fulfillment.length) {
      var anyChecked = false;
      fulfillment.forEach(function (radio) {
        if (radio.checked) anyChecked = true;
      });
      if (!anyChecked) {
        var firstRadio = fulfillment[0];
        setState(firstRadio, false, msg(form, "required", "Поле обов’язкове для заповнення"));
        if (!firstInvalid) firstInvalid = firstRadio;
      }
    }

    if (firstInvalid) {
      try {
        firstInvalid.focus({ preventScroll: false });
      } catch (err) {
        firstInvalid.focus();
      }
      if (typeof firstInvalid.scrollIntoView === "function") {
        firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      return false;
    }
    return true;
  }

  function bindPhone(form, input) {
    if (input.getAttribute("data-phone-bound") === "1") return;
    input.setAttribute("data-phone-bound", "1");

    input.addEventListener("focus", function () {
      if (!digitsOnly(input.value)) {
        input.value = "+38 (";
      }
    });

    input.addEventListener("input", function () {
      var formatted = formatPhoneMask(input.value);
      input.value = formatted;
      if (isPhoneComplete(formatted)) {
        validateControl(form, input, { force: true });
      } else {
        setState(input, null, "");
      }
    });

    input.addEventListener("blur", function () {
      var d = normalizePhoneDigits(input.value);
      if (!d || d === "38") {
        input.value = "";
        validateControl(form, input, { force: true });
        return;
      }
      input.value = formatPhoneMask(d);
      validateControl(form, input, { force: true });
    });
  }

  function bindName(form, input) {
    if (input.getAttribute("data-name-bound") === "1") return;
    input.setAttribute("data-name-bound", "1");

    input.addEventListener("input", function () {
      var value = input.value;
      if (!value) {
        setState(input, null, "");
        return;
      }
      if (hasNameForbidden(value)) {
        validateControl(form, input, { force: true });
        return;
      }
      setState(input, null, "");
    });

    input.addEventListener("blur", function () {
      if (String(input.value || "").trim()) {
        validateControl(form, input, { force: true });
      }
    });
  }

  function bindGeneric(form, input) {
    if (input.getAttribute("data-generic-bound") === "1") return;
    input.setAttribute("data-generic-bound", "1");
    input.addEventListener("blur", function () {
      validateControl(form, input, { force: true });
    });
  }

  function bindForm(form) {
    if (!form || form.getAttribute("data-lead-validation") === "1") return;
    form.setAttribute("data-lead-validation", "1");
    form.setAttribute("novalidate", "novalidate");

    form.querySelectorAll('[data-validate="phone"]').forEach(function (el) {
      bindPhone(form, el);
    });
    form.querySelectorAll('[data-validate="name"]').forEach(function (el) {
      bindName(form, el);
    });
    form.querySelectorAll('[data-validate="email"], [data-validate="required"]').forEach(function (el) {
      bindGeneric(form, el);
    });

    form.addEventListener(
      "submit",
      function (event) {
        if (form.getAttribute("data-submitting") === "1") {
          event.preventDefault();
          event.stopPropagation();
          return;
        }
        if (!validateForm(form)) {
          event.preventDefault();
          event.stopPropagation();
          return;
        }
        // HTMX: lock у htmx:beforeRequest, щоб не заблокувати перший запит
        if (form.hasAttribute("hx-post") || form.hasAttribute("hx-get")) {
          return;
        }
        form.setAttribute("data-submitting", "1");
        form.querySelectorAll('button[type="submit"], input[type="submit"]').forEach(
          function (btn) {
            btn.disabled = true;
          }
        );
      },
      true
    );
  }

  function init(root) {
    var scope = root && root.querySelectorAll ? root : document;
    scope.querySelectorAll("form[data-qa='lead-form'], form[data-lead-form]").forEach(bindForm);
  }

  document.body.addEventListener("htmx:beforeRequest", function (event) {
    var el = event.target;
    var form = el && el.tagName === "FORM" ? el : el && el.closest ? el.closest("form") : null;
    if (!form || (form.getAttribute("data-qa") !== "lead-form" && !form.hasAttribute("data-lead-form"))) {
      return;
    }
    if (form.getAttribute("data-submitting") === "1") {
      event.preventDefault();
      return;
    }
    if (!validateForm(form)) {
      event.preventDefault();
      return;
    }
    form.setAttribute("data-submitting", "1");
    form.querySelectorAll('button[type="submit"], input[type="submit"]').forEach(function (btn) {
      btn.disabled = true;
    });
  });

  document.body.addEventListener("htmx:afterSwap", function (event) {
    init(event.target);
  });

  document.body.addEventListener("htmx:responseError", function (event) {
    var el = event.target;
    var form = el && el.tagName === "FORM" ? el : el && el.closest ? el.closest("form") : null;
    if (!form) return;
    form.removeAttribute("data-submitting");
    form.querySelectorAll('button[type="submit"], input[type="submit"]').forEach(function (btn) {
      btn.disabled = false;
    });
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      init(document);
    });
  } else {
    init(document);
  }
})();
