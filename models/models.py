# -*- coding: utf-8 -*-


import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class AssetImprovementLine(models.Model):
    _name = 'asset.improvement.line'
    _description = 'AssetImprovementLine'


    name = fields.Char(string='Improvement Name', required=True, index=True)
    sequence = fields.Integer(required=True)
    asset_id = fields.Many2one('account.asset.asset', string='Asset', required=True, ondelete='cascade')
    parent_state = fields.Selection(related='asset_id.state', string='State of Asset')
    amount = fields.Float(string='Current Improvement Cost', digits=0, required=True)
    remaining_value = fields.Float(string='New Value', digits=0, required=True)
    depreciated_value = fields.Float(string='Cumulative Improvements', required=True)
    depreciation_date = fields.Date('Improvement Date', index=True)
    move_id = fields.Many2one('account.move', string='Improvement Entry')
    move_check = fields.Boolean(compute='_get_move_check', string='Linked', track_visibility='always', store=True)
    move_posted_check = fields.Boolean(compute='_get_move_posted_check', string='Posted', track_visibility='always',
                                       store=True)

    @api.multi
    @api.depends('move_id')
    def _get_move_check(self):
        for line in self:
            line.move_check = bool(line.move_id)

    @api.multi
    @api.depends('move_id.state')
    def _get_move_posted_check(self):
        for line in self:
            line.move_posted_check = True if line.move_id and line.move_id.state == 'posted' else False

    @api.multi
    def create_move(self, post_move=True):
        created_moves = self.env['account.move']
        for line in self:
            if line.move_id:
                raise UserError(_('This improvement is already linked to a journal entry. Please post or delete it.'))
            move_vals = self._prepare_move(line)
            move = self.env['account.move'].create(move_vals)
            line.write({'move_id': move.id, 'move_check': True})
            created_moves |= move

        if post_move and created_moves:
            created_moves.filtered(
                lambda m: any(m.asset_improvement_ids.mapped('asset_id.category_id.open_asset'))).post()
        return [x.id for x in created_moves]

    def _prepare_move(self, line):
        category_id = line.asset_id.category_id
        account_analytic_id = line.asset_id.account_analytic_id
        analytic_tag_ids = line.asset_id.analytic_tag_ids
        depreciation_date = self.env.context.get('depreciation_date') or line.depreciation_date or fields.Date.context_today(self)
        company_currency = line.asset_id.company_id.currency_id
        current_currency = line.asset_id.currency_id
        prec = company_currency.decimal_places
        amount = current_currency._convert(
            line.amount, company_currency, line.asset_id.company_id, depreciation_date)
        asset_name = line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.asset_improvement_ids))
        move_line_1 = {
            'name': asset_name,
            'account_id': category_id.account_depreciation_id.id,
            'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'partner_id': line.asset_id.partner_id.id,
            'analytic_account_id': account_analytic_id.id if category_id.type == 'sale' else False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'sale' else False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and - 1.0 * line.amount or 0.0,
        }
        move_line_2 = {
            'name': asset_name,
            'account_id': category_id.account_asset_id.id,
            'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'partner_id': line.asset_id.partner_id.id,
            'analytic_account_id': account_analytic_id.id if category_id.type == 'purchase' else False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'purchase' else False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and line.amount or 0.0,
        }
        move_vals = {
            'ref': line.asset_id.code,
            'date': depreciation_date or False,
            'journal_id': category_id.journal_id.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
        }
        return move_vals


class AccountAsset(models.Model):
    _inherit = 'account.asset.asset'

    asset_improvement_ids = fields.One2many(
        comodel_name='asset.improvement.line',
        inverse_name='asset_id',
        string='Asset_improvement_ids',
        required=False)
    state = fields.Selection(
        selection_add=[('sold', 'Sold')],
    )
    sale_date = fields.Date(string="Disposal date")
    sale_move_id = fields.Many2one(
        comodel_name='account.move', string="Disposal move",
    )
    sale_invoice = fields.Many2one(
        comodel_name='account.invoice',
        string='Sale_invoice',
        required=False)

# class asset_improvement(models.Model):
#     _name = 'asset_improvement.asset_improvement'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100