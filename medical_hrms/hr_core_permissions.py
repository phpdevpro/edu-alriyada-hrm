"""Core doctypes HR staff need that ERPNext/HRMS do not grant them (after_migrate).

- Company: HR forms and the Leave Control Panel filter by company. ERPNext
  only lets the Employee role read it, and HR accounts without their own
  Employee record do not have that role.
- Travel Request: HRMS grants only System Manager; the HR Dashboard and
  workspace send HR here to process employee travel.
- Instructor (read only): the HR Academic Schedules & Presence page filters
  by faculty member, and the Instructor data sheet is an HR process.
- Department Edu (read only): converting an academic applicant asks HR for
  the academic department the hire joins.
- Role (select only): HR picks the hired Role on a Job Application Link.
  Which roles may be hired is enforced by validate_hireable_role.

Rows are only added when missing, so later changes in Role Permissions
Manager are kept.
"""
import frappe
from frappe.permissions import add_permission, update_permission_property

GRANTS = {
	"Company": {
		"HR User": ("read", "report"),
		"HR Manager": ("read", "report"),
	},
	"Instructor": {
		"HR User": ("read", "select", "report"),
		"HR Manager": ("read", "select", "report", "export"),
	},
	"Department Edu": {
		"HR User": ("read", "select", "report"),
		"HR Manager": ("read", "select", "report"),
	},
	"Role": {
		"HR User": ("select",),
		"HR Manager": ("select",),
	},
	"Travel Request": {
		"HR User": ("read", "write", "create", "report", "print", "email"),
		"HR Manager": ("read", "write", "create", "submit", "cancel", "amend", "report", "export", "print", "email"),
	},
}


def execute():
	for doctype, roles in GRANTS.items():
		for role, ptypes in roles.items():
			if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0}):
				continue
			add_permission(doctype, role, 0, ptypes[0])
			for ptype in ptypes[1:]:
				update_permission_property(doctype, role, 0, ptype, 1, validate=False)
			if "read" not in ptypes:  # Custom DocPerm defaults read to 1
				update_permission_property(doctype, role, 0, "read", 0, validate=False)
	frappe.clear_cache()
