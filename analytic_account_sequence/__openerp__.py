# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


{
    "name": "Analytic account code sequence",
    "version": "8.0.1.0.0",
    "author": "Eficent Business and IT Consulting Services S.L., "
              "Serpent Consulting Services Pvt. Ltd.,"
              "Odoo Community Association (OCA)",
    "website": "www.eficent.com",
    "category": "Generic Modules/Projects & Services",
    "depends": ["project_wbs"],
    "description": """
    """,
    "data": [
        "views/analytic_account_sequence_view.xml",
        "data/analytic_account_sequence_data.xml",
        "views/account_analytic_account_view.xml",
        "security/ir.model.access.csv",
    ],
    'installable': True,
    'active': False,
    'certificate': '',
    'application': True,
}
