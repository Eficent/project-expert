# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models
from openerp.tools.translate import _


class analytic_resource_plan_copy_version(models.TransientModel):
    """
    For copying all the planned resources to a separate planning version
    """
    _name = "analytic.resource.plan.copy.version"
    _description = "Analytic Resource Plan copy versions"

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
        line_plan_obj = self.pool.get('analytic.resource.plan.line')
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
            'name': _('Resource Planning Lines'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'analytic.resource.plan.line',
            'view_id': False,
            'context': False,
            'type': 'ir.actions.act_window'
        }
