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
			"institute": 2,
			"graduation_year": 2,
		},
		"Jameah Work Experience": {
			"company": 3,
			"designation": 3,
			"start_date": 2,
			"end_date": 2,
		},
		"Jameah Training Course": {
			"course_name": 3,
			"provider": 3,
			"duration": 2,
			"date": 2,
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
