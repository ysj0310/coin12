import time
import pyupbit
import datetime
import numpy as np

access = ""          # 본인 값으로 변경
secret = ""          # 본인 값으로 변경
upbit = pyupbit.Upbit(access, secret)

print(upbit.get_balance("KRW-BTC"))     # KRW-BTC 조회
print(upbit.get_balance("KRW"))         # 보유 현금 조회

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma20(ticker):
    """20일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=20)
    ma20 = df['close'].rolling(20).mean().iloc[-1]
    return ma20

def get_ma5(ticker):
    """5일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=5)
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    return ma5

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def get_ror(k=0.5):
    df = pyupbit.get_ohlcv("KRW-BTC", count = 7)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)
    fee = 0.0005
    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'] - fee,
                         1)

    ror = df['ror'].cumprod()[-2]
    return ror

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

j=0.5
# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=5)

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price("KRW-BTC", j)
            current_price = get_current_price("KRW-BTC")
            buy_price = 0
            ma20 = get_ma20("KRW-BTC")
            ma5 = get_ma5("KRW-BTC")
            if target_price < current_price and ma20 < current_price and ma5 < current_price and ma5 > ma20:
                krw = get_balance("KRW")
                if krw > 5000:
                    upbit.buy_market_order("KRW-BTC", krw*0.9995)
                    buy_price = current_price
            if buy_price*0.95 > current_price or ma20 > ma5:
                btc = get_balance("BTC")
                upbit.sell_market_order("KRW-BTC", btc*0.9995)
                print("sale")
        else:
            btc = get_balance("BTC")
            current_price = get_current_price("KRW-BTC")
            if btc > 5000/current_price:
                upbit.sell_market_order("KRW-BTC", btc*0.9995)
                print("sale")
            a=[]
            b=[]
            for k in np.arange(0.1, 1.0, 0.1):
                ror = get_ror(k)
                a.append(ror)
                b.append(k)

            j=b[a.index(max(a))]

        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)