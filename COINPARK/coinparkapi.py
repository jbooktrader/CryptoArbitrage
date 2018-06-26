# coding=utf-8
import hmac
import hashlib
import requests
import sys
import time
import base64
import json
from collections import OrderedDict


class CoinPark():
    def __init__(self, base_url=' https://api.coinpark.cc/v1/'):
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

    def getSign(self,data, secret):
        result = hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.md5).hexdigest()
        return result

    def doApiRequestWithApikey(self,url, cmds):
        s_cmds = json.dumps(cmds)
        sign = self.getSign(s_cmds,self.secret)
        r = requests.post(url, data={'cmds': s_cmds, 'apikey': self.key, 'sign': sign})
        return r.json()

    # 取账户余额信息
    def get_balance(self):
        url = "https://api.coinpark.cc/v1/transfer"
        cmds = [
            {
                'cmd': "transfer/assets",
                'body': {
                    'select': '',
                }
            }
        ]
        return self.doApiRequestWithApikey(url, cmds)

    #下单，side: 1买 2卖
    def create_order(self,pair,price,amount,flag):
        url = "https://api.coinpark.cc/v1/orderpending"
        if(flag == 'buy'):
            side = '1'
        elif(flag == 'sell'):
            side = '2'

        cmds = [
            {
                'cmd': "orderpending/trade",
                'body': {
                    'pair': pair,
                    'account_type': '0',
                    'order_type': '2',
                    'order_side': side,
                    'pay_bix': '0',
                    'price': price,
                    'amount': amount
                }
            }
        ]
        return self.doApiRequestWithApikey(url, cmds)

    # 取消订单
    def cancel_order(self,orderid):
        url = "https://api.coinpark.cc/v1/orderpending"
        cmds = [
            {
                'cmd': "orderpending/cancelTrade",
                'body': {
                    'orders_id': orderid,
                }
            }
        ]
        return self.doApiRequestWithApikey(url, cmds)

    # 获取当前订单列表
    def get_orderlist(self,pair):
        url = "https://api.coinpark.cc/v1/orderpending"
        cmds = [
            {
                'cmd': "orderpending/orderPendingList",
                'body': {
                    'pair': pair,
                    'account_type': '0',
                    'order_type': '2',
                    'page': '1',
                    'size': '100',
                }
            }
        ]
        return self.doApiRequestWithApikey(url, cmds)

    # 获取订单详情
    def get_orderdetail(self,orderid):
        url = "https://api.coinpark.cc/v1/orderpending"
        cmds = [
            {
                'cmd': "orderpending/order",
                'body': {
                    'id': orderid
                }
            }
        ]
        return self.doApiRequestWithApikey(url, cmds)

    # 获取历史成交信息
    def get_orderhistory(self,pair,size):
        url = "https://api.coinpark.cc/v1/orderpending"
        cmds = [
            {
                'cmd': "orderpending/orderHistoryList",
                'body': {
                    'pair': pair,
                    'account_type': '0',
                    'page': '1',
                    'size': size,
                }
            }
        ]
        return self.doApiRequestWithApikey(url, cmds)

    # 获取市场深度
    def get_market_depth(self, symbol):
        """get market depth"""
        return self.public_request('GET', 'mdata?cmd=depth&pair={symbol}&size=10'.format(symbol=symbol))
