# -*- coding: utf-8 -*-
##############################################################################
#
#    Board Alerts, for Odoo
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
    "name": "Board alerts",
    "description": """
Board alerts
============

Send emails at regular intervals to summarize the contents of a dashboard.


Create your own Odoo notifications
----------------------------------

* Create your own notifications based on the contents of your activity.
* See your alerts in your dasboard.
* Receive them automatically by email at regular intervals.
* The administrator can adjust the email frequency.
""",
    "version": "11.0.1.0",
    "category": "Tools",
    "author": "XCG Consulting",
    "website": "http://odoo.consulting/",
    "depends": ["board", "mail", "web"],
    "data": [
        "data/alert_board.xml",
        "data/board_alerts_email_template.xml",
        "data/board_alerts_cron_task.xml",
        "views/board_alerts_assets.xml",
        "wizard/board_alerts_dlg.xml",
    ],
    "qweb": ["static/src/xml/alert_board.xml"],
    "installable": True,
}
