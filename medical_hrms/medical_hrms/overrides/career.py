import frappe
from frappe import _
from frappe.utils import date_diff

from medical_hrms.medical_hrms.overrides import FINANCE_APPROVER_ROLES, has_any_role

def validate_employee_separation(doc, method):
    # Only evaluate during resignation
    if doc.resignation_letter_date and doc.leaving_date:
        notice_days = date_diff(doc.leaving_date, doc.resignation_letter_date)
        
        # Simple policy check: minimum 30 days notice
        if notice_days < 30:
            frappe.msgprint(_("Notice period is {0} days, which is less than the standard 30 days. Please ensure Manager/HR has waived the remaining notice period.").format(notice_days), alert=True)

def validate_training_request(doc, method):
    # Checks for Training Request, only when it is being approved
    if not doc.estimated_cost or doc.status != "Approved" or not doc.has_value_changed("status"):
        return
    total_cost = doc.estimated_cost

    # Based on workflow rules
    if total_cost > 50000 and not has_any_role(*FINANCE_APPROVER_ROLES):
        frappe.throw(_("Training programs exceeding AED 50,000 require Finance approval."))
    elif total_cost > 30000 and not has_any_role("HR Manager", *FINANCE_APPROVER_ROLES):
        frappe.throw(_("Training programs exceeding AED 30,000 require HR Manager approval."))
    elif total_cost > 10000 and not has_any_role("Department Head", "HR Manager", *FINANCE_APPROVER_ROLES):
        frappe.throw(_("Training programs exceeding AED 10,000 require Department Head approval."))
