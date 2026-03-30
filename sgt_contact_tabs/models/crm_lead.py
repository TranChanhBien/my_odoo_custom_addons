from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # THÊM MỚI: Trường phân loại luồng cơ hội (Inbound/Outbound)
    x_lead_flow = fields.Selection([
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound')
    ], string="Lead Flow", help="Phân loại nguồn cơ hội là Inbound hay Outbound")