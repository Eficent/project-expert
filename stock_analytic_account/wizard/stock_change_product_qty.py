# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from openerp import tools
from openerp import api, fields, models, _
from openerp.exceptions import Warning


class StockChangeProductQty(models.TransientModel):
    _inherit = "stock.change.product.qty"

    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account')

    @api.multi
    def change_product_qty(self):
        """Override to pass the analytic account to inventory."""
        inventory_obj = self.env['stock.inventory']
        inventory_line_obj = self.env['stock.inventory.line']
        for data in self:
            if data.new_quantity < 0:
                raise Warning(_('Quantity cannot be negative.'))
            if data.product_id.id and data.lot_id.id:
                filters = 'none'
            elif data.product_id.id:
                filters = 'product'
            else:
                filters = 'none'
            loc_id = data.location_id.id
            lot_id = data.lot_id.id
            inventory = inventory_obj.create({
                'name': _('INV: %s') % tools.ustr(data.product_id.name),
                'filter': filters,
                'product_id': data.product_id.id,
                'location_id': loc_id,
                'lot_id': lot_id,
            })
            product = data.product_id.with_context(location=loc_id,
                                                   lot_id=lot_id)
            th_qty = product.qty_available
            line_data = {
                'inventory_id': inventory.id,
                'product_qty': data.new_quantity,
                'location_id': data.location_id.id,
                'product_id': data.product_id.id,
                'product_uom_id': data.product_id.uom_id.id,
                'theoretical_qty': th_qty,
                'prod_lot_id': data.lot_id.id,
                # START OF stock_analytic_account
                'analytic_account_id': data.analytic_account_id.id,
            }
            context = ({
                'analytic_account_id': data.analytic_account_id.id,
                'analytic_reserved': True,
            })
            # END OF stock_analytic_account
            inventory_line_obj.with_context(context).create(line_data)
            inventory.with_context(context).action_done()
        return {}
