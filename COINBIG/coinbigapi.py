import time
import base64
import hashlib
import requests
import json
import random
import urllib
import copy
import operator


class CoinBig():
    def __init__(self, apiKey='', secret=''):
        self.url = 'http://www.3k2k.com:81/api/publics/v1'
        self.apiKey = apiKey
        self.secret = secret

    def sign(self, params):
        _params = copy.copy(params)
        sort_params = sorted(_params.items(), key=operator.itemgetter(0))
        sort_params = dict(sort_params)
        sort_params['secret_key'] = self.secret
        string = urllib.parse.urlencode(sort_params)
        _sign = hashlib.md5(bytes(string.encode('utf-8'))).hexdigest().upper()
        params['sign'] = _sign
        return params

    # 获取用户的提现/充值记录
    def account_records(self, ):
        url = self.url + '/account_records'
        params = {'apikey': self.apiKey, 'shortName': 'btc_usdt', 'status': 0, 'recordType': 0}

        data = self.sign(params)
        res = requests.post(url, data=data)
        return res.json()

    # 获取所有订单信息
    def orders_info(self, symbol, trade_type, nums):
        url = self.url + '/orders_info'
        params = {'apikey': self.apiKey, 'symbol': trade_type, 'size': nums, 'type': 3}
        data = self.sign(params)
        res = requests.post(url, data=data)
        return res.json()

    # 用户信息
    def userinfo(self):
        url = self.url + '/userinfo'

        params = {'apikey': self.apiKey}
        data = self.sign(params)
        res = requests.post(url, data=data)
        return res.json()

    # 下订单
    def place_order(self, trade_type, price, amount):
        '''
        type    String 买卖类型: 限价单(buy/sell) 市价单(buy_market/sell_market)
        price   double  否   下单价格 [限价买单(必填)
        amount  double  否   交易数量 [限价卖单（必填)
        '''
        url = self.url + '/trade'
        params = {'apikey': self.apiKey, 'type': trade_type, 'price': price, 'amount': amount}
        data = self.sign(params)
        res = requests.post(url, data=data)

        return res.json()

    # 批量下订单
    def batch_orders(self, symbol, trade_type, order_list):
        '''
        apikey  String  是   用户申请的apiKey
        symbol  String  是   btc_usdt: 比特币
        type    String  否   买卖类型:限价单(buy/sell)
        orders_data String  是   最大下单量为5， price和amount参数参考trade接口中的说明，最终买卖类型由orders_data 中type 为准，如orders_data不设定type 则由上面type设置为准。参数格式:[{price:3,amount:5,type:'sell'},{price:3,amount:3,type:'buy'}]
        sign    String  是   请求参数的签名
        '''
        url = self.url + '/batch_trade'

        params = {'apikey': self.apiKey, 'symbol': symbol, 'type': trade_type, 'orders_data': str(order_list)}
        data = self.sign(params)

        res = requests.post(url, data=data)
        return res.json()

    # 批量撤销订单
    def batch_cancel_orders(self, symbol):
        '''
        apikey  String  是   公钥
        symbol  String  是   币对名称 btc_usdt:比特币
        sign    String  是   签名
        '''
        url = self.url + '/cance_all_orders'
        params = {'apikey': self.apiKey, 'symbol': symbol}
        data = self.sign(params)

        res = requests.post(url, data=data)
        return res.json()

    # 查询订单状况
    def fetch_order(self, order_id):
        url = self.url + '/order_info'
        params = {'apikey': self.apiKey, 'order_id': order_id}
        data = self.sign(params)

        res = requests.post(url, data=data)
        return res.json()


if __name__ == '__main__':
    ex = CoinBig(apiKey, secret)
    print(ex.userinfo())
    print('-' * 80)
    print(ex.account_records())