import frappe


def _require_hr_access():
    if frappe.session.user == "Administrator" or set(frappe.get_roles()).intersection(
        {"HR User", "HR Manager", "System Manager"}
    ):
        return
    frappe.throw("You are not permitted to view the HR Dashboard.", frappe.PermissionError)


@frappe.whitelist()
def get_logged_in_user_details():
    _require_hr_access()
    user_email = frappe.session.user
    user = frappe.get_doc("User", user_email)

    role = "HR Manager" if "HR Manager" in frappe.get_roles(user_email) else "HR User"

    return {
        "status": "success",
        "user": {
            "full_name": user.full_name or user.first_name or "HR User",
            "email": user.email,
            "role": role,
        },
    }


@frappe.whitelist()
def get_hr_dashboard_stats():
    _require_hr_access()
    try:
        return {
            "status": "success",
            "stats": {
                "total_employees": frappe.db.count("Employee"),
                "pending_training_requests": frappe.db.count(
                    "Employee Training Request", {"status": ["like", "Pending%"]}
                ),
                "pending_allowance_requests": frappe.db.count(
                    "Children Medical Allowance Request", {"status": ["like", "Pending%"]}
                ),
                "expiring_medical_licenses": frappe.db.count(
                    "Employee Medical License", {"status": "Active"}
                ),
            },
        }
    except Exception as e:
        frappe.log_error(f"HR dashboard stats error: {e}", "HR Dashboard")
        return {
            "status": "error",
            "stats": {
                "total_employees": 0,
                "pending_training_requests": 0,
                "pending_allowance_requests": 0,
                "expiring_medical_licenses": 0,
            },
        }


@frappe.whitelist()
def get_hr_doctype_counts():
    _require_hr_access()
    doctypes = [
        "Permission Request",
        "Remote Work Request",
        "Leave Plan Request",
        "Leave Return Request",
        "Salary Certificate Request",
        "Pre Approved Overtime Request",
        "Employee Training Request",
        "Children Medical Allowance Request",
        "Company Car Request",
        "Contract Renewal Request",
        "Employee Data Update Request",
        "Employee Medical License",
        # "Jameah Ministry Code",
        # "Jameah Branch",
        # "Jameah Agency",
        # "Jameah Deanery",
        # "Jameah College",
        # "Jameah Academic Department",
        # "Jameah Facility",
    ]

    counts, pending = {}, {}
    for dt in doctypes:
        try:
            counts[dt] = frappe.db.count(dt)
            # Every request type names its waiting steps "Pending ..." (Pending HR, Pending Manager ...).
            pending[dt] = frappe.db.count(dt, {"status": ["like", "Pending%"]}) if frappe.get_meta(dt).has_field("status") else 0
        except Exception:
            counts[dt] = pending[dt] = 0

    return {"status": "success", "counts": counts, "pending": pending}


@frappe.whitelist()
def get_leave_overview():
    """The HR leave section: is each company ready for leave this year, the Sick Leave policy, and today's leave work."""
    _require_hr_access()
    from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
    from frappe.utils import getdate, today
    from hrms.hr.doctype.leave_application.leave_application import get_leave_approver
    from medical_hrms.setup_leave_defaults import KEY

    now = getdate(today())
    annual_types = frappe.get_all("Leave Type", filters={KEY: "annual"}, pluck="name")
    companies = []
    for company in sorted(set(frappe.get_all("Employee", filters={"status": "Active"}, pluck="company"))):
        employees = frappe.get_all("Employee", filters={"status": "Active", "company": company}, pluck="name")
        period = frappe.db.get_value("Leave Period", {"company": company, "is_active": 1, "from_date": ["<=", now], "to_date": [">=", now]},
            ["name", "from_date", "to_date"], as_dict=True)
        covered = 0
        for employee in employees:
            calendar = get_holiday_list_for_employee(employee, raise_exception=False)
            bounds = frappe.db.get_value("Holiday List", calendar, ["from_date", "to_date"], as_dict=True) if calendar else None
            covered += bool(bounds and getdate(bounds.from_date) <= now <= getdate(bounds.to_date))
        with_annual = set(frappe.get_all("Leave Allocation", pluck="employee", filters={
            "employee": ["in", employees or [""]], "leave_type": ["in", annual_types or [""]], "docstatus": 1,
            "from_date": ["<=", now], "to_date": [">=", now]}))
        companies.append({
            "company": company, "employees": len(employees), "period": period,
            "without_holiday_list": len(employees) - covered,
            "without_approver": sum(1 for employee in employees if not get_leave_approver(employee)),
            "without_annual_leave": len(set(employees) - with_annual),
        })
    return {
        "companies": companies,
        "sick_policy": frappe.db.get_value("Leave Policy", {KEY: "medical"}, ["name", "title", "docstatus"], as_dict=True),
        "counts": {
            "applications_waiting": frappe.db.count("Leave Application", {"status": "Open", "docstatus": 0}),
            "plans_waiting": frappe.db.count("Leave Plan Request", {"status": ["like", "Pending%"]}),
            "returns_waiting": frappe.db.count("Leave Return Request", {"status": ["like", "Pending%"]}),
            "on_leave_today": frappe.db.count("Leave Application", {"status": "Approved", "docstatus": 1, "from_date": ["<=", now], "to_date": [">=", now]}),
        },
        "today": now,
    }
