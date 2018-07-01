# coding=utf-8
import time
import threading
from FCOIN.fcoinapi import Fcoin
from FCOIN.fcoin_client import fcoin_client
from FCOIN import config
import csv
import datetime
import ccxt
import sys
##############################全局变量################################################
# 记录最新买卖价
bid1 = 0
ask1 = 0
bid2 = 0
ask2 = 0
#最小交易量
minamount = 0.5
minpercent = 0.003
#货币对
pair = ''
pair2 = ''
# 线程池
threads = []
# 实例化FCOIN接口
fcoin = Fcoin()
fcoin.auth(config.apikey, config.secretkey)
huobi = ccxt.huobipro()
refresh_flag1 = 0
refresh_flag2 = 0
maxpercent1 = -10
maxpercent2 = -10
filename1 = ''

######################################################################################

# 执行交易策略
def runStrategy():
    try:
        global bid1, ask1,refresh_flag1, bid2, ask2, refresh_flag2,maxpercent1,maxpercent2
        if(refresh_flag1 == 0):
            print("FCOIN行情数据未更新！")
            time.sleep(0.5)
        elif(refresh_flag2 == 0):
            print("HUOBI行情数据未更新！")
            time.sleep(0.5)
        else:
            refresh_flag1 = 0
            refresh_flag2 = 0
            if(ask1 >0 and ask2 >0 and bid1 >0 and bid2 >0):
                # FCOIN BUY OCX SELL
                nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                spread1 = round(bid2 - ask1,4)
                percent1 = round(spread1*100/bid2,4)
                spread2 = round(bid1 - ask2,4)
                percent2 = round(spread2*100/bid1,4)
                if(percent1 > maxpercent1):
                    maxpercent1 = percent1

                if (percent2 > maxpercent2):
                    maxpercent2 = percent2
                print('***************************************************************************')
                print(str(nowTime) + '  FCOIN BUY HUOBI SELL: ' + str(percent1) + '%   最大价差:' + str(maxpercent1) + '%')
                print(str(nowTime) + '  HUOBI BUY FCOIN SELL: ' + str(percent2) + '%   最大价差:' + str(maxpercent2) + '%')
            time.sleep(1)
    except Exception as ex:
        time.sleep(0.5)

# 执行策略的线程
def strategyThread():
    while (True):
        runStrategy()

def depth(data):
    global bid1, ask1,refresh_flag1
    if data:
        try:
            bidamount = 0
            askamount = 0
            bids = data['bids']
            asks = data['asks']
            for i in range(20):
                bidamount = bidamount + bids[i*2+1]
                if(bidamount >= minamount*3):
                    bid1 = bids[i*2]
                    break

            for i in range(20):
                askamount = askamount + asks[i*2+1]
                if(askamount >= minamount*3):
                    ask1 = asks[i*2]
                    break

            refresh_flag1 = 1
        except Exception as ex:
            print('FCOIN获取行情异常' + str(ex))

def receive_data_thread1():
    while 1:
        time.sleep(0.5)
        client.subscribe_depth(pair, 'L20')


def receive_data_thread2():
    global bid2, ask2, refresh_flag2
    while 1:
        time.sleep(0.5)
        try:
            res = huobi.fetch_order_book(pair2,10)
            bidamount = 0
            askamount = 0
            for item in res['bids']:
                bidamount = bidamount + item[1]
                if (bidamount >= minamount * 3):
                    bid2 = item[0]
                    break

            for item in res['asks']:
                askamount = askamount + item[1]
                if (askamount >= minamount * 3):
                    ask2 = item[0]
                    break

            refresh_flag2 = 1
        except Exception as ex:
            print('HUOBI获取行情异常' + str(ex))

def recordSpread():
    global maxpercent1,maxpercent2
    while(True):
        time.sleep(60)
        try:
            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log = [str(nowTime) + ',' + str(maxpercent1) + '%,' + str(maxpercent2) + '%']
            out1 = open(filename1, 'a', newline='')
            csvwriter = csv.writer(out1, dialect='excel')
            csvwriter.writerow(log)
            out1.close()
            maxpercent1 = -10
            maxpercent2 = -10
            print('SPREAD RECORDED!')
        except Exception as ex:
            print(ex)

# 程序主入口
if __name__ == '__main__':
    if len(sys.argv) > 3:
        if sys.argv[1] != '':
            pair = sys.argv[1]

        if sys.argv[2] != '':
            pair2 = sys.argv[2]

    client = fcoin_client()
    client.stream.stream_depth.subscribe(depth)
    client.start()
    while not client.isConnected:
        print('等待连接行情服务器！')
        time.sleep(2)
    client.subscribe_depth(pair, 'L20')
    threads.append(threading.Thread(target=receive_data_thread1, args=()))
    threads.append(threading.Thread(target=receive_data_thread2, args=()))
    threads.append(threading.Thread(target=strategyThread, args=()))
    threads.append(threading.Thread(target=recordSpread, args=()))

    print('PAIR1:' + str(pair) + '   PAIR2:' + str(pair2))
    filename1 = pair + '_spread.csv'
    print(filename1)
    for t in threads:
        t.setDaemon(True);
        t.start()
    t.join()

