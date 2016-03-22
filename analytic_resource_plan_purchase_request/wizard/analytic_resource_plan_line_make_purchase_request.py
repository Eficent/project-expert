# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp.tools import misc
from openerp.tools.translate import _
from openerp import api, fields, models
from openerp import netsvc
import openerp.addons.decimal_precision as dp


class AnalyticResourcePlanLineMakePurchaseRequest(models.TransientModel):
    _name = "analytic.resource.plan.line.make.purchase.request"
    _description = "Resource plan make purchase request"

    origin = fields.Char('Origin', required=True)
    description = fields.Text('Description')
    item_ids = fields.One2many('analytic.resource.plan.line.make.purchase.request.item',
                               'wiz_id', 'Items')

    @api.model
    def _prepare_item(self, line):
        return {
            'account_id': line.account_id.id,
            'product_id': line.product_id.id,
            'product_qty': line.unit_amount,
            'product_uom_id': line.product_uom_id.id,
            'line_id': line.id,
        }

    @api.model
    def default_get(self, fields):
        res = super(AnalyticResourcePlanLineMakePurchaseRequest,
                    self).default_get(fields)
        res_plan_obj = self.env['analytic.resource.plan.line']
        resource_plan_line_ids = self._context.get('active_ids', [])
        active_model = self._context.get('active_model')
        if not resource_plan_line_ids:
            return res
        assert active_model == 'analytic.resource.plan.line', \
            'Bad context propagation'

        items = []
        for line in res_plan_obj.browse(resource_plan_line_ids):
                items.append((0, 0, self._prepare_item(line)))
        res['item_ids'] = items
        return res

    @api.model
    def _prepare_purchase_request(self, make_purchase_request,
                                  company_id):
        data = {
            'company_id': company_id,
            'origin': make_purchase_request.origin,
            'description': make_purchase_request.description,
            }
        return data

    @api.model
    def _prepare_purchase_request_line(self, pr, item):
        return {
            'request_id': pr.id,
            'name': item.product_id.name,
            'product_qty': item.product_qty,
            'product_id': item.product_id.id,
            'product_uom_id': item.product_uom_id.id,
            'date_required': item.line_id.date or False,
            'analytic_account_id': item.line_id.account_id.id,
            'analytic_resource_plan_lines': [(4, item.line_id.id)]
        }

    @api.multi
    def make_purchase_request(self):
        res = []
        make_purchase_request = self[0]
        request_obj = self.env['purchase.request']
        request_line_obj = self.env['purchase.request.line']
        company_id = False
        warehouse_id = False
        request_id = False
        for item in make_purchase_request.item_ids:
            line = item.line_id
            if line.state != 'confirm':
                raise Warning(_('Could not create purchase request !'
                                'All resource plan lines must be confirmed.'))
            if item.product_qty < 0.0:
                raise Warning(_('Could not create purchase request !'
                                'Enter a positive quantity.'))

            line_company_id = line.account_id.company_id and\
                line.account_id.company_id.id or False
            if company_id is not False \
                    and line_company_id != company_id:
                raise Warning(_('Could not create purchase request ! You have '
                                'to select lines from the same company.'))
            else:
                company_id = line_company_id

            line_warehouse_id = line.account_id.warehouse_id \
                and line.account_id.warehouse_id.id or False
            if warehouse_id is not False \
                    and line_warehouse_id != warehouse_id:
                raise Warning(_('Could not create purchase request ! You have '
                                'to select lines from the same warehouse.'))
            else:
                warehouse_id = line_warehouse_id

            if request_id is False:
                request_data = self._prepare_purchase_request(
                    make_purchase_request, company_id)
                request = request_obj.create(request_data)
            request_line_data = make_purchase_request.\
                _prepare_purchase_request_line(request, item)
            request_line = request_line_obj.create(request_line_data)
            values = {
                'purchase_request_lines': [(4, request_line.id)]
            }
            line.write(values)
            project_manager_id = line.account_id.user_id and \
                line.account_id.user_id.partner_id.id or False
            if project_manager_id:
                message_follower_ids = [x.id for x in
                                        request.message_follower_ids]
                if project_manager_id not in message_follower_ids:
                    request.write({
                        'message_follower_ids': (4, project_manager_id)})
            res.append(request_line.id)

        return {
            'domain': "[('id','in', [" + ','.join(map(str, res)) + "])]",
            'name': _('Purchase Request Lines'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.request.line',
            'view_id': False,
            'context': False,
            'type': 'ir.actions.act_window'
        }


class AnalyticResourcePlanLineMakePurchaseRequestItem(models.TransientModel):
    _name = "analytic.resource.plan.line.make.purchase.request.item"
    _description = "Resource plan make purchase request item"

    wiz_id = fields.Many2one(
        'analytic.resource.plan.line.make.purchase.request',
        'Wizard', required=True, ondelete='cascade',
        readonly=True)
    line_id = fields.Many2one('analytic.resource.plan.line',
                              'Resource Plan Line',
                              required=True, readonly=True)
    account_id = fields.Many2one(related='line_id.account_id',
                                 relation='account.analytic.account',
                                 string='Analytic Account',
                                 readonly=True)
    product_id = fields.Many2one(related='line_id.product_id',
                                 relation='product.product',
                                 string='Product',
                                 readonly=True)
    product_qty = fields.Float(string='Quantity to request',
                               digits_compute=dp.get_precision(
                                                               'Product UoS'))
    product_uom_id = fields.Many2one(related='line_id.product_uom_id',
                                     relation='product.uom',
                                     string='UoM',
                                     readonly=True)
