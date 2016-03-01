# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Eficent (<http://www.eficent.com/>)
#               <contact@eficent.com>
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


class task(models.Model):
    _inherit = 'project.task'

    @api.multi
    def _project_complete_wbs_name(self):
        if not self._ids:
            return []
        res = []
        data_project = []
        for task in self:
            if task.project_id:
                data_project = task.project_id.complete_wbs_name
            if data_project:
                res.append((task.id, data_project))
            else:
                res.append((task.id, ''))
        return dict(res)

    @api.multi
    def _project_complete_wbs_code(self):
        if not self._ids:
            return []
        res = []
        data_project = []
        for task in self:
            if task.project_id:
                data_project = task.project_id.complete_wbs_code
            if data_project:
                res.append((task.id, data_project))
            else:
                res.append((task.id, ''))
        return dict(res)

    analytic_account_id = fields.\
        Many2one(related='project_id.analytic_account_id',
                 relation='account.analytic.account',
                 string='Analytic Account', store=True, readonly=True)
    project_complete_wbs_code = fields.\
        Char('Full WBS Code', related='analytic_account_id.complete_wbs_code',
             readonly=True)
    project_complete_wbs_name = fields.\
        Char('Full WBS Name', related='analytic_account_id.complete_wbs_name',
             readonly=True)
