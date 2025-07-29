from odoo import models, fields, api

class PickupDriverWizard(models.TransientModel):
    _name = 'pickup.driver.wizard'
    _description = 'Pickup Driver Selection Wizard'

    driver_pickup_id = fields.Many2one('res.users', string='Pickup Driver', required=False)
    driver_delivery_id = fields.Many2one('res.users', string='Delivery Driver', required=False)

    def assign_driver(self):
        active_ids = self.env.context.get('active_ids', [])
        orders = self.env['shipping.order'].browse(active_ids)
        if  self.driver_pickup_id:
            for order in orders:
                order.driver_pickup_id = self.driver_pickup_id
        if self.driver_delivery_id:
            for order in orders:
                order.driver_delivery_id = self.driver_delivery_id

        return {'type': 'ir.actions.act_window_close'}