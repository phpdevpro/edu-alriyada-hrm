// Copyright (c) 2026, Admin and contributors
// For license information, please see license.txt

const NON_ACADEMIC_CATEGORY = "Non-Academic / Other Staff";
const NON_ACADEMIC_ROLE = "Employee";

frappe.ui.form.on("Job Application Link", {
	refresh(frm) {
		toggle_role_for_category(frm);

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
	application_category(frm) {
		toggle_role_for_category(frm);
	},
});

function toggle_role_for_category(frm) {
	const is_non_academic = frm.doc.application_category === NON_ACADEMIC_CATEGORY;

	if (is_non_academic) {
		frm.set_value("role", NON_ACADEMIC_ROLE);
	}
	frm.set_df_property("role", "read_only", is_non_academic ? 1 : 0);
	frm.refresh_field("role");
}
