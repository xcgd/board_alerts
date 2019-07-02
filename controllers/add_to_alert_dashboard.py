from xml.etree import ElementTree

from odoo.http import Controller, request, route


class AddToAlertDashboardController(Controller):
    """Controller for an endpoint called when adding an Odoo view to the alert
    dashboard added by this module.

    Similar to the one for the default dashboard in the "board" module.
    """

    @route(route="/board/add_to_alert_dashboard", type="json", auth="user")
    def add_to_dashboard(
        self, action_id, context_to_save, domain, view_mode, name=""
    ):
        """Called when adding to the alert dashboard from the Odoo web client.
        """

        action = request.env.ref("board_alerts.action_alert_board")
        if (
            action
            and action["res_model"] == "board.board"
            and action["views"][0][1] == "form"
            and action_id
        ):
            view_id = action["views"][0][0]
            board = request.env["board.board"].fields_view_get(view_id, "form")
            if board and "arch" in board:
                xml = ElementTree.fromstring(board["arch"])
                column = xml.find("./board/column")
                if column is not None:
                    new_action = ElementTree.Element(
                        "action",
                        {
                            "context": str(context_to_save),
                            "domain": str(domain),
                            "name": str(action_id),
                            "string": name,
                            "view_mode": view_mode,
                        },
                    )
                    column.insert(0, new_action)
                    arch = ElementTree.tostring(xml, "utf-8")
                    request.env["ir.ui.view.custom"].create(
                        {
                            "arch": arch,
                            "ref_id": view_id,
                            "user_id": request.session.uid,
                        }
                    )
                    return True

        return False
