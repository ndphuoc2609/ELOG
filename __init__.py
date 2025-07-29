from . import models
from . import controllers
from . import wizard

from odoo import api, SUPERUSER_ID
from datetime import datetime

def _elog_post_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # enable free sign-up
    websites = env['website'].search([])
    for website in websites:
        website.write({'auth_signup_uninvited': 'b2c'})

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
                'latitude': str(float(warehouse.latitude) - 0.1),
                'longitude': warehouse.longitude,
                'radius': 100,
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