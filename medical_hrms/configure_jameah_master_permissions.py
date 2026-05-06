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

		dt = frappe.get_doc("DocType", doctype_name)
		dt.set("permissions", [])
		for row in PERMISSIONS:
			dt.append("permissions", row)
		dt.save(ignore_permissions=True)
		print(f"Updated permissions: {doctype_name}")

	frappe.db.commit()
	print("Jameah master permissions applied.")
