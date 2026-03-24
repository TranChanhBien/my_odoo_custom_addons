from odoo import models, api, fields
from lxml import etree

class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_is_company_selection = fields.Selection([
        ('company', 'Công ty'),
        ('individual', 'Cá nhân')
    ], string="Loại đối tác", compute="_compute_is_company_selection", store=True)

    @api.depends('is_company')
    def _compute_is_company_selection(self):
        for rec in self:
            rec.x_is_company_selection = 'company' if rec.is_company else 'individual'

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options=options)
        
        if 'search' in res['views']:
            search_view = res['views']['search']
            doc = etree.fromstring(search_view['arch'])
            
            searchpanel = doc.find('searchpanel')
            if searchpanel is None:
                searchpanel = etree.Element('searchpanel', view_types='kanban,list')
                doc.append(searchpanel)
            else:
                for child in list(searchpanel):
                    searchpanel.remove(child)
            
            # Lấy cấu hình các trường động
            active_fields = self.env['sgt.contact.search.panel.field'].search([('is_active', '=', True)])
            
            for config_field in active_fields:
                field_name = config_field.field_id.name
                
                # BƯỚC QUAN TRỌNG: Nếu trường chưa có trong Metadata của View, hãy nạp nó vào
                if field_name not in res['models'].get('res.partner', {}):
                    # Nạp định nghĩa trường từ server
                    field_info = self.fields_get([field_name])
                    if field_name in field_info:
                        # Bơm vào cấu trúc dữ liệu trả về cho Frontend
                        res['models'].setdefault('res.partner', {}).update(field_info)

                # Chèn thẻ XML như cũ
                etree.SubElement(searchpanel, 'field', {
                    'name': field_name,
                    'icon': config_field.icon or 'fa-users',
                    'enable_counters': '1',
                    'select': 'multi'
                })
            
            search_view['arch'] = etree.tostring(doc, encoding='unicode')
        
        return res