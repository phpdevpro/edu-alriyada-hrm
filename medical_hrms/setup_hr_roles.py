import frappe


HR_ROLES = ("HR User", "HR Manager")


def execute():
    """Ensure enabled HR Desk roles and an HR role profile, preserving existing roles."""
    for role_name in HR_ROLES:
        if frappe.db.exists("Role", role_name):
            role = frappe.get_doc("Role", role_name)
            if role.disabled or not role.desk_access:
                role.disabled = 0
                role.desk_access = 1
                role.save(ignore_permissions=True)
        else:
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "disabled": 0,
                "desk_access": 1,
            }).insert(ignore_permissions=True)

    if frappe.db.exists("Role Profile", "HR"):
        profile = frappe.get_doc("Role Profile", "HR")
    else:
        profile = frappe.new_doc("Role Profile")
        profile.role_profile = "HR"

    existing_roles = {row.role for row in profile.roles}
    missing_roles = [role for role in HR_ROLES if role not in existing_roles]
    for role in missing_roles:
        profile.append("roles", {"role": role})
    if profile.is_new() or missing_roles:
        profile.save(ignore_permissions=True)

    frappe.clear_cache()
    print("HR User and HR Manager enabled; HR Role Profile configured.")
