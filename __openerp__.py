# -*- coding: utf-8 -*-
{
    'name': 'Board alerts',
    'description': '''
Send emails at regular intervals to summarize the contents of a dashboard.
''',
    'version': '1.0',
    'category': 'Tools',
    'author': 'XCG Consulting',
    'website': 'http://www.openerp-experts.com/',
    'depends': [
        'board',
        'email_template',
    ],
    'data': [
        'data/alert_board.xml',
        'data/board_alerts_email_template.xml',
        'data/board_alerts_cron_task.xml',
        'wizard/board_alerts_dlg.xml',
    ],
    'installable': True,
}
