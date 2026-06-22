import frappe


MASTER_DOCTYPES = [
	"Jameah Ministry Code",
	"Jameah Branch",
	"Jameah Agency",
	"Jameah Deanery",
	"Jameah College",
	"Jameah Academic Department",
	"Jameah Facility",
]


PERMISSIONS = [
	{
		"role": "HR User",
		"permlevel": 0,
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 0,
		"print": 1,
		"email": 1,
		"report": 1,
		"export": 1,
		"share": 1,
	},
	{
		"role": "HR Manager",
		"permlevel": 0,
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"print": 1,
		"email": 1,
		"report": 1,
		"export": 1,
		"share": 1,
	},
	{
		"role": "System Manager",
		"permlevel": 0,
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"print": 1,
		"email": 1,
		"report": 1,
		"export": 1,
		"share": 1,
	},
]


def execute():
	for doctype_name in MASTER_DOCTYPES:
		if not frappe.db.exists("DocType", doctype_name):
			print(f"Skipped missing doctype: {doctype_name}")
			continue

		frappe.db.delete("Custom DocPerm", {"parent": doctype_name})
		for row in PERMISSIONS:
			_insert_custom_permission(doctype_name, row)
		frappe.clear_cache(doctype=doctype_name)
		print(f"Updated permissions: {doctype_name}")

	frappe.db.commit()
	print("Jameah master permissions applied.")


def _insert_custom_permission(doctype_name: str, permission: dict):
	doc = frappe.get_doc(
		{
			"doctype": "Custom DocPerm",
			"parent": doctype_name,
			"parenttype": "DocType",
			"parentfield": "permissions",
			**permission,
		}
	)
	doc.insert(ignore_permissions=True)
