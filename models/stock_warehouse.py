# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Stock(models.Model):
    _inherit = 'stock.warehouse'

    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")
    address = fields.Char(string="Address")

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    @api.model
    def update_show_entire_packs(self):
        picking_types = self.search([('warehouse_id', '!=', False)])
        picking_types.write({'show_entire_packs': True})