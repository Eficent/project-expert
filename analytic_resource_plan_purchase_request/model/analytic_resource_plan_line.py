# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError

_REQUEST_STATE = [
    ('none', 'No Request'),
    ('draft', 'Draft'),
    ('to_approve', 'To be approved'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected')
]


class AnalyticResourcePlanLine(models.Model):

    _inherit = 'analytic.resource.plan.line'

    @api.multi
    @api.depends('purchase_request_lines',
                 'purchase_request_lines.product_qty')
    def _requested_qty(self):
        for line in self:
            requested_qty = 0.0
            for purchase_line in line.purchase_request_lines:
                requested_qty += purchase_line.product_qty
            line.requested_qty = requested_qty

    @api.multi
    @api.depends('purchase_request_lines',
                 'purchase_request_lines.request_id.state')
    def _get_request_state(self):
        for line in self:
            line.request_state = 'none'
            if any([pr_line.request_id.state == 'approved' for pr_line in
                    line.purchase_request_lines]):
                line.request_state = 'approved'
            elif all([pr_line.request_id.state == 'cancel' for pr_line in
                      line.purchase_request_lines]):
                line.request_state = 'rejected'
            elif all([po_line.request_id.state in ('to_approve', 'cancel')
                      for po_line in line.purchase_request_lines]):
                line.request_state = 'to_approve'
            elif any([po_line.request_id.state == 'approved' for po_line in
                      line.purchase_request_lines]):
                line.request_state = 'approved'
            elif all([po_line.request_id.state in ('draft', 'cancel')
                      for po_line in line.purchase_request_lines]):
                line.request_state = 'draft'

    requested_qty = fields.Float(compute='_requested_qty',
                                 string='Requested quantity',
                                 readonly=True)
    request_state = fields.Selection(compute='_get_request_state',
                                     string='Request status',
                                     selection=_REQUEST_STATE, default='none')
    purchase_request_lines = fields.Many2many(
        'purchase.request.line',
        'purchase_request_line_analytic_resource_plan_line_line_rel',
        'analytic_resource_plan_line_id',
        'purchase_request_line_id',
        'Purchase Request Lines', readonly=True)

    @api.multi
    def unlink(self):
        for line in self:
            if line.purchase_request_lines:
                raise UserError(_('You cannot delete a record that refers to '
                                'purchase request lines!'))
        return super(AnalyticResourcePlanLine, self).unlink()
