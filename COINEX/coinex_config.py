###############################参数定义##############################################
#客户名称
clientname = 'sunlc-ETH'
# API KEY
apikey = ''
secretkey = ''
# 刷单速度，0.5-超慢速 1-慢速  2-中速  3-快速
speed=2
# 起始货币数量
startamount = 5
startmoney = 2500
# 交易货币
tradecurrency = 'ETH'
# 基础币种
basecurrency = 'USDT'
# 交易对
pair = tradecurrency  + basecurrency
# 下单时间间隔（秒）
interval = 12/speed
# 最小下单数量
minamount = startamount*speed/50
#检查和取消订单时间
sleeptime=300/speed
# 最小价差
minspread = 0.2
# 滑点
slippage = 0.0001

