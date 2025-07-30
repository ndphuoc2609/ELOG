from . import models
from . import controllers
from . import wizard

from odoo import api, SUPERUSER_ID
from datetime import datetime
import math

def calculate_square_corners(center_lat, center_lon, side_length_km=100):
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert side length from kilometers to degrees
    side_length_deg = side_length_km / R * (180 / math.pi)
    
    # Calculate half side length in degrees
    half_side_length_deg = side_length_deg / 2
    
    # Calculate the corners
    corners = [
        [center_lat + half_side_length_deg, center_lon - half_side_length_deg],
        [center_lat + half_side_length_deg, center_lon + half_side_length_deg],
        [center_lat - half_side_length_deg, center_lon + half_side_length_deg],
        [center_lat - half_side_length_deg, center_lon - half_side_length_deg]
    ]
    
    return str(corners)

def _elog_post_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # enable free sign-up
    websites = env['website'].search([])
    for website in websites:
        website.write({'auth_signup_uninvited': 'b2c'})

    # change sign up title
    signup_view = env['ir.ui.view'].search([('key', '=', 'auth_signup.signup')], limit=1)
    signup_view.write({'name': 'Sign up'})

    # enable inter_transit location
    inter_transit = env['stock.location'].search([('active', '=', False), ('name', '=', 'Inter-warehouse transit')], limit=1)
    inter_transit.write({'active': True})

    # create logistic department
    department = env['hr.department'].create({'name': 'Logistic'})

    # create driver job
    job = env['hr.job'].create({'name': 'Driver', 'department_id': department.id})

    # create test drivers
    warehouses = env['stock.warehouse'].search([])
    for i, warehouse in enumerate(warehouses):
        if warehouse.latitude:
            # create working zone
            zone = env['shipping.zone'].create({
                'name': f'{warehouse.name} zone',
                'area': calculate_square_corners(float(warehouse.latitude), float(warehouse.longitude)),
            })

            # create user
            user = env['res.users'].create({
                'name': f'driver {warehouse.name}',
                'login': f'driver.{warehouse.code.lower()}@dhl.com',
                'password': '123',
                'phone': f'09111111{i:02}',
                'tz': 'Asia/Saigon',
                'groups_id': [(4, env.ref('base.group_user').id)]
            })

            # create employeee
            employee = env['hr.employee'].create({
                'name': user.name,
                'work_phone': user.phone,
                'work_email': user.login,
                'address_home_id': user.partner_id.id,
                'department_id': department.id,
                'job_id': job.id,
                'user_id': user.id,
                'default_planning_role_id': zone.role_id.id,
                'warehouse_id': warehouse.id,
                'driver_latitude': str(float(warehouse.latitude) + 0.1),
                'driver_longitude': warehouse.longitude,
            })

            # create shifts
            day_shift = env['planning.slot'].create({
                'start_datetime': datetime(2025, 6, 1, 1, 0, 0),
                'end_datetime': datetime(2025, 6, 1, 5, 0, 0),
                'resource_id': employee.resource_id.id,
                'repeat': True,
                'repeat_type': 'forever',
                'repeat_interval': 1,
                'repeat_unit': 'day'
            })
            
            night_shift = env['planning.slot'].create({
                'start_datetime': datetime(2025, 6, 1, 6, 0, 0),
                'end_datetime': datetime(2025, 6, 1, 10, 0, 0),
                'resource_id': employee.resource_id.id,
                'repeat': True,
                'repeat_type': 'forever',
                'repeat_interval': 1,
                'repeat_unit': 'day'
            })