# coding=utf-8
import time
import threading
import csv
from COINEX.coinexapi import Coinex
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
# 实例化COINPARK接口
coinex = Coinex()
coinex.auth('', '')
refresh_flag = 0
filename1 = 'coinpark_trades.csv'
filename2 = 'coinpari_log.csv'
out1 = open(filename1, 'a', newline='')
out2 = open(filename2, 'a', newline='')
csvwriter = csv.writer(out1, dialect='excel')
csvwriter2 = csv.writer(out2, dialect='excel')
starttime = time.time()
profitpercent = 0.3

######################################################################################

# 执行交易策略
def strategy():
    while(True):
        try:
            global bid1, ask1, tradecount, refresh_flag
            # time.sleep(coinpark_config.sleeptime)
            # time.sleep(2)
            start1 = time.time()
            res = coinex.get_market_depth('BTCUSDT')
            end1 = round(time.time() - start1,3)
            bid1 = res['data']['bids'][0][0]
            ask1 = res['data']['asks'][0][0]
            print('BID:' + str(bid1) + '    ASK:' + str(ask1))
            print(end1)

        except Exception as ex:
            print(ex)
            time.sleep(0.2)

if __name__ == '__main__':
    threads.append(threading.Thread(target=strategy, args=()))
    for t in threads:
        t.setDaemon(True);
        t.start()
    t.join()


