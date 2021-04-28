# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

from urllib.parse import unquote


def get_context(context):
    context.title = "Cart"
    context.description = ""
    context.keywords = ""
    context.mobile_page_title = "Cart"
    customer_id = unquote(frappe.request.cookies.get("customer_id"))
    if customer_id:
        quotation = frappe.get_all(
            "Quotation",
            fields=["name"],
            filters={
                "party_name": customer_id,
                "order_type": "Shopping Cart",
                "docstatus": 0,
            },
            order_by="modified desc",
            limit_page_length=1,
        )
        if quotation:
            qdoc = frappe.get_doc("Quotation", quotation[0].name)
            context.cart = qdoc
