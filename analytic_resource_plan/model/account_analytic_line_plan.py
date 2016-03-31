# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class AccountAnalyticLinePlan(models.Model):
    _inherit = 'account.analytic.line.plan'

    resource_plan_id = fields.Many2one('analytic.resource.plan.line',
                                       'Resource Plan Line',
                                       ondelete='cascade')

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default['resource_plan_id'] = False
        res = super(AccountAnalyticLinePlan, self).copy(default)
        return res
