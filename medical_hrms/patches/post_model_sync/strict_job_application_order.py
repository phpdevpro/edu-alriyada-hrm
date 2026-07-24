import frappe


def execute():
	sequence = [
		"details_section", "custom_salutation", "custom_first_name", "custom_middle_name", "custom_last_name", "custom_employee_name", "gender", "date_of_birth",
		"custom_first_name_en", "custom_second_name_en", "custom_third_name_en", "custom_last_name_en", "custom_first_name_ar", "custom_second_name_ar", "custom_third_name_ar", "custom_last_name_ar",
		"custom_identity_type", "custom_identity_number", "custom_identity_issue_date", "custom_identity_issue_place", "custom_original_home_id_number", "custom_ministry_place_of_birth", "custom_jameah_nationality", "custom_ministry_religion", "custom_is_special_needs", "custom_ministry_special_needs_type", "custom_work_telephone_number", "custom_work_telephone_extention_number",
		"custom_cell_number", "custom_personal_email", "custom_company_email", "custom_prefered_contact_email", "custom_prefered_email", "custom_user_id", "custom_permanent_address", "custom_permanent_accommodation_type", "custom_current_address", "custom_current_accommodation_type",
		"custom_passport_number", "custom_date_of_issue", "custom_valid_upto", "custom_place_of_issue", "custom_marital_status", "custom_blood_group", "custom_family_background", "custom_health_details",
		"academic_qualifications", "academic_work_experience", "previous_work_experience", "professional_certificates_training", "awards", "research_publications",
		"cover_letter", "resume_attachment", "resume_link", "application_details_json", "status", "application_category", "application_token",
	]
	allowed = set(sequence)
	for field in frappe.get_all("DocField", filters={"parent": "Employee Job Applicant"}, fields=["name", "fieldname", "fieldtype"]):
		if field.fieldname not in allowed and field.fieldtype not in {"Section Break", "Column Break", "Tab Break", "HTML"}:
			frappe.db.set_value("DocField", field.name, "hidden", 1, update_modified=False)
	for field in frappe.get_all("Custom Field", filters={"dt": "Employee Job Applicant"}, fields=["name", "fieldname"]):
		if field.fieldname not in allowed:
			frappe.db.set_value("Custom Field", field.name, "hidden", 1, update_modified=False)
	for idx, fieldname in enumerate(sequence, start=1):
		custom = frappe.db.get_value("Custom Field", {"dt": "Employee Job Applicant", "fieldname": fieldname}, "name")
		if custom:
			frappe.db.set_value("Custom Field", custom, "idx", idx, update_modified=False)
		standard = frappe.db.get_value("DocField", {"parent": "Employee Job Applicant", "fieldname": fieldname}, "name")
		if standard:
			frappe.db.set_value("DocField", standard, "idx", idx, update_modified=False)
	frappe.clear_cache(doctype="Employee Job Applicant")
