import json

import frappe


DOCTYPE = "Return from Leave Request"
SAFE_SORT_FIELDS = {"modified", "creation", "name", "employee", "actual_return_date", "status"}
SAFE_SORT_ORDERS = {"asc", "desc"}


def _has_restricted_sql(value):
	if not value or not isinstance(value, str):
		return False
	low = value.lower()
	return any(token in low for token in ("(", ")", "select ", " from ", " ifnull", " coalesce", " concat", "case "))


def _sanitize_list_view_settings():
	rows = frappe.get_all(
		"List View Settings",
		filters={"doc_type": DOCTYPE},
		fields=["name", "user", "sort_by", "sort_order", "filters"],
	)

	updated = 0
	for row in rows:
		changed = False
		sort_by = (row.sort_by or "").strip()
		sort_order = (row.sort_order or "desc").strip().lower()

		if sort_by and (sort_by not in SAFE_SORT_FIELDS or _has_restricted_sql(sort_by)):
			row.sort_by = "modified"
			changed = True

		if sort_order not in SAFE_SORT_ORDERS:
			row.sort_order = "desc"
			changed = True

		if row.filters and _has_restricted_sql(row.filters):
			row.filters = None
			changed = True

		if changed:
			frappe.db.set_value(
				"List View Settings",
				row.name,
				{"sort_by": row.sort_by or "modified", "sort_order": row.sort_order or "desc", "filters": row.filters},
			)
			updated += 1

	return updated


def _sanitize_user_settings_json():
	updated = 0
	rows = frappe.get_all("User", pluck="name")
	for user in rows:
		value = frappe.db.get_value("User", user, "user_settings")
		if not value:
			continue

		try:
			settings = json.loads(value)
		except Exception:
			continue

		if DOCTYPE not in settings:
			continue

		dt_settings = settings.get(DOCTYPE) or {}
		changed = False

		if isinstance(dt_settings, dict):
			sort_by = (dt_settings.get("sort_by") or "").strip()
			sort_order = (dt_settings.get("sort_order") or "desc").strip().lower()

			if sort_by and (sort_by not in SAFE_SORT_FIELDS or _has_restricted_sql(sort_by)):
				dt_settings["sort_by"] = "modified"
				changed = True

			if sort_order not in SAFE_SORT_ORDERS:
				dt_settings["sort_order"] = "desc"
				changed = True

			filters = dt_settings.get("filters")
			if isinstance(filters, str) and _has_restricted_sql(filters):
				dt_settings.pop("filters", None)
				changed = True

			for key in ("last_view", "order_by"):
				v = dt_settings.get(key)
				if isinstance(v, str) and _has_restricted_sql(v):
					dt_settings.pop(key, None)
					changed = True

		if changed:
			settings[DOCTYPE] = dt_settings
			frappe.db.set_value("User", user, "user_settings", json.dumps(settings))
			updated += 1

	return updated


def execute():
	list_updates = _sanitize_list_view_settings()
	user_updates = _sanitize_user_settings_json()
	frappe.db.commit()
	print(f"Updated List View Settings rows: {list_updates}")
	print(f"Updated User user_settings rows: {user_updates}")
	print("Done. Please run: bench --site <site> clear-cache")
