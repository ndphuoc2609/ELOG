from datetime import datetime, timedelta, timezone
from odoo import api, fields, models, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    warehouse_id = fields.Many2one('stock.warehouse', string='Assigned Warehouse', default="")
    is_working = fields.Boolean(string="Is Working", default=False)
    driver_last_updated = fields.Datetime(string="Last Time Driver Connect")
    driver_is_online = fields.Boolean(string="Driver Is Online")
    driver_latitude = fields.Char(string="Driver Latitude", default="0.0")
    driver_longitude = fields.Char(string="Driver Longitude", default="0.0")
    driver_transports = fields.One2many('shipping.order.transport', 'driver_id', compute='_compute_transports', compute_sudo=True)

    def _compute_transports(self):
        for employee in self:
            if employee.job_id.name != "Driver":
                continue
            transports = self.env['shipping.order.transport'].search([('driver_id', '=', employee.id)])
            employee.driver_transports = transports

    def update_drivers(self):
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        employees = self.search([])
        for employee in employees:
            if employee.job_id.name != 'Driver':
                continue
            current_shift = self.env['planning.slot'].search([('employee_id', '=', employee.id), ('state', '=', 'published'), 
                                                              ('start_datetime', '<=', current_time), ('end_datetime', '>=', current_time)])
            if current_shift:
                employee.is_working = True
            else:
                employee.is_working = False
            
            # driver connected to server in the last hour
            if employee.driver_last_updated and employee.driver_last_updated > current_time - timedelta(hours=1):
                employee.driver_is_online = True
            else:
                employee.driver_is_online = False