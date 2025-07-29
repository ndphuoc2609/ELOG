from odoo import models, fields

class ShippingOrderProduct(models.Model):
    _name = 'shipping.order.product'
    _description = 'Shipping Order Product'

    shipping_order_id = fields.Many2one('shipping.order', string='Shipping Order', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=False, ondelete='cascade')
    barcode = fields.Char(string='Barcode', related='product_id.barcode')
    product_name = fields.Char(string='Product Name', required=True)
    weight = fields.Float(string='Weight (kg)', required=True)
    dimensions = fields.Char(string='Dimensions (cm3)', required=True)
    shipment_value = fields.Float(string='Shipment Value (VND)', required=False)