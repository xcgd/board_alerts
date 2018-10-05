from odoo import api, models


class BoardAlertsDlg(models.TransientModel):
    """Dialog shown before manually sending board alert emails, to have some
    kind of confirmation.
    """

    _name = 'board_alerts_dlg'
    _description = 'Board alert sender dialog box'

    @api.multi
    def send_board_alerts(self):
        """Send board alerts then show emails.
        """

        self.env['res.users'].send_board_alerts()

        # Find the action launched by the "Emails" menu command.
        emails_action = self.env.ref('mail.menu_mail_mail').action

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
