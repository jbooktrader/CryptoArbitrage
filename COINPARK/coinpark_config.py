###############################参数定义##############################################
#客户名称
clientname = 'sunlc-BTC'
# API KEY
apikey = '389b943c6fd40485303d5c453657403454a30f10'
secretkey = '10b750ad8c28e5469ec45a9da93d8499a3aa2eac'
# 刷单速度，0.5-超慢速 1-慢速  2-中速  3-快速
speed=3
# 起始货币数量
startamount = 0.5
startmoney = 3000
# 交易货币
tradecurrency = 'BTC'
# 基础币种
basecurrency = 'USDT'
# 交易对
pair = tradecurrency + '_' + basecurrency
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
#返利比例
profitpercent = 0.3

