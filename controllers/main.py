from odoo import http
import requests
import base64
import datetime
import urllib3
import json
import pytz
from markupsafe  import Markup
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
import locale
import pdfkit
import io
import zipfile
import re

locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')

urllib3.disable_warnings()

class CustomController(http.Controller):
    @http.route('/shipping_order', type='http', auth='user', website=True)
    def shipping_webform(self, **kwargs):
        user = http.request.env.user
        customer_name = user.partner_id.name if user.partner_id else ''
        customer_phone = user.partner_id.phone if user.partner_id else ''
        return http.request.render('custom_website.shipping_order_template', {
            'customer_name': customer_name,
            'customer_phone': customer_phone,
            'from_address':'DHL',
            'shipping_fee': 0,
            'promotion_discount': 5000,
            'total_fee': 0,
            'estimated_pickup_date': datetime.datetime.now().date(),
            'estimated_delivery_date': datetime.datetime.now().date() + datetime.timedelta(days=3),
        })

    # @http.route('/create/shipping_order', type='http', auth='public', website=True)
    # def create_shipping_order(self, **kwargs):
    #     user = http.request.env.user
    #     kwargs.update({'customer_id':user.id})
    #     shipping_order = http.request.env['shipping.order'].sudo().create(kwargs)
    #     return http.request.redirect('/tracking_order')
    
    @http.route('/create/shipping_order', type='http', auth='user', website=True, csrf=False)
    def create_shipping_order(self, **post):
        user = http.request.env.user

        order_vals = {
            'customer_id': user.id,
            'customer_name': post.get('customer_name'),
            'customer_phone': post.get('customer_phone'),
            'province_sender': post.get('province_sender'),
            'district_sender': post.get('district_sender'),
            'from_address': post.get('from_address'),
            'receiver_name': post.get('receiver_name'),
            'receiver_phone': post.get('receiver_phone'),
            'province_receiver': post.get('province_receiver'),
            'district_receiver': post.get('district_receiver'),
            'to_address': post.get('to_address'),
            'from_latitude': post.get('from_latitude'),
            'from_longitude': post.get('from_longitude'),
            'to_latitude': post.get('to_latitude'),
            'to_longitude': post.get('to_longitude'),
            'partial_delivery': post.get('partial_delivery') == 'on',
            'joint_inspection': post.get('joint_inspection') == 'on',
            'insurance' : post.get('insurance') == 'on',
            'return_location': post.get('return_location'),
            'additional_service_note': post.get('additional_service_note'),
            'promotion_code': post.get('promotion_code',''),
            'promotion_discount': float(post.get('promotion_discount')) if post.get('promotion_discount') else 0,
            'total_fee': post.get('total_fee'),
            'shipping_fee': post.get('shipping_fee'),
            'service_fee': post.get('insurance_fee'),
        }
        
        shipping_order = http.request.env['shipping.order'].sudo().create(order_vals)
        Product = http.request.env['shipping.order.product']
        product_inventory = http.request.env['product.product']
        index = 1

        data_prods = []

        while True:
            product_name = post.get(f'product_name_{index}',False)
            if not product_name:
                break

            data_prod = product_inventory.sudo().create({
                'name': f"[{shipping_order.order_id}] {product_name}",
                'type': 'product',
                'barcode': f'{shipping_order.order_id}{index}',
                'categ_id': http.request.env.ref('product.product_category_all').id,})
            data_prods.append(data_prod)
            
            product_order = Product.sudo().create({
                'shipping_order_id': shipping_order.id,
                'product_name': product_name,
                'weight': post.get(f'weight_{index}'),
                'dimensions': post.get(f'dimensions_{index}'),
                'shipment_value': int(re.sub(r'[^\d]', '', post.get(f'shipment_value_{index}', '0'))),
                'product_id': data_prod.id,
            })

            index += 1
        
        shipping_order.create_transport_auto()
        return http.request.redirect('/tracking_order/%d' % shipping_order.id)

    @http.route('/', type='http', auth='public', website=True)
    def main_page(self, **kwargs):
        return http.request.render('custom_website.main_page_template', {})

    @http.route('/dashboard', type='http', auth='public', website=True)
    def dashboard(self, **kwargs):
        user = http.request.env.user
        orders = http.request.env['shipping.order'].sudo().search([('customer_id', '=', user.id)],order='create_date desc')
        for order in orders:
            order.create_order_date = order.create_date + datetime.timedelta(hours=7)
        
        count_all = len(orders)
        count_delivered = len(orders.filtered(lambda o: o.status == 'delivered'))
        count_new = len(orders.filtered(lambda o: o.status == 'new'))
        count_in_transit = len(orders.filtered(lambda o: o.status in ['waiting_pickup', 'picked_up', 'in_transit', 'waiting_delivery']))
        count_canceled = len(orders.filtered(lambda o: o.status == 'canceled'))
        
        return http.request.render('custom_website.shipping_statistics_template', {
            'orders': orders,
            'count_all': count_all,
            'count_new': count_new,
            'count_delivered': count_delivered,
            'count_in_transit': count_in_transit,
            'count_canceled': count_canceled,
        })

    @http.route('/tracking_order', type='http', auth='public', website=True)
    def tracking_order(self, **kwargs):
        user = http.request.env.user
        orders = http.request.env['shipping.order'].sudo().search([('customer_id', '=', user.id)])
        return http.request.render('custom_website.tracking_order_template', {
            'orders': orders,
        })
    
    @http.route('/tracking_order/status/<string:status>', type='http', auth='user', website=True)
    def orders_by_status(self, status, **kwargs):
        user = http.request.env.user
        orders = http.request.env['shipping.order'].sudo().search([
            ('customer_id', '=', user.id),
            ('status', '=', status)
        ])
        return http.request.render('custom_website.orders_by_status_template', {
            'orders': orders,
            'status': status.capitalize()
        })

    @http.route('/tracking_order/<int:order_id>', type='http', auth='user', website=True)
    def order_detail(self, order_id, **kwargs):
        order = http.request.env['shipping.order'].sudo().browse(order_id)
        products = http.request.env['shipping.order.product'].sudo().search([('shipping_order_id', '=', order.id)])

        logs = order.message_ids
        def handle_date(date_input):
            utc_dt = pytz.utc.localize(date_input)
            local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            local_dt = utc_dt.astimezone(local_tz)
            return local_dt.strftime('%Y-%m-%d %H:%M:%S')

        log_data = [{'body': log.body, 'date': handle_date(log.date)} for log in order.message_ids]

        return http.request.render('custom_website.order_detail_template', {
            'order': order,
            'products': products,
            'logs': log_data,
        })
    
    @http.route('/list_order', type='http', auth='user', website=True)
    def list_order(self, **kwargs):
        user = http.request.env.user
        orders = http.request.env['shipping.order'].sudo().search([('customer_id', '=', user.id)])
        return http.request.render('custom_website.list_order_template', {
            'orders': orders,
        })
    
    @http.route('/cancel_order/<int:order_id>', type='http', auth='user', website=True)
    def cancel_order(self, order_id, **kwargs):
        order = http.request.env['shipping.order'].sudo().browse(order_id)
        order.write({'status': 'canceled'})
        return http.request.redirect('/tracking_order')
    
    @http.route('/print_order/<int:order_id>', type='http', auth='user', website=True)
    def print_order(self, order_id, **kwargs):
        order = http.request.env['shipping.order'].sudo().browse(order_id)
        if not order:
            return http.request.not_found("Order not found")
        
        product_orders = http.request.env['shipping.order.product'].sudo().search([
            ('shipping_order_id', '=', order.id)
        ])
        
        pieces = 0
        list_product=[]
        for p in product_orders:
            pieces = pieces + 1
            list_product.append({
                'piece': pieces,
                'name': p.product_name,
                'barcode': p.barcode,
                'weight': p.weight,
                'dimensions': p.dimensions,
                'shipment_value': "{:,.0f}".format(p.shipment_value),
            })

        def mask_data(data, visible_chars, suffix=True):
            if not data: return ""
            return ("****" + (data[-visible_chars:] if suffix else data[:visible_chars]))
        
        sender_info = {
            'name': mask_data(order.customer_name, 5),
            'phone': mask_data(order.customer_phone, 4),
            'address': mask_data(order.from_address, 40),
        }
        receiver_info = {
            'name': mask_data(order.receiver_name, 5),
            'phone': mask_data(order.receiver_phone, 4),
            'address': mask_data(order.to_address, 40),
        }

        # return http.request.render('custom_website.print_order_template', {
        #     'order': order,
        #     'sender_info': sender_info,
        #     'receiver_info': receiver_info,
        #     'pieces': pieces,
        #     'product': [product for product in list_product],
        #     'order_date': order.create_order_date + datetime.timedelta(hours=7),
        #     'total_fee': f"{order.total_fee:,.0f}",
        # })
        
        # Tạo file ZIP trong bộ nhớ
        full_html = ""
        for i, product in enumerate(list_product):
            # Render template cho từng sản phẩm
            html = http.request.env['ir.ui.view'].sudo()._render_template(
                'custom_website.print_order_template',
                {
                    'order': order,
                    'sender_info': sender_info,
                    'receiver_info': receiver_info,
                    'pieces': len(list_product),
                    'product': [product],
                    'order_date': order.create_order_date + datetime.timedelta(hours=7),
                    'total_fee': f"{order.total_fee:,.0f}",
                }
            )
            
            # Thêm page break sau mỗi sản phẩm (trừ sản phẩm cuối cùng)
            full_html += html
            if i < len(list_product) - 1:
                full_html += Markup('<div style="page-break-before: always;"></div>')

        # Tạo PDF từ HTML đã gom
        options = {
            'page-width': '105.6mm',
            'page-height': '203.2mm',
            'encoding': "UTF-8",
            'margin-top': '0mm',
            'margin-bottom': '0mm',
            'margin-left': '0mm',
            'margin-right': '0mm',
        }
        
        pdf = pdfkit.from_string(full_html, False, options=options)
        pdf_filename = f"order_{order.order_id}_all_packages.pdf"
        
        return http.request.make_response(pdf, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'attachment; filename="{pdf_filename}"')
        ])

    @http.route('/get_order_logs/<string:order_id>', type='http', auth='public', methods=['GET'])
    def get_order_logs(self, order_id):

        @staticmethod
        def handle_date(time_input):
            utc_dt = pytz.utc.localize(time_input)
            local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            local_dt = utc_dt.astimezone(local_tz)
            return local_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Tìm đơn hàng theo order_id
        order = http.request.env['shipping.order'].sudo().search([('order_id', '=', order_id)], limit=1)
        
        if not order:
            return http.request.make_response('{"logs": []}', headers=[('Content-Type', 'application/json')])
        
        # Lấy thông tin người gửi và người nhận
        sender_info = {
            'name': '****' + order.customer_name[-5:],
            'phone': '****' + order.customer_phone[-4:],
            'address': '****' + order.from_address[-40:],
        }
        receiver_info = {
            'name': '****' + order.receiver_name[-5:],
            'phone': '****' + order.receiver_phone[-4:],
            'address': '****' + order.to_address[-40:],
        }
        
        # Lấy logs từ đơn hàng với date
        logs = [{'body': log.body, 'date': handle_date(log.date)} for log in order.message_ids]
        
        response_data = {
            'logs': logs,
            'sender': sender_info,
            'receiver': receiver_info,
            'estimated_delivery_date': handle_date(datetime.datetime.combine(order.estimated_delivery_date, datetime.datetime.min.time())) if order.estimated_delivery_date else '',
        }
        
        return http.request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

    @http.route('/get_provinces', type='json', auth='public', methods=['POST'], csrf=False)
    def get_provinces(self):
        provinces = http.request.env['country.province'].sudo().search([])
        province_list = [{'id': p.province, 'name': p.province} for p in provinces]
        province_list = list({v['id']: v for v in province_list}.values())
        return province_list
    
    @http.route('/get_city_districts', type='json', auth='public', methods=['POST'], csrf=False)
    def get_city_districts(self, **kwargs):
        province_name = kwargs.get('province_name')
        records = http.request.env['country.province'].sudo().search([('province', '=', province_name)])
        city_districts = list({r.city_district for r in records if r.city_district})
        return [{'id': name, 'name': name} for name in city_districts]


class AuthVerifyController(http.Controller):
    @http.route('/verify', type='http', auth="public", website=True)
    def verify_account(self, uid=None, token=None, **kwargs):
        user = http.request.env['res.users'].sudo().browse(int(uid))
        if user.verification_token != token:
            return "Invalid Token!"
        user.write({'is_verified': True})
        return http.request.redirect('/web/login?message=Your email address was successfully verified.')

    @http.route('/resend', type='http', auth="public", website=True)
    def resend_verification(self, uid=None, **kwargs):
        user = http.request.env['res.users'].sudo().browse(int(uid))
        if user.is_verified:
            return http.request.redirect('/web/login?message=Your email adress is already verified.')
        user.generate_verification_token()
        return http.request.redirect('/web/login?message=A new invitaion have been sent to your email.')

from odoo.addons.web.controllers.home import Home

class AuthVerifyHome(Home):
    @http.route()
    def web_login(self, *args, **kwargs):
        if request.httprequest.method == 'POST':
            login = request.params['login']
            user = request.env["res.users"].sudo().search(['|', ('email', '=', login), ('phone', '=', login)])
            if user.has_group('base.group_portal') and not user.is_verified:
                return request.redirect(f"/web/login?error=Please verify your account email first. <a href='/resend?uid={user.id}'>Resend verification</a>")
            # if user.role == 'driver':
            #     return request.redirect(f"/web/login?error=Wrong login/password")
        return super(AuthVerifyHome, self).web_login(*args, **kwargs)
