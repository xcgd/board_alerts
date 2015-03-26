# -*- coding: utf-8 -*-
##############################################################################
#
#    Board Alerts, for OpenERP
#    Copyright (C) 2013 XCG Consulting (http://odoo.consulting)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Board alerts',
    'description': '''
Send emails at regular intervals to summarize the contents of a dashboard.
''',
    'version': '1.5',
    'category': 'Tools',
    'author': 'XCG Consulting',
    'website': 'http://odoo.consulting/',
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
