# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from erpnext_ecommerce.erpnext_ecommerce.api import (
    get_bestsellers_homepage,
    get_topsavers_homepage,
    get_category_scroll,
)


def get_context(context):
    best_sellers = get_bestsellers_homepage()
    context.best_sellers = best_sellers
    featured_category = frappe.db.sql(
        """
        select name, item_group_name, route, image, is_group 
        from `tabItem Group` 
        where name!="All Item Groups"
        and show_in_website=1
        and is_featured_category=1 
        and deal_category=0 
        limit {limit}
        """.format(
            limit=12
        ),
        as_dict=1,
    )
    if featured_category:
        for item in featured_category:
            if item.is_group:
                subcategories = frappe.db.sql(
                    """
                    SELECT parent_item_group,GROUP_CONCAT(item_group_name SEPARATOR ', ') as categories 
                    from `tabItem Group` 
                    where show_in_website=1 
                    and parent_item_group=%(parent)s 
                    group by parent_item_group
                    """,
                    {"parent": item.name},
                    as_dict=1,
                )
                if subcategories:
                    item.sublist = subcategories[0].categories + " & More"
                    if len(item.sublist) > 60:
                        item.sublist_short = item.sublist[:60] + "..."
                    else:
                        item.sublist_short = item.sublist
            item.products = get_category_scroll(
                item.name,
                1,
                24,
                brand_filter=None,
                minValue=None,
                maxValue=None,
                sortOrder=None,
                attributes=None,
                rating=None,
            )
    context.featured_category = featured_category
