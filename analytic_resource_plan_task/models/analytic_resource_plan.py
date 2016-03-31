# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError


class AnalyticResourcePlanLine(models.Model):

    _inherit = 'analytic.resource.plan.line'

    task_id = fields.Many2one('project.task', 'Task', required=False,
                              ondelete='cascade', readonly=False,
                              states={'confirm': [('readonly', True)]})

    @api.onchange('task_id')
    def on_change_task_id_resource(self):
        res = {}
        res['value'] = {}
        #Change in task_id affects:
        #  - account_id

        if self.task_id:
            task = self.task_id
            account_id = task.project_id and task.project_id.analytic_account_id and task.project_id.analytic_account_id.id or False
            if account_id:
                self.account_id = account_id
#                res_account_id = self._on_change_account_id_resource()
#                if res_account_id:
#                    res['value'].update(res_account_id)
#
#        if res['value']:
#            return res
#        else:
            return {}

    @api.model
    def create(self, vals):
        task_obj = self.env['project.task']
        if 'task_id' in vals and vals['task_id']:
            task = task_obj.browse(vals['task_id'])
            vals['account_id'] = \
                task.project_id \
                and task.project_id.analytic_account_id \
                and task.project_id.analytic_account_id.id \
                or False
        return super(AnalyticResourcePlanLine, self).create(vals)

    @api.multi
    def write(self, vals):
        for p in self:
            if 'task_id' in vals:
                task_id = vals['task_id']
            else:
                task_id = p.task_id and p.task_id.id or False
            if task_id:
                task_obj = self.env['project.task']
                task = task_obj.browse(task_id)
                if 'unit_amount' in vals:
                    if task.default_resource_plan_line and task.default_resource_plan_line.id == p.id:
                        if task.planned_hours != vals['unit_amount']:
                            raise UserError(_('The quantity is different to the number of planned hours '
                                            'in the associated task.'))
        return super(AnalyticResourcePlanLine, self).write(vals)
