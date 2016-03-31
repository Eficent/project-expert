# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    analytic_account_ids =\
        fields.Many2one('account.analytic.account', 'Analytic Account',
                        readonly=True,
                        related='move_lines.analytic_account_id')
    analytic_account_user_ids =\
        fields.Many2one('res.users', 'Project Manager', readonly=True,
                        related='move_lines.analytic_account_user_id')
