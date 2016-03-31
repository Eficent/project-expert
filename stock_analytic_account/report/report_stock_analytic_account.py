# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import tools
from openerp import api, exceptions, fields, models, _


class StockReportAnalyticAccount(models.Model):
    _name = "stock.report.analytic.account"
    _description = "Stock report by Analytic Account"
    _auto = False
    qty = fields.Float('Quantity in ref UoM', help="Quantity expressed in the "
                       "reference UoM", readonly=True)
    location_id = fields.Many2one('stock.location', 'Location', readonly=True,
                                  select=True)
    usage = fields.Selection([('supplier', 'Supplier Location'),
                              ('view', 'View'),
                              ('internal', 'Internal Location'),
                              ('customer', 'Customer Location'),
                              ('inventory', 'Inventory'),
                              ('procurement', 'Procurement'),
                              ('production', 'Production'),
                              ('transit', 'Transit Location for '
                               'Inter-Companies Transfers')],
                             'Location Type', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True,
                                 select=True)
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account', readonly=True,
                                          select=True)
    analytic_reserved = fields.Boolean('Stock reserved for the '
                                       'Analytic Account', readonly=True,
                                       select=True)

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
                %s
                %s
                %s
                %s
        )""" % (self._table, self._select(), self._from(), self._where(),
                self._group_by()))

    def _select(self):
        return """SELECT MAX(id) AS id,
                    location_id,
                    usage,
                    product_id,
                    analytic_account_id,
                    analytic_reserved,
                    SUM(qty) AS qty"""

    def _from(self):
        return """FROM (
                SELECT -MAX(sm.id) AS id,
                    sm.location_id,
                    sl.usage,
                    sm.product_id,
                    sm.analytic_account_id,
                    sm.analytic_reserved,
                    -SUM(sm.product_qty /uo.factor) AS qty
                FROM stock_move AS sm
                    LEFT JOIN stock_location sl ON (sl.id = sm.location_id)
                    LEFT JOIN product_uom uo ON (uo.id=sm.product_uom)
                WHERE state = 'done'
                GROUP BY sm.location_id, sl.usage, sm.product_id,
                sm.product_uom,
                sm.analytic_account_id,
                sm.analytic_reserved
            UNION ALL
                SELECT MAX(sm.id) AS id,
                    sm.location_dest_id AS location_id,
                    sl.usage,
                    sm.product_id,
                    sm.analytic_account_id,
                    sm.analytic_reserved,
                    SUM(sm.product_qty /uo.factor) AS qty
                FROM stock_move AS sm
                LEFT JOIN stock_location sl ON (sl.id = sm.location_dest_id)
                LEFT JOIN product_uom uo ON (uo.id=sm.product_uom)
                WHERE sm.state = 'done'
                GROUP BY sm.location_dest_id, sl.usage, sm.product_id,
                    sm.product_uom, sm.analytic_account_id,
                    sm.analytic_reserved
            ) AS report"""

    def _where(self):
        return """ """

    def _group_by(self):
        return """GROUP BY location_id, usage, product_id,
                analytic_account_id, analytic_reserved"""

    @api.multi
    def unlink(self):
        raise exceptions.except_orm(_('Error!'),
                                    _('You cannot delete any record!'))
