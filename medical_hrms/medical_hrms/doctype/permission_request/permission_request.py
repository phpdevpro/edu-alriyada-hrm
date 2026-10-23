# Copyright (c) 2026, Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, to_timedelta


class PermissionRequest(Document):
	def validate(self):
		if self.from_time and self.to_time:
			self.duration_hours = duration_hours(self.from_time, self.to_time)


def duration_hours(from_time, to_time):
	start, end = to_timedelta(from_time), to_timedelta(to_time)
	if end <= start:
		frappe.throw(_("To Time must be after From Time."))
	return flt((end - start).total_seconds() / 3600, 2)
