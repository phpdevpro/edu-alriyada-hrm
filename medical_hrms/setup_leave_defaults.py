"""Editable starter records, never employee allocations or automatic approvals.

Seed keys survive title/name changes. Existing business settings are preserved.
Medical policy requires explicit HR activation; migration never opens sick years.
"""
import frappe
from frappe.utils import getdate, today

KEY = "custom_medical_hrms_default_key"
NOTES = "custom_medical_hrms_policy_notes"
GUIDANCE = {
    "medical": "MEDICAL LEAVE ONLY: sequential sick-pay stages, separate from annual leave. HR must submit this policy and use Activate Medical Leave Year on the HR dashboard, starting on the first illness date. Do not assign through the annual Leave Control Panel. The unpaid stage is enforced by medical checks, not a Leave Allocation.",
    "annual": "Annual leave only. Medical/sick leave is a separate entitlement and must not be deducted from this balance. HR must confirm carry-forward and holiday-counting rules.",
    "sick_full": "Separate medical/sick entitlement: first 30 days at full pay within the sick-leave year starting on the first sick-leave date. Do not allocate this from annual leave. Tier progression requires HR verification.",
    "sick_partial": "Separate medical/sick entitlement: following 60 days at 75% pay in the same sick-leave year. HR must verify prior sick usage and payroll configuration before use; this category alone does not automate progression.",
    "sick_unpaid": "Separate medical/sick entitlement: following 30 days unpaid in the same sick-leave year. HR must verify prior sick usage; not a separate annually renewable allowance.",
    "unpaid": "General unpaid leave by agreement. Not annual or medical leave and not a casual-leave entitlement.",
    "annual_21": "ANNUAL LEAVE ONLY: 21 days. Starter for employees below five consecutive years with the employer where Saudi Labour Law applies. Medical/sick leave is separate. Casual leave is not included. HR must confirm eligibility before assigning.",
    "annual_30": "ANNUAL LEAVE ONLY: 30 days. Starter for employees with five or more consecutive years with the employer where Saudi Labour Law applies. Medical/sick leave is separate. Casual leave is not included. HR must confirm eligibility before assigning.",
}


def _ensure_marker_fields():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields({doctype: [{
        "fieldname": KEY, "label": "Medical HRMS Default Key", "fieldtype": "Data",
        "read_only": 1, "hidden": 1, "no_copy": 1,
    }, {"fieldname": NOTES, "label": "Leave Scope and HR Review Notes", "fieldtype": "Small Text",
        "insert_after": "title" if doctype == "Leave Policy" else "leave_type_name",
    }] for doctype in ("Leave Type", "Leave Policy")}, update=True)


def clarify_defaults():
    """Fill explanatory notes only when HR has not written their own."""
    for doctype in ("Leave Type", "Leave Policy"):
        for row in frappe.get_all(doctype, filters={KEY: ["in", list(GUIDANCE)]}, fields=["name", KEY, NOTES]):
            if not row.get(NOTES):
                frappe.db.set_value(doctype, row.name, NOTES, GUIDANCE[row.get(KEY)])


def _leave_type(key, label, aliases=(), **settings):
    found = frappe.db.get_value("Leave Type", {KEY: key}, "name")
    if found:
        return found
    for candidate in (label, *aliases):
        if frappe.db.exists("Leave Type", candidate):
            # Add only bookkeeping, not changes to HR's pay/carry-forward rules.
            frappe.db.set_value("Leave Type", candidate, KEY, key, update_modified=False)
            return candidate
    doc = frappe.get_doc({"doctype": "Leave Type", "leave_type_name": label,
        KEY: key, "max_leaves_allowed": 0, "allow_negative": 0,
        "allow_over_allocation": 0, "allow_encashment": 0, **settings})
    doc.insert(ignore_permissions=True)
    return doc.name


def _policy(key, title, annual_type, days):
    if frappe.db.exists("Leave Policy", {KEY: key}):
        return
    existing = frappe.db.get_value("Leave Policy", {"title": title}, "name")
    if existing:
        frappe.db.set_value("Leave Policy", existing, KEY, key, update_modified=False)
        return
    maximum = frappe.db.get_value("Leave Type", annual_type, "max_leaves_allowed") or 0
    if maximum and maximum < days:
        print(f"Skipped {title}: existing {annual_type} allocation cap is {maximum}; HR must review it.")
        return
    frappe.get_doc({"doctype": "Leave Policy", KEY: key, "title": title,
        "leave_policy_details": [{"leave_type": annual_type, "annual_allocation": days}],
    }).insert(ignore_permissions=True)  # Intentionally remains a draft.


def execute():
    _ensure_marker_fields()
    annual = _leave_type("annual", "Annual Leave", aliases=("Annual",), is_carry_forward=1)
    _leave_type("sick_full", "Sick Leave - Full Pay", include_holiday=1)
    _leave_type("sick_partial", "Sick Leave - 75 Percent Pay", is_ppl=1, fraction_of_daily_salary_per_leave=0.75, include_holiday=1)
    _leave_type("sick_unpaid", "Sick Leave - Unpaid", is_lwp=1, include_holiday=1)
    _leave_type("unpaid", "Unpaid Leave", aliases=("Leave Without Pay",), is_lwp=1)
    _policy("annual_21", "Medical HRMS - Annual Leave 21 Days (HR Review)", annual, 21)
    _policy("annual_30", "Medical HRMS - Annual Leave 30 Days (HR Review)", annual, 30)
    if not frappe.db.exists("Leave Policy", {KEY: "medical"}):
        frappe.get_doc({"doctype": "Leave Policy", "title": "Medical HRMS - Medical Leave (Separate Sick Year)", KEY: "medical",
            "leave_policy_details": [{"leave_type": frappe.db.get_value("Leave Type", {KEY: key}, "name"), "annual_allocation": days}
                for key, days in (("sick_full", 30), ("sick_partial", 60), ("sick_unpaid", 30))],
        }).insert(ignore_permissions=True)
    clarify_defaults()

    year = getdate(today()).year
    start, end = f"{year}-01-01", f"{year}-12-31"
    for company in frappe.get_all("Company", pluck="name"):
        # Do not impose a calendar-year period over an existing fiscal/anniversary period.
        if frappe.db.exists("Leave Period", {"company": company, "from_date": ["<=", end], "to_date": [">=", start]}):
            continue
        frappe.get_doc({"doctype": "Leave Period", "company": company,
            "from_date": start, "to_date": end, "is_active": 0,
        }).insert(ignore_permissions=True)
    print("Leave starter records ready. HR must review policies and periods before assignment.")
