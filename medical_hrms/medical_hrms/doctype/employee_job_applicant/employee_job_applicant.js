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

// Fields the Employee form requires that the public application form does not ask for (or the
// applicant may have left empty): asked here so the new Employee can be saved without "Missing Fields".
// Keys are Employee fieldnames; create_employee_from_applicant accepts only these (EMPLOYEE_DETAIL_FIELDS).
function employee_detail_fields(frm, branches) {
	const d = frm.doc;
	// The Employee is created in the default company (job_application.get_default_company).
	const company = frappe.defaults.get_global_default("company") || frappe.defaults.get_user_default("Company");
	const ministry = (category) => () => ({ query: "medical_hrms.ministry_lookup_query.get_ministry_codes", filters: { code_category: category } });
	return [
		{ fieldtype: "Section Break", label: __("Employee Record") },
		{ fieldname: "department", fieldtype: "Link", options: "Department", label: __("Academic Department"), reqd: 1, default: d.department,
			get_query: () => ({ filters: { is_group: 0, ...(company ? { company } : {}) } }) },
		{ fieldname: "branch", fieldtype: "Link", options: "Branch", label: __("Geographical Work Location"), reqd: 1, default: branches.length === 1 ? branches[0].name : "" },
		...(d.gender ? [] : [{ fieldname: "gender", fieldtype: "Link", options: "Jameah Ministry Code", label: __("Gender"), reqd: 1, get_query: ministry("Gender"),
			description: __("Not given on the application.") }]),
		{ fieldtype: "Column Break" },
		{ fieldname: "custom_ministry_work_city", fieldtype: "Link", options: "Jameah Ministry Code", label: __("City (Geographical Place of Business)"), reqd: 1,
			default: d.custom_ministry_work_city, get_query: ministry("Coding cities and governora") },
		{ fieldname: "custom_ministry_job_rank", fieldtype: "Link", options: "Jameah Ministry Code", label: __("Job Rank"), reqd: 1,
			default: d.custom_ministry_job_rank, get_query: ministry("Job ranks") },
		...(d.date_of_birth ? [] : [{ fieldname: "date_of_birth", fieldtype: "Date", label: __("Date of Birth"), reqd: 1, description: __("Not given on the application.") }]),
		{ fieldtype: "Section Break", label: __("Login and Academic Records") },
	];
}

const EMPLOYEE_DETAIL_FIELDS = ["department", "branch", "gender", "custom_ministry_work_city", "custom_ministry_job_rank", "date_of_birth"];

function show_create_employee_dialog(frm) {
	frappe.db.get_list("Branch", { fields: ["name"], limit: 2 }).then(
		(branches) => open_create_employee_dialog(frm, branches || []),
		() => open_create_employee_dialog(frm, []),
	);
}

function open_create_employee_dialog(frm, branches) {
	const dialog = new frappe.ui.Dialog({
		title: __("Create Employee"),
		fields: [
			...employee_detail_fields(frm, branches),
			{
				fieldname: "edu_department",
				fieldtype: "Link",
				options: "Department Edu",
				label: __("Education Department"),
				description: __("Academic department in the Education system, for the Instructor / Head of Department record."),
				// The hire becomes Head of this department.
				reqd: ["Head of Department", "Department Head"].includes(frm.doc.role) ? 1 : 0,
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
				description: ["Instructor", "Academic Advisor"].includes(frm.doc.role)
					? __("Academic staff need an official college address (…@alriyada.edu.sa) for their Instructor record.")
					: "",
				depends_on: 'eval:doc.email_choice=="Company Email"',
				mandatory_depends_on: 'eval:doc.email_choice=="Company Email"',
			},
		],
		primary_action_label: __("Create Employee"),
		primary_action: (values) => {
			const company_email = values.email_choice === "Company Email" ? values.company_email : "";
			const employee_details = {};
			EMPLOYEE_DETAIL_FIELDS.forEach((f) => { if (values[f]) employee_details[f] = values[f]; });
			dialog.hide();
			frappe.call({
				method: "medical_hrms.medical_hrms.recruitment.job_application.create_employee_from_applicant",
				args: {
					job_applicant: frm.doc.name,
					department: values.edu_department,
					company_email: company_email,
					employee_details: employee_details,
				},
				freeze: true,
				callback: (r) => {
					const res = r.message || {};
					if (!res.employee) return;
					const created = [
						__("Employee {0}", [res.employee]),
						res.instructor && __("Instructor {0}", [res.instructor]),
						res.advisor && __("Academic Advisor {0}", [res.advisor]),
						res.hod_of && __("Head of {0}", [res.hod_of]),
					].filter(Boolean);
					frappe.show_alert({ message: __("Created: {0}", [created.join(", ")]), indicator: "green" }, 8);
					frappe.set_route("Form", "Employee", res.employee);
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
