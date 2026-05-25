frappe.ui.form.on("Job Application Link", {
	refresh(frm) {
		if (frm.is_new()) {
			frm.add_custom_button(__("Save to Generate Link"), () => frm.save());
			return;
		}

		frm.add_custom_button(__("Generate Link"), () => {
			frm.call("generate_link").then((r) => {
				if (!r.message) {
					return;
				}

				const url = r.message.url || "";
				const safeUrl = frappe.utils.escape_html(url);
				frappe.msgprint({
					title: __("Job Application Link"),
					indicator: "green",
					message: __(
						`Link generated: <a href="${safeUrl}" target="_blank">${safeUrl}</a>`
					),
				});
				frm.reload_doc();
			});
		});
	},

	copy_url(frm) {
		if (!frm.doc.generated_url) {
			frappe.msgprint(__("Please generate a link first."));
			return;
		}
		frappe.utils.copy_to_clipboard(frm.doc.generated_url);
		frappe.show_alert({ message: __("URL copied to clipboard"), indicator: "green" });
	},
});
