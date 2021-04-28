# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import frappe.utils


def get_context(context):
    context.mobile_page_title = "Login / Register"
    context.title = "Login / Register"
    if frappe.session.user != "Guest":
        frappe.local.flags.redirect_location = "/"
        raise frappe.Redirect
