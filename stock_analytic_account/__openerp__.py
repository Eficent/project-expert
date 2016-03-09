# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Analytic Account",
    "version": "8.0.1.0.0",
    "author": "Eficent Business and IT Consulting Services S.L., "
              "Serpent Consulting Services Pvt. Ltd.,"
              "Odoo Community Association (OCA)",
    "website": "www.eficent.com",
    'summary': 'Adds the analytic account to stock moves',
    "depends": ["stock", "analytic"],
    "description": """
Project Procurement
===================
Features of this module:
    - Adds the analytic account to the stock move
    - Makes it possible to search stock moves by analytic account or its
        project manager
    - Makes it possible to search picking lists by analytic account or its
        project manager
    - Adds button in the Project Form and an Action from Project's 'More' menu
        to list the
    Procurement Orders associated to the selected project.
    """,
    'data': [
        'view/stock_view.xml',
        'view/stock_picking_view.xml',
        'view/analytic_account_view.xml',
        'report/report_stock_analytic_account_view.xml',
#        'report/report_stock_move_view.xml',
        'wizard/stock_change_product_qty_view.xml',
#        'wizard/stock_fill_inventory_view.xml',
    ],
    'test': [
        'test/stock_users.yml',
        'demo/stock_demo.yml',
        'test/opening_stock.yml',
        'test/shipment.yml',
        'test/stock_report.yml',
        'test/setlast_tracking.yml',
    ],
    'installable': True,
}
