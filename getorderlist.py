# coding=utf-8
import time
import threading
import csv
from COINEX.coinexapi import CoinEx
import datetime
import sys


if __name__ == '__main__':
    coinex = CoinEx('EDD92410E6EF4E27915FD784EE5CFBD2', '83B64C69F8FF4A2DA80714F46EA059884F6F6C71CBE6FE24')
    tradelist = []


    try:
        for i in range(1,100):
            list = coinex.order_finished('ETHUSDT',i)['data']
            out = open('tradedetails1.csv', 'a', newline='')
            csvwriter = csv.writer(out, dialect='excel')
            for item in list:
                date = datetime.datetime.fromtimestamp(item['create_time'])
                tradedetail = [str(date),item['market'],item['type'],item['deal_amount'],item['deal_money'],item['deal_fee']]
                print(tradedetail)
                tradelist.append(tradedetail)
                csvwriter.writerow(tradedetail)
            out.close()
            print('PAGE:' + str(i))
            time.sleep(1)

    except Exception as ex:
        print(ex)
        out.close()
        time.sleep(1)












