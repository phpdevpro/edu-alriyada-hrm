import frappe


ALLOWED_ROLES = [
	"System Manager",
	"Education Manager",
	"Academic User",
	"Academics User",
	"Instructor",
]


def execute():
	if not frappe.db.exists("DocType", "Instructor"):
		print("Instructor DocType not found; skipped.")
		return

	dt = frappe.get_doc("DocType", "Instructor")
	dt.set("permissions", [])

	for role in ALLOWED_ROLES:
		if not frappe.db.exists("Role", role):
			continue

		row = {
			"role": role,
			"permlevel": 0,
			"read": 1,
			"report": 1,
			"print": 1,
		}

		if role in {"Education Manager", "System Manager"}:
			row.update({"write": 1, "create": 1, "delete": 1, "export": 1, "email": 1, "share": 1})
		elif role in {"Academic User", "Academics User"}:
			row.update({"write": 1, "create": 1, "export": 1, "email": 1})
		elif role == "Instructor":
			row.update({"write": 1})

		dt.append("permissions", row)

	dt.save(ignore_permissions=True)
	frappe.clear_cache(doctype="Instructor")
	frappe.db.commit()
	print("Instructor permissions updated for Academic handoff model.")
