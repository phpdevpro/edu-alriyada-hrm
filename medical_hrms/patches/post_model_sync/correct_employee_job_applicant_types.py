import frappe


def execute():
	types = {
		"custom_first_name_en": "Data", "custom_second_name_en": "Data", "custom_third_name_en": "Data", "custom_last_name_en": "Data",
		"custom_first_name_ar": "Data", "custom_second_name_ar": "Data", "custom_third_name_ar": "Data", "custom_last_name_ar": "Data",
		"custom_identity_type": "Data", "custom_identity_number": "Data", "custom_identity_issue_date": "Date", "custom_identity_issue_place": "Data",
		"custom_original_home_id_number": "Data", "custom_ministry_place_of_birth": "Data", "custom_jameah_nationality": "Data",
		"custom_ministry_religion": "Data", "custom_is_special_needs": "Check", "custom_ministry_special_needs_type": "Data",
		"custom_work_telephone_number": "Data", "custom_work_telephone_extention_number": "Data",
	}
	for fieldname, fieldtype in types.items():
		name = frappe.db.get_value("Custom Field", {"dt": "Employee Job Applicant", "fieldname": fieldname}, "name")
		if name:
			frappe.db.set_value("Custom Field", name, {"fieldtype": fieldtype, "options": ""}, update_modified=False)
	frappe.clear_cache(doctype="Employee Job Applicant")
