import frappe


def execute():
    workspace_name = "Medical HRMS"
    if not frappe.db.exists("Workspace", workspace_name):
        raise frappe.ValidationError(f"Workspace not found: {workspace_name}")

    workspace = frappe.get_doc("Workspace", workspace_name)
    workspace.public = 1
    workspace.is_hidden = 0
    workspace.for_user = ""
    workspace.set("roles", [])

    for role in ("HR User", "HR Manager", "System Manager"):
        workspace.append("roles", {"role": role})

    workspace.save(ignore_permissions=True)
    frappe.db.commit()
    print("Medical HRMS workspace access restricted to HR roles.")
