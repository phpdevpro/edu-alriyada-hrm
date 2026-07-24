import frappe


DUPLICATE_EMPLOYEE_FIELDS = [
	"custom_ministry_identity_type",
	"custom_ministry_birth_place",
	"custom_ministry_gender",
	"custom_ministry_nationality",
	"custom_ministry_marital_status",
	"custom_ministry_employment_status",
	"custom_ministry_institute",
	"custom_ministry_department",
]


def execute():
	deleted = 0
	for fieldname in DUPLICATE_EMPLOYEE_FIELDS:
		custom_field_name = f"Employee-{fieldname}"
		if not frappe.db.exists("Custom Field", custom_field_name):
			continue

		value_count = frappe.db.sql(
			f"""
			select count(*)
			from `tabEmployee`
			where `{fieldname}` is not null and `{fieldname}` != ''
			"""
		)[0][0]
		if value_count:
			print(f"Skipped {fieldname}: {value_count} records have data")
			continue

		# Avoid frappe.delete_doc here because it enqueues cleanup jobs and fails when Redis is down.
		# The fields are empty and only need to disappear from DocType metadata/form layout.
		frappe.db.delete("Custom Field", {"name": custom_field_name})
		deleted += 1

	frappe.clear_cache(doctype="Employee")
	frappe.db.commit()
	print(f"Deleted duplicate Employee custom fields: {deleted}")
