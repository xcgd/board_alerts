/* Alert board. */

/* Taken from the default "My board" dashboard.
 * Ref: odoo/addons/board/static/src/js/favorite_menu.js.
 *
 * Adapted to add an "Add to my alert board" menu command.
 */

odoo.define('board_alerts.alert_board', function(require) {
    'use strict';

    var ActionManager = require('web.ActionManager');
    var Context = require('web.Context');
    var core = require('web.core');
    var Domain = require('web.Domain');
    var FavoriteMenu = require('web.FavoriteMenu');
    var pyeval = require('web.pyeval');
    var ViewManager = require('web.ViewManager');

    var _t = core._t;
    var QWeb = core.qweb;

    FavoriteMenu.include({

    // Same as the base "start" function.
    start: function() {
        var self = this;
        if (this.action_id === undefined) {
            return this._super();
        }
        var am = this.findAncestor(function(a) {
            return a instanceof ActionManager;
        });
        if (am && am.get_inner_widget() instanceof ViewManager) {
            this.view_manager = am.get_inner_widget();
            this.add_to_alert_dashboard_available = true;
            this.$('.o_favorites_menu').append(QWeb.render('SearchView.add_to_alert_dashboard'));
            this.$add_to_alert_dashboard = this.$('.o_add_to_alert_dashboard');
            this.$add_alert_dashboard_btn = this.$add_to_alert_dashboard.eq(1).find('button');
            this.$add_alert_dashboard_input = this.$add_to_alert_dashboard.eq(0).find('input');
            this.$add_alert_dashboard_link = this.$('.o_add_to_alert_dashboard_link');
            var title = this.searchview.get_title();
            this.$add_alert_dashboard_input.val(title);
            this.$add_alert_dashboard_link.click(function(e) {
                e.preventDefault();
                self._toggleAlertDashboardMenu();
            });
            this.$add_alert_dashboard_btn.click(this.proxy('_addAlertDashboard'));
        }
        return this._super();
    },

    // Same as the base "_addDashboard" function.
    _addAlertDashboard: function() {
        var self = this;
        var search_data = this.searchview.build_search_data();
        var context = new Context(this.searchview.dataset.get_context() || []);
        var domain = this.searchview.dataset.get_domain() || [];

        _.each(search_data.contexts, context.add, context);
        _.each(search_data.domains, function(d) {
            domain.push.apply(domain, Domain.prototype.stringToArray(d));
        });

        context.add({
            group_by: pyeval.eval('groupbys', search_data.groupbys || [])
        });
        context.add(this.view_manager.active_view.controller.getContext());
        var c = pyeval.eval('context', context);
        for ( var k in c) {
            if (c.hasOwnProperty(k) && /^search_default_/.test(k)) {
                delete c[k];
            }
        }
        this._toggleAlertDashboardMenu(false);
        c.dashboard_merge_domains_contexts = false;

        var name = self.$add_alert_dashboard_input.val();

        return self._rpc({
        route: '/board/add_to_alert_dashboard',
        params: {
        action_id: self.action_id || false,
        context_to_save: c,
        domain: domain,
        view_mode: self.view_manager.active_view.type,
        name: name,
        },
        }).then(function(r) {
            if (r) {
                self.do_notify(_.str.sprintf(_t("'%s' added to alert dashboard"), name), '');
            } else {
                self.do_warn(_t("Could not add filter to alert dashboard"));
            }
        });
    },

    // Same as the base "_closeMenus" function.
    _closeMenus: function() {
        if (this.add_to_alert_dashboard_available) {
            this._toggleAlertDashboardMenu(false);
        }
        this._super();
    },

    // Same as the base "_toggleDashboardMenu" function.
    _toggleAlertDashboardMenu: function(isOpen) {
        this.$add_alert_dashboard_link // nowrap
        .toggleClass('o_closed_menu', !(_.isUndefined(isOpen)) ? !isOpen : undefined) // nowrap
        .toggleClass('o_open_menu', isOpen);
        this.$add_to_alert_dashboard.toggle(isOpen);
        if (this.$add_alert_dashboard_link.hasClass('o_open_menu')) {
            this.$add_alert_dashboard_input.focus();
        }
    },

    });

});
