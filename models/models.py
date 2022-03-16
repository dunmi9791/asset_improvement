# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AssetImprovementLine(models.Model):
    _name = 'asset.improvement.line'
    _description = 'AssetImprovementLine'


    name = fields.Char(string='Depreciation Name', required=True, index=True)
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



class AccountAsset(models.Model):
    _inherit = 'account.asset.asset'

    asset_improvement_ids = fields.One2many(
        comodel_name='asset.improvement.line',
        inverse_name='asset_id',
        string='Asset_improvement_ids',
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