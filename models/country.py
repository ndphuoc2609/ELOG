from odoo import models, fields

class CountryProvince(models.Model):
    _name = 'country.province'
    _description = 'Vietnam Province Information'

    province = fields.Text(string='Province')
    city_district = fields.Text(string='City/District')
    code = fields.Text(string='Code')
    local_ship = fields.Text(string='Local Ship')