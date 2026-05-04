from odoo import models, fields

class LarkStatusMapping(models.Model):
    _name = 'lark.status.mapping'
    _description = 'Ánh xạ trạng thái Task Odoo và Lark'

    odoo_stage_id = fields.Many2one('project.task.type', string='Trạng thái Odoo (Stage)', required=True)
    lark_status_key = fields.Selection([
        ('todo', 'Chưa hoàn thành (To-do)'),
        ('done', 'Đã hoàn thành (Done)')
    ], string='Hành động trên Lark', required=True, default='todo')
    
    _sql_constraints = [
        ('unique_stage_mapping', 'unique(odoo_stage_id)', 'Mỗi trạng thái Odoo chỉ được ánh xạ một lần!')
    ]