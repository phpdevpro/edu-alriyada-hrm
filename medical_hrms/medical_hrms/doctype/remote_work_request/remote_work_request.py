# Copyright (c) 2026, Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, getdate


class RemoteWorkRequest(Document):
	def validate(self):
		if not (self.from_date and self.to_date):
			return
		if getdate(self.to_date) < getdate(self.from_date):
			frappe.throw(_("To Date cannot be before From Date."))
		self.duration = request_days(self.employee, self.from_date, self.to_date)


def request_days(employee, from_date, to_date):
	"""Working days, as the monthly work-from-home limit counts them; calendar days when HR has not set up a
	holiday list covering the dates yet."""
	from medical_hrms.monthly_leave_policy import working_days

	try:
		return len(working_days(employee, from_date, to_date))
	except frappe.ValidationError:
		frappe.clear_last_message()
		return date_diff(to_date, from_date) + 1
