# coding=utf-8
import time
import threading
import csv
from COINEX.coinexapi import CoinEx
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
pair = tradecurrency  + basecurrency
# 下单时间间隔（秒）
interval = 12/speed
# 最小下单数量
minamount = round(startamount*speed/50,2)
#检查和取消订单时间
sleeptime=300/speed
# 最小价差
minspread = 0.2
# 滑点
slippage = 0.01
#返利比例
profitpercent = 0.2
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
coinex = CoinEx(apikey, secretkey)
refresh_flag = 0
filename1 = 'coinex_trades.csv'
filename2 = 'coinex_log.csv'
starttime = time.time()
# 返利比例
profitpercent = 0.2
#挖矿难度
difficulty = 0
#每小时挖矿限额
tradelimit = 999
#本小时已挖矿金额
totalfee= 0
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
    global tradecount,starttime,profitpercent,difficulty,tradelimit,totalfee
    usdtamount = 0
    while (True):
        time.sleep(120)
        sum = 0
        try:
            difficulty = float(coinex.order_mining_difficulty()['difficulty'])
            cetprice = float(coinex.market_depth('CETUSDT')['bids'][0][0])
            tradelimit = round(difficulty * cetprice,2)
            usdtamount = get_balance(basecurrency)
            for i in pricelist:
                sum = sum + i
            avgprice = round(sum / tradecount, 2)
            fee = avgprice * tradecount * 0.001 * minamount
            runtime = round((time.time() - starttime)/60,1)
            profit = round(fee * profitpercent,2)
            # dailyprofit = round(fee*profitpercent*86400/(time.time()-starttime),2)
            dailyprofit = round(tradelimit*24*profitpercent,2)
            content = '交易次数：'+ str(tradecount)  +'    成交均价:' + str(avgprice)  + '   USDT余额：' + str(round(usdtamount,2))
            print('**********************************利润统计**********************************')
            print(content)
            # print('运行时间：' + str(runtime) + '分钟   预计利润：' + str(profit) + 'USDT    24小时预计利润：' + str(dailyprofit) + 'USDT')
            print('当前挖矿难度：' + str(difficulty) + '个／小时   每小时挖矿限额：' + str(tradelimit) + 'USDT  24小时预计利润：' + str(dailyprofit) + 'USDT')
            print('运行时间：' + str(runtime) + '分钟   本小时手续费支出：' + str(totalfee) + 'USDT   累计手续费支出：' +  str(fee) + 'USDT')
            print('****************************************************************************')
            log(filename2,content)
        except Exception as ex:
            print(ex)
            print('计算成交均价出错！')


# 检查补单的线程
def balanceAccountThread():
    while (True):
        time.sleep(120)
        try:
            accountbalance = get_balance(tradecurrency)
            if (accountbalance - startamount >= minamount * 2):
                print('需要卖出补单的数量：' + str(round(accountbalance - startamount, 4)))
                amount = round(minamount * 2, 4)
                count = 0
                while (count < 5):
                    try:
                        count = count + 1
                        orderid = coinex.order_limit(pair,'sell',str(amount),str(round(bid1 * 0.995, 2)))
                        if (orderid > 0):
                            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            trade = [nowTime, 'coinex', pair, 'sell', amount, bid1]
                            log(filename1,trade)
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
                        orderid = coinex.order_limit(pair,'buy',str(amount),str(round(ask1 * 1.005, 4)))['id']
                        if (orderid > 0):
                            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            trade = [nowTime, 'coinex', pair, 'buy', amount, bid1]
                            log(filename1,trade)
                            print('补单买入：' + str(amount))
                            break;
                    except Exception as ex:
                        time.sleep(0.5)
            else:
                print('差额：' + str(round(accountbalance - startamount, 4)) + '  无需补单')
        except Exception as ex:
            print(ex)
            time.sleep(2)

# 定时取消未成交订单的线程
def cancelOrdersThread():
    while (True):
        time.sleep(150)
        try:
            orderlist = coinex.order_pending(pair)
            size = float(orderlist['count'])
            print('未成交：' + str(size))
            if(size > 0):
                count = 0
                for item in orderlist['data']:
                    try:
                        orderid = item['id']
                        coinex.order_pending_cancel(pair,orderid)
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

#记录交易日志
def log(filename,content):
    out = open(filename, 'a', newline='')
    csvwriter = csv.writer(out, dialect='excel')
    csvwriter.writerow(content)
    out.close()


def autoSell():
    while (True):
        time.sleep(120)
        try:
            cetamount = get_balance('CET')
            if (cetamount > 1):
                bid = float(coinex.market_depth('CETUSDT')['bids'][0][0])
                price = round(bid * 0.95, 4)
                amount = round(cetamount, 0) - 1
                print(coinex.order_limit('CETUSDT', 'sell', amount, price)['id'])
                print('CET余额：' + str(cetamount) + '  自动卖出！卖出价：' + str(price))
            else:
                print('CET余额：' + str(cetamount) + '  无需卖出！')
        except Exception as ex:
            print(ex)

# 执行交易策略
def strategy():
    while(True):
        try:
            global bid1, ask1, tradecount, refresh_flag,totalfee
            time.sleep(interval)
            minute = datetime.datetime.now().minute
            if (minute == 0):
                totalfee = 0
            start1 = time.time()
            res = coinex.market_depth(pair)
            end1 = round(time.time() - start1,3)
            bid1 = float(res['bids'][0][0])
            ask1 = float(res['asks'][0][0])
            if(tradelimit < totalfee * 0.9):
                print('本小时挖矿限额已满，暂停挖矿。')
            elif (bid1 > 0 and ask1 > 0):
                price = round((bid1 + ask1) / 2, 4)
                print('盘口买价:' + str(bid1) + '  盘口卖价:' + str(ask1) + ' 下单价:' + str(price))
                start2 = time.time()
                buyorderid = coinex.order_limit(pair,'buy',minamount,round(price + slippage, 2))['id']
                if(buyorderid > 0):
                    tradecount = tradecount + 1
                    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                    trade = [nowTime, 'coinex', pair, 'buy', minamount, price]
                    totalfee = totalfee + round(price*minamount*0.001,4)
                    log(filename1,trade)
                    print(str(nowTime) + ':下买单成功！下单数量：' + str(minamount) + '    交易次数：' + str(tradecount))
                    pricelist.append(price)
                    count = 0
                    while (count < 5):
                        try:
                            count = count + 1
                            sellorderid = coinex.order_limit(pair, 'sell', minamount,round(price - slippage, 2))['id']
                            if (sellorderid > 0):
                                end2 = round(time.time() - start2, 3)
                                tradecount = tradecount + 1
                                nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                                trade = [nowTime, 'coinex', pair, 'sell', minamount, price]
                                totalfee = totalfee + round(price * minamount * 0.001, 4)
                                log(filename1,trade)
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
    content = '开始时间：' + str(nowTime) + '  初始币量:' + str(currency) + '   初始USDT:' + str(usdt)
    print(content)
    log(filename2,content)
    threads.append(threading.Thread(target=strategy, args=()))
    threads.append(threading.Thread(target=cancelOrdersThread, args=()))
    threads.append(threading.Thread(target=calProfitThread, args=()))
    threads.append(threading.Thread(target=balanceAccountThread, args=()))
    threads.append(threading.Thread(target=autoSell, args=()))
    for t in threads:
        t.setDaemon(True);
        t.start()
    t.join()


