{
    "name": "SGT Contact Embedded Tabs",
    "version": "1.0.0",
    "category": "Tools",
    "summary": "Hiển thị Opportunities, Sales, Invoices và Meetings trực tiếp trong tab của Contacts",
    "depends": ["base", "contacts", "crm", "sale_management", "account", "calendar", "sgt_crm_flow_core"],
    "data": [
        "views/crm_lead_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}