# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import openerp.addons.decimal_precision as dp
from openerp import api, fields, models


class AccountAnalyticAccount(models.Model):

    _inherit = 'account.analytic.account'

    @api.model
    def default_get(self, fields):
        res = super(AccountAnalyticAccount, self).default_get(fields)
        plan_versions = self.env['account.analytic.plan.version'].\
            search([('default_plan', '=', True)])
        for plan_version in plan_versions:
            if plan_version:
                res['active_analytic_planning_version'] = plan_version.id
                return res
        return res

    @api.multi
    def _compute_level_tree_plan(self, child_ids, res):
        recres = {}
        field_names = ['debit_plan', 'credit_plan', 'balance_plan',
                       'quantity_plan']

        def recursive_computation(account):
            result2 = res[account.id].copy()
            for son in account.child_ids:
                result = recursive_computation(son)
                for field in field_names:
                    if (account.currency_id.id != son.currency_id.id) \
                            and (field != 'quantity_plan'):
                        son.currency_id.compute(result[field],
                                                account.currency_id)
                    result2[field] += result[field]
            return result2
        for account in self:
            if account.id not in child_ids:
                continue
            recres[account.id] = recursive_computation(account)
        return recres

    @api.depends('balance_plan', 'debit_plan', 'credit_plan', 'quantity_plan')
    def _debit_credit_bal_qtty_plan(self):
        res = {}
        fields = ['debit_plan', 'credit_plan', 'balance_plan', 'quantity_plan']
        childs = self.search([('parent_id', 'child_of', self.ids)])
        child_ids = tuple(childs.ids)
        for i in child_ids:
            res[i] = {}
            for n in fields:
                res[i][n] = 0.0
        if not child_ids:
            return res
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
        rec = self._cr.dictfetchall()
        for row in rec:
            child_rec = self.browse(row['id'])
            child_rec.debit_plan = row['debit_plan']
            child_rec.credit_plan = row['credit_plan']
            child_rec.balance_plan = row['balance_plan']
            child_rec.quantity_plan = row['quantity_plan']
        return self._compute_level_tree_plan(child_ids, res)

    balance_plan = fields.Float(compute='_debit_credit_bal_qtty_plan',
                                string='Planned Balance',
                                digits_compute=dp.get_precision('Account'),
                                store=False)
    debit_plan = fields.Float(compute='_debit_credit_bal_qtty_plan',
                              string='Planned Debit',
                              digits_compute=dp.get_precision('Account'),
                              store=False)
    credit_plan = fields.Float(compute='_debit_credit_bal_qtty_plan',
                               string='Planned Credit',
                               digits_compute=dp.get_precision('Account'),
                               store=False)
    quantity_plan = fields.Float(compute='_debit_credit_bal_qtty_plan',
                                 string='Quantity Debit',
                                 digits_compute=dp.get_precision('Account'),
                                 store=False)
    plan_line_ids = fields.One2many('account.analytic.line.plan',
                                    'account_id',
                                    'Analytic Entries')
    active_analytic_planning_version = fields.\
        Many2one('account.analytic.plan.version', 'Active planning Version',
                 required=True)

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
        res = self.env['ir.actions.act_window'].\
            for_xml_id('analytic_plan',
                       'action_account_analytic_plan_journal_open_form')
        plan_obj = self.env['account.analytic.line.plan']
        acc_ids = account.get_child_accounts()
        line = plan_obj.search([('account_id', 'in', acc_ids.keys()),
                                ('version_id', '=',
                                 account.active_analytic_planning_version.id)])
        res['domain'] = "[('id', 'in', [" + ','.join(
            map(str, line.ids)) + "])]"
        res['nodestroy'] = False
        return res
