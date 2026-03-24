from odoo import models, api
from lxml import etree

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options=options)
        
        # Nếu đang xem view search (để render searchpanel)
        if 'search' in res['views']:
            search_view = res['views']['search']
            doc = etree.fromstring(search_view['arch'])
            
            # Tìm thẻ searchpanel hiện có hoặc tạo mới
            searchpanel = doc.find('searchpanel')
            if searchpanel is None:
                searchpanel = etree.Element('searchpanel', view_types='kanban,list')
                doc.append(searchpanel)
            else:
                for child in list(searchpanel):
                    searchpanel.remove(child)
            
            # Lấy các trường đã cấu hình trong Settings
            active_fields = self.env['sgt.crm.search.panel.field'].search([('is_active', '=', True)])
            
            for field in active_fields:
                etree.SubElement(searchpanel, 'field', {
                    'name': field.field_id.name,
                    'icon': field.icon or 'fa-filter',
                    'enable_counters': '1', # Hiển thị số lượng lead
                    'select': 'multi'       # Cho phép tích chọn nhiều mục
                })
            
            search_view['arch'] = etree.tostring(doc, encoding='unicode')
        
        return res