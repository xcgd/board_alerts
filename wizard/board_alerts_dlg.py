from openerp.osv import orm
from openerp.tools.translate import _


class board_alerts_dlg(orm.TransientModel):
    """Dialog shown before manually sending board alert emails, to have some
    kind of confirmation.
    """

    _name = 'board_alerts_dlg'

    def send_board_alerts(self, cr, uid, ids, context=None):
        self.pool.get('board.board').send_board_alerts(
            cr, uid, context=context
        )

        this = self.browse(cr, uid, ids)[0]

        data_obj = self.pool.get('ir.model.data')
        done_view = data_obj.get_object(
            cr, uid,
            'board_alerts',
            'board_alerts_dlg_done',
            context=context
        )

        return {
            'name': _('Send board alerts'),
            'res_id': this.id,
            'res_model': 'board_alerts_dlg',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': done_view.id,
            'view_mode': 'form',
            'view_type': 'form',
        }
