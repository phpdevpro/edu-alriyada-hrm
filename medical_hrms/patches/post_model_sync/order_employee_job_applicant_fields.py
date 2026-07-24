import frappe


def execute():
	sequence = [
		"applicant_name", "email_id", "phone_number", "status", "designation", "department",
		"application_category", "application_token", "date_of_birth", "gender", "nic_passport", "address",
		"custom_first_name_en", "custom_second_name_en", "custom_third_name_en", "custom_last_name_en",
		"custom_first_name_ar", "custom_second_name_ar", "custom_third_name_ar", "custom_last_name_ar",
		"custom_identity_type", "custom_identity_number", "custom_identity_issue_date", "custom_identity_issue_place",
		"custom_original_home_id_number", "custom_ministry_place_of_birth", "custom_jameah_nationality",
		"custom_ministry_religion", "custom_is_special_needs", "custom_ministry_special_needs_type",
		"custom_work_telephone_number", "custom_work_telephone_extention_number", "personal_email", "cell_number",
		"company_email", "prefered_contact_email", "prefered_email", "user_id", "permanent_address",
		"permanent_accommodation_type", "current_address", "current_accommodation_type", "passport_number",
		"date_of_issue", "valid_upto", "place_of_issue", "marital_status", "blood_group", "family_background",
		"health_details", "academic_qualifications", "academic_work_experience", "previous_work_experience",
		"professional_certificates_training", "awards", "research_publications", "cover_letter", "resume_attachment",
		"resume_link", "application_details_json",
	]
	for idx, fieldname in enumerate(sequence, start=1):
		custom = frappe.db.get_value("Custom Field", {"dt": "Employee Job Applicant", "fieldname": fieldname}, "name")
		if custom:
			frappe.db.set_value("Custom Field", custom, "idx", idx, update_modified=False)
		elif frappe.db.exists("DocField", {"parent": "Employee Job Applicant", "fieldname": fieldname}):
			frappe.db.set_value("DocField", {"parent": "Employee Job Applicant", "fieldname": fieldname}, "idx", idx, update_modified=False)
	frappe.clear_cache(doctype="Employee Job Applicant")
