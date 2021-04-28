from __future__ import unicode_literals

import frappe
import frappe.utils

from frappe import _
from urllib.parse import unquote


def get_context(context):
    OrderId = frappe.form_dict.id
    customer_id = (
        unquote(frappe.request.cookies.get("customer_id"))
        if frappe.request.cookies.get("customer_id")
        else None
    )
    if OrderId:
        order = frappe.get_doc("Sales Order", OrderId)
        if order.customer == customer_id or order.owner == frappe.session.user:
            context.Order = order
        else:
            frappe.throw(
                _("You are not allowed to access this document"), frappe.PermissionError
            )
    context.title = "Thankyou - " + OrderId
    context.description = ""
    context.keywords = ""

    context.payment_status = frappe.db.get_value(
        "Integration Request",
        {"reference_doctype": "Sales Order", "reference_docname": OrderId},
        "status",
    )
    context.payment_url = (
        _get_payment_url(OrderId) if context.payment_status != "Completed" else None
    )

    context.mobile_page_title = (
        "Order Completed"
        if context.payment_status == "Completed"
        else "Order Not Yet Completed"
    )


def _get_payment_url(order_id):
    ireq = frappe.db.exists(
        "Integration Request",
        {
            "integration_request_service": "AFS Payment",
            "reference_doctype": "Sales Order",
            "reference_docname": order_id,
        },
    )
    if not ireq:
        return None
    return frappe.utils.get_url("./afs_payment_checkout?token={0}".format(ireq))
