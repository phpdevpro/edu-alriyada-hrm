import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def _filter_new_fields(custom_fields):
	filtered = {}
	for doctype, fields in custom_fields.items():
		new_fields = []
		for field in fields:
			fieldname = field.get("fieldname")
			if not fieldname:
				new_fields.append(field)
				continue

			existing_type = frappe.db.get_value(
				"Custom Field",
				{"dt": doctype, "fieldname": fieldname},
				"fieldtype",
			)
			if not existing_type:
				new_fields.append(field)
				continue
			if existing_type == field.get("fieldtype"):
				continue
			continue

		if new_fields:
			filtered[doctype] = new_fields
	return filtered
def execute():
	custom_fields = {
		"Employee": [
			{
				"fieldname": "custom_application_section",
				"fieldtype": "Section Break",
				"label": "Application Details",
				"insert_after": "relation",
			},
			{
				"fieldname": "custom_application_category",
				"fieldtype": "Select",
				"label": "Application Category",
				"options": "Academic Staff\nNon-Academic / Other Staff",
				"insert_after": "custom_application_section",
			},
			{
				"fieldname": "custom_expected_salary",
				"fieldtype": "Currency",
				"label": "Expected Salary",
				"options": "Company:company:default_currency",
				"insert_after": "custom_application_category",
			},
			{
				"fieldname": "custom_nic_passport",
				"fieldtype": "Data",
				"label": "NIC/Passport",
				"insert_after": "custom_expected_salary",
			},
			{
				"fieldname": "custom_resume_attachment",
				"fieldtype": "Attach",
				"label": "Resume Attachment",
				"insert_after": "custom_nic_passport",
			},
			{
				"fieldname": "custom_job_applicant",
				"fieldtype": "Link",
				"label": "Job Applicant",
				"options": "Medical HRMS Job Applicant",
				"insert_after": "custom_resume_attachment",
			},
			{
				"fieldname": "custom_profiles_section",
				"fieldtype": "Section Break",
				"label": "Applicant Profile",
				"insert_after": "custom_job_applicant",
			},
			{
				"fieldname": "custom_skills",
				"fieldtype": "Table",
				"label": "Skills",
				"options": "Medical HRMS Applicant Skill",
				"insert_after": "custom_profiles_section",
			},
			{
				"fieldname": "custom_training_courses",
				"fieldtype": "Table",
				"label": "Training Courses",
				"options": "Medical HRMS Training Course",
				"insert_after": "custom_skills",
			},
			{
				"fieldname": "custom_academic_certifications",
				"fieldtype": "Table",
				"label": "Academic Certifications",
				"options": "Medical HRMS Academic Certification",
				"insert_after": "custom_training_courses",
			},
			{
				"fieldname": "custom_teaching_experience",
				"fieldtype": "Table",
				"label": "Teaching Experience",
				"options": "Medical HRMS Teaching Experience",
				"insert_after": "custom_academic_certifications",
			},
			{
				"fieldname": "custom_research_publications",
				"fieldtype": "Table",
				"label": "Research Publications",
				"options": "Medical HRMS Research Publication",
				"insert_after": "custom_teaching_experience",
			},
			{
				"fieldname": "custom_professional_memberships",
				"fieldtype": "Table",
				"label": "Professional Memberships",
				"options": "Medical HRMS Professional Membership",
				"insert_after": "custom_research_publications",
			},
			{
				"fieldname": "custom_awards",
				"fieldtype": "Table",
				"label": "Awards",
				"options": "Medical HRMS Award",
				"insert_after": "custom_professional_memberships",
			},
		],
	}

	filtered_fields = _filter_new_fields(custom_fields)
	if filtered_fields:
		create_custom_fields(filtered_fields, update=False)

