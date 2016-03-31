# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Analytic Resource Planning - Purchase Requests",
    "version": "1.0",
    "author": "Eficent",
    "website": "www.eficent.com",
    "category": "Generic Modules/Projects & Services",
    "depends": ["analytic_resource_plan", "analytic_location",
                "purchase_request"],
    "description": """
Analytic Resource Planning - Purchase Requests
==============================================
Module features:
    - Create purchase requests from analytic resource planning lines

    """,
    "data": [
        "wizard/analytic_resource_plan_line_make_purchase_request.xml",
        "views/purchase_request_view.xml",
        "views/analytic_resource_plan_view.xml",
    ],
    'installable': True,
    'active': False,
}
