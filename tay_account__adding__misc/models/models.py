# -*- coding: utf-8 -*-

import time
from collections import OrderedDict
from odoo import api, fields, models, _
from odoo.api import cr
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
import odoo.addons.decimal_precision as dp
from lxml import etree

# class tay_account__adding__misc(models.Model):
#     _name = 'tay_account__adding__misc.tay_account__adding__misc'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100
class account_payment_Adding_mics(models.Model):
    _name = 'account.payment'
    _inherit = 'account.payment'

    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor'), ('Mics', 'Mics')])
    journal_entry = fields.Many2one('account.move')
    line_ids=fields.One2many('account.payment.line','payment_id')

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if not self.amount > 0.0:
            if(self.partner_type != 'Mics'):
                raise ValidationError(_('The payment amount must be strictly positive.'))

    @api.multi
    def post(self):
        if(self.partner_type=='Mics'):
            for rec in self:
                sequence_code = 'hr.advance.sequence'
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(
                    sequence_code)
                total=0.0
                for line in rec.line_ids:
                    total+=line.value
                if(rec.payment_type=='inbound'):
                    lst=[(0, 0, {
                        'name': '/',
                        'debit':rec.currency_id.compute(total, rec.currency_id) ,
                        'account_id': rec.journal_id.default_debit_account_id.id,

                    })]
                    for line in rec.line_ids:
                        lst.append((0, 0, {
                            'name': line.name,
                            'credit': rec.currency_id.compute(line.value, rec.currency_id),
                            'account_id': line.account_id.id,

                        }))
                    move = {
                        'name':  '/',
                        'journal_id': rec.journal_id.id,
                        'date': rec.payment_date,
                        'line_ids': lst
                    }
                    move_id = self.env['account.move'].create(move)
                    move_id.post()
                    return rec.write({'state': 'posted', 'move_id': move_id.id})
                else:
                    if(rec.payment_type=='outbound'):
                        lst = [(0, 0, {
                            'name': '/',
                            'credit': rec.currency_id.compute(total, rec.currency_id),
                            'account_id': rec.journal_id.default_credit_account_id.id,

                        })]
                        for line in rec.line_ids:
                            lst.append((0, 0, {
                                'name': line.name,
                                'debit': rec.currency_id.compute(line.value, rec.currency_id),
                                'account_id': line.account_id.id,

                            }))
                        move = {
                            'name': '/',
                            'journal_id': rec.journal_id.id,
                            'date': rec.payment_date,
                            'line_ids': lst
                        }
                        move_id = self.env['account.move'].create(move)
                        move_id.post()
                        return rec.write({'state': 'posted', 'move_id': move_id.id})
        else :
            """ Create the journal items for the payment and update the payment's state to 'posted'.
                        A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
                        and another in the destination reconciliable account (see _compute_destination_account_id).
                        If invoice_ids is not empty, there will be one reconciliable move line per invoice to reconcile with.
                        If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
                    """
            for rec in self:

                if rec.state != 'draft':
                    raise UserError(
                        _("Only a draft payment can be posted. Trying to post a payment in state %s.") % rec.state)

                if any(inv.state != 'open' for inv in rec.invoice_ids):
                    raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(
                    sequence_code)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

                # Create the journal entry
                amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
                move = rec._create_payment_entry(amount)

                # In case of a transfer, the first journal entry created debited the source liquidity account and credited
                # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
                if rec.payment_type == 'transfer':
                    transfer_credit_aml = move.line_ids.filtered(
                        lambda r: r.account_id == rec.company_id.transfer_account_id)
                    transfer_debit_aml = rec._create_transfer_entry(amount)
                    (transfer_credit_aml + transfer_debit_aml).reconcile()

                rec.write({'state': 'posted', 'move_name': move.name})





class t_account_payment_line(models.Model):
    _name='account.payment.line'

    id=fields.Integer()
    payment_id=fields.Many2one('account.payment')

    account_id = fields.Many2one('account.account', string='Account',
                                 required=True, domain=[('deprecated', '=', False)])
    value=fields.Float('vlaue')
    name=fields.Char('label')

