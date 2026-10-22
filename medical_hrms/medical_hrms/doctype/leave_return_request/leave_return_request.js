// Copyright (c) 2026, Admin and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Return Request", {
	setup(frm) {
		// Only the employee's own approved, submitted leave can be returned from.
		frm.set_query("leave_application", () => ({
			filters: { employee: frm.doc.employee, status: "Approved", docstatus: 1 },
		}));
	},
	refresh(frm) {
		if (frm.doc.is_sick_leave && frm.doc.status === "Pending Occupational Health") {
			frm.dashboard.set_headline(__("After sick leave: record the occupational health clearance, then set Status to Completed."));
		}
	},
});
