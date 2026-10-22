// Copyright (c) 2026, Admin and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Plan Request", {
	refresh(frm) {
		if (frm.doc.status === "Approved" && !frm.doc.leave_application) {
			frm.dashboard.set_headline(__("Approved plan. The employee applies for this leave from the Employee Portal (Apply now) when the time comes."));
		}
		if (frm.doc.leave_application) {
			frm.add_custom_button(__("Open Leave Application"), () => frappe.set_route("Form", "Leave Application", frm.doc.leave_application));
		}
	},
});
