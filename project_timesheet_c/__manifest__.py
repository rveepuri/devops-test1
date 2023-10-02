
{
    'name': 'Project Timesheet',
    'summary': 'Project Timesheet',
    'author': 'Cellersoft',
    'company': 'Cellersoft',
    'maintainer': 'Cellersoft',
    'website': "",
    'category': 'Project',
    'version': '16.1.0.1.1',
    'depends': ['account','project','hr_timesheet','hr', 'hr_hourly_cost', 'analytic','sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'security/security.xml',
        'views/project_task.xml',
        'views/overhead.xml',
        'views/role.xml',

    ],
    'qweb': [
    ],
    "installable": True,
}
