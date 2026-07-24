import frappe


def execute():
	old_name = "Medical HRMS Job Applicant"
	new_name = "Employee Job Applicant"

	if frappe.db.exists("DocType", old_name) and not frappe.db.exists("DocType", new_name):
		if frappe.db.table_exists(new_name):
			# A previous partial migration may have created the destination table.
			# Only remove the old empty table; applicant records remain in the new table.
			old_table = frappe.db.escape(frappe.scrub(old_name), percent=False)
			if frappe.db.table_exists(old_name) and not frappe.db.sql(f"select name from `tab{frappe.scrub(old_name)}` limit 1"):
				frappe.db.sql(f"drop table `tab{old_table}`")
		else:
			frappe.rename_doc("DocType", old_name, new_name, force=True)
