import requests
import json
import logging
import datetime
import time
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    lark_task_id = fields.Char(string='Lark Task ID', copy=False, index=True, readonly=True)
    lark_url = fields.Char(string='Link Lark Task', copy=False, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Override hàm tạo để đẩy task sang Lark"""
        # 1. Tạo task trong database Odoo trước
        tasks = super(ProjectTask, self).create(vals_list)

        # Kiểm tra cờ chống vòng lặp
        if self.env.context.get('from_lark'):
            return tasks

        # 2. Duyệt từng task vừa tạo để kiểm tra điều kiện đồng bộ
        for task in tasks:
            # Chỉ đồng bộ nếu Dự án được bật cờ 'lark_sync_enabled'
            if task.project_id and task.project_id.lark_sync_enabled:
                task._sync_to_lark('create')
        
        return tasks

    def _sync_to_lark(self, mode='create'):
        """Hàm xử lý gọi API Lark"""
        self.ensure_one()
        
        # Lấy Token từ kho lưu trữ
        token = self.env['ir.config_parameter'].sudo().get_param('lark_odoo_sync.tenant_token')
        if not token:
            _logger.error("Không tìm thấy Lark Tenant Token để đồng bộ.")
            return

        # Đóng gói dữ liệu theo Mapping đã chốt
        url = "https://open.larksuite.com/open-apis/task/v2/tasks"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json; charset=utf-8'
        }

        # Mapping các trường cơ bản
        payload_data = {
            "summary": self.name,
            "description": self.description or "",
        }

        # Mapping người phụ trách (Assignees)
        members = []
        for user in self.user_ids:
            if user.lark_user_id:
                members.append({
                    "id": user.lark_user_id,
                    "type": "user",
                    "role": "assignee"
                })
        if members:
            payload_data["members"] = members

        # Mapping Deadline (Lark dùng timestamp milisecond)
        if self.date_deadline:
            if isinstance(self.date_deadline, datetime.datetime):
                deadline_ts = int(self.date_deadline.timestamp() * 1000)
            else:
                dt = datetime.datetime.combine(self.date_deadline, datetime.time(23, 59, 59))
                deadline_ts = int(dt.timestamp() * 1000)
                
            # SỬA Ở ĐÂY: Từ khóa chuẩn là timestamp
            payload_data["due"] = {
                "timestamp": str(deadline_ts),
                "is_all_day": False
            }

        try:
            # Thực hiện đẩy dữ liệu
            response = requests.post(url, headers=headers, data=json.dumps(payload_data), timeout=10)
            res_json = response.json()

            if res_json.get('code') == 0:
                lark_task = res_json.get('data', {}).get('task', {})
                
                # KHAI BÁO BIẾN lark_id TRƯỚC KHI SỬ DỤNG
                lark_id = lark_task.get('guid')
                
                # Cập nhật ngược lại ID và URL từ Lark trả về
                self.with_context(from_lark=True).sudo().write({
                    'lark_task_id': lark_id, # Dùng luôn biến lark_id cho gọn
                    'lark_url': lark_task.get('url')
                })

                # ----- CODE BỔ SUNG: NHÉT TASK VÀO LARK TASK LIST -----
                if self.project_id and self.project_id.lark_tasklist_id:
                    tasklist_id = self.project_id.lark_tasklist_id
                    
                    # Lúc này lark_id đã có giá trị nên URL sẽ hợp lệ
                    add_to_list_url = f"https://open.larksuite.com/open-apis/task/v2/tasks/{lark_id}/add_tasklist"
                    add_payload = json.dumps({
                        "tasklist_guid": tasklist_id
                    })
                    
                    # Gọi API để gán Task vào List
                    res_add = requests.post(add_to_list_url, headers=headers, data=add_payload, timeout=10)
                    
                    # KÍCH HOẠT CÒI BÁO ĐỘNG
                    if res_add.json().get('code') != 0:
                        error_msg = res_add.json().get('msg', 'Không rõ nguyên nhân')
                        raise UserError(f"Lark tạo Task thành công nhưng TỪ CHỐI đưa vào List!\nLý do từ Lark: {error_msg}\nMã lỗi: {res_add.json().get('code')}")
                # ------------------------------------------------------

                _logger.info(f"Đồng bộ thành công Task {self.name} sang Lark.")
            else:
                _logger.error(f"Lark API Error: {res_json.get('msg')}")
        
        except Exception as e:
            _logger.error(f"Lỗi kết nối khi đồng bộ task: {str(e)}")

    def write(self, vals):
        """Override hàm write để đồng bộ cập nhật sang Lark"""
        res = super(ProjectTask, self).write(vals)

        if self.env.context.get('from_lark'):
            return res

        sync_fields = ['name', 'description', 'date_deadline', 'stage_id']
        if any(field in vals for field in sync_fields):
            for task in self:
                if task.lark_task_id:
                    task._sync_update_to_lark(vals)
                    
        return res

    def _sync_update_to_lark(self, vals):
        """Hàm đóng gói dữ liệu và gọi API PATCH để update Task trên Lark"""
        self.ensure_one()
        token = self.env['ir.config_parameter'].sudo().get_param('lark_odoo_sync.tenant_token')
        if not token:
            raise UserError("Lỗi Đồng Bộ: Không tìm thấy Token Lark. Hãy kiểm tra lại kết nối.")

        url = f"https://open.larksuite.com/open-apis/task/v2/tasks/{self.lark_task_id}"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json; charset=utf-8'
        }

        task_data = {}
        update_fields = []

        if 'name' in vals:
            task_data['summary'] = self.name
            update_fields.append('summary')
            
        if 'description' in vals:
            task_data['description'] = self.description or ""
            update_fields.append('description')
            
        if 'date_deadline' in vals:
            if self.date_deadline:
                if isinstance(self.date_deadline, datetime.datetime):
                    deadline_ts = int(self.date_deadline.timestamp() * 1000)
                else:
                    dt = datetime.datetime.combine(self.date_deadline, datetime.time(23, 59, 59))
                    deadline_ts = int(dt.timestamp() * 1000)
                
                # SỬA Ở ĐÂY: Đổi "time" thành "timestamp" và thêm cờ is_all_day
                task_data['due'] = {
                    "timestamp": str(deadline_ts),
                    "is_all_day": False
                }
            else:
                # Nếu người dùng xóa ngày deadline trên Odoo
                task_data['due'] = {
                    "timestamp": "0", 
                    "is_all_day": False
                } 
            update_fields.append('due')

        # Xử lý cập nhật Trạng thái (Kanban Stage)
        if 'stage_id' in vals:
            new_stage_id = vals.get('stage_id')
            # Truy vấn xem Stage mới này được cấu hình ánh xạ là gì
            mapping = self.env['lark.status.mapping'].search([('odoo_stage_id', '=', new_stage_id)], limit=1)
            
            if mapping:
                if mapping.lark_status_key == 'done':
                    # Đánh dấu Hoàn thành: Lark v2 yêu cầu truyền timestamp thời điểm hoàn thành
                    completed_ts = str(int(time.time() * 1000))
                    task_data['completed_at'] = completed_ts
                else:
                    # Đánh dấu Chưa hoàn thành (Hủy tích xanh): Truyền 0
                    task_data['completed_at'] = "0"
                
                update_fields.append('completed_at')

        if not update_fields:
            return

        payload = json.dumps({
            "task": task_data,
            "update_fields": update_fields
        })

        try:
            response = requests.patch(url, headers=headers, data=payload, timeout=10)
            res_json = response.json()
            
            # KÍCH HOẠT CÒI BÁO ĐỘNG: Nếu Lark trả về lỗi, ném thẳng lên màn hình
            if res_json.get('code') != 0:
                error_msg = res_json.get('msg', 'Không rõ nguyên nhân')
                raise UserError(f"Lark từ chối cập nhật Task!\nLý do từ Lark: {error_msg}\nMã lỗi: {res_json.get('code')}")
                
        except requests.exceptions.RequestException as e:
            # Lỗi mất mạng hoặc sai URL
            raise UserError(f"Lỗi mạng khi kết nối tới máy chủ Lark: {str(e)}")

    def _sync_from_lark(self):
        """Kéo dữ liệu mới nhất từ Lark về Odoo khi có Webhook báo cập nhật"""
        self.ensure_one()
        token = self.env['ir.config_parameter'].sudo().get_param('lark_odoo_sync.tenant_token')
        if not token or not self.lark_task_id:
            return

        # Gọi ngược API Lark v2 để lấy trạng thái mới nhất của Task
        url = f"https://open.larksuite.com/open-apis/task/v2/tasks/{self.lark_task_id}"
        headers = {'Authorization': f'Bearer {token}'}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            res_json = response.json()

            if res_json.get('code') == 0:
                lark_task = res_json.get('data', {}).get('task', {})
                update_vals = {}
                
                # 1. Đồng bộ Tên
                if 'summary' in lark_task:
                    update_vals['name'] = lark_task['summary']
                
                # 2. Đồng bộ Mô tả
                if 'description' in lark_task:
                    update_vals['description'] = lark_task['description']

                # 3. Đồng bộ Trạng thái Kanban theo logic NÚT GẠT (Cấu hình UI mới)
                completed_at = lark_task.get('completed_at', '0')
                is_done = completed_at != '0'
                target_stage = False
                
                # Ưu tiên tìm Stage có chứa nút gạt trong chính Dự án này
                if self.project_id:
                    domain_done = [('is_lark_done_stage', '=', True), ('project_ids', 'in', self.project_id.id)]
                    domain_default = [('is_lark_default_stage', '=', True), ('project_ids', 'in', self.project_id.id)]
                    
                    if is_done:
                        target_stage = self.env['project.task.type'].sudo().search(domain_done, limit=1)
                    if not target_stage: 
                        target_stage = self.env['project.task.type'].sudo().search(domain_default, limit=1)
                
                # Nếu không tìm thấy, quét rộng ra toàn hệ thống
                if not target_stage:
                    if is_done:
                        target_stage = self.env['project.task.type'].sudo().search([('is_lark_done_stage', '=', True)], limit=1)
                    else:
                        target_stage = self.env['project.task.type'].sudo().search([('is_lark_default_stage', '=', True)], limit=1)

                if target_stage:
                    update_vals['stage_id'] = target_stage.id

                # 4. Đồng bộ Người phụ trách (Assignee)
                lark_members = lark_task.get('members', [])
                odoo_user_ids = []
                
                for member in lark_members:
                    if member.get('role') == 'assignee' and member.get('type') == 'user':
                        lark_user_id = member.get('id')
                        user = self.env['res.users'].sudo().search([('lark_user_id', '=', lark_user_id)], limit=1)
                        if user:
                            odoo_user_ids.append(user.id)
                
                if odoo_user_ids:
                    update_vals['user_ids'] = [(6, 0, odoo_user_ids)]

                # 5. Ghi dữ liệu vào Database
                if update_vals:
                    # from_lark=True để ngăn vòng lặp ngược
                    self.with_context(from_lark=True).sudo().write(update_vals)
                    _logger.info(f"Đồng bộ ngược thành công Task '{self.name}' từ Lark.")

        except Exception as e:
            _logger.error(f"Lỗi khi kéo dữ liệu từ Lark: {str(e)}")

    @api.model
    def _sync_new_task_from_lark(self, lark_task_id):
        """Hàm xử lý tạo mới Task trên Odoo khi nhận tín hiệu từ Lark"""
        existing_task = self.search([('lark_task_id', '=', lark_task_id)], limit=1)
        if existing_task:
            return

        ICPSudo = self.env['ir.config_parameter'].sudo()
        token = ICPSudo.get_param('lark_odoo_sync.tenant_token')
        if not token:
            return

        url = f"https://open.larksuite.com/open-apis/task/v2/tasks/{lark_task_id}"
        headers = {'Authorization': f'Bearer {token}'}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            res_json = response.json()

            if res_json.get('code') == 0:
                # CHÍNH LÀ DÒNG NÀY: Khai báo biến lark_task rất dễ bị mất khi copy/paste
                lark_task = res_json.get('data', {}).get('task', {})
                
                # 1. BỘ LỌC DỰ ÁN
                project_id = False
                tasklists = lark_task.get('tasklists', [])
                for tl in tasklists:
                    lark_list_id = tl.get('tasklist_guid')
                    project = self.env['project.project'].sudo().search([('lark_tasklist_id', '=', lark_list_id)], limit=1)
                    if project:
                        project_id = project.id
                        break
                
                if not project_id:
                    return

                # 2. CHUẨN BỊ DỮ LIỆU
                create_vals = {
                    'name': lark_task.get('summary', 'New Lark Task'),
                    'description': lark_task.get('description', ''),
                    'lark_task_id': lark_task.get('guid'),
                    'lark_url': lark_task.get('url'),
                    'project_id': project_id,
                }

                # Mapping Hạn chót
                due_info = lark_task.get('due', {})
                if due_info and due_info.get('timestamp') and due_info.get('timestamp') != '0':
                    timestamp_sec = int(due_info['timestamp']) / 1000.0
                    create_vals['date_deadline'] = fields.Datetime.from_timestamp(timestamp_sec)

                # 3. XỬ LÝ TRẠNG THÁI (STAGE)
                completed_at = lark_task.get('completed_at', '0')
                is_done = completed_at != '0'
                target_stage = False
                
                if project_id:
                    domain_done = [('is_lark_done_stage', '=', True), ('project_ids', 'in', project_id)]
                    domain_default = [('is_lark_default_stage', '=', True), ('project_ids', 'in', project_id)]
                    
                    if is_done:
                        target_stage = self.env['project.task.type'].sudo().search(domain_done, limit=1)
                    if not target_stage: 
                        target_stage = self.env['project.task.type'].sudo().search(domain_default, limit=1)
                
                if not target_stage:
                    if is_done:
                        target_stage = self.env['project.task.type'].sudo().search([('is_lark_done_stage', '=', True)], limit=1)
                    else:
                        target_stage = self.env['project.task.type'].sudo().search([('is_lark_default_stage', '=', True)], limit=1)

                if target_stage:
                    create_vals['stage_id'] = target_stage.id

                # 4. LƯU VÀO DATABASE
                new_task = self.with_context(from_lark=True).sudo().create(create_vals)
                
                # Gọi lại hàm cập nhật để map Assignee
                new_task._sync_from_lark()

        except Exception as e:
            # Đổi câu báo lỗi để biết chính xác nó đang nổ ở hàm nào
            raise Exception(f"Lỗi ở hàm Tạo Mới (_sync_new_task_from_lark): {str(e)}")

    