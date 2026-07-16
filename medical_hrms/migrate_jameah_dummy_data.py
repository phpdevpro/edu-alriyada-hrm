import json
import os

import frappe
from education.education.doctype.instructor import instructor as instructor_module


def _insert_if_missing(doctype, values, name):
    if frappe.db.exists(doctype, name):
        return frappe.get_doc(doctype, name)
    doc = frappe.get_doc({"doctype": doctype, **values})
    doc.insert(ignore_permissions=True)
    return doc


def _exists_by_field(doctype, values, fieldname):
    return frappe.db.exists(doctype, {fieldname: values[fieldname]})


def _insert_ministry_code_if_missing(values):
    filters = {
        "code_category": values["code_category"],
        "ministry_code": values["ministry_code"],
    }
    name = frappe.db.get_value("Jameah Ministry Code", filters, "name")
    if name:
        return frappe.get_doc("Jameah Ministry Code", name)

    doc = frappe.get_doc({"doctype": "Jameah Ministry Code", **values})
    doc.insert(ignore_permissions=True)
    return doc


def _resolve_ministry_code(category, ministry_code):
    if not ministry_code:
        return ministry_code

    name = frappe.db.get_value(
        "Jameah Ministry Code",
        {"code_category": category, "ministry_code": ministry_code},
        "name",
    )
    if not name:
        raise frappe.LinkValidationError(
            f"Could not resolve Jameah Ministry Code {category}: {ministry_code}"
        )
    return name


def _resolve_ministry_name(category, name_english):
    if not name_english:
        return name_english

    name = frappe.db.get_value(
        "Jameah Ministry Code",
        {"code_category": category, "name_english": name_english},
        "name",
    )
    if not name:
        raise frappe.LinkValidationError(
            f"Could not resolve Jameah Ministry Code {category}: {name_english}"
        )
    return name


def _resolve_fields(values, field_categories):
    resolved = dict(values)
    for fieldname, category in field_categories.items():
        if resolved.get(fieldname):
            resolved[fieldname] = _resolve_ministry_code(category, resolved[fieldname])
    return resolved


def _resolve_person_ministry_links(values):
    resolved = _resolve_fields(
        values,
        {
            "custom_identity_type": "Identity type",
            "custom_identity_issue_place": "Coding cities and governora",
            "custom_jameah_nationality": "Nationality",
        },
    )

    child_field_categories = {
        "custom_jameah_qualifications": {
            "degree": "Degree",
            "specialization": "Specialization",
            "country": "Nationality",
        },
        "custom_jameah_experience": {
            "city": "Coding cities and governora",
            "country": "Nationality",
        },
        "custom_jameah_training": {
            "city": "Coding cities and governora",
            "country": "Nationality",
        },
    }
    for table_field, field_categories in child_field_categories.items():
        resolved[table_field] = [
            _resolve_fields(row, field_categories) for row in resolved.get(table_field, [])
        ]

    return resolved


def _set_rows(doc, fieldname, rows):
    if not rows:
        return
    doc.set(fieldname, [])
    for row in rows:
        doc.append(fieldname, row)


def _ensure_genders():
    for gender in ("Male", "Female"):
        if not frappe.db.exists("Gender", gender):
            try:
                frappe.get_doc({"doctype": "Gender", "gender": gender}).insert(ignore_permissions=True)
            except Exception:
                pass


def execute():
    app_path = frappe.get_app_path("medical_hrms")
    data_file = os.path.join(app_path, "seed_data", "jameah_dummy_data.json")
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data.get("ministry_codes", []):
        _insert_ministry_code_if_missing(item)

    standard = data.get("standard_masters", {})
    if standard.get("company") and not _exists_by_field("Company", standard["company"], "company_name"):
        frappe.get_doc({"doctype": "Company", **standard["company"]}).insert(ignore_permissions=True)

    if standard.get("designation") and not _exists_by_field("Designation", standard["designation"], "designation_name"):
        frappe.get_doc({"doctype": "Designation", **standard["designation"]}).insert(ignore_permissions=True)

    if standard.get("branch") and not _exists_by_field("Branch", standard["branch"], "branch"):
        frappe.get_doc({"doctype": "Branch", **standard["branch"]}).insert(ignore_permissions=True)

    if standard.get("department") and not _exists_by_field("Department", standard["department"], "department_name"):
        frappe.get_doc({"doctype": "Department", **standard["department"]}).insert(ignore_permissions=True)

    if standard.get("location_edu") and not _exists_by_field("Location Edu", standard["location_edu"], "location_name_edu"):
        frappe.get_doc({"doctype": "Location Edu", **standard["location_edu"]}).insert(ignore_permissions=True)

    if standard.get("campus") and not _exists_by_field("Campus", standard["campus"], "campus_name"):
        frappe.get_doc({"doctype": "Campus", **standard["campus"], "campus_location": standard["location_edu"]["location_name_edu"]}).insert(ignore_permissions=True)

    if standard.get("college") and not _exists_by_field("College", standard["college"], "college_name"):
        college_doc = frappe.get_doc({"doctype": "College", **standard["college"]})
        college_doc.append("college_campus_list", {"college_campus_name": standard["campus"]["campus_name"]})
        college_doc.insert(ignore_permissions=True)

    if standard.get("department_edu") and not _exists_by_field("Department Edu", standard["department_edu"], "department_name"):
        dept_doc = frappe.get_doc({"doctype": "Department Edu", **standard["department_edu"]})
        dept_doc.append("department_table_college", {"ins_college_name": standard["college"]["college_name"], "ins_college_campus": standard["campus"]["campus_name"]})
        dept_doc.insert(ignore_permissions=True)

    if standard.get("faculty_status") and not _exists_by_field("Faculty Status", standard["faculty_status"], "faculty_status_name"):
        frappe.get_doc({"doctype": "Faculty Status", **standard["faculty_status"]}).insert(ignore_permissions=True)

    if standard.get("faculty_contract_type") and not _exists_by_field("Faculty Contract Type", standard["faculty_contract_type"], "faculty_contract_type_name"):
        frappe.get_doc({"doctype": "Faculty Contract Type", **standard["faculty_contract_type"]}).insert(ignore_permissions=True)

    if standard.get("faculty_ranking") and not _exists_by_field("Faculty Ranking", standard["faculty_ranking"], "faculty_ranking_name"):
        frappe.get_doc({"doctype": "Faculty Ranking", **standard["faculty_ranking"]}).insert(ignore_permissions=True)

    if standard.get("major") and not _exists_by_field("Major", standard["major"], "major_name"):
        frappe.get_doc({"doctype": "Major", **standard["major"]}).insert(ignore_permissions=True)

    if standard.get("education_level") and not _exists_by_field("Education Level", standard["education_level"], "education_level_name"):
        frappe.get_doc({"doctype": "Education Level", **standard["education_level"]}).insert(ignore_permissions=True)

    for section, doctype, key in (
        ("branches", "Jameah Branch", "branch_name_en"),
        ("agencies", "Jameah Agency", "agency_name_en"),
        ("deaneries", "Jameah Deanery", "deanery_name_en"),
        ("colleges", "Jameah College", "college_name_en"),
        ("departments", "Jameah Academic Department", "department_name_en"),
        ("facilities", "Jameah Facility", "facility_name_en"),
    ):
        for item in data.get(section, []):
            item = _resolve_fields(item, {"ministry_code": "Coding cities and governora"})
            _insert_if_missing(doctype, item, item[key])

    company = frappe.db.get_value("Company", {}, "name")
    if not company:
        raise frappe.ValidationError("Create a Company before running the seed migration.")

    _ensure_genders()

    employee_data = _resolve_person_ministry_links(data["employee"])
    employee_gender_field = frappe.get_meta("Employee").get_field("gender")
    if employee_gender_field.options == "Jameah Ministry Code":
        employee_data["gender"] = _resolve_ministry_name("Gender", employee_data["gender"])
    employee_data["company"] = company
    employee_data.setdefault("employee_name", f"{employee_data['first_name']} {employee_data['middle_name']} {employee_data['last_name']}")
    employee_data.setdefault("employee", employee_data.get("employee_number") or "EMP-0001")
    employee_data.pop("branch", None)

    employee = frappe.db.exists("Employee", {"employee_number": employee_data["employee_number"]})
    if employee:
        employee_doc = frappe.get_doc("Employee", employee)
    else:
        employee_doc = frappe.get_doc({"doctype": "Employee", **employee_data})
        _set_rows(employee_doc, "custom_jameah_qualifications", employee_data.get("custom_jameah_qualifications", []))
        _set_rows(employee_doc, "custom_jameah_experience", employee_data.get("custom_jameah_experience", []))
        _set_rows(employee_doc, "custom_jameah_training", employee_data.get("custom_jameah_training", []))
        _set_rows(employee_doc, "custom_jameah_publications", employee_data.get("custom_jameah_publications", []))
        _set_rows(employee_doc, "custom_jameah_awards", employee_data.get("custom_jameah_awards", []))
        employee_doc.insert(ignore_permissions=True)

    instructor_data = _resolve_person_ministry_links(data["instructor"])
    instructor_data["employee"] = employee_doc.name
    instructor_data.setdefault("employee_no", employee_doc.employee_number or employee_doc.name)
    instructor_data["department"] = standard.get("department_edu", {}).get("department_name", instructor_data.get("department"))
    instructor_data["instructor_location"] = standard.get("location_edu", {}).get("location_name_edu", instructor_data.get("instructor_location"))
    instructor_data["instructor_campus"] = standard.get("campus", {}).get("campus_name", instructor_data.get("instructor_campus"))
    instructor_data["instructor_college"] = standard.get("college", {}).get("college_name", instructor_data.get("instructor_college"))
    instructor_data["instructor_qualification"] = standard.get("education_level", {}).get("education_level_name", instructor_data.get("instructor_qualification"))
    instructor_data["instructor_faculty_status"] = standard.get("faculty_status", {}).get("faculty_status_name", instructor_data.get("instructor_faculty_status"))
    instructor_data["instructor_faculty_contract_type"] = standard.get("faculty_contract_type", {}).get("faculty_contract_type_name", instructor_data.get("instructor_faculty_contract_type"))
    instructor_data["instructor_faculty_ranking"] = standard.get("faculty_ranking", {}).get("faculty_ranking_name", instructor_data.get("instructor_faculty_ranking"))
    instructor_data["instructor_major"] = standard.get("major", {}).get("major_name", instructor_data.get("instructor_major"))

    instructor = frappe.db.exists("Instructor", {"instructor_id": instructor_data["instructor_id"]})
    if not instructor:
        instructor = frappe.db.exists("Instructor", {"employee": employee_doc.name})
    if instructor:
        instructor_doc = frappe.get_doc("Instructor", instructor)
    else:
        original_after_insert = getattr(instructor_module.Instructor, "after_insert", None)
        instructor_module.Instructor.after_insert = lambda self: None
        try:
            instructor_doc = frappe.get_doc({"doctype": "Instructor", **instructor_data})
            _set_rows(instructor_doc, "custom_jameah_qualifications", instructor_data.get("custom_jameah_qualifications", []))
            _set_rows(instructor_doc, "custom_jameah_experience", instructor_data.get("custom_jameah_experience", []))
            _set_rows(instructor_doc, "custom_jameah_training", instructor_data.get("custom_jameah_training", []))
            _set_rows(instructor_doc, "custom_jameah_publications", instructor_data.get("custom_jameah_publications", []))
            _set_rows(instructor_doc, "custom_jameah_awards", instructor_data.get("custom_jameah_awards", []))
            instructor_doc.insert(ignore_permissions=True)
        finally:
            if original_after_insert is not None:
                instructor_module.Instructor.after_insert = original_after_insert

    frappe.db.commit()
    print("Seed migration complete")
