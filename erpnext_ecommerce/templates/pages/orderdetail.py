# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
import frappe.utils

no_cache = True


def get_context(context):
    order_id = frappe.form_dict.id
    context.mobile_page_title = "Order Details"
    if frappe.session.user == "Guest":
        frappe.throw(
            frappe._("You need to be logged in to access this page"),
            frappe.PermissionError,
        )
    context.order_id = order_id
    if order_id:
        order_details = frappe.get_doc("Sales Order", order_id)
        context.order_details = order_details
