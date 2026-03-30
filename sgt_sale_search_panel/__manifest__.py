{
    'name': 'Sale Search Panel Config',
    'version': '1.0',
    'summary': 'Tùy chỉnh và cấu hình Search Panel cho Sales',
    'category': 'Sales',
    'author': 'SGT',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/search_panel_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}