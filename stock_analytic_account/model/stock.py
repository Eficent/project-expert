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
from openerp import api, fields, models
from openerp.exceptions import Warning
from openerp.tools.translate import _
import logging
from openerp import netsvc
_logger = logging.getLogger(__name__)
from openerp.tools import float_compare, frozendict


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account')

    @api.model
    def quants_get_prefered_domain(self, location, product, qty,
                                   domain=None, prefered_domain_list=[],
                                   restrict_lot_id=False,
                                   restrict_partner_id=False):
#    def quants_get_prefered_domain(self, qty, move, ops=False, lot_id=False,
#                                    domain=None, preferred_domain_list=[]):
        '''
        Override to add the condition in domain to search quants of specific
        analytic accounts.
        '''
        analytic_account_id = self.env.args[2].get('analytic_account_id',
                                                   False)
#        analytic_reserved = self._context.get('analytic_reserved', False)
        domain += [('analytic_account_id', '=', analytic_account_id)]
        return super(StockQuant, self).\
            quants_get_prefered_domain(location, product, qty,
                                   domain=domain,
                                   prefered_domain_list=prefered_domain_list,
                                   restrict_lot_id=restrict_lot_id,
                                   restrict_partner_id=restrict_partner_id)

    @api.model
    def _quant_create(self, qty, move, lot_id=False, owner_id=False,
                      src_package_id=False, dest_package_id=False,
                      force_location_from=False, force_location_to=False):
        quant = super(StockQuant, self).\
            _quant_create(qty, move, lot_id=lot_id,
                          owner_id=owner_id,
                          src_package_id=src_package_id,
                          dest_package_id=dest_package_id,
                          force_location_from=force_location_from,
                          force_location_to=force_location_to)
        quant.write({'analytic_account_id': move.analytic_account_id.id})
        return quant


class StockMove(models.Model):
    _inherit = "stock.move"

    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account')
    analytic_reserved =\
        fields.Boolean('Reserved', help="Reserved for the Analytic Account")
    analytic_account_user_id =\
        fields.Many2one('res.users', 'Project Manager', store=True,
                        related='analytic_account_id.user_id', readonly=True)

    @api.model
    def _get_analytic_reserved(self, vals):
        aa_id = vals.get('analytic_account_id')
        if aa_id:
            analytic_obj = self.env['account.analytic.account']
            return analytic_obj.browse(aa_id).use_reserved_stock
        return False

    @api.model
    def create(self, vals):
        if 'analytic_account_id' in vals:
            vals['analytic_reserved'] = self._get_analytic_reserved(vals)
        return super(StockMove, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'analytic_account_id' in vals:
            vals['analytic_reserved'] = self._get_analytic_reserved(vals)
        return super(StockMove, self).write(vals)

    @api.multi
    def action_assign(self):
        """ Checks the product type and accordingly writes the state.
        """
        quant_obj = self.env["stock.quant"]
        to_assign_moves = set()
        main_domain = {}
        todo_moves = []
        operations = set()
        for move in self:
            cr, uid, context = move.env.args
            context = dict(context)
            context.update({
                'analytic_account_id': move.analytic_account_id.id,
                'analytic_reserved': move.analytic_reserved,
            })
            move.env.args = cr, uid, frozendict(context)
            if move.state not in ('confirmed', 'waiting', 'assigned'):
                continue
            if move.location_id.usage in ('supplier', 'inventory', 'production'):
                to_assign_moves.add(move.id)
                #in case the move is returned, we want to try to find quants before forcing the assignment
                if not move.origin_returned_move_id:
                    continue
            if move.product_id.type == 'consu':
                to_assign_moves.add(move.id)
                continue
            else:
                todo_moves.append(move)

                #we always keep the quants already assigned and try to find the remaining quantity on quants not assigned only
                main_domain[move.id] = [('reservation_id', '=', False), ('qty', '>', 0)]

                #if the move is preceeded, restrict the choice of quants in the ones moved previously in original move
                ancestors = self.find_move_ancestors(move)
                if move.state == 'waiting' and not ancestors:
                    #if the waiting move hasn't yet any ancestor (PO/MO not confirmed yet), don't find any quant available in stock
                    main_domain[move.id] += [('id', '=', False)]
                elif ancestors:
                    main_domain[move.id] += [('history_ids', 'in', ancestors)]

                #if the move is returned from another, restrict the choice of quants to the ones that follow the returned move
                if move.origin_returned_move_id:
                    main_domain[move.id] += [('history_ids', 'in', move.origin_returned_move_id.id)]
                for link in move.linked_move_operation_ids:
                    operations.add(link.operation_id)
        # Check all ops and sort them: we want to process first the packages, then operations with lot then the rest
        operations = list(operations)
        operations.sort(key=lambda x: ((x.package_id and not x.product_id) and -4 or 0) + (x.package_id and -2 or 0) + (x.lot_id and -1 or 0))
        for ops in operations:
            #first try to find quants based on specific domains given by linked operations
            for record in ops.linked_move_operation_ids:
                move = record.move_id
                if move.id in main_domain:
                    domain = main_domain[move.id] + self.env['stock.move.operation.link'].get_specific_domain(record)
                    qty = record.qty
                    if qty:
                        quants = quant_obj.quants_get_prefered_domain(ops.location_id, move.product_id, qty, domain=domain, prefered_domain_list=[], restrict_lot_id=move.restrict_lot_id.id, restrict_partner_id=move.restrict_partner_id.id)
                        quant_obj.quants_reserve(quants, move, record)
        for move in todo_moves:
            if move.linked_move_operation_ids:
                continue
            #then if the move isn't totally assigned, try to find quants without any specific domain
            if move.state != 'assigned':
                qty_already_assigned = move.reserved_availability
                qty = move.product_qty - qty_already_assigned
                quants = quant_obj.quants_get_prefered_domain(move.location_id, move.product_id, qty, domain=main_domain[move.id], prefered_domain_list=[], restrict_lot_id=move.restrict_lot_id.id, restrict_partner_id=move.restrict_partner_id.id)
                print "\n\n#    ", quants
                quant_obj.quants_reserve(quants, move)

        #force assignation of consumable products and incoming from supplier/inventory/production
        if to_assign_moves:
            to_assign_moves = self.browse(to_assign_moves)
            to_assign_moves.force_assign(list(to_assign_moves))

    @api.multi
    def action_scrap(self, quantity, location_id, restrict_lot_id=False,
                     restrict_partner_id=False):
        """ Move the scrap/damaged product into scrap location
        @param cr: the database cursor
        @param uid: the user id
        @param ids: ids of stock move object to be scrapped
        @param quantity : specify scrap qty
        @param location_id : specify scrap location
        @param context: context arguments
        @return: Scraped lines
        """
        quant_obj = self.env["stock.quant"]
        #quantity should be given in MOVE UOM
        if quantity <= 0:
            raise Warning(_('Please provide a positive quantity to scrap.'))
        res = []
        for move in self:
            source_location = move.location_id
            if move.state == 'done':
                source_location = move.location_dest_id
            # Previously used to prevent scraping from virtual location but not
                # necessary anymore
            # if source_location.usage != 'internal':
                # restrict to scrap from a virtual location because it's
                # meaningless and it may introduce errors in stock
                # ('creating' new products from nowhere)
                # raise osv.except_osv(_('Error!'),
                # _('Forbidden operation: it is not allowed to scrap products \
                # from a virtual location.'))
            move_qty = move.product_qty
            uos_qty = quantity / move_qty * move.product_uos_qty
            default_val = {
                'location_id': source_location.id,
                'product_uom_qty': quantity,
                'product_uos_qty': uos_qty,
                'state': move.state,
                'scrapped': True,
                'location_dest_id': location_id,
                'restrict_lot_id': restrict_lot_id,
                'restrict_partner_id': restrict_partner_id,
                # START OF stock_analytic_account
                'analytic_account_id': move.analytic_account_id.id,
                # ENF OF stock_analytic_account
            }
            new_move = move.copy(default_val)

            res += [new_move]
            product_obj = self.env['product.product']
            for product in product_obj.browse([move.product_id.id]):
                if move.picking_id:
                    uom = product.uom_id.name if product.uom_id else ''
                    message = _("%s %s %s has been <b>moved to</b> scrap.") %\
                        (quantity, uom, product.name)
                    move.picking_id.message_post(body=message)

            # We "flag" the quant from which we want to scrap the products.
            # To do so:
            #    - we select the quants related to the move we scrap from
            #    - we reserve the quants with the scrapped move
            # See self.action_done, et particularly how is defined the
            # "prefered_domain" for clarification
            if move.state == 'done' and new_move.location_id.usage not in\
                    ('supplier', 'inventory', 'production'):
                domain = [('qty', '>', 0), ('history_ids', 'in', [move.id])]
                # We use scrap_move data since a reservation makes sense
                # for a move not already done
                quants =\
                    quant_obj.quants_get_prefered_domain(new_move.location_id,
                        new_move.product_id, quantity, domain=domain,
                        prefered_domain_list=[],
                        restrict_lot_id=new_move.restrict_lot_id.id,
                        restrict_partner_id=new_move.restrict_partner_id.id)
                quant_obj.quants_reserve(quants, new_move)
        self.action_done(res)
        return res

#    def check_assign(self, cr, uid, ids, context=None):
#        """ Checks the product type and accordingly writes the state.
#        @return: No. of moves done
#        """
#        done = []
#        count = 0
#        pickings = {}
#        if context is None:
#            context = {}
#        for move in self.browse(cr, uid, ids, context=context):
#            if move.product_id.type == 'consu' or move.location_id.usage == 'supplier':
#                if move.state in ('confirmed', 'waiting'):
#                    done.append(move.id)
#                pickings[move.picking_id.id] = 1
#                continue
#            if move.state in ('confirmed', 'waiting'):
#                # Important: we must pass lock=True to _product_reserve() to avoid race conditions and double reservations
#                if move.analytic_reserved:
#                    analytic_account_id = move.analytic_account_id.id
#                else:
#                    analytic_account_id = False
#                res = self.pool.get(
#                    'stock.location')._product_reserve(
#                    cr, uid, [move.location_id.id], move.product_id.id,
#                    move.product_qty, {'uom': move.product_uom.id,
#                                       'analytic_account_id':
#                                           analytic_account_id}, lock=True)
#                if res:
#                    #_product_available_test depends on the next status for correct functioning
#                    #the test does not work correctly if the same product occurs multiple times
#                    #in the same order. This is e.g. the case when using the button 'split in two' of
#                    #the stock outgoing form
#                    self.write(cr, uid, [move.id], {'state':'assigned'})
#                    done.append(move.id)
#                    pickings[move.picking_id.id] = 1
#                    r = res.pop(0)
#                    product_uos_qty = self.pool.get('stock.move').onchange_quantity(cr, uid, [move.id], move.product_id.id, r[0], move.product_id.uom_id.id, move.product_id.uos_id.id)['value']['product_uos_qty']
#                    cr.execute('update stock_move set location_id=%s, product_qty=%s, product_uos_qty=%s where id=%s', (r[1], r[0],product_uos_qty, move.id))
#
#                    while res:
#                        r = res.pop(0)
#                        product_uos_qty = self.pool.get('stock.move').onchange_quantity(cr, uid, [move.id], move.product_id.id, r[0], move.product_id.uom_id.id, move.product_id.uos_id.id)['value']['product_uos_qty']
#                        move_id = self.copy(cr, uid, move.id, {'product_uos_qty': product_uos_qty, 'product_qty': r[0], 'location_id': r[1]})
#                        done.append(move_id)
#        if done:
#            count += len(done)
#            self.write(cr, uid, done, {'state': 'assigned'})
#
#        if count:
#            for pick_id in pickings:
#                wf_service = netsvc.LocalService("workflow")
#                wf_service.trg_write(uid, 'stock.picking', pick_id, cr)
#        return count


class StockLocation(models.Model):
    _inherit = "stock.location"

    def _product_reserve(self, cr, uid, ids, product_id, product_qty,
                         context=None, lock=False):
        """
        Override the _product_reserve method in order to add the analytic
        account
        """
        result = super(StockLocation, self)._product_reserve(
            cr, uid, ids, product_id, product_qty, context, lock)
        if context is None:
            context = {}
        result = []
        amount = 0.0
        if context is None:
            context = {}
        uom_obj = self.pool.get('product.uom')
        uom_rounding = self.pool.get('product.product').browse(
            cr, uid, product_id, context=context).uom_id.rounding
        if context.get('uom'):
            uom_rounding = uom_obj.browse(cr, uid, context.get('uom'),
                                          context=context).rounding
        analytic_account_id = context.get('analytic_account_id', False)

        for id in self.search(cr, uid, [('location_id', 'child_of', ids)]):
            params = {}
            if analytic_account_id:
                lines_where_clause = \
                    "AND analytic_account_id=%(p_analytic_account_id)s"
                params['p_analytic_account_id'] = analytic_account_id
            else:
                lines_where_clause = "AND analytic_account_id IS NULL"
            params.update({'p_location': id, 'p_product_id': product_id})

            query = ("SELECT product_uom, sum(product_qty) AS product_qty"
                     " FROM stock_move"
                     " WHERE location_dest_id=%(p_location)s AND"
                     " location_id<>%(p_location)s AND"
                     " product_id=%(p_product_id)s AND"
                     " state='done' "
                     + lines_where_clause +
                     " GROUP BY product_uom")

            cr.execute(query, params)
            results = cr.dictfetchall()

            query = ("SELECT product_uom,-sum(product_qty) AS product_qty"
                     " FROM stock_move "
                     " WHERE location_id=%(p_location)s AND"
                     " location_dest_id<>%(p_location)s AND"
                     " product_id=%(p_product_id)s AND"
                     " state in ('done', 'assigned') "
                     + lines_where_clause +
                     " GROUP BY product_uom")
            cr.execute(query, params)
            results += cr.dictfetchall()
            total = 0.0
            results2 = 0.0
            for r in results:
                amount = uom_obj._compute_qty(cr, uid, r['product_uom'],
                                              r['product_qty'],
                                              context.get('uom', False))
                results2 += amount
                total += amount
            if total <= 0.0:
                continue

            amount = results2
            compare_qty = float_compare(amount, 0,
                                        precision_rounding=uom_rounding)
            if compare_qty == 1:
                if amount > min(total, product_qty):
                    amount = min(product_qty, total)
                result.append((amount, id))
                product_qty -= amount
                total -= amount
                if product_qty <= 0.0:
                    return result
                if total <= 0.0:
                    continue
        return False


class StockInventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account')

    @api.multi
    @api.constrains('location_id', 'product_id', 'prod_lot_id', 'analytic_account_id')
    def _check_inventory_line(self):
        """Refuse to record duplicate inventory lines
        Inventory lines with the sale Product, Location, Serial Number,
        Analytic Account and date are not taken into account correctly when
        computing the stock level difference, so we'll simply refuse to
        record them rather than allow users to introduce errors without
        even knowing it."""
        for line in self:
            inv_lines = self.search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.location_id.id),
                    ('prod_lot_id', '=', (
                        line.prod_lot_id
                        and line.prod_lot_id.id
                        or False)),
                    ('inventory_id.date', '=', line.inventory_id.date),
                    ('analytic_account_id', '=', line.analytic_account_id.id),
                    ('id', 'not in', self._ids),
                ])
            if inv_lines:
                raise Warning(
                    _('Duplicate line detected'),
                    _('You cannot enter more than a single inventory line for '
                      'the same Product, Location, Serial Number, Analytic '
                      'Account and date : \n'
                      '- Product: %s\n'
                      '- Location: %s\n'
                      '- Serial Number: %s\n'
                      '- Analytic Account: %s.') % (
                        line.product_id.default_code,
                        line.location_id.name,
                        (line.prod_lot_id and line.prod_lot_id.id or _('N/A')),
                        (line.analytic_account_id and
                         line.analytic_account_id.name or _('N/A')))
                )

#    _constraints = [
#        (_check_inventory_line, 'Duplicate line detected',
#         ['location_id', 'product_id', 'prod_lot_id', 'analytic_account_id'])
#    ]

    @api.model
    def xcreate(self, values):
        cr, uid, context = self.env.args
        context = dict(context.copy())
        context.update({
            'analytic_account_id': values.get('analytic_account_id', False)
        })
        print "\n\n#######    " ,context
        self.env.args = cr, uid, frozendict(context)
        return super(StockInventoryLine, self).create(values)

    def _resolve_inventory_line(self, cr, uid, inventory_line, context=None):
        stock_move_obj = self.pool.get('stock.move')
        quant_obj = self.pool.get('stock.quant')
        diff = inventory_line.theoretical_qty - inventory_line.product_qty
        if not diff:
            return
        #each theorical_lines where difference between theoretical and checked quantities is not 0 is a line for which we need to create a stock move
        vals = {
            'name': _('INV:') + (inventory_line.inventory_id.name or ''),
            'product_id': inventory_line.product_id.id,
            'product_uom': inventory_line.product_uom_id.id,
            'date': inventory_line.inventory_id.date,
            'company_id': inventory_line.inventory_id.company_id.id,
            'inventory_id': inventory_line.inventory_id.id,
            'state': 'confirmed',
            'restrict_lot_id': inventory_line.prod_lot_id.id,
            'restrict_partner_id': inventory_line.partner_id.id,
            'analytic_account_id': inventory_line.analytic_account_id.id,
        }
        inventory_location_id = inventory_line.product_id.property_stock_inventory.id
        if diff < 0:
            #found more than expected
            vals['location_id'] = inventory_location_id
            vals['location_dest_id'] = inventory_line.location_id.id
            vals['product_uom_qty'] = -diff
        else:
            #found less than expected
            vals['location_id'] = inventory_line.location_id.id
            vals['location_dest_id'] = inventory_location_id
            vals['product_uom_qty'] = diff
        move_id = stock_move_obj.create(cr, uid, vals, context=context)
        move = stock_move_obj.browse(cr, uid, move_id, context=context)
        if diff > 0:
            domain = [('qty', '>', 0.0), ('package_id', '=', inventory_line.package_id.id), ('lot_id', '=', inventory_line.prod_lot_id.id), ('location_id', '=', inventory_line.location_id.id)]
            preferred_domain_list = [[('reservation_id', '=', False)], [('reservation_id.inventory_id', '!=', inventory_line.inventory_id.id)]]
            quants = quant_obj.quants_get_preferred_domain(cr, uid, move.product_qty, move, domain=domain, preferred_domain_list=preferred_domain_list)
            quant_obj.quants_reserve(cr, uid, quants, move, context=context)
        elif inventory_line.package_id:
            stock_move_obj.action_done(cr, uid, move_id, context=context)
            quants = [x.id for x in move.quant_ids]
            quant_obj.write(cr, uid, quants, {'package_id': inventory_line.package_id.id}, context=context)
            res = quant_obj.search(cr, uid, [('qty', '<', 0.0), ('product_id', '=', move.product_id.id),
                                    ('location_id', '=', move.location_dest_id.id), ('package_id', '!=', False)], limit=1, context=context)
            if res:
                for quant in move.quant_ids:
                    if quant.location_id.id == move.location_dest_id.id: #To avoid we take a quant that was reconcile already
                        quant_obj._quant_reconcile_negative(cr, uid, quant, move, context=context)
        return move_id


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    @api.model
    def _inventory_line_hook(self, cr, uid, inventory_line, move_vals):
        """ Creates a stock move from an inventory line
        @param inventory_line:
        @param move_vals:
        @return:
        """
        if inventory_line.analytic_account_id:
            move_vals['analytic_account_id'] = \
                inventory_line.analytic_account_id.id
        return super(StockInventory, self)._inventory_line_hook(inventory_line,
                                                                move_vals)

    @api.multi
    def xaction_confirm(self):
        """ Confirm the inventory and writes its finished date
        Attention!!! This method overrides the standard without calling Super
        The changes introduced by this module are encoded within a
        comments START OF and END OF stock_analytic_account.
        @return: True
        """
        # to perform the correct inventory corrections we need analyze
        # stock location by
        # location, never recursively, so we use a special context
        product_context = dict(self._context, compute_child=False)

        location_obj = self.env['stock.location']
        for inv in self:
            move_ids = []
            for line in inv.line_ids:
                pid = line.product_id.id
                # START OF stock_analytic_account
                # Replace the existing entry:
                # product_context.update(uom=line.product_uom.id,
                # to_date=inv.date,
                # date=inv.date, prodlot_id=line.prod_lot_id.id)
                # ,with this one:
                product_context.update(
                    uom=line.product_uom.id, to_date=inv.date, date=inv.date,
                    lot_id=line.lot_id.id,
                    analytic_account_id=line.analytic_account_id.id,)
                # ENF OF stock_analytic_account
                amount = location_obj._product_get(line.location_id.id, [pid], product_context)[pid]
                change = line.product_qty - amount
                lot_id = line.lot_id.id
                analytic_account_id = line.analytic_account_id.id or False
                if change:
                    location_id = line.product_id.property_stock_inventory.id
                    value = {
                        'name': _('INV:') + (line.inventory_id.name or ''),
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom.id,
                        'prodlot_id': lot_id,

                        'date': inv.date,
                    }

                    if change > 0:
                        value.update({
                            'product_qty': change,
                            'location_id': location_id,
                            'location_dest_id': line.location_id.id,
                        })
                    else:
                        value.update({
                            'product_qty': -change,
                            'location_id': line.location_id.id,
                            'location_dest_id': location_id,
                        })
                    move_ids.append(self._inventory_line_hook(line, value))
            inv.write({'state': 'confirm', 'move_ids': [(6, 0, move_ids)]})
            self.env['stock.move'].action_confirm(move_ids)
        return True
