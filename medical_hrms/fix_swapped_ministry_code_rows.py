import re

import frappe


DOCTYPE = "Jameah Ministry Code"


def _is_code_like(value: str) -> bool:
	v = re.sub(r"\s+", "", (value or "").strip().upper())
	if not v or len(v) > 15:
		return False
	return bool(re.fullmatch(r"[A-Z0-9][A-Z0-9\-/]{0,14}", v))


def _looks_like_phrase(value: str) -> bool:
	v = (value or "").strip()
	if not v:
		return False
	if re.search(r"\d", v):
		return False
	if not re.search(r"[A-Za-z]", v):
		return False
	return bool(re.fullmatch(r"[A-Za-z][A-Za-z\s&()\-/]{1,80}", v))


def _score(row):
	english = (row.name_english or "").strip()
	arabic = (row.name_arabic or "").strip()
	code = (row.ministry_code or "").strip()
	score = 0
	if english and english.upper() != code.upper():
		score += 2
	if arabic and arabic.upper() != code.upper() and arabic != english:
		score += 3
	if row.creation:
		score += 1
	return score


def execute(dry_run: bool = False):
	rows = frappe.get_all(
		DOCTYPE,
		fields=["name", "code_category", "ministry_code", "name_english", "name_arabic", "creation"],
		limit_page_length=0,
	)

	to_swap = []
	for row in rows:
		code = (row.ministry_code or "").strip()
		ar = (row.name_arabic or "").strip()
		en = (row.name_english or "").strip()

		if not _looks_like_phrase(code):
			continue
		if not re.fullmatch(r"[0-9]{2,15}", ar):
			continue
		to_swap.append(row)

	print(f"Rows detected for swap fix: {len(to_swap)}")
	for row in to_swap[:120]:
		print(f"swap {row.name} | {row.code_category} | code={row.ministry_code} -> {row.name_arabic}")

	if not dry_run:
		for row in to_swap:
			frappe.db.set_value(
				DOCTYPE,
				row.name,
				{
					"ministry_code": (row.name_arabic or "").strip(),
					"name_arabic": (row.name_english or "").strip(),
				},
				update_modified=False,
			)

	# Deduplicate per category+code after swap.
	all_rows = frappe.get_all(
		DOCTYPE,
		fields=["name", "code_category", "ministry_code", "name_english", "name_arabic", "creation"],
		order_by="code_category asc, ministry_code asc, creation asc",
		limit_page_length=0,
	)

	grouped = {}
	for row in all_rows:
		key = ((row.code_category or "").strip(), (row.ministry_code or "").strip())
		grouped.setdefault(key, []).append(row)

	to_delete = []
	for key, items in grouped.items():
		if len(items) <= 1:
			continue
		sorted_items = sorted(items, key=lambda r: (_score(r), r.creation), reverse=True)
		keep = sorted_items[0]
		for drop in sorted_items[1:]:
			to_delete.append((key[0], key[1], keep.name, drop.name))

	print(f"Duplicate rows to delete: {len(to_delete)}")
	for cat, code, keep_name, drop_name in to_delete[:120]:
		print(f"dupe {cat} | {code} | keep={keep_name} drop={drop_name}")

	if dry_run:
		print("Dry run only. No changes committed.")
		return

	for _, _, _, drop_name in to_delete:
		frappe.db.delete(DOCTYPE, {"name": drop_name})

	frappe.db.commit()
	frappe.clear_cache(doctype=DOCTYPE)
	print(f"Applied swap fix rows: {len(to_swap)}")
	print(f"Deleted duplicate rows: {len(to_delete)}")
