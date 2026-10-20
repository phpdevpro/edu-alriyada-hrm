# Copyright (c) 2026, Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class JameahCodeMap(Document):
	def validate(self):
		if self.jameah_code:
			category = frappe.db.get_value("Jameah Ministry Code", self.jameah_code, "code_category")
			if category != self.code_category:
				frappe.throw(
					_("{0} is a '{1}' code; this row needs a '{2}' code.").format(
						frappe.bold(self.jameah_code), category, self.code_category
					)
				)
		if self.status == "Verified" and not self.jameah_code:
			frappe.throw(_("Choose the Ministry code before marking the row Verified."))

		duplicate = frappe.db.exists(
			"Jameah Code Map",
			{
				"source_doctype": self.source_doctype,
				"source_value": self.source_value,
				"code_category": self.code_category,
				"name": ["!=", self.name],
			},
		)
		if duplicate:
			frappe.throw(_("A mapping for this value already exists: {0}").format(duplicate))

		# A person's decision is final: the automatic refresh never overwrites it.
		if not self.flags.from_refresh and not self.is_new():
			if self.has_value_changed("jameah_code") or self.has_value_changed("status"):
				self.method = "Manual"
