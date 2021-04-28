# -*- coding: utf-8 -*-
# Copyright (c) 2020, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, nowdate, getdate
from frappe import _

from erpnext.controllers.selling_controller import SellingController

form_grid_templates = {"items": "templates/form_grid/item_grid.html"}


class Wishlist(SellingController):
    def set_indicator(self):
        if self.docstatus == 1:
            self.indicator_color = "blue"
            self.indicator_title = "Submitted"
        if self.valid_till and getdate(self.valid_till) < getdate(nowdate()):
            self.indicator_color = "darkgrey"
            self.indicator_title = "Expired"

    def validate(self):
        # super(Wishlist, self).validate()
        self.set_status()
        self.update_opportunity()
        self.validate_uom_is_integer("stock_uom", "qty")
        self.validate_valid_till()
        self.set_customer_name()
        if self.items:
            self.with_items = 1
            self.check_item_price_list()

    def validate_valid_till(self):
        if self.valid_till and self.valid_till < self.transaction_date:
            frappe.throw(_("Valid till date cannot be before transaction date"))

    def check_item_price_list(self):
        for item in self.items:
            item_price = frappe.db.get_all(
                "Item Price",
                fields=["price_list_rate"],
                filters={"item_code": item.item_code, "selling": 1},
            )
            if item_price:
                item.rate = item_price[0].price_list_rate

    def has_sales_order(self):
        return frappe.db.get_value(
            "Sales Order Item", {"prevdoc_docname": self.name, "docstatus": 1}
        )

    def update_lead(self):
        if self.quotation_to == "Lead" and self.party_name:
            frappe.get_doc("Lead", self.party_name).set_status(update=True)

    def set_customer_name(self):
        if self.party_name and self.quotation_to == "Customer":
            self.customer_name = frappe.db.get_value(
                "Customer", self.party_name, "customer_name"
            )
        elif self.party_name and self.quotation_to == "Lead":
            lead_name, company_name = frappe.db.get_value(
                "Lead", self.party_name, ["lead_name", "company_name"]
            )
            self.customer_name = company_name or lead_name

    def update_opportunity(self):
        for opportunity in list(set([d.prevdoc_docname for d in self.get("items")])):
            if opportunity:
                self.update_opportunity_status(opportunity)

        if self.opportunity:
            self.update_opportunity_status()

    def update_opportunity_status(self, opportunity=None):
        if not opportunity:
            opportunity = self.opportunity

        opp = frappe.get_doc("Opportunity", opportunity)
        opp.status = None
        opp.set_status(update=True)

    def declare_order_lost(self, reason):
        if not self.has_sales_order():
            frappe.db.set(self, "status", "Lost")
            frappe.db.set(self, "order_lost_reason", reason)
            self.update_opportunity()
            self.update_lead()
        else:
            frappe.throw(_("Cannot set as Lost as Sales Order is made."))

    def on_submit(self):
        # Check for Approving Authority
        frappe.get_doc("Authorization Control").validate_approving_authority(
            self.doctype, self.company, self.base_grand_total, self
        )

        # update enquiry status
        self.update_opportunity()
        self.update_lead()

    def on_cancel(self):
        # update enquiry status
        self.set_status(update=True)
        self.update_opportunity()
        self.update_lead()

    def print_other_charges(self, docname):
        print_lst = []
        for d in self.get("taxes"):
            lst1 = []
            lst1.append(d.description)
            lst1.append(d.total)
            print_lst.append(lst1)
        return print_lst

    def on_recurring(self, reference_doc, auto_repeat_doc):
        self.valid_till = None
