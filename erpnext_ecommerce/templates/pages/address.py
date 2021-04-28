# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import frappe.utils
from frappe import _


def get_context(context):
    context.mobile_page_title = "Addresses"
    if frappe.session.user == "Guest":
        frappe.throw(
            _("You need to be logged in to access this page"), frappe.PermissionError
        )
    else:
        customer = frappe.db.get_all(
            "Customer", filters={"email_id": frappe.session.user}, fields=["*"]
        )
        if customer:
            address = frappe.db.sql(
                """
                select a.* 
                from `tabAddress` a,`tabDynamic Link` d 
                where a.name=d.parent 
                and d.link_doctype="Customer" 
                and d.link_name=%(customer)s 
                order by a.creation desc
                """,
                {"customer": customer[0].name},
                as_dict=1,
            )
            context.address = address
        else:
            supplier = frappe.db.get_all(
                "Supplier", filters={"user": frappe.session.user}, fields=["*"]
            )
            if supplier:
                address = frappe.db.sql(
                    """
                    select a.* 
                    from `tabAddress` a,`tabDynamic Link` d 
                    where a.name=d.parent 
                    and d.link_doctype="Supplier" 
                    and d.link_name=%(supplier)s 
                    order by a.creation desc
                    """,
                    {"supplier": supplier[0].name},
                    as_dict=1,
                )
                context.address = address
