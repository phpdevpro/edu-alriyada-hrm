import frappe
from frappe.desk.doctype.notification_settings.notification_settings import create_notification_settings


def execute(user="hr@gmail.com"):
	create_notification_settings(user)
	frappe.db.commit()
	print(f"Notification Settings ensured for: {user}")
