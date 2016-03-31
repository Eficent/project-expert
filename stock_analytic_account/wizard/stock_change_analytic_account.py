# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import tools


class StockChangeAnalyticAccount(orm.TransientModel):
    _inherit = "stock.change.analytic.account"

    _columns = {
        'src_analytic_account_id': fields.many2one(
            'account.analytic.account', 'Source Analytic Account'),
        'dest_analytic_account_id': fields.many2one(
            'account.analytic.account', 'Source Analytic Account'),
        'location_id': fields.many2one(
            'stock.location', 'Source Location', readonly=True, required=True),
        'location_dest_id': fields.many2one(
                'stock.location', 'Destination Location', readonly=True,
                required=True),
        'quantity': fields.float('Quantity'),
    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(StockChangeAnalyticAccount,
                    self).default_get(cr, uid, fields, context=context)
        product_obj = self.pool['product.product']
        product_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not product_ids:
            return res
        assert active_model == 'product.product', \
            'Bad context propagation'

        items = []
        for line in product_obj.browse(cr, uid, request_line_ids,
                                       context=context):
                items += self._prepare_item(cr, uid, line, context=context)
        res['item_ids'] = items

        return res
