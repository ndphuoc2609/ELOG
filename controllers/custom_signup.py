from odoo.addons.auth_signup.controllers.main import AuthSignupHome
import werkzeug
from werkzeug.urls import url_encode
from odoo.http import request
from odoo.exceptions import UserError
from odoo import http, tools, _
import logging
import random
import string
import datetime
import re
import uuid

_logger = logging.getLogger(__name__)

class CustomSignup(AuthSignupHome):

    @http.route('/web/signup/get_otp', type='json', auth='public', methods=['POST'])
    def get_otp(self, phone):
        if not re.match(r'^\d{10}$', phone):
            return {'status': 'error', 'message': 'Phone number must be exactly 10 digits'}
        creation_time = request.session.get('otp_creation')
        if creation_time:
            # Can only get new otp every 15s
            time_until_new_code = creation_time + datetime.timedelta(seconds=15) - datetime.datetime.now()
            time_until_new_code = int(time_until_new_code.total_seconds())
            if time_until_new_code > 0:
                return {'status': 'error', 'message': f'Please wait for {time_until_new_code} seconds before you can get a new code'}
        # Generate a random OTP code
        otp_code = ''.join(random.choices(string.digits, k=6))
        
        # Save the OTP code and creation time in the session
        creation_time = datetime.datetime.now()
        request.session['otp_phone'] = phone
        request.session['otp_code'] = otp_code
        request.session['otp_creation'] = creation_time
        
        # Testing for phone number not starts with "0"
        if not phone.startswith("0"):
            return {'status': 'success', 'message': f'OTP code sent to your phone', 'otp': otp_code}
        
        # Send the OTP code to the user's phone
        response = request.env["res.users"].sudo().send_sms(otp_code, phone)
        if response.status_code != 201:  # 201 Created is the success status code for Twilio message creation
            error_response = response.json()
            return {'status': 'error', 'message': error_response['message']}
        
        return {'status': 'success', 'message': f'OTP code sent to your phone', 'otp': otp_code}
    
    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        res = super().web_auth_signup(*args, **kw)
        # If user register successful => send email and logout
        if request.httprequest.method == 'POST' and request.session.uid:
            user = request.env.user
            user.generate_verification_token()
            request.session.logout()
            return request.redirect('/web/login?message=Please check email invitation in your email and confirm it.')
        return res
    
    def get_auth_signup_qcontext(self):
        qcontext = super().get_auth_signup_qcontext()
        # Re-Update context for signup form
        qcontext.update({k: v for (k, v) in request.params.items() if k in ['city', 'district', 'address', 'phone', 'otp']})
        return qcontext
    
    def _prepare_signup_values(self, qcontext):
        values = super()._prepare_signup_values(qcontext)
        phone = qcontext.get('phone')
        otp_code = qcontext.get('otp')
        if not phone or not otp_code:
            raise UserError(_("The form was not properly filled in."))
        if request.env["res.users"].sudo().search([("phone", "=", phone)]):
            raise UserError(_("Another user is already registered using this phone number."))
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', qcontext.get('login')):
            raise UserError(_("Invalid email address."))
        
        # Check OTP code
        stored_otp_phone = request.session.get('otp_phone')
        stored_otp_code = request.session.get('otp_code')
        creation_time = request.session.get('otp_creation')
        # Check if 5 min passed
        if stored_otp_phone and stored_otp_code and creation_time and datetime.datetime.now() < creation_time + datetime.timedelta(minutes=5):
            if phone != stored_otp_phone:
                raise UserError(_("Please get a new OTP for new number."))
            if otp_code != stored_otp_code:
                raise UserError(_("Invalid OTP."))
        else:
            raise UserError(_("OTP expired, please get a new OTP."))
        
        values['phone'] = phone
        values['city'] = qcontext.get('city')
        values['street'] = qcontext.get('address') + ", " + qcontext.get('district')
        return values