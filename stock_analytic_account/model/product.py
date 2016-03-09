# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
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
