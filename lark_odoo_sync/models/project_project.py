import requests
import json
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ProjectProject(models.Model):
    _inherit = 'project.project'

    # Giữ nguyên cờ đồng bộ đã tạo từ trước
    lark_sync_enabled = fields.Boolean(string='Đồng bộ với Lark', default=False, help='Bật cờ này để hệ thống tự động đẩy Task của dự án này sang Lark.')
    
    # 2 trường định danh mới để lưu ID của Task List
    lark_tasklist_id = fields.Char(string='Lark Tasklist ID', copy=False, readonly=True)
    lark_tasklist_url = fields.Char(string='Link Lark Tasklist', copy=False, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        projects = super(ProjectProject, self).create(vals_list)
        for project in projects:
            if project.lark_sync_enabled:
                project._sync_tasklist_to_lark('create')
        return projects

    def write(self, vals):
        res = super(ProjectProject, self).write(vals)
        for project in self:
            # Nếu người dùng bật cờ đồng bộ nhưng chưa có ID trên Lark -> Tạo mới
            if 'lark_sync_enabled' in vals and project.lark_sync_enabled and not project.lark_tasklist_id:
                project._sync_tasklist_to_lark('create')
            
            # Nếu đổi tên dự án và đã có ID trên Lark -> Cập nhật tên
            elif 'name' in vals and project.lark_tasklist_id:
                project._sync_tasklist_to_lark('update')
        return res

    def _sync_tasklist_to_lark(self, mode='create'):
        """Hàm gọi API Lark để tạo hoặc sửa Task List"""
        self.ensure_one()
        token = self.env['ir.config_parameter'].sudo().get_param('lark_odoo_sync.tenant_token')
        if not token:
            raise UserError("Lỗi Đồng Bộ: Không tìm thấy Token Lark.")

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json; charset=utf-8'
        }

        if mode == 'create':
            url = "https://open.larksuite.com/open-apis/task/v2/tasklists"
            payload_data = {"name": self.name}
            
            # Gán Quản lý dự án làm Chủ danh sách bên Lark
            if self.user_id and self.user_id.lark_user_id:
                payload_data["members"] = [{
                    "id": self.user_id.lark_user_id,
                    "type": "user",
                    "role": "editor"
                }]

            response = requests.post(url, headers=headers, data=json.dumps(payload_data), timeout=10)
            
        elif mode == 'update':
            url = f"https://open.larksuite.com/open-apis/task/v2/tasklists/{self.lark_tasklist_id}"
            payload_data = {
                "tasklist": {"name": self.name},
                "update_fields": ["name"]
            }
            response = requests.patch(url, headers=headers, data=json.dumps(payload_data), timeout=10)

        res_json = response.json()
        if res_json.get('code') == 0:
            if mode == 'create':
                lark_data = res_json.get('data', {}).get('tasklist', {})
                self.sudo().write({
                    'lark_tasklist_id': lark_data.get('guid'),
                    'lark_tasklist_url': lark_data.get('url')
                })
        else:
            raise UserError(f"Lỗi từ Lark khi thao tác Task List: {res_json.get('msg')}")

    def action_force_sync_from_lark(self):
        """Kéo toàn bộ Task từ Lark Task List về Odoo khi người dùng bấm nút"""
        self.ensure_one()
        
        if not getattr(self, 'lark_sync_enabled', True) or not getattr(self, 'lark_tasklist_id', False):
            raise UserError("Dự án này chưa được cấu hình đồng bộ Lark hoặc thiếu Mã Task List.")
            
        token = self.env['ir.config_parameter'].sudo().get_param('lark_odoo_sync.tenant_token')
        if not token:
            raise UserError("Thiếu cấu hình Tenant Token của Lark.")
        
        url = f"https://open.larksuite.com/open-apis/task/v2/tasklists/{self.lark_tasklist_id}/tasks"
        headers = {'Authorization': f'Bearer {token}'}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            res_json = response.json()
            
            if res_json.get('code') == 0:
                tasks = res_json.get('data', {}).get('items', [])
                count_new = 0
                count_updated = 0 # Thêm biến đếm số lượng Task được cập nhật
                
                # Duyệt qua từng Task mà Lark trả về
                for task in tasks:
                    lark_id = task.get('guid')
                    
                    exists = self.env['project.task'].sudo().search([('lark_task_id', '=', lark_id)], limit=1)
                    
                    if not exists:
                        # 1. NẾU CHƯA CÓ -> TẠO MỚI
                        self.env['project.task'].sudo()._sync_new_task_from_lark(lark_id)
                        count_new += 1
                    else:
                        # 2. NẾU ĐÃ CÓ -> ÉP CẬP NHẬT LẠI TOÀN BỘ (Tên, Ghi chú, Trạng thái, Người phụ trách)
                        exists.sudo()._sync_from_lark()
                        count_updated += 1
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Đồng bộ Lark thành công!',
                        'message': f'Đã tạo mới {count_new} công việc và cập nhật {count_updated} công việc hiện có.',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(f"Lark từ chối trả dữ liệu: {res_json.get('msg')}")
                
        except UserError as ue:
            raise ue
        except Exception as e:
            raise UserError(f"Lỗi kết nối khi quét dữ liệu: {str(e)}")