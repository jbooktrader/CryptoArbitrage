# coding=utf-8
import time
import threading
import csv
from COINBIG.coinbigapi import CoinBigClient
import datetime
import sys
##############################参数设置#################################################
# API KEY
apikey1 = str(sys.argv[1])
secretkey1 = str(sys.argv[2])
apikey2 = str(sys.argv[3])
secretkey2 = str(sys.argv[4])
# 刷单速度，0.5-超慢速 1-慢速  2-中速  3-快速
speed=float(sys.argv[5])
# 起始货币数量
startamount = float(sys.argv[6])
# 交易货币
tradecurrency = str(sys.argv[7])
# 基础币种
basecurrency = str(sys.argv[8])
# 交易对
pair = tradecurrency  + '_' + basecurrency
# 下单时间间隔（秒）
interval = 3
# 最小下单数量
minamount = 0.1
# 最小价差
minspread = 0.0002
# 滑点
slippage = 0.0001
#返利比例
profitpercent = 0.2
##############################全局变量################################################
# 交易次数
tradecount1 = 0
tradecount2 = 0
# 记录最新买卖价
bid1 = 0
ask1 = 0
# 价格列表
pricelist = []
# 线程池
threads = []
# 实例化COINEX接口
coinbig1 = CoinBigClient(apikey1, secretkey1)
coinbig2 = CoinBigClient(apikey2, secretkey2)
filename1 = 'coinbig_trades.csv'
filename2 = 'coinbig_log.csv'
starttime = time.time()
# 返利比例
profitpercent = 0.2
currency1 = 0
currency2 = 0
######################################################################################
# 取账户余额信息
def get_balance1(symbol):
    try:
        res = coinbig1.fetch_balance(symbol)
        return float(res['total'])
    except Exception as ex:
        print(ex)
        print(symbol + '取账户1余额失败！')

def get_balance2(symbol):
    try:
        res = coinbig2.fetch_balance(symbol)
        return float(res['total'])
    except Exception as ex:
        print(ex)
        print(symbol + '取账户2余额失败！')


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
            global bid1, ask1, tradecount, refresh_flag,currency1,currency2
            start1 = time.time()
            res = coinbig1.fetch_order_book(pair)
            print(res)
            end1 = round(time.time() - start1,3)
            bid1 = float(res['bids'][0][0])
            ask1 = float(res['asks'][0][0])
            price = round((bid1+ask1)/2,4)
            print('盘口买价:' + str(bid1) + '  盘口卖价:' + str(ask1) + '   下单价：' + str(price))
            print('行情延迟：' + str(end1) + '秒')

            if (bid1 > 0 and ask1 > 0 and (ask1-bid1)>= minspread):
                print('********交易开始********')
                #计算差额
                diff = round(currency1 + currency2 - startamount,4)
                print(diff)
                # 账号1的币比账号2的币少，则在账号1买入，账号2卖出，卖出量为账号2的数量
                if(currency1 < currency2):
                    sellamount = currency2
                    buyamount = currency2 - diff
                    print('账号1买入:' + str(buyamount) + '  账号2卖出:' + str(sellamount));
                    sellorderid = coinbig2.create_order(pair,price,'0.1','sell')
                    if(sellorderid > 0 and buyamount >= minamount):
                        buyorderid = coinbig1.create_order(pair,price,'0.1','buy')
                    print('买入ID：' + str(buyorderid) + ' 卖出ID：' + str(sellorderid))
                    time.sleep(10)
                    sellstatus = coinbig2.fetch_order(sellorderid)['orderinfo']['status']
                    buystatus = coinbig1.fetch_order(buyorderid)['orderinfo']['status']
                    print('买入订单状态：' + str(buystatus) + '   卖出订单状态：' + str(sellstatus))
                    if(buystatus != 0):
                        coinbig1.cancel_order(buyorderid)
                    if (sellstatus != 0):
                        coinbig2.cancel_order(sellorderid)

                # 账号2的币比账号1的币少，则在账号2买入，账号1卖出，卖出量为账号1的数量
                else:
                    sellamount = currency1
                    buyamount = currency1-diff
                    print('账号2买入:' + str(buyamount) + '  账号1卖出:' + str(sellamount));
                    sellorderid = coinbig1.create_order(pair, price, '0.1', 'sell')
                    if (sellorderid > 0 and buyamount >= minamount):
                        buyorderid = coinbig2.create_order(pair, price, '0.1', 'buy')
                    print('买入ID：' + str(buyorderid) + ' 卖出ID：' + str(sellorderid))
                    time.sleep(10)
                    sellstatus = coinbig1.fetch_order(sellorderid)
                    buystatus = coinbig2.fetch_order(buyorderid)
                    print('买入订单状态：' + str(buystatus) + '   卖出订单状态：' + str(sellstatus))
                    if (buystatus != 0):
                        coinbig2.cancel_order(buyorderid)
                    if (sellstatus != 0):
                        coinbig1.cancel_order(sellorderid)

                print('********交易完成********')
                currency1 = get_balance1(tradecurrency)
                currency2 = get_balance2(tradecurrency)
                time.sleep(10)
        except Exception as ex:
            print(ex)
            time.sleep(interval)

if __name__ == '__main__':
    try:
        currency1 = get_balance1(tradecurrency)
        currency2 = get_balance2(tradecurrency)
        time.sleep(1)
        usdt1 = get_balance1(basecurrency)
        usdt2 = get_balance2(basecurrency)
    except Exception as ex:
        print(ex)
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    content = '开始时间：' + str(nowTime) + '  初始币量合计:' + str(currency1+currency2) + '   初始USDT合计:' + str(usdt1+usdt2)
    print(content)

    #log(filename2,content)
    threads.append(threading.Thread(target=strategy, args=()))
    for t in threads:
        t.setDaemon(True);
        t.start()
    t.join()


