# coding=utf-8
import time
import threading
# from COINPARK import coinpark_config
import csv
from COINPARK.coinparkapi import CoinPark
import datetime
import sys

##############################参数设置#################################################
# API KEY
apikey = str(sys.argv[1])
secretkey = str(sys.argv[2])
# 刷单速度，0.5-超慢速 1-慢速  2-中速  3-快速
speed=float(sys.argv[3])
# 起始货币数量
startamount = float(sys.argv[4])
# 交易货币
tradecurrency = str(sys.argv[5])
# 基础币种
basecurrency = str(sys.argv[6])
# 交易对
pair = tradecurrency + '_' + basecurrency
# 下单时间间隔（秒）
interval = 12/speed
# 最小下单数量
minamount = startamount*speed/50
#检查和取消订单时间
sleeptime=150/speed
# 最小价差
minspread = 0.2
# 滑点
slippage = 0.0001
#返利比例
profitpercent = 0.3
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
# 实例化COINPARK接口
coinpark = CoinPark()
coinpark.auth(apikey, secretkey)
refresh_flag = 0
filename1 = 'coinpark_trades.csv'
filename2 = 'coinpark_log.csv'
starttime = time.time()
######################################################################################
# 取账户余额信息
def get_balance(symbol):
    try:
        res = coinpark.get_balance();
        for currency in res['result'][0]['result']['assets_list']:
            if (currency['coin_symbol'] == symbol):
                return (float(currency['balance']) + float(currency['freeze']))
    except Exception as ex:
        print(symbol + '取账户余额失败！')

# 利润统计线程
def calProfitThread():
    global tradecount,starttime
    usdtamount = 0
    while (True):
        time.sleep(60)
        sum = 0
        try:
            usdtamount = get_balance(basecurrency)
            for i in pricelist:
                sum = sum + i
            avgprice = round(sum / tradecount, 2)
            fee = avgprice * tradecount * 0.001 * minamount
            runtime = round((time.time() - starttime)/60,1)
            profit = round(fee * profitpercent,2)
            dailyprofit = round(fee*profitpercent*86400/(time.time()-starttime),2)
            content = '交易次数：'+ str(tradecount)  +'    成交均价:' + str(avgprice) + '   预计手续费支出：' + str(fee) + '    USDT余额：' + str(round(usdtamount,2))
            print('**********************************利润统计**********************************')
            print(content)
            print('运行时间：' + str(runtime) + '分钟   预计利润：' + str(profit) + 'USDT    24小时预计利润：' + str(dailyprofit) + 'USDT')
            print('****************************************************************************')
            log(filename2, content)
        except Exception as ex:
            print('计算成交均价出错！')


# 检查补单的线程
def balanceAccountThread():
    while (True):
        time.sleep(sleeptime)
        try:
            accountbalance = get_balance(tradecurrency)
            if (accountbalance - startamount >= minamount * 2):
                print('需要卖出补单的数量：' + str(round(accountbalance - startamount, 4)))
                amount = round(minamount * 2, 4)
                count = 0
                while (count < 5):
                    try:
                        count = count + 1
                        orderid = coinpark.create_order(pair, str(round(bid1 * 0.995, 4)), str(amount),'sell')['result'][0]['result']
                        if (orderid > 0):
                            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            trade = [nowTime, 'coinpark', pair, 'sell', amount, bid1]
                            log(filename1, trade)
                            print('补单卖出：' + str(amount))
                            break;
                    except Exception as ex:
                        time.sleep(0.5)
            elif (startamount - accountbalance >= minamount * 2):
                print('需要买入补单的数量：' + str(round(startamount - accountbalance, 4)))
                amount = round(minamount * 2, 4)
                count = 0
                while (count < 5):
                    try:
                        count = count + 1
                        orderid = coinpark.create_order(pair, str(round(ask1 * 1.005, 4)), str(amount),'buy')['result'][0]['result']
                        if (orderid > 0):
                            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            trade = [nowTime, 'coinpark', pair, 'buy', amount, bid1]
                            log(filename1, trade)
                            print('补单买入：' + str(amount))
                            break;
                    except Exception as ex:
                        time.sleep(0.5)
            else:
                print('差额：' + str(round(accountbalance - startamount, 4)) + '  无需补单')
        except Exception as ex:
            time.sleep(2)

# 定时取消未成交订单的线程
def cancelOrdersThread():
    while (True):
        time.sleep(sleeptime)
        try:
            orderlist = coinpark.get_orderlist(pair)['result'][0]['result']['items']
            print('未成交：' + str(len(orderlist)))
            count = 0
            for item in orderlist:
                try:
                    orderid = item['id']
                    coinpark.cancel_order(orderid)
                    count = count +1
                    time.sleep(0.5)
                except Exception as ex:
                    print(ex)
                    print('撤单失败:' + str(orderid))
                    time.sleep(0.5)
            print('撤单成功：' + str(count))
        except Exception as ex:
            time.sleep(0.2)

#记录交易日志
def log(filename,content):
    out = open(filename, 'a', newline='')
    csvwriter = csv.writer(out, dialect='excel')
    csvwriter.writerow(content)
    out.close()


# 执行交易策略
def strategy():
    while(True):
        try:
            global bid1, ask1, tradecount, refresh_flag
            time.sleep(interval)
            start1 = time.time()
            res = coinpark.get_market_depth(pair)
            end1 = round(time.time() - start1,3)
            bid1 = float(res['result']['bids'][0]['price'])
            ask1 = float(res['result']['asks'][0]['price'])
            if (bid1 > 0 and ask1 > 0):
                price = round((bid1 + ask1) / 2, 4)
                # price = 6112.2495
                print('盘口买价:' + str(bid1) + '  盘口卖价:' + str(ask1) + ' 下单价:' + str(price))
                start2 = time.time()
                buyorderid = coinpark.create_order(pair, round(price + slippage, 4), minamount, 'buy')['result'][0]['result']
                if(buyorderid > 0):
                    tradecount = tradecount + 1
                    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                    trade = [nowTime, 'coinpark', pair, 'buy', minamount, price]
                    log(filename1,trade)
                    print(str(nowTime) + ':下买单成功！下单数量：' + str(minamount) + '    交易次数：' + str(tradecount))
                    pricelist.append(price)
                    count = 0
                    while (count < 5):
                        try:
                            count = count + 1
                            sellorderid = coinpark.create_order(pair, round(price - slippage, 4), minamount, 'sell')['result'][0]['result']
                            if (sellorderid > 0):
                                end2 = round(time.time() - start2, 3)
                                tradecount = tradecount + 1
                                nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                                trade = [nowTime, 'coinpark', pair, 'sell', minamount, price]
                                log(filename1, trade)
                                print(str(nowTime) + ':下卖单成功！下单数量：' + str(minamount) + '    交易次数：' + str(tradecount))
                                pricelist.append(price)
                                break;
                        except Exception as ex:
                            time.sleep(0.5)
                print('行情延迟：' + str(end1) + '秒   下单延迟：'  +  str(end2) + '秒')
        except Exception as ex:
            print(ex)
            time.sleep(interval)

if __name__ == '__main__':
    try:
        currency = get_balance(tradecurrency)
        time.sleep(1)
        usdt = get_balance(basecurrency)
    except Exception as ex:
        print(ex)
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    content = 'START FROM ' + str(nowTime) + '  CURRENCY:' + str(currency) + '   USDT:' + str(usdt)
    print(content)
    log(filename2,content)
    threads.append(threading.Thread(target=strategy, args=()))
    threads.append(threading.Thread(target=cancelOrdersThread, args=()))
    threads.append(threading.Thread(target=calProfitThread, args=()))
    threads.append(threading.Thread(target=balanceAccountThread, args=()))
    for t in threads:
        t.setDaemon(True);
        t.start()
    t.join()

