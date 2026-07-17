
import frappe


def _apply_columns(doctype, config):
	updated = 0
	for fieldname, columns in config.items():
		if frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname}):
			frappe.db.set_value(
				"DocField",
				{"parent": doctype, "fieldname": fieldname},
				{"columns": columns, "in_list_view": 1},
				update_modified=False,
			)
			updated += 1
	return updated


def execute():
	settings = {
		"Jameah Academic Qualification": {
			"degree": 3,
			"specialization": 3,
			"minor": 2,
			"assessment_type": 2,
			"gpa": 2,
			"gpa_type": 2,
			"study_type": 2,
			"institute": 3,
			"faculty": 2,
			"qualification_date": 2,
			"graduation_year": 2,
			"city": 2,
			"country": 2,
		},
		"Jameah Academic Work Experience": {
			"is_latest_work_experience_record": 2,
			"current_academic_year_date": 2,
			"employment_status_code": 3,
			"profession": 3,
			"institute_code": 3,
			"location_code": 3,
			"section_code": 3,
			"employee_number": 2,
			"profession_rank_code": 3,
			"hiring_date": 2,
			"start_working_date": 2,
			"end_working_date": 2,
			"functional_tasks": 3,
			"accommodation_code": 3,
		},
		"Jameah Previous Work Experience": {
			"profession": 3,
			"organization_name": 3,
			"city": 2,
			"country": 2,
			"department": 3,
			"section": 2,
			"start_work_date": 2,
			"end_work_date": 2,
			"functional_tasks": 3,
		},
		"Jameah Professional Certificates and Training Courses": {
			"course_name": 3,
			"course_type": 2,
			"issuer": 3,
			"course_date": 2,
			"course_period": 2,
			"course_city": 2,
			"course_country": 2,
		},
		"Jameah Research Publication": {
			"title": 3,
			"journal": 3,
			"publication_date": 2,
			"link": 2,
		},
		"Jameah Award": {
			"award_name": 4,
			"organization": 4,
			"date": 2,
		},
	}

	total = 0
	for doctype, config in settings.items():
		total += _apply_columns(doctype, config)
		frappe.clear_cache(doctype=doctype)

	frappe.db.commit()
	print(f"Updated child table column widths: {total}")
