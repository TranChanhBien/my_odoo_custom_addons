import requests
import json
from odoo import fields, models, api
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Thông tin xác thực từ Lark
    lark_app_id = fields.Char(string='Lark App ID', config_parameter='lark_odoo_sync.app_id')
    lark_app_secret = fields.Char(string='Lark App Secret', config_parameter='lark_odoo_sync.app_secret')
    
    # Lưu trữ Token và thời gian hết hạn để chạy ngầm
    lark_tenant_token = fields.Char(string='Lark Tenant Token', config_parameter='lark_odoo_sync.tenant_token')
    lark_token_expiry = fields.Datetime(string='Token Expiry Time', config_parameter='lark_odoo_sync.token_expiry')
    
    # Tài khoản dự phòng khi đồng bộ User bị lỗi
    lark_fallback_user_id = fields.Many2one(
        'res.users', 
        string='Người nhận Task dự phòng', 
        config_parameter='lark_odoo_sync.fallback_user_id',
        help='Nếu task từ Lark đổ về không tìm thấy user tương ứng trong Odoo, task sẽ được gán cho người này.'
    )

    # Trường Webhook Token
    lark_webhook_token = fields.Char(string='Lark Webhook Token', config_parameter='lark_odoo_sync.webhook_token')

    def action_test_lark_connection(self):
        """Hàm dùng để lấy tenant_access_token từ Lark và kiểm tra kết nối"""
        
        # 1. Lấy thông tin App ID và App Secret từ Database
        app_id = self.env['ir.config_parameter'].sudo().get_param('lark_odoo_sync.app_id')
        app_secret = self.env['ir.config_parameter'].sudo().get_param('lark_odoo_sync.app_secret')

        if not app_id or not app_secret:
            raise UserError("Vui lòng nhập đầy đủ Lark App ID và App Secret trước khi kiểm tra.")

        # 2. Gọi API của Lark để xin cấp Token
        url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        payload = json.dumps({
            "app_id": app_id,
            "app_secret": app_secret
        })

        try:
            response = requests.post(url, headers=headers, data=payload)
            response_data = response.json()

            # 3. Xử lý kết quả trả về
            if response_data.get('code') == 0:
                # Thành công: Lark trả về mã code 0
                token = response_data.get('tenant_access_token')
                
                # Lưu Token vào system parameter để dùng cho các hàm sau này
                self.env['ir.config_parameter'].sudo().set_param('lark_odoo_sync.tenant_token', token)
                
                # Báo cáo thành công cho người dùng
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Kết nối thành công!',
                        'message': f'Đã lấy Token thành công từ Lark. Token hợp lệ trong 2 giờ.',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                # Thất bại: Sai App ID hoặc App Secret
                error_msg = response_data.get('msg', 'Lỗi không xác định')
                raise UserError(f"Kết nối thất bại! Chi tiết từ Lark: {error_msg}")

        except Exception as e:
            raise UserError(f"Lỗi hệ thống khi gọi API: {str(e)}")

    @api.model
    def cron_refresh_lark_token(self):
        """Hàm chạy ngầm tự động làm mới Token mỗi giờ"""
        app_id = self.env['ir.config_parameter'].sudo().get_param('lark_odoo_sync.app_id')
        app_secret = self.env['ir.config_parameter'].sudo().get_param('lark_odoo_sync.app_secret')
        
        # Nếu chưa cấu hình thì bỏ qua, không báo lỗi làm phiền hệ thống
        if not app_id or not app_secret:
            return False

        url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        payload = json.dumps({
            "app_id": app_id,
            "app_secret": app_secret
        })

        try:
            response = requests.post(url, headers=headers, data=payload)
            response_data = response.json()

            if response_data.get('code') == 0:
                token = response_data.get('tenant_access_token')
                # Lưu Token mới đè lên Token cũ trong System Parameters
                self.env['ir.config_parameter'].sudo().set_param('lark_odoo_sync.tenant_token', token)
                return True
        except Exception as e:
            # Ghi log lỗi nếu cần thiết (sẽ làm ở bảng log sau)
            pass
        
        return False

    def action_sync_lark_users_by_email(self):
        """Hàm tự động quét Email trong Odoo và lấy lark_user_id từ Lark về"""
        
        # 1. Lấy Token đã được Cron Job tạo ra
        token = self.env['ir.config_parameter'].sudo().get_param('lark_odoo_sync.tenant_token')
        if not token:
            raise UserError("Chưa có Token. Vui lòng bấm 'Kiểm tra kết nối Lark' trước.")

        # 2. Lấy danh sách các User Odoo đang hoạt động và có Email
        odoo_users = self.env['res.users'].search([('email', '!=', False), ('active', '=', True)])
        emails = odoo_users.mapped('email')

        if not emails:
            raise UserError("Không tìm thấy nhân sự nào có email trong hệ thống Odoo.")

        # 3. Gọi API của Lark để tra cứu ID hàng loạt (Batch Get ID)
        url = "https://open.larksuite.com/open-apis/contact/v3/users/batch_get_id"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        # Đóng gói danh sách email gửi đi (Lark v3 hỗ trợ API này để dò ID bằng email)
        payload = json.dumps({
            "emails": emails
        })

        try:
            response = requests.post(url, headers=headers, data=payload)
            response_data = response.json()

            # 4. Xử lý kết quả và gán vào Odoo
            if response_data.get('code') == 0:
                user_list = response_data.get('data', {}).get('user_list', [])
                matched_count = 0
                
                for lark_user in user_list:
                    # Tùy thuộc cấu hình tài khoản Lark, email có thể nằm trong 'email' hoặc 'emails'
                    lark_email = lark_user.get('email')
                    lark_id = lark_user.get('user_id') 

                    if lark_email and lark_id:
                        # Tìm lại user bên Odoo có email khớp với Lark
                        matched_users = odoo_users.filtered(lambda u: u.email == lark_email)
                        for u in matched_users:
                            u.sudo().write({'lark_user_id': lark_id})
                            matched_count += 1
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Đồng bộ User thành công!',
                        'message': f'Đã quét và ánh xạ thành công ID cho {matched_count} nhân sự.',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                error_msg = response_data.get('msg', 'Lỗi không xác định')
                raise UserError(f"Lark từ chối đồng bộ: {error_msg}. Vui lòng kiểm tra lại quyền 'contact:user.email:readonly' trên Lark.")

        except Exception as e:
            raise UserError(f"Lỗi gọi API: {str(e)}")