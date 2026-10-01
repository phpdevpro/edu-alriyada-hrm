"""Allowlisted employee forms. Never accept identity or approval fields from clients."""
import frappe
from frappe.utils import cint
from medical_hrms.employee_permissions import get_employee_for_user

FIELDS = {
    "Permission Request": "date from_time to_time reason",
    "Remote Work Request": "from_date to_date work_plan location",
    "Leave Application": "leave_type from_date to_date half_day half_day_date description",
    "Return from Leave Request": "leave_application actual_return_date fitness_certificate",
    "Salary Certificate Request": "purpose language_preference addressee include_salary_breakdown",
    "Pre Approved Overtime Request": "date ot_hours_requested ot_type business_justification compensation_preference",
    "Employee Training Request": "course_details provider estimated_cost business_benefit",
    "Children Medical Allowance Request": "child_name school_name academic_year fee_amount_requested payment_preference invoice_attachment birth_certificate",
    "Company Car Request": "business_justification client_visits_per_week preferred_category",
    "Employee Data Update Request": "update_type new_value supporting_document",
}


def employee_identity():
    if "Employee" not in frappe.get_roles():
        frappe.throw("Employee access is required.", frappe.PermissionError)
    employee = get_employee_for_user()
    if not employee:
        frappe.throw("Ask HR to link your login to an Employee record.", frappe.PermissionError)
    return employee


def fields_for(doctype):
    if doctype not in FIELDS:
        frappe.throw("This service is not available for employee submission.", frappe.PermissionError)
    return FIELDS[doctype].split()


@frappe.whitelist()
def form_schema(doctype):
    employee_identity()
    meta = frappe.get_meta(doctype)
    result = []
    for fieldname in fields_for(doctype):
        df = meta.get_field(fieldname)
        result.append({key: df.get(key) for key in ("fieldname", "label", "fieldtype", "options", "reqd", "default")})
        if fieldname == "half_day_date":
            result[-1].update(depends_on="eval:doc.half_day", mandatory_depends_on="eval:doc.half_day")
    return result


def validate_employee_request(doc, method=None):
    if frappe.session.user == "Administrator" or set(frappe.get_roles()).intersection({"HR User", "HR Manager", "System Manager"}):
        return
    employee = employee_identity()
    if doc.employee != employee:
        frappe.throw("You can only submit your own requests.", frappe.PermissionError)
    if doc.doctype in {"Contract Renewal Request", "Leave Plan Request"}:
        frappe.throw("This process is managed by HR. Use Request Leave to apply for leave.", frappe.PermissionError)
    old = doc.get_doc_before_save()
    if old and (old.employee != employee or old.status != "Draft"):
        frappe.throw("Sent requests cannot be edited by employees.", frappe.PermissionError)
    statuses = frappe.get_meta(doc.doctype).get_field("status").options.splitlines()
    pending = next((status for status in statuses if status.startswith("Pending")), None)
    if doc.status not in ("Draft", pending):
        frappe.throw("Only HR can set approval status.", frappe.PermissionError)
    for field in ("occupational_health_clearance", "approved_amount", "manager_recommendation", "proposed_salary_increase"):
        if doc.meta.has_field(field):
            expected = old.get(field) if old else doc.meta.get_field(field).default
            if (doc.get(field) or "") != (expected or ""):
                frappe.throw("Only HR can change approval or clearance fields.", frappe.PermissionError)
    if doc.get("leave_application"):
        if frappe.db.get_value("Leave Application", doc.leave_application, "employee") != employee:
            frappe.throw("Select your own leave application.", frappe.PermissionError)


@frappe.whitelist()
def save_request(doctype, values, send=False):
    employee = employee_identity()
    allowed = fields_for(doctype)
    values = frappe.parse_json(values)
    if not isinstance(values, dict) or set(values) - set(allowed):
        frappe.throw("Unsupported form fields.", frappe.PermissionError)
    meta = frappe.get_meta(doctype)
    for name, value in values.items():
        if meta.get_field(name).fieldtype == "Attach" and value:
            attachment = frappe.db.get_value("File", {"file_url": value, "owner": frappe.session.user, "is_private": 1}, "name")
            if not attachment:
                frappe.throw("Upload a private attachment from your own account.", frappe.PermissionError)
    if doctype == "Leave Application":
        from hrms.hr.doctype.leave_application.leave_application import get_leave_approver
        if not cint(send):
            frappe.throw("Use Send Request to send your leave application for review.")
        approver = get_leave_approver(employee)
        if not approver or approver == frappe.session.user:
            frappe.throw("Ask HR to configure a leave approver for your employee or department.")
        doc = frappe.get_doc({
            "doctype": doctype, **values, "employee": employee,
            "company": frappe.db.get_value("Employee", employee, "company"),
            "leave_approver": approver, "status": "Open",
        })
        # Open is the native pending-review state. Only an approver submits it.
        doc.insert()
        return {"name": doc.name, "status": doc.status}
    pending = next(status for status in meta.get_field("status").options.splitlines() if status.startswith("Pending"))
    doc = frappe.get_doc({"doctype": doctype, **values, "employee": employee, "status": pending if cint(send) else "Draft"})
    doc.insert()
    return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def my_requests(doctype):
    fields_for(doctype)
    return frappe.get_list(doctype, filters={"employee": employee_identity()}, fields=["name", "status", "modified"], order_by="modified desc", limit_page_length=50)


@frappe.whitelist()
def request_details(doctype, name):
    allowed = fields_for(doctype)
    employee = employee_identity()
    # Use one response for missing and other employees' records.
    if frappe.db.get_value(doctype, name, "employee") != employee:
        frappe.throw("This request is not available to you.", frappe.PermissionError)
    doc = frappe.get_doc(doctype, name)
    doc.check_permission("read")
    fields = []
    for fieldname in allowed:
        df = doc.meta.get_field(fieldname)
        value = doc.get(fieldname)
        if df.fieldtype == "Attach" and value:
            files = frappe.get_all("File", filters={"file_url": value}, pluck="name")
            if not any(frappe.has_permission("File", "read", doc=frappe.get_doc("File", file)) for file in files):
                value = None
        fields.append({"label": df.label, "fieldtype": df.fieldtype, "value": value})
    return {"name": doc.name, "doctype": doc.doctype, "status": doc.status, "fields": fields}


def validate_employee_leave(doc, method=None):
    if frappe.session.user == "Administrator" or set(frappe.get_roles()).intersection({"HR User", "HR Manager", "System Manager"}):
        return
    if "Employee" not in frappe.get_roles() or doc.employee != get_employee_for_user():
        return  # Core permissions govern designated approvers handling other staff.
    from hrms.hr.doctype.leave_application.leave_application import get_leave_approver
    if doc.status != "Open" or doc.docstatus != 0:
        frappe.throw("Only your leave approver or HR can approve, reject, or submit leave.", frappe.PermissionError)
    if doc.leave_approver != get_leave_approver(doc.employee):
        frappe.throw("The leave approver is assigned by HR.", frappe.PermissionError)
