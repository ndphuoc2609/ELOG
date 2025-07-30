from odoo import models, fields, api

class AssignDriverWizard(models.TransientModel):
    _name = 'assign.driver.wizard'
    _description = 'Assign Driver Wizard'

    shift_id = fields.Many2one('planning.slot', string="Shift", required=True,
                domain="[('state', '=', 'published'), ('job_title', '=', 'Driver'), ('end_datetime', '>=', context_today().strftime('%Y-%m-%d 00:00:00'))]")
    shift_start = fields.Datetime('Shift start', related = 'shift_id.start_datetime', readonly=True)
    shift_end = fields.Datetime('Shift end', related = 'shift_id.end_datetime', readonly=True)
    transport_type = fields.Selection([
        ('pickup', 'Pick up'),
        ('transit', 'Transit'),
        ('delivery', 'Delivery')], string='Type', default='pickup', required=True)

    def assign_driver(self):
        active_ids = self.env.context.get('active_ids', [])
        orders = self.env['shipping.order'].browse(active_ids)
        for order in orders:
            for transport in order.transport_ids:
                if transport.type == self.transport_type and transport.state == 'new':
                    transport.shift_id = self.shift_id
                    break

        return {'type': 'ir.actions.act_window_close'}