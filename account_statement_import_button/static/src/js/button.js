/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";

patch(ListController.prototype, {
    get showImportStatementButton() {
        return this.props.resModel === "account.bank.statement";
    },

    async importStatement() {
        await this.actionService.doAction(
            "account_statement_import_file.account_statement_import_action"
        );
    },
});
