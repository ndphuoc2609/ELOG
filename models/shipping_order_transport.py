from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import math

MAX_TRANSPORTS_PER_SHIFT = 100
class ShippingOrderTransport(models.Model):
    _name = 'shipping.order.transport'
    _description = 'Shipping Order Transport'

    shipping_order_id = fields.Many2one('shipping.order', string='Shipping Order', required=True, ondelete='cascade')
    type = fields.Selection([
        ('pickup', 'Pick up'),
        ('transit', 'Transit'),
        ('delivery', 'Delivery')], string='Type', default='pickup', required=True)
    shift_id = fields.Many2one('planning.slot', string="Shift", required=False,
                domain="[('state', '=', 'published'), ('job_title', '=', 'Driver'), ('end_datetime', '>=', context_today().strftime('%Y-%m-%d 00:00:00'))]")
    shift_start = fields.Datetime('Shift start', related = 'shift_id.start_datetime', readonly=True)
    shift_end = fields.Datetime('Shift end', related = 'shift_id.end_datetime', readonly=True)
    driver_id = fields.Many2one(string='Driver', related='shift_id.employee_id', readonly=True)
    driver_phone = fields.Char(string='Driver Phone', related='driver_id.phone', readonly=True)
    from_location = fields.Many2one('stock.location', string="From Location", required=True, domain=[('name', 'in', ['Stock', 'Customers', 'Vendors'])])
    to_location = fields.Many2one('stock.location', string="To Location", required=True, domain=[('name', 'in', ['Stock', 'Customers', 'Vendors'])])
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed')], string='State', default='new', required=True)
    from_address = fields.Char(string='From Address', compute='_compute_location_info', readonly=True)
    from_latitude = fields.Char(string='From Latitude', compute='_compute_location_info', readonly=True)
    from_longitude = fields.Char(string='From Longitude', compute='_compute_location_info', readonly=True)
    to_address = fields.Char(string='To Address', compute='_compute_location_info', readonly=True)
    to_latitude = fields.Char(string='To Latitude', compute='_compute_location_info', readonly=True)
    to_longitude = fields.Char(string='To Longitude', compute='_compute_location_info', readonly=True)
    zone_id = fields.Many2one('shipping.zone', compute='_compute_location_info')
    
    def _compute_location_info(self):
        def get_location_info(order, location):
            address = latitude = longitude = ""
            if location.name == "Vendors":
                address = order.from_address
                latitude = order.from_latitude
                longitude = order.from_longitude
            elif location.name == "Customers":
                address = order.to_address
                latitude = order.to_latitude
                longitude = order.to_longitude
            else:
                warehouse = location.warehouse_id
                address = warehouse.address
                latitude = warehouse.latitude
                longitude = warehouse.longitude
            return address, latitude, longitude
        
        def haversine(lat1, lon1, lat2, lon2):
            # Radius of the Earth in kilometers
            R = 6371.0

            # Convert latitude and longitude from degrees to radians
            lat1 = math.radians(float(lat1))
            lon1 = math.radians(float(lon1))
            lat2 = math.radians(float(lat2))
            lon2 = math.radians(float(lon2))

            # Difference in coordinates
            dlat = lat2 - lat1
            dlon = lon2 - lon1

            # Haversine formula
            a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            # Distance in kilometers
            distance = R * c

            return distance
        
        def find_best_zone(latitude, longitude):
            zones = self.env['shipping.zone'].search([])
            closest_distance = 10000
            closest_zone = None
            for zone in zones:
                distance = haversine(latitude, longitude, zone.latitude, zone.longitude)
                if distance <= zone.radius and distance < closest_distance:
                    closest_distance = distance
                    closest_zone = zone
            
            return closest_zone.id

        for transport in self:
            transport.from_address, transport.from_latitude, transport.from_longitude = get_location_info(transport.shipping_order_id, transport.from_location)
            transport.to_address, transport.to_latitude, transport.to_longitude = get_location_info(transport.shipping_order_id, transport.to_location)
            if transport.type == "delivery":
                transport.zone_id = find_best_zone(transport.to_latitude, transport.to_longitude)
            else:
                transport.zone_id = find_best_zone(transport.from_latitude, transport.from_longitude)
    
    def find_shift(self, pickup_time=datetime.now()):
        if pickup_time.hour < 8: # before 8am => 8am-12pm shift
            pickup_time = pickup_time.replace(hour=8, minute=0, second=0)
        elif pickup_time.hour == 12: # 12pm-13pm => 13pm-17pm shift
            pickup_time = pickup_time.replace(hour=13, minute=0, second=0)
        elif pickup_time.hour > 17: # after 17pm => next day 8am-12pm shift
            pickup_time = pickup_time + timedelta(days=1)
            pickup_time = pickup_time.replace(hour=8, minute=0, second=0)
        next_available_shifts = self.env['planning.slot'].search([('state', '=', 'published'), ('role_id', '=', self.zone_id.role_id.id), 
                                                                 ('end_datetime', '>', pickup_time)], order='start_datetime asc')
        if next_available_shifts:
            index = 0
            # find next shift if current shift is full
            shift_transports = self.env['shipping.order.transport'].search([('shift_id', '=', next_available_shifts[index].id), ('state', 'in', ['new', 'in_progress'])])
            while len(shift_transports) > MAX_TRANSPORTS_PER_SHIFT and index < len(next_available_shifts):
                index += 1
                shift_transports = self.env['shipping.order.transport'].search([('shift_id', '=', next_available_shifts[index].id), ('state', 'in', ['new', 'in_progress'])])
            self.write({'shift_id': next_available_shifts[index].id })
        else:
            print(f"Can't find any available shift for {self.zone_id.name}")

    def create_tranfers(self):
        if self.type == "transit":
            transit_location = self.env['stock.location'].search([('name', 'ilike', 'Inter-warehouse transit')], limit=1)
            self.shipping_order_id.create_transfer(self.from_location, transit_location, self.type)
            self.shipping_order_id.create_transfer(transit_location, self.to_location, self.type)
        else:
            self.shipping_order_id.create_transfer(self.from_location, self.to_location, self.type)
        
    def create(self, vals):
        transport = super().create(vals)
        transport.create_tranfers()
        return transport