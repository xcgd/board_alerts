from ast import literal_eval
from lxml import etree

from openerp.osv import orm
from openerp import SUPERUSER_ID


class board_alerts(orm.Model):
    """Inherit from board.board to allow sending email alerts."""

    _inherit = 'board.board'

    def send_board_alerts(self, cr, context=None):
        data_obj = self.pool.get('ir.model.data')

        # Use the super-user until we know which user this board is for.
        uid = SUPERUSER_ID

        # Boards are stored as views; get the one referenced by the XML ID.
        board_view = data_obj.get_object(
            cr, uid,
            'board_alerts',
            'alert_board',
            context=context
        )

        # Get our email template, referenced by its XML ID.
        email_template = data_obj.get_object(
            cr, uid,
            'board_alerts',
            'board_alerts_email_template',
            context=context
        )

        # Get the "custom view" representing the board.
        board = self.fields_view_get(
            cr, uid,
            view_id=board_view.id,
            context=context
        )

        # Switch to the user who has created the board.
        custom_view_obj = self.pool.get('ir.ui.view.custom')
        user = custom_view_obj.browse(
            cr, uid,
            board['custom_view_id'],
            context=context
        ).user_id
        uid = user.id

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
            )
            to_send.append(contents)

            from pprint import pprint
            print('Fields: %s' % fields)
            print('IDs: %s' % content_ids)
            print('Data:')
            pprint(contents)

        if not to_send:
            # TODO Send an empty email when there is nothing to send?
            return

        # Fill the email.
        email = email_template_obj.generate_email(
            cr, uid,
            email_template.id,
            None,
            context=context
        )
        email['body_html'] = str(to_send)
        email['email_from'] = 'TODO'  # TODO
        email['email_to'] = user.email

        # Send the user an email. Imitate email_template's send_mail but
        # without the checks (we fill values manually).
        email.pop('attachments')
        email.pop('email_recipients')
        mail_obj = self.pool.get('mail.mail')
        email_id = mail_obj.create(cr, uid, email, context=context)

        print('Sent email: %s' % email_id)
