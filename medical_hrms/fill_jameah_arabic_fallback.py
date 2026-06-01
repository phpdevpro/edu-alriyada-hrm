import frappe


DOCTYPE = "Jameah Ministry Code"


def execute(batch_size: int = 500):
	rows = frappe.get_all(
		DOCTYPE,
		fields=["name", "ministry_code", "name_english", "name_arabic"],
		limit_page_length=0,
	)

	updated = 0
	batch_updates = 0
	for row in rows:
			english = (row.name_english or "").strip()
			arabic = (row.name_arabic or "").strip()
			code = (row.ministry_code or "").strip()

			if not english:
				continue
			if english.upper() == code.upper():
				continue
			if arabic:
				continue

			frappe.db.set_value(DOCTYPE, row.name, "name_arabic", english, update_modified=False)
			batch_updates += 1
			updated += 1

			if batch_updates >= int(batch_size):
				frappe.db.commit()
				print(f"Batch updated: {batch_updates}; total updated: {updated}")
				batch_updates = 0

	if batch_updates:
		frappe.db.commit()
		print(f"Batch updated: {batch_updates}; total updated: {updated}")

	frappe.clear_cache(doctype=DOCTYPE)
	print(f"Fallback fill complete. Updated rows: {updated}")
