# Copyright (c) 2026, Admin and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document


class JameahSettings(Document):
	def validate(self):
		# link_filters only guide the picker; enforce the category on save too.
		for df in self.meta.fields:
			if df.fieldtype != "Link" or df.options != "Jameah Ministry Code" or not self.get(df.fieldname):
				continue
			expected = json.loads(df.link_filters)[0][3]
			actual = frappe.db.get_value("Jameah Ministry Code", self.get(df.fieldname), "code_category")
			if actual != expected:
				frappe.throw(_("{0} must be a '{1}' code.").format(_(df.label), expected))
		if self.program_period is not None and self.program_period < 0:
			frappe.throw(_("Program Duration cannot be negative."))
		if self.file_base_url:
			self.file_base_url = self.file_base_url.strip().rstrip("/")
