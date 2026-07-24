import frappe


def execute():
	allowed = {
		"details_section", "applicant_name", "email_id", "phone_number", "status", "designation", "department",
		"application_category", "application_token", "date_of_birth", "gender", "nic_passport", "address",
		"emergency_contact_name", "emergency_contact_phone", "emergency_contact_relation", "cover_letter",
		"resume_attachment", "resume_link", "application_details_json", "academic_qualifications",
		"academic_work_experience", "previous_work_experience", "professional_certificates_training", "awards",
		"research_publications", "custom_first_name_en", "custom_second_name_en", "custom_third_name_en", "custom_last_name_en",
		"custom_first_name_ar", "custom_second_name_ar", "custom_third_name_ar", "custom_last_name_ar",
		"custom_identity_type", "custom_identity_number", "custom_identity_issue_date", "custom_identity_issue_place",
		"custom_original_home_id_number", "custom_ministry_place_of_birth", "custom_jameah_nationality",
		"custom_ministry_religion", "custom_is_special_needs", "custom_ministry_special_needs_type",
		"custom_work_telephone_number", "custom_work_telephone_extention_number",
	}
	for field in frappe.get_all("Custom Field", filters={"dt": "Employee Job Applicant"}, fields=["name", "fieldname"]):
		if field.fieldname not in allowed:
			frappe.db.set_value("Custom Field", field.name, "hidden", 1, update_modified=False)
	for field in frappe.get_all("DocField", filters={"parent": "Employee Job Applicant"}, fields=["name", "fieldname", "fieldtype"]):
		if field.fieldname not in allowed and field.fieldtype not in {"Section Break", "Column Break", "Tab Break", "HTML"}:
			frappe.db.set_value("DocField", field.name, "hidden", 1, update_modified=False)
	frappe.clear_cache(doctype="Employee Job Applicant")
