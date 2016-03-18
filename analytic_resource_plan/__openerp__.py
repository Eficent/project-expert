# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Analytic Resource Planning",
    "version": "8.0.1.0.0.",
    "author": "Eficent Business and IT Consulting Services S.L., "
              "Serpent Consulting Services Pvt. Ltd.,"
              "Odoo Community Association (OCA)",
    "website": "www.eficent.com",
    "category": "Generic Modules/Projects & Services",
    "depends": ["account", "purchase", "analytic_plan"],
    "description": """
Analytic Resource Planning
====================================
    An effective planning of the resources required for a project or analytic account
    becomes essential in organizations that are run by projects, or profit center accounting.
    The process of resource planning generally follows an rolling wave planning approach, in which
    the level of detail of the planned resources increases over time, as the details of the work required
    are known to the planning group.

    Resources planned for a project/analytic account have an impact on the planned costs.
    If the resources are procured internally, the standard cost is determined.
    If the resources are procured externally, the user can indicate the supplier, and the planned costs
    are then determined on the basis of the supplier's price list.

    Multiple planning versions can be maintained for a resource plan, so that the organization can create
    a first rough-cut resource plan, that can then be refined as the project progresses.

    """,
    "data": [
        "view/account_analytic_line_plan_view.xml",
        "view/account_analytic_plan_version_view.xml",
        "view/analytic_resource_plan_view.xml",
        "view/analytic_account_view.xml",
        "view/product_view.xml",
        "view/project_view.xml",
        "wizard/analytic_resource_plan_copy_version_view.xml",
        "wizard/resource_plan_line_change_state_view.xml",
        "security/ir.model.access.csv",
    ],
    'installable': True,
    'active': False,
    'certificate': '',
}
