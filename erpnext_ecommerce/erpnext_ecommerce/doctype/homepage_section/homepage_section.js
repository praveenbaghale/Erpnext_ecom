// Copyright (c) 2019, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Homepage Section', {
	refresh: function(frm) {
		if(frm.doc.child_doc){
		if(frm.doc.child_doc.length > 0){
			cur_frm.set_query("product_id","product", function(doc, cdt, cdn) {
			 	let category_list=''
		        if(frm.doc.child_doc){
		            $(frm.doc.child_doc).each(function(k,v){
		                category_list=category_list+'"'+v.doc_fields+'",';
		            })
		        }
				category_list=category_list.slice(0,-1)
	            return {
	            	query: "erpnext_ecommerce.erpnext_ecommerce.doctype.homepage_section.homepage_section.get_all_products",
	                filters: {
	                	category_list:category_list,
	                	type:frm.doc.select_doctype
	                },
	            }
	        });
		}
	}
		
	},
	select_field: function(frm){
		if(frm.doc.select_field=="Category Tabs"){
			frm.set_query("select_category", function() {
	            return {
	                "filters": {
	                    "parent_item_group": 'All Item Groups'
	                }
	            }
	        })
		}
	},
	select_category: function(frm){
		frm.set_query("sub_child_category","categories", function(doc, cdt, cdn) {
	            return {
	            	query: "erpnext_ecommerce.erpnext_ecommerce.doctype.homepage_section.homepage_section.get_all_subcategories",
	                filters: {
	                	sub_category:frm.doc.select_category
	                },
	            }
	        });
	}
});
frappe.ui.form.on('Static Product Page',{
	product_add:function(frm, cdt, cdn){
		frappe.model.set_value(cdt,cdn,'doctypes',frm.doc.select_doctype);
	}
});
frappe.ui.form.on('Static Product Page',{
	product_add:function(frm, cdt, cdn){
		if(frm.doc.child_doc.length > 0){
			frappe.model.set_value(cdt,cdn,'doctypes','Item');
		}
	}
});
frappe.ui.form.on('Child Doctype',{
	child_doc_add:function(frm, cdt, cdn){
		frappe.model.set_value(cdt,cdn,'doc_names',frm.doc.select_doctype);
	}
});
