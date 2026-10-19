import frappe
from frappe import _

def validate_education_allowance(doc, method):
    # 1. Check max 3 children
    # Count how many distinct children have claims for this academic year
    existing_claims = frappe.get_all(
        "Children Medical Allowance Request",
        filters={
            "employee": doc.employee,
            "academic_year": doc.academic_year,
            "name": ("!=", doc.name),
            "status": ("in", ["Approved", "Pending HR Review", "Pending HR Director", "Pending Finance"])
        },
        fields=["child_name", "approved_amount"]
    )
    
    unique_children = set([claim.child_name for claim in existing_claims])
    if doc.child_name not in unique_children and len(unique_children) >= 3:
        frappe.throw(_("Employee has reached the maximum limit of 3 children for the education allowance this academic year."))

    # 2. Per-child cap. Grade-based caps are not defined yet, so Employee
    # Grade is not required: requiring it blocked every claim (even drafts)
    # without the grade changing the outcome.
    max_cap = 30000.0
    
    # Sum up existing approved amounts for THIS child
    child_claims = [claim.approved_amount for claim in existing_claims if claim.child_name == doc.child_name and claim.approved_amount]
    total_approved_this_child = sum(child_claims)
    
    if doc.approved_amount:
        if (total_approved_this_child + doc.approved_amount) > max_cap:
            frappe.throw(_("Total approved amount for {0} exceeds the maximum cap of {1}.").format(doc.child_name, max_cap))
