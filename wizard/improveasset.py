from odoo import fields, models, api


class ImproveAsset(models.TransientModel):
    _name = 'improve.asset'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
        required=True)
    date = fields.Date(
        string='Date',
        required=True)
    asset_id = fields.Many2one(comodel_name="account.asset.asset")
    amount = fields.Float(
        string='Amount',
        required=False)
    description = fields.Char(
        string='Description',
        required=False)

    def improve_asset(self):
        for inv in self:
            asset = inv.asset_id
            invoice_vals = {
                'partner_id': inv.partner_id.id,
                'state': 'draft',
                'invoice_date': inv.date,
                'type': 'in_invoice',
                'invoice_line_ids': [(0, 0, {
                    'name': asset.asset_number,
                    'account_id': asset.category_id.account_asset_id.id,
                    'quantity': 1,
                    'price_unit': inv.amount,
                })]
            }
            improve_vals = {
                'name': asset.name,
                'asset_id': asset.id,
                'amount': inv.amount,
                'description': inv.description,


            }
            improvement = self.env['asset.improvement.line'].create(improve_vals)
            invoice = self.env['account.invoice'].create(invoice_vals)
            invoice.action_invoice_open()
            improvement.move_id = invoice.move_id.id
            # self.asset_id.sale_move_id = invoice.move_id.id