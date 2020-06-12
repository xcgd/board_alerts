/* Alert board. */

/* Taken from the default "My board" dashboard.
 * Ref: odoo/addons/board/static/src/js/add_to_board_menu.js.
 *
 * Adapted to add an "Add to my alert board" menu command.
 */

odoo.define('board_alerts.AddToAlertBoardMenu', function(require) {
    "use strict";

    var ActionManager = require('web.ActionManager');
    var Context = require('web.Context');
    var core = require('web.core');
    var Domain = require('web.Domain');
    var favorites_submenus_registry = require('web.favorites_submenus_registry');
    var pyUtils = require('web.py_utils');
    var Widget = require('web.Widget');

    var _t = core._t;
    var QWeb = core.qweb;

    var AddToAlertBoardMenu = Widget.extend({
    events: _.extend({}, Widget.prototype.events, {
    'click .o_add_to_alert_board.o_menu_header': '_onAlertMenuHeaderClick',
    'click .o_add_to_alert_board_confirm_button': '_onAddToAlertBoardConfirmButtonClick',
    'click .o_add_to_alert_board_input': '_onAddToAlertBoardInputClick',
    'keyup .o_add_to_alert_board_input': '_onAlertKeyUp',
    }),
    /**
     * @override
     * @param {Object} params
     * @param {Object} params.action an ir.actions description
     */
    init: function(parent, params) {
        this._super(parent);
        this.action = params.action;
        this.isOpen = false;
    },
    /**
     * @override
     */
    start: function() {
        if (this.action.id && this.action.type === 'ir.actions.act_window') {
            this._render();
        }
        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Closes the menu and render it.
     * 
     */
    closeMenu: function() {
        this.isOpen = false;
        this._render();
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * This is the main function for actually saving the dashboard. This method is supposed to call
     * the route /board/add_to_alert_dashboard with proper information.
     * 
     * @private
     * @returns {Promise}
     */
    _addToAlertBoard: function() {
        var self = this;
        var searchQuery;
        // TO DO: for now the domains in query are evaluated.
        // This should be changed I think.
        this.trigger_up('get_search_query', {
            callback: function(query) {
                searchQuery = query;
            }
        });
        // TO DO: replace direct reference to action manager, controller, and currentAction in code below

        // AAB: trigger_up an event that will be intercepted by the controller,
        // as soon as the controller is the parent of the control panel
        var actionManager = this.findAncestor(function(ancestor) {
            return ancestor instanceof ActionManager;
        });
        var controller = actionManager.getCurrentController();

        var context = new Context(this.action.context);
        context.add(searchQuery.context);
        context.add({
        group_by: searchQuery.groupBy,
        orderedBy: searchQuery.orderedBy,
        });

        this.trigger_up('get_controller_query_params', {
            callback: function(controllerQueryParams) {
                var queryContext = controllerQueryParams.context;
                var allContext = _.extend(_.omit(controllerQueryParams, ['context']), queryContext);
                context.add(allContext);
            }
        });

        var domain = new Domain(this.action.domain || []);
        domain = Domain.prototype.normalizeArray(domain.toArray().concat(searchQuery.domain));

        var evalutatedContext = pyUtils.eval('context', context);
        for ( var key in evalutatedContext) {
            if (evalutatedContext.hasOwnProperty(key) && /^search_default_/.test(key)) {
                delete evalutatedContext[key];
            }
        }
        evalutatedContext.dashboard_merge_domains_contexts = false;

        var name = this.$input.val();

        this.closeMenu();

        return self._rpc({
        route: '/board/add_to_alert_dashboard',
        params: {
        action_id: self.action.id || false,
        context_to_save: evalutatedContext,
        domain: domain,
        view_mode: controller.viewType,
        name: name,
        },
        }).then(function(r) {
            if (r) {
                self.do_notify(_.str.sprintf(_t("'%s' added to alert dashboard"), name), _t('Please refresh your browser for the changes to take effect.'));
            } else {
                self.do_warn(_t("Could not add filter to alert dashboard"));
            }
        });
    },
    /**
     * Renders and focuses the unique input if it is visible.
     * 
     * @private
     */
    _render: function() {
        var $el = QWeb.render('AddToAlertBoardMenu', {
            widget: this
        });
        this._replaceElement($el);
        if (this.isOpen) {
            this.$input = this.$('.o_add_to_alert_board_input');
            this.$input.val(this.action.name);
            this.$input.focus();
        }
    },
    /**
     * Hides and displays the submenu which allows adding custom filters.
     * 
     * @private
     */
    _toggleMenu: function() {
        this.isOpen = !this.isOpen;
        this._render();
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {jQueryEvent} event
     */
    _onAddToAlertBoardInputClick: function(event) {
        event.preventDefault();
        event.stopPropagation();
        this.$input.focus();
    },
    /**
     * @private
     * @param {jQueryEvent} event
     */
    _onAddToAlertBoardConfirmButtonClick: function(event) {
        event.preventDefault();
        event.stopPropagation();
        this._addToAlertBoard();
    },
    /**
     * @private
     * @param {jQueryEvent} event
     */
    _onAlertKeyUp: function(event) {
        if (event.which === $.ui.keyCode.ENTER) {
            this._addToAlertBoard();
        }
    },
    /**
     * @private
     * @param {jQueryEvent} event
     */
    _onAlertMenuHeaderClick: function(event) {
        event.preventDefault();
        event.stopPropagation();
        this._toggleMenu();
    },

    });

    // Use prio=11 here so this comes right after the base "add_to_board_menu" which has prio=10.
    favorites_submenus_registry.add('add_to_alert_board_menu', AddToAlertBoardMenu, 11);

    return AddToAlertBoardMenu;
});
