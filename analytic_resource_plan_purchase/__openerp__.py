# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Analytic Resource Planning - Purchase Orders",
    "version": "1.0",
    "author": "Eficent",
    "website": "www.eficent.com",
    "category": "Generic Modules/Projects & Services",
    "depends": ["purchase", "analytic_resource_plan"],
    "description": """
Resource Plan
====================================
    An effective planning of costs and revenues associated to projects or to other analytic accounts
    becomes essential in organizations that are run by projects, or profit center accounting.
    The process of cost planning generally follows an rolling wave planning approach, in which
    the level of detail of the planned costs is increases over time, as the details of the work required
    are known to the planning group.

    The module 'Resource Plan' makes it possible to plan the resources required for a project and determines
    the cost associated with them. It provides also the possibility to create purchase orders f

Define Planning Versions:
------------------------------------
    Organizations typically maintain different versions of their planned costs (rough cut, detailed,
    approved budget, committed,...).
    A Planning Version is defined by the following attributes:
        * Name
        * Code
        * Active: The planning version is active for use in the cost planning
        * Default version for committed costs: This planning version should be used for committed costs
        * Default planning version: This version is proposed by default

Define Analytic Planning Journals:
------------------------------------
    The Analytic Planning Journal serves as an attribute to classify the costs or revenue by the it's origin.
    It is equivalent to the Analytic Journal.

    """,
    "init_xml": [],
    "update_xml": [        
        "wizard/analytic_resource_plan_line_make_purchase.xml",
        "analytic_resource_plan_line_view.xml",
        "analytic_account_view.xml",
        
    ],
    'demo_xml': [

    ],
    'test':[
    ],
    'installable': True,
    'active': False,
    'certificate': '',
}