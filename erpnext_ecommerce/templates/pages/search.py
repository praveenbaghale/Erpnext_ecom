# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
import frappe.utils
from erpnext_ecommerce.erpnext_ecommerce.docevents import get_product_list_for_group

no_cache = True


def get_context(context):
    searchText = frappe.form_dict.text
    brand = frappe.form_dict.brand
    if brand:
        brandslist = brand.split(",")
    minValue = frappe.form_dict.min
    maxValue = frappe.form_dict.max
    sortOrder = frappe.form_dict.sort
    if not sortOrder:
        sortOrder = "relevance"
    context.page_no = 0
    # for x in frappe.form_dict:
    #     if (
    #         x != "text"
    #         and x != "brand"
    #         and x != "min"
    #         and x != "max"
    #         and x != "rating"
    #         and x != "sort"
    #     ):
    #         attr.append({"attribute": x, "value": frappe.form_dict[x]})

    if searchText:
        Items = get_product_list_for_group(
            search=searchText,
            start=0,
            limit=12,
            brand=brand,
            minPrice=minValue,
            maxPrice=maxValue,
            sort=sortOrder,
        )
        if Items["item_group_html"]:
            context.Items_group = Items["item_group_html"]
        if Items["item_html"]:
            context.Items = Items["item_html"]
        context.title = "Search Results - " + searchText
        context.mobile_page_title = searchText
        context.searchText = searchText
        context.brand = brand
        if brand:
            while "" in brandslist:
                brandslist.remove("")
            context.brandslist = brandslist
        context.minValue = minValue
        context.maxValue = maxValue
        context.sort = sortOrder
        context.description = ""
        context.keywords = ""
    else:
        frappe.throw(frappe._("The page you are looking for is not found."))
