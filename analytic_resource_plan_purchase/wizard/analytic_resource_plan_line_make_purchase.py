# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models
from openerp.tools.translate import _


class AnalyticResourcePlanLineMakePurchase(models.TransientModel):
    _name = "analytic.resource.plan.line.make.purchase"
    _description = "Resource plan - make purchase"

    @api.model
    def _get_order_lines(self):
        """
        Returns the order lines associated to the analytic accounts selected.
        """

        record_ids = self._context and self._context.get('active_ids', False)

        if record_ids:
            order_line_ids = []
            line_plan_obj = self.env['analytic.resource.plan.line']

            for line in line_plan_obj.browse(record_ids):
                    for order_line in line.order_line_ids:
                        order_line_id = order_line and order_line.id
                        order_line_ids.extend([order_line_id])
            if order_line_ids:
                return order_line_ids
        return False

    order_line_ids = fields.Many2many('purchase.order.line',
                                      'make_purchase_order_line_rel',
                                      'order_line_id',
                                      'make_purchase_order_id', default=_get_order_lines)

    @api.multi
    def make_purchase_orders(self):
        """
             To make purchases.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: A dictionary which of fields with values.

        """

        record_ids = self._context and self._context.get('active_ids', False)
        res = []
        if record_ids:
            line_plan_obj = self.env['analytic.resource.plan.line']
            order_obj = self.env['purchase.order']
            order_line_obj = self.env['purchase.order.line']
            partner_obj = self.env['res.partner']
            acc_pos_obj = self.env['account.fiscal.position']

            location_ids = []
            list_line = []
            supplier_data = False
            company_id = False
            purchase_id = False

            for line in line_plan_obj.browse(record_ids):
                if not line.supplier_id:
                    raise Warning(_('Could not create purchase order !'),
                        _('You have to enter a supplier.'))

                if supplier_data is not False \
                        and line.supplier_id.id != supplier_data:
                    raise Warning(_('Could not create purchase order !'),
                        _('You have to select lines '
                          'from the same supplier.'))
                else:
                    supplier_data = line.supplier_id.id

                address_id = partner_obj.address_get([line.supplier_id.id],
                    ['delivery'])['delivery']
                partner = line.supplier_id
                line_company_id = line.company_id \
                    and line.company_id.id or False
                if company_id is not False \
                        and line_company_id != company_id:
                    raise Warning(_('Could not create purchase order !'),
                        _('You have to select lines '
                          'from the same company.'))
                else:
                    company_id = line_company_id

                line_account_id = line.account_id \
                    and line.account_id.id or False

                account_id = line_account_id

                warehouse_obj = self.env['stock.warehouse']
                warehouses = warehouse_obj.search([('company_id', '=', company_id)])
                if warehouses:
                    location_ids = []
                    for lot_stock_ids in warehouses:
                        location_ids.append(lot_stock_ids.lot_stock_id.id)

                location_id = False
                if location_ids:
                    location_id = location_ids[0]

                purchase_order_line = {
                    'name': line.name,
                    'product_qty': line.unit_amount,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'price_unit': line.price_unit,
                    'date_planned': line.date,
                    'notes': line.notes,
                    'account_analytic_id': account_id,
                }
                taxes = False
                if line.product_id:
                    taxes_ids = \
                        line.product_id.product_tmpl_id.supplier_taxes_id
                    taxes = partner.property_account_position.map_tax(taxes_ids)

                if taxes:
                    purchase_order_line.update({
                        'taxes_id': [(6, 0, taxes)]
                    })
                list_line.append(purchase_order_line)

                if purchase_id is False:
                    purchase = order_obj.create(
                        {'origin': '',
                         'partner_id': line.supplier_id.id,
                         'partner_address_id': address_id,
                         'pricelist_id': line.pricelist_id.id,
                         'location_id': location_id,
                         'company_id': company_id,
                         'fiscal_position':
                            partner.property_account_position
                            and partner.property_account_position.id
                            or False,
                         'payment_term':
                            partner.property_supplier_payment_term
                            and partner.property_supplier_payment_term.id
                            or False
                         })
                    if line.account_id.user_id:
                        purchase.message_subscribe_users(user_ids=[line.account_id.user_id.id])

                purchase_order_line.update({
                    'order_id': purchase.id
                })

                order_line = order_line_obj.create(purchase_order_line)
                values = {
                    'order_line_ids': [(4, order_line.id)]
                }
                line.write(values)
                res.append(order_line.id)

        return {
            'domain': "[('id','in', ["+','.join(map(str, res))+"])]",
            'name': _('Purchase order lines'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order.line',
            'view_id': False,
            'context': False,
            'type': 'ir.actions.act_window'
        }
