import frappe
from frappe.permissions import add_permission, update_permission_property


ROLE_PERMS = {
	"HR User": {
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 0,
		"submit": 0,
		"cancel": 0,
		"amend": 0,
		"report": 1,
		"export": 1,
		"print": 1,
		"email": 1,
		"share": 1,
	},
	"HR Manager": {
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"submit": 0,
		"cancel": 0,
		"amend": 0,
		"report": 1,
		"export": 1,
		"print": 1,
		"email": 1,
		"share": 1,
	},
}


TARGET_DOCTYPES = [
	"Employee",
	"Department",
	"Designation",
	"Branch",
	"Company",
	"Employment Type",
	"Leave Application",
	"Attendance",
	"Expense Claim",
	"Travel Request",
	"Employee Separation",
	"Full and Final Statement",
	"Permission Request",
	"Remote Work Request",
	"Leave Plan Request",
	"Return from Leave Request",
	"Salary Certificate Request",
	"Pre Approved Overtime Request",
	"Employee Training Request",
	"Children Medical Allowance Request",
	"Company Car Request",
	"Contract Renewal Request",
	"Employee Data Update Request",
	"Employee Medical License",
	"Jameah Ministry Code",
	"Jameah Branch",
	"Jameah Agency",
	"Jameah Deanery",
	"Jameah College",
	"Jameah Academic Department",
	"Jameah Facility",
	"Page",
]


def _ensure_role_permission(doctype, role, is_submittable):
	if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0}):
		add_permission(doctype, role, 0, "read")

	perms = dict(ROLE_PERMS[role])
	if is_submittable and role == "HR Manager":
		perms.update({"submit": 1, "cancel": 1, "amend": 1})

	for ptype, val in perms.items():
		update_permission_property(doctype, role, 0, ptype, val)


def execute():
	doctypes = []
	for name in TARGET_DOCTYPES:
		if not frappe.db.exists("DocType", name):
			continue
		meta = frappe.get_meta(name)
		if meta.issingle or meta.istable or meta.is_virtual:
			continue
		doctypes.append({"name": name, "is_submittable": meta.is_submittable})

	updated = []
	for dt in doctypes:
		for role in ROLE_PERMS:
			_ensure_role_permission(dt["name"], role, dt["is_submittable"])
		updated.append(dt["name"])

	frappe.clear_cache()
	frappe.db.commit()

	print(f"Permissions ensured on doctypes: {len(updated)}")
	print("Includes core Page doctype read access for HR roles.")
