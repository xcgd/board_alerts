/* Alert board. */

/* Taken from the default "My board" dashboard.
 * Ref: odoo/addons/board/static/js/dashboard.js.
 *
 * Adapted to add an "Add to my alert board" menu command.
 */

odoo.define('board_alerts.alert_board', function(require) {
    'use strict';

    var ActionManager = require('web.ActionManager');
    var core = require('web.core');
    var data = require('web.data');
    var FavoriteMenu = require('web.FavoriteMenu');
    var Model = require('web.DataModel');
    var pyeval = require('web.pyeval');
    var ViewManager = require('web.ViewManager');
    var data_manager = require('web.data_manager');

    var _t = core._t;
    var QWeb = core.qweb;

    FavoriteMenu.include({
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
                self.toggle_alert_dashboard_menu();
            });
            this.$add_alert_dashboard_btn.click(this.proxy('add_alert_dashboard'));
        }
        return this._super();
    },
    toggle_alert_dashboard_menu: function(is_open) {
        this.$add_alert_dashboard_link.toggleClass(
            'o_closed_menu',
            !(_.isUndefined(is_open)) ? !is_open : undefined
        ).toggleClass('o_open_menu', is_open);
        this.$add_to_alert_dashboard.toggle(is_open);
        if (this.$add_alert_dashboard_link.hasClass('o_open_menu')) {
            this.$add_alert_dashboard_input.focus();
        }
    },
    close_menus: function() {
        if (this.add_to_alert_dashboard_available) {
            this.toggle_alert_dashboard_menu(false);
        }
        this._super();
    },
    add_alert_dashboard: function() {
        var self = this;

        var search_data = this.searchview.build_search_data(),
            context = new data.CompoundContext(this.searchview.dataset.get_context() || []),
            domain = new data.CompoundDomain(this.searchview.dataset.get_domain() || []);
        _.each(search_data.contexts, context.add, context);
        _.each(search_data.domains, domain.add, domain);

        context.add({
            group_by: pyeval.eval('groupbys', search_data.groupbys || [])
        });
        context.add(this.view_manager.active_view.controller.get_context());
        var c = pyeval.eval('context', context);
        for ( var k in c) {
            if (c.hasOwnProperty(k) && /^search_default_/.test(k)) {
                delete c[k];
            }
        }
        this.toggle_alert_dashboard_menu(false);
        c.dashboard_merge_domains_contexts = false;
        var d = pyeval.eval('domain', domain),
            board = new Model('board.board'),
            name = self.$add_alert_dashboard_input.val();

        return self.rpc('/board/add_to_alert_dashboard', {
        action_id: self.action_id || false,
        context_to_save: c,
        domain: d,
        view_mode: self.view_manager.active_view.type,
        name: name,
        }).then(function(r) {
            if (r) {
                self.do_notify(_.str.sprintf(_t("'%s' added to alert dashboard"), name), '');
                data_manager.invalidate();
            } else {
                self.do_warn(_t("Could not add filter to alert dashboard"));
            }
        });
    },
    });

});
