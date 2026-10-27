import frappe
from frappe import _

from medical_hrms.medical_hrms.overrides import FINANCE_APPROVER_ROLES, has_any_role

def validate_expense_claim(doc, method):
    # This hook applies to standard Expense Claim.
    # We evaluate total claimed amount to set required approver level (could be a custom field).
    if not frappe.db.has_column("Expense Claim", "custom_required_approval_level"):
        # Ensure we have the field first, or we can just run dynamic validations
        pass

    # Basic rules based on HR Workflow Design Document:
    # Total < SAR 5,000 -> Direct Manager
    # Total > SAR 5,000 -> Department Head
    # Total > SAR 20,000 -> Finance Manager

    # Since Frappe's Expense Claim uses the standard `approval_status`,
    # we can add a check on submission or approval.
    
    total_claimed = doc.total_claimed_amount

    # If it's being approved
    if doc.approval_status == "Approved":
        if total_claimed > 20000:
            if not has_any_role(*FINANCE_APPROVER_ROLES):
                frappe.throw(_("Claims above SAR 20,000 require Finance approval."))
        elif total_claimed > 5000:
            if not has_any_role("Department Head", *FINANCE_APPROVER_ROLES):
                frappe.throw(_("Claims above SAR 5,000 require Department Head approval."))
        else:
            # Direct manager can approve (assuming Leave Approver or equivalent)
            pass
