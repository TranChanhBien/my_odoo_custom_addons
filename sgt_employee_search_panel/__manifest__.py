{
    'name': 'Employee Search Panel Config',
    'version': '1.0',
    'summary': 'Tùy chỉnh và cấu hình Search Panel cho Employees (Nhân viên)',
    'category': 'Human Resources/Employees',
    'author': 'SGT',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/search_panel_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}