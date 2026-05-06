import frappe
from frappe import _
from frappe.utils import date_diff

def validate_employee_separation(doc, method):
    # Only evaluate during resignation
    if doc.resignation_letter_date and doc.leaving_date:
        notice_days = date_diff(doc.leaving_date, doc.resignation_letter_date)
        
        # Simple policy check: minimum 30 days notice
        if notice_days < 30:
            frappe.msgprint(_("Notice period is {0} days, which is less than the standard 30 days. Please ensure Manager/HR has waived the remaining notice period.").format(notice_days), alert=True)

def validate_training_request(doc, method):
    # Checks for Training Request
    if doc.estimated_cost:
        total_cost = doc.estimated_cost
        user_roles = frappe.get_roles(frappe.session.user)
        
        # Based on workflow rules
        if doc.status == "Approved":
            if total_cost > 50000 and "Finance Manager" not in user_roles and frappe.session.user != "Administrator":
                frappe.throw(_("Training programs exceeding AED 50,000 require Finance Manager approval."))
            elif total_cost > 30000 and "HR Manager" not in user_roles and "Finance Manager" not in user_roles and frappe.session.user != "Administrator":
                frappe.throw(_("Training programs exceeding AED 30,000 require HR Manager approval."))
            elif total_cost > 10000 and "Department Head" not in user_roles and "HR Manager" not in user_roles and frappe.session.user != "Administrator":
                frappe.throw(_("Training programs exceeding AED 10,000 require Department Head approval."))
