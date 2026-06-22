import frappe


DOCTYPE = "Assessment Group"


def execute():
	if not frappe.db.exists("Module Def", "Education"):
		frappe.get_doc({"doctype": "Module Def", "module_name": "Education"}).insert(ignore_permissions=True)

	if not frappe.db.exists("DocType", DOCTYPE):
		frappe.get_doc(
			{
				"doctype": "DocType",
				"name": DOCTYPE,
				"module": "Education",
				"custom": 1,
				"is_tree": 1,
				"autoname": "field:assessment_group_name",
				"title_field": "assessment_group_name",
				"nsm_parent_field": "parent_assessment_group",
				"fields": [
					{
						"fieldname": "assessment_group_name",
						"label": "Assessment Group Name",
						"fieldtype": "Data",
						"reqd": 1,
						"unique": 1,
					},
					{
						"fieldname": "parent_assessment_group",
						"label": "Parent Assessment Group",
						"fieldtype": "Link",
						"options": DOCTYPE,
					},
					{
						"fieldname": "is_group",
						"label": "Is Group",
						"fieldtype": "Check",
						"default": "0",
					},
				],
				"permissions": [
					{
						"role": "System Manager",
						"read": 1,
						"write": 1,
						"create": 1,
						"delete": 1,
					},
				],
			}
		).insert(ignore_permissions=True)

	frappe.clear_cache(doctype=DOCTYPE)
	frappe.db.commit()
	print(f"Ensured {DOCTYPE} DocType exists.")
