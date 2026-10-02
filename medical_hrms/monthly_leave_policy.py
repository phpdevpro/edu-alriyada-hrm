"""Opt-in company rules, separate from statutory leave entitlements."""
from collections import Counter
from datetime import timedelta

import frappe
from frappe.utils import cint, getdate, get_first_day, get_last_day, today


def setup():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields({"HR Settings": [
        {"fieldname": "custom_employee_monthly_policy", "fieldtype": "Section Break", "label": "Employee Monthly Limits", "insert_after": "leave_and_expense_claim_settings"},
        {"fieldname": "custom_limit_half_days", "fieldtype": "Check", "label": "Enable Monthly Half-day Limit", "default": "0", "insert_after": "custom_employee_monthly_policy"},
        {"fieldname": "custom_half_day_leave_type", "fieldtype": "Link", "options": "Leave Type", "label": "Leave Type Subject to Half-day Limit", "insert_after": "custom_limit_half_days", "description": "Select the applicable annual leave type. Other leave types are not capped by this rule."},
        {"fieldname": "custom_half_day_monthly_limit", "fieldtype": "Int", "label": "Half-day Requests per Calendar Month", "default": "2", "insert_after": "custom_half_day_leave_type"},
        {"fieldname": "custom_limit_remote_work", "fieldtype": "Check", "label": "Enable Monthly Work-from-home Limit", "default": "0", "insert_after": "custom_half_day_monthly_limit"},
        {"fieldname": "custom_remote_work_monthly_limit", "fieldtype": "Int", "label": "Work-from-home Working Days per Calendar Month", "default": "3", "insert_after": "custom_limit_remote_work", "description": "Pending and approved days count. Employee/company Holiday List determines non-working days."},
    ]}, update=True)
    # Field defaults do not populate existing Single DocType records.
    settings = frappe.get_doc("HR Settings")
    changed = False
    for field, default in (("custom_half_day_monthly_limit", 2), ("custom_remote_work_monthly_limit", 3)):
        if settings.get(field) is None:
            settings.set(field, default)
            changed = True
    if changed:
        settings.save(ignore_permissions=True)


def policy():
    return frappe.get_cached_doc("HR Settings")


def validate_settings(doc, method=None):
    if doc.get("custom_limit_half_days") and (not doc.get("custom_half_day_leave_type") or cint(doc.get("custom_half_day_monthly_limit")) < 1):
        frappe.throw("Choose a leave type and a positive monthly half-day limit.")
    if doc.get("custom_limit_remote_work") and cint(doc.get("custom_remote_work_monthly_limit")) < 1:
        frappe.throw("Enter a positive monthly work-from-home limit.")


def working_days(employee, start, end):
    from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
    start, end = getdate(start), getdate(end)
    if end < start:
        frappe.throw("End date must not be before start date.")
    calendar = get_holiday_list_for_employee(employee)
    bounds = frappe.db.get_value("Holiday List", calendar, ["from_date", "to_date"], as_dict=True)
    if not bounds or getdate(bounds.from_date) > start or getdate(bounds.to_date) < end:
        frappe.throw("HR must configure a Holiday List covering all requested work-from-home dates.")
    holidays = {getdate(row.holiday_date) for row in frappe.get_all("Holiday", filters={"parent": calendar, "holiday_date": ["between", [start, end]]}, fields=["holiday_date"])}
    return {start + timedelta(days=i) for i in range((end - start).days + 1) if start + timedelta(days=i) not in holidays}


def half_day_count(employee, start, end, leave_type, exclude=None):
    if exclude is not None:
        return len(frappe.db.sql("""select name from `tabLeave Application`
            where employee=%s and half_day=1 and half_day_date between %s and %s
            and status in ('Open','Approved') and docstatus<2 and leave_type=%s
            and name!=%s for update""", (employee, start, end, leave_type, exclude)))
    filters = {"employee": employee, "half_day": 1, "half_day_date": ["between", [start, end]], "status": ["in", ["Open", "Approved"]], "docstatus": ["<", 2]}
    if leave_type:
        filters["leave_type"] = leave_type
    if exclude:
        filters["name"] = ["!=", exclude]
    return frappe.db.count("Leave Application", filters)


def remote_days(employee, start, end, exclude=None):
    filters = {"employee": employee, "from_date": ["<=", end], "to_date": [">=", start], "status": ["not in", ["Draft", "Rejected", "Cancelled"]], "docstatus": ["<", 2]}
    if exclude:
        filters["name"] = ["!=", exclude]
    if exclude is not None:
        rows = frappe.db.sql("""select from_date, to_date from `tabRemote Work Request`
            where employee=%s and from_date<=%s and to_date>=%s and docstatus<2
            and status not in ('Draft','Rejected','Cancelled') and name!=%s for update""",
            (employee, end, start, exclude), as_dict=True)
    else:
        rows = frappe.get_all("Remote Work Request", filters=filters, fields=["from_date", "to_date"])
    result = set()
    for row in rows:
        result |= working_days(employee, max(getdate(start), getdate(row.from_date)), min(getdate(end), getdate(row.to_date)))
    return result


def validate_monthly_limit(doc, method=None):
    settings = policy()
    half = doc.doctype == "Leave Application"
    if half:
        if not settings.get("custom_limit_half_days") or not doc.half_day or doc.leave_type != settings.custom_half_day_leave_type or doc.status not in ("Open", "Approved") or doc.docstatus == 2:
            return
    elif not settings.get("custom_limit_remote_work") or doc.status in ("Draft", "Rejected", "Cancelled") or doc.docstatus == 2:
        return
    # Serialize competing requests for one employee, including cross-month requests.
    frappe.db.sql("select name from `tabEmployee` where name=%s for update", doc.employee)
    if half:
        date = getdate(doc.half_day_date or doc.from_date)
        used = half_day_count(doc.employee, get_first_day(date), get_last_day(date), doc.leave_type, doc.name or "")
        if used + 1 > cint(settings.custom_half_day_monthly_limit):
            frappe.throw(f"Monthly half-day limit reached for {date:%Y-%m}. Pending requests also count.")
    else:
        requested = working_days(doc.employee, doc.from_date, doc.to_date)
        if not requested:
            frappe.throw("Select at least one working day for work from home.")
        existing = remote_days(doc.employee, get_first_day(doc.from_date), get_last_day(doc.to_date), doc.name or "")
        if requested & existing:
            frappe.throw("A pending or approved work-from-home request already covers these dates.")
        counts = Counter(day.strftime("%Y-%m") for day in requested | existing)
        if any(count > cint(settings.custom_remote_work_monthly_limit) for count in counts.values()):
            frappe.throw("Monthly work-from-home limit exceeded. Pending and approved working days count in each calendar month.")


def dashboard_summary(employee):
    from hrms.hr.doctype.leave_application.leave_application import get_leave_details
    settings = policy()
    start, end = get_first_day(today()), get_last_day(today())
    half_limit = cint(settings.get("custom_half_day_monthly_limit")) if settings.get("custom_limit_half_days") else None
    remote_limit = cint(settings.get("custom_remote_work_monthly_limit")) if settings.get("custom_limit_remote_work") else None
    half_used = half_day_count(employee, start, end, settings.get("custom_half_day_leave_type"))
    from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
    remote_used = None
    calendar = get_holiday_list_for_employee(employee, raise_exception=False)
    bounds = frappe.db.get_value("Holiday List", calendar, ["from_date", "to_date"], as_dict=True) if calendar else None
    if bounds and getdate(bounds.from_date) <= start and getdate(bounds.to_date) >= end:
        remote_used = len(remote_days(employee, start, end))
    return {
        "month": start.strftime("%Y-%m"),
        "balances": get_leave_details(employee, today())["leave_allocation"],
        "half_day": {"used": half_used, "limit": half_limit, "leave_type": settings.get("custom_half_day_leave_type")},
        "remote_work": {"used": remote_used, "limit": remote_limit},
    }
