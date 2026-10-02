"""HR-activated sick years and sequential medical-pay-stage validation."""
import frappe
from frappe.utils import add_days, add_years, flt, getdate
from medical_hrms.setup_leave_defaults import KEY

STAGES = ("sick_full", "sick_partial", "sick_unpaid")


def medical_types():
    return {row.get(KEY): row.name for row in frappe.get_all("Leave Type", filters={KEY: ["in", STAGES]}, fields=["name", KEY])}


def medical_policy():
    name = frappe.db.get_value("Leave Policy", {KEY: "medical", "docstatus": 1}, "name")
    if not name:
        frappe.throw("HR must review and submit the separate Medical Leave policy first.")
    return frappe.get_doc("Leave Policy", name)


def quotas(policy, types):
    amounts = {row.leave_type: flt(row.annual_allocation) for row in policy.leave_policy_details}
    if len(types) != 3 or set(amounts) != set(types.values()) or any(amounts[name] <= 0 for name in types.values()):
        frappe.throw("The medical policy must contain exactly the three medical stages with positive day limits.")
    return [amounts[types[stage]] for stage in STAGES]


def prevent_annual_assignment(doc, method=None):
    if frappe.db.get_value("Leave Policy", doc.leave_policy, KEY) == "medical":
        frappe.throw("Use HR Dashboard → Activate Medical Leave Year. Medical leave must not use an annual policy assignment.")


@frappe.whitelist()
def activate_year(employee, first_sick_date):
    if frappe.session.user != "Administrator" and not set(frappe.get_roles()).intersection({"HR Manager", "System Manager"}):
        frappe.throw("Only HR Manager or System Manager can activate a medical leave year.", frappe.PermissionError)
    emp = frappe.get_doc("Employee", employee)
    emp.check_permission("read")
    start = getdate(first_sick_date)
    end = getdate(add_days(add_years(start, 1), -1))
    if emp.status != "Active" or start < getdate(emp.date_of_joining):
        frappe.throw("Choose an active employee and a first illness date on or after joining.")
    policy = medical_policy()
    types = medical_types()
    limits = quotas(policy, types)
    if frappe.db.get_single_value("Payroll Settings", "payroll_based_on") == "Attendance":
        frappe.throw("Attendance-based partial-pay calculations need payroll review before activating this medical policy. No payroll settings were changed.")
    for stage in STAGES:
        leave_type = frappe.get_doc("Leave Type", types[stage])
        if not leave_type.include_holiday or leave_type.is_carry_forward or leave_type.is_earned_leave:
            frappe.throw("For medical stages, HR must include holidays and disable carry-forward/earned leave on each Leave Type before activation.")
        if stage == "sick_full" and (leave_type.is_lwp or leave_type.is_ppl):
            frappe.throw("The first medical stage must be full pay.")
        if stage == "sick_partial" and (not leave_type.is_ppl or leave_type.is_lwp or flt(leave_type.fraction_of_daily_salary_per_leave) != 0.75):
            frappe.throw("The second medical stage must be configured for 75% pay.")
        if stage == "sick_unpaid" and not leave_type.is_lwp:
            frappe.throw("The last medical stage must be leave without pay.")
    frappe.db.sql("select name from `tabEmployee` where name=%s for update", employee)
    existing = frappe.db.sql("""select name from `tabLeave Allocation` where employee=%s
        and leave_type in %s and docstatus<2 and from_date<=%s and to_date>=%s for update""",
        (employee, tuple(types.values()), end, start))
    if existing:
        frappe.throw("An overlapping medical allocation exists. HR must review it; no duplicate allocations were created.")
    allocations = []
    for stage, days in zip(STAGES[:2], limits[:2]):
        doc = frappe.get_doc({"doctype": "Leave Allocation", "employee": employee,
            "leave_type": types[stage], "from_date": start, "to_date": end,
            "new_leaves_allocated": days, "leave_policy": policy.name, "carry_forward": 0})
        doc.insert()
        doc.submit()
        doc.add_comment("Comment", f"Medical year activated by {frappe.session.user}; HR-confirmed first sick date: {start}.")
        allocations.append(doc.name)
    return {"from_date": start, "to_date": end, "allocations": allocations}


def check_stage_sequence(rows, limits):
    """Rows in date order; each request must stay inside one pay stage."""
    used = 0.0
    boundaries = [limits[0], limits[0] + limits[1], sum(limits)]
    last_end = None
    for row in rows:
        start, end = getdate(row["from_date"]), getdate(row["to_date"])
        days = flt(row["days"])
        if last_end and start <= last_end:
            raise ValueError("Medical leave requests overlap.")
        if days <= 0 or days > (end - start).days + 1:
            raise ValueError("Invalid medical leave duration.")
        expected = next((i for i, boundary in enumerate(boundaries) if used < boundary), None)
        if expected is None or row["stage"] != expected or used + days > boundaries[expected]:
            raise ValueError("Medical leave must use full pay, then 75% pay, then unpaid leave in order. Split requests at a pay-stage boundary and ask HR to review dependent requests after changes.")
        used += days
        last_end = end


def validate_medical_leave(doc, method=None):
    types = medical_types()
    if doc.leave_type not in types.values():
        return
    frappe.db.sql("select name from `tabEmployee` where name=%s for update", doc.employee)
    windows = frappe.db.sql("""select from_date, to_date, leave_policy from `tabLeave Allocation`
        where employee=%s and leave_type=%s and docstatus=1
        and from_date<=%s and to_date>=%s for update""",
        (doc.employee, types.get("sick_full"), doc.from_date, doc.to_date), as_dict=True)
    if len(windows) != 1:
        frappe.throw("HR must activate a medical leave year covering this entire request. Split requests crossing sick-year boundaries.")
    window = windows[0]
    policy = frappe.get_doc("Leave Policy", window.leave_policy) if window.leave_policy else None
    if not policy or policy.get(KEY) != "medical" or policy.docstatus != 1:
        frappe.throw("Medical allocation must reference the submitted Medical Leave policy.")
    limits = quotas(policy, types)
    stored = frappe.db.sql("""select name, leave_type, from_date, to_date, total_leave_days from `tabLeave Application`
        where employee=%s and leave_type in %s and docstatus<2
        and status in ('Open','Approved') and name!=%s
        and from_date<=%s and to_date>=%s order by from_date for update""",
        (doc.employee, tuple(types.values()), doc.name or "", window.to_date, window.from_date), as_dict=True)
    stages = {types[key]: i for i, key in enumerate(STAGES)}
    rows = [{"from_date": row.from_date, "to_date": row.to_date, "days": row.total_leave_days, "stage": stages[row.leave_type]} for row in stored]
    if method != "before_cancel" and doc.docstatus != 2 and doc.status in ("Open", "Approved"):
        rows.append({"from_date": doc.from_date, "to_date": doc.to_date, "days": doc.total_leave_days, "stage": stages[doc.leave_type]})
    rows.sort(key=lambda row: getdate(row["from_date"]))
    if rows and getdate(rows[0]["from_date"]) != getdate(window.from_date):
        frappe.throw("The first medical request must begin on the HR-confirmed first illness date. Ask HR to review the medical year before changing that date.")
    try:
        check_stage_sequence(rows, limits)
    except ValueError as error:
        frappe.throw(str(error))
