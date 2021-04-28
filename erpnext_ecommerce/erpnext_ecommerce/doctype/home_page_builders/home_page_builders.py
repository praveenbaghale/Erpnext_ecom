# -*- coding: utf-8 -*-
# Copyright (c) 2019, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import frappe, os, re
from frappe.utils import touch_file, encode, cstr, flt


class HomePageBuilders(Document):
    def validate(self):
        if not self.file_name:
            self.file_name = (
                re.sub("[^a-zA-Z0-9 ]", "", self.name).lower().replace(" ", "_")
            )
        path = None
        try:
            path = frappe.get_module_path("erpnext_ecommerce")
        except Exception as e:
            try:
                path = frappe.get_module_path("restaurant_cms_website")
            except Exception as e:
                path = None
        if path:
            path_parts = path.split("/")
            path_parts = path_parts[:-1]
            url = "/".join(path_parts)
            home_template = self.get_homepage_data1()
            with open(
                os.path.join(url, "templates/pages", (self.file_name + ".html")), "w"
            ) as f:
                f.write(home_template)

    def get_homepage_data1(self):
        builder = frappe.db.get_all(
            "Home Page Builders",
            fields=["name"],
            filters={"name": self.name, "is_active": 1},
        )
        page_template = '{% extends "templates/layout/customweb.html" %}{% block loader %}{% include "/templates/pages/homepageloader.html" %}{% endblock %}{% block content %}'
        if builder:
            for build in builder:
                component = frappe.db.get_all(
                    "Home Page Component",
                    fields=["home_page_section1", "name"],
                    filters={"parent": build.name},
                    order_by="idx",
                )
                if component:
                    for item in component:
                        homepagedata = frappe.db.get_all(
                            "Homepage Section",
                            fields=["*"],
                            filters={"name": item.home_page_section1},
                        )
                        if homepagedata:
                            for item1 in homepagedata:
                                context = {}
                                page_template += (
                                    '{% include "templates/pages/'
                                    + item1.route
                                    + '1.html" %}'
                                )

        if self.custom_css:
            context = {}
            page_template += "<style>"
            template = frappe.render_template(self.custom_css, context)
            page_template += template
            page_template += "</style>"
        page_template += "{% endblock %}"
        if self.custom_js:
            page_template += "{% block script %}"
            context = {}
            template = frappe.render_template(self.custom_js, context)
            page_template += template
            page_template += "{% endblock %}"
        return page_template

    def on_trash(self):
        path = frappe.get_module_path("erpnext_ecommerce")
        path_parts = path.split("/")
        path_parts = path_parts[:-1]
        url = "/".join(path_parts)
        if os.path.exists(
            os.path.join(url, "templates/pages", (self.file_name + ".html"))
        ):
            os.remove(os.path.join(url, "templates/pages", (self.file_name + ".html")))
