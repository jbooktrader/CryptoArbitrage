# coding=utf-8
import time
import threading
from COINEX import coinex_config
import csv
from COINEX.coinexapi import CoinEx
import datetime
import schedule

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
# 实例化COINEX接口
coinex = CoinEx(coinex_config.apikey, coinex_config.secretkey)
refresh_flag = 0
filename1 = 'coinex_trades.csv'
filename2 = 'coinex_log.csv'
out1 = open(filename1, 'a', newline='')
out2 = open(filename2, 'a', newline='')
csvwriter = csv.writer(out1, dialect='excel')
csvwriter2 = csv.writer(out2, dialect='excel')
starttime = time.time()
profitpercent = 0.2

######################################################################################
# 取账户余额信息
def get_balance(symbol):
    try:
        res = coinex.balance()
        return (float(res[symbol]['available']) + float(res[symbol]['frozen']))
    except Exception as ex:
        print(ex)
        print(symbol + '取账户余额失败！')

# 利润统计线程
def calProfitThread():
    global tradecount,starttime,profitpercent
    usdtamount = 0
    while (True):
        time.sleep(60)
        sum = 0
        try:
            usdtamount = get_balance(coinex_config.basecurrency)
            for i in pricelist:
                sum = sum + i
            avgprice = round(sum / tradecount, 2)
            fee = avgprice * tradecount * 0.001 * coinex_config.minamount
            runtime = round((time.time() - starttime)/60,1)
            profit = round(fee * profitpercent,2)
            dailyprofit = round(fee*profitpercent*86400/(time.time()-starttime),2)
            print('**********************************利润统计**********************************')
            print('交易次数：'+ str(tradecount)  +'    成交均价:' + str(avgprice) + '   预计手续费支出：' + str(fee) + '    USDT余额：' + str(round(usdtamount,2)))
            print('运行时间：' + str(runtime) + '分钟   预计利润：' + str(profit) + 'USDT    24小时预计利润：' + str(dailyprofit) + 'USDT')
            print('****************************************************************************')
            log=['交易次数：'+ str(tradecount)  +'    成交均价:' + str(avgprice) + '   预计手续费支出：' + str(fee) + '    USDT余额：' + str(round(usdtamount,2))]
            csvwriter2.writerow(log)
        except Exception as ex:
            print(ex)
            print('计算成交均价出错！')


# 检查补单的线程
def balanceAccountThread():
    while (True):
        time.sleep(60)
        try:
            accountbalance = get_balance(coinex_config.tradecurrency)
            if (accountbalance - coinex_config.startamount >= coinex_config.minamount * 2):
                print('需要卖出补单的数量：' + str(round(accountbalance - coinex_config.startamount, 4)))
                amount = round(coinex_config.minamount * 2, 4)
                count = 0
                while (count < 5):
                    try:
                        count = count + 1
                        orderid = coinex.order_limit(coinex_config.pair,'sell',str(amount),str(round(bid1 * 0.995, 4)))
                        print(orderid)
                        if (orderid > 0):
                            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            trade = [nowTime, 'coinex', coinex_config.pair, 'sell', amount, bid1]
                            csvwriter.writerow(trade)
                            print('补单卖出：' + str(amount))
                            break;
                    except Exception as ex:
                        time.sleep(0.5)
            elif (coinex_config.startamount - accountbalance >= coinex_config.minamount * 2):
                print('需要买入补单的数量：' + str(round(coinex_config.startamount - accountbalance, 4)))
                amount = round(coinex_config.minamount * 2, 4)
                count = 0
                while (count < 5):
                    try:
                        count = count + 1
                        orderid = coinex.order_limit(coinex_config.pair,'buy',str(amount),str(round(ask1 * 1.005, 4)))
                        print(orderid)
                        if (orderid > 0):
                            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            trade = [nowTime, 'coinex', coinex_config.pair, 'buy', amount, bid1]
                            csvwriter.writerow(trade)
                            print('补单买入：' + str(amount))
                            break;
                    except Exception as ex:
                        time.sleep(0.5)
            else:
                print('差额：' + str(round(accountbalance - coinex_config.startamount, 4)) + '  无需补单')
        except Exception as ex:
            print(ex)
            time.sleep(2)

# 定时取消未成交订单的线程
def cancelOrdersThread():
    while (True):
        time.sleep(60)
        try:
            orderlist = coinex.order_pending(coinex_config.pair)
            print(orderlist)
            print('未成交：' + str(len(orderlist)))
            count = 0
            for item in orderlist:
                try:
                    orderid = item['id']
                    coinex.order_pending_cancel(coinex_config.pair,orderid)
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
            time.sleep(coinex_config.interval)
            start1 = time.time()
            res = coinex.market_depth(coinex_config.pair)
            end1 = round(time.time() - start1,3)
            bid1 = float(res['bids'][0][0])
            ask1 = float(res['asks'][0][0])
            if (bid1 > 0 and ask1 > 0):
                price = round((bid1 + ask1) / 2, 4)
                print('盘口买价:' + str(bid1) + '  盘口卖价:' + str(ask1) + ' 下单价:' + str(price))
                start2 = time.time()
                buyorderid = coinex.order_limit(coinex_config.pair,'buy',coinex_config.minamount,round(price + coinex_config.slippage, 4))
                print(buyorderid)
                if(buyorderid > 0):
                    tradecount = tradecount + 1
                    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                    trade = [nowTime, 'coinex', coinex_config.pair, 'buy', coinex_config.minamount, price]
                    csvwriter.writerow(trade)
                    print(str(nowTime) + ':下买单成功！下单数量：' + str(coinex_config.minamount) + '    交易次数：' + str(tradecount))
                    pricelist.append(price)
                    count = 0
                    while (count < 5):
                        try:
                            count = count + 1
                            sellorderid = coinex.order_limit(coinex_config.pair, 'sell', coinex_config.minamount,round(price - coinex_config.slippage, 4))
                            print(sellorderid)
                            if (sellorderid > 0):
                                end2 = round(time.time() - start2, 3)
                                tradecount = tradecount + 1
                                nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                                trade = [nowTime, 'coinex', coinex_config.pair, 'sell', coinex_config.minamount, price]
                                csvwriter.writerow(trade)
                                print(str(nowTime) + ':下卖单成功！下单数量：' + str(coinex_config.minamount) + '    交易次数：' + str(tradecount))
                                pricelist.append(price)
                                break;
                        except Exception as ex:
                            time.sleep(0.5)
                print('行情延迟：' + str(end1) + '秒   下单延迟：'  +  str(end2) + '秒')
        except Exception as ex:
            print(ex)
            time.sleep(coinex_config.interval)

if __name__ == '__main__':
    try:
        currency = get_balance(coinex_config.tradecurrency)
        time.sleep(1)
        usdt = get_balance(coinex_config.basecurrency)
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


