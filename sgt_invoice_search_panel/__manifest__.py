{
    'name': 'Invoice Search Panel Config',
    'version': '1.0',
    'summary': 'Tùy chỉnh và cấu hình Search Panel cho Invoices (Hóa đơn)',
    'category': 'Accounting/Accounting',
    'author': 'SGT',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/search_panel_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}