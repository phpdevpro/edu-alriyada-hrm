"""Keep employee self-service separate from administration workspaces."""

import json

import frappe


def execute():
    restrictions = {
        "HR": ("HR User", "HR Manager", "System Manager"),
        "Medical HRMS": ("HR User", "HR Manager", "System Manager"),
        "Payroll": ("HR Manager", "Payroll Manager", "Payroll User", "Accounts Manager", "Accounts User", "System Manager"),
    }
    for name, roles in restrictions.items():
        if not frappe.db.exists("Workspace", name):
            continue
        workspace = frappe.get_doc("Workspace", name)
        workspace.set("roles", [{"role": role} for role in roles if frappe.db.exists("Role", role)])
        workspace.save(ignore_permissions=True)

    name = "Employee Self Service"
    if not frappe.db.exists("Workspace", name):
        workspace = frappe.get_doc({
            "doctype": "Workspace", "name": name, "title": name, "label": name,
            "module": "Medical HRMS", "public": 1, "icon": "users",
            "roles": [{"role": "Employee"}, {"role": "System Manager"}],
            "content": json.dumps([
                {"id": "employee_heading", "type": "header", "data": {"text": "Employee Self Service", "col": 12}},
                {"id": "employee_dashboard", "type": "shortcut", "data": {"shortcut_name": "My Dashboard", "col": 4}},
            ]),
            "shortcuts": [{"label": "My Dashboard", "type": "Page", "link_to": "employee-dashboard"}],
        })
        workspace.insert(ignore_permissions=True)
    frappe.clear_cache()
