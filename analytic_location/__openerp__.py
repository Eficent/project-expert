# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Location in Analytic Account",
    "version": "1.0",
    "author": "Eficent",
    "website": "www.eficent.com",
    "category": "Generic Modules/Projects & Services",
    "depends": ["analytic", "stock", "stock_analytic_account"],
    "description": """
Stock Location in Analytic Account
==================================
Features of this module:
    - Adds the stock location in the analytic account.

    """,
    "data": [
        "view/analytic_account_view.xml",
    ],
    'installable': True,
    'active': False,
    'application': True,
}
