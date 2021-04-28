# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
import frappe.utils

from frappe import _


def get_context(context):
    context.mobile_page_title = "Update Profile"
    if frappe.session.user == "Guest":
        frappe.throw(
            _("You need to be logged in to access this page"), frappe.PermissionError
        )
    else:
        customer = frappe.db.get_all(
            "Customer", filters={"email_id": frappe.session.user}, fields=["*"]
        )
        if customer:
            contact = frappe.db.get_all(
                "Contact", filters={"user": frappe.session.user}, fields=["mobile_no"]
            )
            if contact:
                customer[0].mobile_no = contact[0].mobile_no
            context.customer_id = customer[0].name
            context.customer = customer
        else:
            supplier = frappe.db.get_all(
                "Supplier", filters={"user": frappe.session.user}, fields=["*"]
            )
            if supplier:
                context.supplier = supplier
