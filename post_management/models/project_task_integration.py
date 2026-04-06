from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    pm_sale_order_id = fields.Many2one(
        'sale.order', 
        string='Linked Sale Order', 
        compute='_compute_pm_integration_data',
        store=True,
        readonly=False
    )
    
    pm_so_salesperson_id = fields.Many2one(
        'res.users', 
        string='Linked Salesperson', 
        compute='_compute_pm_integration_data',
        store=True,
        readonly=False
    )

    @api.depends('project_id', 'project_id.sale_order_id', 'sale_line_id.order_id', 'project_id.name')
    def _compute_pm_integration_data(self):
        for task in self:
            # Tầng 1: Lấy từ liên kết chuẩn của Odoo (Nếu có)
            so = task.project_id.sale_order_id or task.sale_line_id.order_id
            
            # Tầng 2 (Failsafe): Nếu vẫn False, thử tìm SO theo Tên Project (S00002)
            if not so and task.project_id.name:
                # Tách lấy chữ S00002 từ chuỗi "S00002 - bánh"
                so_name = task.project_id.name.split(' - ')[0].strip()
                so = self.env['sale.order'].search([('name', '=', so_name)], limit=1)
            
            # Gán kết quả
            task.pm_sale_order_id = so
            task.pm_so_salesperson_id = so.user_id if so else False