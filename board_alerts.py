###############################################################################
#
#    OpenERP, Open Source Management Solution
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

from ast import literal_eval
import datetime
from lxml import etree

from openerp import exceptions
from openerp import SUPERUSER_ID
from openerp.osv import orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _


class board_alerts(orm.Model):
    """Inherit from res.users to allow sending email alerts."""

    _inherit = 'res.users'

    def send_board_alerts(self, cr, uid, context=None):
        """Find users and send them their board alerts.
        """

        data_obj = self.pool['ir.model.data']
        email_template_obj = self.pool['email.template']

        # Get our email template, referenced by its XML ID.
        email_template_id = data_obj.get_object(
            cr, SUPERUSER_ID,
            'board_alerts',
            'board_alerts_email_template',
            context=context
        ).id

        # Loop through all users; send them an email.
        for user_id in self.search(cr, SUPERUSER_ID, [], context=context):

            # Don't send an email when there is no content.
            contents = self.get_board_alert_contents(
                cr, uid, [user_id], context
            )
            if not contents:
                continue

            # Fill the context to avoid computing contents twice.
            email_context = context.copy() if context else {}
            email_context['board_alert_contents'] = contents

            email_template_obj.send_mail(
                cr, SUPERUSER_ID,
                email_template_id,
                user_id,
                context=email_context
            )

    def get_board_alert_contents(self, cr, uid, ids, context=None):
        """Get the HTML content to be put inside a board alert email.
        A board is stored as a custom view; read it, find the actions it
        points to, get the models and views referenced by these actions and
        fetch the data.
        @rtype: String if there is content, else None.
        """

        if not isinstance(ids, list):
            ids = [ids]
        if len(ids) != 1:
            raise exceptions.Warning(
                'board_alerts: Only 1 ID expected in the '
                '"get_board_alert_contents" function.'
            )
        uid = ids[0]

        if not context:
            context = {}

        prev_contents = context.get('board_alert_contents')
        if prev_contents:
            return prev_contents

        context = self._default_context(cr, uid, context)

        # Only users in the base "employee" group can see boards, so only they
        # can receive board alerts.
        if not self.user_has_groups(
            cr, uid, 'base.group_user', context=context
        ):
            return

        act_window_obj = self.pool['ir.actions.act_window']
        board_obj = self.pool['board.board']
        data_obj = self.pool['ir.model.data']
        param_obj = self.pool['ir.config_parameter']
        view_obj = self.pool['ir.ui.view']

        # Boards are stored as views; get the one referenced by the XML ID.
        board_view = data_obj.get_object(
            cr, uid,
            'board_alerts',
            'alert_board',
            context=context
        )

        # Set up the link that will be inserted in emails.
        board_link = param_obj.get_param(
            cr, uid,
            'web.base.url',
            context=context
        )
        if board_link:
            board_link += '/?db=%s#action=%s' % (
                cr.dbname,
                str(data_obj.get_object(
                    cr, uid,
                    'board_alerts',
                    'action_alert_board',
                    context=context
                ).id)
            )

        # Get the "custom view" representing the board.
        board = board_obj.fields_view_get(
            cr, uid,
            view_id=board_view.id,
            context=context
        )

        to_send = []

        # Loop through "action" tags stored inside this custom view.
        tree = etree.fromstring(board['arch'])
        for action in tree.xpath('//action'):

            if action.attrib['view_mode'] != 'list':
                # Only care about lists for now.
                continue
            view_type = 'tree'

            # Interpret the attributes of the current "action" tag.
            act_id = int(action.attrib['name'])
            act_domain = literal_eval(action.attrib['domain'])
            act_context = literal_eval(action.attrib['context'])
            act_title = action.attrib['string']

            # Get the action object pointed to by this "action" tag.
            act_window = act_window_obj.browse(
                cr, uid,
                act_id,
                context=context
            )

            # Get the model referenced by this "action" tag.
            act_model = self.pool.get(act_window.res_model)

            # Find the view referenced by this "action" tag; we take the first
            # view that matches, which is correct as they are ordered by
            # priority.
            act_view_id = view_obj.search(
                cr, uid,
                [
                    ('model', '=', act_window.res_model),
                    ('type', '=', view_type),
                ],
                limit=1,
                context=act_context,
            )[0]
            act_view = act_model.fields_view_get(
                cr, uid,
                view_id=act_view_id,
                view_type=view_type,
                context=act_context
            )

            # Get the fields required by the view. Use this method so that the
            # result is similar to what the user sees in her board.
            act_tree = etree.fromstring(act_view['arch'])
            fields = [
                field.attrib['name']
                for field in act_tree.xpath('//field')
                if not field.attrib.get('invisible')
            ]
            fields_info = act_model.fields_get(
                cr, uid,
                fields,
                context=context
            )

            # Get data IDs, according to the domain & context defined in the
            # action.
            content_ids = act_model.search(
                cr, uid,
                act_domain,
                context=act_context
            )

            # Add field names at the top of the list.
            contents = [[fields_info[field]['string'] for field in fields]]

            # Fetch the data
            content_data_list = act_model.browse(
                cr, uid,
                content_ids,
                context=act_context
            ) or []
            contents += [
                [
                    self._format_content(
                        getattr(content_data, field),
                        fields_info[field],
                        context
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

        return self._data_list_to_email_html(to_send, board_link, context)

    def _data_list_to_email_html(self, data_list, board_link, context):
        """Convert a data list to HTML code suitable for an email.
        @rtype: String.
        """

        # The "context" parameter is required for translations to work.

        root = etree.Element('div')

        if board_link:
            link = etree.SubElement(etree.SubElement(root, 'h2'), 'a')
            link.attrib['href'] = board_link
            link.text = _('My Alerts')

        for data_title, data in data_list:
            frame = etree.SubElement(root, 'div')
            frame.attrib['style'] = (
                'border: 1px solid LightGray;'
                'margin-top: 8px;'
                'padding: 8px;'
            )

            title = etree.SubElement(frame, 'h3')
            title.text = data_title or u''

            table = etree.SubElement(frame, 'table')
            table.attrib['style'] = (
                'border-collapse: collapse;'
                'border-spacing: 2px;'
            )

            first_record = True

            for record in data:
                row = etree.SubElement(table, 'tr')

                if first_record:
                    first_record = False
                    row.attrib['style'] = (
                        'background-color: LightGray;'
                        'font-weight: bolder;'
                    )

                for field in record:
                    cell = etree.SubElement(row, 'td')
                    cell.attrib['style'] = 'padding: 3px 6px;'
                    cell.text = field

        return etree.tostring(root, pretty_print=True)

    def _default_context(self, cr, uid, context):
        """Get an Odoo context, adapted to the specified user. Contains
        additional values the "_format_content" function expects.
        """

        ret = context.copy()

        lang_obj = self.pool['res.lang']

        user = self.browse(cr, SUPERUSER_ID, [uid], context=context)[0]

        # The user object only has a "lang" selection key; find the actual
        # language object.
        lang_ids = lang_obj.search(
            cr, SUPERUSER_ID,
            [('code', '=', user.lang)],
            limit=1,
            context=context
        )
        if not lang_ids:
            raise exceptions.Warning(_('Lang %s not found') % user.lang)
        lang = lang_obj.browse(cr, SUPERUSER_ID, lang_ids, context=context)[0]

        ret.update({
            'date_format': lang.date_format,
            'datetime_format': '%s %s' % (lang.date_format, lang.time_format),
            'lang': user.lang,
            'tz': user.tz,
            'uid': uid,
        })

        return ret

    def _format_content(self, content, field_info, context):
        """Stringify the specified field value, taking care of translations and
        fetching related names.
        @type content: Odoo browse-record object.
        @param field_info: Odoo field information.
        @param context: Odoo context; must define the following:
            * date_format.
            * datetime_format.
        @rtype: String.
        """

        # Delegate to per-type functions.
        return getattr(
            self,
            '_format_content_%s' % field_info['type'],
            lambda content, *args: str(content)
        )(
            content, field_info, context
        )

    def _format_content_boolean(self, content, field_info, context):
        return _('Yes') if content else _('No')

    def _format_content_char(self, content, field_info, context):
        return content or ''

    def _format_content_date(self, content, field_info, context):
        if not content:
            return ''
        return (
            datetime.datetime.strptime(content, DEFAULT_SERVER_DATE_FORMAT)
            .strftime(context['date_format'])
        )

    def _format_content_datetime(self, content, field_info, context):
        if not content:
            return ''
        return (
            datetime.datetime.strptime(content, DEFAULT_SERVER_DATETIME_FORMAT)
            .strftime(context['datetime_format'])
        )

    def _format_content_float(self, content, field_info, context):
        # TODO Better float formatting (see report_sxw:digits_fmt,
        # report_sxw:get_digits for details.
        return str(content or 0.0)

    def _format_content_integer(self, content, field_info, context):
        return str(content or 0)

    def _format_content_many2many(self, content, field_info, context):
        if not content:
            return ''
        # TODO Simplify the following when a method can be executed on a
        # "browse_record_list" object (see the TODO near its declaration).
        return ', '.join(
            self._get_object_name(linked_content, context)
            for linked_content in content
        )

    def _format_content_one2many(self, content, field_info, context):
        if not content:
            return ''
        # TODO Simplify the following when a method can be executed on a
        # "browse_record_list" object (see the TODO near its declaration).
        return ', '.join(
            self._get_object_name(linked_content, context)
            for linked_content in content
        )

    def _format_content_selection(self, content, field_info, context):
        if not content:
            return ''
        return dict(field_info['selection']).get(content, '')

    def _format_content_many2one(self, content, field_info, context):
        if not content:
            return ''
        return self._get_object_name(content, context)

    def _format_content_text(self, content, field_info, context):
        return content or ''

    def _get_object_name(self, content, context):
        """Call the "name_get" function of the specified Odoo browse-record
        object. The "context" parameter is here to ensure proper translations.
        """

        # 0: first element of the returned list.
        # 1: second element of the (ID, name) tuple.
        return content.name_get()[0][1]
