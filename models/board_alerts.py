###############################################################################
#
#    Board Alerts, for Odoo
#    Copyright (C) 2013, 2015 XCG Consulting (http://www.xcg-consulting.fr/)
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
###############################################################################

import datetime
from ast import literal_eval

from lxml import etree

from odoo import _, api, exceptions, models
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
)


class BoardAlerts(models.Model):
    """Inherit from res.users to allow sending email alerts."""

    _inherit = "res.users"

    @api.model
    def send_board_alerts(self):
        """Find users and send them their board alerts.
        """

        # Get our email template, referenced by its XML ID.
        email_template = self.sudo().env.ref(
            "board_alerts.board_alerts_mail_template"
        )

        # Loop through all users; send them an email.
        for user in self.sudo().search([]):

            # Don't send an email when there is no content.
            contents = user.get_board_alert_contents()
            if not contents:
                continue

            # Fill the context to avoid computing contents twice.
            (
                email_template.with_context(
                    board_alert_contents=contents
                ).send_mail(user.id)
            )

    @api.multi
    def get_board_alert_contents(self):
        """Get the HTML content to be put inside a board alert email.
        A board is stored as a custom view; read it, find the actions it
        points to, get the models and views referenced by these actions and
        fetch the data.

        :rtype: String if there is content; None otherwise.
        """

        prev_contents = self.env.context.get("board_alert_contents")
        if prev_contents:
            return prev_contents

        self.ensure_one()

        # Only users in the base "employee" group can see boards, so only they
        # can receive board alerts.
        if not self.user_has_groups("base.group_user"):
            return

        # Define an Odoo context adapted to the specified user. Contains
        # additional values the "_format_content" function expects.
        self = self.sudo(self).with_context(self._board_alert_context())

        # Boards are stored as views; get the one referenced by the XML ID.
        board_view = self.env.ref("board_alerts.alert_board")

        # Set up the link that will be inserted in emails.
        board_link = self.env["ir.config_parameter"].get_param("web.base.url")
        if board_link:
            board_link += "/?db=%s#action=%s" % (
                self.env.cr.dbname,
                str(self.env.ref("board_alerts.action_alert_board").id),
            )

        # Get the "custom view" representing the board.
        board = self.env["board.board"].fields_view_get(view_id=board_view.id)

        to_send = []

        # Loop through "action" tags stored inside this custom view.
        tree = etree.fromstring(board["arch"])
        for action in tree.xpath("//action"):

            if action.attrib["view_mode"] != "list":
                # Only care about lists for now.
                continue
            view_type = "tree"

            # Interpret the attributes of the current "action" tag.
            act_id = int(action.attrib["name"])
            act_domain = literal_eval(action.attrib["domain"])
            act_context = literal_eval(action.attrib["context"])
            act_title = action.attrib["string"]

            # Get the action object pointed to by this "action" tag.
            act_window = self.env["ir.actions.act_window"].browse(act_id)

            # Get the model referenced by this "action" tag.
            act_model = self.env[act_window.res_model]

            # Find the view referenced by this "action" tag; we take the first
            # view that matches, which is correct as they are ordered by
            # priority.
            act_view_id = (
                self.env["ir.ui.view"]
                .search(
                    [
                        ("model", "=", act_window.res_model),
                        ("type", "=", view_type),
                    ],
                    limit=1,
                )
                .id
            )
            act_view = act_model.with_context(act_context).fields_view_get(
                view_id=act_view_id, view_type=view_type
            )

            # Get the fields required by the view. Use this method so that the
            # result is similar to what the user sees in her board.
            act_tree = etree.fromstring(act_view["arch"])
            fields = [
                field.attrib["name"]
                for field in act_tree.xpath("//field")
                if not field.attrib.get("invisible")
            ]
            fields_info = act_model.fields_get(fields)

            # Gather records, according to the domain & context defined in the
            # action.
            content_data_list = (
                act_model.with_context(act_context).search(act_domain)
            ) or []

            # Add field names at the top of the list.
            contents = [[fields_info[field]["string"] for field in fields]]

            # Fetch the data.
            contents += [
                [
                    self._format_content(
                        getattr(content_data, field), fields_info[field]
                    )
                    for field in fields
                ]
                for content_data in content_data_list
            ]

            # Do not send empty content
            if not contents:
                # XXX Maybe change to a message.
                # XXX Probably add an option to send the message or not
                continue

            to_send.append((act_title, contents))

        if not to_send:
            return

        return self._data_list_to_email_html(to_send, board_link)

    def _data_list_to_email_html(self, data_list, board_link):
        """Convert a data list to HTML code suitable for an email.
        :rtype: String.
        """

        root = etree.Element("div")

        if board_link:
            link = etree.SubElement(etree.SubElement(root, "h2"), "a")
            link.attrib["href"] = board_link
            link.text = _("My Alerts")

        for data_title, data in data_list:
            frame = etree.SubElement(root, "div")
            frame.attrib["style"] = (
                "border: 1px solid LightGray;"
                "margin-top: 8px;"
                "padding: 8px;"
            )

            title = etree.SubElement(frame, "h3")
            title.text = data_title or u""

            table = etree.SubElement(frame, "table")
            table.attrib["style"] = (
                "border-collapse: collapse;" "border-spacing: 2px;"
            )

            first_record = True

            for record in data:
                row = etree.SubElement(table, "tr")

                if first_record:
                    first_record = False
                    row.attrib["style"] = (
                        "background-color: LightGray;" "font-weight: bolder;"
                    )

                for field in record:
                    cell = etree.SubElement(row, "td")
                    cell.attrib["style"] = "padding: 3px 6px;"
                    cell.text = field

        return etree.tostring(root, pretty_print=True)

    @api.multi
    def _board_alert_context(self):
        """Define an Odoo context adapted to the specified user. Contains
        additional values the "_format_content" function expects.
        """

        self.ensure_one()

        ret = self.env.context.copy()

        # The user object only has a "lang" selection key; find the actual
        # language object.
        lang = (
            self.sudo()
            .env["res.lang"]
            .search([("code", "=", self.lang)], limit=1)
        )
        if not lang:
            raise exceptions.Warning(_("Lang %s not found") % self.lang)

        ret.update(
            {
                "date_format": lang.date_format,
                "datetime_format": "%s %s"
                % (lang.date_format, lang.time_format),
                "lang": self.lang,
                "tz": self.tz,
                "uid": self.id,
            }
        )

        return ret

    def _format_content(self, content, field_info):
        """Stringify the specified field value, taking care of translations and
        fetching related names.

        The Odoo context must define the following:
            * date_format.
            * datetime_format.

        :type content: Odoo record set.
        :param field_info: Odoo field information.
        :rtype: String.
        """

        # Delegate to per-type functions.
        return getattr(
            self,
            "_format_content_%s" % field_info["type"],
            lambda content, *args: str(content),
        )(content, field_info)

    def _format_content_boolean(self, content, field_info):
        return _("Yes") if content else _("No")

    def _format_content_char(self, content, field_info):
        return content or ""

    def _format_content_date(self, content, field_info):
        if not content:
            return ""
        return datetime.datetime.strptime(
            content, DEFAULT_SERVER_DATE_FORMAT
        ).strftime(self.env.context["date_format"])

    def _format_content_datetime(self, content, field_info):
        if not content:
            return ""
        return datetime.datetime.strptime(
            content, DEFAULT_SERVER_DATETIME_FORMAT
        ).strftime(self.env.context["datetime_format"])

    def _format_content_float(self, content, field_info):
        # TODO Better float formatting (see report_sxw:digits_fmt,
        # report_sxw:get_digits for details.
        return str(content or 0.0)

    def _format_content_integer(self, content, field_info):
        return str(content or 0)

    def _format_content_many2many(self, content, field_info):
        if not content:
            return ""
        # TODO Simplify the following when a method can be executed on a
        # record list (see the TODO near its declaration).
        return ", ".join(
            self._get_object_name(linked_content) for linked_content in content
        )

    def _format_content_one2many(self, content, field_info):
        if not content:
            return ""
        # TODO Simplify the following when a method can be executed on a
        # record list (see the TODO near its declaration).
        return ", ".join(
            self._get_object_name(linked_content) for linked_content in content
        )

    def _format_content_selection(self, content, field_info):
        if not content:
            return ""
        return dict(field_info["selection"]).get(content, "")

    def _format_content_many2one(self, content, field_info):
        if not content:
            return ""
        return self._get_object_name(content)

    def _format_content_text(self, content, field_info):
        return content or ""

    def _get_object_name(self, content):
        """Call the "name_get" function of the specified Odoo record set.
        """

        # 0: first element of the returned list.
        # 1: second element of the (ID, name) tuple.
        return content.name_get()[0][1]
