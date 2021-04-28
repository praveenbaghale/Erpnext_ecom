# -*- coding: utf-8 -*-
# Copyright (c) 2019, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import nowdate, flt, cint, cstr
from erpnext.setup.doctype.item_group.item_group import (
    adjust_qty_for_expired_items,
    get_child_groups,
)
from erpnext.shopping_cart.product_info import set_product_info_for_website
from frappe.model.naming import make_autoname


@frappe.whitelist(allow_guest=True)
def get_product_list_for_group(
    product_group=None,
    start=0,
    limit=12,
    search=None,
    sort=None,
    minPrice=None,
    maxPrice=None,
    brand=None,
):
    try:
        child_group_html = None
        child_groups = '""'
        if product_group:
            item_group = frappe.get_cached_doc("Item Group", product_group)
            if item_group.is_group:
                # return child item groups if the type is of "Is Group"
                child_group_html = get_child_groups_for_list_in_html(
                    item_group, start, limit, search
                )

            child_groups = ", ".join(
                [
                    '"' + frappe.db.escape(i[0]) + '"'
                    for i in get_child_groups(product_group)
                ]
            )
        # base query
        price_list = frappe.db.get_single_value("Shopping Cart Settings", "price_list")
        price_query = ""
        if price_list:
            price_query = ", (select price_list_rate from `tabItem Price` where item_code = I.name and \
                price_list = '{price_list}'  and (case when valid_from is not null then valid_from <= %(today)s\
                else 1=1 end) and (case when valid_upto is not null then valid_upto >= %(today)s else 1=1 end) limit 1)\
                as item_price".format(
                price_list=price_list
            )
        query = """
            select 
                I.name, 
                I.item_name, 
                I.item_code, 
                I.route, 
                I.image, 
                I.website_image, 
                I.thumbnail, 
                I.item_group,
                I.description, 
                I.web_long_description as website_description, 
                I.is_stock_item,
                case 
                    when (S.actual_qty - S.reserved_qty) > 0 
                    then 1 
                    else 0 
                end as in_stock, 
                I.website_warehouse,
                I.has_batch_no, 
                I.variant_of{price_query}
            from `tabItem` I
            left join tabBin S on I.item_code = S.item_code and I.website_warehouse = S.warehouse
            left join tabBrand B on I.brand = B.name
            where (I.show_in_website = 1 or I.show_variant_in_website = 1)
            and I.disabled = 0
            and (I.end_of_life is null or I.end_of_life='0000-00-00' or I.end_of_life > %(today)s)
            -- and (I.variant_of = '' or I.variant_of is null) and I.has_variants = 0
        """.format(
            price_query=price_query
        )
        if product_group:
            query += """ and (I.item_group in ({child_groups})
                or I.name in (select parent from `tabWebsite Item Group` where item_group in ({child_groups})))
            """.format(
                child_groups=child_groups
            )
        # search term condition
        if search:
            query += """ and (I.web_long_description like %(search)s
                or I.item_name like %(search)s
                or I.name like %(search)s)"""
            search = "%" + cstr(search) + "%"

        # check brand filters
        if brand:
            if brand.find(",") != -1:
                brand_list = brand.split(",")
            else:
                brand_list = [brand]
            if brand_list:
                brands = ", ".join(
                    ['"' + frappe.db.escape(i) + '"' for i in brand_list]
                )
                query += """ and B.name in ({brands})""".format(brands=brands)
        # check min & max price filter
        filters = ""
        if minPrice and maxPrice:
            filters = " having item_price >= %s and item_price <= %s" % (
                minPrice,
                maxPrice,
            )
        else:
            if minPrice:
                filters = " having item_price >= %s" % (minPrice)
            if maxPrice:
                filters = " having item_price <= %s" % (maxPrice)
        query += """%s """ % (filters)
        # check for sort options
        order_by = ""
        if sort:
            ref = get_sort_options(sort)
            if ref:
                order_by = ref + ", "

        query += (
            """order by %s I.weightage desc, in_stock desc, I.modified desc limit %s, %s"""
            % (order_by, start, limit)
        )
        data = frappe.db.sql(
            query,
            {"product_group": product_group, "search": search, "today": nowdate()},
            as_dict=1,
        )
        data = adjust_qty_for_expired_items(data)
        if cint(frappe.db.get_single_value("Shopping Cart Settings", "enabled")):
            for item in data:
                set_product_info_for_website(item)

        items_html = get_item_for_list_in_html(data, start)
        return {"item_group_html": child_group_html, "item_html": items_html}
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "ecommerce_business_store.ecommerce_business_store.docevents.get_product_list_for_group",
        )


def get_child_groups_for_list_in_html(item_group, start, limit, search):
    search_filters = None
    if search_filters:
        search_filters = [
            dict(name=("like", "%{}%".format(search))),
            dict(description=("like", "%{}%".format(search))),
        ]
    data = frappe.db.get_all(
        "Item Group",
        fields=["name", "route", "description", "image"],
        filters=dict(show_in_website=1, parent_item_group=item_group.name),
        or_filters=search_filters,
        order_by="weightage desc, name asc",
    )

    return get_child_category_html(data)


def get_child_category_html(context):
    template = "templates/pages/childitemgroup.html"
    return frappe.get_template(template).render({"item_group": context})


def get_item_for_list_in_html(context, start):
    if context:
        template = "templates/pages/itemlist.html"
        return frappe.get_template(template).render(
            {"Items": context, "page_no": start}
        )
    else:
        return None


def get_sort_options(sort):
    sort_options = {
        "name_asc": "item_name asc",
        "name_desc": "item_name desc",
        "relevance": "",
        "price_desc": "item_price desc",
        "price_asc": "item_price asc",
    }
    return sort_options[sort]


def autoname_customer(doc, method):
    if doc.customer_name == "Guest":
        doc.naming_series = "GC-.YYYY.-"
        doc.name = make_autoname(doc.naming_series + ".#####", doc=doc)
