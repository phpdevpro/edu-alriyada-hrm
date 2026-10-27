"""Linking an Employee on the Instructor or Academic Advisor form (education app) - B-26 / HR-48.

Both forms copied gender and department from the Employee, but into their own lists: Instructor.gender and
Academic Advisor.gender link to "Gender Edu" ("Male"), Instructor.department to "Department Edu"
("Internal Medicine"), while the Employee holds a Ministry code ("Gender::1") and a core Department
("Internal Medicine - ARC"). The copied value is not in the list, so saving failed. The copy is switched off
for those fields (Property Setters, setup below) and the matching value is filled in instead: on the form
when an Employee is picked (public/js/staff_employee_link.js) and on save when the field is still empty.
"""
import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from medical_hrms.medical_hrms.recruitment.job_application import (
	_resolve_department_edu_from_employee,
	_resolve_gender_from_ministry_code,
)

FIELDS = {"Instructor": ("gender", "department"), "Academic Advisor": ("gender",)}


def setup():
	for doctype, fields in FIELDS.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		for fieldname in fields:
			make_property_setter(doctype, fieldname, "fetch_from", "", "Small Text", validate_fields_for_doctype=False)
		frappe.clear_cache(doctype=doctype)


def matching_values(doctype, employee):
	"""{field: value} for the doctype's fields, only values that exist in its own lists."""
	row = frappe.db.get_value("Employee", employee, ["gender", "department"], as_dict=True)
	if not row:
		return {}
	found = {}
	gender = _resolve_gender_from_ministry_code(row.gender)
	if gender and frappe.db.exists("Gender Edu", gender):
		found["gender"] = gender
	department = _resolve_department_edu_from_employee(row.department)
	if department:
		found["department"] = department
	return {field: value for field, value in found.items() if field in FIELDS[doctype]}


@frappe.whitelist()
def values_from_employee(doctype, employee):
	if doctype not in FIELDS:
		frappe.throw(frappe._("Not available for {0}.").format(doctype), frappe.PermissionError)
	frappe.has_permission(doctype, "write", throw=True)
	if not frappe.has_permission("Employee", "read", doc=employee):
		return {}
	# The form can only set values from lists the user may read (Gender Edu is readable by System Managers
	# only); it clears the others and fill_from_employee fills them on save.
	meta = frappe.get_meta(doctype)
	readable = lambda field: any(frappe.has_permission(meta.get_field(field).options, ptype) for ptype in ("select", "read"))
	found = matching_values(doctype, employee)
	return {"values": {f: v for f, v in found.items() if readable(f)}, "filled_on_save": [f for f in found if not readable(f)]}


def fill_from_employee(doc, method=None):
	"""before_validate: fill the empty fields from the linked Employee."""
	if not doc.get("employee"):
		return
	for field, value in matching_values(doc.doctype, doc.employee).items():
		if not doc.get(field):
			doc.set(field, value)
