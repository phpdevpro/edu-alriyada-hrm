import frappe


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


def _ensure_base_custom_perms(doctype):
	if frappe.db.exists("Custom DocPerm", {"parent": doctype}):
		return
	rows = frappe.get_all("DocPerm", filters={"parent": doctype}, fields=["*"], limit_page_length=1000)
	for r in rows:
		d = frappe.new_doc("Custom DocPerm")
		d.update(r)
		d.insert(ignore_permissions=True)


def _ensure_row(doctype, role):
	name = frappe.db.get_value(
		"Custom DocPerm",
		{"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0},
		"name",
	)
	if name:
		return name

	d = frappe.new_doc("Custom DocPerm")
	d.parent = doctype
	d.parenttype = "DocType"
	d.parentfield = "permissions"
	d.role = role
	d.permlevel = 0
	d.if_owner = 0
	d.read = 1
	d.insert(ignore_permissions=True)
	return d.name


def execute():
	hr_user = {
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
	}
	hr_manager = {
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
	}

	updated = 0
	for doctype in TARGET_DOCTYPES:
		if not frappe.db.exists("DocType", doctype):
			continue
		meta = frappe.get_meta(doctype)
		if meta.issingle or meta.istable or meta.is_virtual:
			continue

		_ensure_base_custom_perms(doctype)

		u = _ensure_row(doctype, "HR User")
		m = _ensure_row(doctype, "HR Manager")

		mgr = dict(hr_manager)
		if meta.is_submittable:
			mgr.update({"submit": 1, "cancel": 1, "amend": 1})

		frappe.db.set_value("Custom DocPerm", u, hr_user, update_modified=False)
		frappe.db.set_value("Custom DocPerm", m, mgr, update_modified=False)
		updated += 1

	frappe.clear_cache()
	frappe.db.commit()
	print(f"Updated doctypes: {updated}")
