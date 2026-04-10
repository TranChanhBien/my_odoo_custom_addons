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
    'assets': {
        'web.assets_backend': [
            'post_management/static/src/js/image_preview.js',
            'post_management/static/src/css/image_preview.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}