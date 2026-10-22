"""Crosswalk from values stored by the college system to official Ministry codes.

The Student data lives in the Education app's own masters (Religion, City,
Country Edu...). Their code columns are not always Ministry codes (every City
has code 90, Religion uses REL001...), so the Ministry views never trust them
directly. Each distinct value gets a Jameah Code Map row that points at a
Jameah Ministry Code, and the views only use rows marked Verified.

A row is Verified automatically only when the meaning agrees with the
official list: the stored code exists in the category AND its name matches,
or the name matches exactly one official entry. REVIEWED holds mappings that
were checked by hand when the views were built. Anything else stays
"Needs Review" (sent as NULL) until HR or Academic Affairs picks the code.
A row someone edited (method "Manual") is never overwritten.
"""
import re
import unicodedata

import frappe

CODE_DOCTYPE = "Jameah Ministry Code"
MAP_DOCTYPE = "Jameah Code Map"


def _rows(sql, params=None):
	return frappe.db.sql(sql, params or {}, as_dict=True)


def _usage(*pairs):
	"""Count of records per value across (table, column) pairs."""
	counts = {}
	for table, column in pairs:
		for r in frappe.db.sql(f"SELECT `{column}` v, COUNT(*) n FROM `tab{table}` WHERE IFNULL(`{column}`, '') != '' GROUP BY 1"):
			counts[r[0]] = counts.get(r[0], 0) + r[1]
	return counts


def _master(doctype, code_field, name_fields, usage_pairs):
	def load():
		if not frappe.db.exists("DocType", doctype):
			return []
		meta = frappe.get_meta(doctype)
		fields = [f for f in [code_field, *name_fields] if f and meta.has_field(f)]
		usage = _usage(*usage_pairs)
		out = []
		for r in frappe.get_all(doctype, fields=["name", *fields]):
			out.append({
				"value": r.name,
				"code": (r.get(code_field) or "").strip() if code_field else "",
				"names": [r.name, *[r.get(f) for f in name_fields]],
				"usage": usage.get(r.name, 0),
			})
		return out
	return load


def _options(doctype, fieldname, usage_pairs, split_names=False):
	def load():
		options = set()
		for dt, fn in [(doctype, fieldname), *[(t, c) for t, c in usage_pairs if (t, c) != (doctype, fieldname)]]:
			df = frappe.get_meta(dt).get_field(fn)
			if df and df.fieldtype == "Select":
				options.update(o.strip() for o in (df.options or "").split("\n") if o.strip())
		usage = _usage(*usage_pairs)
		out = []
		for value in sorted(options):
			names = [value]
			if split_names:  # e.g. "مسجل - \tEnrolled" -> ["مسجل", "Enrolled"]
				names += [p.strip() for p in re.split(r"\s-\s|\t", value) if p.strip()]
			out.append({"value": value, "code": "", "names": names, "usage": usage.get(value, 0)})
		return out
	return load


def _nationality_text():
	"""Student/Guardian nationality is free text ("Saudi"); resolve it through Country Edu."""
	usage = _usage(("Student", "nationality"), ("Student Guardian", "nationality"))
	countries = {}
	for c in frappe.get_all("Country Edu", fields=["name", "country", "nationality", "country_name_arabic", "nationality_name_arabic", "ministry_code"]):
		if c.nationality:
			countries.setdefault(c.nationality.strip().lower(), c)
	out = []
	for value, n in usage.items():
		c = countries.get(value.strip().lower())
		out.append({
			"value": value,
			"code": (c.ministry_code or "").strip() if c else "",
			"names": [value, *([c.country, c.country_name_arabic, c.nationality_name_arabic] if c else [])],
			"usage": n,
		})
	return out


# (source, Ministry category, loader). The source string is what the views join on.
SOURCES = [
	("Gender Edu", "Gender", _master("Gender Edu", "gender_edu_ministry_code", ["gender_edu", "gender_edu_ar"], [("Student", "gender")])),
	("Country Edu", "Nationality", _master(
		"Country Edu", "ministry_code", ["country", "country_name_arabic", "nationality", "nationality_name_arabic"],
		[("Student", "place_of_birth"), ("Address Edu", "country"), ("Student Certificate", "high_school_diploma_obtained_in_outside_kigdom")])),
	("Nationality (text)", "Nationality", _nationality_text),
	("Marital Status", "Social status", _master("Marital Status", "marital_status_ministry_code", ["marital_status", "marital_status_ar"], [("Student", "marital_status")])),
	("Religion", "Religions", _master("Religion", "religion_ministry_code", ["religion_name", "religion_name_ar"], [("Student", "religion")])),
	("Special Need", "Type of special needs", _master("Special Need", "special_need_ministry_code", ["special_need_name", "special_need_name_ar"], [("Student", "special_need_type")])),
	("City", "Coding cities and governora", _master("City", "ministry_code", ["city_name", "city_name_ar"], [("Student", "current_city"), ("Student Certificate", "city_of_high_school")])),
	("Certificate Type", "Type of secondary school ce", _master("Certificate Type", "ministry_code", ["certificate_type_name", "name_in_arabic"], [("Student Certificate", "type_of_certificate")])),
	("Student Status", "General situation", _master("Student Status", "student_status_code", ["student_status_name"], [("Student", "original_status")])),
	("Degree", "Coding of academic degrees", _master("Degree", "degree_code", ["degree_name", "degree_name_ar"], [("Program", "academic_degree")])),
	("Education Level", "Educational level - 33", _master("Education Level", "education_level_external_code", ["education_level_name", "education_level_name_ar"], [("Program", "academic_education_level")])),
	("Major", "Specialization Coding Guide", _master("Major", "major_external_code", ["major_name", "major_name_ar"], [("Program", "academic_program_major")])),
	("Program", "Coding academic departments", _master("Program", None, ["program_name", "program_name_ar"], [("Program Enrollment", "program")])),
	("Academic Term.term_name", "Admission to study", lambda: [
		{"value": r.v, "code": "", "names": [r.v], "usage": r.n}
		for r in _rows("SELECT term_name v, COUNT(*) n FROM `tabAcademic Term` WHERE IFNULL(term_name, '') != '' GROUP BY 1")]),
	("Student.current_year_status", "Registration status", _options("Student", "current_year_status", [("Student", "current_year_status")], split_names=True)),
	("Identity Type (Select)", "Identity type", _options("Student", "id_type", [("Student", "id_type"), ("Student Guardian", "id_type_civil_registration_type")])),
	("Address Edu.housing_status", "Residential status coding", _options("Address Edu", "housing_status", [("Address Edu", "housing_status")])),
	("Employee.marital_status", "Social status", _options("Employee", "marital_status", [("Employee", "marital_status")])),
	# Faculty masters (Faculty views). Their own codes are not Ministry codes (1 / 0 / FCT-FULL), so only the name can match.
	("Faculty Ranking", "Academic ranks", _master("Faculty Ranking", None, ["faculty_ranking_name"], [("Instructor", "instructor_faculty_ranking")])),
	("Faculty Status", "Job status", _master("Faculty Status", None, ["faculty_status_name"], [("Instructor", "instructor_faculty_status")])),
	("Faculty Contract Type", "Type of appointment", _master("Faculty Contract Type", None, ["faculty_contract_type_name"], [("Instructor", "instructor_faculty_contract_type")])),
]

# Checked by hand against the Ministry list when the views were built
# (names differ in wording, so the automatic match cannot confirm them).
REVIEWED = {
	("Religion", "Islam"): "1", ("Religion", "Christianity"): "2", ("Religion", "Hinduism"): "5", ("Religion", "Buddhism"): "6",
	("Identity Type (Select)", "Saudi National ID"): "01", ("Identity Type (Select)", "Gulf ID"): "02",
	("Identity Type (Select)", "Residence Permit"): "03", ("Identity Type (Select)", "Passport"): "04",
	("Address Edu.housing_status", "He lives in the educational institution’s housing"): "1",
	("Address Edu.housing_status", "He does not live in the educational institution’s housing"): "2",
	("Address Edu.housing_status", "There is no housing in the educational area"): "8",
	("Academic Term.term_name", "Fall"): "1", ("Academic Term.term_name", "Spring"): "2", ("Academic Term.term_name", "Summer"): "3",
	("Degree", "Bachelor"): "2",
	("Education Level", "Bachelor"): "6", ("Education Level", "Master"): "7", ("Education Level", "PhD"): "8", ("Education Level", "Doctorate"): "8",
	# Education's own Student Status codes follow the Ministry "General situation" list.
	("Student Status", "Active"): "0", ("Student Status", "Withdrawn"): "1", ("Student Status", "Transferred"): "2",
	("Student Status", "Dismissed"): "3", ("Student Status", "Expelled"): "4", ("Student Status", "Terminated"): "5",
	("Student Status", "Graduated"): "6", ("Student Status", "Died"): "7", ("Student Status", "Other"): "9",
	# The Ministry list has married / bachelor / other only.
	("Employee.marital_status", "Married"): "1", ("Employee.marital_status", "Single"): "2",
	("Employee.marital_status", "Divorced"): "9", ("Employee.marital_status", "Widowed"): "9",
	("Marital Status", "Married"): "1", ("Marital Status", "Single"): "2", ("Marital Status", "Other"): "9",
	("Gender Edu", "Male"): "1", ("Gender Edu", "Female"): "2",
	("Certificate Type", "Scientific Certificate"): "01", ("Certificate Type", "Literary Certificate"): "03",
	# Jeddah Governorate; "Center in Jeddah" (0701005) is a different place in another region.
	("City", "Jeddah"): "0202000",
}

_AR_DIACRITICS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_EN_NOISE = re.compile(r"\b(the|kingdom of|republic of|state of|of)\b")


def normalize(text):
	if not text:
		return ""
	s = unicodedata.normalize("NFKC", str(text)).strip().lower()
	s = _AR_DIACRITICS.sub("", s)
	s = s.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ى": "ي", "’": "'", "‘": "'"}))
	s = _EN_NOISE.sub(" ", s)
	s = re.sub(r"[^\w؀-ۿ]+", " ", s)
	return re.sub(r"\s+", " ", s).strip()


def _official():
	by_category = {}
	for r in frappe.get_all(CODE_DOCTYPE, fields=["name", "code_category", "ministry_code", "name_english", "name_arabic"]):
		by_category.setdefault(r.code_category, []).append(r)
	return by_category


def match(candidates, code, names):
	"""(ministry_code, method) when the meaning is certain, else (None, suggestion text)."""
	wanted = {normalize(n) for n in names if normalize(n)}
	agrees = lambda c: normalize(c.name_english) in wanted or normalize(c.name_arabic) in wanted
	if code:
		for c in candidates:
			if c.ministry_code in (code, code.zfill(2), code.lstrip("0") or "0") and agrees(c):
				return c.ministry_code, "Code and name"
	hits = [c for c in candidates if agrees(c)]
	if len({h.ministry_code for h in hits}) == 1:
		return hits[0].ministry_code, "Name"
	tokens = set(" ".join(wanted).split())
	scored = sorted(
		((len(tokens & set(normalize(f"{c.name_english} {c.name_arabic}").split())), c) for c in candidates),
		key=lambda x: -x[0])
	suggestions = [f"{c.ministry_code} {c.name_english} / {c.name_arabic}" for score, c in scored[:4] if score]
	same_code = [c for c in candidates if code and c.ministry_code == code]
	if same_code:
		suggestions.insert(0, f"Stored code {code} = {same_code[0].name_english} (name differs, check it)")
	return None, "\n".join(suggestions) or "No similar Ministry entry"


def refresh():
	"""Create/update a Jameah Code Map row for every source value. Returns counts."""
	official = _official()
	stats = {"verified": 0, "needs_review": 0, "manual": 0}
	for source, category, load in SOURCES:
		candidates = official.get(category, [])
		for row in load():
			value = (row["value"] or "").strip()
			if not value:
				continue
			name = frappe.db.get_value(MAP_DOCTYPE, {"source_doctype": source, "source_value": value, "code_category": category})
			doc = frappe.get_doc(MAP_DOCTYPE, name) if name else frappe.new_doc(MAP_DOCTYPE)
			doc.update({"source_doctype": source, "source_value": value, "code_category": category, "usage_count": row["usage"]})
			if doc.method == "Manual":
				stats["manual"] += 1
			else:
				code, how = None, None
				if (source, value) in REVIEWED:
					code, how = REVIEWED[(source, value)], "Reviewed"
				else:
					code, how = match(candidates, row["code"], row["names"])
				jameah_code = f"{category}::{code}" if code else None
				if jameah_code and not frappe.db.exists(CODE_DOCTYPE, jameah_code):
					code, how, jameah_code = None, f"Reviewed code {code} is missing from the Ministry list", None
				doc.jameah_code = jameah_code
				doc.status = "Verified" if jameah_code else "Needs Review"
				doc.method = how if jameah_code else ""
				doc.suggestion = None if jameah_code else how
				stats["verified" if jameah_code else "needs_review"] += 1
			doc.flags.from_refresh = True
			doc.save(ignore_permissions=True)
	return stats
