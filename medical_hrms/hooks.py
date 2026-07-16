app_name = "medical_hrms"
app_title = "Medical HRMS"
app_publisher = "Admin"
app_description = "Medical College HRMS"
app_email = "admin@example.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "medical_hrms",
# 		"logo": "/assets/medical_hrms/logo.png",
# 		"title": "Medical HRMS",
# 		"route": "/medical_hrms",
# 		"has_permission": "medical_hrms.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/medical_hrms/css/medical_hrms.css"
# app_include_js = "/assets/medical_hrms/js/medical_hrms.js"

# include js, css files in header of web template
# web_include_css = "/assets/medical_hrms/css/medical_hrms.css"
# web_include_js = "/assets/medical_hrms/js/medical_hrms.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "medical_hrms/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {"Medical HRMS Job Applicant": "public/js/job_applicant.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "medical_hrms/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
role_home_page = {
	"HR User": "hr-dashboard",
	"HR Manager": "hr-dashboard",
}

on_session_creation = [
	"medical_hrms.login_redirect.redirect_hr_users_after_login"
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]
website_route_rules = [
	{"from_route": "/job-application", "to_route": "medical-job-application"},
	{"from_route": "/job-application/<path:token>", "to_route": "medical-job-application"},
]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "medical_hrms.utils.jinja_methods",
# 	"filters": "medical_hrms.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "medical_hrms.install.before_install"
# after_install = "medical_hrms.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "medical_hrms.uninstall.before_uninstall"
# after_uninstall = "medical_hrms.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "medical_hrms.utils.before_app_install"
# after_app_install = "medical_hrms.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "medical_hrms.utils.before_app_uninstall"
# after_app_uninstall = "medical_hrms.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "medical_hrms.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Expense Claim": {
		"validate": "medical_hrms.medical_hrms.overrides.expense_claim.validate_expense_claim",
		"before_submit": "medical_hrms.medical_hrms.overrides.expense_claim.validate_expense_claim"
	},
	"Children Medical Allowance Request": {
		"validate": "medical_hrms.medical_hrms.overrides.education_allowance.validate_education_allowance"
	},
	"Employee Separation": {
		"validate": "medical_hrms.medical_hrms.overrides.career.validate_employee_separation"
	},
	"Employee Training Request": {
		"validate": "medical_hrms.medical_hrms.overrides.career.validate_training_request",
		"before_submit": "medical_hrms.medical_hrms.overrides.career.validate_training_request"
	},
	"Travel Request": {
		"validate": "medical_hrms.medical_hrms.overrides.admin.validate_travel_request",
		"before_submit": "medical_hrms.medical_hrms.overrides.admin.validate_travel_request"
	},
	"Company Car Request": {
		"validate": "medical_hrms.medical_hrms.overrides.admin.validate_company_car"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"medical_hrms.tasks.all"
# 	],
# 	"daily": [
# 		"medical_hrms.tasks.daily"
# 	],
# 	"hourly": [
# 		"medical_hrms.tasks.hourly"
# 	],
# 	"weekly": [
# 		"medical_hrms.tasks.weekly"
# 	],
# 	"monthly": [
# 		"medical_hrms.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "medical_hrms.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "medical_hrms.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "medical_hrms.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["medical_hrms.utils.before_request"]
# after_request = ["medical_hrms.utils.after_request"]

# Job Events
# ----------
# before_job = ["medical_hrms.utils.before_job"]
# after_job = ["medical_hrms.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"medical_hrms.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
