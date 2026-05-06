import frappe
from frappe.desk.desktop import get_workspace_sidebar_items


def _ensure_user(email: str, first_name: str, roles: list[str]):
    frappe.flags.in_test = True

    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
    else:
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": first_name,
                "send_welcome_email": 0,
                "enabled": 1,
                "user_type": "System User",
            }
        )
        user.insert(ignore_permissions=True)

    current_roles = {d.role for d in user.roles}
    for role in roles:
        if role not in current_roles:
            user.append("roles", {"role": role})

    user.enabled = 1
    user.user_type = "System User"
    user.save(ignore_permissions=True)


def _workspace_visible_for(user_email: str, workspace_name: str = "Medical HRMS") -> bool:
    frappe.set_user(user_email)
    sidebar = get_workspace_sidebar_items()
    pages = sidebar.get("pages", [])
    return any(p.get("name") == workspace_name for p in pages)


def _create_demo_training_request(employee_name: str) -> str:
    doc = frappe.get_doc(
        {
            "doctype": "Employee Training Request",
            "employee": employee_name,
            "course_details": "Demo Leadership Program",
            "provider": "Demo Academy",
            "estimated_cost": 2500,
            "business_benefit": "Improves team management and service quality",
            "status": "Draft",
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _move_request_status(request_name: str, status: str):
    doc = frappe.get_doc("Employee Training Request", request_name)
    doc.status = status
    doc.save(ignore_permissions=True)


def execute():
    frappe.set_user("Administrator")

    hr_user = "hr.user.demo@medicalcollege.local"
    hr_manager = "hr.manager.demo@medicalcollege.local"
    finance_user = "accounts.manager.demo@medicalcollege.local"
    employee_user = "employee.demo@medicalcollege.local"

    _ensure_user(hr_user, "HR User Demo", ["HR User"])
    _ensure_user(hr_manager, "HR Manager Demo", ["HR Manager"])
    _ensure_user(finance_user, "Accounts Manager Demo", ["Accounts Manager"])
    _ensure_user(employee_user, "Employee Demo", ["Employee"])

    ws_visible_hr_user = _workspace_visible_for(hr_user)
    ws_visible_hr_manager = _workspace_visible_for(hr_manager)
    ws_visible_finance = _workspace_visible_for(finance_user)
    ws_visible_employee = _workspace_visible_for(employee_user)

    frappe.set_user("Administrator")
    employee_name = frappe.db.get_value("Employee", {}, "name")
    if not employee_name:
        raise frappe.ValidationError("No Employee found for demo flow.")

    request_name = _create_demo_training_request(employee_name)
    _move_request_status(request_name, "Pending HR")
    _move_request_status(request_name, "Pending Finance")

    frappe.set_user(finance_user)
    finance_can_read = frappe.has_permission("Employee Training Request", ptype="read", doc=request_name)

    frappe.set_user("Administrator")
    print("HRM Demo Verification")
    print("---------------------")
    print(f"HR workspace visible to HR User: {ws_visible_hr_user}")
    print(f"HR workspace visible to HR Manager: {ws_visible_hr_manager}")
    print(f"HR workspace visible to Accounts Manager: {ws_visible_finance}")
    print(f"HR workspace visible to Employee-only user: {ws_visible_employee}")
    print(f"Demo request created: {request_name}")
    print("Request status path: Draft -> Pending HR -> Pending Finance")
    print(f"Finance can read request at Pending Finance: {finance_can_read}")

    return {
        "workspace_visibility": {
            "hr_user": ws_visible_hr_user,
            "hr_manager": ws_visible_hr_manager,
            "accounts_manager": ws_visible_finance,
            "employee_only": ws_visible_employee,
        },
        "demo_request": {
            "doctype": "Employee Training Request",
            "name": request_name,
            "status": "Pending Finance",
            "finance_can_read": bool(finance_can_read),
        },
        "demo_users": [hr_user, hr_manager, finance_user, employee_user],
    }
