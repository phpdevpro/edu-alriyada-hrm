import frappe


def _add_role(user_doc, role_name: str):
    existing = {d.role for d in user_doc.roles}
    if role_name not in existing:
        user_doc.append("roles", {"role": role_name})


def execute(user_email: str, access_level: str = "hr_user"):
    if not user_email:
        raise frappe.ValidationError("user_email is required")

    if not frappe.db.exists("User", user_email):
        raise frappe.ValidationError(f"User not found: {user_email}")

    user_doc = frappe.get_doc("User", user_email)
    user_doc.enabled = 1
    user_doc.user_type = "System User"

    _add_role(user_doc, "HR User")

    if access_level == "hr_manager":
        _add_role(user_doc, "HR Manager")

    user_doc.save(ignore_permissions=True)
    frappe.db.commit()
    print(f"HR login access granted for {user_email} ({access_level}).")
