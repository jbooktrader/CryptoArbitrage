# coding=utf-8
import time
import threading
from COINPARK import coinpark_config
import csv
from COINPARK.coinparkapi import CoinPark
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
# 实例化COINPARK接口
coinpark = CoinPark()
coinpark.auth(coinpark_config.apikey, coinpark_config.secretkey)
refresh_flag = 0
filename1 = 'coinpark_trades.csv'
filename2 = 'coinpari_log.csv'
out1 = open(filename1, 'a', newline='')
out2 = open(filename2, 'a', newline='')
csvwriter = csv.writer(out1, dialect='excel')
csvwriter2 = csv.writer(out2, dialect='excel')


######################################################################################
# 取账户余额信息
def get_balance(symbol):
    try:
        res = coinpark.get_balance();
        for currency in res['result'][0]['result']['assets_list']:
            if (currency['coin_symbol'] == symbol):
                return (float(currency['balance']) + float(currency['freeze']))
    except Exception as ex:
        print(ex)
        print(symbol + '取账户余额失败！')

# 利润统计线程
def calProfitThread():
    global tradecount
    usdtamount = 0
    while (True):
        time.sleep(60)
        sum = 0
        try:
            usdtamount = get_balance(coinpark_config.basecurrency)
            for i in pricelist:
                sum = sum + i
            avgprice = round(sum / tradecount, 2)
            fee = avgprice * tradecount * 0.001 * coinpark_config.minamount
            print('交易次数：'+ str(tradecount)  +'    成交均价:' + str(avgprice) + '   预计手续费支出：' + str(fee) + '    USDT余额：' + str(round(usdtamount,2)))
            log=['交易次数：'+ str(tradecount)  +'    成交均价:' + str(avgprice) + '   预计手续费支出：' + str(fee) + '    USDT余额：' + str(round(usdtamount,2))]
            csvwriter2.writerow(log)
        except Exception as ex:
            print('计算成交均价出错！')


# 检查补单的线程
def balanceAccountThread():
    while (True):
        # time.sleep(coinpark_config.sleeptime)
        time.sleep(60)
        try:
            accountbalance = get_balance(coinpark_config.tradecurrency)
            if (accountbalance - coinpark_config.startamount >= coinpark_config.minamount * 2):
                print('需要卖出补单的数量：' + str(round(accountbalance - coinpark_config.startamount, 4)))
                amount = round(coinpark_config.minamount * 2, 4)
                count = 0
                while (count < 5):
                    try:
                        count = count + 1
                        orderid = coinpark.create_order(coinpark_config.pair, str(round(bid1 * 0.995, 4)), str(amount),'sell')['result'][0]['result']
                        if (orderid > 0):
                            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            trade = [nowTime, 'coinpark', coinpark_config.pair, 'sell', amount, bid1]
                            csvwriter.writerow(trade)
                            print('补单卖出：' + str(amount))
                            break;
                    except Exception as ex:
                        time.sleep(0.5)
            elif (coinpark_config.startamount - accountbalance >= coinpark_config.minamount * 2):
                print('需要买入补单的数量：' + str(round(coinpark_config.startamount - accountbalance, 4)))
                amount = round(coinpark_config.minamount * 2, 4)
                count = 0
                while (count < 5):
                    try:
                        count = count + 1
                        status = coinpark.create_order(coinpark_config.pair, str(round(ask1 * 1.005, 4)), str(amount),'buy')['result'][0]['result']
                        if (orderid > 0):
                            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            trade = [nowTime, 'coinpark', coinpark_config.pair, 'buy', amount, bid1]
                            csvwriter.writerow(trade)
                            print('补单买入：' + str(amount))
                            break;
                    except Exception as ex:
                        time.sleep(0.5)
            else:
                print('差额：' + str(round(accountbalance - coinpark_config.startamount, 4)) + '  无需补单')
        except Exception as ex:
            time.sleep(2)

# 定时取消未成交订单的线程
def cancelOrdersThread():
    while (True):
        # time.sleep(coinpark_config.sleeptime)
        time.sleep(60)
        try:
            # 查询所有状态为SUBMITTED的订单列表，并逐个取消
            orderlist = coinpark.get_orderlist(coinpark_config.pair)['result'][0]['result']['items']
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
            print(ex)
            time.sleep(0.2)

# 执行交易策略
def strategy():
    while(True):
        try:
            global bid1, ask1, tradecount, refresh_flag
            # time.sleep(coinpark_config.sleeptime)
            time.sleep(2)
            start1 = time.time()
            res = coinpark.get_market_depth(coinpark_config.pair)
            end1 = round(time.time() - start1,3)
            bid1 = float(res['result']['bids'][0]['price'])
            ask1 = float(res['result']['asks'][0]['price'])
            if (bid1 > 0 and ask1 > 0):
                price = round((bid1 + ask1) / 2, 4)
                # price = 6112.2495
                print('盘口买价:' + str(bid1) + '  盘口卖价:' + str(ask1) + ' 下单价:' + str(price))
                start2 = time.time()
                buyorderid = coinpark.create_order(coinpark_config.pair, round(price + coinpark_config.slippage, 4), coinpark_config.minamount, 'buy')['result'][0]['result']
                if(buyorderid > 0):
                    tradecount = tradecount + 1
                    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                    trade = [nowTime, 'coinpark', coinpark_config.pair, 'buy', coinpark_config.minamount, price]
                    csvwriter.writerow(trade)
                    print(str(nowTime) + ':下买单成功！下单数量：' + str(coinpark_config.minamount) + '    交易次数：' + str(tradecount))
                    pricelist.append(price)
                    count = 0
                    while (count < 5):
                        try:
                            count = count + 1
                            sellorderid = coinpark.create_order(coinpark_config.pair, round(price + coinpark_config.slippage, 4), coinpark_config.minamount, 'sell')['result'][0]['result']
                            if (sellorderid > 0):
                                end2 = round(time.time() - start2, 3)
                                tradecount = tradecount + 1
                                nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                                trade = [nowTime, 'coinpark', coinpark_config.pair, 'sell', coinpark_config.minamount, price]
                                csvwriter.writerow(trade)
                                print(str(nowTime) + ':下卖单成功！下单数量：' + str(coinpark_config.minamount) + '    交易次数：' + str(tradecount))
                                # 记录本次下单价格
                                pricelist.append(price)
                                break;
                        except Exception as ex:
                            time.sleep(0.5)
                print('网络延迟：' + str(end1) + '秒   下单延迟：'  +  str(end2) + '秒')
        except Exception as ex:
            print(ex)
            time.sleep(coinpark_config.sleeptime)




# 程序主入口
if __name__ == '__main__':
    try:
        currency = get_balance(coinpark_config.tradecurrency)
        time.sleep(1)
        usdt = get_balance(coinpark_config.basecurrency)
    except Exception as ex:
        print(ex)
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print('START FROM ' + str(nowTime) + '  CURRENCY:' + str(currency) + '   USDT:' + str(usdt))
    log=['START FROM ' + str(nowTime) + '  CURRENCY:' + str(currency) + '   USDT:' + str(usdt)]
    csvwriter2.writerow(log)
    threads.append(threading.Thread(target=strategy, args=()))
    threads.append(threading.Thread(target=cancelOrdersThread, args=()))
    threads.append(threading.Thread(target=calProfitThread, args=()))
    threads.append(threading.Thread(target=balanceAccountThread, args=()))
    for t in threads:
        t.setDaemon(True);
        t.start()
    t.join()

