from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
from odoo.tools import float_compare, float_is_zero


class SellAsset(models.TransientModel):
    _name = 'sell.asset'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Buyer',
        required=True)
    date = fields.Date(
        string='Date', 
        required=True)
    asset_id = fields.Many2one(comodel_name="account.asset.asset")
    amount = fields.Float(
        string='Amount', 
        required=False)
    asset_number = fields.Char(string="Asset Number", related="asset_id.asset_number")
    residual_value = fields.Float(string="Residual Value", related="asset_id.value_residual")

    def sell_asset(self):
        for inv in self:
            asset = inv.asset_id
            invoice_vals = {
                'partner_id': inv.partner_id.id,
                'state': 'draft',
                'invoice_date': inv.date,
                'type': 'out_invoice',
                'invoice_line_ids': [(0, 0, {
                    'name': asset.asset_number,
                    'account_id': asset.category_id.account_asset_id.id,
                    'quantity': 1,
                    'price_unit': inv.amount,
                })]
            }
            invoice = self.env['account.invoice'].create(invoice_vals)
            self.asset_id.sale_invoice = invoice.id
            self.asset_id.sale_invoice.action_invoice_open()
            self.asset_id.sale_move_id = invoice.move_id.id
            if self.amount > self.residual_value :
                asset_name = self.asset_number
                category_id = self.asset_id.category_id
                gain_amount = self.amount - self.residual_value
                company_currency = self.asset_id.company_id.currency_id
                current_currency = self.asset_id.currency_id
                prec = company_currency.decimal_places
                account_analytic_id = self.asset_id.account_analytic_id
                analytic_tag_ids = self.asset_id.analytic_tag_ids
                amount = current_currency._convert(
                    self.amount, company_currency, self.asset_id.company_id, self.date)
                move_line_1 = {
                    'name': asset_name,
                    'account_id': category_id.account_asset_id.id,
                    'debit': 0.0 if float_compare(self.amount, 0.0, precision_digits=prec) > 0 else -amount,
                    'credit': gain_amount if float_compare(self.amount, 0.0, precision_digits=prec) > 0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'analytic_account_id': account_analytic_id.id if category_id.type == 'sale' else False,
                    'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'sale' else False,
                    'currency_id': company_currency != current_currency and current_currency.id or False,
                    'amount_currency': company_currency != current_currency and - 1.0 * self.amount or 0.0,
                }
                move_line_2 = {
                    'name': asset_name,
                    'account_id': category_id.account_asset_gain.id,
                    'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                    'debit': gain_amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'analytic_account_id': account_analytic_id.id if category_id.type == 'purchase' else False,
                    'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'purchase' else False,
                    'currency_id': company_currency != current_currency and current_currency.id or False,
                    'amount_currency': company_currency != current_currency and self.amount or 0.0,
                }
                move_vals = {
                    'ref': self.asset_id.name,
                    'date': self.date or False,
                    'journal_id': category_id.journal_id.id,
                    'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
                }
                move = self.env['account.move'].create(move_vals)
                self.asset_id.gain_loss_move_id = move.id
                self.asset_id.gain_amount = gain_amount
                self.asset_id.state = 'sold'
                # entered = entry.id
                # entered.action_post()
            elif self.amount < self.residual_value:
                asset_name = self.asset_number
                category_id = self.asset_id.category_id
                loss_amount = self.residual_value - self.amount
                company_currency = self.asset_id.company_id.currency_id
                current_currency = self.asset_id.currency_id
                prec = company_currency.decimal_places
                account_analytic_id = self.asset_id.account_analytic_id
                analytic_tag_ids = self.asset_id.analytic_tag_ids
                amount = current_currency._convert(
                    self.amount, company_currency, self.asset_id.company_id, self.date)
                move_line_1 = {
                    'name': asset_name,
                    'account_id': category_id.account_loss_id.id,
                    'debit': 0.0 if float_compare(self.amount, 0.0, precision_digits=prec) > 0 else -amount,
                    'credit': loss_amount if float_compare(self.amount, 0.0, precision_digits=prec) > 0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'analytic_account_id': account_analytic_id.id if category_id.type == 'sale' else False,
                    'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'sale' else False,
                    'currency_id': company_currency != current_currency and current_currency.id or False,
                    'amount_currency': company_currency != current_currency and - 1.0 * self.amount or 0.0,
                }
                move_line_2 = {
                    'name': asset_name,
                    'account_id': category_id.account_asset_id.id,
                    'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                    'debit': loss_amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'analytic_account_id': account_analytic_id.id if category_id.type == 'purchase' else False,
                    'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'purchase' else False,
                    'currency_id': company_currency != current_currency and current_currency.id or False,
                    'amount_currency': company_currency != current_currency and self.amount or 0.0,
                }
                move_vals = {
                    'ref': self.asset_id.name,
                    'date': self.date or False,
                    'journal_id': category_id.journal_id.id,
                    'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
                }
                move = self.env['account.move'].create(move_vals)
                self.asset_id.gain_loss_move_id = move.id
                self.asset_id.loss_amount = loss_amount
                self.asset_id.state = 'sold'
            elif self.amount == self.residual_value:
                self.asset_id.state = 'sold'




