# -*- coding: utf-8 -*-
from odoo import http

# class AssetImprovement(http.Controller):
#     @http.route('/asset_improvement/asset_improvement/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/asset_improvement/asset_improvement/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('asset_improvement.listing', {
#             'root': '/asset_improvement/asset_improvement',
#             'objects': http.request.env['asset_improvement.asset_improvement'].search([]),
#         })

#     @http.route('/asset_improvement/asset_improvement/objects/<model("asset_improvement.asset_improvement"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('asset_improvement.object', {
#             'object': obj
#         })