# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class PurchaseRequestLine(models.Model):

    _inherit = 'purchase.request.line'

    analytic_resource_plan_lines = fields.Many2many(
        'analytic.resource.plan.line',
        'purchase_request_line_analytic_resource_plan_line_line_rel',
        'purchase_request_line_id',
        'analytic_resource_plan_line_id',
        'Purchase Request Lines', readonly=True)
