import ccxt
import pandas as pd

exchange = ccxt.binance({
    'options': {'defaultType': 'future'}
})

symbol = "BTC/USDT"
print(f"--- FONDATION {symbol} ---")

try:
    ticker = exchange.fetch_ticker(symbol)
    print(f"Ticker Bid: {ticker.get('bidVolume')}, Ask: {ticker.get('askVolume')}")
except Exception as e:
    print(f"Ticker Error: {e}")

try:
    funding = exchange.fetch_funding_rate(symbol)
    print(f"Funding Rate: {funding.get('fundingRate')}")
except Exception as e:
    print(f"Funding Error: {e}")

try:
    ob = exchange.fetch_order_book(symbol, limit=20)
    bid_vol = sum(b[1] for b in ob['bids'])
    ask_vol = sum(a[1] for a in ob['asks'])
    print(f"OrderBook Bid Vol: {bid_vol}, Ask Vol: {ask_vol}")
except Exception as e:
    print(f"OB Error: {e}")
