# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

from urllib.parse import unquote


def get_context(context):
    context.country = frappe.db.sql(
        """select name from tabCountry order by name""", as_dict=1
    )
    customer_id = (
        unquote(frappe.request.cookies.get("customer_id"))
        if frappe.request.cookies.get("customer_id")
        else None
    )
    context.isCartEmpty = 0
    if frappe.session.user != "Guest":
        customers = frappe.db.get_all(
            "Customer", filters={"name": customer_id}, fields=["*"]
        )
        if customers:
            customers[0].customer_address = frappe.db.sql(
                """
                select a.* 
                from `tabAddress` a,`tabDynamic Link` d 
                where a.name=d.parent 
                and d.link_name=%(customer)s
                """,
                {"customer": customers[0].name},
                as_dict=1,
            )
            customer_contact = frappe.db.sql(
                """
                select a.*
                from `tabContact` a,`tabDynamic Link` d
                where a.name=d.parent
                and a.is_primary_contact=1
                and d.link_name=%(customer)s
                """,
                {"customer": customers[0].name},
                as_dict=1,
            )
            if customer_contact:
                customers[0].customer_contact = customer_contact[0]
            context.customer = customers[0]
        else:
            context.customer = None

    if customer_id:
        quotation = frappe.get_all(
            "Quotation",
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
            if not qdoc:
                context.isCartEmpty = 1
            else:
                item_groups = []
                for item in qdoc.items:
                    item_group = frappe.get_value("Item", item.item_code, "item_group")
                    if item_group:
                        item_groups.append(item_group)
                        itemgroup = frappe.get_doc("Item Group", item_group)
                        parent_groups = frappe.db.sql(
                            """
                                select name from `tabItem Group`
                                where lft <= %s and rgt >= %s
                                and show_in_website=1
                                order by lft asc
                            """,
                            (itemgroup.lft, itemgroup.rgt),
                            as_dict=True,
                        )
                        if parent_groups:
                            for group in parent_groups:
                                item_groups.append(group.name)
                if len(item_groups) > 0:
                    item_groups = list(dict.fromkeys(item_groups))
                    item_groups = '"{0}"'.format('", "'.join(item_groups))
                    query = """
                        SELECT parent as name
                        from `tabShipping Rule Itemgroup`
                        WHERE item_group in ({item_groups})
                    """.format(
                        item_groups=item_groups
                    )
                    shipping_methods = frappe.db.sql(
                        """{query}""".format(query=query), as_dict=1
                    )
                    if shipping_methods:
                        context.shipping_methods = shipping_methods
        else:
            context.isCartEmpty = 1

    payment_methods = frappe.db.get_all(
        "Payment Method",
        fields=["name", "payment_method", "mode_of_payment", "payment_charges"],
    )
    if payment_methods:
        context.payment_methods = payment_methods

    context.description = ""
    context.keywords = ""
    context.title = "Checkout"
    context.mobile_page_title = "Checkout"
