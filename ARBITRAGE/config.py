###############################参数定义##############################################
#客户名称
clientname = ''
# API KEY
apikey1 = ''
secretkey1 = ''
apikey2 = ''
secretkey2 = ''
#交易速度
speed = 3
#起始资金
startamount = 10
startmoney = 10000
# 交易货币
tradecurrency1 = 'eth'
tradecurrency2 = 'ETH'
# 基础币种
basecurrency1 = 'usdt'
basecurrency2 = 'USDT'
# 交易对
pair1 = tradecurrency1 + basecurrency1
pair2 = tradecurrency2 + '/' + basecurrency2
# 下单时间间隔（秒）
interval = 12/speed
# 最小下单数量
minamount = startamount*speed/50
#检查和取消订单时间
sleeptime=300/speed
# 最小价差
minspread = 0.2
# 滑点
slippage = 0.01
#最小交易量
minamount = 0.1
#套利价差百分比
minpercent = 0.002

