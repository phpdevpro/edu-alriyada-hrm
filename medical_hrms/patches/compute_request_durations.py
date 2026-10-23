"""Remote Work Request.duration and Permission Request.duration_hours were never calculated (always 0).
Fill them in for the requests already saved; new and edited requests calculate them on save."""
import frappe
from frappe.utils import cint, flt

from medical_hrms.medical_hrms.doctype.permission_request.permission_request import duration_hours
from medical_hrms.medical_hrms.doctype.remote_work_request.remote_work_request import request_days


def execute():
	# filter in Python: a SQL "in (0, NULL)" misses decimal zeros
	for row in frappe.get_all("Remote Work Request", fields=["name", "employee", "from_date", "to_date", "duration"]):
		if not cint(row.duration) and row.from_date and row.to_date and row.to_date >= row.from_date:
			frappe.db.set_value("Remote Work Request", row.name, "duration", request_days(row.employee, row.from_date, row.to_date), update_modified=False)
	for row in frappe.get_all("Permission Request", fields=["name", "from_time", "to_time", "duration_hours"]):
		if flt(row.duration_hours) or not (row.from_time and row.to_time):
			continue
		try:
			frappe.db.set_value("Permission Request", row.name, "duration_hours", duration_hours(row.from_time, row.to_time), update_modified=False)
		except frappe.ValidationError:
			frappe.clear_last_message()  # reversed times: leave as it is
