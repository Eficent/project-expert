# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp.tools.translate import _
from openerp import api, fields, models
from datetime import datetime, date
from datetime import datetime as dt


class Project(models.Model):
    _inherit = "project.project"

    @api.multi
    def write(self, vals):
        task_obj = self.env['project.task']
        if 'tasks' in vals:
            if vals['tasks'] and vals['tasks'][0] and vals['tasks'][0][2]:
                resource_vals = {}
                for p in self:
                    for task_id in vals['tasks'][0][2]:
                        task = task_obj.browse(task_id)
                        for resource_plan_line in task.resource_plan_lines:
                            resource_vals['account_id'] = \
                                p.analytic_account_id and \
                                p.analytic_account_id.id or False
                            resource_plan_line.write(resource_vals)
        return super(Project, self).write(vals)
