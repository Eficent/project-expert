# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Eficent (<http://www.eficent.com/>)
#              Jordi Ballester Alomar <jordi.ballester@eficent.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
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
