"""Employees whose Ministry (Jameah) data is incomplete: one row per employee the Employee views send,
listing every Ministry-mandatory value that would be sent empty, named after the Employee form field
HR fills in (not the Ministry column name).

The gaps are read from the views themselves (medical_hrms.jameah.views), so the report shows exactly
what the Ministry would receive. Columns filled from Jameah Settings are left out: they are the same
for every employee and are listed on the Jameah Data Check page.
"""
import re
from collections import defaultdict

import frappe
from frappe import _

from medical_hrms.jameah import views as V
from medical_hrms.jameah.status import SPEC

SKIP_FIELDS = {"name", "parent", "parenttype", "parentfield", "modified"}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	gaps = missing_by_employee()
	rows = frappe.db.sql(
		"""SELECT e.name, e.employee_name, e.department, e.designation
		FROM `jameahEmployeePersonalInfo` v JOIN `tabEmployee` e ON e.name = v.EmployeeId
		WHERE (%(department)s = '' OR e.department = %(department)s) ORDER BY e.employee_name""",
		{"department": filters.department or ""}, as_dict=True)
	data = []
	for r in rows:
		items = gaps.get(r.name, [])
		if not items and not filters.show_complete:
			continue
		data.append({**r, "missing_count": len(items), "missing": "; ".join(items) or _("Complete")})
	data.sort(key=lambda r: -r["missing_count"])
	return columns(), data, None, None, summary(rows, data)


def columns():
	return [
		{"fieldname": "name", "label": _("Employee"), "fieldtype": "Link", "options": "Employee", "width": 140},
		{"fieldname": "employee_name", "label": _("Employee Name"), "fieldtype": "Data", "width": 200},
		{"fieldname": "department", "label": _("Academic Department"), "fieldtype": "Link", "options": "Department", "width": 170},
		{"fieldname": "designation", "label": _("Designation"), "fieldtype": "Link", "options": "Designation", "width": 150},
		{"fieldname": "missing_count", "label": _("Missing"), "fieldtype": "Int", "width": 90},
		{"fieldname": "missing", "label": _("Missing Ministry data (Employee form field)"), "fieldtype": "Data", "width": 600},
	]


def summary(rows, data):
	incomplete = sum(1 for r in data if r["missing_count"])
	return [
		{"value": len(rows), "label": _("Employees sent to the Ministry"), "datatype": "Int", "indicator": "Blue"},
		{"value": incomplete, "label": _("With missing data"), "datatype": "Int", "indicator": "Red" if incomplete else "Green"},
	]


def missing_by_employee():
	"""{employee: ["Identity Issue Date", "Academic Qualification (2 rows): Degree", ...]}"""
	out = defaultdict(list)
	for view in V.employee_views():
		mandatory = {s["column"] for s in SPEC.get(view.section, []) if s["mandatory"]}
		child = re.match(r"`tab([^`]+)` r JOIN", view.source)
		child_doctype = child.group(1) if child else None
		for column, sql, _type, _note in view.columns:
			if column not in mandatory or column in ("EmployeeId", "RecordId"):
				continue
			label = source_label(view, sql, child_doctype)
			if not label:
				continue  # filled from Jameah Settings
			for employee, n in frappe.db.sql(f"SELECT EmployeeId, COUNT(*) FROM `{view.name}` WHERE `{column}` IS NULL GROUP BY EmployeeId"):
				if child_doctype:
					section = _(child_doctype.replace("Jameah ", ""))
					label_text = f"{section} ({n} {_('rows') if n > 1 else _('row')}): {label}"
				else:
					label_text = label
				if label_text not in out[employee]:
					out[employee].append(label_text)
	return out


def source_label(view, sql, child_doctype):
	"""The form label of the field a view column is built from, or None for a Jameah Settings value."""
	expr = sql
	alias = re.search(r"(\w+)\.ministry_code", sql)
	if alias:
		a = alias.group(1)
		join = next((j for j in view.joins if re.search(rf"\b{a}\.name = ", j)), "")
		m = re.search(rf"\b{a}\.name = (\S+)", join)
		expr = m.group(1) if m else ""
		if expr.endswith("_m.jameah_code"):  # value resolved through the Code Map: the source is its source_value
			mj = next((j for j in view.joins if re.search(rf"\b{a}_m\.source_value = ", j)), "")
			m = re.search(rf"\b{a}_m\.source_value = (\S+)", mj)
			expr = m.group(1) if m else ""
	if expr.startswith("cfg.") or "cfg." in expr and not re.search(r"\b[er]\.\w+", expr):
		return None
	fields = [(t, f) for t, f in re.findall(r"\b([er])\.(\w+)", expr) if f not in SKIP_FIELDS]
	if not fields:
		return None
	table, fieldname = fields[0]
	doctype = child_doctype if table == "r" else "Employee"
	return _(frappe.get_meta(doctype).get_label(fieldname) or fieldname)
