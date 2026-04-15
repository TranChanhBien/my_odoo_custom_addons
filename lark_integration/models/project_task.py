from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    lark_task_guid = fields.Char(string='Lark Task GUID', copy=False, index=True)

    def _get_lark_token(self):
        app_id = "cli_a959cc9161f9de17"
        app_secret = "sZIkHurUwarSNpUczYjCHe6CVZbm5JYi"
        url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
        try:
            res = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=10)
            return res.json().get('tenant_access_token') if res.status_code == 200 else None
        except Exception: return None

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        if self.env.context.get("from_lark"): return tasks
        token = self._get_lark_token()
        if token:
            for task in tasks:
                if task.project_id.id == 2:
                    self._sync_to_lark(task, token, is_update=False)
        return tasks

    def write(self, vals):
        # Chống lặp GUID
        if len(vals) == 1 and 'lark_task_guid' in vals:
            return super().write(vals)
        result = super().write(vals)
        if self.env.context.get("from_lark"): return result
        
        if any(k in vals for k in ['name', 'description', 'user_ids']):
            token = self._get_lark_token()
            if token:
                for task in self:
                    if task.project_id.id == 2 and task.lark_task_guid:
                        self._sync_to_lark(task, token, is_update=True)
        return result

    def _sync_to_lark(self, task, token, is_update=False):
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        assignee = task.user_ids[0] if task.user_ids else False
        # Field của bạn là lark_open_id
        lark_open_id = getattr(assignee, 'lark_open_id', False)

        task_payload = {"summary": task.name, "description": task.description or ""}
        if lark_open_id:
            task_payload["members"] = [{"id": lark_open_id, "type": "user", "role": "assignee"}]

        try:
            if is_update:
                url = f"https://open.larksuite.com/open-apis/task/v2/tasks/{task.lark_task_guid}"
                requests.patch(url, headers=headers, json={"task": task_payload}, timeout=10)
            else:
                url = "https://open.larksuite.com/open-apis/task/v2/tasks"
                res = requests.post(url, headers=headers, json=task_payload, timeout=10)
                if res.status_code == 200:
                    guid = res.json().get('data', {}).get('task', {}).get('guid')
                    task.sudo().with_context(from_lark=True).lark_task_guid = guid
        except Exception as e: _logger.error(f">>> SYNC ERROR: {e}")