import json

import frappe


def execute():
    workspace_name = "Medical HRMS"
    if not frappe.db.exists("Workspace", workspace_name):
        raise frappe.ValidationError(f"Workspace not found: {workspace_name}")

    doc = frappe.get_doc("Workspace", workspace_name)
    doc.title = "Medical HRMS"
    doc.label = "Medical HRMS"
    doc.icon = "heart"
    doc.category = "Modules"
    doc.module = "Medical Hrms"
    doc.public = 1
    doc.hide_custom = 1
    doc.set("roles", [])
    for role in ("HR User", "HR Manager", "System Manager"):
        doc.append("roles", {"role": role})

    doc.content = json.dumps(
        [
            {
                "id": "intro_h",
                "type": "header",
                "data": {"text": '<span class="h3"><b>Medical HRMS - Administration Panel</b></span>', "col": 12},
            },
            {
                "id": "intro_p",
                "type": "paragraph",
                "data": {
                    "text": "Centralized HR hub for employee services, approvals, compliance, and HR-finance handoffs.",
                    "col": 12,
                },
            },
            {"id": "card_hr", "type": "card", "data": {"card_name": "HR Dashboard", "col": 4}},
            {"id": "card_es", "type": "card", "data": {"card_name": "Employee Services", "col": 4}},
            {"id": "card_ta", "type": "card", "data": {"card_name": "Time & Attendance", "col": 4}},
            {"id": "card_fa", "type": "card", "data": {"card_name": "Financial & Admin", "col": 4}},
            {"id": "card_cc", "type": "card", "data": {"card_name": "Career & Compliance", "col": 4}},
        ]
    )

    doc.set("shortcuts", [])
    doc.set("links", [])

    doc.append("links", {"label": "HR Dashboard", "type": "Card Break"})
    doc.append("links", {"label": "HR Dashboard", "type": "Link", "link_type": "Page", "link_to": "hr-dashboard"})

    doc.append("links", {"label": "Employee Services", "type": "Card Break"})
    for item in ["Permission Request", "Remote Work Request", "Leave Plan Request", "Return from Leave Request", "Salary Certificate Request"]:
        doc.append("links", {"label": item, "type": "Link", "link_type": "DocType", "link_to": item})

    doc.append("links", {"label": "Time & Attendance", "type": "Card Break"})
    for item in ["Leave Application", "Attendance Request", "Pre Approved Overtime Request"]:
        doc.append("links", {"label": item, "type": "Link", "link_type": "DocType", "link_to": item})

    doc.append("links", {"label": "Financial & Admin", "type": "Card Break"})
    for label, link_to in [
        ("Expense Claim", "Expense Claim"),
        ("Travel Request", "Travel Request"),
        ("Children Medical Allowance Request", "Children Medical Allowance Request"),
        ("Company Car Request", "Company Car Request"),
    ]:
        doc.append("links", {"label": label, "type": "Link", "link_type": "DocType", "link_to": link_to})

    doc.append("links", {"label": "Career & Compliance", "type": "Card Break"})
    for item in [
        "Contract Renewal Request",
        "Employee Training Request",
        "Employee Separation",
        "Full and Final Statement",
        "Employee Data Update Request",
        "Employee Medical License",
        "Employee",
    ]:
        doc.append("links", {"label": item, "type": "Link", "link_type": "DocType", "link_to": item})

    for row in doc.links:
        if row.type == "Card Break":
            row.link_type = None
            row.link_to = None

    doc.save(ignore_permissions=True)
    frappe.db.commit()
    print("Medical HRMS workspace layout updated successfully.")
