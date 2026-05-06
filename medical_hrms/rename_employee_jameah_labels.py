import frappe


def execute():
	label_by_field = {
		"custom_jameah_demographics": "Demographics",
		"custom_jameah_identity": "Identity Details",
		"custom_jameah_nationality": "Nationality",
		"custom_jameah_institute_details": "Institute Placement",
		"custom_jameah_branch": "Branch",
		"custom_jameah_agency": "Agency",
		"custom_jameah_deanery": "Deanery",
		"custom_jameah_college": "College",
		"custom_jameah_academic_department": "Academic Department",
		"custom_jameah_qualifications": "Qualifications",
		"custom_jameah_experience": "Work Experience",
		"custom_jameah_training": "Training Courses",
		"custom_jameah_publications": "Research Publications",
		"custom_jameah_awards": "Awards",
	}

	updated = 0
	for fieldname, label in label_by_field.items():
		custom_field_name = f"Employee-{fieldname}"
		if frappe.db.exists("Custom Field", custom_field_name):
			frappe.db.set_value("Custom Field", custom_field_name, "label", label, update_modified=False)
			updated += 1

	frappe.clear_cache(doctype="Employee")
	frappe.db.commit()
	print(f"Updated Employee custom field labels: {updated}")
