# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
import frappe.utils
from frappe import _


def get_context(context):
    context.mobile_page_title = "My Profile"
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
            week_order_list = frappe.db.sql(
                """
                select name 
                from `tabSales Order` s 
                where s.customer=%(customer)s 
                and YEARWEEK(`creation`, 1) = YEARWEEK(CURDATE(), 1)
                """,
                {"customer": customer[0].name},
                as_dict=1,
            )
            month_order_list = frappe.db.sql(
                """
                select name 
                from `tabSales Order` s 
                where s.customer=%(customer)s 
                and MONTH(`creation`) = MONTH(CURDATE())
                """,
                {"customer": customer[0].name},
                as_dict=1,
            )
            today_order_list = frappe.db.sql(
                """
                select name 
                from `tabSales Order` s 
                where s.customer=%(customer)s 
                and DATE(`creation`) = CURDATE()
                """,
                {"customer": customer[0].name},
                as_dict=1,
            )
            all_order_list = frappe.db.sql(
                """
                select name 
                from `tabSales Order` s 
                where s.customer=%(customer)s
                """,
                {"customer": customer[0].name},
                as_dict=1,
            )
            paid_amount = 0
            pending_amount = 0
            customer_invoices = frappe.db.get_all(
                "Sales Invoice",
                filters={
                    "docstatus": 1,
                    "customer": customer[0].name,
                    "is_return": ("!=", 1),
                },
                fields=[
                    "name",
                    "status",
                    "outstanding_amount",
                    "grand_total",
                    "is_return",
                ],
            )
            if customer_invoices:
                for item in customer_invoices:
                    pending_amount = pending_amount + item.outstanding_amount
                    return_created = frappe.db.get_all(
                        "Sales Invoice",
                        filters={
                            "customer": customer[0].name,
                            "docstatus": 1,
                            "return_against": item.name,
                        },
                        fields=["status", "outstanding_amount", "grand_total"],
                    )
                    if not return_created:
                        paid_amount = (
                            paid_amount + item.grand_total - item.outstanding_amount
                        )
                    else:
                        if item.outstanding_amount < 0:
                            paid_amount = paid_amount - item.outstanding_amount
            context.paid_amount = paid_amount
            context.pending_amount = pending_amount
            context.customer_id = customer[0].name
            context.orders = orders_list
            context.today_count = len(today_order_list)
            context.weekly_count = len(week_order_list)
            context.monthly_count = len(month_order_list)
            context.all_count = len(all_order_list)
        else:
            supplier = frappe.db.get_all(
                "Supplier", filters={"user": frappe.session.user}, fields=["*"]
            )
            if supplier:
                deals = frappe.db.sql(
                    """
                    select 
                        s.name as deal_id,
                        s.total_price,
                        soi.extra_charges,
                        so.name,
                        so.transaction_date,
                        (s.total_price+soi.extra_charges) as total 
                    from `tabSale` s
                    inner join `tabSales Order Item` soi on soi.reference=s.name 
                    left join `tabSales Order` so on so.name=soi.parent
                    where s.seller=%(supplier)s
                    group by so.name 
                    limit 10
                    """,
                    {"supplier": supplier[0].name},
                    as_dict=1,
                )
                context.deals = deals
                week_order_list = frappe.db.sql(
                    """
                    select name 
                    from `tabSales Order` s 
                    where s.supplier=%(supplier)s 
                    and YEARWEEK(`creation`, 1) = YEARWEEK(CURDATE(), 1)
                    """,
                    {"supplier": supplier[0].name},
                    as_dict=1,
                )
            month_order_list = frappe.db.sql(
                """
                select name 
                from `tabSales Order` s 
                where s.supplier=%(supplier)s 
                and MONTH(`creation`) = MONTH(CURDATE())
                """,
                {"supplier": supplier[0].name},
                as_dict=1,
            )
            today_order_list = frappe.db.sql(
                """
                select name 
                from `tabSales Order` s 
                where s.supplier=%(supplier)s 
                and DATE(`creation`) = CURDATE()
                """,
                {"supplier": supplier[0].name},
                as_dict=1,
            )
            all_order_list = frappe.db.sql(
                """
                select name 
                from `tabSales Order` s 
                where s.supplier=%(supplier)s
                """,
                {"supplier": supplier[0].name},
                as_dict=1,
            )
            context.today_count = len(today_order_list)
            context.weekly_count = len(week_order_list)
            context.monthly_count = len(month_order_list)
            context.all_count = len(all_order_list)
