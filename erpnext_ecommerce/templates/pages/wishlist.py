# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
import frappe.utils
from urllib.parse import unquote


def get_context(context):
    context.title = "Wishlist"
    context.mobile_page_title = "Wishlist"
    context.description = ""
    context.keywords = ""
    customer_id = unquote(frappe.request.cookies.get("customer_id"))
    if customer_id:
        wishlist = frappe.get_all(
            "Wishlist",
            fields=["name"],
            filters={
                "party_name": customer_id,
                "order_type": "Wishlist",
                "docstatus": 0,
            },
            order_by="modified desc",
            limit_page_length=1,
        )
        if wishlist:
            qdoc = frappe.get_doc("Wishlist", wishlist[0].name)
            context.wishlist = qdoc
