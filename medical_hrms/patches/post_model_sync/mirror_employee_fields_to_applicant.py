import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	fields = []
	for field in frappe.get_meta("Employee").fields:
		if field.fieldtype in ("Table", "Table MultiSelect", "Section Break", "Column Break", "Tab Break", "HTML"):
			continue
		if field.fieldname in {"name", "owner", "creation", "modified", "modified_by", "docstatus"}:
			continue
		if frappe.db.exists("DocField", {"parent": "Employee Job Applicant", "fieldname": field.fieldname}):
			continue
		if frappe.db.exists("Custom Field", {"dt": "Employee Job Applicant", "fieldname": "custom_" + field.fieldname}):
			continue
		spec = {"fieldname": "custom_" + field.fieldname, "fieldtype": field.fieldtype, "label": field.label or field.fieldname}
		if field.options:
			spec["options"] = field.options
		fields.append(spec)
	if fields:
		create_custom_fields({"Employee Job Applicant": fields}, update=True)
