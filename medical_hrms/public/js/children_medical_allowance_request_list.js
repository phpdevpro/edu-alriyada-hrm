frappe.listview_settings["Children Medical Allowance Request"] = {
  onload(listview) {
    const newTitle = "Children Medical Allowance Request";

    listview.page.set_title(newTitle);
    document.title = `${newTitle} - ${frappe.boot?.sitename || ""}`;

    const rewriteLabels = () => {
      const oldText = "Children Education Allowance Request";
      const newText = "Children Medical Allowance Request";

      $(listview.page.wrapper)
        .find(".page-title, .level-item, .list-empty-state p, .list-empty-state button, .btn-primary, .breadcrumb-item, .list-row-col")
        .each(function () {
          const $el = $(this);
          const txt = $el.text();
          if (txt && txt.includes(oldText)) {
            $el.text(txt.replaceAll(oldText, newText));
          }
        });

      if (listview.page.btn_primary) {
        const txt = listview.page.btn_primary.text();
        if (txt && txt.includes(oldText)) {
          listview.page.btn_primary.text(txt.replaceAll(oldText, newText));
        }
      }
    };

    rewriteLabels();
    setTimeout(rewriteLabels, 200);
    setTimeout(rewriteLabels, 800);
    const observer = new MutationObserver(rewriteLabels);
    observer.observe(listview.page.wrapper.get(0), { childList: true, subtree: true });
  },
};
