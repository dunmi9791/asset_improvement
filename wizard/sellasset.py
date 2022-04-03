from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class SellAsset(models.TransientModel):
    _name = 'sell.asset'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Buyer',
        required=False)
    date = fields.Date(
        string='Date', 
        required=False)
    asset_id = fields.Many2one(comodel_name="account.asset.asset")
    amount = fields.Float(
        string='Amount', 
        required=False)

    def sell_asset(self):
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'state': 'draft',
            'invoice_date': self.date,
            'type': 'out_invoice',
            'invoice_line_ids': [0, 0, {
                'name': self.asset_id.asset_number,
                'account_id': self.asset_id.category_id.account_asset_id.id,
                'quantity': 1,
                'price_unit': self.amount,
            }]
        }
        invoice = self.env['account.invoice'].create(invoice_vals)
        self.asset_id.sale_invoice = invoice.id