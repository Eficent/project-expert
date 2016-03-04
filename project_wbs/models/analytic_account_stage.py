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

_ANALYTIC_ACCOUNT_STATE = [('draft', 'New'),
                           ('open', 'In Progress'),
                           ('pending', 'To Renew'),
                           ('close', 'Closed'),
                           ('cancelled', 'Cancelled')]


class AnalyticAccountStage(models.Model):
    _name = 'analytic.account.stage'
    _description = 'Analytic Account Stage'
    _order = 'sequence'

    @api.model
    def _get_default_parent_id(self):
        analytic = self._context.get('default_parent_id')
        if isinstance(analytic, int):
            return [analytic]
        return analytic

    name = fields.Char('Name', required=True, translate=True)
    description = fields.Text('Description')
    sequence = fields.Integer('Sequence', default=1)
    analytic_account_ids = fields.Many2many('account.analytic.account',
                                            'analytic_account_stage_rel',
                                            'stage_id',
                                            'analytic_account_id',
                                            string='Project/Analytic stages',
                                            default=_get_default_parent_id)
    fold = fields.Boolean('Folded by Default', help="This stage is not "
                          "visible,  for example in status bar or kanban "
                          "view, when there are no records in that stage to "
                          "display.")
    case_default = fields.Boolean('Default for New Projects', default=False,
                                  help="If you check this field, this stage "
                                  "will be proposed by default on each new "
                                  "project. It will not assign this stage to "
                                  "existing projects.")
    project_state = fields.Selection([('open', 'In Progress'),
                                      ('cancelled', 'Cancelled'),
                                      ('pending', 'Pending'),
                                      ('close', 'Closed')],
                                     'Project Status', required=True)

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default['analytic_account_ids'] = []
        return super(AnalyticAccountStage, self).copy(default)
