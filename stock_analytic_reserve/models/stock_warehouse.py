# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class StockWarehouse(models.Model):

    _inherit = 'stock.warehouse'

    wh_analytic_reserve_location_id =\
        fields.\
            Many2one('stock.location', 'Stock Analytic Reservation Location',
                     help="This is an inventory location that will be used "
                     "when making stock reservations for an analytic account."
                     " Should be different from the one used to report"
                     "inventory adjustments. If you use real-time inventory "
                     "valuation, please make sure that the GL accounts defined"
                     " in this location are the same for Debit and Credit, and"
                     " classified as Balance Sheet accounts.",
                     domain=[('usage', '=', 'inventory')])

    @api.one
    def copy_data(self, default=None):
        if default is None:
            default = {}
        default['wh_analytic_reserve_location_id'] = False
        return super(StockWarehouse, self).copy_data(default)
