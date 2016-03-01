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


class project(models.Model):
    _inherit = "project.project"

    @api.multi
    def action_openTasksTreeView(self):
        """
        :return dict: dictionary value for created view
        """
        project = self[0]
        task = self.env['project.task'].search([('project_id', '=', project.id)])
        res = self.env['ir.actions.act_window'].for_xml_id('project_wbs_task', 'action_task_tree_view')
        res['context'] = {
            'default_project_id': project.id,
        }
        res['domain'] = "[('id', 'in', ["+','.join(
            map(str, task.ids))+"])]"
        res['nodestroy'] = False
        return res