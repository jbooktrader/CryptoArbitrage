import hmac
import hashlib
import requests
import sys
import time
import base64
import json
from collections import OrderedDict


class Coinex():
    def __init__(self, base_url='https://api.coinex.com/v1/'):
        self.base_url = base_url

    def auth(self, key, secret):
        self.key = key
        self.secret = secret

    def public_request(self, method, api_url, **payload):
        """request public url"""
        r_url = self.base_url + api_url
        try:
            r = requests.request(method, r_url, params=payload)
            if r.status_code == 200:
                return r.json()
            else:
                r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
            print(r.text)
        except Exception as err:
            print(err)

    def get_sign(params, secret_key):
        sort_params = sorted(params)
        data = []
        for item in sort_params:
            data.append(item + '=' + str(params[item]))
        str_params = "{0}&secret_key={1}".format('&'.join(data), secret_key)
        token = hashlib.md5(str_params).hexdigest().upper()
        return token

    def signed_request(self, method, api_url, **payload):
        """request a signed url"""

        param = ''
        if payload:
            sort_pay = sorted(payload.items())
            # sort_pay.sort()
            for k in sort_pay:
                param += '&' + str(k[0]) + '=' + str(k[1])
            param = param.lstrip('&')
        timestamp = str(int(time.time() * 1000))
        full_url = self.base_url + api_url

        if method == 'GET':
            if param:
                full_url = full_url + '?' +param
            sig_str = method + full_url + timestamp
        elif method == 'POST':
            sig_str = method + full_url + timestamp + param

        signature = self.get_signed(bytes(sig_str, 'utf-8'))

        headers = {
            'FC-ACCESS-KEY': self.key,
            'FC-ACCESS-SIGNATURE': signature,
            'FC-ACCESS-TIMESTAMP': timestamp
        }

        try:
            r = requests.request(method, full_url, headers=headers, json=payload)
            if r.status_code == 200:
                return r.json()
            else:
                r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
            print(r.text)
        except Exception as err:
            print(err)

    def get_market_depth(self, symbol):
        """get market depth"""
        return self.public_request('GET', 'market/depth?market={market}&merge=0.001&limit=10'.format(market=symbol))

    def get_mining_difficulty(self):
        """get market depth"""
        return self.public_request('GET', 'order/mining/difficulty')

    def get_balance(self):
        """get user balance"""
        return self.signed_request('GET', 'accounts/balance')

    def list_orders(self, **payload):
        """get orders"""
        return self.signed_request('GET', 'orders', **payload)

    def create_order(self, **payload):
        """create order"""
        return self.signed_request('POST', 'orders', **payload)

    def buy(self,symbol, price, amount):
        """buy someting"""
        return self.create_order(symbol=symbol, side='buy', type='limit', price=str(price), amount=amount)

    def sell(self, symbol, price, amount):
        """buy someting"""
        return self.create_order(symbol=symbol, side='sell', type='limit', price=str(price), amount=amount)

    def get_order(self, order_id):
        """get specfic order"""
        return self.signed_request('GET', 'orders/{order_id}'.format(order_id=order_id))

    def cancel_order(self, order_id):
        """cancel specfic order"""
        return self.signed_request('POST', 'orders/{order_id}/submit-cancel'.format(order_id=order_id))

    def order_result(self, order_id):
        """check order result"""
        return self.signed_request('GET', 'orders/{order_id}/match-results'.format(order_id=order_id))

