# Copyright (c) 2026, Admin and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from medical_hrms.medical_hrms.doctype.permission_request.permission_request import duration_hours


class TestPermissionRequest(FrappeTestCase):
	def test_duration_hours_from_the_times(self):
		self.assertEqual(duration_hours("10:15:00", "11:45:00"), 1.5)
		doc = frappe.get_doc({"doctype": "Permission Request", "date": "2026-10-21", "from_time": "08:00:00", "to_time": "10:30:00"})
		doc.validate()
		self.assertEqual(doc.duration_hours, 2.5)

	def test_to_time_must_be_after_from_time(self):
		self.assertRaises(frappe.ValidationError, duration_hours, "11:00:00", "10:00:00")
		self.assertRaises(frappe.ValidationError, duration_hours, "10:00:00", "10:00:00")
