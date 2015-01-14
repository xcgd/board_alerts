from ast import literal_eval
from lxml import etree

from openerp.osv import orm
from openerp.tools.translate import _
from openerp import SUPERUSER_ID


class board_alerts(orm.Model):
    """Inherit from board.board to allow sending email alerts."""

    _inherit = 'board.board'

    def send_board_alerts(self, cr, uid, context=None):
        """Set up preliminary data, find users and let
        send_board_alerts_per_user handle the rest.
        """

        data_obj = self.pool.get('ir.model.data')

        # Boards are stored as views; get the one referenced by the XML ID.
        board_view = data_obj.get_object(
            cr, uid,
            'board_alerts',
            'alert_board',
            context=context
        )

        # Set up the link that will be inserted in emails.
        param_obj = self.pool.get('ir.config_parameter')
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

        # Get our email template, referenced by its XML ID.
        email_template = data_obj.get_object(
            cr, uid,
            'board_alerts',
            'board_alerts_email_template',
            context=context
        )

        # Loop through all users.
        user_obj = self.pool.get('res.users')
        user_ids = user_obj.search(cr, uid, [], context=context)
        users = user_obj.browse(cr, uid, user_ids, context=context)

        for user in users:
            self._send_board_alerts_per_user(
                cr,
                user,
                board_view,
                board_link,
                email_template,
                context=context
            )

    def _send_board_alerts_per_user(
        self,
        cr,
        user,
        board_view,
        board_link,
        email_template,
        context=None
    ):
        """A board is stored as a custom view; read it, find the actions it
        points to, get the models and views referenced by these actions and
        fetch the data. Then send that data (properly formatted) by email.
        """

        uid = user.id

        # Get the "custom view" representing the board.
        board = self.fields_view_get(
            cr, uid,
            view_id=board_view.id,
            context=context
        )

        act_window_obj = self.pool.get('ir.actions.act_window')
        email_template_obj = self.pool.get('email.template')
        view_obj = self.pool.get('ir.ui.view')

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

            # Get data IDs, according to the domain & context defined in the
            # action.
            content_ids = act_model.search(
                cr, uid,
                act_domain,
                context=act_context
            )

            # Fetch the data.
            contents = act_model.export_data(
                cr, uid,
                content_ids,
                fields,
                context=act_context
            )['datas'] or []
            
            # Do not send empty content
            if not contents:
                # XXX Maybe change to a message.
                # XXX Probably add an option to send the message or not 
                continue

            # Add field names at the top of the list.
            fields_info = act_model.fields_get(
                cr, uid,
                fields,
                context=context
            )
            contents.insert(0, [
                fields_info[field]['string']
                for field in fields
            ])

            to_send.append((act_title, contents))

        if not to_send:
            return

        # Fill the email.
        email = email_template_obj.generate_email(
            cr, uid,
            email_template.id,
            None,
            context=context
        )
        email['body_html'] = email['body_html'] % {
            'recipient': user.name,
            'contents': self._get_html(to_send, board_link),
        }
        email['email_from'] = '%s <%s>' % (
            user.company_id.name or u'',
            user.company_id.email or u''
        )
        email['email_to'] = user.email

        # Send the user an email. Imitate email_template's send_mail but
        # without the checks (we fill values manually).
        email.pop('attachments')
        email.pop('email_recipients')
        mail_obj = self.pool.get('mail.mail')
        mail_obj.create(cr, SUPERUSER_ID, email, context=context)

    def _get_html(self, data_list, board_link):
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
                    cell.text = (
                        field if isinstance(field, basestring)
                        else str(field)
                    )

        return etree.tostring(root, pretty_print=True)
