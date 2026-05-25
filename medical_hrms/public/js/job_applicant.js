frappe.ui.form.on("Medical HRMS Job Applicant", {
	refresh(frm) {
		if (frm.doc.__islocal) {
			return;
		}

		if (frm.doc.status === "Pending") {
			frm.add_custom_button(__("Accept"), () => update_application_status(frm, "accept"));
			frm.add_custom_button(__("Reject"), () => update_application_status(frm, "reject"));
		}

		if (frm.doc.status === "Accepted") {
			frm.add_custom_button(__("Create Employee"), () => create_employee(frm), __("Actions"));
		}
	},
});

function update_application_status(frm, action) {
	const method =
		action === "accept"
			? "medical_hrms.medical_hrms.recruitment.job_application.accept_application"
			: "medical_hrms.medical_hrms.recruitment.job_application.reject_application";

	frappe.call({
		method,
		args: { job_applicant: frm.doc.name },
		callback: () => {
			frm.reload_doc();
		},
	});
}

function create_employee(frm) {
	frappe.call({
		method: "medical_hrms.medical_hrms.recruitment.job_application.create_employee_from_applicant",
		args: { job_applicant: frm.doc.name },
		callback: (r) => {
			if (r.message && r.message.employee) {
				frappe.set_route("Form", "Employee", r.message.employee);
			} else {
				frm.reload_doc();
			}
		},
	});
}
