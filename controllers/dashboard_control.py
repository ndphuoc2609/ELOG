from odoo import http
from odoo.http import request
from datetime import datetime, timedelta

class ShippingDashboardController(http.Controller):
    @http.route('/custom_website/shipping_dashboard_stats', type='json', auth='user')
    def shipping_dashboard_stats(self, period="1", warehouse_name=None):
        period = int(period) if period else 1
        date_from = (datetime.now() - timedelta(days=period)).strftime('%Y-%m-%d')
        domain = [('create_date', '>=', date_from)]

        if warehouse_name:
            domain.append(('province_sender', 'ilike', warehouse_name))
            domain.append(('province_receiver', 'ilike', warehouse_name))

        ShippingOrder = request.env['shipping.order'].sudo().search(domain)
        total_shipments = ShippingOrder.search_count(domain)
        waiting_pickup = len([order for order in ShippingOrder if order.status in ('waiting_pickup','new','picked_up')])
        waiting_delivery = len([order for order in ShippingOrder if order.status in ('waiting_delivery','in_transit','delivered')])
        total_fees = sum(order.total_fee for order in ShippingOrder)

        status_list = [
            ('new', 'New'),
            ('waiting_pickup', 'Waiting Pickup'),
            ('picked_up', 'Picked Up'),
            ('in_transit', 'In Transit'),
            ('waiting_delivery', 'Waiting Delivery'),
            ('delivered', 'Delivered'),
            ('failed', 'Failed'),
            ('canceled', 'Canceled'),
        ]

        status_labels = [label for code, label in status_list]
        status_values = [
            len([order for order in ShippingOrder if order.status == code])
            for code, label in status_list
        ]

        background_colors = [
            '#f39c12', '#00a65a', '#f56954', '#00c0ef',
            '#3c8dbc', '#d2d6de', '#8e44ad', '#e67e22'
        ]
        order_status_chart = {
            "labels": status_labels,
            "datasets": [{
                "label": "Số lượng đơn",
                "data": status_values,
                "backgroundColor": background_colors,
                "hoverOffset": 4,
            }]
        }

        return {
            "total_shipments": total_shipments,
            "pickup_progress": waiting_pickup,
            "delivery_progress": waiting_delivery,
            "total_fees": f"{total_fees:,.0f}",
            "order_status_chart": order_status_chart,
        }
    
    @http.route('/custom_website/get_warehouses', type='json', auth='user')
    def get_warehouses(self):
        warehouses = request.env['stock.warehouse'].sudo().search_read([], ['id', 'name'])
        return warehouses