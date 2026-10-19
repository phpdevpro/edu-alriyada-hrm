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
from medical_hrms.ministry_lookup_validation import identity_problems, is_saudi_nationality, ministry_codes
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
	("identity_type", "Identity Type / نوع الهوية [identity_type]", 18, "input"),
	("identity_number", "Identity Number (National ID / Iqama: 10 digits) / رقم الهوية [identity_number]", 26, "input"),
	("home_id", "Optional: ID in Home Country (non-Saudis) / رقم الهوية في بلد الأصل - اختياري [home_id]", 26, "input"),
	("department", "Department / القسم [department]", 30, "input"),
	("employee_number", "Employee Number / الرقم الوظيفي [employee_number]", 18, "input"),
]
TEXT_COLUMNS = {"identity_number", "home_id", "employee_number"}
# Instructor.instructor_id_type -> Ministry identity type (name_english).
ID_TYPE_SUGGESTION = {"Saudi National ID": "National ID", "Residence Permit": "Iqama", "Gulf ID": "Gulf ID", "Passport": "Passport"}

INSTRUCTIONS = [
	"Instructor Ministry Data / بيانات المحاضرين للوزارة",
	"",
	"Why: these Instructors have no Employee record, so HR can't manage them and they can't use HR self-service.",
	"The Ministry requires a nationality and an ID number for every Employee.",
	"",
	"How to fill in the 'Instructors' sheet:",
	"  • Grey columns: do not change.",
	"  • Green columns: please fill in.",
	"  • Yellow cells: a suggestion from the ID type on file (e.g. Saudi National ID → Saudi Arabian). Please check.",
	"  • Everyone needs an Identity Type and an Identity Number (Ministry requirement):",
	"      Saudi employees: National ID, 10 digits starting with 1.",
	"      Residents: Iqama, 10 digits starting with 2.  (Gulf ID / Passport also accepted.)",
	"  • 'ID in Home Country' is optional, for non-Saudis only.",
	"  • Use the dropdowns where available. A nationality not in the list can be typed;",
	"    the import will report it if it is not in the Ministry codes yet.",
	"  • Leave a row blank if you don't have the data yet - it will simply be skipped.",
	"",
	"Then upload the file in Desk (File list) and send the file name to the system administrator.",
]


def _nationalities():
	return ministry_codes("Nationality")


def _identity_types():
	return ministry_codes("Identity type")


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
			"custom_jameah_nationality", "custom_identity_type", "custom_identity_number", "department", "employee_no"],
		order_by="instructor_name",
	)
	nationalities = _nationalities()
	identity_types = _identity_types()
	saudi = next((n for n in nationalities if is_saudi_nationality(n.name)), None)
	code_to_label = {n.name: n.name_english for n in nationalities + identity_types}
	known_identity_types = {t.name_english for t in identity_types}

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
		identity_type = code_to_label.get(ins.custom_identity_type)
		suggested_identity_type = None
		if not identity_type and ID_TYPE_SUGGESTION.get(ins.instructor_id_type) in known_identity_types:
			suggested_identity_type = ID_TYPE_SUGGESTION[ins.instructor_id_type]
		values = {
			"instructor": ins.name, "name": ins.instructor_name, "arabic_name": ins.arabic_name,
			"email": ins.email, "id_type": ins.instructor_id_type, "gender": ins.gender,
			"nationality": nationality or suggested_nationality,
			"identity_type": identity_type or suggested_identity_type,
			"identity_number": ins.custom_identity_number,
			"department": ins.department, "employee_number": ins.employee_no,
		}
		for col, key in enumerate(keys, start=1):
			cell = sheet.cell(row=row, column=col, value=values.get(key) or None)
			if key in TEXT_COLUMNS:
				cell.number_format = "@"  # keep leading zeros / long IDs as text
		for key, was_suggested in (("nationality", suggested_nationality), ("identity_type", suggested_identity_type)):
			if was_suggested:
				sheet.cell(row=row, column=keys.index(key) + 1).fill = suggested

	# Dropdown sources on a hidden sheet.
	lists = workbook.create_sheet("Lists")
	lists.sheet_state = "hidden"
	sources = {
		"gender": frappe.get_all("Gender Edu", pluck="name", order_by="name"),
		"nationality": list(dict.fromkeys(n.name_english for n in nationalities if n.name_english)),
		"identity_type": list(dict.fromkeys(t.name_english for t in identity_types if t.name_english)),
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


def _resolve_code(value, codes):
	"""Match what HR typed against a code's name, code or labels; codes are
	ordered real-first (see ministry_codes)."""
	wanted = value.strip().lower()
	for n in codes:
		if wanted in {cstr(n.name).lower(), cstr(n.ministry_code).lower(),
				cstr(n.name_english).strip().lower(), cstr(n.name_arabic).strip().lower()}:
			return n.name
	return None


def _check_row(values, nationalities, identity_types, departments):
	"""Return (sheet_values, problems). Empty data rows are skipped, not errors."""
	if not any(values.get(k) for k in ("nationality", "identity_number", "home_id")):
		return None, ["Skipped: no data filled in yet"]

	instructor = frappe.db.get_value("Instructor", values["instructor"], ["status", "employee"], as_dict=True)
	if not instructor:
		return None, ["Instructor ID not found - the grey columns may have been changed"]
	if instructor.employee:
		return None, [f"Skipped: already linked to Employee {instructor.employee}"]

	problems = []
	nationality = identity_type = None
	for key, codes, label in (("nationality", nationalities, "Nationality"), ("identity_type", identity_types, "Identity Type")):
		if values.get(key):
			code = _resolve_code(values[key], codes)
			if code:
				nationality, identity_type = (code, identity_type) if key == "nationality" else (nationality, code)
			else:
				problems.append(f"{label} '{values[key]}' is not in the Ministry codes - ask the administrator to add it")

	number = values.get("identity_number")
	# Unknown typed values were already reported above; only flag what's missing.
	problems += [
		problem for problem in identity_problems(nationality, identity_type, number)
		if not (problem.startswith("Nationality") and values.get("nationality"))
		and not (problem.startswith("Identity Type") and values.get("identity_type"))
	]
	if number:
		existing = frappe.db.get_value("Employee", {"custom_identity_number": number}, "name")
		if existing:
			problems.append(f"Identity Number {number} is already registered to Employee {existing}")

	if values.get("gender") not in {"Male", "Female"}:
		problems.append("Gender must be Male or Female")
	if values.get("department") and values["department"] not in departments:
		problems.append(f"Department '{values['department']}' does not exist")

	sheet_values = {
		"custom_jameah_nationality": nationality,
		"custom_identity_type": identity_type,
		"custom_identity_number": number,
		"custom_original_home_id_number": values.get("home_id") or None,
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
	identity_types = _identity_types()
	departments = set(frappe.get_all("Department Edu", pluck="name"))

	results = []
	seen = {}  # same person twice in the sheet; per-row rollback can't catch it
	for excel_row, values in _read_rows(file):
		sheet_values, problems = _check_row(values, nationalities, identity_types, departments)
		for key, label in (("identity_number", "Identity Number"), ("employee_number", "Employee Number")):
			value = values.get(key)
			if sheet_values and value:
				if (key, value) in seen:
					problems.append(f"{label} {value} is also on Excel row {seen[(key, value)]}")
				else:
					seen[(key, value)] = excel_row
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
