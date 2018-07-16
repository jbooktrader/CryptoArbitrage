import copy
import hashlib
import json
import operator
import time
import urllib
from urllib.request import Request, urlopen


from COINBIG.enums import *


# ORDER_STATUS
# 1：未完成,2：部分成交,3：完全成交,4：用户撤销、5：部分撤销、6：成交失败
FINISH_CODE = 3
PARTIAL_FINISH_CODE = 2
PENDING_CODE = 1
CANCEL_CODE = 4
PARTIAL_CANCEL_CODE = 5
FAIL_CODE = 6


def format_symbol(symbol):
    return symbol.replace('/', '_').lower()


class CoinBigClient():
    def __init__(self, key='', secret=''):
        self._exchange_name = COINBIG
        self.url = 'https://www.coinbig.com'
        self.apiKey = key
        self.secret = secret

    @property
    def exchange(self):
        return self._exchange_name

    def httpGet(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }
        request = Request(url=url, headers=headers)
        content = urlopen(request, timeout=15).read()
        content = content.decode('utf-8')
        json_data = json.loads(content)
        return json_data

    def httpPost(self, url, params):
        params['time'] = int(round(time.time() * 1000))
        params = self.sign(params)
        temp_params = urllib.parse.urlencode(params)
        data = bytes(temp_params, encoding='utf8')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }
        request = Request(url=url, data=data, headers=headers)
        content = urlopen(request, timeout=30).read()
        json_data = json.loads(content)
        return json_data

    def sign(self, params):
        _params = copy.copy(params)
        sort_params = sorted(_params.items(), key=operator.itemgetter(0))
        sort_params = dict(sort_params)
        sort_params['secret_key'] = self.secret
        string = urllib.parse.urlencode(sort_params)
        # _sign1 = hashlib.md5(bytes('abc'.encode('utf-8'))).hexdigest().upper()
        _sign = hashlib.md5(bytes(string.encode('utf-8'))).hexdigest().upper()
        params['sign'] = _sign
        return params

    # 查询深度信息
    def fetch_order_book(self, symbol, **kwargs):
        url = self.url + '/api/publics/v1/depth'
        url += '?symbol=' + format_symbol(symbol)
        try:
            res = self.httpGet(url)
            code = res['code']
            if code == 0:
                payload = {
                    'bids': res['data']['bids'][:10],
                    'asks': res['data']['asks'][:10]
                }
                return payload
            else:
                return code, res['msg']
        except Exception as e:
            return GENERIC_ERROR_CODE, None

    def fetch_balance(self, currency, **kwargs):
        url = self.url + '/api/publics/v1/userinfoBySymbol'
        params = {
            'apikey': self.apiKey,
            'shortName': currency.upper(),
        }
        try:
            res = self.httpPost(url, params)
            code = res['code']
            if code == 0:
                # format payload
                payload = res['data']
                return payload
            else:
                return code, res['msg']
        except Exception as e:
            return GENERIC_ERROR_CODE, None

    # 获取所有订单信息
    def fetch_all_orders(self, symbol, limit, status, **kwargs):
        url = self.url + '/api/publics/v1/orders_info'
        params = {
            'apikey': self.apiKey,
            'symbol': format_symbol(symbol),
            'size': limit,
            'type': status
        }
        try:
            res = self.httpPost(url, params)
            code = res['code']
            if code == 0:
                # format payload
                payload = res['data']['orders']
                return SUCCESS_CODE, payload
            else:

                return code, res['msg']
        except Exception as e:

            return GENERIC_ERROR_CODE, None

    # 用户信息
    def fetch_user_info(self, **kwargs):
        url = self.url + '/api/publics/v1/userinfo'
        params = {
            'apikey': self.apiKey,
        }
        try:
            res = self.httpPost(url, params)
            code = res['code']
            if code == 0:
                # format payload
                payload = res['data']['info']
                return SUCCESS_CODE, payload
            else:

                return code, res['msg']
        except Exception as e:

            return GENERIC_ERROR_CODE, None

    # 获取用户的提现/充值记录
    def fetch_account_records(self, currency, status, recode_type, **kwargs):
        url = self.url + '/account_records'
        params = {
            'apikey': self.apiKey,
            'shortName': currency.upper(),
            'status': status,
            'recordType': recode_type
        }
        try:
            res = self.httpPost(url, params)
            code = res['code']
            if code == 0:
                # format payload
                payload = res['data']
                return SUCCESS_CODE, payload
            else:

                return code, res['msg']
        except Exception as e:

            return GENERIC_ERROR_CODE, None

    # 查询最新行情价
    def fetch_ticker(self, symbol, **kwargs):
        url = self.url + '/api/publics/v1/ticker'
        url += '?symbol=' + format_symbol(symbol)
        try:
            res = self.httpGet(url)
            code = res['code']
            if code == 0:
                payload = res['data']['ticker']
                return SUCCESS_CODE, payload
            else:

                return code, res['msg']
        except Exception as e:

            return GENERIC_ERROR_CODE, None

    # ======================
    # == 以下接口还未调试过 ==
    # ======================

    # 查询订单状况
    def fetch_order(self, order_id):
        url = self.url + '/order_info'
        params = {
            'apikey': self.apiKey,
            'order_id': order_id
        }
        try:
            res = self.httpPost(url, params)
            code = res['code']
            if code == 0:
                # format payload
                payload = res['data']
                return payload
            else:

                return code, res['msg']
        except Exception as e:

            return GENERIC_ERROR_CODE, None

    # 撤销订单
    def cancel_order(self, order_id, **kwargs):
        '''
        apikey  String  是   公钥
        order_id String 是   订单号
        sign    String  是   签名
        '''
        url = self.url + '/api/publics/v1/cancel_order'
        params = {
            'apikey': self.apiKey,
            'order_id': order_id
        }
        try:
            res = self.httpPost(url, params)
            code = res['code']
            if code == 0:
                # format payload
                payload = res['data']
                return SUCCESS_CODE, payload
            else:

                return code, res['msg']
        except Exception as e:

            return GENERIC_ERROR_CODE, None

    # 创建订单
    def create_order(self, symbol, price, amount, side, **kwargs):
        '''
        side    String 买卖类型: 限价单(buy/sell) 市价单(buy_market/sell_market)
        price   double  否   下单价格 [限价买单(必填)
        amount  double  否   交易数量 [限价卖单（必填)
        '''
        url = self.url + '/api/publics/v1/trade'
        params = {
            'amount': amount,
            'apikey': self.apiKey,
            'price': price,
            'symbol': format_symbol(symbol),
            'type': side
        }
        try:
            res = self.httpPost(url, params)
            print(res)
            code = res['code']
            if code == 0:
                # format payload
                payload = res['data']['order_id']
                return payload
            else:

                return res['msg']
        except Exception as e:

            return GENERIC_ERROR_CODE, None

    # 批量下订单
    def batch_create_orders(self, symbol, trade_type, order_list):
        '''
        apikey  String  是   用户申请的apiKey
        symbol  String  是   btc_usdt: 比特币
        type    String  否   买卖类型:限价单(buy/sell)
        orders_data String  是   最大下单量为5， price和amount参数参考trade接口中的说明，最终买卖类型由orders_data 中type 为准，如orders_data不设定type 则由上面type设置为准。参数格式:[{price:3,amount:5,type:'sell'},{price:3,amount:3,type:'buy'}]
        sign    String  是   请求参数的签名
        '''
        url = self.url + '/batch_trade'

        params = {
            'apikey': self.apiKey,
            'symbol': format_symbol(symbol),
            'type': trade_type,
            'orders_data': str(order_list)
        }
        try:
            res = self.httpPost(url, params)
            code = res['code']
            if code == 0:
                # format payload
                payload = res['data']
                return SUCCESS_CODE, payload
            else:

                return code, res['msg']
        except Exception as e:

            return GENERIC_ERROR_CODE, None

    # 批量撤销订单
    def batch_cancel_orders(self, symbol):
        '''
        apikey  String  是   公钥
        symbol  String  是   币对名称 btc_usdt:比特币
        sign    String  是   签名
        '''
        url = self.url + '/cance_all_orders'
        params = {
            'apikey': self.apiKey,
            'symbol': format_symbol(symbol)
        }
        try:
            res = self.httpPost(url, params)
            code = res['code']
            if code == 0:
                # format payload
                payload = res['data']
                return SUCCESS_CODE, payload
            else:

                return code, res['msg']
        except Exception as e:

            return GENERIC_ERROR_CODE, None
