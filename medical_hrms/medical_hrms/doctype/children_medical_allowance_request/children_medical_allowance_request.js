// Copyright (c) 2026, Admin and contributors
// For license information, please see license.txt

frappe.ui.form.on("Children Medical Allowance Request", {
  refresh(frm) {
    const oldText = "Children Education Allowance Request";
    const newText = "Children Medical Allowance Request";

    frm.page.set_title(newText);
    frm.page.set_indicator(__(frm.doc.status || "Draft"), "blue");

    $(frm.page.wrapper)
      .find(".breadcrumb-item, .page-title, .title-text")
      .each(function () {
        const $el = $(this);
        const txt = $el.text();
        if (txt && txt.includes(oldText)) {
          $el.text(txt.replaceAll(oldText, newText));
        }
      });
  },
});
