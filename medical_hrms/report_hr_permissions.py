import frappe


def execute():
	roles = ["HR User", "HR Manager"]
	doctypes = frappe.get_all("DocType", filters={"module": "Medical HRMS"}, pluck="name")

	rows = frappe.get_all(
		"DocPerm",
		filters={"role": ["in", roles], "parent": ["in", doctypes]},
		fields=[
			"parent",
			"role",
			"permlevel",
			"read",
			"write",
			"create",
			"delete",
			"submit",
			"cancel",
			"amend",
			"report",
			"export",
			"print",
			"email",
			"share",
		],
		order_by="parent asc, role asc, permlevel asc",
	)

	for r in rows:
		perms = []
		for key in [
			"read",
			"write",
			"create",
			"delete",
			"submit",
			"cancel",
			"amend",
			"report",
			"export",
			"print",
			"email",
			"share",
		]:
			if r.get(key):
				perms.append(key)

		print(f"{r.parent} | {r.role} | permlevel={r.permlevel} | {', '.join(perms)}")
