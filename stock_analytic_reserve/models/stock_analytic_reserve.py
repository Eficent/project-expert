# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError
from datetime import datetime

_STATES = [
    ('draft', 'Draft'),
    ('prepared', 'Prepared'),
    ('confirmed', 'Confirmed'),
    ('done', 'Completed'),
    ('cancel', 'Cancelled')]

_MOVE_STATES = [('draft', 'New'),
                ('cancel', 'Cancelled'),
                ('waiting', 'Waiting Another Move'),
                ('confirmed', 'Waiting Availability'),
                ('assigned', 'Available'),
                ('done', 'Done')]


class StockAnalyticReserve(models.Model):

    _name = 'stock.analytic.reserve'
    _description = 'Stock Analytic Reservation'

    @api.model
    def _get_default_warehouse(self):
        warehouse_obj = self.env['stock.warehouse']
        company_id = self.env['res.users'].browse(self._uid).company_id.id
        warehouse = warehouse_obj.search([('company_id', '=', company_id)])
        warehouse_id = warehouse.id and warehouse[0].id or False
        return warehouse_id

    name = fields.Char('Reference', required=True,
                       default=lambda obj: '/')

    action = fields.Selection([('reserve', 'Reserve'),
                               ('unreserve', 'Unreserve')],
                              string="Reservation Action", required=True,
                              states={'draft': [('readonly', False)]})

    state = fields.Selection(selection=_STATES, string='Status', readonly=True,
                             required=True, default='draft',
                             states={'draft': [('readonly', False)]})

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env['res.users'].
                                 browse(self._uid).company_id.id,)

    date = fields.Date('Date', default=fields.Date.context_today)

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse',
                                   required=True,
                                   default=_get_default_warehouse)

    wh_analytic_reserve_location_id = fields.\
        Many2one(related='warehouse_id.wh_analytic_reserve_location_id',
                 relation='stock.location',
                 string='Analytic Reservation Location', readonly=True)

    line_ids = fields.One2many('stock.analytic.reserve.line', 'reserve_id')

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].\
                get('stock.analytic.reserve') or '/'
        return super(StockAnalyticReserve, self).create(vals)

    @api.multi
    def action_prepare(self):
        for reserve in self:
            reserve.line_ids.prepare_stock_moves()
        self.write({'state': 'prepared'})
        return True

    @api.multi
    def action_confirm(self):
        for reserve in self:
            reserve.line_ids.confirm_stock_moves()
        self.write({'state': 'confirmed'})
        return True

    @api.multi
    def action_assign(self):
        for reserve in self:
            reserve.line_ids.assign_stock_moves()
        return True

    @api.multi
    def action_force_assign(self):
        for reserve in self:
            reserve.line_ids.force_assign_stock_moves()
        return True

    @api.multi
    def action_cancel(self):
        for reserve in self:
            reserve.line_ids.cancel_stock_moves()
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def action_draft(self):
        for reserve in self:
            reserve.line_ids.remove_stock_moves()
        self.write({'state': 'draft'})
        return True

    @api.multi
    def action_done(self):
        for reserve in self:
            reserve.line_ids.done_stock_moves()
        self.write({'state': 'done'})
        return True

    @api.one
    def copy_data(self, default=None):
        if default is None:
            default = {}
        default['name'] = '/'
        return super(StockAnalyticReserve, self).copy_data(default)


class StockAnalyticReserveLine(models.Model):

    _name = 'stock.analytic.reserve.line'
    _description = 'Stock Analytic Reservation Line'

    reserve_id = fields.Many2one('stock.analytic.reserve',
                                 'Stock Analytic Reservation',
                                 required=True,
                                 readonly=True,
                                 ondelete='cascade')

    product_id = fields.Many2one('product.product', 'Product', required=True,
                                 domain=[('type', '=', 'product')])

    product_uom_qty =\
        fields.\
            Float('Quantity',
                  digits_compute=dp.get_precision('Product Unit of Measure'),
                  required=True)

    product_uom_id = fields.Many2one('product.uom', 'Unit of Measure',
                                     required=True)

    location_id = fields.Many2one('stock.location', 'Stock Location',
                                  required=True)

    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account',
                                          required=True)

    company_id = fields.Many2one(related='reserve_id.company_id',
                                 relation='res.company',
                                 string='Company',
                                 store=True, readonly=True)

    out_move_id = fields.Many2one('stock.move', 'Out Stock Move',
                                  readonly=True)

    out_move_status = fields.Selection(related='out_move_id.state',
                                       selection=_MOVE_STATES,
                                       string='Out Move Status',
                                       readonly=True)

    in_move_id = fields.Many2one('stock.move', 'In Stock Move',
                                 readonly=True)

    @api.onchange('product_id')
    def onchange_product_id(self):
        """ Finds UoM for changed product.
        @param product_id: Changed id of product.
        @return: Dictionary of values.
        """
        if self.product_id:
            d = {'product_uom_id': [('category_id', '=',
                                     self.product_id.uom_id.category_id.id)]}
            self.product_uom_id = self.product_id.uom_id.id
            return {'domain': d}
        return {'domain': {'product_uom': []}}

    @api.multi
    def _prepare_basic_move(self):

        return {
            'name': self.product_id.name,
            'create_date': fields.datetime.now,
            'date': self.reserve_id.date,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_uom_qty,
            'product_uom': self.product_uom_id.id,
            'company_id': self.company_id.id
#            'picking_type_id': 'internal'
        }

    @api.multi
    def _prepare_out_move(self):
        self.ensure_one()
        res = self._prepare_basic_move()
        res['name'] = _('OUT:') + (self.reserve_id.name or '')
        res['location_id'] = self.location_id.id
        res['location_dest_id'] = \
            self.reserve_id.wh_analytic_reserve_location_id.id
        if self.reserve_id.action == 'unreserve':
            res['analytic_account_id'] = self.analytic_account_id.id
        else:
            res['analytic_account_id'] = False
        return res

    @api.multi
    def _prepare_in_move(self):
        self.ensure_one()
        res = self._prepare_basic_move()
        res['name'] = _('IN:') + (self.reserve_id.name or '')
        res['location_id'] = self.reserve_id.wh_analytic_reserve_location_id.id
        res['location_dest_id'] = self.location_id.id
        if self.reserve_id.action == 'reserve':
            res['analytic_account_id'] = self.analytic_account_id.id
        else:
            res['analytic_account_id'] = False
        return res

    @api.multi
    def prepare_stock_moves(self):
        move_obj = self.env['stock.move']
        for line in self:
            move_out_data = line._prepare_out_move()
            out_move = move_obj.create(move_out_data)
            line.write({'out_move_id': out_move.id})

            move_in_data = line._prepare_in_move()
            in_move = move_obj.create(move_in_data)
            line.write({'in_move_id': in_move.id})

        return True

    @api.multi
    def confirm_stock_moves(self):
        for line in self:
            if line.in_move_id.state == 'draft':
                line.in_move_id.action_confirm()
                line.in_move_id.action_assign()

            if line.out_move_id.state == 'draft':
                line.in_move_id.action_confirm()
                line.in_move_id.action_assign()
        return True

    @api.multi
    def assign_stock_moves(self):
        for line in self:
            if line.in_move_id.state not in ['draft', 'cancel', 'done']:
                line.in_move_id.action_assign()
            if line.out_move_id.state not in ['draft', 'cancel', 'done']:
                line.out_move_id.action_assign()
        return True

    @api.multi
    def force_assign_stock_moves(self):
        for line in self:
            if line.out_move_id.state not in ['draft', 'cancel', 'done']:
                line.out_move_id.force_assign()
        return True

    @api.multi
    def cancel_stock_moves(self):
        for line in self:
            line.in_move_id.action_cancel()
            line.out_move_id.action_cancel()
        return True

    @api.multi
    def done_stock_moves(self):
        for line in self:
            if line.out_move_id.state != 'assigned':
                raise UserError(_('All stock moves must be in'
                                  ' status Available'))
            line.in_move_id.action_done()
            line.out_move_id.action_done()
        return True

    @api.multi
    def remove_stock_moves(self):
        self.write({'out_move_id': False, 'in_move_id': False})
        return True

    @api.one
    def copy_data(self, default=None):
        if default is None:
            default = {}
        default['in_move_id'] = False
        default['out_move_id'] = False
        return super(StockAnalyticReserveLine, self).copy_data(default)
