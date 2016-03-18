# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp.tools import misc
import time
import openerp.addons.decimal_precision as dp
from openerp import api, fields, models
from openerp.tools.translate import _


class AccountAnalyticLinePlan(models.Model):
    _name = 'account.analytic.line.plan'
    _description = 'Analytic planning line'
    _order = 'date desc'

    @api.model
    def _get_company_currency(self):
        """
        Returns the default company currency
        """
        company_obj = self.env['res.company']
        company_id = self.env['res.company']._company_default_get('account.analytic.line')
        company = company_obj.browse(company_id)
        return company.currency_id and company.currency_id.id or False

    @api.model
    def _get_currency(self):
        company_obj = self.env['res.company']
        company_id = company_obj._company_default_get('account.analytic.line')
        company = company_obj.browse(company_id)
        return company.currency_id.id

    name = fields.Char('Activity description', required=True)
    date = fields.Date('Date', required=True, select=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    amount = fields.Float('Amount', required=True,
                           help='Calculated by multiplying the quantity '
                                'and the price given in the Product\'s '
                                'cost price. Always expressed in the '
                                'company main currency.',
                           digits_compute=dp.get_precision('Account'),
                           default=0.00)
    unit_amount = fields.Float('Quantity', help='Specifies the amount of '
                                                 'quantity to count.')
    amount_currency = fields.Float('Amount Currency',
                                    help="The amount expressed in an "
                                         "optional other currency.")
    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_currency)
    account_id = fields.Many2one('account.analytic.account',
                                  'Analytic Account', required=True,
                                  ondelete='restrict', select=True,
                                  domain=[('type', '<>', 'view')])
    user_id = fields.Many2one('res.users', 'User')
    company_id = fields.Many2one(related='account_id.company_id',
                                 relation='res.company',
                                 string='Company', store=True,
                                 readonly=True, default=lambda self:
        self.env['res.company']._company_default_get('account.analytic.line'))
    product_uom_id = fields.Many2one('product.uom', 'UoM')
    product_id = fields.Many2one('product.product', 'Product')
    general_account_id = fields.Many2one('account.account',
                                          'General Account',
                                          required=True,
                                          ondelete='restrict')
    journal_id = fields.Many2one('account.analytic.plan.journal',
                                  'Planning Analytic Journal',
                                  required=True, ondelete='restrict',
    select=True, default=lambda self: self._context['journal_id'] if self._context and 'journal_id' in self._context else None)
    code = fields.Char('Code')
    ref = fields.Char('Ref.')
    notes = fields.Text('Notes')
    version_id = fields.Many2one('account.analytic.plan.version',
                                  'Planning Version', required=True,
                                  ondelete='cascade', default=lambda s: s.env['account.analytic.plan.version'].search([('default_plan', '=', True)]))

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self._context.get('from_date', False):
            args.append(['date', '>=', self._context['from_date']])
        if self._context.get('to_date', False):
            args.append(['date', '<=', self._context['to_date']])
        return super(AccountAnalyticLinePlan, self).search(args, offset,
                                                           limit, order,
                                                           count=count)

    @api.multi
    def _check_company(self):
        lines = self.browse(self._ids)
        for l in lines:
            if l.move_id and not l.account_id.company_id.id == \
                    l.move_id.account_id.company_id.id:
                return False
        return True

#############################
# from_currecy : currency_id
# to_currency : company_currency_id
# from_amount : amount_currency
#############################
#    def on_change_amount_currency(self, amount_currency, currency_id, company_id):

    @api.onchange('amount_currency', 'currency_id')
    def on_change_amount_currency(self):
        print "on_change_amount_currency 44444444444444444444444444444444", self
#        res = {}
#        res['value'] = {}
        company = self.company_id
        company_currency = company.currency_id
#        company_currency_id = company.currency_id.id
        currency = self.currency_id
        if self.amount_currency:
            amount_company_currency = currency.compute(self.amount_currency,
                                                           company_currency)
        else:
            amount_company_currency = 0.0
#        res['value'].update({
#            'amount': amount_company_currency,
#        })
#        if self:
        print "amount_company_currency 8888888888888888888888888888888888", amount_company_currency
        self.amount = amount_company_currency
        return {}

#    def on_change_unit_amount(self, cr, uid, id, prod_id, quantity,
#                              currency_id, company_id, unit=False,
#                              journal_id=False, context=None):
    @api.onchange('unit_amount', 'product_uom_id')
    def on_change_unit_amount(self):
        print "voila 222222222222222222222222222222222", self
#        res = dict()
#        res['value'] = {}
        product_obj = self.env['product.product']
        analytic_journal_obj = self.env['account.analytic.plan.journal']
        product_price_type_obj = self.env['product.price.type']

        prod = False
        if self.product_id:
            prod = self.product_id
        if not self.journal_id:
            j = analytic_journal_obj.search([('type', '=', 'purchase')])
            journal = j[0] if j and j[0] else False
        if not self.journal_id or not self.product_id:
            return {}
        journal = self.journal_id if self.journal_id else journal
        if journal.type != 'sale' and prod:
            a = prod.product_tmpl_id.property_account_expense.id
            if not a:
                a = prod.categ_id.property_account_expense_categ.id
            if not a:
                raise Warning(_('There is no expense account defined '
                                       'for this product: "%s" (id:%d)')
                                     % (prod.name, prod.id,))
        else:
            a = prod.product_tmpl_id.property_account_income.id
            if not a:
                a = prod.categ_id.property_account_income_categ.id
            if not a:
                raise Warning(_('There is no income account defined '
                                       'for this product: "%s" (id:%d)')
                                     % (prod.name, self.product_id,))
        flag = False
        # Compute based on pricetype
        product_price_type = product_price_type_obj.search([('field', '=', 'standard_price')])
        pricetype = product_price_type[0]
        print "pricetype ################################", pricetype
        if self.journal_id:
            if journal.type == 'sale':
                product_price_type = product_price_type_obj.search([('field', '=', 'list_price')])
                if product_price_type:
                    pricetype = product_price_type[0]
        # Take the company currency as the reference one
        if pricetype.field == 'list_price':
            flag = True
        cr, uid, context = self.env.args
        print "context ####################################", context
        ctx = dict(context.copy())
        if self.product_uom_id:
            # price_get() will respect a 'uom' in its context, in order
            # to return a default price for those units
            ctx['uom'] = self.product_uom_id
            print "ctx 222222222222222222222222222222222222", ctx
        amount_unit = prod.with_context(ctx).price_get(pricetype.field)[prod.id]
        self.env.args = cr, uid, misc.frozendict(context)
        prec = self.env['decimal.precision'].precision_get('Account')
        amount = amount_unit * self.unit_amount or 1.0
        print "amount ################################", amount
        result = round(amount, prec)
        print "\n\nresult ################################", result
        if not flag:
            if journal.type != 'sale':
                result *= -1
#        res = self.on_change_amount_currency(cr, uid, id, result, currency_id, 
#                                             company_id, context)
#        if self:
        self.amount_currency = result
        self.general_account_id = a
        print "\n\nresult 2222222 ################################", result
        self.on_change_amount_currency()
#        res['value'].update({
#            'amount_currency': result,
#            'general_account_id': a,
#        })
        return {}

####### on_change="on_change_product_id(product_id, unit_amount, currency_id, company_id, product_uom_id, journal_id)"

    @api.onchange('product_id')
    def on_change_product_id(self):
#        if self.product_id:
        print "on_change_product_id #########################", self.product_id
#        res = self.on_change_unit_amount(prod_id, quantity,
#                                         currency_id, company_id,
#                                         unit, journal_id)
        self.on_change_unit_amount()
#        if self.product_id:
        prod = self.product_id
#            res['value'].update({
#                'name': prod.name,
#            })
        self.name = prod.name
        if prod.uom_id:
#                res['value'].update({
#                    'product_uom_id': prod.uom_id.id,
#                })
            self.product_uom_id = prod.uom_id.id
        return {}

    @api.model
    def view_header_get(self, view_id, view_type):
        if self._context.get('account_id', False):
            self._cr.execute('select name from account_analytic_account where id=%s',
                       (self._context['account_id'],))
            res = self._cr.fetchone()
            if res:
                res = _('Entries: ')+(res[0] or '')
            return res
        return False
