app_name = "kenz_report"
app_title = "Kenz Report"
app_publisher = "sammish"
app_description = "kenz report"
app_email = "sammish.thundiyil@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "kenz_report",
# 		"logo": "/assets/kenz_report/logo.png",
# 		"title": "Kenz Report",
# 		"route": "/kenz_report",
# 		"has_permission": "kenz_report.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/kenz_report/css/kenz_report.css"
# app_include_js = "/assets/kenz_report/js/kenz_report.js"

# include js, css files in header of web template
# web_include_css = "/assets/kenz_report/css/kenz_report.css"
# web_include_js = "/assets/kenz_report/js/kenz_report.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kenz_report/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "kenz_report/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "kenz_report.utils.jinja_methods",
# 	"filters": "kenz_report.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kenz_report.install.before_install"
# after_install = "kenz_report.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "kenz_report.uninstall.before_uninstall"
# after_uninstall = "kenz_report.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kenz_report.utils.before_app_install"
# after_app_install = "kenz_report.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kenz_report.utils.before_app_uninstall"
# after_app_uninstall = "kenz_report.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kenz_report.notifications.get_notification_config"

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

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"kenz_report.tasks.all"
# 	],
# 	"daily": [
# 		"kenz_report.tasks.daily"
# 	],
# 	"hourly": [
# 		"kenz_report.tasks.hourly"
# 	],
# 	"weekly": [
# 		"kenz_report.tasks.weekly"
# 	],
# 	"monthly": [
# 		"kenz_report.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "kenz_report.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kenz_report.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "kenz_report.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["kenz_report.utils.before_request"]
# after_request = ["kenz_report.utils.after_request"]

# Job Events
# ----------
# before_job = ["kenz_report.utils.before_job"]
# after_job = ["kenz_report.utils.after_job"]

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
# 	"kenz_report.auth.validate"
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

fixtures = [
    {
        "doctype": "Print Format",
        "filters": [["name", "in", ["Party Statement"]]],
    },
]

