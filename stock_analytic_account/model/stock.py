# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging
from openerp.exceptions import Warning
from openerp import api, fields, models, _
from openerp.tools import frozendict

_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account')

    @api.model
    def quants_get_prefered_domain(self, location, product, qty,
                                   domain=None, prefered_domain_list=[],
                                   restrict_lot_id=False,
                                   restrict_partner_id=False):
        '''
        Override to add the condition in domain to search quants of specific
        analytic accounts.
        '''
        analytic_account_id = self.env.args[2].get('analytic_account_id',
                                                   False)
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
    _inherit = 'stock.move'

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
        """Checks the product type and accordingly writes the state."""
        quant_obj = self.env["stock.quant"]
        to_assign_moves = set()
        main_domain = {}
        todo_moves = []
        operations = set()
        op_link_obj = self.env['stock.move.operation.link']
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
            if move.location_id.usage in ('supplier', 'inventory',
                                          'production'):
                to_assign_moves.add(move.id)
                # in case the move is returned, we want to try to find quants
                # before forcing the assignment
                if not move.origin_returned_move_id:
                    continue
            if move.product_id.type == 'consu':
                to_assign_moves.add(move.id)
                continue
            else:
                todo_moves.append(move)

                # we always keep the quants already assigned and try to find
                # the remaining quantity on quants not assigned only
                main_domain[move.id] = [('reservation_id', '=', False),
                                        ('qty', '>', 0)]

                # if the move is preceeded, restrict the choice of quants in
                # the ones moved previously in original move
                ancestors = self.find_move_ancestors(move)
                if move.state == 'waiting' and not ancestors:
                    # if the waiting move hasn't yet any ancestor
                    # (PO/MO not confirmed yet), don't find any quant
                    # available in stock
                    main_domain[move.id] += [('id', '=', False)]
                elif ancestors:
                    main_domain[move.id] += [('history_ids', 'in', ancestors)]

                # if the move is returned from another, restrict the choice
                # of quants to the ones that follow the returned move
                if move.origin_returned_move_id:
                    main_domain[move.id] += [('history_ids', 'in',
                                              move.origin_returned_move_id.id)]
                for link in move.linked_move_operation_ids:
                    operations.add(link.operation_id)
        # Check all ops and sort them: we want to process first the packages,
        # then operations with lot then the rest
        operations = list(operations)
        operations.sort(key=lambda x: ((x.package_id and not x.product_id) and
                                       -4 or 0) + (x.package_id and -2 or 0) +
                        (x.lot_id and -1 or 0))
        for ops in operations:
            # first try to find quants based on specific domains given by
            # linked operations
            for record in ops.linked_move_operation_ids:
                move = record.move_id
                if move.id in main_domain:
                    domain = main_domain[move.id] +\
                        op_link_obj.get_specific_domain(record)
                    qty = record.qty
                    if not qty:
                        continue
                    lot_id = move.restrict_lot_id.id
                    part_id = move.restrict_partner_id.id
                    quants = quant_obj.\
                        quants_get_prefered_domain(ops.location_id,
                                                   move.product_id, qty,
                                                   domain=domain,
                                                   prefered_domain_list=[],
                                                   restrict_lot_id=lot_id,
                                                   restrict_partner_id=part_id)
                    quant_obj.quants_reserve(quants, move, record)
        for move in todo_moves:
            if move.linked_move_operation_ids:
                continue
            # then if the move isn't totally assigned, try to find quants
            # without any specific domain
            if move.state != 'assigned':
                qty_already_assigned = move.reserved_availability
                qty = move.product_qty - qty_already_assigned
                lot_id = move.restrict_lot_id.id
                part_id = move.restrict_partner_id.id
                quants = quant_obj.\
                    quants_get_prefered_domain(move.location_id,
                                               move.product_id,
                                               qty,
                                               domain=main_domain[move.id],
                                               prefered_domain_list=[],
                                               restrict_lot_id=lot_id,
                                               restrict_partner_id=part_id)
                quant_obj.quants_reserve(quants, move)

        # force assignation of consumable products and incoming
        # from supplier/inventory/production
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
                # END OF stock_analytic_account
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
                lot_id = new_move.restrict_lot_id.id
                part_id = new_move.restrict_partner_id.id
                quants = quant_obj.\
                    quants_get_prefered_domain(new_move.location_id,
                                               new_move.product_id, quantity,
                                               domain=domain,
                                               prefered_domain_list=[],
                                               restrict_lot_id=lot_id,
                                               restrict_partner_id=part_id)
                quant_obj.quants_reserve(quants, new_move)
        self.action_done(res)
        return res


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account')

    @api.multi
    @api.constrains('location_id', 'product_id', 'prod_lot_id',
                    'analytic_account_id')
    def _check_inventory_line(self):
        """Refuse to record duplicate inventory lines
        Inventory lines with the sale Product, Location, Serial Number,
        Analytic Account and date are not taken into account correctly when
        computing the stock level difference, so we'll simply refuse to
        record them rather than allow users to introduce errors without
        even knowing it."""
        for line in self:
            # START OF stock_analytic_account
            inv_lines =\
                self.search([('product_id', '=', line.product_id.id),
                             ('location_id', '=', line.location_id.id),
                             ('prod_lot_id', '=', (line.prod_lot_id and
                                                   line.prod_lot_id.id
                                                   or False)),
                             ('inventory_id.date', '=',
                              line.inventory_id.date),
                             ('analytic_account_id', '=',
                              line.analytic_account_id.id),
                             ('id', 'not in', self._ids)])
            # END OF stock_analytic_account
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
                        # START OF stock_analytic_account
                        (line.analytic_account_id and
                         line.analytic_account_id.name or _('N/A')))
                        # END OF stock_analytic_account
                )

    @api.model
    def _resolve_inventory_line(self, inventory_line):
        stock_move_obj = self.env['stock.move']
        quant_obj = self.env['stock.quant']
        diff = inventory_line.theoretical_qty - inventory_line.product_qty
        if not diff:
            return
        # each theorical_lines where difference between theoretical and
        # checked quantities is not 0 is a line for which we need to
        # create a stock move
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
            # START OF stock_analytic_account
            'analytic_account_id': inventory_line.analytic_account_id.id,
            # END OF stock_analytic_account
        }
        inventory_location_id =\
            inventory_line.product_id.property_stock_inventory.id
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
        move = stock_move_obj.create(vals)
        if diff > 0:
            domain = [('qty', '>', 0.0),
                      ('package_id', '=', inventory_line.package_id.id),
                      ('lot_id', '=', inventory_line.prod_lot_id.id),
                      ('location_id', '=', inventory_line.location_id.id)]
            pref_domain = [[('reservation_id', '=', False)],
                           [('reservation_id.inventory_id', '!=',
                             inventory_line.inventory_id.id)]]
            quants = quant_obj.\
                quants_get_preferred_domain(move.product_qty, move,
                                            domain=domain,
                                            preferred_domain_list=pref_domain)
            quant_obj.quants_reserve(quants, move)
        elif inventory_line.package_id:
            move.action_done()
#            quants = [x.id for x in move.quant_ids]
            quants = move.quant_ids.ids
            quants.write({'package_id': inventory_line.package_id.id})
            location_dest_id = move.location_dest_id.id
            res = quant_obj.search([('qty', '<', 0.0),
                                    ('product_id', '=', move.product_id.id),
                                    ('location_id', '=', location_dest_id),
                                    ('package_id', '!=', False)], limit=1)
            if res.ids:
                for quant in move.quant_ids:
                    if quant.location_id.id == move.location_dest_id.id:
                        # To avoid we take a quant that was reconcile already
                        quant_obj._quant_reconcile_negative(quant, move)
        return move.id


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    @api.model
    def _inventory_line_hook(self, cr, uid, inventory_line, move_vals):
        """Override to pass analytic account to inventory."""
        # START OF stock_analytic_account
        if inventory_line.analytic_account_id:
            move_vals['analytic_account_id'] = \
                inventory_line.analytic_account_id.id
        # END OF stock_analytic_account
        return super(StockInventory, self)._inventory_line_hook(inventory_line,
                                                                move_vals)
