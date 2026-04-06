from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PostLink(models.Model):
    _name = 'post.link'
    _description = 'Post Link Management'
    _order = 'name desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    post_url = fields.Char(string='Post URL', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', readonly=True) # Để readonly để bắt buộc dùng nút bấm

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    partner_id = fields.Many2one('res.partner', string='Contact')
    so_salesperson_id = fields.Many2one('res.users', string='SO Salesperson', readonly=True)
    responsible_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    
    # Kết nối với bảng project.task
    task_id = fields.Many2one('project.task', string='Related Task')
    
    # Kết nối gián tiếp để lấy project_id từ task
    project_id = fields.Many2one('project.project', string='Project', related='task_id.project_id', store=True)

    # --- LOGIC NÚT BẤM (BUTTON ACTIONS) ---
    def action_publish(self):
        """Chuyển sang trạng thái Published"""
        for record in self:
            record.state = 'published'

    def action_draft(self):
        """Quay lại trạng thái Draft"""
        for record in self:
            record.state = 'draft'

    def action_cancel(self):
        """Hủy bỏ"""
        for record in self:
            record.state = 'cancel'

    # --- LOGIC LỌC TRÙNG TUYỆT ĐỐI ---
    @api.constrains('post_url')
    def _check_unique_post_url(self):
        for record in self:
            if record.post_url:
                current_url = record.post_url.strip().rstrip('/')
                all_records = self.search([('id', '!=', record.id)])
                for existing in all_records:
                    if existing.post_url:
                        existing_url = existing.post_url.strip().rstrip('/')
                        if current_url == existing_url:
                            raise ValidationError(_("Duplicate Link Detected! The URL already exists in %s.") % existing.name)

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        if self.sale_order_id:
            self.partner_id = self.sale_order_id.partner_id
            self.so_salesperson_id = self.sale_order_id.user_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('post.link') or _('New')
        return super(PostLink, self).create(vals_list)