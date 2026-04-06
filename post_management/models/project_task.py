from odoo import models, fields

class ProjectTask(models.Model):
    _inherit = 'project.task' # Kế thừa module project

    # Tạo trường kết nối One2many sang bảng post.link
    post_link_ids = fields.One2many(
        'post.link', 
        'task_id', 
        string='Post Links'
    )