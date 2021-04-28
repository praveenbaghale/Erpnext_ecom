# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import frappe.utils


def get_context(context):
    # path = frappe.local.request.path
    # MetaInfo=frappe.db.get_all('Page Seo', fields=['*'],filters={'page':'About','restaurant':context.Restaurant.name}, limit_page_length=8)
    # if len(MetaInfo)>0:
    # 	context.MetaTitle=MetaInfo[0].meta_title
    # 	context.MetaDescription=MetaInfo[0].meta_description
    # 	context.MetaKeywords=MetaInfo[0].meta_keywords
    about_us = frappe.db.get_single_value("About Us Settings", "company_introduction")
    context.about_us = about_us
    context.mobile_page_title = "About Us"
