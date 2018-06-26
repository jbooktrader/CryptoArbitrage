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
# 取账户余额信息
def get_balance(self,symbol):
    try:
        res = coinpark.get_balance();
        for currency in res['result'][0]['result']['assets_list']:
            if (currency['coin_symbol'] == symbol):
                return (float(currency['balance']) + float(currency['freeze']))
            else:
                print(symbol + '取账户余额失败！')
    except Exception as ex:
        print(symbol + '取账户余额失败！')




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
        orderid = coinpark.create_order('ETH_USDT','300','0.01','1')['result'][0]['result']
        print(orderid)
        time.sleep(1)
        orderdetail = coinpark.get_orderdetail(orderid)
        print(orderdetail['result'][0]['result']['unexecuted'])
        time.sleep(1)
        orderlist = coinpark.get_orderlist(coinpark_config.pair)
        print(orderlist)
        time.sleep(1)
        cancel = coinpark.cancel_order(orderid)
        print(cancel['result'][0]['result'])
        #
        #orderlist = coinpark.get_orderlist(coinpark_config.pair)

        time.sleep(1)
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

