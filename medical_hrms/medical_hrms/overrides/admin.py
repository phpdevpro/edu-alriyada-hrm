import frappe
from frappe import _

def validate_travel_request(doc, method):
    # This targets standard Frappe Travel Request
    cost = doc.total_estimated_cost or sum([item.estimated_cost for item in doc.get("costings", [])])
    
    if getattr(doc, 'approval_status', '') == "Approved":
        user_roles = frappe.get_roles(frappe.session.user)
        
        if cost > 50000:
            if "Finance Manager" not in user_roles and frappe.session.user != "Administrator":
                frappe.throw(_("Trips over AED 50,000 require Finance Manager approval."))
        elif cost > 15000:
            if "Department Head" not in user_roles and frappe.session.user != "Administrator":
                frappe.throw(_("Trips over AED 15,000 require Department Head approval."))
                
def validate_company_car(doc, method):
    # Custom business rules from document
    if doc.status == "Approved":
        user_roles = frappe.get_roles(frappe.session.user)
        
        if "Finance Manager" not in user_roles and frappe.session.user != "Administrator":
            frappe.throw(_("Company Car allocation requires final Finance approval based on fleet cap."))
