# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Eficent (<http://www.eficent.com/>)
#              <contact@eficent.com>
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
from openerp.tools.translate import _
import time


class analytic_plan_copy_version(models.TransientModel):
    """
    For copying all the planned costs to a separate planning version
    """
    _name = "analytic.plan.copy.version"
    _description = "Analytic Plan copy versions"

    source_version_id = fields.Many2one('account.analytic.plan.version',
                                         'Source Planning Version',
                                         required=True)
    dest_version_id = fields.Many2one('account.analytic.plan.version',
                                       'Destination Planning Version',
                                       required=True)
    include_child = fields.Boolean('Include child accounts',
                                    required=True)

    _defaults = {
        'include_child': True,
    }

    @api.multi
    def analytic_plan_copy_version_open_window(self):
        new_line_plan_ids = []
        analytic_obj = self.pool.get('account.analytic.account')
        line_plan_obj = self.pool.get('account.analytic.line.plan')
#        plan_version_obj = self.pool.get('account.analytic.plan.version')

        data = self[0]
        record_ids = self._context and self._context.get('active_ids', False)
        include_child = data.include_child or False
        source_version = data.source_version_id or False
        dest_version = data.dest_version_id or False
        if dest_version.default_plan:
            raise Warning(_('It is prohibited to copy '
                                   'to the default planning version.'))

        if source_version == dest_version:
            raise Warning(_('Choose different source and destination '
                                   'planning versions.'))
        if include_child:
            account_ids = analytic_obj.get_child_accounts(record_ids).keys()
        else:
            account_ids = record_ids

        line_plan = line_plan_obj.search([('account_id', 'in', account_ids),
                      ('version_id', '=', source_version.id)])

        for line_plan_id in line_plan:
            new_line_plan_id = line_plan_id.copy()
            new_line_plan_ids.append(new_line_plan_id)

        new_line_plan_ids.write({'version_id': dest_version[0]})

        return {
            'domain': "[('id','in', ["+','.join(map(str, new_line_plan_ids))+"])]",
            'name': _('Analytic Planning Lines'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.analytic.line.plan',
            'view_id': False,
            'context': False,
            'type': 'ir.actions.act_window'
        }
