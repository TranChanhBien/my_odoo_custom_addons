{
    'name': 'Post Management Pro',
    'version': '1.4',
    'category': 'Sales',
    'depends': ['base', 'sale', 'project', 'sale_project'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/post_link_views.xml',
        'views/project_task_views.xml',
        'views/project_task_button_views.xml',
        'views/project_task_integration_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}