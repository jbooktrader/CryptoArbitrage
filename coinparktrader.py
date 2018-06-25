# coding=utf-8
import time
import threading
import coinpark_config
import csv
from COINPARK.coinparkapi import CoinPark

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
coinpark.auth(coinpark_config.apikey,coinpark_config.secretkey)
refresh_flag = 0
filename1 = 'coinpark_trades.csv'
filename2 = 'coinpari_log.csv'
out1 = open(filename1, 'a', newline='')
out2 = open(filename2, 'a', newline='')
csvwriter = csv.writer(out1, dialect='excel')
csvwriter2 = csv.writer(out2, dialect='excel')


######################################################################################
# 执行交易策略
def runStrategy():
    try:
        global bid1, ask1, tradecount, refresh_flag
        start = time.time()
        res = coinpark.get_market_depth(coinpark_config.pair)
        end = time.time() - start
        bid1 = res['result']['bids'][0]['price']
        ask1 = res['result']['asks'][0]['price']
        print('BID:' + str(bid1) + ' ASK:' + str(ask1))
        print(end)
        balance = coinpark.get_balance()
        # print(balance)
        buy = coinpark.create_order(coinpark_config.pair,'400','0.01','1')
        cancel = coinpark.cancel_order('11111')
        orderlist = coinpark.get_orderlist(coinpark_config.pair)
        orderdetail = coinpark.get_orderdetail('11111')
        #print(buy)
        time.sleep(5)
    except Exception as ex:
        print(ex)
        time.sleep(1)




# 执行策略的线程
def strategyThread():
    while (True):
        runStrategy()


# 程序主入口
if __name__ == '__main__':
    threads.append(threading.Thread(target=strategyThread, args=()))
    for t in threads:
        t.setDaemon(True);
        t.start()
    t.join()

