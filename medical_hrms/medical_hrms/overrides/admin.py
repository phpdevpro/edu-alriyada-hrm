import frappe
from frappe import _
from frappe.utils import flt

from medical_hrms.medical_hrms.overrides import FINANCE_APPROVER_ROLES, has_any_role


def validate_travel_request(doc, method):
    # Standard HRMS Travel Request has no approval_status or estimated-cost
    # field; its cost lives on the costings rows and approval is submission.
    if method != "before_submit":
        return
    cost = sum(flt(item.total_amount) for item in doc.get("costings", []))

    if cost > 50000:
        if not has_any_role(*FINANCE_APPROVER_ROLES):
            frappe.throw(_("Trips over AED 50,000 require Finance approval."))
    elif cost > 15000:
        if not has_any_role("Department Head"):
            frappe.throw(_("Trips over AED 15,000 require Department Head approval."))


def validate_company_car(doc, method):
    # Custom business rules from document
    if doc.status == "Approved" and doc.has_value_changed("status"):
        if not has_any_role(*FINANCE_APPROVER_ROLES):
            frappe.throw(_("Company Car allocation requires final Finance approval based on fleet cap."))
