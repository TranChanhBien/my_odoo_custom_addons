from odoo import models, fields

class CrmLead(models.Model):
    _inherit = "crm.lead"

    # Gán lại mặc định để đảm bảo ưu tiên của module mới
    x_lead_flow = fields.Selection(
        selection_add=[("inbound", "Inbound"), ("outbound", "Outbound")],
        default="inbound"
    )