from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead' # Kế thừa model Cơ hội

    # Ví dụ thêm trường: Phân loại khách hàng (VIP, Thường, Tiềm năng)
    x_customer_rank = fields.Selection([
        ('vip', 'Khách hàng VIP'),
        ('normal', 'Khách hàng thường'),
        ('potential', 'Tiềm năng')
    ], string="Xếp hạng khách", default='normal')