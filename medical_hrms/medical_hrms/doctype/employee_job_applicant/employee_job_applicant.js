// Copyright (c) 2026, Admin and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Job Applicant", {
	refresh(frm) {
		if (frm.doc.status === "Pending" && !frm.is_new()) {
			frm.add_custom_button(__("Accept"), () => {
				frappe.call({
					method: "medical_hrms.medical_hrms.recruitment.job_application.accept_application",
					args: { job_applicant: frm.doc.name },
					freeze: true,
					callback: () => frm.reload_doc(),
				});
			});
			frm.add_custom_button(__("Reject"), () => {
				frappe.call({
					method: "medical_hrms.medical_hrms.recruitment.job_application.reject_application",
					args: { job_applicant: frm.doc.name },
					freeze: true,
					callback: () => frm.reload_doc(),
				});
			});
		}

		if (frm.doc.status === "Accepted" && !frm.is_new()) {
			frappe.db.count("Employee", { filters: { custom_job_applicant: frm.doc.name } }).then((count) => {
				if (!count) {
					frm.add_custom_button(__("Create Employee"), () => {
						frappe.call({
							method: "medical_hrms.medical_hrms.recruitment.job_application.create_employee_from_applicant",
							args: { job_applicant: frm.doc.name },
							freeze: true,
							callback: (r) => {
								if (r.message && r.message.employee) {
									frappe.set_route("Form", "Employee", r.message.employee);
								}
							},
						});
					});
				}
			});
		}
	},
});
