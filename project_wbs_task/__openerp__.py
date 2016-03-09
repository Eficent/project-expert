# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


{
    "name": "Work Breakdown Structure - Tasks",
    "version": "8.0.2.0.0",
    "author": "Eficent Business and IT Consulting Services S.L., "
              "Serpent Consulting Services Pvt. Ltd.,"
              "Odoo Community Association (OCA)",
    "website": "www.eficent.com",
    "category": "Generic Modules/Projects & Services",
    "depends": ["project_wbs"],
    "description": """
Work Breakdown Structure - Tasks
================================
This module extends the standard Odoo functionality by adding:

- A button in the project tree view that will conduct the user to the list
view for the associated tasks.
- The possibility to search for task by the WBS complete reference or name.

    """,
    "data": [
        "view/project_task_view.xml",
        "view/project_view.xml",
    ],
    'installable': True,
    'active': False,
    'certificate': '',
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
