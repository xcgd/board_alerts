from openerp.osv import orm


class board_alerts_dlg(orm.TransientModel):
    """Dialog shown before manually sending board alert emails, to have some
    kind of confirmation.
    """

    _name = 'board_alerts_dlg'

    def send_board_alerts(self, cr, uid, ids, context=None):

        data_obj = self.pool['ir.model.data']
        user_obj = self.pool['res.users']

        user_obj.send_board_alerts(cr, uid, context=context)

        # Find the action launched by the "Emails" menu command.
        emails_action = data_obj.get_object(
            cr, uid,
            'mail',
            'menu_mail_mail',
            context=context
        ).action

        return {
            'context': emails_action.context,
            'name': emails_action.name,
            'res_model': emails_action.res_model,
            'search_view_id': emails_action.search_view_id.id,
            'target': emails_action.target,
            'type': emails_action.type,
            'view_mode': emails_action.view_mode,
            'view_type': emails_action.view_type,
        }
