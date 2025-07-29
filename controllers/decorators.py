import json
from functools import wraps
from odoo import http

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return http.request.make_response(json.dumps({"error": str(e)}), headers={'Content-Type': 'application/json'}, status=401)
    return wrapper