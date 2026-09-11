// Copyright (c) 2026, Admin and contributors
// For license information, please see license.txt

frappe.ui.form.on("Job Application Link", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Generate Link"), () => {
				frm.call("generate_link").then((r) => {
					frm.reload_doc();
					if (r.message && r.message.url) {
						frappe.msgprint({
							title: __("Application Link Generated"),
							message: `<a href="${r.message.url}" target="_blank">${r.message.url}</a>`,
							indicator: "green",
						});
					}
				});
			});
		}
	},
});
