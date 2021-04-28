# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
import frappe.utils
from frappe import _


def get_context(context):
    context.mobile_page_title = "Order List"
    if frappe.session.user == "Guest":
        frappe.throw(
            _("You need to be logged in to access this page"), frappe.PermissionError
        )
    else:
        customer = frappe.db.get_all(
            "Customer", filters={"email_id": frappe.session.user}, fields=["*"]
        )
        if customer:
            orders_list = frappe.db.get_all(
                "Sales Order",
                fields=["*"],
                filters={"customer": customer[0].name},
                order_by="creation desc",
                limit_page_length=10,
            )
            for i in orders_list:
                order_items = frappe.get_all(
                    "Sales Order Item",
                    fields=["*"],
                    filters={"parent": i.name},
                    limit_page_length=100,
                )
                i.no_of_items = len(order_items)
            context.orders = orders_list
            context.customer = customer[0]
        elif context.supplier_id:
            orders_list = frappe.db.sql(
                """
                select 
                    s.name as deal_id,
                    s.total_price,
                    soi.extra_charges,
                    so.name,
                    so.transaction_date,
                    (s.total_price+soi.extra_charges) as total,
                    s.item_name 
                from `tabSale` s inner join `tabSales Order Item` soi on soi.reference=s.name 
                left join `tabSales Order` so on so.name=soi.parent 
                where s.seller=%(supplier)s 
                group by so.name 
                limit 10
                """,
                {"supplier": context.supplier_id},
                as_dict=1,
            )
            context.deals = orders_list


@frappe.whitelist()
def get_order_list(start, limit=10, customer=None, supplier=None):
    start = str((int(start) * int(limit)))
    if customer:
        result = frappe.db.sql(
            """
            select * 
            from `tabSales Order`
            where customer=%(customer)s
            order by creation desc limit {start},{limit}
            """.format(
                start=start, limit=limit
            ),
            {"customer": customer},
            as_dict=1,
        )
        for i in result:
            order_items = frappe.get_all(
                "Sales Order Item",
                fields=["*"],
                filters={"parent": i.name},
                limit_page_length=100,
            )
            i.no_of_items = len(order_items)
        return result
    elif supplier:
        result = frappe.db.sql(
            """
            select 
                s.name as deal_id,
                s.total_price,
                soi.extra_charges,
                so.name,
                so.transaction_date,
                (s.total_price+soi.extra_charges) as total,
                s.item_name 
            from `tabSale` s inner join `tabSales Order Item` soi on soi.reference=s.name 
            left join `tabSales Order` so on so.name=soi.parent 
            where s.seller=%(supplier)s 
            group by so.name
            limit {start},{limit}
            """.format(
                start=start, limit=limit
            ),
            {"supplier": supplier},
            as_dict=1,
        )
        return result
