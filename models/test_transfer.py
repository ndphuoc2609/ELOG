from odoo import api, fields, models, _
from odoo.exceptions import AccessDenied



class Picking(models.Model):
    _inherit = "stock.picking"

    def test(self):
        productA = self.env['product.product'].search([('name', '=', 'Test product 1')])
        productB = self.env['product.product'].search([('name', '=', 'Test product 2')])
        suppliers = self.env.ref('stock.stock_location_suppliers')
        wh = self.env['stock.location'].search([('location_id', '=', 'WH1')])
        picking = self.env['stock.picking'].create({
            'location_id': suppliers.id,
            'location_dest_id': wh.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
        })
        move1 = self.env['stock.move'].create({
            'name': 'test_transit_1',
            'location_id': suppliers.id,
            'location_dest_id': wh.id,
            'product_id': productA.id,
            'product_uom': self.env.ref('uom.product_uom_unit').id,
            'product_uom_qty': 1.0,
            'picking_id': picking.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
        })
        move2 = self.env['stock.move'].create({
            'name': 'test_transit_1',
            'location_id': suppliers.id,
            'location_dest_id': wh.id,
            'product_id': productB.id,
            'product_uom': self.env.ref('uom.product_uom_unit').id,
            'product_uom_qty': 1.0,
            'picking_id': picking.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
        })
        picking.action_confirm()
        picking.action_assign()
        move1.quantity_done = 1
        move2.quantity_done = 1
        picking.action_put_in_pack()
        package = picking.package_level_ids.package_id
        package.write({'name': "test002"})
        picking.button_validate()
        return True
    
    def transfer(self):
        package = self.env['stock.quant.package'].search([('name', '=', 'test002')])
        wh1 = self.env['stock.location'].search([('location_id', '=', 'WH1')])
        wh2 = self.env['stock.location'].search([('location_id', '=', 'WH2')])
        customer = self.env.ref('stock.stock_location_customers')
        type1 = self.env['stock.picking.type'].search(['&', ('warehouse_id', '=', 'WH2'), ('name', '=', 'Internal Transfers')])
        type2 = self.env['stock.picking.type'].search(['&', ('warehouse_id', '=', 'WH2'), ('name', '=', 'Delivery Orders')])
        picking1 = self.env['stock.picking'].create({
            'location_id': wh1.id,
            'location_dest_id': wh2.id,
            'picking_type_id': type1.id,
        })
        package_level = self.env['stock.package_level'].create({
            'package_id': package.id,
            'picking_id': picking1.id,
            'company_id': picking1.company_id.id,
        })
        picking2 = self.env['stock.picking'].create({
            'location_id': wh2.id,
            'location_dest_id': customer.id,
            'picking_type_id': type2.id,
        })
        package_level = self.env['stock.package_level'].create({
            'package_id': package.id,
            'picking_id': picking2.id,
            'company_id': picking2.company_id.id,
        })

        picking1.action_confirm()
        picking2.action_confirm()
        picking1.action_assign()
        picking2.action_assign()
        return True