import frappe
from pathlib import Path


WORKBOOK_NAME = "Ministry Code - (Translated).xlsx"


def _resolve_file_path(file_path: str | None) -> str:
	candidates = []

	if file_path and not file_path.startswith("/path/to/"):
		candidates.append(Path(file_path))
		candidates.append(Path(frappe.get_site_path(Path(file_path).name)))
	else:
		candidates.append(Path(frappe.get_site_path(WORKBOOK_NAME)))

	try:
		candidates.append(Path(frappe.get_app_path("education")).parent / WORKBOOK_NAME)
	except Exception:
		pass

	for candidate in candidates:
		if candidate.exists():
			return str(candidate)

	checked_paths = "\n".join(str(candidate) for candidate in candidates)
	frappe.throw(f"Excel file not found. Checked:\n{checked_paths}")


def execute(file_path: str):
	"""Run full, idempotent normalization pipeline for ministry codes."""
	file_path = _resolve_file_path(file_path)
	print(f"Using workbook: {file_path}")

	print("Step 1/6: fix constraints")
	from medical_hrms.fix_jameah_ministry_code_constraints import execute as fix_constraints

	fix_constraints()

	print("Step 2/6: import workbook")
	from medical_hrms.import_ministry_excel_to_jameah_codes import execute as import_codes

	import_codes(file_path=file_path, dry_run=False)

	print("Step 3/6: cleanup suspicious rows")
	from medical_hrms.cleanup_jameah_ministry_codes import execute as cleanup

	cleanup(dry_run=False, delete_rows=True)

	print("Step 4/6: fix name mapping from workbook")
	from medical_hrms.fix_jameah_ministry_code_names import execute as fix_names

	fix_names(file_path=file_path, dry_run=False)

	print("Step 5/6: fix Included specializations duplicates")
	from medical_hrms.fix_included_specializations_duplicates import execute as fix_dupes

	fix_dupes(dry_run=False)

	print("Step 6/6: final audit")
	from medical_hrms.cleanup_jameah_ministry_codes import execute as audit

	audit(dry_run=True, delete_rows=False)
	frappe.db.commit()
	print("Normalization pipeline complete.")
