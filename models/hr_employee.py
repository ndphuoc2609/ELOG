from odoo import api, fields, models, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    warehouse_id = fields.Many2one('stock.warehouse', string='Assigned Warehouse', default="")
    driver_is_online = fields.Boolean(string="Is Driver Online", default=False)
    driver_latitude = fields.Char(string="Driver Latitude", default="0.0")
    driver_longitude = fields.Char(string="Driver Longitude", default="0.0")
    driver_transports = fields.One2many('shipping.order.transport', 'driver_id', compute='_compute_transports', compute_sudo=True)

    def _compute_transports(self):
        for employee in self:
            if employee.job_id.name != "Driver":
                continue
            transports = self.env['shipping.order.transport'].search([('driver_id', '=', employee.id)])
            employee.driver_transports = transports