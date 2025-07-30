from odoo import api, models, fields

class ShippingZone(models.Model):
    _name = 'shipping.zone'
    _description = 'Driver Working Zone'

    name = fields.Char("Name", required=True)
    area = fields.Char("Area", required=True)
    role_id = fields.Many2one('planning.role', string="Role")
    transports = fields.One2many('shipping.order.transport', 'driver_id', compute='_compute_transports', compute_sudo=True)

    def _compute_transports(self):
        for zone in self:
            transports = self.env['shipping.order.transport'].search([('zone_id', '=', zone.id)])
            zone.transports = transports

    @api.model
    def create(self, vals):
        # create new role for the zone
        role = self.env['planning.role'].create({'name': f'{vals["name"]} driver'})

        # create shift template for the zone
        morning_shift = self.env['planning.slot.template'].create({
            'role_id': role.id,
            'start_time': 8.0,
            'end_time': 12.0,
            'duration': 4.0,
        })
        evening_shift = self.env['planning.slot.template'].create({
            'role_id': role.id,
            'start_time': 13.0,
            'end_time': 12.0,
            'duration': 4.0,
        })
        vals['role_id'] = role.id
        return super(ShippingZone, self).create(vals)

    def write(self, vals):
        if vals.get('name'):
            role = self.role_id
            role.write({'name': f'{vals["name"]} driver'})
        return super().write(vals)