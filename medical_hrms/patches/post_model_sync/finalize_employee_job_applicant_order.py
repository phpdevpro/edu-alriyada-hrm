import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	for field in frappe.get_all("Custom Field", filters={"dt": "Employee Job Applicant"}, fields=["name"]):
		frappe.db.set_value("Custom Field", field.name, {"fieldtype": "Text", "options": ""}, update_modified=False)
	frappe.db.commit()
	correct_fields = [
		("custom_first_name_en", "First Name (English)"), ("custom_second_name_en", "Second Name (English)"),
		("custom_third_name_en", "Third Name (English)"), ("custom_last_name_en", "Fourth Name (English)"),
		("custom_first_name_ar", "First Name (Arabic)"), ("custom_second_name_ar", "Second Name (Arabic)"),
		("custom_third_name_ar", "Third Name (Arabic)"), ("custom_last_name_ar", "Fourth Name (Arabic)"),
		("custom_identity_type", "Identity Type"), ("custom_identity_number", "Identity Number"),
		("custom_identity_issue_date", "Identity Issue Date"), ("custom_identity_issue_place", "Identity Issue Place"),
		("custom_original_home_id_number", "Origin ID Number"), ("custom_ministry_place_of_birth", "Place of Birth"),
		("custom_jameah_nationality", "Nationality"), ("custom_ministry_religion", "Religion"),
		("custom_is_special_needs", "Is Special Needs"), ("custom_ministry_special_needs_type", "Special Needs Type"),
		("custom_work_telephone_number", "Work Telephone"), ("custom_work_telephone_extention_number", "Work Telephone Extension"),
	]
	create_custom_fields({"Employee Job Applicant": [{"fieldname": name, "fieldtype": "Text", "label": label} for name, label in correct_fields]}, update=True)

	for field in frappe.get_all("Custom Field", filters={"dt": "Employee Job Applicant"}, fields=["name", "fieldname"]):
		if field.fieldname.startswith("custom_custom_"):
			frappe.db.set_value("Custom Field", field.name, "hidden", 1, update_modified=False)

	ordered = [
		"custom_first_name_en", "custom_second_name_en", "custom_third_name_en", "custom_last_name_en",
		"custom_first_name_ar", "custom_second_name_ar", "custom_third_name_ar", "custom_last_name_ar",
		"custom_identity_type", "custom_identity_number", "custom_identity_issue_date", "custom_identity_issue_place",
		"custom_original_home_id_number", "custom_ministry_place_of_birth", "custom_jameah_nationality", "custom_ministry_religion",
		"custom_is_special_needs", "custom_ministry_special_needs_type", "custom_work_telephone_number", "custom_work_telephone_extention_number",
	]
	for field in frappe.get_all("Custom Field", filters={"dt": "Employee Job Applicant", "hidden": ["!=", 1]}, fields=["name", "fieldname"]):
		if field.fieldname not in ordered:
			ordered.append(field.fieldname)
	for idx, fieldname in enumerate(ordered, start=138):
		name = frappe.db.get_value("Custom Field", {"dt": "Employee Job Applicant", "fieldname": fieldname}, "name")
		if name:
			frappe.db.set_value("Custom Field", name, "idx", idx, update_modified=False)
	frappe.clear_cache(doctype="Employee Job Applicant")
