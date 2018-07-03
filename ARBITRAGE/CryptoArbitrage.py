# coding=utf-8
import ccxt
import time
import threading
import json
import sys

# 线程池
threads = []
# 交易所列表
exchanges = []
# 全局变量，卖价列表
asks = {}
# 全局变量，买价列表
bids = {}
# 全局变量，记录最大的价差比例
maxpercent = {}
# 全局变量，最小每次下单的数量
minamount = 2
# 全局变量，所有的交易对列表
pairs={}

# 获取交易所ORDER BOOK
def getOrderBook(pair, exchange):
    exchangeName = exchange
    market = getattr(ccxt, exchangeName)()
    limit = 10
    while True:
        try:
            orderbook = market.fetch_order_book(pair['name'], limit)
            bid = orderbook['bids']
            ask = orderbook['asks']
            global bids
            global asks
            tempBidAmount = 0
            tempAskAmount = 0
            # 判断报单的数量是否大于最小交易量
            for i in range(len(bid)):
                tempBidAmount = tempBidAmount + bid[i][1]
                if( tempBidAmount>= minamount):
                    bids[pair['name']][exchangeName] = bid[i][0]
                    break
            # 判断报单的数量是否大于最小交易量
            for j in range(len(ask)):
                tempAskAmount = tempAskAmount + ask[j][1]
                if( tempAskAmount>= minamount):
                    asks[pair['name']][exchangeName] = ask[j][0]
                    break

            # print('bids:' + str(bids))
            # print('asks:' + str(asks))
            time.sleep(2)
        except:
            info = sys.exc_info()
            print(info[0], ":", info[1])
            # 如果交易所发生连接中断，则从DICT中移除之前的报价
            try:
                bids[pair['name']].pop(exchangeName)
                asks[pair['name']].pop(exchangeName)
            except:
                time.sleep(5)
            time.sleep(5)

# 每个交易所的币种对创建一个线程
def createThread():
    # 取交易所列表
    with open("exchangelist.json", 'r') as f1:
        exchangelist = json.loads(f1.read())
        for i in exchangelist:
            exchanges.append(exchangelist[i]['name'])

    for i in range(len(exchanges)):
        try:
            # 取每个交易所的币种对列表，每个交易所的每个币种对创建一个行情监控线程，并且初始化bids,asks,maxpercent全局参数
            with open(exchanges[i] + '.json', 'r') as f2:
                pairlist = json.loads(f2.read())
                pairs[exchanges[i]] = pairlist
                for j in pairlist:
                    threads.append(threading.Thread(target=getOrderBook, args=(pairlist[j], exchanges[i],)))
                    bids[pairlist[j]['name']] = {}
                    asks[pairlist[j]['name']] = {}
                    global maxpercent
                    maxpercent[pairlist[j]['name']] = 0
        except Exception as ex:
            print(ex)

# 根据VALUE获取KEY值
def get_key(dict, value):
    return [k for k, v in dict.items() if v == value]

# 价差监控策略，每个交易对创建一个线程，监控该交易对所有交易所的价格
def strategy(pair):
    while(True):
        try:
            bestbid = max(bids[pair].values())
            bestask = min(asks[pair].values())
            spread = round(bestbid - bestask,8)
            percent = round((spread)*100/bestask, 4)
            sellmarket = get_key(bids[pair], bestbid)
            buymarket = get_key(asks[pair], bestask)
            global maxpercent
            # 记录历史最大价差比例
            if(maxpercent[pair] is None):
                maxpercent[pair] = percent
            elif(percent > maxpercent[pair]):
                maxpercent[pair] = percent

            # 如果价差比例大于0.5%，则给出显著提示
            if(percent >= 0.5):
                print(pair + '\033[1;31;40m价差：' + str(spread) + '   比例：' + str(percent) + '%\033[0m' + '  最大比例：' + str(maxpercent[pair]) + '%')
            else:
                print(pair + '价差：' + str(spread) + '   比例：' + str(percent) + '%' + '  最大比例：' + str(maxpercent[pair]) + '%')
            print(pair + '买入价：' + str(bestask) + ' 买入市场：' + str(buymarket) + ' 卖出价：' + str(bestbid) + ' 卖出市场：' + str(sellmarket))
            print('*************************************************************************************************************')
            time.sleep(5)
        except:
            info = sys.exc_info()
            print(info[0], ":", info[1])
            time.sleep(10)

# MAIN方法
if __name__ == '__main__':
    # 创建行情监控线程
    createThread()
    # 创建策略线程
    threads.append(threading.Thread(target=strategy, args=('BTC/USDT',)))
    threads.append(threading.Thread(target=strategy, args=('ETH/USDT',)))
    threads.append(threading.Thread(target=strategy, args=('EOS/USDT',)))
    threads.append(threading.Thread(target=strategy, args=('ETC/USDT',)))
    threads.append(threading.Thread(target=strategy, args=('LTC/USDT',)))
    threads.append(threading.Thread(target=strategy, args=('BCH/USDT',)))
    # threads.append(threading.Thread(target=strategy, args=('AE/USDT',)))
    # threads.append(threading.Thread(target=strategy, args=('ADA/USDT',)))
    threads.append(threading.Thread(target=strategy, args=('XRP/USDT',)))
    # threads.append(threading.Thread(target=strategy, args=('QTUM/USDT',)))
    for t in threads:
        t.setDaemon(True);
        t.start()
    t.join()






