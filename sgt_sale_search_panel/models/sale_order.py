from odoo import models, api
from lxml import etree

class SaleOrder(models.Model):
    _inherit = 'sale.order'

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
            
            # Lấy các trường đã cấu hình trong Settings
            active_fields = self.env['sgt.sale.search.panel.field'].search([('is_active', '=', True)])
            
            for field in active_fields:
                field_name = field.field_id.name
                
                # Bơm trường vào metadata nếu Odoo chưa tự động load
                if field_name not in res['models'].get('sale.order', {}):
                    field_info = self.fields_get([field_name])
                    if field_name in field_info:
                        res['models'].setdefault('sale.order', {}).update(field_info)

                # Sinh thẻ filter
                etree.SubElement(searchpanel, 'field', {
                    'name': field_name,
                    'string': field.name,  # Ghi đè Tên hiển thị
                    'icon': field.icon or 'fa-filter',
                    'enable_counters': '1',
                    'select': 'multi'
                })
            
            search_view['arch'] = etree.tostring(doc, encoding='unicode')
        
        return res