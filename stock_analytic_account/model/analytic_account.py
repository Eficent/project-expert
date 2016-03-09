# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    move_ids = fields.One2many('stock.move', 'analytic_account_id',
                               'Moves for this analytic account',
                               readonly=True)
    use_reserved_stock = fields.Boolean('Use reserved stock',
                                        help="Stock with reference to this "
                                        "analytic account is considered to be "
                                        "reserved.")

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default['move_ids'] = []
        res = super(AccountAnalyticAccount, self).copy(default)
        return res
