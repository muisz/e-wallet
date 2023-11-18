import string
import random
import requests
import uuid
from django.conf import settings
from django.core.cache import cache

from apps.utils.decorators import cache_result


class InstamoneyError(Exception):
    pass

def handle_error(default=None):
    def wrapper(func):
        def inner(*args, **kwargs):
            try:
                response = func(*args, **kwargs)
                if hasattr(response, 'status_code') and not str(response.status_code).startswith('2'):
                    json_response = response.json()
                    raise InstamoneyError(json_response.get("error_code"))
                return response

            except Exception as error:
                print("error instamoney: ", error)
                if default is not None:
                    return default
                raise InstamoneyError("Service unavailable.")
        return inner
    return wrapper

class Instamoney:
    SECRET_KEY = settings.INSTAMONEY_SECRET_KEY
    BASE_URL = 'https://api.instamoney.co'

    def get_auth(self):
        return (self.SECRET_KEY, '')

class RNE(Instamoney):

    @cache_result('instamoney-banks')
    @handle_error(default=[])
    def list_banks(self):
        url = f"{self.BASE_URL}/available_virtual_account_banks"
        response = requests.get(url, auth=self.get_auth())
        if str(response.status_code).startswith('2'):
            return response.json()
        return response

    @handle_error()
    def create_virtual_account(self, name: str, bank_code: str, external_id: str):
        if settings.TESTING:
            return {
                "account_number": "".join(random.choice(string.digits) for _ in range(10)),
                "external_id": external_id,
                "id": str(uuid.uuid4()),
            }
        
        url = f"{self.BASE_URL}/callback_virtual_accounts"
        payload = {
            "name": name,
            "bank_code": bank_code,
            "external_id": external_id,
        }
        response = requests.post(url, auth=self.get_auth(), json=payload)
        if str(response.status_code).startswith('2'):
            return response.json()
        return response

    def is_valid_bank_code(self, value):
        found = False
        banks = self.list_banks()
        for bank in banks:
            if bank.get('code') == value:
                found = True
                break
        return found
