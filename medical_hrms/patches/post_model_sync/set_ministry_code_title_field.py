import frappe


def execute():
	if frappe.db.exists("DocType", "Jameah Ministry Code"):
		frappe.db.set_value("DocType", "Jameah Ministry Code", "title_field", "name_english", update_modified=False)
		frappe.clear_cache(doctype="Jameah Ministry Code")
