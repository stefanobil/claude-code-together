import ccxt
import pandas as pd
from rich.console import Console
from config import EXCHANGE_CONFIG

class DataFetcher:
    """Communication avancée avec Binance Futures V2.0 (Volumes, Open Interest)."""
    def __init__(self):
        exchange_class = getattr(ccxt, EXCHANGE_CONFIG['exchange_id'])
        exchange_params = {
            'enableRateLimit': EXCHANGE_CONFIG['enableRateLimit'],
            'options': EXCHANGE_CONFIG.get('options', {}) # Mode Derivatives
        }
        
        if EXCHANGE_CONFIG['api_key'] and EXCHANGE_CONFIG['api_key'] != 'TON_API_KEY_ICI':
            exchange_params['apiKey'] = EXCHANGE_CONFIG['api_key']
            exchange_params['secret'] = EXCHANGE_CONFIG['secret']
            
        self.exchange = exchange_class(exchange_params)

    def get_historical_data(self, symbol: str, timeframe: str, limit: int = 1000) -> pd.DataFrame:
        """Récupère l'Action des Prix (OHLCV)."""
        try:
            futures_symbol = f"{symbol}:USDT" if ":" not in symbol else symbol
            bars = self.exchange.fetch_ohlcv(futures_symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            from logger_manager import log_error # Lazy import
            err_msg = f"Crypto Data Error {symbol}: {e}"
            Console().print(f"[dim red]{err_msg}[/dim red]")
            log_error("DataFetcher", err_msg)
            return pd.DataFrame()
            
    def get_derivatives_data(self, symbol: str) -> dict:
        """V6.3: Scanne l'OI, Funding et le Volume Delta avec fallback sur OrderBook."""
        try:
            futures_symbol = f"{symbol}:USDT" if ":" not in symbol else symbol
            
            # --- 1. Funding Rate ---
            try:
                funding = self.exchange.fetch_funding_rate(futures_symbol)
                fr_value = float(funding.get('fundingRate', 0.0))
            except:
                fr_value = 0.0
            
            # --- 2. Volume Delta (Momentum) ---
            delta = 0.0
            try:
                ticker = self.exchange.fetch_ticker(futures_symbol)
                bid_v = ticker.get('bidVolume')
                ask_v = ticker.get('askVolume')
                
                # Fallback si le ticker n'a pas les volumes (cas fréquent sur certaines API)
                if bid_v is None or ask_v is None or (bid_v + ask_v == 0):
                    ob = self.exchange.fetch_order_book(futures_symbol, limit=20)
                    bid_v = sum(b[1] for b in ob['bids'])
                    ask_v = sum(a[1] for a in ob['asks'])
                
                delta = (bid_v - ask_v) / (bid_v + ask_v + 1e-9)
            except:
                delta = 0.0
            
            return {
                'funding_rate': fr_value,
                'volume_delta': delta
            }
        except Exception:
            from logger_manager import log_error
            import traceback
            log_error("DataFetcher_Derivatives", f"Derivatives error on {symbol}: {traceback.format_exc()}")
            return {'funding_rate': 0.0, 'volume_delta': 0.0}
            
    def get_btc_trend(self) -> str:
        """V6.0: Détermine la santé du marché via le Bitcoin."""
        try:
            df_btc = self.get_historical_data("BTC/USDT", "1h", limit=50)
            if df_btc.empty: return 'NEUTRAL'
            
            # SMA 20 (Court terme) vs SMA 50 (Moyen terme) sur BTC
            sma20 = df_btc['close'].rolling(20).mean().iloc[-1]
            sma50 = df_btc['close'].rolling(50).mean().iloc[-1]
            
            if df_btc['close'].iloc[-1] > sma20 and sma20 > sma50:
                return 'BULLISH'
            elif df_btc['close'].iloc[-1] < sma20 and sma20 < sma50:
                return 'BEARISH'
            return 'NEUTRAL'
        except Exception:
            return 'NEUTRAL'
    
    def get_current_price(self, symbol: str) -> float:
        try:
            futures_symbol = f"{symbol}:USDT" if ":" not in symbol else symbol
            return self.exchange.fetch_ticker(futures_symbol)['last']
        except:
            return 0.0

    def check_high_impact_news(self) -> bool:
        """V3.0: Protège le bot 60min avant et après une News US majeure (NFP, FOMC)."""
        import requests
        from datetime import datetime, timezone
        try:
            url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
            response = requests.get(url, timeout=5)
            if response.status_code != 200: return False
        except Exception as e:
            from logger_manager import log_error
            log_error("NewsShield", f"Failed to fetch news: {e}")
            return False

        try:
            data = response.json()
            now = datetime.now(timezone.utc)
            
            for event in data:
                if event.get('impact') == 'High' and event.get('country') == 'USD':
                    news_time = pd.to_datetime(event['date'], utc=True)
                    diff_minutes = abs((now - news_time).total_seconds()) / 60
                    if diff_minutes <= 60:
                        return True
            return False
        except Exception:
            return False
