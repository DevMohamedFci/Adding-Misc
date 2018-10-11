# -*- coding: utf-8 -*-
from odoo import http

# class TayAccountAddingMisc(http.Controller):
#     @http.route('/tay_account__adding__misc/tay_account__adding__misc/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tay_account__adding__misc/tay_account__adding__misc/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tay_account__adding__misc.listing', {
#             'root': '/tay_account__adding__misc/tay_account__adding__misc',
#             'objects': http.request.env['tay_account__adding__misc.tay_account__adding__misc'].search([]),
#         })

#     @http.route('/tay_account__adding__misc/tay_account__adding__misc/objects/<model("tay_account__adding__misc.tay_account__adding__misc"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tay_account__adding__misc.object', {
#             'object': obj
#         })