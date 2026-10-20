"""Rename "Return from Leave Request" to "Leave Return Request".

Frappe's list queries reject any field containing " from " (an SQL-injection
guard), and table-qualified fields such as `tabReturn from Leave Request`.name
trip it, so the HR list view and counts for this DocType failed."""
import frappe

OLD, NEW = "Return from Leave Request", "Leave Return Request"


def execute():
	if frappe.db.exists("DocType", OLD) and not frappe.db.exists("DocType", NEW):
		frappe.rename_doc("DocType", OLD, NEW, force=True)
