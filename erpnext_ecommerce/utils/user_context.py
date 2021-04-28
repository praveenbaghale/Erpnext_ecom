import frappe
from urllib.parse import unquote


def set_user_context(context):
    if frappe.session.user != "Guest":
        customer = frappe.db.get_all(
            "Customer", filters={"email_id": frappe.session.user}, fields=["name"]
        )
        if customer:
            context.customer_id = customer[0].name

        user_details = frappe.get_doc("User", frappe.session.user)
        context.UserDetails = user_details

    customer_id_cookie = frappe.request.cookies.get("customer_id")
    customer_id = unquote(customer_id_cookie) if customer_id_cookie else None
    if not customer_id:
        create_guest_customer()


def create_guest_customer():
    doc = frappe.new_doc("Customer")
    doc.customer_name = "Guest"
    doc.customer_type = "Individual"
    doc.save(ignore_permissions=True)
    if hasattr(frappe.local, 'cookie_manager'):
        frappe.local.cookie_manager.set_cookie("customer_id", doc.name)
        frappe.local.cookie_manager.set_cookie("guest_customer", doc.name)
    return doc.name
