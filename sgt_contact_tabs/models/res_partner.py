from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # 1. Cơ hội (Opportunities)
    def action_view_opportunity_custom(self):
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        action['domain'] = [('partner_id', '=', self.id)]
        return action

    # 2. Đơn hàng (Sales)
    def action_view_sale_order_custom(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action['domain'] = [('partner_id', 'child_of', self.id)]
        return action

    # 3. Hóa đơn (Invoices)
    def action_view_invoice_custom(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [('partner_id', 'child_of', self.id)]
        return action

    # 4. Cuộc hẹn (Meetings)
    def action_view_calendar_event_custom(self):
        action = self.env["ir.actions.actions"]._for_xml_id("calendar.action_calendar_event")
        action['domain'] = [('partner_ids', 'in', self.ids)]
        return action