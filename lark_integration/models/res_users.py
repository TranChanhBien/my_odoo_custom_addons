from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    lark_open_id = fields.Char(string='Lark Open ID', help='Lấy từ Lark Developer Console')
