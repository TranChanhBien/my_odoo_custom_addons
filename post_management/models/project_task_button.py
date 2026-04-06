from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    # Trường tính toán tổng số link của toàn bộ Project
    project_post_link_count = fields.Integer(compute='_compute_project_post_link_count', string='Project Links Count')

    def _compute_project_post_link_count(self):
        for task in self:
            if task.project_id:
                # Đếm tất cả link có project_id trùng với project của task hiện tại
                count = self.env['post.link'].search_count([('project_id', '=', task.project_id.id)])
                task.project_post_link_count = count
            else:
                task.project_post_link_count = 0

    def action_view_project_post_links(self):
        """Hành động khi bấm vào nút: Mở danh sách toàn bộ link của Project"""
        self.ensure_one()
        return {
            'name': 'All Project Post Links',
            'type': 'ir.actions.act_window',
            'res_model': 'post.link',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.project_id.id)], # Lọc đúng project
            'context': {'default_project_id': self.project_id.id},
            'target': 'current',
        }