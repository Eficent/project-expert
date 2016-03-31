# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models
from openerp import netsvc


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    @api.model
    def _compute_scheduled_dates(self):
        # Obtain the earliest and latest dates of the children
        start_dates = []
        end_dates = []
        if not self.child_ids:
            return True
        for child in self.child_ids:
            if child.date_start:
                start_dates.append(child.date_start)
            if child.date:
                end_dates.append(child.date)
        min_start_date = False
        max_end_date = False
        if start_dates:
            min_start_date = min(start_dates)
        if end_dates:
            max_end_date = max(end_dates)
        vals = {
            'date_start': min_start_date,
            'date': max_end_date,
        }
        self.write(vals)
        return True

    @api.model
    def create(self, values):
        acc = super(AccountAnalyticAccount, self).create(values)
        acc.parent_id._compute_scheduled_dates()
        return acc

    @api.multi
    def write(self, vals):
        res = super(AccountAnalyticAccount, self).write(vals)
        if 'date_start' in vals or 'date' in vals:
            for acc in self:
                if not acc.parent_id:
                    return res
                acc.parent_id._compute_scheduled_dates()
        return res
