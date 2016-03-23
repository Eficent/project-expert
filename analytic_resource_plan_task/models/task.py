# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp.tools.translate import _
from openerp import api, fields, models
from datetime import datetime, date
from datetime import datetime as dt


class ProjectTask(models.Model):
    _inherit = "project.task"

    resource_plan_lines = fields.One2many('analytic.resource.plan.line',
                                          'task_id', "Planned resources")
    default_resource_plan_line = fields.Many2one('analytic.resource.plan.line',
                                                 'Default resource plan line',
                                                 required=False,
                                                 ondelete="cascade",
                                                 help='Resource plan line '
                                                 'associated to the employee'
                                                 'assigned to the task')

    @api.model
    def _prepare_resource_plan_line(self, plan_input):

        plan_output = {}
        project_obj = self.env['project.project']
        employee_obj = self.env['hr.employee']
#        product_obj = self.env['product.product']
        company_obj = self.env['res.company']
        product_price_type_obj = self.env['product.price.type']

        date_start = plan_input.get('date_start', False)
        date_end = plan_input.get('date_end', False)
        company_id = plan_input.get('company_id', False)
        user_id = plan_input.get('user_id', False)
        project_id = plan_input.get('project_id', False)
        planned_hours = plan_input.get('planned_hours', False)
        name = plan_input.get('name', False)

        plan_output['name'] = name

        plan_output['date'] = date.today()
        if date_start:
            dt_start = dt.strptime(date_start, "%Y-%m-%d %H:%M:%S")
            plan_output['date'] = dt_start.date()
        if date_end:
            dt_end = dt.strptime(date_end, "%Y-%m-%d %H:%M:%S")
            plan_output['date'] = dt_end.date()

        plan_output['unit_amount'] = planned_hours

        if project_id:
            project = project_obj.browse(project_id)
            if project.analytic_account_id:
                plan_output['account_id'] = project.analytic_account_id.id
                plan_output['version_id'] =\
                    project.analytic_account_id.active_analytic_planning_version and\
                    project.analytic_account_id.active_analytic_planning_version.id

        plan_output['company_id'] = company_id
        company = company_obj.browse(company_id)
        plan_output['currency_id'] = company.currency_id and\
            company.currency_id.id or False

        #Look for the employee that the user of the task is assigned to
        employees = employee_obj.search([('user_id', '=', user_id)])
        if employees:
            employee = employees[0]
        else:
            employee = False

        #Obtain the product associated to the employee
        if employee.product_id:
            plan_output['product_id'] = employee.product_id.id
            #Obtain the default uom of the product
            plan_output['product_uom_id'] = \
                employee.product_id.uom_id and \
                employee.product_id.uom_id.id or False

            prod = employee.product_id
            general_account_id =\
                prod.product_tmpl_id.property_account_expense.id
            if not general_account_id:
                general_account_id =\
                    prod.categ_id.property_account_expense_categ.id
            if not general_account_id:
                raise Warning(_('There is no expense account defined '
                                'for this product: "%s" (id:%d)')
                              % (prod.name, prod.id,))

            plan_output['general_account_id'] = general_account_id
            plan_output['journal_id'] = \
                prod.expense_analytic_plan_journal_id and \
                prod.expense_analytic_plan_journal_id.id or False

            product_price_type = product_price_type_obj.\
                search([('field', '=', 'standard_price')])
            pricetype = product_price_type[0]
            price_unit = prod.price_get(pricetype.field)[prod.id]
            prec = self.env['decimal.precision'].precision_get('Account')
            amount = price_unit * planned_hours or 1.0
            result = round(amount, prec)
            plan_output['price_unit'] = price_unit
            plan_output['amount_currency'] = -1 * result
            plan_output['amount'] = plan_output['amount_currency']

        return plan_output

    @api.model
    def create(self, vals):
        task = super(ProjectTask, self).create(vals)
        new_vals = {}
        resource_plan_line_obj = self.env['analytic.resource.plan.line']
        stage_obj = self.env['project.task.type']
        if 'stage_id' in vals:
            if vals['stage_id']:
                stage = stage_obj.browse(vals['stage_id'])
                state = stage.state
            else:
                state = False

            if not state and state != 'cancelled':
                if 'planned_hours' in vals and vals['planned_hours']:
                    if 'user_id' in vals and vals['user_id']:
                        if 'project_id' in vals and vals['project_id']:
                            if ('delegated_user_id' not in vals) or\
                            ('delegated_user_id' in vals and not
                             vals['delegated_user_id']):
                                plan_output = self.\
                                    _prepare_resource_plan_line(vals)
                                plan_output['task_id'] = task.id
                                new_plan_line = resource_plan_line_obj.\
                                    create(plan_output)

                                new_vals['default_resource_plan_line'] = \
                                    new_plan_line.id
                                task.write(new_vals)
        return task

    @api.multi
    def write(self, vals):
        resource_plan_line_obj = self.env['analytic.resource.plan.line']
        stage_obj = self.env['project.task.type']
        if 'stage_id' in vals \
                or 'planned_hours' in vals \
                or 'user_id' in vals \
                or 'delegated_user_id' in vals \
                or 'project_id' in vals \
                or 'default_resource_plan_line' in vals:

            for t in self:
                plan_input = {}

                if 'stage_id' in vals:
                    plan_input['stage_id'] = vals['stage_id']
                else:
                    plan_input['stage_id'] = t.stage_id

                if 'planned_hours' in vals:
                    plan_input['planned_hours'] = vals['planned_hours']
                else:
                    plan_input['planned_hours'] = t.planned_hours

                if 'user_id' in vals:
                    plan_input['user_id'] = vals['user_id']
                else:
                    plan_input['user_id'] = t.user_id and t.user_id.id or False

                if 'delegated_user_id' in vals:
                    plan_input['delegated_user_id'] = vals['delegated_user_id']
                else:
                    plan_input['delegated_user_id'] = t.delegated_user_id and\
                        t.delegated_user_id.id or False

                if 'name' in vals:
                    plan_input['name'] = vals['name']
                else:
                    plan_input['name'] = t.name

                if 'date_start' in vals:
                    plan_input['date_start'] = vals['date_start']
                elif t.date_start:
                    plan_input['date_start'] = t.date_start

                if 'date_end' in vals:
                    plan_input['date_end'] = vals['date_end']
                elif t.date_end:
                    plan_input['date_end'] = t.date_end

                if 'project_id' in vals:
                    plan_input['project_id'] = vals['project_id']
                else:
                    plan_input['project_id'] = t.project_id and\
                        t.project_id.id or False

                if 'company_id' in vals:
                    plan_input['company_id'] = vals['company_id']
                else:
                    plan_input['company_id'] = t.company_id and\
                        t.company_id.id or False

                if 'default_resource_plan_line' in vals:
                    plan_input['default_resource_plan_line'] = \
                        vals['default_resource_plan_line']
                else:
                    plan_input['default_resource_plan_line'] = \
                        t.default_resource_plan_line and\
                        t.default_resource_plan_line.id or False

                stage = stage_obj.browse(plan_input['stage_id'])
                state = stage.state

                if state != 'cancelled' \
                        and plan_input['planned_hours'] > 0.0 \
                        and plan_input['user_id'] \
                        and not plan_input['delegated_user_id'] \
                        and plan_input['project_id']:
                    #Add or update the resource plan line
                    plan_output = self._prepare_resource_plan_line(plan_input)
                    plan_output['task_id'] = t.id
                    if plan_input['default_resource_plan_line']:

                        res = super(ProjectTask, self).write(vals)
                        default_resource_plan_line = resource_plan_line_obj.\
                            browse([plan_input['default_resource_plan_line']])
                        default_resource_plan_line.write(plan_output)
                        return res

                    else:
                        new_resource_plan_line = resource_plan_line_obj.\
                            create(plan_output)
                        vals['default_resource_plan_line'] = \
                            new_resource_plan_line.id
                        return super(ProjectTask, self).write(vals)

                else:
                    #Remove the resource plan line
                    if t.default_resource_plan_line:
                        t.default_resource_plan_line.unlink()

        return super(ProjectTask, self).write(vals)

    @api.model
    def map_resource_plan_lines(self, new_task):
        """ copy and map tasks from old to new project """
        map_resource_plan_line_id = []
        default = {}

        default['account_id'] = \
            new_task.project_id and \
            new_task.project_id.analytic_account_id and \
            new_task.project_id.analytic_account_id.id or False

        default['task_id'] = new_task.id
        task_vals = {}
        for resource_plan_line in self.resource_plan_lines:
            new_resource_plan_line = resource_plan_line.copy(default)
            if new_resource_plan_line:
                map_resource_plan_line_id.append(new_resource_plan_line.id)

            default_resource_plan_line = \
                self.default_resource_plan_line \
                and self.default_resource_plan_line.id \
                or False
            if resource_plan_line.id == default_resource_plan_line:
                task_vals['default_resource_plan_line'] = \
                    new_resource_plan_line.id
        if map_resource_plan_line_id:
            task_vals['resource_plan_lines'] = [(6, 0,
                                                 map_resource_plan_line_id)]

        if task_vals:
            new_task.write(task_vals)

        return True

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}

        default['default_resource_plan_line'] = False
        default['resource_plan_lines'] = []
        res = super(ProjectTask, self).copy(default)
        self.map_resource_plan_lines(res)
        return res
