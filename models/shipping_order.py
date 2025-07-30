from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import random
import string
import ast


class ShippingOrder(models.Model):
    _name = 'shipping.order'
    _description = 'Shipping Order'
    _inherit = ['mail.thread']
    _rec_name = 'order_id'

    customer_name = fields.Char(string='Sender Name', required=True)
    customer_phone = fields.Char(string='Sender Phone', required=True)
    province_sender = fields.Text(string='Sender Province/City', required=True)
    district_sender = fields.Text(string='Sender District', required=True)
    from_address = fields.Text(string='Sender Address', required=True)
    create_order_date = fields.Datetime(string='Create Order Date', default=fields.Datetime.now)

    receiver_name = fields.Char(string='Receiver Name', required=True)
    receiver_phone = fields.Char(string='Receiver Phone', required=True)
    province_receiver = fields.Text(string='Receiver Province/City', required=True)
    district_receiver = fields.Text(string='Receiver District', required=True)
    to_address = fields.Text(string='Receiver Address', required=True)


    order_id = fields.Char(string='Order ID',unique=True,readonly=True)
    product = fields.Char(string='Product')
    customer_id = fields.Many2one('res.users', string='Customer', required=True)
    package_location = fields.Char(string='Package Location', compute='_compute_location', readonly=True, store=True)
    next_location = fields.Char(string='Next Location', compute='_compute_location', readonly=True, store=True)

    transport_ids = fields.One2many('shipping.order.transport', 'shipping_order_id')
    current_driver_name = fields.Char(string='Driver Name', compute='_compute_current_driver', readonly=True, store=True)
    current_driver_phone = fields.Char(string='Driver Phone', compute='_compute_current_driver', readonly=True, store=True)

    shipping_date = fields.Datetime(string='Shipping Date')
    from_latitude = fields.Char(string='From Latitude')
    from_longitude = fields.Char(string='From Longitude')
    to_latitude = fields.Char(string='To Latitude')
    to_longitude = fields.Char(string='To Longitude')
    ship_image = fields.Binary("Shipping Image")

    status = fields.Selection([
        ('new', 'New'),
        ('waiting_pickup', 'Waiting for Pickup'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('in_warehouse', 'In Warehouse'),
        ('waiting_delivery', 'Waiting for Delivery'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ], string='Status', default='new')
    current_transit = fields.Char(string='Current Transit')

    #product
    product_ids = fields.One2many('shipping.order.product', 'shipping_order_id', string='Products')
    total_weight = fields.Float(string='Total Weight (VND)', compute='_compute_total', readonly=True)
    total_shipment_value = fields.Float(string='Total Shipment Value (VND)', compute='_compute_total', readonly=True)


    #service
    pickup_type = fields.Selection([
        ('my_address', 'At my address'),
        ('pickup_address', 'Pickup address'),
        ('service_point', 'Bring to service point'),
        ('dhl_point', 'Select DHL service point'),
    ], string='Pick-up Type')
    pickup_address = fields.Text(string='Pickup Address')
    pickup_shift = fields.Char(string='Pickup Shift')
    dhl_service_point = fields.Char(string='DHL Service Point')
    pickup_note = fields.Text(string='Note for Pickup')

    # Delivery 
    partial_delivery = fields.Boolean(string='Partial Delivery')
    joint_inspection = fields.Boolean(string='Joint Inspection')

    # Fall Delivery & Return
    return_location = fields.Selection([
        ('service_point', 'At service point'),
        ('my_address', 'At my address'),
    ], string='Return Location')

    # Additional Services
    insurance = fields.Boolean(string='Insurance')
    additional_service_note = fields.Text(string='Additional Service Note')
    service_fee = fields.Float(string='Service Fee (VND)')

    shipping_fee = fields.Float(string='Shipping Fee (VND)')
    promotion_code = fields.Char(string='Promotion Code')
    promotion_discount = fields.Float(string='Promotion Discount (VND)')
    total_fee = fields.Float(string='Total Amount (VND)')
    estimated_pickup_date = fields.Date(string='Estimated Pickup Date')
    estimated_delivery_date = fields.Date(string='Estimated Delivery Date')

    all_locations = fields.Char()
    current_location_idx = fields.Integer(default=0)

    @property
    def all_location_ids(self):
        return ast.literal_eval(self.all_locations)

    def generate_unique_order_id(self):
        while True:
            order_id = ''.join(random.choices(string.digits, k=10))
            order_id = f"DHL{order_id}VN"

            if not self.search([('order_id', '=', order_id)]):
                return order_id
            
    def generate_locations(self, vals):
        wh_orig = self.env['stock.warehouse'].search([('name', 'ilike', vals['province_sender'].replace('Thành phố', '').replace('Tỉnh', '').strip())], limit=1)
        wh_dest = self.env['stock.warehouse'].search([('name', 'ilike', vals['province_receiver'].replace('Thành phố', '').replace('Tỉnh', '').strip())], limit=1)

        location_customers = self.env['stock.location'].search([('name', 'ilike', 'Customers')], limit=1)
        location_suppliers = self.env['stock.location'].search([('name', 'ilike', 'Vendors')], limit=1)
        
        location_orig = self.env['stock.location'].search(['&', ('warehouse_id', '=', wh_orig.id),('name', '=', 'Stock')], limit=1)
        location_dest = self.env['stock.location'].search(['&', ('warehouse_id', '=', wh_dest.id),('name', '=', 'Stock')], limit=1)

        locations = [location_suppliers, location_orig]
        if vals['province_sender'] != vals['province_receiver']:
            locations += [location_dest, location_customers]
        else:
            locations += [location_customers]

        locations = [location.id for location in locations]
        return str(locations)
    
    def create_transport_auto(self):
        # mark all current transports as completed
        for transport in self.transport_ids:
            if transport.state == 'new' or transport.state == 'in_progress':
                transport.write({'state': 'completed'})

        # create new transport based on current location
        if self.current_location_idx == 0:
            transport_type = 'pickup'
        elif self.current_location_idx == len(self.all_location_ids) - 2:
            transport_type = 'delivery'
        else:
            transport_type = 'transit'
        transport = self.env['shipping.order.transport'].create({
            'shipping_order_id': self.id,
            'type': transport_type,
            'from_location': self.all_location_ids[self.current_location_idx],
            'to_location': self.all_location_ids[self.current_location_idx+1],
        })
        transport.find_shift()

    def create_transfer(self, from_location, to_location, transfer_type):
        if transfer_type == "pickup":
            warehouse = to_location.warehouse_id
            name = "Receipts"
        elif transfer_type == "delivery":
            warehouse = from_location.warehouse_id
            name = "Delivery Orders"
        else: # transit
            if from_location.name == "Inter-warehouse transit":
                warehouse = to_location.warehouse_id
            else:
                warehouse = from_location.warehouse_id
            name = "Internal Transfers"
            
        picking_type = self.env['stock.picking.type'].search([('warehouse_id', '=', warehouse.id), ('name', '=', name)], limit=1)

        # check if transfer already exist
        existing_transfer = self.env['stock.picking'].search([('origin', '=', self.order_id), ('location_id', '=', from_location.id), ('location_dest_id', '=', to_location.id), 
                                                              ('state', 'in', ['assigned', 'confirmed']), ('picking_type_id', '=', picking_type.id)])
        if existing_transfer:
            return
        
        picking = self.env['stock.picking'].create({
            'location_id': from_location.id,
            'location_dest_id': to_location.id,
            'picking_type_id': picking_type.id,
            'origin': self.order_id,
        })
        
        for product in self.product_ids:
            self.env['stock.move'].create({
                'name': "test_stock",
                'location_id': from_location.id,
                'location_dest_id': to_location.id,
                'product_id': product.product_id.id,
                'product_uom': product.product_id.uom_id.id,
                'product_uom_qty': 1.0,
                'picking_id': picking.id,
            })

        picking.action_confirm()
        picking.action_assign()

    def create(self, vals):
        vals['order_id'] = self.generate_unique_order_id()
        vals['all_locations'] = self.generate_locations(vals)
        if vals['from_latitude'] == '':
            location_id = ast.literal_eval(vals['all_locations'])[1]
            location = self.env['stock.location'].browse(location_id)
            vals['from_latitude'] = location.warehouse_id.latitude
            vals['from_longitude'] = location.warehouse_id.longitude
        if vals['to_latitude'] == '':
            location_id = ast.literal_eval(vals['all_locations'])[-2]
            location = self.env['stock.location'].browse(location_id)
            vals['to_latitude'] = location.warehouse_id.latitude
            vals['to_longitude'] = location.warehouse_id.longitude
        return super(ShippingOrder, self).create(vals)
    
    def get_status_label(self):
        return dict(self._fields['status'].selection).get(self.status)

    def formater_money(self,value):
        return "{:,.0f}".format(value) if value else "0"
    
    def write(self, vals):
        transports = vals.get('transport_ids')
        if transports:
            for i, transport in enumerate(transports):
                if transport[-1]:
                    type = transport[-1].get('type')
                    state = transport[-1].get('state')
                    from_location = transport[-1].get('from_location')
                    to_location = transport[-1].get('to_location')

                    if not type:
                        type = self.transport_ids[i].type

        return super().write(vals)

    # @api.model
    # def _search_driver_pickup(self, operator, value):
    #     return ['|', ('driver_pickup_id.name', operator, value), ('driver_pickup_id.phone', operator, value)]
    
    def action_view_package_delivery(self):
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        pickings = self.env['stock.picking'].search([('origin', '=', self.order_id)])
        action['domain'] = [('id', 'in', pickings.ids)]
        return action
    
    def _compute_total(self):
        for order in self:
            order.total_weight = sum([product.weight for product in order.product_ids])
            order.total_shipment_value = sum([product.shipment_value for product in order.product_ids])
    
    @api.depends('current_location_idx')
    def _compute_location(self):
        for order in self:
            current_location = self.env['stock.location'].browse(order.all_location_ids[order.current_location_idx])
            order.package_location = current_location.complete_name
            next_location = self.env['stock.location'].browse(order.all_location_ids[order.current_location_idx+1]) if order.current_location_idx < len(order.all_location_ids) - 1 else current_location
            order.next_location = next_location.complete_name

    @api.depends("transport_ids")
    def _compute_current_driver(self):
        for order in self:
            order.current_driver_name = ""
            order.current_driver_phone = ""
            for transport in order.transport_ids:
                if transport.state == "new" or transport.state == "in_progress":
                    order.current_driver_name = transport.driver_id.name
                    order.current_driver_phone = transport.driver_id.phone
                    break
            

class StockPicking(models.Model):
    _inherit = 'stock.picking'
        
    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for picking in self:
            location_orig = picking.location_id.complete_name
            location_dest = picking.location_dest_id.complete_name
            order = self.env['shipping.order'].search([('order_id', '=', picking.origin)], limit=1)
            if order:
                if 'Customers' in location_dest:
                    order.write({"status": "waiting_delivery"})
                    order.message_post(body=f"The order will arrive soon, please keep an eye on your phone")
                elif 'Inter-warehouse transit' in location_dest:
                    warehouse_orig = picking.location_id.warehouse_id.name
                    order.write({"status": "in_transit"})
                    order.message_post(body=f"The order has left {warehouse_orig} warehouse")
                else:
                    warehouse_dest = picking.location_dest_id.warehouse_id.name
                    order.write({"status": "in_warehouse", "current_location_idx": order.current_location_idx + 1})
                    order.message_post(body=f"The order has arrived at {warehouse_dest} warehouse")
                    order.create_transport_auto()

        return res
    
class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    def write(self, vals):
        resource_id = vals.get("resource_id")
        shipping_orders = []
        if resource_id:
            new_driver = self.env['resource.resource'].browse(resource_id).user_id
            transports = self.env['shipping.order.transport'].search([('shift_id', '=', self.id)])
            for transport in transports:
                transport.notify_driver(new_driver)
                shipping_orders.append(transport.shipping_order_id)
        result = super().write(vals)
        for order in shipping_orders:
            order._compute_current_driver()
        return result