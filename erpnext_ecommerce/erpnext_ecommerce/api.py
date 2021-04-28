# -*- coding: utf-8 -*-
# Copyright (c) 2019, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint, flt, get_url, getdate, nowdate
from erpnext_ecommerce.erpnext_ecommerce.docevents import get_product_list_for_group
from erpnext.setup.doctype.item_group.item_group import get_child_groups
from urllib.parse import unquote

from erpnext.shopping_cart.cart import (
    _get_cart_quotation,
    apply_cart_settings,
    set_cart_count,
    get_cart_quotation,
    get_shopping_cart_menu,
    apply_shipping_rule,
)
from erpnext.shopping_cart.product_info import (
    get_product_info_for_website,
    set_product_info_for_website,
)

from erpnext_ecommerce.utils.user_context import set_user_context, create_guest_customer
from erpnext_ecommerce.utils.footer_context import set_footer_context

# from frappe.integrations.utils import get_payment_gateway_controller

import json
from erpnext.utilities.product import get_qty_in_stock


def update_website_context(context):
    country = frappe.db.get_single_value("Global Defaults", "country")
    if not country:
        return  # If Global Defaults is not set, ERPNext hasn't set

    default_currency = frappe.db.get_single_value("Global Defaults", "default_currency")

    currency = frappe.get_value("Currency", default_currency, "symbol")

    context.Currency = currency
    context.default_country = country
    context.currency_precision = frappe.db.get_single_value(
        "System Settings", "currency_precision"
    )

    # item group
    item_group = get_category_for_menu()
    context.ItemGroupList = item_group

    # user details
    set_user_context(context)
    set_footer_context(context)

    context.csrf_token = (
        frappe.local.session.data.csrf_token
        if frappe.local.session.data.csrf_token
        else ""
    )

    template = "templates/web.html"
    apps = frappe.get_all_apps(True)
    if "cmswebsite" in apps:
        template = "templates/Layout/customweb.html"
    context.layout_template = template

    route = frappe.local.request.path.strip("/ ")
    check_homepage_route(context)
    check_item_group_route(context, route)
    check_item_route(context, route)


def has_website_permission(doc, ptype, user, verbose=False):
    if "Customer" in frappe.get_roles(user):
        if doc.email_id == user:
            return True
        else:
            return False
    else:
        return False


def check_homepage_route(context):
    route = frappe.local.request.path.strip("/ ")
    if not route or route == "":
        meta_data = frappe.db.get_all(
            "Home Page Builders",
            filters={"is_active": 1},
            fields=["meta_title", "meta_description", "meta_keywords"],
        )
        if meta_data:
            if meta_data[0].meta_title:
                context.title = meta_data[0].meta_title
            if meta_data[0].meta_description:
                context.description = meta_data[0].meta_description
            if meta_data[0].meta_keywords:
                context.keywords = meta_data[0].meta_keywords


def check_item_group_route(context, route):
    if route:
        check_item_group = frappe.db.get_all("Item Group", filters={"route": route})
        if check_item_group:
            item_group = check_item_group[0].name
            # check for query parameters
            context.sort = frappe.form_dict.sort
            if not frappe.form_dict.sort:
                context.sort = "relevance"

            context.minPrice = frappe.form_dict.min
            context.maxPrice = frappe.form_dict.max
            context.brand_filter = frappe.form_dict.brand

            if frappe.form_dict.brand:
                context.brandslist = [x for x in frappe.form_dict.brand.split(",") if x.split()]

            page_length = (
                cint(
                    frappe.db.get_single_value("Products Settings", "products_per_page")
                )
                or 8
            )

            res = get_product_list_for_group(
                item_group,
                start=0,
                limit=page_length,
                sort=context.sort,
                minPrice=context.minPrice,
                maxPrice=context.maxPrice,
                brand=context.brand_filter,
            )
            if res:
                context.items_html = res["item_html"]
                context.item_group_html = res["item_group_html"]


def check_item_route(context, route):
    if route:
        check_item = frappe.db.get_all(
            "Item",
            filters={"route": route},
            fields=["image", "has_variants", "name", "slideshow"],
        )
        if check_item:
            item = check_item[0].name
            product_images = []
            if check_item[0].image:
                product_images.append({"image": check_item[0].image})
            if check_item[0].slideshow:
                product_images = frappe.db.get_all(
                    "Website Slideshow Item",
                    filters={"parent": check_item[0].slideshow},
                    fields=["image"],
                )
            context.product_images = product_images
            if check_item[0].has_variants and frappe.form_dict.variant:
                item = frappe.form_dict.variant
            price_list = frappe.db.get_single_value(
                "Shopping Cart Settings", "price_list"
            )
            item_price = frappe.db.get_all(
                "Item Price",
                filters={"item_code": item, "price_list": price_list},
                fields=["price_list_rate"],
            )
            if item_price:
                context.item_price = item_price[0].price_list_rate

        path = frappe.local.request.path
        context.currenturl = get_url() + path
        if check_item:
            get_related_products(context, check_item[0].name)


def get_related_products(context, item_code):
    price_list = frappe.db.get_single_value("Shopping Cart Settings", "price_list")
    price_query = ""
    if price_list:
        price_query = ", (select price_list_rate from `tabItem Price` where item_code = I.name and price_list = '{price_list}') as item_price".format(
            price_list=price_list
        )
    item_doc = frappe.get_doc("Item", item_code)
    item_group_list = '""'
    if item_doc.website_item_groups:
        item_group_list = ", ".join(
            [
                '"' + frappe.db.escape(i.item_group) + '"'
                for i in item_doc.website_item_groups
            ]
        )

    related_products = frappe.db.sql(
        """
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
            case when (S.actual_qty - S.reserved_qty) > 0 then 1 else 0 end as in_stock,
            I.website_warehouse,
            I.has_batch_no,
            I.variant_of{price_query}
        from `tabItem` I
        left join tabBin S on I.item_code = S.item_code and I.website_warehouse = S.warehouse
        left join tabBrand B on I.brand = B.name
        where (I.show_in_website = 1 or I.show_variant_in_website = 1)
            and I.disabled = 0
            and (I.end_of_life is null or I.end_of_life='0000-00-00' or I.end_of_life > %(today)s)
            and I.has_variants = 0 and (I.item_group = %(item_group)s or I.name in 
                (
                    select parent 
                    from `tabWebsite Item Group` 
                    where item_group in ({item_group_list})
                )
            )
            and I.name <> %(item_code)s 
            limit 12
            """.format(
            item_group_list=item_group_list, price_query=price_query
        ),
        {"today": nowdate(), "item_group": item_doc.item_group, "item_code": item_code},
        as_dict=1,
    )

    for item in related_products:
        set_product_info_for_website(item)

    context.RelatedProducts = related_products


@frappe.whitelist(allow_guest=True)
def get_search_data(searchTxt, page_no, page_len=10):
    text = "%" + searchTxt + "%"
    results = frappe.db.sql(
        """
        SELECT 
            content, 
            doctype, 
            name
        from __global_search 
        where content like %(searchTxt)s 
        and doctype in ("Item","Item Group") 
        and (case 
            when doctype="Item Group" 
                then (
                    select show_in_website 
                    from `tabItem Group` 
                    where  __global_search.name collate utf8mb4_general_ci = `tabItem Group`.name limit 1
                ) = 1 
            when doctype="Item"
                then (
                    select show_in_website 
                    from `tabItem` 
                    where  __global_search.name collate utf8mb4_general_ci = tabItem.name limit 1
                ) = 1
            end)
        order by field (doctype, "Item", "Item Group") 
        limit {limit}
        """.format(
            limit=page_len
        ),
        {"searchTxt": text},
        as_dict=1,
    )
    return results


@frappe.whitelist(allow_guest=True)
def get_category_for_menu():
    item_group = frappe.db.get_all(
        "Item Group",
        fields=["*"],
        filters={"parent_item_group": "All Item Groups", "show_in_website": 1},
        order_by="weightage",
        limit_page_length=50,
    )
    if item_group:
        for item in item_group:
            child = frappe.db.get_all(
                "Item Group",
                fields=["*"],
                filters={
                    "parent_item_group": item.item_group_name,
                    "show_in_website": 1,
                },
                order_by="weightage",
                limit_page_length=50,
            )
            first_column_items = []
            second_column_items = []
            third_column_items = []
            fourth_column_items = []
            if child:
                index = 1
                for cat in child:
                    cat.child = frappe.db.get_all(
                        "Item Group",
                        fields=["*"],
                        filters={
                            "parent_item_group": cat.item_group_name,
                            "show_in_website": 1,
                        },
                        order_by="weightage",
                        limit_page_length=50,
                    )
                    if cat.weightage == 1:
                        first_column_items.append(cat)
                    elif cat.weightage == 2:
                        second_column_items.append(cat)
                    elif cat.weightage == 3:
                        third_column_items.append(cat)
                    elif cat.weightage == 4:
                        fourth_column_items.append(cat)
                    else:
                        first_column_items.append(cat)

                    if index == 4:
                        index = 1
                    else:
                        index += 1
            item.megamenu_itemgroups = {
                "first_column_items": first_column_items,
                "second_column_items": second_column_items,
                "third_column_items": third_column_items,
                "fourth_column_items": fourth_column_items,
            }
            item.child = child

    return item_group


@frappe.whitelist(allow_guest=True)
def get_bestsellers_homepage():
    items = frappe.db.sql(
        """
        select 
            i.name, 
            i.is_stock_item, 
            i.item_name, 
            i.standard_rate, 
            i.max_discount, 
            i.thumbnail,
            i.item_group,
            i.brand,
            if(i.is_stock_item=1,sum(ifnull(bin.actual_qty-bin.reserved_qty,0)),1) as stock,
            i.route,
            b.route as brand_route,
            count(si.name) as sales_count 
        from `tabItem` i 
        left join `tabItem Variant Attribute` iva on iva.parent=i.name
        left join `tabBrand` b on b.name=i.brand 
        inner join `tabSales Order Item` si on si.item_code=i.name 
        left join `tabBin` bin on bin.item_code=i.name and bin.warehouse=i.website_warehouse 
        where (i.show_in_website=1 or i.show_variant_in_website=1) 
        and i.disabled=0 
        group by i.name having stock>0 
        order by sales_count desc 
        limit 12
        """,
        as_dict=1,
    )
    for item in items:
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
    return items


@frappe.whitelist(allow_guest=True)
def get_product_price_details(item_code):
    from erpnext.utilities.product import get_price, get_qty_in_stock

    cart_settings = frappe.get_single("Shopping Cart Settings")
    details = get_price(
        item_code,
        cart_settings.price_list,
        cart_settings.default_customer_group,
        cart_settings.company,
        1,
    )
    stock_status = get_qty_in_stock(item_code, "website_warehouse")
    in_stock = 0
    if stock_status.is_stock_item:
        if stock_status.in_stock:
            in_stock = 1
    else:
        in_stock = 1
    product_info = {
        "price": details,
        "stock_qty": stock_status.stock_qty,
        "in_stock": in_stock,
        "uom": frappe.db.get_value("Item", item_code, "stock_uom"),
        "qty": 1,
    }
    return product_info


@frappe.whitelist(allow_guest=True)
def get_brands(item_group=None, searchTxt=None):
    if item_group:
        return get_brands_category_based(item_group)
    else:
        return get_all_brands(searchTxt)


@frappe.whitelist(allow_guest=True)
def get_brands_category_based(item_group):
    child_groups = ", ".join(
        ['"' + frappe.db.escape(i[0]) + '"' for i in get_child_groups(item_group)]
    )
    brands = frappe.db.sql(
        """
        SELECT count(i.name) as item_count, b.name 
        FROM `tabItem` i, `tabBrand` b 
        WHERE i.brand=b.name 
        and i.item_group in ({item_group}) 
        and i.has_variants = 0 
        group by b.name
        """.format(
            item_group=child_groups
        ),
        as_dict=1,
    )
    return brands


@frappe.whitelist(allow_guest=True)
def get_all_brands(searchTxt=None):
    if not searchTxt:
        result = frappe.db.sql(
            """
            SELECT count(i.name) as item_count, b.name 
            FROM `tabItem` i, `tabBrand` b 
            WHERE i.brand=b.name 
            and i.has_variants = 0 
            and i.disabled=0 
            and i.show_in_website=1
            group by b.name
            """,
            as_dict=1,
        )
    else:
        result = frappe.db.sql(
            """
            SELECT count(i.name) as item_count, b.name 
            FROM `tabItem` i, `tabBrand` b 
            WHERE i.brand=b.name 
            and i.has_variants = 0 
            and i.disabled=0 
            and i.show_in_website=1 
            and i.item_name like %(txt)s 
            group by b.name
            """,
            {"txt": "%" + searchTxt + "%"},
            as_dict=1,
        )
    return result


@frappe.whitelist(allow_guest=True)
def item_attribute_filters(category=None, brand=None, searchTxt=None):
    condition = ""
    if category:
        condition += ' and i.item_group="{category}"'.format(
            category=category.replace("&amp;", "&")
        )
    if brand:
        condition += " and i.brand in ("
        for br in brand.split(","):
            condition += '"' + br + '",'
        condition = condition[:-1] + ")"
    if searchTxt:
        condition += ' and i.item_name like "%{text}%"'.format(text=searchTxt)
    attributes = frappe.db.sql(
        """
        SELECT distinct ia.name, ia.attribute_name 
        FROM `tabItem Attribute` ia, `tabItem Variant Attribute` iva, `tabItem` i 
        WHERE i.name = iva.parent 
        and iva.attribute = ia.name {condition} 
        order by ia.name
        """.format(
            condition=condition
        ),
        as_dict=1,
    )
    if attributes:
        for item in attributes:
            item.values = frappe.db.sql(
                """
                SELECT attribute_value, abbr, name 
                FROM `tabItem Attribute Value` 
                WHERE parent=%(parent)s
                """,
                {"parent": item.name},
                as_dict=1,
            )
    return attributes


@frappe.whitelist(allow_guest=True)
def get_categories_sidemenu(category):
    category = category.replace("&amp;", "&")
    current_category = frappe.get_cached_doc("Item Group", category)
    result = {}
    if (
        current_category.parent_item_group
        and current_category.parent_item_group != "All Item Group"
    ):
        parent_category = frappe.get_cached_doc(
            "Item Group", current_category.parent_item_group
        )
        result["parent_category"] = parent_category
    parent_category_child = frappe.db.get_all(
        "Item Group",
        fields=["*"],
        filters={
            "parent_item_group": current_category.parent_item_group,
            "show_in_website": 1,
        },
        limit_page_length=50,
    )
    child_categories = frappe.db.get_all(
        "Item Group",
        fields=["*"],
        filters={"parent_item_group": category, "show_in_website": 1},
        limit_page_length=50,
    )
    result["parent_category_child"] = parent_category_child
    result["child_categories"] = child_categories
    result["current_category"] = current_category
    all_categories = frappe.db.get_all(
        "Item Group",
        fields=["*"],
        filters={"parent_item_group": "All Item Groups", "show_in_website": 1},
        limit_page_length=50,
    )
    result["all_categories"] = all_categories
    return result


@frappe.whitelist(allow_guest=True)
def update_cart(item_code, qty, with_items=False):
    # Validate stock - Inserted by shankar on 4-12-19
    avaiable_stock = 0
    item = frappe.db.sql(
        """
        SELECT website_warehouse 
        FROM `tabItem` 
        WHERE name=%(name)s
        """,
        {"name": item_code},
        as_dict=1,
    )
    if item:
        item_bin = frappe.db.sql(
            """
            SELECT (actual_qty - reserved_qty) AS quantity 
            FROM `tabBin` 
            WHERE warehouse=%(warehouse)s AND 
            item_code=%(name)s
            """,
            {"warehouse": item[0].website_warehouse, "name": item_code},
            as_dict=1,
        )
        if item_bin:
            avaiable_stock = item_bin[0].quantity
    # ---- Break---- of change -Validate stock - Inserted by shankar on 4-12-19
    customer_id = (
        unquote(frappe.request.cookies.get("customer_id"))
        if frappe.request.cookies.get("customer_id")
        else None
    )
    customer = frappe.db.get_all("Customer", filters={"name": customer_id})
    if not customer:
        customer_id = None
        customer_id = create_guest_customer()
    if not customer_id:
        customer_id = create_guest_customer()
    if customer_id:
        customer = frappe.get_doc("Customer", customer_id)
        quotation = _get_cart_quotation(customer)
        empty_card = False
        qty = flt(qty)
        # ---- continue---- of change -Validate stock - Inserted by shankar on 4-12-19
        if avaiable_stock >= qty:
            # ---- Break ---- of change -Validate stock - Inserted by shankar on 4-12-19
            if qty == 0:
                quotation_items = quotation.get(
                    "items", {"item_code": ["!=", item_code]}
                )
                if quotation_items:
                    quotation.set("items", quotation_items)
                else:
                    empty_card = True
            else:
                quotation_items = quotation.get("items", {"item_code": item_code})
                if not quotation_items:
                    quotation.append(
                        "items",
                        {
                            "doctype": "Quotation Item",
                            "item_code": item_code,
                            "qty": qty,
                        },
                    )
                else:
                    quotation_items[0].qty = qty
            apply_cart_settings(quotation=quotation)

            quotation.flags.ignore_permissions = True
            quotation.payment_schedule = []
            if not empty_card:
                quotation.run_method("calculate_taxes_and_totals")
                quotation.save()
            else:
                quotation.delete()
                quotation = None
            set_cart_count(quotation)

            context = get_cart_quotation(quotation)

            if cint(with_items):
                return {
                    "items": frappe.render_template(
                        "templates/includes/cart/cart_items.html", context
                    ),
                    "taxes": frappe.render_template(
                        "templates/includes/order/order_taxes.html", context
                    ),
                }
            else:
                return {
                    "name": quotation.name if not empty_card else None,
                    "shopping_cart_menu": get_shopping_cart_menu(context),
                }
        # ---- continue---- of change -Validate stock - Inserted by shankar on 4-12-19
        else:
            return {
                "status": "failed",
                "message": "Sorry! Only " + str(int(avaiable_stock)) + " is available.",
                "qty": avaiable_stock,
            }
        # ---- End ---- of change -Validate stock - Inserted by shankar on 4-12-19


@frappe.whitelist(allow_guest=True)
def place_order(bill_addr, ship_addr, ship_method=None, payment_method=None):
    cart_settings = frappe.db.get_value(
        "Shopping Cart Settings",
        None,
        ["company", "allow_items_not_in_stock"],
        as_dict=1,
    )
    customer_id = (
        unquote(frappe.request.cookies.get("customer_id"))
        if frappe.request.cookies.get("customer_id")
        else None
    )
    if customer_id:
        customer = frappe.get_doc("Customer", customer_id)
        additional_payment_charges = 0
        payment_method_setting = None
        if ship_method:
            apply_shipping_rule(ship_method)
        if payment_method:
            payment_method_setting = frappe.get_doc("Payment Method", payment_method)
            payment_charges = payment_method_setting.payment_charges
            additional_payment_charges = payment_charges
        if additional_payment_charges > 0:
            default_account = frappe.get_value(
                "Company", cart_settings.company, "default_cash_account"
            )
            cart_quotation = _get_cart_quotation(customer)
            cart_quotation.append(
                "taxes",
                {
                    "total": cart_quotation.grand_total + additional_payment_charges,
                    "account_head": default_account,
                    "base_total": cart_quotation.base_grand_total
                    + additional_payment_charges,
                    "base_tax_amount": additional_payment_charges,
                    "tax_amount_after_discount_amount": additional_payment_charges,
                    "base_tax_amount_after_discount_amount": additional_payment_charges,
                    "tax_amount": additional_payment_charges,
                    "charge_type": "Actual",
                    "description": "Payment charge",
                },
            )
            cart_quotation.grand_total = (
                cart_quotation.grand_total + additional_payment_charges
            )
            cart_quotation.base_grand_total = (
                cart_quotation.base_grand_total + additional_payment_charges
            )
            cart_quotation.base_rounded_total = (
                cart_quotation.base_rounded_total + additional_payment_charges
            )
            cart_quotation.rounded_total = (
                cart_quotation.rounded_total + additional_payment_charges
            )
            cart_quotation.flags.ignore_permissions = True
            cart_quotation.save(ignore_permissions=True)
            frappe.db.commit()
        quotation = _get_cart_quotation(customer)
        quotation.company = cart_settings.company
        quotation.customer_address = bill_addr
        quotation.shipping_address_name = ship_addr
        quotation.shipping_method = ship_method
        quotation.payment_method = payment_method
        if not quotation.get("customer_address"):
            frappe.throw(
                _("{0} is required").format(
                    _(quotation.meta.get_label("customer_address"))
                )
            )
        for qp in quotation.payment_schedule:
            if qp.due_date < getdate(nowdate()):
                qp.due_date = getdate(nowdate())
        warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")

        quotation.flags.ignore_permissions = True
        quotation.save()
        quotation.submit()

        if quotation.quotation_to == "Lead" and quotation.party_name:
            # company used to create customer accounts
            frappe.defaults.set_user_default("company", quotation.company)

        from erpnext.selling.doctype.quotation.quotation import _make_sales_order

        sales_order = frappe.get_doc(
            _make_sales_order(quotation.name, ignore_permissions=True)
        )
        if not sales_order.set_warehouse:
            if warehouse:
                sales_order.set_warehouse = warehouse

        # if ship_method:
        # 	sales_order.shipping_rule = ship_method

        items = sales_order.items
        for item in items:
            item = item.as_dict()
            item.reserved_warehouse, is_stock_item = frappe.db.get_value(
                "Item", item.item_code, ["website_warehouse", "is_stock_item"]
            )
            item["warehouse"] = sales_order.set_warehouse

            if is_stock_item:
                item_stock = get_qty_in_stock(item.item_code, "website_warehouse")
                if not cart_settings.allow_items_not_in_stock:
                    if item.qty > item_stock.stock_qty[0][0]:
                        frappe.throw(
                            _("Only {0} in stock for item {1}").format(
                                item_stock.stock_qty[0][0], item.item_code
                            )
                        )

        sales_order.set("items", items)
        sales_order.flags.ignore_permissions = True
        sales_order.save()
        sales_order.submit()

        if hasattr(frappe.local, "cookie_manager"):
            frappe.local.cookie_manager.delete_cookie("cart_count")
        redirect_url = "/thankyou?id=" + sales_order.name
        if payment_method_setting:
            if payment_method_setting.gateway_settings:
                controller = frappe.get_single(payment_method_setting.gateway_settings)
                payment_details = {
                    "amount": sales_order.grand_total,
                    "customer_name": sales_order.customer_name,
                    "reference_doctype": "Sales Order",
                    "reference_docname": sales_order.name,
                }
                redirect_url = controller.get_payment_url(**payment_details)

        return {
            "status": "Success",
            "name": sales_order.name,
            "redirect_url": redirect_url,
        }


def login_customer(login_manager):
    check_customer = frappe.db.sql(
        """
        select c.name 
        from `tabCustomer` c 
        inner join `tabDynamic Link` dl on dl.link_doctype = "Customer" 
        and dl.link_name = c.name 
        and dl.parenttype = "Contact" 
        inner join `tabContact` ca on ca.name = dl.parent 
        where ca.user = %(user)s
        """,
        {"user": frappe.session.user},
        as_dict=1,
    )
    if check_customer and check_customer[0].name:
        frappe.local.cookie_manager.set_cookie("customer_id", check_customer[0].name)
        move_cart_items(
            check_customer[0].name, frappe.request.cookies.get("guest_customer")
        )


def logout_customer(login_manager):
    frappe.local.cookie_manager.delete_cookie("customer_id")
    frappe.local.cookie_manager.delete_cookie("guest_customer")


def move_cart_items(customer, guest_id=None):
    try:
        if not guest_id:
            guest = frappe.request.cookies.get("guest_customer")
        else:
            guest = guest_id
        if guest:
            guest_cart = frappe.db.get_all(
                "Quotation",
                filters={
                    "quotation_to": "Customer",
                    "party_name": unquote(guest),
                    "order_type": "Shopping Cart",
                },
            )
            if guest_cart:
                # commented by Shankar on 21-12-2020
                # doc = frappe.get_doc('Quotation', guest_cart[0].name)
                # doc.party_name = customer
                # doc.title = frappe.db.get_value('Customer', customer, 'customer_name')
                # doc.save(ignore_permissions=True)

                # inserted by Shankar on 21-12-2020
                cart = frappe.db.get_all(
                    "Quotation",
                    filters={
                        "party_name": customer,
                        "order_type": "Shopping Cart",
                        "status": "Draft",
                    },
                    fields=["*"],
                )
                if cart:
                    cartitems = frappe.db.get_all(
                        "Quotation Item", filters={"parent": cart[0].name}
                    )
                    if cartitems:
                        g_cart_items = frappe.db.get_all(
                            "Quotation Item",
                            filters={"parent": guest_cart[0].name},
                            fields=["item_code", "name", "qty", "rate"],
                        )
                        if g_cart_items:
                            for item in g_cart_items:
                                g_item = frappe.db.get_all(
                                    "Quotation Item",
                                    fields=["item_code", "name", "qty", "rate"],
                                    filters={
                                        "parent": cart[0].name,
                                        "item_code": item.item_code,
                                    },
                                )
                                if g_item:
                                    item_info = frappe.get_doc(
                                        "Item", g_item[0].item_code
                                    )
                                    if item_info:
                                        qty = float(item.qty) + float(g_item[0].qty)
                                        if item_info.is_stock_item == 0:
                                            frappe.db.sql(
                                                """
                                                update `tabQuotation Item` 
                                                set qty={qty} 
                                                where name=%(name)s
                                                """.format(
                                                    qty=float(qty)
                                                ),
                                                {"name": g_item[0].name},
                                            )
                                            frappe.db.sql(
                                                """
                                                update `tabQuotation Item` 
                                                set amount={total} 
                                                where name=%(name)s
                                                """.format(
                                                    total=float(item.rate) * float(qty)
                                                ),
                                                {"name": g_item[0].name},
                                            )
                                        else:
                                            avaiable_stock = 0
                                            item_detail = frappe.db.sql(
                                                """
                                                SELECT website_warehouse 
                                                FROM `tabItem` 
                                                WHERE name=%(name)s
                                                """,
                                                {"name": g_item[0].item_code},
                                                as_dict=1,
                                            )
                                            if item_detail:
                                                item_bin = frappe.db.sql(
                                                    """
                                                    SELECT (actual_qty - reserved_qty) AS quantity
                                                    FROM `tabBin`
                                                    WHERE warehouse=%(warehouse)s
                                                    AND item_code=%(name)s
                                                    """,
                                                    {
                                                        "warehouse": item_detail[
                                                            0
                                                        ].website_warehouse,
                                                        "name": g_item[0].item_code,
                                                    },
                                                    as_dict=1,
                                                )
                                                if item_bin:
                                                    avaiable_stock = item_bin[
                                                        0
                                                    ].quantity
                                                    if avaiable_stock >= qty:
                                                        frappe.db.sql(
                                                            """
                                                            update `tabQuotation Item` 
                                                            set qty={qty} 
                                                            where name=%(name)s
                                                            """.format(
                                                                qty=float(qty)
                                                            ),
                                                            {"name": g_item[0].name},
                                                        )
                                                        frappe.db.sql(
                                                            """
                                                            update `tabQuotation Item` 
                                                            set amount={total} 
                                                            where name=%(name)s
                                                            """.format(
                                                                total=float(item.rate)
                                                                * float(qty)
                                                            ),
                                                            {"name": g_item[0].name},
                                                        )
                                    frappe.db.sql(
                                        """
                                        delete from `tabQuotation Item` 
                                        where name=%(name)s
                                        """,
                                        {"name": item.name},
                                    )
                                else:
                                    frappe.db.sql(
                                        """
                                        update `tabQuotation Item`
                                        set parent=%(parent)s
                                        where name=%(name)s
                                        """,
                                        {"parent": cart[0].name, "name": item.name},
                                    )
                    else:
                        frappe.db.sql(
                            """
                            update `tabQuotation Item` 
                            set parent=%(n_parent)s 
                            where parent=%(parent)s
                            """,
                            {"n_parent": cart[0].name, "parent": guest_cart[0].name},
                        )
                    parent_doc = frappe.get_doc("Quotation", cart[0].name)
                    parent_doc.save(ignore_permissions=True)
                else:
                    doc = frappe.get_doc("Quotation", guest_cart[0].name)
                    doc.party_name = customer
                    doc.contact_person = None
                    doc.contact_email = frappe.session.user
                    doc.title = frappe.db.get_value(
                        "Customer", customer, "customer_name"
                    )
                    doc.save(ignore_permissions=True)
                # end of insertion done by shankar on 21-12-2020
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "ecommerce_business_store.ecommerce_business_store.api.move_cart_items",
        )


@frappe.whitelist(allow_guest=True)
def get_cartItems(customer):
    quotation = frappe.get_all(
        "Quotation",
        fields=["name"],
        filters={"party_name": customer, "order_type": "Shopping Cart", "docstatus": 0},
        order_by="modified desc",
        limit_page_length=1,
    )
    if quotation:
        qdoc = frappe.get_doc("Quotation", quotation[0].name)
        return qdoc


@frappe.whitelist(allow_guest=True)
def get_WishlistItems(customer):
    quotation = frappe.get_all(
        "Wishlist",
        fields=["name"],
        filters={"party_name": customer, "order_type": "Wishlist", "docstatus": 0},
        order_by="modified desc",
        limit_page_length=1,
    )
    if quotation:
        qdoc = frappe.get_doc("Wishlist", quotation[0].name)
        return qdoc


@frappe.whitelist(allow_guest=True)
def insert_newcustomer(data):
    response = json.loads(data)
    customer = frappe.new_doc("Customer")
    customer.customer_name = response.get("customer_name")
    customer.save(ignore_permissions=True)
    insert_user(
        response.get("email_id"),
        response.get("first_name"),
        response.get("last_name"),
        response.get("new_password"),
    )
    insert_contact(customer, response.get("email_id"), response.get("mobile"))


def insert_user(email, first_name, last_name, new_password):
    user = frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "send_welcome_email": 0,
        }
    ).insert(ignore_permissions=True)
    usr_doc = frappe.get_doc("User", user.name)
    usr_doc.new_password = new_password
    usr_doc.append("roles", {"role": "Customer"})
    usr_doc.save(ignore_permissions=True)
    return usr_doc


def insert_contact(customer, email, mobile_no):
    contact = frappe.new_doc("Contact")
    contact.first_name = customer.customer_name
    contact.email_id = email
    contact.user = email
    contact.mobile_no = mobile_no
    contact.phone = mobile_no
    contact.append("links", {"link_doctype": "Customer", "link_name": customer.name})
    contact.save(ignore_permissions=True)
    frappe.db.set_value("Customer", customer.name, "email_id", email)
    frappe.db.set_value("Customer", customer.name, "mobile_no", mobile_no)
    return contact


@frappe.whitelist(allow_guest=True)
def get_customer_info():
    customer_id = (
        unquote(frappe.request.cookies.get("customer_id"))
        if frappe.request.cookies.get("customer_id")
        else None
    )
    if customer_id:
        customer_info = frappe.db.get_all(
            "Customer",
            filters={"name": customer_id},
            fields=["customer_name", "name", "email_id", "mobile_no"],
        )
        if customer_info:
            address = frappe.db.sql(
                """
                select a.* 
                from `tabAddress` a 
                left join `tabDynamic Link` d on d.parent = a.name
                where d.link_doctype = "Customer" 
                and d.link_name = %(cust_id)s
                group by a.name
                """,
                {"cust_id": customer_info[0].name},
                as_dict=1,
            )
            customer_info[0].customer_address = address
            return customer_info[0]


@frappe.whitelist(allow_guest=True)
def insert_address(data):
    response = json.loads(data)
    address = frappe.new_doc("Address")
    address.address_line1 = response.get("addr1")
    address.address_line2 = response.get("addr2")
    address.city = response.get("city")
    address.county = response.get("county")
    address.state = response.get("state")
    address.country = response.get("country")
    # address.pincode = response.get('pincode')
    address.address_title = response.get("addrtitle")
    for item in response.get("links"):
        address.append("links", item)
    address.save(ignore_permissions=True)
    return address


@frappe.whitelist(allow_guest=True)
def edit_address(data):
    response = json.loads(data)
    address = frappe.get_doc("Address", response.get("name"))
    address.address_line1 = response.get("addr1")
    address.address_line2 = response.get("addr2")
    address.city = response.get("city")
    address.state = response.get("state")
    address.country = response.get("country")
    # address.pincode = response.get('pincode')
    address.address_title = response.get("addrtitle")
    address.save(ignore_permissions=True)
    return address


@frappe.whitelist(allow_guest=True)
def delete_address(id):
    frappe.db.sql(
        """
        delete from `tabDynamic Link`
        where parent=%(parent)s
        """,
        {"parent": id},
    )
    frappe.db.sql(
        """
        delete from `tabAddress` 
        where name=%(name)s
        """,
        {"name": id},
    )


@frappe.whitelist(allow_guest=True)
def update_customer(data):
    response = json.loads(data)
    # customer = frappe.get_doc('Customer',response.get('name'))
    # customer.customer_name = response.get('cus_name')
    # customer.save(ignore_permissions=True)
    customer_email = frappe.get_doc("Customer", response.get("name"))
    if response.get("update_pswrd"):
        user = frappe.get_doc("User", customer_email.email_id)
        user.new_password = response.get("update_pswrd")
        user.save(ignore_permissions=True)

    customer = frappe.db.sql(
        """
        UPDATE `tabCustomer` 
        SET
            customer_name=%(cus_name)s,
            customer_phone=%(customer_phone)s,
            mobile=%(mobile)s,
            mobile_2=%(mobile_2)s,
            home=%(home)s,
            office=%(office)s
        WHERE name=%(name)s
        """,
        {
            "cus_name": response.get("cus_name"),
            "name": response.get("name"),
            "customer_phone": response.get("customer_phone"),
            "mobile": response.get("mobile"),
            "mobile_2": response.get("mobile_2"),
            "home": response.get("home"),
            "office": response.get("office"),
        },
    )

    user = frappe.db.sql(
        """
        UPDATE `tabUser`
        SET
            full_name=%(cus_name)s,
            first_name=%(cus_name)s,
            last_name=''
        WHERE name=%(name)s
        """,
        {"cus_name": response.get("cus_name"), "name": customer_email.email_id},
    )

    return customer


@frappe.whitelist(allow_guest=True)
def movetocart(user, name, customer, qty=1):
    wishlist_items = frappe.get_doc("Wishlist Item", name)
    if wishlist_items:
        item_code = wishlist_items.item_name
        with_items = False
        avaiable_stock = 0
        item = frappe.db.sql(
            """
            SELECT website_warehouse
            FROM `tabItem` 
            WHERE name=%(name)s
            """,
            {"name": item_code},
            as_dict=1,
        )
        if item:
            item_bin = frappe.db.sql(
                """
                SELECT (actual_qty - reserved_qty) AS quantity
                FROM `tabBin`
                WHERE warehouse=%(warehouse)s
                AND item_code=%(name)s
                """,
                {"warehouse": item[0].website_warehouse, "name": item_code},
                as_dict=1,
            )
            if item_bin:
                avaiable_stock = item_bin[0].quantity
        customer_id = (
            unquote(frappe.request.cookies.get("customer_id"))
            if frappe.request.cookies.get("customer_id")
            else None
        )
        customer = frappe.db.get_all("Customer", filters={"name": customer_id})
        if not customer:
            customer_id = None
            customer_id = create_guest_customer()
        if not customer_id:
            customer_id = create_guest_customer()
        if customer_id:
            customer = frappe.get_doc("Customer", customer_id)
            quotation = _get_cart_quotation(customer)
            empty_card = False
            qty = flt(qty)
            if avaiable_stock >= qty:
                if qty == 0:
                    quotation_items = quotation.get(
                        "items", {"item_code": ["!=", item_code]}
                    )
                    if quotation_items:
                        quotation.set("items", quotation_items)
                    else:
                        empty_card = True
                else:
                    quotation_items = quotation.get("items", {"item_code": item_code})
                    if not quotation_items:
                        quotation.append(
                            "items",
                            {
                                "doctype": "Quotation Item",
                                "item_code": item_code,
                                "qty": qty,
                            },
                        )
                    else:
                        quotation_items[0].qty = qty
                apply_cart_settings(quotation=quotation)

                quotation.flags.ignore_permissions = True
                quotation.payment_schedule = []
                if not empty_card:
                    quotation.run_method("calculate_taxes_and_totals")
                    quotation.save()
                else:
                    quotation.delete()
                    quotation = None
                set_cart_count(quotation)

                context = get_cart_quotation(quotation)

                wishlistitems = frappe.get_doc("Wishlist Item", name)
                wishlistitems.delete()
                if cint(with_items):
                    return {
                        "items": frappe.render_template(
                            "templates/includes/cart/cart_items.html", context
                        ),
                        "taxes": frappe.render_template(
                            "templates/includes/order/order_taxes.html", context
                        ),
                    }
                else:
                    return {
                        "name": quotation.name if not empty_card else None,
                        "shopping_cart_menu": get_shopping_cart_menu(context),
                    }
            else:
                return {
                    "status": "failed",
                    "message": "Sorry! Only "
                    + str(int(avaiable_stock))
                    + " is available.",
                    "qty": avaiable_stock,
                }


@frappe.whitelist(allow_guest=True)
def deleteWishlistItems(name):
    wishlistitems = frappe.get_doc("Wishlist Item", name)
    wishlistitems.delete()
    return {"status": "success"}


@frappe.whitelist(allow_guest=True)
def add_to_wishlist(item_code):
    qty = 1
    customer_id = (
        unquote(frappe.request.cookies.get("customer_id"))
        if frappe.request.cookies.get("customer_id")
        else None
    )
    customer = frappe.db.get_all("Customer", filters={"name": customer_id})
    if not customer:
        customer_id = None
        customer_id = create_guest_customer()
    if not customer_id:
        customer_id = create_guest_customer()
    if customer_id:
        customer = frappe.get_doc("Customer", customer_id)
        quotation = _get_wishlist_quotation(customer)
        empty_card = False
        qty = flt(qty)
        avaiable_stock = 1
        if avaiable_stock >= qty:
            if qty == 0:
                quotation_items = quotation.get(
                    "items", {"item_code": ["!=", item_code]}
                )
                if quotation_items:
                    quotation.set("items", quotation_items)
                else:
                    empty_card = True
            else:
                quotation_items = quotation.get("items", {"item_code": item_code})
                if not quotation_items:
                    quotation.append(
                        "items",
                        {
                            "doctype": "Wishlist Item",
                            "item_code": item_code,
                            "item_name": item_code,
                            "qty": qty,
                            "uom": "Nos",
                        },
                    )
                else:
                    quotation_items[0].qty = qty
            # apply_cart_settings(quotation=quotation)

            quotation.flags.ignore_permissions = True
            quotation.payment_schedule = []
            if not empty_card:
                # quotation.run_method("calculate_taxes_and_totals")
                quotation.save()
            else:
                quotation.delete()
                quotation = None

            context = get_cart_quotation(quotation)
            with_items = False
            if cint(with_items):
                return {
                    "items": frappe.render_template(
                        "templates/includes/cart/cart_items.html", context
                    ),
                    "taxes": frappe.render_template(
                        "templates/includes/order/order_taxes.html", context
                    ),
                }
            else:
                return {
                    "name": quotation.name if not empty_card else None,
                    # 'shopping_cart_menu': get_shopping_cart_menu(context)
                }
        else:
            return {
                "status": "failed",
                "message": "Sorry! Only " + str(int(avaiable_stock)) + " is available.",
                "qty": avaiable_stock,
            }


def _get_wishlist_quotation(party=None):
    if not party:
        customer_id = (
            unquote(frappe.request.cookies.get("customer_id"))
            if frappe.request.cookies.get("customer_id")
            else None
        )
        customer = frappe.db.get_all("Customer", filters={"name": customer_id})
        if not customer:
            customer_id = None
            customer_id = create_guest_customer()
        if not customer_id:
            customer_id = create_guest_customer()
        party = frappe.get_doc("Customer", customer_id)
    quotation = frappe.get_all(
        "Wishlist",
        fields=["name"],
        filters={"party_name": party.name, "order_type": "Wishlist", "docstatus": 0},
        order_by="modified desc",
        limit_page_length=1,
    )

    if quotation:
        qdoc = frappe.get_doc("Wishlist", quotation[0].name)
    else:
        company = frappe.db.get_value("Shopping Cart Settings", None, ["company"])
        qdoc = frappe.get_doc(
            {
                "doctype": "Wishlist",
                "quotation_to": "Customer",
                "company": company,
                "order_type": "Wishlist",
                "status": "Draft",
                "docstatus": 0,
                "__islocal": 1,
                "party_name": party.name,
            }
        )

        qdoc.contact_person = frappe.db.get_value(
            "Contact", {"email_id": frappe.session.user}
        )
        qdoc.contact_email = frappe.session.user

        qdoc.flags.ignore_permissions = True
    return qdoc


@frappe.whitelist(allow_guest=True)
def calculate_shipping_charges(shipping_method, total):
    customer_id = unquote(frappe.request.cookies.get("customer_id"))
    # total = 0
    shipping_charges = 0
    if customer_id:
        quotation = frappe.get_all(
            "Quotation",
            fields=["name"],
            filters={
                "party_name": customer_id,
                "order_type": "Shopping Cart",
                "docstatus": 0,
            },
            order_by="modified desc",
            limit_page_length=1,
        )
        if quotation:
            qdoc = frappe.get_doc("Quotation", quotation[0].name)
            total = qdoc.total
            if total > 0:
                based_on = frappe.get_value(
                    "Shipping Rule", shipping_method, "calculate_based_on"
                )
                if based_on == "Fixed":
                    shipping_charges = frappe.get_value(
                        "Shipping Rule", shipping_method, "shipping_amount"
                    )
                if based_on == "Net Total":
                    shipping_amount = frappe.db.sql(
                        """
                        SELECT shipping_amount 
                        FROM `tabShipping Rule Condition`
                        WHERE from_value<=%(total)s 
                        AND to_value>=%(total)s
                        AND parent=%(shipping_method)s
                        """,
                        {"total": total, "shipping_method": shipping_method},
                        as_dict=1,
                    )
                    if shipping_amount:
                        shipping_charges = shipping_amount[0].shipping_amount
                total = flt(total) + shipping_charges
                return {"total": total, "shipping_charges": shipping_charges}


@frappe.whitelist(allow_guest=True)
def make_payment_entry(order_id, request_id):
    # order_id ==frappe.form_dict.id
    payment_request_id = frappe.get_doc("Integration Request", request_id)
    payment_request_id.status = "Completed"
    payment_request_id.save(ignore_permissions=True)
    from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

    si = make_sales_invoice(order_id, ignore_permissions=True)
    si.posting_date = getdate()
    si.due_date = getdate()
    si.docstatus = 1
    si.save(ignore_permissions=True)
    frappe.db.commit()
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

    payment_entry = get_payment_entry("Sales Invoice", si.name)
    payment_entry.reference_no = si.name
    payment_entry.reference_date = getdate()
    payment_entry.docstatus = 1
    payment_entry.mode_of_payment = "Credit Card"
    payment_entry.save(ignore_permissions=True)
