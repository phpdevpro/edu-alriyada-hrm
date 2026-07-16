import time
import requests

import frappe


DOCTYPE = "Jameah Ministry Code"


def _translate_text(text: str, timeout_sec: int = 8) -> str:
	url = "https://translate.googleapis.com/translate_a/single"
	params = {
		"client": "gtx",
		"sl": "en",
		"tl": "ar",
		"dt": "t",
		"q": text,
	}
	resp = requests.get(url, params=params, timeout=timeout_sec)
	resp.raise_for_status()
	data = resp.json()
	parts = data[0] if data and isinstance(data, list) else []
	translated = "".join(part[0] for part in parts if part and part[0])
	return translated.strip()


def _needs_translation(row) -> bool:
	english = (row.name_english or "").strip()
	arabic = (row.name_arabic or "").strip()
	code = (row.ministry_code or "").strip()
	if not english:
		return False
	if english.lower() in {"name", "the name", "english name"}:
		return False
	if english.upper() == code.upper():
		return False
	if not arabic:
		return True
	return arabic == english


def execute(limit: int | None = None, dry_run: bool = False, request_timeout_sec: int = 8):
	rows = frappe.get_all(
		DOCTYPE,
		fields=["name", "ministry_code", "name_english", "name_arabic"],
		limit_page_length=0,
	)

	candidates = [r for r in rows if _needs_translation(r)]
	if limit:
		candidates = candidates[: int(limit)]

	print(f"Candidates for translation: {len(candidates)}")
	if dry_run:
		print("Dry run only. No updates applied.")
		return

	cache = {}
	updated = 0
	errors = 0
	timeouts = 0

	for idx, row in enumerate(candidates, start=1):
		english = (row.name_english or "").strip()
		try:
			arabic = cache.get(english)
			if not arabic:
				arabic = _translate_text(english, timeout_sec=int(request_timeout_sec))
				cache[english] = arabic
			if not arabic:
				continue
			frappe.db.set_value(DOCTYPE, row.name, "name_arabic", arabic, update_modified=False)
			updated += 1
		except requests.Timeout:
			timeouts += 1
		except Exception:
			errors += 1

		if idx % 200 == 0:
			frappe.db.commit()
			print(f"Processed {idx}/{len(candidates)}; updated={updated}; errors={errors}; timeouts={timeouts}")
			time.sleep(0.2)

	frappe.db.commit()
	frappe.clear_cache(doctype=DOCTYPE)
	print(f"Translation done. Updated={updated}; errors={errors}; timeouts={timeouts}")
