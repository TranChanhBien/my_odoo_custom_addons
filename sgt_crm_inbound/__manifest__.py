{
    "name": "SGT CRM Inbound",
    "version": "1.0.0",
    "depends": ["crm", "sgt_crm_flow_core"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/inbound_menu.xml",
    ],
    "installable": True,
    "application": True,
}