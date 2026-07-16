import frappe
from pathlib import Path


def execute(file_path: str):
	"""Run full, idempotent normalization pipeline for ministry codes."""
	if not file_path or file_path.startswith("/path/to/"):
		default_path = Path(frappe.get_site_path("Ministry Code - (Translated).xlsx"))
		if default_path.exists():
			file_path = str(default_path)
		else:
			frappe.throw(
				"Please pass a real Excel path in file_path. "
				"Example: /home/abdul/frappe-bench/sites/site1.local/Ministry Code - (Translated).xlsx"
			)

	if not Path(file_path).exists():
		frappe.throw(f"Excel file not found: {file_path}")

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
