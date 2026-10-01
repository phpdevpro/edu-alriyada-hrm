"""Explicit, rollback-only integration checks for the local demo setup."""
from datetime import timedelta
from unittest.mock import patch
from contextlib import ExitStack

import frappe
from frappe.utils import getdate, today
from medical_hrms.self_service import save_request, request_details
from medical_hrms.medical_leave import medical_types
from medical_hrms.setup_leave_defaults import KEY

EMPLOYEE_USER = "employee.demo@medicalcollege.local"
HR_USER = "hr.manager.demo@medicalcollege.local"


def expect_rejected(action):
    try:
        action()
    except frappe.ValidationError:
        return
    except frappe.PermissionError:
        return
    raise AssertionError("Operation unexpectedly allowed")


def execute():
    if frappe.local.site != "site1.local":
        frappe.throw("Local test site only.")
    original_user = frappe.session.user
    employee = frappe.db.get_value("Employee", {"user_id": EMPLOYEE_USER}, "name")
    annual = frappe.db.get_value("Leave Type", {KEY: "annual"}, "name")
    start = getdate(today())
    workdays = [start + timedelta(days=i) for i in range(1, 15) if (start+timedelta(days=i)).weekday() not in (4, 5)]
    days = [day for day in workdays if day.month == workdays[0].month][:4]
    if len(days) < 4:
        frappe.throw("Integration tests need four upcoming demo working days in one allocation month.")
    results = []

    def leave(date, half=False):
        return save_request("Leave Application", {"leave_type": annual, "from_date": str(date), "to_date": str(date),
            "half_day": int(half), "half_day_date": str(date) if half else None, "description": "Rollback integration test"}, True)

    def annual_approval():
        result = leave(days[0])
        assert result["status"] == "Open"
        assert request_details("Leave Application", result["name"])["status"] == "Open"
        frappe.set_user(HR_USER)
        doc = frappe.get_doc("Leave Application", result["name"])
        doc.status = "Approved"
        doc.submit()
        assert doc.docstatus == 1 and doc.total_leave_days == 1

    def half_day_limit():
        leave(days[0], True)
        leave(days[1], True)
        expect_rejected(lambda: leave(days[2], True))

    def remote_limit():
        values = {"from_date": str(days[0]), "to_date": str(days[2]), "location": "Home", "work_plan": "Rollback test"}
        save_request("Remote Work Request", values, True)
        expect_rejected(lambda: save_request("Remote Work Request", {**values, "from_date": str(days[3]), "to_date": str(days[3])}, True))

    def medical_request():
        kind = medical_types()["sick_full"]
        date = frappe.db.get_value("Leave Allocation", {"employee": employee, "leave_type": kind, "docstatus": 1}, "from_date")
        result = save_request("Leave Application", {"leave_type": kind, "from_date": str(date), "to_date": str(date), "description": "Rollback medical test"}, True)
        assert result["status"] == "Open"
        frappe.set_user(HR_USER)
        doc = frappe.get_doc("Leave Application", result["name"])
        doc.status = "Approved"
        doc.submit()

    def medical_stage_rejected():
        kind = medical_types()["sick_partial"]
        expect_rejected(lambda: save_request("Leave Application", {"leave_type": kind, "from_date": str(days[0]), "to_date": str(days[0]), "description": "Invalid stage test"}, True))

    def employee_security():
        doc = frappe.get_doc("Employee", employee)
        assert not frappe.has_permission("Employee", "write", doc=doc)
        expect_rejected(lambda: save_request("Permission Request", {"employee": "someone-else", "status": "Approved"}, True))
        expect_rejected(lambda: request_details("Leave Application", "not-owned"))
        from medical_hrms.medical_hrms.page.hr_dashboard.hr_dashboard import get_hr_dashboard_stats
        expect_rejected(get_hr_dashboard_stats)

    from hrms.hr.doctype.leave_application.leave_application import LeaveApplication
    try:
        with ExitStack() as stack:
            # Do not emit notifications or outbound mail during test requests.
            for method in ("notify_approver", "notify_leave_approver", "notify_employee", "notify_approval_status", "publish_update"):
                stack.enter_context(patch.object(LeaveApplication, method))
            for test in (annual_approval, half_day_limit, remote_limit, medical_request, medical_stage_rejected, employee_security):
                frappe.db.savepoint("local_leave_check")
                try:
                    frappe.set_user(EMPLOYEE_USER)
                    test()
                    results.append({"test": test.__name__, "result": "PASS"})
                except Exception as error:
                    results.append({"test": test.__name__, "result": "FAIL", "error": str(error)})
                finally:
                    frappe.db.rollback(save_point="local_leave_check")
    finally:
        frappe.set_user(original_user)
    return results
