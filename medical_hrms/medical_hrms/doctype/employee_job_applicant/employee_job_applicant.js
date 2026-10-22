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
						show_create_employee_dialog(frm);
					});
				}
			});
		}
	},
});

function show_create_employee_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Create Employee"),
		fields: [
			{
				fieldname: "department",
				fieldtype: "Link",
				options: "Department Edu",
				label: __("Department"),
			},
			{
				fieldname: "email_choice",
				fieldtype: "Select",
				label: __("Email to Use"),
				options: [
					{ label: __("Company Email"), value: "Company Email" },
					{ label: __("Use Personal Email") + ` (${frm.doc.email_id || ""})`, value: "Personal Email" },
				],
				default: "Company Email",
				reqd: 1,
				onchange: () => toggle_company_email_field(),
			},
			{
				fieldname: "company_email",
				fieldtype: "Data",
				options: "Email",
				label: __("Company Email"),
				depends_on: 'eval:doc.email_choice=="Company Email"',
				mandatory_depends_on: 'eval:doc.email_choice=="Company Email"',
			},
		],
		primary_action_label: __("Create Employee"),
		primary_action: (values) => {
			const company_email = values.email_choice === "Company Email" ? values.company_email : "";
			dialog.hide();
			frappe.call({
				method: "medical_hrms.medical_hrms.recruitment.job_application.create_employee_from_applicant",
				args: {
					job_applicant: frm.doc.name,
					department: values.department,
					company_email: company_email,
				},
				freeze: true,
				callback: (r) => {
					if (r.message && r.message.employee) {
						frappe.set_route("Form", "Employee", r.message.employee);
					}
				},
			});
		},
	});

	function toggle_company_email_field() {
		dialog.set_df_property("company_email", "reqd", dialog.get_value("email_choice") === "Company Email");
	}

	toggle_company_email_field();
	dialog.show();
}
