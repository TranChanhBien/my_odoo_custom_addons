from odoo import models, fields

class ContactSearchPanelField(models.Model):
    _name = 'sgt.contact.search.panel.field'
    _description = 'Cấu hình bộ lọc Search Panel cho Contacts'
    _order = 'sequence'

    name = fields.Char(string='Tên hiển thị', required=True)
    field_id = fields.Many2one(
    'ir.model.fields', 
    string='Trường dữ liệu', 
    domain="[('model', '=', 'res.partner'), ('ttype', 'in', ['selection', 'many2one'])]",
    required=True,
    ondelete='cascade'
)
    icon = fields.Char(string='Icon (FontAwesome)', default='fa-users')
    sequence = fields.Integer(default=10)
    is_active = fields.Boolean(string='Kích hoạt', default=True)