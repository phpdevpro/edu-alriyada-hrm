"""Explicit local test setup. Never run automatically during migration."""
from datetime import timedelta

import frappe
from frappe.utils import add_days, getdate, today
from medical_hrms.setup_leave_defaults import KEY, execute as setup_defaults
from medical_hrms.medical_leave import activate_year, medical_types


def execute():
    if frappe.local.site != "site1.local":
        frappe.throw("This opt-in demo setup is restricted to site1.local.")
    from medical_hrms.setup_hr_roles import execute as setup_roles
    from medical_hrms.monthly_leave_policy import setup as setup_limits
    setup_roles()
    setup_limits()
    setup_defaults()
    employee = frappe.db.get_value("Employee", {"user_id": "employee.demo@medicalcollege.local"}, "name")
    if not employee:
        frappe.throw("Create the demo employee first.")
    emp = frappe.get_doc("Employee", employee)
    hr = frappe.get_doc("User", "hr.manager.demo@medicalcollege.local")
    hr.enabled = 1
    hr.role_profile_name = "HR"
    hr.save(ignore_permissions=True)
    hr.add_roles("HR User", "HR Manager", "Leave Approver")

    department = frappe.db.get_value("Department", {"department_name": "Internal Medicine", "company": emp.company}, "name")
    if not department:
        department = frappe.get_doc({"doctype": "Department", "department_name": "Internal Medicine", "company": emp.company, "parent_department": "All Departments"}).insert(ignore_permissions=True).name
    year = getdate(today()).year
    start, end = getdate(f"{year}-01-01"), getdate(f"{year+1}-12-31")
    calendar_name = f"Medical HRMS Demo Weekends {year}-{year+1}"
    if not frappe.db.exists("Holiday List", calendar_name):
        holidays = [{"holiday_date": start + timedelta(days=i), "description": "Demo weekly rest", "weekly_off": 1}
            for i in range((end-start).days+1) if (start + timedelta(days=i)).weekday() in (4, 5)]
        frappe.get_doc({"doctype": "Holiday List", "holiday_list_name": calendar_name,
            "from_date": start, "to_date": end, "holidays": holidays}).insert(ignore_permissions=True)
    # Repair only these known-bad seed links; do not overwrite other employee data.
    frappe.db.set_value("Employee", employee, {"department": department, "holiday_list": calendar_name, "leave_approver": hr.name})
    frappe.clear_document_cache("Employee", employee)

    for name in medical_types().values():
        leave_type = frappe.get_doc("Leave Type", name)
        leave_type.include_holiday = 1
        leave_type.is_carry_forward = 0
        leave_type.is_earned_leave = 0
        leave_type.save(ignore_permissions=True)
    for name in frappe.get_all("Leave Policy", filters={KEY: ["in", ["annual_21", "annual_30", "medical"]], "docstatus": 0}, pluck="name"):
        policy = frappe.get_doc("Leave Policy", name)
        policy.submit()

    annual = frappe.db.get_value("Leave Type", {KEY: "annual"}, "name")
    settings = frappe.get_doc("HR Settings")
    settings.custom_limit_half_days = 1
    settings.custom_half_day_leave_type = annual
    settings.custom_half_day_monthly_limit = 2
    settings.custom_limit_remote_work = 1
    settings.custom_remote_work_monthly_limit = 3
    settings.save(ignore_permissions=True)

    period = frappe.db.get_value("Leave Period", {"company": emp.company, "from_date": ["<=", today()], "to_date": [">=", today()]}, "name")
    if not period:
        frappe.throw("No matching demo Leave Period found.")
    period_doc = frappe.get_doc("Leave Period", period)
    period_doc.is_active = 1
    period_doc.save(ignore_permissions=True)
    policy_name = frappe.db.get_value("Leave Policy", {KEY: "annual_21", "docstatus": 1}, "name")
    if not frappe.db.exists("Leave Policy Assignment", {"employee": employee, "docstatus": 1, "effective_from": ["<=", today()], "effective_to": [">=", today()]}):
        assignment = frappe.get_doc({"doctype": "Leave Policy Assignment", "employee": employee,
            "leave_policy": policy_name, "assignment_based_on": "Leave Period", "leave_period": period})
        assignment.insert(ignore_permissions=True)
        assignment.submit()
    if not frappe.db.exists("Leave Allocation", {"employee": employee, "leave_type": medical_types()["sick_full"], "docstatus": 1, "from_date": ["<=", today()], "to_date": [">=", today()]}):
        activate_year(employee, today())
    frappe.clear_cache()
    return {"employee": employee, "hr_user": hr.name, "holiday_calendar": calendar_name, "annual_policy": policy_name}
