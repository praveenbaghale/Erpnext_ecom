# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "erpnext_ecommerce"
app_title = "Erpnext Ecommerce"
app_publisher = "Tridots Tech"
app_description = "Ecommerce website using ERPNext"
app_icon = "octicon octicon-globe"
app_color = "#689421"
app_email = "info@valiantsystems.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/erpnext_ecommerce/css/erpnext_ecommerce.css"
# app_include_js = "/assets/erpnext_ecommerce/js/erpnext_ecommerce.js"

# include js, css files in header of web template
# web_include_css = "/assets/erpnext_ecommerce/css/erpnext_ecommerce.css"
# web_include_js = "/assets/erpnext_ecommerce/js/erpnext_ecommerce.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}
update_website_context = (
    "erpnext_ecommerce.erpnext_ecommerce.api.update_website_context"
)
# on login
on_session_creation = "erpnext_ecommerce.erpnext_ecommerce.api.login_customer"
# on logout
on_logout = "erpnext_ecommerce.erpnext_ecommerce.api.logout_customer"
website_route_rules = [
    {"from_route": "/my-profile", "to_route": "myprofile"},
    {"from_route": "/me", "to_route": "myprofile"},
    {"from_route": "/my-orders-list", "to_route": "orderslist"},
    {"from_route": "/order-detail", "to_route": "orderdetail"},
    {"from_route": "/my-address", "to_route": "address"},
    {"from_route": "/cart", "to_route": "cartpage"},
    {"from_route": "/about", "to_route": "aboutus"},
    {"from_route": "/contact-us", "to_route": "support"},
    {"from_route": "/login", "to_route": "customerlogin"},
]
# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "erpnext_ecommerce.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "erpnext_ecommerce.install.before_install"
# after_install = "erpnext_ecommerce.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "erpnext_ecommerce.notifications.get_notification_config"

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


has_website_permission = {
    "Customer": "erpnext_ecommerce.erpnext_ecommerce.api.has_website_permission"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Customer": {
        "autoname": "erpnext_ecommerce.erpnext_ecommerce.docevents.autoname_customer"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"erpnext_ecommerce.tasks.all"
# 	],
# 	"daily": [
# 		"erpnext_ecommerce.tasks.daily"
# 	],
# 	"hourly": [
# 		"erpnext_ecommerce.tasks.hourly"
# 	],
# 	"weekly": [
# 		"erpnext_ecommerce.tasks.weekly"
# 	]
# 	"monthly": [
# 		"erpnext_ecommerce.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "erpnext_ecommerce.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
override_whitelisted_methods = {
    "erpnext.setup.doctype.item_group.item_group.get_product_list_for_group": "erpnext_ecommerce.erpnext_ecommerce.docevents.get_product_list_for_group"
}
