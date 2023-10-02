
{
    'name': 'Timesheet Approval',
    'summary': 'Timesheet Timesheet',
    'author': '',
    'company': '',
    'maintainer': '',
    'website': "",
    'category': 'Timesheet',
    'version': '16.1.0.1.1',
    'depends': ['account','hr_timesheet','hr', 'hr_hourly_cost', 'timesheet_grid'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/timesheet_approval.xml',
        'views/i_9.xml',
    ],
    'qweb': [
    ],
    "installable": True,
}
