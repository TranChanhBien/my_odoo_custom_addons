from odoo import models, fields

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    is_lark_default_stage = fields.Boolean(string='Mặc định cho Task từ Lark', default=False, 
        help="Task tạo mới từ Lark sẽ được tự động xếp vào cột này.")
    
    is_lark_done_stage = fields.Boolean(string='Đồng bộ "Hoàn thành" từ Lark', default=False,
        help="Khi Task được đánh dấu Done trên Lark, nó sẽ chuyển sang cột này.")