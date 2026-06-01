import frappe
from frappe.model.rename_doc import rename_doc


OLD_NAME = "Children Education Allowance Request"
NEW_NAME = "Children Medical Allowance Request"


def execute():
	if not frappe.db.exists("DocType", OLD_NAME):
		print(f"Skipped: {OLD_NAME} not found.")
		return

	if frappe.db.exists("DocType", NEW_NAME):
		print(f"Skipped: {NEW_NAME} already exists.")
		return

	rename_doc("DocType", OLD_NAME, NEW_NAME, force=True, ignore_permissions=True)
	frappe.clear_cache()
	frappe.db.commit()
	print(f"Renamed doctype: {OLD_NAME} -> {NEW_NAME}")
