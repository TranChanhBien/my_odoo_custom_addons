import json
import logging
import requests
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

class LarkWebhookController(http.Controller):

    @http.route("/lark/webhook/task", type="http", auth="public", methods=["POST"], csrf=False)
    def lark_task_webhook(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
        except Exception:
            return Response("Invalid JSON", status=400)

        # 1. Challenge xác thực URL
        if data.get("type") == "url_verification":
            return Response(json.dumps({"challenge": data.get("challenge")}), content_type="application/json")

        header = data.get('header', {})
        event = data.get('event', {})
        event_type = header.get('event_type')

        # 2. Chống lặp: Nếu operator là con BOT thì bỏ qua
        operator = event.get("operator", {})
        if operator.get("operator_type") == "app":
            return Response(json.dumps({"code": 200}), content_type="application/json")

        # 3. Xử lý khi có update từ Lark
        # Cả 2 event: task.task.updated_v1 hoặc task.task.update_user_access_v2 đều lấy được guid
        guid = event.get("task_id") or event.get("task", {}).get("task_guid") or event.get("task_guid")

        if guid:
            # Lấy Token thông qua Model ProjectTask
            TaskModel = request.env["project.task"].sudo()
            token = TaskModel._get_lark_token()

            if token:
                # GỌI API LARK ĐỂ LẤY CHI TIẾT TASK (Vì Webhook không gửi summary)
                url_get = f"https://open.larksuite.com/open-apis/task/v2/tasks/{guid}"
                res = requests.get(url_get, headers={'Authorization': f'Bearer {token}'}, timeout=10)
                
                if res.status_code == 200:
                    lark_data = res.json().get('data', {}).get('task', {})
                    new_summary = lark_data.get('summary')
                    new_desc = lark_data.get('description', '')

                    _logger.info(">>> LẤY THÔNG TIN MỚI TỪ LARK: %s", new_summary)

                    # Tìm và cập nhật Odoo
                    target_task = TaskModel.search([("lark_task_guid", "=", guid)], limit=1)
                    if target_task:
                        target_task.with_context(from_lark=True).write({
                            "name": new_summary,
                            "description": new_desc
                        })
                        _logger.info(">>> LARK -> ODOO: ĐÃ CẬP NHẬT TÊN MỚI THÀNH CÔNG.")

        return Response(json.dumps({"code": 200}), content_type="application/json")