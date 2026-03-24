{
    "name": "SGT CRM Lead Default & View",
    "version": "1.0.0",
    "category": "CRM",
    "summary": "Đặt mặc định Inbound và hiển thị field để chỉnh sửa",
    "depends": ["crm", "sgt_crm_flow_core", "sgt_crm_inbound", "sgt_crm_outbound"],
    "data": [
        "views/crm_lead_views.xml",
    ],
    "installable": True,
    "application": True,
}