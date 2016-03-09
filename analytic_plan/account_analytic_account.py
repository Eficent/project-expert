# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import openerp.addons.decimal_precision as dp
from openerp import api, fields, models


class AccountAnalyticAccount(models.Model):

    _inherit = 'account.analytic.account'

    @api.multi
    def _get_active_analytic_planning_version(self):
        plan_versions = self.env['account.analytic.plan.version'].search([('default_plan', '=', True)])
        for plan_version in plan_versions:
            if plan_version:
                return plan_version
        return False

    @api.model
    def _compute_level_tree_plan(self, child_ids):
        currency_obj = self.env['res.currency']
        recres = {}

        @api.model
        def recursive_computation(self):
            result2 = account.copy()
            for son in account.child_ids:
                result = son.recursive_computation()
                for field in field_names:
                    if (account.currency_id.id != son.currency_id.id) \
                            and not account.quantity_plan:
                        result[field] = currency_obj.compute(son.currency_id.id,
                            account.currency_id.id, result[field])
                    result2[field] += result[field]
            return result2
        for account in self.browse(self._ids):
            if account.id not in child_ids:
                continue
            recres[account.id] = account.recursive_computation()
        return recres

    @api.model
    @api.depends('balance_plan', 'debit_plan', 'credit_plan', 'quantity_plan')
    def _debit_credit_bal_qtty_plan(self):
        res = {}
        child_ids = []
        child = self.search([('parent_id', 'child_of', self._ids)])
        for child_id in child:
            child_ids.append(child_id.id)
        child_ids = tuple(child_ids)
#        for i in child_ids:
#            res[i] = {}
#            for n in fields:
#                res[i][n] = 0.0
        if not child_ids:
            return res
#        for ac_id in child_ids:
#            res[ac_id] = {'debit_plan': 0,
#                          'credit_plan': 0,
#                          'balance_plan': 0,
#                          'quantity_plan': 0}
        child.write({'debit_plan': 0,
                      'credit_plan': 0,
                      'balance_plan': 0,
                      'quantity_plan': 0})
        where_date = ''
        where_clause_args = [child_ids]
        if self._context.get('from_date', False):
            where_date += " AND l.date >= %s"
            where_clause_args += [self._context['from_date']]
        if self._context.get('to_date', False):
            where_date += " AND l.date <= %s"
            where_clause_args += [self._context['to_date']]
        self._cr.execute("""
              SELECT a.id,
                     sum(
                         CASE WHEN l.amount > 0
                         THEN l.amount
                         ELSE 0.0
                         END
                          ) as debit_plan,
                     sum(
                         CASE WHEN l.amount < 0
                         THEN -l.amount
                         ELSE 0.0
                         END
                          ) as credit_plan,
                     COALESCE(SUM(l.amount),0) AS balance_plan,
                     COALESCE(SUM(l.unit_amount),0) AS quantity_plan
              FROM account_analytic_account a
                  LEFT JOIN account_analytic_line_plan l ON
                  (a.id = l.account_id)
              WHERE a.id IN %s
              AND a.active_analytic_planning_version = l.version_id
              """ + where_date + """
              GROUP BY a.id""", where_clause_args)
        for row in self._cr.dictfetchall():
            res[row['id']] = {}
            for field in fields:
                res[row['id']][field] = row[field]
        return self._compute_level_tree_plan(child_ids)

    balance_plan = fields.Float(
        compute='_debit_credit_bal_qtty_plan', method=True,
        string='Planned Balance', multi='debit_credit_bal_qtty_plan',
        digits_compute=dp.get_precision('Account'))
    debit_plan = fields.Float(
        compute='_debit_credit_bal_qtty_plan', method=True,
        string='Planned Debit', multi='debit_credit_bal_qtty_plan',
        digits_compute=dp.get_precision('Account'))
    credit_plan = fields.Float(
        compute='_debit_credit_bal_qtty_plan', method=True,
        string='Planned Credit', multi='debit_credit_bal_qtty_plan',
        digits_compute=dp.get_precision('Account'))
    quantity_plan = fields.Float(
        compute='_debit_credit_bal_qtty_plan', method=True,
        string='Quantity Debit', multi='debit_credit_bal_qtty_plan',
        digits_compute=dp.get_precision('Account'))
    plan_line_ids = fields.One2many('account.analytic.line.plan',
                                     'account_id',
                                     'Analytic Entries')
    active_analytic_planning_version = fields.\
        Many2one('account.analytic.plan.version', 'Active planning Version',
                 required=True, default=_get_active_analytic_planning_version)

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default['plan_line_ids'] = []
        return super(AccountAnalyticAccount, self).copy(default)

    @api.multi
    def action_openPlanCostTreeView(self):
        """
        :return dict: dictionary value for created view
        """
        account = self[0]
        res = self.env['ir.actions.act_window'].for_xml_id('analytic_plan',
            'action_account_analytic_plan_journal_open_form')
        plan_obj = self.env['account.analytic.line.plan']
        acc_ids = account.get_child_accounts()
        line = plan_obj.search([('account_id', 'in', acc_ids.keys()),
                      ('version_id', '=',
                       account.active_analytic_planning_version.id)])
        res['domain'] = "[('id', 'in', ["+','.join(
            map(str, line.ids))+"])]"
        res['nodestroy'] = False
        return res
