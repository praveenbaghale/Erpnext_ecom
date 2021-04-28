# -*- coding: utf-8 -*-
# Copyright (c) 2019, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


class HomepageBanner(Document):
    def on_update(self):
        self.get_banners()
        home_page_banner = frappe.db.get_all(
            "Banner Images", fields=["*"], filters={"banner_name": self.name}
        )
        if home_page_banner and home_page_banner[0].parent:
            homepage_section = frappe.get_doc(
                "Homepage Section", home_page_banner[0].parent
            )
            if homepage_section:
                homepage_section.save(ignore_permissions=True)

    def on_trash(self):
        banner_images = frappe.db.get_all(
            "Banner Images", fields=["*"], filters={"banner_name": self.name}
        )
        if banner_images:
            banner = frappe.get_doc("Banner Images", banner_images[0].name)
            banner.delete()
            homepage_section = frappe.get_doc(
                "Homepage Section", banner_images[0].parent
            )
            homepage_section.save(ignore_permissions=True)

    def get_banners(self):
        home_page = frappe.db.get_all("Homepage Section", fields=["name"])
        if self.section == "Best Sellers":
            best_sellers_banner = _get_homepage_banner(self.section)
            if len(home_page) > 0:
                for best_sel_banner in best_sellers_banner:
                    banner_set = frappe.db.get_all(
                        "Banner Images", filters={"banner_name": best_sel_banner.name}
                    )
                    if banner_set:
                        template = frappe.get_doc("Banner Images", banner_set[0].name)
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "image_name",
                            best_sel_banner.banner_title,
                        )
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "banner_image",
                            best_sel_banner.banner_image,
                        )
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "column_layout",
                            best_sel_banner.layout,
                        )
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "redirect_url",
                            best_sel_banner.redirect_url,
                        )
                    else:
                        homepage_banner = frappe.get_doc(
                            {
                                "doctype": "Banner Images",
                                "parent": best_sellers_banner[0]["name"],
                                "parenttype": "Homepage Section",
                                "parentfield": "banner_images",
                                "banner_image": best_sel_banner.banner_image,
                                "column_layout": best_sel_banner.layout,
                                "image_name": best_sel_banner.banner_title,
                                "redirect_url": best_sel_banner.redirect_url,
                                "banner_name": best_sel_banner.name,
                            }
                        ).insert(ignore_permissions=True)
        if self.section == "Slider":
            slider_banner = _get_homepage_banner(self.section)
            if len(home_page) > 0:
                if slider_banner:
                    for best_sel_banner in slider_banner:
                        banner_set = frappe.db.get_all(
                            "Banner Images",
                            filters={"banner_name": best_sel_banner.name},
                        )
                        print(banner_set)
                        if banner_set:
                            template = frappe.get_doc(
                                "Banner Images", banner_set[0].name
                            )
                            frappe.db.set_value(
                                "Banner Images",
                                template.name,
                                "image_name",
                                best_sel_banner.banner_title,
                            )
                            frappe.db.set_value(
                                "Banner Images",
                                template.name,
                                "banner_image",
                                best_sel_banner.banner_image,
                            )
                            frappe.db.set_value(
                                "Banner Images",
                                template.name,
                                "column_layout",
                                best_sel_banner.layout,
                            )
                            frappe.db.set_value(
                                "Banner Images",
                                template.name,
                                "redirect_url",
                                best_sel_banner.redirect_url,
                            )
                        else:
                            frappe.get_doc(
                                {
                                    "doctype": "Banner Images",
                                    "parent": self.section,
                                    "parenttype": "Homepage Section",
                                    "parentfield": "banner_images",
                                    "banner_image": best_sel_banner.banner_image,
                                    "column_layout": best_sel_banner.layout,
                                    "image_name": best_sel_banner.banner_title,
                                    "redirect_url": best_sel_banner.redirect_url,
                                    "banner_name": best_sel_banner.name,
                                }
                            ).insert(ignore_permissions=True)

        if self.section == "New Arrivals":
            new_arrival_banner = _get_homepage_banner(self.section)
            if len(home_page) > 0:
                for best_sel_banner in new_arrival_banner:
                    banner_set = frappe.db.get_all(
                        "Banner Images", filters={"banner_name": best_sel_banner.name}
                    )
                    if banner_set:
                        template = frappe.get_doc("Banner Images", banner_set[0].name)
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "image_name",
                            best_sel_banner.banner_title,
                        )
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "banner_image",
                            best_sel_banner.banner_image,
                        )
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "column_layout",
                            best_sel_banner.layout,
                        )
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "redirect_url",
                            best_sel_banner.redirect_url,
                        )
                    else:
                        homepage_banner = frappe.get_doc(
                            {
                                "doctype": "Banner Images",
                                "parent": self.section,
                                "parenttype": "Homepage Section",
                                "parentfield": "banner_images",
                                "banner_image": best_sel_banner.banner_image,
                                "column_layout": best_sel_banner.layout,
                                "image_name": best_sel_banner.banner_title,
                                "redirect_url": best_sel_banner.redirect_url,
                                "banner_name": best_sel_banner.name,
                            }
                        ).insert(ignore_permissions=True)
        if self.section == "Featured Products":
            featured_product_banner = _get_homepage_banner(self.section)
            if len(home_page) > 0:
                for best_sel_banner in featured_product_banner:
                    banner_set = frappe.db.get_all(
                        "Banner Images", filters={"banner_name": best_sel_banner.name}
                    )
                    if banner_set:
                        template = frappe.get_doc("Banner Images", banner_set[0].name)
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "image_name",
                            best_sel_banner.banner_title,
                        )
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "banner_image",
                            best_sel_banner.banner_image,
                        )
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "column_layout",
                            best_sel_banner.layout,
                        )
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "redirect_url",
                            best_sel_banner.redirect_url,
                        )
                    else:
                        homepage_banner = frappe.get_doc(
                            {
                                "doctype": "Banner Images",
                                "parent": self.section,
                                "parenttype": "Homepage Section",
                                "parentfield": "banner_images",
                                "banner_image": best_sel_banner.banner_image,
                                "column_layout": best_sel_banner.layout,
                                "image_name": best_sel_banner.banner_title,
                                "redirect_url": best_sel_banner.redirect_url,
                                "banner_name": best_sel_banner.name,
                            }
                        ).insert(ignore_permissions=True)
        if self.section == "Category":
            category_banner = _get_homepage_banner(self.section)
            if len(home_page) > 0:
                for best_sel_banner in category_banner:
                    banner_set = frappe.db.get_all(
                        "Banner Images", filters={"banner_name": best_sel_banner.name}
                    )
                    if banner_set:
                        template = frappe.get_doc("Banner Images", banner_set[0].name)
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "image_name",
                            best_sel_banner.banner_title,
                        )
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "banner_image",
                            best_sel_banner.banner_image,
                        )
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "column_layout",
                            best_sel_banner.layout,
                        )
                        frappe.db.set_value(
                            "Banner Images",
                            template.name,
                            "redirect_url",
                            best_sel_banner.redirect_url,
                        )
                    else:
                        homepage_banner = frappe.get_doc(
                            {
                                "doctype": "Banner Images",
                                "parent": self.section,
                                "parenttype": "Homepage Section",
                                "parentfield": "banner_images",
                                "banner_image": best_sel_banner.banner_image,
                                "column_layout": best_sel_banner.layout,
                                "image_name": best_sel_banner.banner_title,
                                "redirect_url": best_sel_banner.redirect_url,
                                "banner_name": best_sel_banner.name,
                            }
                        ).insert(ignore_permissions=True)


def _get_homepage_banner(section):
    return frappe.db.get_all(
        "Homepage Banner",
        fields=["name", "banner_image", "banner_title", "layout", "redirect_url"],
        filters={"section": section},
    )
