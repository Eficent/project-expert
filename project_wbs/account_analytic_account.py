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
from openerp.tools import misc


class AccountAnalyticAccount(models.Model):

    _inherit = 'account.analytic.account'

    @api.depends('complete_wbs_code', 'code', 'name', 'parent_id')
    def _complete_wbs_code_calc(self):
        if not self._ids:
            return []
        res = []
        for account in self:
            data = []
            acc = account
            while acc:
                if acc.code:
                    data.insert(0, acc.code)
                else:
                    data.insert(0, '')
                acc = acc.parent_id
            data = ' / '.join(data)
            data = '[' + data + '] '
            res.append((account.id, data))
        return dict(res)

    @api.depends('complete_wbs_name', 'code', 'name', 'parent_id')
    def _complete_wbs_name_calc(self):
        if not self._ids:
            return []
        res = []
        for account in self:
            data = []
            acc = account
            while acc:
                if acc.name:
                    data.insert(0, acc.name)
                else:
                    data.insert(0, '')
                acc = acc.parent_id
            data = ' / '.join(data)
            res.append((account.id, data))
        return dict(res)

    @api.depends('parent_id', 'name')
    def _wbs_indent_calc(self):
        if not self._ids:
            return []
        res = []
        for account in self:
            data = []
            acc = account
            while acc:
                if acc.name and acc.parent_id.parent_id:
                    data.insert(0, '>')
                else:
                    data.insert(0, '')

                acc = acc.parent_id
            data = ''.join(data)
            res.append((account.id, data))
        return dict(res)

    @api.multi
    def _child_count(self, account_class, arg):
        res = dict.fromkeys(self._ids, 0)
        ctx = self._context.copy()
        ctx['active_test'] = False
        for analytic_account in self:
            deliverable = self.env['account.analytic.account'].\
                with_context(ctx).search([('parent_id', '=',
                                           analytic_account.id),
                          ('account_class', '=', account_class)])
            if deliverable:
                res[analytic_account.id] = len(deliverable.ids)
            else:
                res[analytic_account.id] = 0
        return res

    @api.depends('child_project_count')
    def _child_project_count(self):
        for account in self:
            account.child_project_count = account._child_count('project',
                                                               self._arg)

    @api.depends('child_phase_count')
    def _child_phase_count(self):
        for account in self:
            account.child_phase_count = account._child_count('phase',
                                                             self._arg)

    @api.depends('child_deliverable_count')
    def _child_deliverable_count(self):
        for account in self:
            account.child_deliverable_count = account.\
                _child_count('deliverable', self._arg)

    @api.depends('child_work_package_count')
    def _child_work_package_count(self):
        for account in self:
            account.child_work_package_count = account.\
                _child_count('work_package', self._arg)

    @api.depends('child_unclassified_count')
    def _child_unclassified_count(self):
        for account in self:
            account.child_unclassified_count = account._child_count('',
                                                                    self._arg)

    @api.model
    def _resolve_analytic_account_id_from_context(self):
        """ Returns ID of parent analytic account based on the value of
        'default_parent_id'
            context key, or None if it cannot be resolved to a single
            account.analytic.account
        """
        if type(self._context.get('default_parent_id')) in (int, long):
            return self._context['default_parent_id']
        if isinstance(self._context.get('default_parent_id'), basestring):
            analytic_account_name = self._context['default_parent_id']
            analytic_account_ids = \
                self.env['account.analytic.account'].\
                    name_search(name=analytic_account_name)
            if len(analytic_account_ids) == 1:
                return analytic_account_ids[0][0]
        return None

    @api.depends('project_analytic_account_id', 'account_class', 'parent_id')
    def _get_project_account_id(self):
        if not self._ids:
            return []
        res = dict.fromkeys(self._ids, False)
        for account in self:
            acc = account
            while acc:
                if acc.account_class == 'project':
                    res[account.id] = acc.id
                    break
                acc = acc.parent_id
        return res

    @api.multi
    def _read_group_stage_ids(self, domain, read_group_order=None,
                              access_rights_uid=None):
        stage_obj = self.env['analytic.account.stage']
        order = stage_obj._order
        access_rights_uid = access_rights_uid or self._uid
        if read_group_order == 'stage_id desc':
            order = '%s desc' % order
        search_domain = []
        analytic_account_id = self._resolve_analytic_account_id_from_context()
        if analytic_account_id:
            search_domain += ['|', ('analytic_account_ids', '=',
                                    analytic_account_id)]
        search_domain += [('id', 'in', self._ids)]
        stage_ids = stage_obj._search(search_domain, order=order,
                                      access_rights_uid=access_rights_uid)
        stages = stage_obj.sudo(access_rights_uid).browse(stage_ids)
        result = stages.sudo(access_rights_uid).name_get()
        # restore order of the search
        result.sort(lambda x, y: cmp(stage_ids.index(x[0]),
                                     stage_ids.index(y[0])))

        fold = {}
        for stage in stage_obj.sudo(access_rights_uid).browse(stage_ids):
            fold[stage.id] = stage.fold or False
        return result, fold

    wbs_indent = fields.Char(compute='_wbs_indent_calc', string='Level',
                             readonly=True, store=True)
    complete_wbs_code = fields.Char(compute='_complete_wbs_code_calc',
                                    string='Full WBS Code',
        help='The full WBS code describes the full path of this component '
             'within the project WBS hierarchy', store=True)
#        store={'account.analytic.account': (get_child_accounts)})
    complete_wbs_name = fields.Char(compute='_complete_wbs_name_calc',
                                    string='Full WBS path',
        help='Full path in the WBS hierarchy', store=True)
#        store={'account.analytic.account': (get_child_accounts)})
    project_analytic_account_id = fields.Many2one('account.analytic.account',
        compute='_get_project_account_id',
        string='Root Project',
        help='Root Project in the WBS hierarchy', store=True)
#        store={'account.analytic.account': (get_child_accounts)})
    account_class = fields.Selection([('project', 'Project'),
                                      ('phase', 'Phase'),
                                      ('deliverable', 'Deliverable'),
                                      ('work_package', 'Work Package')],
                                     'Class',
        help='The classification allows you to create a proper project '
             'Work Breakdown Structure')
    stage_id = fields.Many2one('analytic.account.stage', 'Stage',
        domain="['&', ('fold', '=', False), "
               "('analytic_account_ids', '=', parent_id)]")
    child_stage_ids = fields.Many2many(
        'analytic.account.stage', 'analytic_account_stage_rel',
        'analytic_account_id', 'stage_id', 'Child Stages', states={
            'close': [('readonly', True)], 'cancelled': [('readonly',
                                                          True)]})
    child_project_count = fields.Integer(compute='_child_project_count',
                                         "Projects", store=True)
    child_phase_count = fields.Integer(compute='_child_phase_count',
                                       "Phases", store=True)
    child_deliverable_count = fields.\
        Integer(compute='_child_deliverable_count', "Deliverables", store=True)
    child_work_package_count = fields.\
        Integer(compute='_child_work_package_count', "Work Packages",
                store=True)
    child_unclassified_count = fields.\
        Integer(compute='_child_unclassified_count', "Unclassified projects",
                store=True)

    @api.model
    def _get_type_common(self):
        stage = self.env['analytic.account.stage'].search([('case_default',
                                                            '=', 1)])
        return stage

    _group_by_full = {
        'stage_id': _read_group_stage_ids,
    }

    _defaults = {
        'child_stage_ids': _get_type_common,
    }

    _order = 'complete_wbs_code'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        args = args[:]
        accountbycode = self.search([('complete_wbs_code',
                                      'ilike', '%%%s%%' % name)] + args,
                                    limit=limit)
        accountbyname = self.search([('complete_wbs_name', 'ilike',
                                      '%%%s%%' % name)] + args, limit=limit)
        account = accountbycode + accountbyname
        return account.name_get()

    @api.multi
    @api.depends('code', 'parent_id')
    def code_get(self):
        if not self._ids:
            return []
        res = []
        for account in self:
            data = []
            acc = account
            while acc:
                if acc.code:
                    data.insert(0, acc.code)
                else:
                    data.insert(0, '')
                acc = acc.parent_id
            data = ' / '.join(data)
            res.append((account.id, data))
        return res

    @api.multi
    @api.depends('name', 'parent_id')
    def name_get(self):
        if not self._ids:
            return []
        if isinstance(self._ids, int):
            ids = [self._ids]
        else:
            ids = self._ids
        new_list = []
        for i in ids:
            if i not in new_list:
                new_list.append(i)
        ids = new_list
        res = []
        for account in self:
            data = []
            acc = account
            while acc:
                if acc.name:
                    data.insert(0, acc.name)
                else:
                    data.insert(0, '')
                acc = acc.parent_id
            data = ' / '.join(data)
            res2 = account.code_get()
            if res2:
                data = '[' + res2[0][1] + '] ' + data
            res.append((account.id, data))
        return res

    @api.multi
    def write(self, values):
        # Find the previous stage
        old_stage_id = {}
        old_state_id = {}
        for acc in self:
            old_stage_id[acc.id] = acc.stage_id or False
            old_state_id[acc.id] = acc.state
        res = super(AccountAnalyticAccount, self).write(values)
        if values.get('stage_id'):
            project_obj = self.env['project.project']
            stage_obj = self.env['analytic.account.stage']
            for acc in self:
                # Search if there's an associated project
                project = project_obj.search([('analytic_account_id', '=',
                                               acc.id)])
                if old_stage_id[acc.id]:
                    old_stage = acc.stage_id
                else:
                    old_stage = False
                new_stage = stage_obj.browse(values.get('stage_id'))
                cr, uid, context = self.env.args
                context = dict(context)
                context.update({
                    'stage_updated': True
                })
                # If the new stage is found in the child accounts, then set
                # it as well (only if the new stage sequence is greater than
                #  the current)
                if new_stage.id in [st.id for st in acc.child_stage_ids]:
                    child = self.search([('parent_id', '=', acc.id)])
                    if child.stage_id.sequence < new_stage.sequence:
                        child.with_context(context).\
                            write({'stage_id': new_stage.id})
                        self.env.args = cr, uid, misc.frozendict(context)
                if old_stage and old_stage.project_state == \
                        new_stage.project_state:
                    continue
                if new_stage.project_state == 'close':
                    project.set_done()
                elif new_stage.project_state == 'cancelled':
                    project.set_cancel()
                elif new_stage.project_state == 'pending':
                    project.set_pending()
                elif new_stage.project_state == 'open':
                    project.set_open()
        return res
