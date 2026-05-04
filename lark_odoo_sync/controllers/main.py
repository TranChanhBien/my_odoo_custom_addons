import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class LarkWebhookController(http.Controller):

    # ĐỔI TỪ type='json' SANG type='http'
    @http.route('/lark/webhook', type='http', auth='public', methods=['POST'], csrf=False)
    def lark_webhook(self, **kwargs):
        try:
            # 1. Đọc dữ liệu thô (raw data) do Lark bắn xuống
            raw_data = request.httprequest.data
            if not raw_data:
                return request.make_response(json.dumps({'error': 'Empty payload'}), headers=[('Content-Type', 'application/json')])

            # 2. Giải mã chuỗi thô thành Dictionary JSON
            data = json.loads(raw_data.decode('utf-8'))
            # --- CHỐT BẢO MẬT WEBHOOK ---
            # Lấy token từ cấu hình của Odoo
            expected_token = request.env['ir.config_parameter'].sudo().get_param('lark_odoo_sync.webhook_token')
            
            # Lark gửi Token ở ngoài gốc (khi verify url) hoặc trong header (khi gửi event)
            received_token = data.get('token') or data.get('header', {}).get('token')

            if expected_token and received_token != expected_token:
                _logger.warning(f"CẢNH BÁO BẢO MẬT: Phát hiện truy cập Webhook trái phép! Mã sai: {received_token}")
                return request.make_response(
                    json.dumps({'error': 'Truy cập bị từ chối. Token không hợp lệ!'}), 
                    headers=[('Content-Type', 'application/json')], 
                    status=403 # Lỗi 403 Forbidden (Cấm truy cập)
                )
            # ----------------------------
            _logger.info(f"Lark Webhook nhận được: {data}")

            # 3. BÀI TEST CHALLENGE TỪ LARK
            if data.get('type') == 'url_verification':
                challenge = data.get('challenge')
                _logger.info(f"Vượt qua bài test Challenge: {challenge}")
                
                # Trả về Response đúng chuẩn HTTP mà Lark yêu cầu
                return request.make_response(
                    json.dumps({'challenge': challenge}), 
                    headers=[('Content-Type', 'application/json')]
                )

            # Khung sườn để xử lý Event thực tế (Task bị sửa/hoàn thành) sẽ viết ở bước sau
            header = data.get('header', {})
            event_type = header.get('event_type')
            
            if event_type == 'task.task.updated_v1':
                event_data = data.get('event', {})
                lark_task_id = event_data.get('task_id')
                
                if lark_task_id:
                    # 1. Tìm Task tương ứng trong Database Odoo
                    # Dùng sudo() vì Webhook chạy ở quyền public (khách vô danh)
                    task = request.env['project.task'].sudo().search([('lark_task_id', '=', lark_task_id)], limit=1)
                    
                    if task:
                        # 2. Ra lệnh cho Model tự đi kéo dữ liệu chi tiết về
                        task._sync_from_lark()
                        _logger.info(f"Đã nhận lệnh cập nhật cho Task: {task.name}")

            return request.make_response(
                json.dumps({'status': 'success'}), 
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            _logger.error(f"Lỗi xử lý Webhook: {str(e)}")
            return request.make_response(
                json.dumps({'error': str(e)}), 
                headers=[('Content-Type', 'application/json')], 
                status=500
            )