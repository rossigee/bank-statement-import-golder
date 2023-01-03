odoo.define('account_statment_import_button.statement_view', function (require) {
    "use strict";

    var ListView = require('web.ListView');

    ListView.include({
        renderButtons: function($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                let import_button = this.$buttons.find('.o_list_button_import');
                import_button && import_button.click(this.proxy('import_statement_button')) ;
            }
        },

        import_statement_button: function () {
            console.log("BUTTON PRESSED");
            var action = ({
                type: 'ir.actions.act_window',
                res_model: 'account_statement_import.account_statement_import_action',
                view_type: 'form',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new'
            })
            this.do_action(action);
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            };
        }
    });

    // core.action_registry.add('account_statment_import_button.statement_view', ListView);
    // return ListView;
})
