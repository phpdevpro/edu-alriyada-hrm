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
        "Return From Leave Request",
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

    counts = {}
    for dt in doctypes:
        try:
            counts[dt] = frappe.db.count(dt)
        except Exception:
            counts[dt] = 0

    return {"status": "success", "counts": counts}
