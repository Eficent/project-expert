# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class AnalyticResourcePlanLine(models.Model):

    _inherit = 'analytic.resource.plan.line'

    @api.multi
    @api.depends('order_line_ids', 'order_line_ids.state')
    def _has_active_order(self):
        for plan_line in self:
            plan_line.has_active_order = False
            for order_line in plan_line.order_line_ids:
                if order_line.state and order_line.state != 'cancel':
                    plan_line.has_active_order = True

    order_line_ids = fields.Many2many('purchase.order.line',
                                       'analytic_resource_plan_order_line_rel',
                                       'order_line_id',
                                       'analytic_resource_plan_line_id')

    has_active_order = fields.Boolean(compute='_has_active_order', method=True,
                                      string='Order', help="Indicates that this resource plan line "
                                      "contains at least one non-cancelled purchase order.")

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default['order_line_ids'] = []
        return super(AnalyticResourcePlanLine, self).copy(default)
