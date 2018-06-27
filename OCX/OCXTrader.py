# coding=utf-8
from OCX.client import Client
import time
import threading
from OCX import ocx_config
import csv
import datetime

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
# 实例化OCX接口
ocx =  Client(access_key=ocx_config.apikey, secret_key=ocx_config.secretkey)
refresh_flag = 0
filename1 = 'trades.csv'
filename2 = 'log.csv'
out1 = open(filename1,'a',newline='')
out2 = open(filename2,'a',newline='')
csvwriter = csv.writer(out1,dialect='excel')
csvwriter2 = csv.writer(out2,dialect='excel')
######################################################################################
# 执行交易策略
def runStrategy():
    try:
        global bid1, ask1, tradecount,refresh_flag
        res = ocx.get_market_depth(ocx_config.pair)
        bid1 = float(res['data']['bids'][0][0])
        ask1 = float(res['data']['asks'][-1][0])

        if (bid1 > 0 and ask1 > 0):
            price = round((bid1 + ask1) / 2, 4)
            print('bid:' + str(bid1) + '  ask:' + str(ask1) + ' price:' + str(price))
            buystatus = ocx.buy(ocx_config.pair, str(round(price + ocx_config.slippage, 4)), str(ocx_config.minamount))
            # 如果下买单成功，则继续下卖单，遇到异常则终止本次交易。
            if (buystatus['data']['id'] > 0):
                # 下卖单，如果遇到异常则重复5次下单直到成功为止
                nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                trade = [nowTime, 'ocx', ocx_config.pair, 'buy', ocx_config.minamount, price]
                csvwriter.writerow(trade)
                count = 0
                while (count < 10):
                    try:
                        count = count + 1
                        sellstatus = ocx.sell(ocx_config.pair, str(round(price - ocx_config.slippage, 4)),
                                              str(ocx_config.minamount))
                        if (sellstatus['data']['id'] >0):
                            tradecount = tradecount + 1
                            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            trade = [nowTime,'ocx', ocx_config.pair, 'sell', ocx_config.minamount, price]
                            csvwriter.writerow(trade)
                            print('下单成功！下单数量：' + str(ocx_config.minamount) + '    交易次数：' + str(tradecount))
                            # 记录本次下单价格
                            pricelist.append(price)
                            break;
                    except Exception as ex:
                        time.sleep(2)
        time.sleep(ocx_config.interval)
    except Exception as ex:
        time.sleep(ocx_config.interval)

# 取账户余额信息
def get_balance():
    try:
        res = ocx.get_balance();
        for currency in res['data']:
            if (currency['currency_code'] == ocx_config.tradecurrency):
                return (float(currency['balance']) + float(currency['locked']))
    except Exception as ex:
        print('取账户余额失败！')

def get_usdt():
    try:
        res = ocx.get_balance();
        for currency in res['data']:
            if (currency['currency_code'] == ocx_config.basecurrency):
                return (float(currency['balance']) + float(currency['locked']))
    except:
        print('取账户余额失败！')


# 检查订单状态的线程
def checkOrdersThread():
    while (True):
        time.sleep(ocx_config.sleeptime)
        try:
            accountbalance = get_balance()
            if (accountbalance - ocx_config.startamount >= ocx_config.minamount * 2):
                #amount = round(accountbalance - config.startamount, 4)
                print('需要补单的数量：' + str(round(accountbalance - ocx_config.startamount, 4)))
                amount = round(ocx_config.minamount * 2, 4)
                count = 0
                while (count < 10):
                    try:
                        count = count + 1
                        status = ocx.sell(ocx_config.pair, str(round(bid1 * 0.995, 4)), str(amount))
                        if (status['data']['id'] > 0):
                            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            trade = [nowTime, 'ocx', ocx_config.pair, 'sell', amount, bid1]
                            csvwriter.writerow(trade)
                            print('补单卖出：' + str(amount))
                            break;
                    except Exception as ex:
                        time.sleep(0.1)
            elif (ocx_config.startamount - accountbalance >= ocx_config.minamount * 2):
                print('需要补单的数量：' + str(round(ocx_config.startamount - accountbalance, 4)))
                amount = round(ocx_config.minamount * 2, 4)
                count = 0
                while (count < 10):
                    try:
                        count = count + 1
                        status = ocx.buy(ocx_config.pair, str(round(ask1 * 1.005, 4)), str(amount))
                        time.sleep(1)
                        if (status['data']['id'] > 0):
                            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            trade = [nowTime, 'ocx', ocx_config.pair, 'buy', amount, bid1]
                            csvwriter.writerow(trade)
                            print('补单买入：' + str(amount))
                            break;
                    except Exception as ex:
                        time.sleep(0.1)
            else:
                print('差额：' + str(round(accountbalance - ocx_config.startamount, 4)) + '  无需补单')
        except Exception as ex:
            time.sleep(2)


# 执行策略的线程
def strategyThread():
    while (True):
        runStrategy()

# 定时取消未成交订单的线程
def cancelOrdersThread():
    while (True):
        time.sleep(ocx_config.sleeptime)
        try:
            # 查询所有状态为SUBMITTED的订单列表，并逐个取消
            orderlist = ocx.list_orders()
            count = 0
            for item in orderlist['data']:
                if(item['state'] == 'wait'):
                    try:
                        ocx.cancel_order(item['id'])
                        time.sleep(1)
                        count = count +1
                    except Exception as ex:
                        print('清除订单出错：' + str(ex))
                        time.sleep(1)
            print('订单清除成功！' + str(count))
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
            fee = avgprice * tradecount * 0.001 * 2 * ocx_config.minamount
            print('交易次数：'+ str(tradecount)  +'    成交均价:' + str(avgprice) + '   预计手续费支出：' + str(fee) + '    USDT余额：' + str(round(usdtamount,2)))
            log=['交易次数：'+ str(tradecount)  +'    成交均价:' + str(avgprice) + '   预计手续费支出：' + str(fee) + '    USDT余额：' + str(round(usdtamount,2))]
            csvwriter2.writerow(log)
        except Exception as ex:
            print('计算成交均价出错！')

def checkOcxThread():
    while(True):
        time.sleep(30)
        try:
            ocxamount = get_ocx()
            if(ocxamount > 100):
                    res = ocx.get_market_depth('ocxeth')
                    bid = float(res['data']['bids'][0][0])               
                    price = round(bid*0.95,8)
                    amount = round(ocxamount,0) - 1
                    ocx.sell('ocxeth',price,amount)
                    print('OCX余额：' + str(ocxamount) + '  自动卖出！卖出价：' + str(price))
                
            else:
                print('OCX余额：' + str(ocxamount) + '  无需卖出！')
        except Exception as ex:
                print(ex)

def get_ocx():
    try:
        res = ocx.get_balance();
        for currency in res['data']:
            if (currency['currency_code'] == 'ocx'):
                return (float(currency['balance']) + float(currency['locked']))
    except:
        print('取OCX余额失败！')

# 程序主入口
if __name__ == '__main__':
    try:
        currency = get_balance()
        time.sleep(1)
        usdt = get_usdt()
    except Exception as ex:
        print(ex)
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log=['START FROM ' + str(nowTime) + '  CURRENCY:' + str(currency) + '   USDT:' + str(usdt)]
    csvwriter2.writerow(log)
    threads.append(threading.Thread(target=strategyThread, args=()))
    threads.append(threading.Thread(target=checkOrdersThread, args=()))
    threads.append(threading.Thread(target=cancelOrdersThread, args=()))
    threads.append(threading.Thread(target=calProfitThread, args=()))
    # threads.append(threading.Thread(target=checkOcxThread, args=()))
    for t in threads:
        t.setDaemon(True);
        t.start()
    t.join()

