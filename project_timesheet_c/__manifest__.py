
{
    'name': 'Project Timesheet',
    'summary': 'Project Timesheet',
    'author': '',
    'company': '',
    'maintainer': '',
    'website': "",
    'category': 'Project',
    'version': '16.1.0.1.1',
    'depends': ['account','project','hr_timesheet','hr', 'hr_hourly_cost', 'analytic','sale','hr_contract','sale_timesheet','sale_project'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'security/security.xml',
        'views/project_task.xml',
        'views/overhead.xml',
        'views/role.xml',
        'reports/invoice_inherit.xml',
        'reports/timesheet.xml',
        'reports/purchase_report_views.xml',

    ],
    'qweb': [
    ],
    "installable": True,
}
