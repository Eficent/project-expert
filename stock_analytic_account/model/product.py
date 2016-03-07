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
from openerp import api, models


class Product(models.Model):
    _inherit = 'product.product'

    @api.multi
    def _get_domain_locations(self):
        """
        Override to add condition for analytic account.
        """
        # START OF stock_analytic_account
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc =\
            super(Product, self)._get_domain_locations()
        analytic_account_id = self._context.get('analytic_account_id', False)
        analytic_domain = [('analytic_account_id', '=', analytic_account_id)]
        domain_quant_loc += analytic_domain
        if analytic_account_id:
            analytic_domain += [('analytic_reserved', '=', True)]
        domain_move_in_loc += analytic_domain
        domain_move_out_loc += analytic_domain
        # END OF stock_analytic_account
        return (domain_quant_loc, domain_move_in_loc, domain_move_out_loc)
