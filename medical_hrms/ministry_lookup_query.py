import frappe
from frappe import _
from frappe.utils import cint


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_ministry_codes(doctype, txt, searchfield, start, page_len, filters, **kwargs):
	category = filters.get("code_category") if isinstance(filters, dict) else None
	if not category:
		frappe.throw(_("Code category is required"))

	limit = min(max(cint(page_len), 250), 300)
	search_text = f"{txt}%"

	return frappe.db.sql(
		"""
		select name, name_english
		from `tabJameah Ministry Code`
		where code_category = %(category)s
			and (
				%(txt)s = '%%'
				or name_english like %(txt)s
				or ministry_code like %(txt)s
			)
		order by cast(ministry_code as unsigned), ministry_code, name_english
		limit %(start)s, %(limit)s
		""",
		{
			"category": category,
			"txt": search_text,
			"start": cint(start),
			"limit": limit,
		},
	)
