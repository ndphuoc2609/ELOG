import json
import odoo
from odoo import http
from odoo.http import request
from datetime import datetime
from .decorators import handle_errors
import base64
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

CORS = '*'
class ShippingAPI(http.Controller):

    @staticmethod
    def serialize(obj):
        if isinstance(obj, datetime):
            return obj.isoformat() 
        raise TypeError("Type not serializable")

    @http.route('/shipping/authenticate', type='http', auth="none",
                methods=['POST'], csrf=False, save_session=True, cors="*")
    @handle_errors
    def get_token(self):
        byte_string = request.httprequest.data
        data = json.loads(byte_string.decode('utf-8'))
        username = data['username']
        password = data['password']
        try:
            user_id = request.session.authenticate(request.db, username, password)
            request.session.db = request.db
            registry = odoo.modules.registry.Registry(request.db)
            with registry.cursor() as cr:
                env = odoo.api.Environment(cr, request.session.uid, request.session.context)
                http.root.session_store.rotate(request.session, env)
                request.future_response.set_cookie(
                    'session_id', request.session.sid,
                    max_age=http.SESSION_LIFETIME, httponly=True
                )
                session_info = env['ir.http'].session_info()
                driver = env.user.employee_id
                warehouse = {
                    'latitude': driver.warehouse_id.latitude,
                    'longitude': driver.warehouse_id.longitude,
                    'address': driver.warehouse_id.address
                }
                payload = {
                    'user_id': user_id,
                    'username': username,
                    'name': session_info['name'],
                    'password': password,
                    'session_id': request.session.sid,
                    'warehouse': warehouse,
                }
                return request.make_response(json.dumps({
                    "data": payload,
                    "messages": "User Validated",
                }), headers={'Content-Type': 'application/json'})
        except Exception as e:
            msg = str(e)
            if msg == "Access Denied":
                msg = "Wrong login/password"
            return request.make_response(json.dumps({"message": msg}), headers={'Content-Type': 'application/json'}, status=401)
    
    @http.route('/shipping/push_token', type='http', auth="user", methods=['POST'], csrf=False, cors="*")
    @handle_errors
    def update_push_token(self):
        data = json.loads(request.httprequest.data.decode('utf-8'))
        push_token = data.get('push_token')

        user = request.env.user
        user.write({'push_token': push_token})
        return request.make_response(json.dumps({"message": f"Push token {push_token} updated successfully"}, default=ShippingAPI.serialize), headers={'Content-Type': 'application/json'})

    @http.route('/shipping/order_info', type='http', auth="user", methods=['GET'], csrf=False, cors="*")
    @handle_errors
    def get_order_info(self):
        driver = request.env.user.employee_id
        
        transports = request.env['shipping.order.transport'].sudo().search([('shift_id.employee_id', '=', driver.id)])
        transport_data = []
        for transport in transports:
            order = transport.shipping_order_id
            products_data = [{
                'product_name': product.product_name,
                'weight': product.weight,
                'dimensions': product.dimensions,
                'shipment_value': product.shipment_value,
                } for product in order.product_ids]
            transport_data.append({
                'transport_id': transport.id,
                'order_id': order.order_id,
                'pickup_note': order.pickup_note,
                'customer_name': order.customer_name,
                'customer_phone': order.customer_phone,
                'receiver_name': order.receiver_name,
                'receiver_phone': order.receiver_phone,
                'from_address': transport.from_address,
                'to_address': transport.to_address,
                'create_order_date': order.create_order_date,
                'products': products_data,
                'total_fee': order.total_fee,
                'status': order.status,
                'type': transport.type,
                'transport_state': transport.state,
                'from_latitude': transport.from_latitude,
                'from_longitude': transport.from_longitude,
                'to_latitude': transport.to_latitude,
                'to_longitude': transport.to_longitude,
                'shift_end': transport.shift_end,
            })
        return request.make_response(json.dumps(transport_data, default=ShippingAPI.serialize), headers={'Content-Type': 'application/json'})

    def add_text_to_image(self, base64_str, text):
        # Decode the base64 string to bytes
        image_data = base64.b64decode(base64_str)
        
        # Create an image from the bytes
        image = Image.open(BytesIO(image_data))

        # Initialize ImageDraw
        draw = ImageDraw.Draw(image)
        
        # Define the font and size
        font_size = 20
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
        
        # Get image dimensions
        width, height = image.size
        
        # Define text position (bottom left)
        text_position = (10, height - font_size * 3 - 20)
        
        # Add text to image
        draw.text(text_position, text, font=font, fill="white")
        
        # Save image to bytes
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        
        # Encode image to base64
        base64_image_with_text = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return base64_image_with_text
    
    def convert_to_dms(self, lat, lon):
        def to_dms(deg):
            d = int(deg)
            m = int((deg - d) * 60)
            s = (deg - d - m / 60) * 3600
            return d, m, s

        lat_d, lat_m, lat_s = to_dms(abs(lat))
        lon_d, lon_m, lon_s = to_dms(abs(lon))

        lat_hemisphere = 'N' if lat >= 0 else 'S'
        lon_hemisphere = 'E' if lon >= 0 else 'W'

        return f"{lat_d}°{lat_m}'{lat_s:.2f}\"{lat_hemisphere}, {lon_d}°{lon_m}'{lon_s:.2f}\"{lon_hemisphere}"
    
    @http.route('/shipping/update_status', type='http', auth="user", methods=['POST'], csrf=False, cors="*")
    @handle_errors
    def update_status(self):
        #handle data
        data = json.loads(request.httprequest.data.decode('utf-8'))
        order_id = data.get('order_id')
        order_status = data.get('order_status')
        image_data = data.get('ship_image')
        failed_note = data.get('note')
        
        #hanlde function
        order = request.env['shipping.order'].sudo().search([('order_id', '=', order_id)], limit=1)
        message_body = f'Change status to {order_status}'
        attachment_ids = []
        if order_status:
            current_transport = [transport for transport in order.transport_ids if transport.state == 'in_progress'][0]
            order_vals = {'status': order_status}
            if order_status == "picked_up":
                message_body = 'The order has been picked up'
            elif order_status == 'delivered':
                message_body = 'The order has been delivered'
                current_transport.write({'state': 'completed'})
                order_vals.update({'current_location_idx': order.current_location_idx + 1})
            elif order_status == 'failed':
                if order.status == 'waiting_pickup':
                    message_body = 'Failed to pick up the order'
                else:
                    message_body = 'Failed to deliver the order'
                current_transport.write({'state': 'failed'})
                
            elif order_status == 'canceled':
                message_body = 'The order has been canceled'
                current_transport.write({'state': 'failed'})

            order.write(order_vals)

        if failed_note:
            message_body += "\nNote: " + failed_note

        #handle image
        if image_data:
            user = request.env.user
            location = data.get('driver_location')
            location_string = self.convert_to_dms(location['latitude'], location['longitude'])
            current_time = datetime.now()
            # Format the current time as a string
            time_string = current_time.strftime("%Y-%m-%d %H:%M:%S")
            text = time_string + "\n" + location_string + "\n" + order_id + " " + user.name
            new_image = self.add_text_to_image(image_data, text)
            order.write({'ship_image': new_image})
            attachment = request.env['ir.attachment'].sudo().create({
                'name': 'image.jpg',
                'datas': new_image,
                'res_model': order._name,
                'res_id': order.id,
            })
            attachment_ids.append(attachment.id)
        order.message_post(body=(message_body.replace('\n', '<br/>')), attachment_ids=attachment_ids)
        
        return request.make_response(json.dumps({"message": "Order status updated successfully"}, default=ShippingAPI.serialize), headers={'Content-Type': 'application/json'})
    
    @http.route('/shipping/update_driver', type='http', auth="user", methods=['POST'], csrf=False, cors="*")
    @handle_errors
    def update_driver(self):
        data = json.loads(request.httprequest.data.decode('utf-8'))
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        driver = request.env.user.employee_id

        if latitude and longitude:
            driver.write({'driver_latitude': latitude, 'driver_longitude': longitude, 'driver_last_updated': datetime.now()})

        return request.make_response(json.dumps({"message": f"Driver updated successfully"}, default=ShippingAPI.serialize), headers={'Content-Type': 'application/json'})

    @http.route('/shipping/update_transports', type='http', auth="user", methods=['POST'], csrf=False, cors="*")
    @handle_errors
    def update_transports(self):
        data = json.loads(request.httprequest.data.decode('utf-8'))
        ids = data.get('ids')
        state = data.get('state')

        transports = request.env['shipping.order.transport'].sudo().search([('id', 'in', ids)])
        for transport in transports:
            transport.write({'state': state})

        return request.make_response(json.dumps({"message": f"Transports updated successfully"}, default=ShippingAPI.serialize), headers={'Content-Type': 'application/json'})