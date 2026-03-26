import pandas as pd
import numpy as np
from rich.console import Console
from config import TRADING_CONFIG
from data_fetcher import DataFetcher
from indicators import add_all_indicators
import os
import sys

# Forcer UTF-8 pour Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

console = Console()

def run_backtest(symbol: str, fetcher: DataFetcher):
    console.print(f"\n[bold cyan]-- Telechargement des Mathematiques sur {symbol}...[/bold cyan]")
    df = fetcher.get_historical_data(symbol, '1h', limit=1500)
    
    if df.empty: 
        return
    
    df = add_all_indicators(df)
    
    in_pos = False
    side = None
    entry_price = 0.0
    sl = 0.0
    tp = 0.0
    
    wins = 0
    losses = 0
    be_shots = 0
    
    pnl_pct = 100.0 
    
    for i in range(200, len(df)-1):
        row = df.iloc[i]
        
        if not in_pos:
            if row.get('ob_bullish', False):
                in_pos = True
                side = 'LONG'
                entry_price = row['close']
                sl = row['ob_bullish_level'] if not pd.isna(row.get('ob_bullish_level')) else (entry_price * 0.99)
                tp = entry_price + (abs(entry_price - sl) * TRADING_CONFIG['risk_reward_ratio'])
        else:
            if side == 'LONG':
                if row['low'] <= sl:
                    losses += 1
                    pnl_pct -= (TRADING_CONFIG['max_risk_per_trade_pct'] * 100)
                    in_pos = False
                elif row['high'] >= tp:
                    wins += 1
                    pnl_pct += (TRADING_CONFIG['max_risk_per_trade_pct'] * 100 * TRADING_CONFIG['risk_reward_ratio'])
                    in_pos = False
    
    total = wins + losses + be_shots
    win_rate = (wins / total * 100) if total > 0 else 0
    
    color = "green" if pnl_pct >= 100 else "red"
    console.print(f"-> {symbol} | Trades Executes: {total} | Win Rate: {win_rate:.1f}% | Performance Simulee: [{color}]{pnl_pct:.2f}%[/{color}]")

if __name__ == "__main__":
    console.print("[on magenta bold] -- V3 QUANTITATIVE LOCAL BACKTEST -- [/on magenta bold]")
    f = DataFetcher()
    for s in TRADING_CONFIG['symbols']:
        run_backtest(s, f)
