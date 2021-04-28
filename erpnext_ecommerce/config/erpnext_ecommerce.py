from frappe import _


def get_data():
    def make_item(type, name, label, is_query_report=None):
        return {
            "type": type,
            "name": name,
            "label": _(label),
            "is_query_report": is_query_report,
        }

    def make_section(label, items):
        return {"label": _(label), "items": items}

    return [
        make_section(
            "Documents",
            [
                make_item("doctype", "Home Page Builders", "Home Page Builders"),
                make_item("doctype", "Payment Method", "Payment Method"),
                make_item("doctype", "Wishlist", "Wishlist"),
                make_item("doctype", "Homepage Section", "Homepage Section"),
                make_item("doctype", "HomePage Templates", "HomePage Templates"),
                make_item("doctype", "Homepage Banner", "Homepage Banner"),
            ],
        ),
    ]