import frappe


def set_footer_context(context):
    contact_settings = frappe.get_single("Contact Us Settings")

    address = ""
    address += (
        contact_settings.address_title + "<br>"
        if contact_settings.address_title
        else ""
    )
    address += contact_settings.address_line1 if contact_settings.address_line1 else ""
    address += (
        ", " + contact_settings.address_line2 if contact_settings.address_line2 else ""
    )
    address += ", " + contact_settings.city if contact_settings.city else ""
    address += "<br>" + contact_settings.state if contact_settings.state else ""
    address += " " + contact_settings.country if contact_settings.country else ""
    address += " - " + contact_settings.pincode if contact_settings.pincode else ""

    context.footer_address = address
    context.footer_email = contact_settings.email_id
    context.footer_phone = contact_settings.phone
