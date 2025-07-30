from odoo import api, fields, models, _
import requests
import uuid
import logging
from requests.auth import HTTPBasicAuth
from odoo.http import request
from odoo.exceptions import AccessDenied
import urllib.parse

_logger = logging.getLogger(__name__)



class ResUsers(models.Model):
    _inherit = 'res.users'

    failed_login_attempts = fields.Integer(default=0)
    is_locked = fields.Boolean(default=False)
    push_token = fields.Char(string="Push notification token", default="")
    verification_token = fields.Char(string="Verification Token", copy=False)
    is_verified = fields.Boolean(string="Verified", default=False)

    def generate_verification_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        encoded_url = urllib.parse.quote_plus(f"{base_url}/verify?uid={self.id}&token={self.verification_token}")
        return f"{base_url}/web?redirect={encoded_url}"
    
    def generate_verification_token(self):
        self.sudo().write({'verification_token': str(uuid.uuid4())})
        # Gửi email xác thực
        template = request.env.ref('custom_website.template_verification_email')
        body = template.sudo()._render_field('body_html', [self.id])[self.id]
        print(body)
        template.sudo().send_mail(self.id, force_send=True)

    @api.model
    def _check_credentials(self, password, env):
        if self.is_locked:
            raise AccessDenied(_("Account is locked. Contact your Administrator to unlock your account."))
        return super(ResUsers, self)._check_credentials(password, env)

    @classmethod
    def authenticate(cls, db, login, password, user_agent_env):
        if login == "admin":
            return super(ResUsers, cls).authenticate(db, login, password, user_agent_env=user_agent_env)
        user = request.env['res.users'].sudo().search(['|', ('email', '=', login), ('phone', '=', login)], limit=1)
        if user:
            if user.is_locked:
                raise AccessDenied(_("Your account is locked due to too many failed login attempts."))
            else:
                email = user.email
                try:
                    user_id = super(ResUsers, cls).authenticate(db, email, password, user_agent_env=user_agent_env)
                    user = request.env.user
                    user.write({'failed_login_attempts': 0})
                    return user_id
                except Exception as e:
                    user.sudo()._increase_failed_attempts()
                    raise AccessDenied(_(str(e)))
        else:
            raise AccessDenied(_("Wrong login/password"))

    def _increase_failed_attempts(self):
        limit = int(self.env['ir.config_parameter'].sudo().get_param('auth_failure.login_lock_limit', 5))
        if self.failed_login_attempts == limit:
            self.sudo().write({'is_locked': True, 'failed_login_attempts': self.failed_login_attempts + 1})
            template = request.env.ref('custom_website.template_account_locked_email')
            body = template.sudo()._render_field('body_html', [self.id])[self.id]
            print(body)
            template.sudo().send_mail(self.id, force_send=True)
        else:
            self.sudo().write({'failed_login_attempts': self.failed_login_attempts + 1})

    def send_push_notification(self, body):
        # if self.push_token == "":
        #     raise Warning("Driver push token haven't set yet.")
        url = "https://exp.host/--/api/v2/push/send"
        data = {
            "to": self.push_token,
            "title": "DHL express",
            "body": body,
        }

        response = requests.post(url, json=data)
        print(f"send_push_notification: {response.json()}")
        # if response.status_code != 200:
        #     raise Warning(f"Failed to send push notification: {response.text}.")
        return response

    def send_sms(self, content, phone=None):
        twilio_sid = "AC73b199b33d2850372551bea0cd64864e"
        twilio_token = "b82460b0e30c2b1613e8f2615f34407e"
        url = f'https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json'
        if not phone:
            phone = self.phone
        data = {
            'To': f'+84{phone}',
            'From': '+19787486021',
            'Body': str(content),
        }
        auth = HTTPBasicAuth(twilio_sid, twilio_token)

        response = requests.post(url, data=data, auth=auth)
        print(f"send_sms: {response.json()}")
        return response
    
    def action_reset_login(self):
        self.ensure_one()
        self.sudo().write({'is_locked': False, 'failed_login_attempts': 0})
        return True