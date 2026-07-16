import re

import frappe


DOCTYPE = "Jameah Ministry Code"


def _is_code_like(value: str) -> bool:
	if not value:
		return False
	v = re.sub(r"\s+", "", str(value).strip().upper())
	if not v or len(v) > 15:
		return False
	if not re.search(r"\d", v):
		return False
	return bool(re.fullmatch(r"[A-Z0-9][A-Z0-9\-/]{0,14}", v))


def _is_header_text(value: str) -> bool:
	if not value:
		return False
	v = re.sub(r"\s+", " ", str(value).strip().lower())
	blocked = {
		"the symbol",
		"symbol",
		"name",
		"name in english",
		"coding",
		"last modified date",
		"edited by",
		"الرمز",
		"الاسم",
	}
	return v in blocked


def _is_section_title(text: str) -> bool:
	if not text:
		return False
	v = str(text).strip()
	if len(v) < 8:
		return False
	if len(v.split()) >= 3:
		return True
	return False


def execute(dry_run: bool = True, delete_rows: bool = False):
	rows = frappe.get_all(
		DOCTYPE,
		fields=["name", "code_category", "ministry_code", "name_english", "name_arabic"],
		limit_page_length=0,
	)

	bad = []
	for row in rows:
		code = (row.ministry_code or "").strip()
		name_en = (row.name_english or "").strip()
		name_ar = (row.name_arabic or "").strip()

		reason = None
		if not _is_code_like(code):
			reason = "non_code_ministry_code"
		elif _is_header_text(code):
			reason = "header_token_as_code"
		elif _is_section_title(code):
			reason = "section_title_as_code"
		elif _is_header_text(name_en) or _is_header_text(name_ar):
			reason = "header_in_name_columns"

		if reason:
			bad.append((row.name, row.code_category, code, name_en, reason))

	print(f"Total rows: {len(rows)}")
	print(f"Suspicious rows: {len(bad)}")
	for item in bad[:200]:
		print(f"{item[0]} | {item[1]} | code={item[2]} | en={item[3]} | reason={item[4]}")

	if dry_run or not delete_rows:
		print("Dry run only. No records deleted.")
		return

	for name, *_ in bad:
		frappe.db.delete(DOCTYPE, {"name": name})

	frappe.db.commit()
	frappe.clear_cache(doctype=DOCTYPE)
	print(f"Deleted suspicious rows: {len(bad)}")
