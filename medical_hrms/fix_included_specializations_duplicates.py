import frappe


DOCTYPE = "Jameah Ministry Code"
CATEGORY = "Included specializations - 39"


def _score(row):
	english = (row.name_english or "").strip()
	arabic = (row.name_arabic or "").strip()
	ministry_code = (row.ministry_code or "").strip()
	score = 0
	if english and english.upper() != ministry_code.upper():
		score += 2
	if arabic and arabic != english and arabic.upper() != ministry_code.upper():
		score += 3
	if row.creation:
		score += 1
	return score


def execute(dry_run: bool = False):
	rows = frappe.get_all(
		DOCTYPE,
		filters={"code_category": CATEGORY},
		fields=["name", "ministry_code", "name_english", "name_arabic", "creation"],
		order_by="ministry_code asc, creation asc",
		limit_page_length=0,
	)

	by_code = {}
	for row in rows:
		by_code.setdefault(row.ministry_code, []).append(row)

	to_delete = []
	for code, items in by_code.items():
		if len(items) <= 1:
			continue
		sorted_items = sorted(items, key=lambda r: (_score(r), r.creation), reverse=True)
		keep = sorted_items[0]
		for drop in sorted_items[1:]:
			to_delete.append((code, keep.name, drop.name))

	print(f"Duplicate code groups: {sum(1 for v in by_code.values() if len(v) > 1)}")
	print(f"Rows to delete: {len(to_delete)}")
	for code, keep_name, drop_name in to_delete[:120]:
		print(f"code={code} keep={keep_name} drop={drop_name}")

	if dry_run:
		print("Dry run only. No records deleted.")
		return

	for _, _, drop_name in to_delete:
		frappe.db.delete(DOCTYPE, {"name": drop_name})

	frappe.db.commit()
	frappe.clear_cache(doctype=DOCTYPE)
	print(f"Deleted duplicate rows: {len(to_delete)}")
