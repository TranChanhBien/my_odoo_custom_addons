from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    lark_user_id = fields.Char(string='Lark User ID', help='Mã định danh của nhân sự này trên Lark', copy=False)