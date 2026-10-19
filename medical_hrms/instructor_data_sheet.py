"""HR spreadsheet to collect the Ministry data existing Instructors are missing.

Active Instructors without an Employee can't be linked to HR because they
have no nationality / ID number (see link_existing_instructors). HR fills
these in one sheet, the import checks every row, and only then creates the
Employees. Files are named <date>_<time>_Instructor-Ministry-Data_<step>.xlsx and
saved as private Files (Desk > File list).

1. Export the sheet for HR:
    bench --site <site> execute medical_hrms.instructor_data_sheet.export_sheet
2. HR fills it in and uploads it (Desk > File > upload).
3. Check it - nothing is saved, a result sheet lists each row's status:
    bench --site <site> execute medical_hrms.instructor_data_sheet.import_sheet --kwargs "{'file': '/private/files/<name>.xlsx'}"
4. Import for real once the check is clean:
    ... import_sheet --kwargs "{'file': '/private/files/<name>.xlsx', 'commit': 1}"
"""
import io
import re

import frappe
from frappe.utils import cstr, now_datetime

from medical_hrms.link_existing_instructors import try_link
from medical_hrms.medical_hrms.recruitment.job_application import get_default_company

FILE_PREFIX = "Instructor-Ministry-Data"
SHEET = "Instructors"
SUGGESTED_FILL = "FFF2CC"  # yellow: pre-filled guess HR must confirm
INPUT_FILL = "E2EFDA"  # green: HR fills these
LOCKED_FILL = "EDEDED"  # grey: do not edit

# (key, header, width, kind). Headers are bilingual; the import matches on
# the key in brackets so HR can't break it by retyping a header.
COLUMNS = [
	("instructor", "Instructor ID / رقم المحاضر [instructor]", 16, "locked"),
	("name", "Name / الاسم [name]", 30, "locked"),
	("arabic_name", "Arabic Name / الاسم بالعربي [arabic_name]", 26, "locked"),
	("email", "Email / البريد [email]", 34, "locked"),
	("id_type", "ID Type / نوع الهوية [id_type]", 20, "locked"),
	("gender", "Gender / الجنس [gender]", 14, "input"),
	("nationality", "Nationality / الجنسية [nationality]", 22, "input"),
	("national_id", "Saudi National ID (10 digits) / رقم الهوية الوطنية [national_id]", 24, "input"),
	("home_id", "Non-Saudi: ID in Home Country / رقم الهوية في بلد الأصل [home_id]", 26, "input"),
	("department", "Department / القسم [department]", 30, "input"),
	("employee_number", "Employee Number / الرقم الوظيفي [employee_number]", 18, "input"),
]
TEXT_COLUMNS = {"national_id", "home_id", "employee_number"}

INSTRUCTIONS = [
	"Instructor Ministry Data / بيانات المحاضرين للوزارة",
	"",
	"Why: these Instructors have no Employee record, so HR can't manage them and they can't use HR self-service.",
	"The Ministry requires a nationality and an ID number for every Employee.",
	"",
	"How to fill in the 'Instructors' sheet:",
	"  • Grey columns: do not change.",
	"  • Green columns: please fill in.",
	"  • Yellow cells: a suggestion from the ID type (e.g. Saudi National ID → Saudi Arabian). Please check.",
	"  • Saudi employees: fill 'Saudi National ID' (10 digits).",
	"  • Non-Saudi employees: fill 'ID in Home Country' instead.",
	"  • Use the dropdowns where available. A nationality not in the list can be typed;",
	"    the import will report it if it is not in the Ministry codes yet.",
	"  • Leave a row blank if you don't have the data yet - it will simply be skipped.",
	"",
	"Then upload the file in Desk (File list) and send the file name to the system administrator.",
]


def _nationalities():
	return frappe.get_all(
		"Jameah Ministry Code",
		filters={"code_category": "Nationality"},
		fields=["name", "ministry_code", "name_english", "name_arabic"],
		order_by="name_english",
	)


def _is_saudi(code):
	row = frappe.db.get_value("Jameah Ministry Code", code, ["ministry_code", "name_english"], as_dict=True)
	return bool(row) and (row.ministry_code in {"101", "N-SA"} or (row.name_english or "").lower().startswith("saudi"))


def _dated_name(step):
	"""e.g. 2026-10-19_14-05_Instructor-Ministry-Data_1-For-HR.xlsx: sorts by
	date and time, and same-day reruns never collide."""
	return f"{now_datetime():%Y-%m-%d_%H-%M}_{FILE_PREFIX}_{step}.xlsx"


def _save_file(file_name, workbook):
	buffer = io.BytesIO()
	workbook.save(buffer)
	file_doc = frappe.get_doc(
		{"doctype": "File", "file_name": file_name, "is_private": 1, "content": buffer.getvalue()}
	).insert(ignore_permissions=True)
	frappe.db.commit()
	print(f"Saved {file_doc.file_name}\n  Desk: /app/file/{file_doc.name}\n  Path: {file_doc.get_full_path()}")
	return file_doc.file_url


def _style_header(sheet, fills):
	from openpyxl.styles import Alignment, Font, PatternFill

	for col, (key, header, width, kind) in enumerate(COLUMNS, start=1):
		cell = sheet.cell(row=1, column=col, value=header)
		cell.font = Font(bold=True)
		cell.alignment = Alignment(wrap_text=True, vertical="center")
		cell.fill = PatternFill("solid", fgColor=fills[kind])
		sheet.column_dimensions[cell.column_letter].width = width
	sheet.row_dimensions[1].height = 48
	sheet.freeze_panes = "B2"


def export_sheet():
	from openpyxl import Workbook
	from openpyxl.styles import PatternFill
	from openpyxl.worksheet.datavalidation import DataValidation

	instructors = frappe.get_all(
		"Instructor",
		filters={"status": "Active", "employee": ["is", "not set"]},
		fields=["name", "instructor_name", "arabic_name", "email", "instructor_id_type", "gender",
			"custom_jameah_nationality", "custom_identity_number", "department", "employee_no"],
		order_by="instructor_name",
	)
	nationalities = _nationalities()
	saudi = next((n for n in nationalities if _is_saudi(n.name)), None)
	code_to_label = {n.name: n.name_english for n in nationalities}

	workbook = Workbook()
	guide = workbook.active
	guide.title = "Instructions"
	for row, line in enumerate(INSTRUCTIONS, start=1):
		guide.cell(row=row, column=1, value=line)
	guide.column_dimensions["A"].width = 110

	sheet = workbook.create_sheet(SHEET)
	fills = {"locked": LOCKED_FILL, "input": INPUT_FILL}
	_style_header(sheet, fills)
	keys = [c[0] for c in COLUMNS]
	suggested = PatternFill("solid", fgColor=SUGGESTED_FILL)

	for row, ins in enumerate(instructors, start=2):
		nationality = code_to_label.get(ins.custom_jameah_nationality)
		suggested_nationality = None
		if not nationality and saudi and ins.instructor_id_type == "Saudi National ID":
			suggested_nationality = saudi.name_english
		values = {
			"instructor": ins.name, "name": ins.instructor_name, "arabic_name": ins.arabic_name,
			"email": ins.email, "id_type": ins.instructor_id_type, "gender": ins.gender,
			"nationality": nationality or suggested_nationality, "national_id": ins.custom_identity_number,
			"department": ins.department, "employee_number": ins.employee_no,
		}
		for col, key in enumerate(keys, start=1):
			cell = sheet.cell(row=row, column=col, value=values.get(key) or None)
			if key in TEXT_COLUMNS:
				cell.number_format = "@"  # keep leading zeros / long IDs as text
		if suggested_nationality:
			sheet.cell(row=row, column=keys.index("nationality") + 1).fill = suggested

	# Dropdown sources on a hidden sheet.
	lists = workbook.create_sheet("Lists")
	lists.sheet_state = "hidden"
	sources = {
		"gender": frappe.get_all("Gender Edu", pluck="name", order_by="name"),
		"nationality": [n.name_english for n in nationalities],
		"department": frappe.get_all("Department Edu", pluck="name", order_by="name"),
	}
	last = max(len(instructors) + 1, 2)
	for list_col, (key, options) in enumerate(sources.items(), start=1):
		for i, option in enumerate(options, start=1):
			lists.cell(row=i, column=list_col, value=option)
		letter = lists.cell(row=1, column=list_col).column_letter
		target = sheet.cell(row=2, column=keys.index(key) + 1).column_letter
		validation = DataValidation(
			type="list", formula1=f"=Lists!${letter}$1:${letter}${max(len(options), 1)}",
			# Nationalities not seeded yet may be typed; the import reports them.
			showErrorMessage=key != "nationality",
		)
		sheet.add_data_validation(validation)
		validation.add(f"{target}2:{target}{last}")

	file_url = _save_file(_dated_name("1-For-HR"), workbook)
	print(f"{len(instructors)} Instructors listed; {sum(1 for _ in instructors if _.instructor_id_type == 'Saudi National ID')} with a suggested nationality.")
	return file_url


def _read_rows(file):
	from openpyxl import load_workbook

	# An uploaded File's URL (/private/files/...), or a path on the server.
	is_file_url = file.startswith(("/private/files/", "/files/"))
	path = frappe.get_doc("File", {"file_url": file}).get_full_path() if is_file_url else file
	sheet = load_workbook(path, data_only=True)[SHEET]
	header_keys = []
	for cell in sheet[1]:
		match = re.search(r"\[(\w+)\]\s*$", cstr(cell.value))
		header_keys.append(match.group(1) if match else None)
	for excel_row, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
		values = {}
		for key, value in zip(header_keys, row):
			if key:
				# Excel turns typed IDs into numbers (1012345678.0); undo that.
				if isinstance(value, float) and value.is_integer():
					value = int(value)
				values[key] = cstr(value).strip() if value is not None else ""
		if values.get("instructor"):
			yield excel_row, values


def _resolve_nationality(value, nationalities):
	wanted = value.strip().lower()
	for n in nationalities:
		if wanted in {cstr(n.name).lower(), cstr(n.ministry_code).lower(),
				cstr(n.name_english).lower(), cstr(n.name_arabic).strip().lower()}:
			return n.name
	return None


def _check_row(values, nationalities, departments):
	"""Return (sheet_values, problems). Empty data rows are skipped, not errors."""
	if not any(values.get(k) for k in ("gender", "nationality", "national_id", "home_id")):
		return None, ["Skipped: no data filled in yet"]

	instructor = frappe.db.get_value("Instructor", values["instructor"], ["status", "employee"], as_dict=True)
	if not instructor:
		return None, ["Instructor ID not found - the grey columns may have been changed"]
	if instructor.employee:
		return None, [f"Skipped: already linked to Employee {instructor.employee}"]

	problems = []
	nationality = _resolve_nationality(values.get("nationality", ""), nationalities) if values.get("nationality") else None
	if not values.get("nationality"):
		problems.append("Nationality is missing")
	elif not nationality:
		problems.append(f"Nationality '{values['nationality']}' is not in the Ministry codes - ask the administrator to add it")

	national_id, home_id = values.get("national_id"), values.get("home_id")
	if nationality and _is_saudi(nationality):
		if not national_id:
			problems.append("Saudi employee: Saudi National ID is missing")
		elif not re.fullmatch(r"\d{10}", national_id):
			problems.append(f"Saudi National ID '{national_id}' must be exactly 10 digits")
	elif nationality and not home_id:
		problems.append("Non-Saudi employee: ID in Home Country is missing")

	if values.get("gender") not in {"Male", "Female"}:
		problems.append("Gender must be Male or Female")
	if values.get("department") and values["department"] not in departments:
		problems.append(f"Department '{values['department']}' does not exist")

	sheet_values = {
		"custom_jameah_nationality": nationality,
		"custom_identity_number": national_id if nationality and _is_saudi(nationality) else None,
		"custom_original_home_id_number": home_id if nationality and not _is_saudi(nationality) else None,
		"gender": values.get("gender"),
		"department": values.get("department") or None,
		"employee_number": values.get("employee_number") or None,
	}
	return sheet_values, problems


def import_sheet(file, commit=0):
	from openpyxl import Workbook
	from openpyxl.styles import PatternFill

	commit = int(commit)
	company = get_default_company()
	nationalities = _nationalities()
	departments = set(frappe.get_all("Department Edu", pluck="name"))

	results = []
	for excel_row, values in _read_rows(file):
		sheet_values, problems = _check_row(values, nationalities, departments)
		if problems:
			status = "Skipped" if problems[0].startswith("Skipped") else "Fix needed"
			results.append((excel_row, values, status, "; ".join(problems)))
			continue
		ok, message = try_link(values["instructor"], company, commit, sheet_values)
		if ok:
			results.append((excel_row, values, "Done" if commit else "Ready", message if commit else "All checks passed"))
		else:
			results.append((excel_row, values, "Fix needed", message))

	if not commit:
		frappe.db.rollback()

	# Result sheet: the same rows plus a status, coloured for quick review.
	workbook = Workbook()
	sheet = workbook.active
	sheet.title = "Result"
	headers = ["Excel Row", "Instructor ID", "Name", "Status / الحالة", "Details / التفاصيل"]
	sheet.append(headers)
	colours = {"Ready": "C6EFCE", "Done": "C6EFCE", "Fix needed": "FFC7CE", "Skipped": "EDEDED"}
	for excel_row, values, status, details in results:
		sheet.append([excel_row, values["instructor"], values.get("name"), status, details])
		sheet.cell(row=sheet.max_row, column=4).fill = PatternFill("solid", fgColor=colours[status])
	for letter, width in zip("ABCDE", (10, 16, 30, 16, 90)):
		sheet.column_dimensions[letter].width = width
	sheet.freeze_panes = "A2"

	step = "3-Import-Done" if commit else "2-Check-Result"
	file_url = _save_file(_dated_name(step), workbook)

	counts = {}
	for *_, status, _details in results:
		counts[status] = counts.get(status, 0) + 1
	print(("IMPORTED" if commit else "CHECK ONLY (nothing saved)") + f": {counts}")
	return {"result_file": file_url, "counts": counts}
