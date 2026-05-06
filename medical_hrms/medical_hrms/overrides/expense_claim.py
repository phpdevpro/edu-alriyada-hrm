import frappe
from frappe import _

def validate_expense_claim(doc, method):
    # This hook applies to standard Expense Claim.
    # We evaluate total claimed amount to set required approver level (could be a custom field).
    if not frappe.db.has_column("Expense Claim", "custom_required_approval_level"):
        # Ensure we have the field first, or we can just run dynamic validations
        pass

    # Basic rules based on HR Workflow Design Document:
    # Total < AED 5,000 -> Direct Manager
    # Total > AED 5,000 -> Department Head
    # Total > AED 20,000 -> Finance Manager

    # Since Frappe's Expense Claim uses the standard `approval_status`,
    # we can add a check on submission or approval.
    
    total_claimed = doc.total_claimed_amount

    # If it's being approved
    if doc.approval_status == "Approved":
        user_roles = frappe.get_roles(frappe.session.user)
        
        if total_claimed > 20000:
            if "Finance Manager" not in user_roles and frappe.session.user != "Administrator":
                frappe.throw(_("Claims above AED 20,000 require Finance Manager approval."))
        elif total_claimed > 5000:
            if "Department Manager" not in user_roles and "Department Head" not in user_roles and frappe.session.user != "Administrator":
                frappe.throw(_("Claims above AED 5,000 require Department Head approval."))
        else:
            # Direct manager can approve (assuming Leave Approver or equivalent)
            pass
