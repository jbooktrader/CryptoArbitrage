# coding=utf-8
from fcoinapi import Fcoin
import time
import threading
import sys
from asyncio.tasks import sleep
from fcoinapi import Fcoin
from WSS.fcoin_client import fcoin_client
import config

##############################全局变量################################################
# 交易次数
tradecount = 0
# 记录最新买卖价
bid1 = 0
ask1 = 0
# 价格列表
pricelist = []
# 线程池
threads = []
# 实例化FCOIN接口
fcoin = Fcoin()
fcoin.auth(config.apikey, config.secretkey)
refresh_flag = 0
######################################################################################

# 执行交易策略
def runStrategy():
    try:
        global bid1, ask1, tradecount,refresh_flag
        if(refresh_flag == 0):
            print("行情数据未更新！")
        else:
            refresh_flag = 0
            if(bid1 > 0 and ask1 >0):
                price = round((bid1 + ask1) / 2, 2)
                print('bid:' + str(bid1) + '  ask:' + str(ask1) + ' price:' +str(price))
                buystatus = fcoin.buy(config.pair, str(round(price+config.slippage,2)), str(config.minamount))
                # 如果下买单成功，则继续下卖单，遇到异常则终止本次交易。
                if (buystatus['status'] is 0):
                    # 下卖单，如果遇到异常则重复5次下单直到成功为止
                    count = 0
                    while (count < 10):
                        try:
                            count = count + 1
                            sellstatus = fcoin.sell(config.pair, str(round(price-config.slippage,2)), str(config.minamount))
                            time.sleep(1)
                            if (sellstatus['status'] is 0):
                                tradecount = tradecount + 1
                                print('下单成功！下单数量：' +  str(config.minamount) + '    交易次数：' + str(tradecount))
                                # 记录本次下单价格
                                pricelist.append(price)
                                break;
                        except Exception as ex:
                            time.sleep(2)
            time.sleep(config.interval)
    except Exception as ex:
        time.sleep(config.interval)

# 取账户余额信息
def get_balance():
    try:
        res = fcoin.get_balance();
        for currency in res['data']:
            if (currency['currency'] == config.tradecurrency):
                return (float(currency['balance']))
    except:
        print('取账户余额失败！')

def get_usdt():
    try:
        res = fcoin.get_balance();
        for currency in res['data']:
            if (currency['currency'] == config.basecurrency):
                return (float(currency['balance']))
    except:
        print('取账户余额失败！')


# 检查订单状态的线程
def checkOrdersThread():
    while (True):
        time.sleep(config.sleeptime)
        try:
            accountbalance = get_balance()
            if (accountbalance - config.startamount >= config.minamount * 2):
                #amount = round(accountbalance - config.startamount, 4)
                print('需要补单的数量：' + str(round(accountbalance - config.startamount, 4)))
                amount = round(config.minamount * 2,4)
                count = 0
                while (count < 10):
                    try:
                        count = count + 1
                        status = fcoin.sell(config.pair, str(round(bid1 * 0.95, 2)), str(amount))
                        time.sleep(1)
                        if (status['status'] is 0):
                            print('补单卖出：' + str(amount))
                            break;
                    except Exception as ex:
                        time.sleep(0.1)
            elif (config.startamount - accountbalance >= config.minamount * 2):
                # amount = round(startamount - accountbalance, 4)
                print('需要补单的数量：' + str(round(config.startamount - accountbalance, 4)))
                amount = round(config.minamount * 2, 4)
                count = 0
                while (count < 10):
                    try:
                        count = count + 1
                        status = fcoin.buy(config.pair, str(round(ask1 * 1.05, 2)), str(amount))
                        time.sleep(1)
                        if (status['status'] is 0):
                            print('补单买入：' + str(amount))
                            break;
                    except Exception as ex:
                        time.sleep(0.1)
            else:
                print('差额：' + str(round(accountbalance - config.startamount, 4)) + '  无需补单')
        except Exception as ex:
            time.sleep(2)


# 执行策略的线程
def strategyThread():
    while (True):
        runStrategy()

# 定时取消未成交订单的线程
def cancelOrdersThread():
    while (True):
        time.sleep(config.sleeptime)
        try:
            # 查询所有状态为SUBMITTED的订单列表，并逐个取消
            orders = fcoin.list_orders(symbol=config.pair, states='submitted')
            orderlist = orderlist['data']
            orderlist.reverse()
            for item in orderlist:
                id = item['id']
                try:
                    fcoin.cancel_order(id)
                    time.sleep(3)
                except Exception as ex:
                    print('清除订单出错：' + str(ex))
                    time.sleep(3)
            print('订单清除成功！' + str(len(orderlist['data'])))
        except Exception as ex:
            time.sleep(0.2)



# 利润统计线程
def calProfitThread():
    global tradecount
    usdtamount = 0
    while (True):
        time.sleep(60)
        sum = 0
        try:
            usdtamount = get_usdt()

            for i in pricelist:
                sum = sum + i
            avgprice = round(sum / tradecount, 2)
            fee = avgprice * tradecount * 0.001 * 2 * config.minamount
            print('成交均价:' + str(avgprice) + '   预计手续费支出：' + str(fee) + '    USDT余额：' + str(round(usdtamount,2)))
        except Exception as ex:
            print('计算成交均价出错！')

def depth(data):
    global bid1, ask1,refresh_flag
    if data:
        try:
            bid1 = data['bids'][0]
            ask1 = data['asks'][0]
            refresh_flag = 1
        except Exception as ex:
            print('获取行情异常' + str(ex))

def receive_data_thread():
    while 1:
        time.sleep(0.1)
        client.subscribe_depth(config.pair, 'L20')

# 程序主入口
if __name__ == '__main__':
    client = fcoin_client()
    client.stream.stream_depth.subscribe(depth)
    client.start()
    while not client.isConnected:
        print('等待连接行情服务器！')
        time.sleep(2)
    client.subscribe_depth(config.pair, 'L20')
    threads.append(threading.Thread(target=receive_data_thread, args=()))
    threads.append(threading.Thread(target=checkOrdersThread, args=()))
    threads.append(threading.Thread(target=strategyThread, args=()))
    threads.append(threading.Thread(target=cancelOrdersThread, args=()))
    threads.append(threading.Thread(target=calProfitThread, args=()))
    for t in threads:
        t.setDaemon(True);
        t.start()
    t.join()

