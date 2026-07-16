import frappe


DOCTYPE = "Jameah Ministry Code"


def execute():
	if not frappe.db.exists("DocType", DOCTYPE):
		print(f"Skipped: {DOCTYPE} not found")
		return

	frappe.db.set_value("DocType", DOCTYPE, "autoname", "hash")

	if frappe.db.exists("DocField", {"parent": DOCTYPE, "fieldname": "ministry_code"}):
		frappe.db.set_value(
			"DocField",
			{"parent": DOCTYPE, "fieldname": "ministry_code"},
			"unique",
			0,
			update_modified=False,
		)

	# Drop any unique index on ministry_code.
	unique_indexes = frappe.db.sql(
		"""
		select index_name
		from information_schema.statistics
		where table_schema = database()
		  and table_name = %s
		  and column_name = 'ministry_code'
		  and non_unique = 0
		""",
		(f"tab{DOCTYPE}",),
		as_dict=True,
	)
	for row in unique_indexes:
		if row.index_name == "PRIMARY":
			continue
		frappe.db.sql(f"ALTER TABLE `tab{DOCTYPE}` DROP INDEX `{row.index_name}`")

	frappe.clear_cache(doctype=DOCTYPE)
	frappe.db.commit()
	print(f"Updated {DOCTYPE} constraints")
