from odoo import fields, models

class CrmLead(models.Model):
    _inherit = "crm.lead"

    x_lead_flow = fields.Selection(
        selection=[("inbound", "Inbound"), ("outbound", "Outbound")],
        string="Lead Flow",
        default="inbound",
        index=True,
    )