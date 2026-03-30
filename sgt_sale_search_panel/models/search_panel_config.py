from odoo import models, fields

class SaleSearchPanelField(models.Model):
    _name = 'sgt.sale.search.panel.field'
    _description = 'Cấu hình bộ lọc Search Panel cho Sales'
    _order = 'sequence'

    name = fields.Char(string='Tên hiển thị', required=True)
    field_id = fields.Many2one(
        'ir.model.fields', 
        string='Trường dữ liệu', 
        domain="[('model', '=', 'sale.order'), ('ttype', 'in', ['selection', 'many2one'])]",
        required=True,
        ondelete='cascade'
    )
    icon = fields.Char(string='Icon (FontAwesome)', default='fa-filter')
    sequence = fields.Integer(default=10)
    is_active = fields.Boolean(string='Kích hoạt', default=True)