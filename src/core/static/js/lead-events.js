/**
 * generate_lead у dataLayer лише після успішного збереження заявки.
 * Джерела: HX-Trigger leadSubmitted або data-* на сторінці подяки.
 * Не вішається на клік / submit.
 */
(function () {
  var pushed = false;

  function value(detail, key, fallbackKey) {
    if (!detail) return "";
    if (detail[key] != null && detail[key] !== "") return String(detail[key]);
    if (fallbackKey && detail[fallbackKey] != null) return String(detail[fallbackKey]);
    return "";
  }

  function pushLead(detail) {
    if (!detail) return;
    var formId = value(detail, "form_id");
    if (!formId || pushed) return;
    pushed = true;
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
      event: "generate_lead",
      form_id: formId,
      user_data: {
        email: value(detail, "email"),
        phone_number: value(detail, "phone_number", "phone"),
      },
    });
  }

  function fromDom() {
    var el = document.querySelector("[data-lead-event]");
    if (!el) return;
    pushLead({
      form_id: el.getAttribute("data-form-id") || "",
      email: el.getAttribute("data-email") || "",
      phone_number: el.getAttribute("data-phone") || "",
    });
    el.removeAttribute("data-lead-event");
  }

  document.addEventListener("leadSubmitted", function (evt) {
    pushLead(evt.detail || {});
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", fromDom);
  } else {
    fromDom();
  }
})();
