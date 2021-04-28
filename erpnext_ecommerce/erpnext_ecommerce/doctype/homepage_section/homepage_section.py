# -*- coding: utf-8 -*-
# Copyright (c) 2019, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import os
from frappe.model.document import Document
from frappe.utils import nowdate, cint
from frappe.utils import touch_file, encode, cstr, flt


class HomepageSection(Document):
    def validate(self):
        from erpnext.setup.doctype.item_group.item_group import (
            adjust_qty_for_expired_items,
            get_child_groups,
        )
        from erpnext.shopping_cart.product_info import set_product_info_for_website

        if not self.route:
            self.route = frappe.scrub(self.name).replace("-", "_")
        path = frappe.get_module_path("erpnext_ecommerce")
        path_parts = path.split("/")
        path_parts = path_parts[:-1]
        url = "/".join(path_parts)
        context = {}

        if self.select_field == "Slider":
            if self.select_slider:
                Sliders = frappe.db.get_all(
                    "Website Slideshow Item",
                    fields=["image", "heading", "description", "mobile_image"],
                    filters={"parent": self.select_slider},
                )
                context["sliders"] = Sliders
                slider_template = frappe.db.get_all(
                    "HomePage Templates",
                    fields=["page_template"],
                    filters={"name": self.view_template},
                )
                template = frappe.render_template(
                    slider_template[0].page_template, context
                )
                page_template1 = template
                with open(
                    os.path.join(url, "templates/pages", (self.route + "1.html")), "w"
                ) as f:
                    f.write(page_template1)
        elif self.select_field == "Category Tabs":
            condition = ""
            limit = self.no_of_product_display if self.no_of_product_display else 12
            if self.category_image_position:
                context["image_position"] = self.category_image_position
            if self.select_category:
                category_info = frappe.db.get_all(
                    "Item Group",
                    filters={"name": self.select_category},
                    fields=["item_group_name", "route", "image", "name"],
                )
                context["category_info"] = category_info
                context["category_info1"] = category_info[0].image
            if self.select_category:
                categories = []
                subcategory_list = frappe.db.get_all(
                    "Sub Categories",
                    fields=["sub_child_category", "sub_category_name"],
                    filters={"parent": self.name},
                    order_by="idx",
                )
                price_list = frappe.db.get_single_value(
                    "Shopping Cart Settings", "price_list"
                )
                price_query = ""
                if price_list:
                    price_query = ", (select price_list_rate from `tabItem Price` where item_code = I.name and \
					price_list = '{price_list}' and (case when valid_from is not null then valid_from >= '{today}' \
					else 1=1 end) and (case when valid_upto is not null then valid_upto <= '{today}' else 1=1 end) limit 1) \
					as item_price".format(
                        price_list=price_list, today=nowdate()
                    )
                if len(subcategory_list) > 0:
                    for subcat in subcategory_list:
                        if subcat:
                            category_info = frappe.db.get_all(
                                "Item Group",
                                filters={"name": subcat.sub_child_category},
                                fields=["name", "image", "item_group_name", "route"],
                            )[0]
                            child_groups = ", ".join(
                                [
                                    '"' + frappe.db.escape(i[0]) + '"'
                                    for i in get_child_groups(
                                        category_info.item_group_name
                                    )
                                ]
                            )
                        query = """{query} limit {limit}""".format(
                            query=self.query, limit=limit
                        )
                        product = frappe.db.sql(
                            query.format(
                                price_query=price_query, child_groups=child_groups
                            ),
                            as_dict=1,
                        )
                        product = adjust_qty_for_expired_items(product)
                        if cint(
                            frappe.db.get_single_value(
                                "Shopping Cart Settings", "enabled"
                            )
                        ):
                            for item in product:
                                set_product_info_for_website(item)
                        category_info.product = product
                        categories.append(category_info)
                    context[self.route] = categories
                    slider_template = frappe.db.get_all(
                        "HomePage Templates",
                        fields=["page_template"],
                        filters={"name": self.view_template},
                    )
                    template = frappe.render_template(
                        slider_template[0].page_template, context
                    )
                    page_template1 = template
                    with open(
                        os.path.join(url, "templates/pages", (self.route + "1.html")),
                        "w",
                    ) as f:
                        f.write(encode(page_template1))

        elif self.select_field == "Section":
            if self.select_type == "Static":
                categories = []
                limit = ""
                if self.no_of_product_display:
                    limit = self.no_of_product_display
                if self.route:
                    context["route"] = self.route
                if self.enable_view_more_btn:
                    context["enable_view_more_btn"] = self.enable_view_more_btn
                if self.select_doctype:
                    doctype = self.select_doctype
                    category_list = frappe.db.get_all(
                        "Child Doctype",
                        fields=["doc_names", "doc_fields"],
                        filters={"parent": self.name},
                        order_by="idx",
                    )
                    product_list = frappe.db.get_all(
                        "Static Product Page",
                        fields=["product_id", "product_name"],
                        filters={"parent": self.name},
                        order_by="idx",
                    )
                    if len(category_list) > 0 and len(product_list) == 0:
                        for cat in category_list:
                            if cat.doc_names == "Item Group":
                                cat.category_info = frappe.db.get_all(
                                    "Item Group",
                                    filters={"name": cat.doc_fields},
                                    fields=[
                                        "name",
                                        "image",
                                        "item_group_name",
                                        "route",
                                    ],
                                )
                            else:
                                cat.category_info = frappe.db.get_all(
                                    "Brand",
                                    filters={"name": cat.doc_fields},
                                    fields=["name", "description"],
                                )
                        context[self.route] = category_list
                        slider_template = frappe.db.get_all(
                            "HomePage Templates",
                            fields=["page_template"],
                            filters={"name": self.view_template},
                        )
                        template = frappe.render_template(
                            slider_template[0].page_template, context
                        )
                        page_template1 = template
                        with open(
                            os.path.join(
                                url, "templates/pages", (self.route + "1.html")
                            ),
                            "w",
                        ) as f:
                            f.write(encode(page_template1))
                    elif len(category_list) > 0 and len(product_list) > 0:
                        for cat in category_list:
                            category_info = frappe.db.get_all(
                                "Item Group",
                                filters={"name": cat.doc_fields},
                                fields=["name", "image", "item_group_name", "route"],
                            )[0]
                            if cat.doc_names == "Item Group":
                                product = frappe.db.sql(
                                    """
                                    select sp.product_id, sp.product_name, p.*
                                    from `tabStatic Product Page` sp
                                    inner join `tabItem` p on p.name=sp.product_id 
                                    where sp.parent=%(parent)s 
                                    order by idx 
                                    limit {limit}
                                    """.format(
                                        limit=limit, doctypes=doctype
                                    ),
                                    {"parent": self.name},
                                    as_dict=1,
                                )
                            else:
                                product = frappe.db.sql(
                                    """
                                    select sp.product_id, sp.product_name, p.* 
                                    from `tabStatic Product Page` sp 
                                    inner join `tabItem` p on p.name=sp.product_id 
                                    where sp.parent=%(parent)s 
                                    and p.brand in ({brand}) 
                                    order by idx 
                                    limit {limit}
                                    """.format(
                                        limit=limit,
                                        doctypes=doctype,
                                        brand='"' + str(cat.doc_fields) + '"',
                                    ),
                                    {"parent": self.name},
                                    as_dict=1,
                                )
                            product = adjust_qty_for_expired_items(product)
                            if cint(
                                frappe.db.get_single_value(
                                    "Shopping Cart Settings", "enabled"
                                )
                            ):
                                for item in product:
                                    set_product_info_for_website(item)
                            category_info.product = product
                            categories.append(category_info)
                        context[self.route] = categories
                        product_template = frappe.db.get_all(
                            "HomePage Templates",
                            fields=["page_template"],
                            filters={"name": self.view_template},
                        )
                        template1 = frappe.render_template(
                            product_template[0].page_template, context
                        )
                        page_template2 = template1
                        with open(
                            os.path.join(
                                url, "templates/pages", (self.route + "1.html")
                            ),
                            "w",
                        ) as f:
                            f.write(encode(page_template2))
                    else:
                        product = frappe.db.sql(
                            """
                            select pcm.product_id, pcm.product_name, p.* 
                            from `tabStatic Product Page` pcm 
                            inner join `tab{doctypes}` p on p.name=pcm.product_id 
                            where pcm.parent=%(parent)s
                            limit {limit}
                            """.format(
                                limit=limit, doctypes=doctype
                            ),
                            {"parent": self.name},
                            as_dict=1,
                        )
                        context[self.route] = product
                        product_template = frappe.db.get_all(
                            "HomePage Templates",
                            fields=["page_template"],
                            filters={"name": self.view_template},
                        )
                        template1 = frappe.render_template(
                            product_template[0].page_template, context
                        )
                        page_template2 = template1
                        with open(
                            os.path.join(
                                url, "templates/pages", (self.route + "1.html")
                            ),
                            "w",
                        ) as f:
                            f.write(encode(page_template2))
            if self.select_type == "Dynamic":
                categories = []
                limit = ""
                if self.no_of_product_display:
                    limit = self.no_of_product_display
                if self.route:
                    context["route"] = self.route
                if self.enable_view_more_btn:
                    context["enable_view_more_btn"] = self.enable_view_more_btn
                default_currency = frappe.db.get_single_value(
                    "Global Defaults", "default_currency"
                )
                currency = frappe.get_value("Currency", default_currency, "symbol")
                context["currency"] = currency
                condition = ""
                if self.no_of_product_display:
                    limit = self.no_of_product_display
                categories = []
                category_list = frappe.db.get_all(
                    "Child Doctype",
                    fields=["doc_names", "doc_fields"],
                    filters={"parent": self.name},
                    order_by="idx",
                )
                if len(category_list) > 0:
                    price_list = frappe.db.get_single_value(
                        "Shopping Cart Settings", "price_list"
                    )
                    price_query = ""
                    if price_list:
                        price_query = ", (select price_list_rate from `tabItem Price` where item_code = I.name and price_list = '{price_list}') as item_price".format(
                            price_list=price_list
                        )
                    for cat in category_list:
                        if cat.doc_names == "Item Group":
                            category_info = frappe.db.get_all(
                                "Item Group",
                                filters={"name": cat.doc_fields},
                                fields=["name", "image", "item_group_name", "route"],
                            )[0]
                            child_groups = ", ".join(
                                [
                                    '"' + frappe.db.escape(i[0]) + '"'
                                    for i in get_child_groups(
                                        category_info.item_group_name
                                    )
                                ]
                            )
                        else:
                            category_info = frappe.db.get_all(
                                "Brand",
                                filters={"name": cat.doc_fields},
                                fields=["name", "description", "brand"],
                            )[0]

                        query = """{query} limit {limit}""".format(
                            query=self.query, limit=limit
                        )
                        category_k = str(cat.doc_fields.encode("ascii", "ignore"))
                        product = frappe.db.sql(
                            query.format(
                                price_query=price_query, child_groups=child_groups
                            ),
                            as_dict=1,
                        )
                        product = adjust_qty_for_expired_items(product)
                        if cint(
                            frappe.db.get_single_value(
                                "Shopping Cart Settings", "enabled"
                            )
                        ):
                            for item in product:
                                set_product_info_for_website(item)
                        category_info.product = product
                        categories.append(category_info)
                    context[self.route] = categories
                else:
                    category = ""
                    price_list = frappe.db.get_single_value(
                        "Shopping Cart Settings", "price_list"
                    )
                    price_query = ""
                    if price_list:
                        price_query = ", (select price_list_rate from `tabItem Price` where item_code = I.name and price_list = '{price_list}') as item_price".format(
                            price_list=price_list
                        )
                    query1 = """{query}""".format(query=self.query)
                    product = frappe.db.sql(
                        query1.format(price_query=price_query),
                        {"today": nowdate()},
                        as_dict=1,
                    )
                    product = adjust_qty_for_expired_items(product)
                    if cint(
                        frappe.db.get_single_value("Shopping Cart Settings", "enabled")
                    ):
                        for item in product:
                            set_product_info_for_website(item)
                    context[self.route] = product

                product_template = frappe.db.get_all(
                    "HomePage Templates",
                    fields=["page_template"],
                    filters={"name": self.view_template},
                )
                template1 = frappe.render_template(
                    product_template[0].page_template, context
                )
                page_template3 = template1
                with open(
                    os.path.join(url, "templates/pages", (self.route + "1.html")), "w"
                ) as f:
                    f.write(encode(page_template3))
        if self.select_field == "Banner":
            banner = frappe.db.get_all(
                "Banner Images", fields=["*"], filters={"parent": self.name}
            )
            context[self.route] = banner
            slider_template2 = frappe.db.get_all(
                "HomePage Templates",
                fields=["page_template"],
                filters={"name": self.view_template},
            )
            template2 = frappe.render_template(
                slider_template2[0].page_template, context
            )
            page_template4 = template2
            with open(
                os.path.join(url, "templates/pages", (self.route + "1.html")), "w"
            ) as f:
                f.write(encode(page_template4))

    def on_trash(self):
        path = frappe.get_module_path("erpnext_ecommerce")
        path_parts = path.split("/")
        path_parts = path_parts[:-1]
        url = "/".join(path_parts)
        if os.path.exists(
            os.path.join(url, "templates/pages", (self.route + "1.html"))
        ):
            os.remove(os.path.join(url, "templates/pages", (self.route + "1.html")))

    def on_update(self):
        homepage_component = frappe.db.sql(
            """
            select * 
            from `tabHome Page Component` 
            where home_page_section1=%(name)s
            """,
            {"name": self.name},
            as_dict=1,
        )
        if homepage_component:
            homepage_build = frappe.get_doc(
                "Home Page Builders", homepage_component[0].parent
            )
            homepage_build.save(ignore_permissions=True)


@frappe.whitelist(allow_guest=True)
def get_homepage_product(
    section_name=None,
    data=None,
    brands=None,
    ratings=None,
    sort_by=None,
    min_price=None,
    max_price=None,
    attributes=None,
    page_no=None,
    page_size=None,
    as_html=None,
):
    from erpnext_ecommerce.erpnext_ecommerce.api import get_product_price_details

    category_products = get_product_data(
        section=section_name,
        data=data,
        brands=None,
        ratings=ratings,
        sort_by=sort_by,
        min_price=min_price,
        max_price=max_price,
        attributes=None,
        page_no=page_no,
        page_size=page_size,
    )
    if category_products:
        for item in category_products:
            variant_of = frappe.db.get_value("Item", item.name, "variant_of")
            if variant_of:
                template_route = frappe.db.get_value("Item", variant_of, "route")
                if template_route:
                    item.route = template_route + "?variant=" + item.name
            details = get_product_price_details(item.name)
            item.price = details["price"]
            item.stock_qty = details["stock_qty"]
            item.in_stock = details["in_stock"]
            item.qty = details["qty"]
            item.uom = details["uom"]
    return category_products


@frappe.whitelist(allow_guest=True)
def get_product_data(
    section=None,
    data=None,
    brands=None,
    ratings=None,
    sort_by=None,
    min_price=None,
    max_price=None,
    attributes=None,
    page_no=None,
    page_size=None,
):
    # from erpnext_ecommerce.erpnext_ecommerce.api import get_conditions_sort
    category_list = frappe.db.get_all(
        "Child Doctype",
        fields=["doc_names", "doc_fields"],
        filters={"parent": section},
        order_by="idx",
    )
    if len(category_list) > 0:
        for cat in category_list:
            if cat.doc_names == "Item Group":
                category_info = frappe.db.get_all(
                    "Item Group",
                    filters={"name": cat.doc_fields},
                    fields=["name", "item_group_name", "route"],
                )[0]
            else:
                category_info = frappe.db.get_all(
                    "Brand",
                    filters={"name": cat.doc_fields},
                    fields=["name", "brand", "description"],
                )[0]
        # condition,sort=get_conditions_sort(brands=None,ratings=ratings,sort_by=sort_by,min_price=min_price,max_price=max_price,attributes=None)
        query = """{query} limit {page_len},{page}""".format(
            query=data,
            page_len=(int(page_no) - 1) * int(page_size),
            page=int(page_size),
        )
        result = frappe.db.sql(
            query.format(category='"' + category_info.name + '"'), as_dict=1
        )
        return result
    else:
        # condition,sort=get_conditions_sort(brands=None,ratings=ratings,sort_by=sort_by,min_price=min_price,max_price=max_price,attributes=None)
        query = """{query} limit {page_len},{page}""".format(
            query=data,
            page_len=(int(page_no) - 1) * int(page_size),
            page=int(page_size),
        )
        result = frappe.db.sql(query, as_dict=1)
        return result


@frappe.whitelist()
def get_all_products(doctype, txt, searchfield, start, page_len, filters):
    category_list = ""
    doc = filters.get("type")
    if filters.get("category_list"):
        if doc == "Item Group":
            category_list = frappe.db.sql(
                """
                select name 
                from `tabItem` 
                where (item_group in ({category}) 
                or name in (select parent from `tabWebsite Item Group`
                where item_group in ({category})))
                """.format(
                    category=filters.get("category_list")
                )
            )
        elif doc == "Brand":
            category_list = frappe.db.sql(
                """
                select name 
                from `tabItem` 
                where brand in ({brand})
                """.format(
                    brand=filters.get("category_list")
                )
            )
    return category_list


@frappe.whitelist()
def get_all_subcategories(doctype, txt, searchfield, start, page_len, filters):
    category_list1 = ""
    if filters.get("sub_category"):
        category_list1 = frappe.db.sql(
            """
            select name 
            from `tabItem Group` 
            where parent_item_group=%(category)s
            """,
            {"category": filters.get("sub_category")},
        )
    return category_list1
