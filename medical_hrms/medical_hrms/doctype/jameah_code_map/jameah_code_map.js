// Copyright (c) 2026, Admin and contributors
// For license information, please see license.txt

frappe.ui.form.on("Jameah Code Map", {
	setup(frm) {
		frm.set_query("jameah_code", () => ({ filters: { code_category: frm.doc.code_category } }));
	},
	refresh(frm) {
		if (frm.doc.status !== "Verified") {
			frm.set_intro(__("Not sent to the Ministry until a code is chosen and the status is Verified."), "orange");
		}
	},
});
