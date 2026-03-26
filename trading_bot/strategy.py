import pandas as pd
from config import TRADING_CONFIG

def check_market_structure_trend(df: pd.DataFrame) -> str:
    """V5.0: Identifie la tendance par l'Action des Prix (HH/HL)."""
    if len(df) < 50: return 'NEUTRAL'
    
    last_5 = df.tail(5)
    prev_5 = df.iloc[-10:-5]
    
    # Tendance Haussière : Les plus hauts montent, les plus bas montent
    is_hh = last_5['high'].max() > prev_5['high'].max()
    is_hl = last_5['low'].min() > prev_5['low'].min()
    
    # Tendance Baissière : Les plus hauts baissent, les plus bas baissent
    is_lh = last_5['high'].max() < prev_5['high'].max()
    is_ll = last_5['low'].min() < prev_5['low'].min()
    
    if is_hh and is_hl: return 'BULLISH'
    if is_lh and is_ll: return 'BEARISH'
    return 'NEUTRAL'

def check_buy_signal(df_1h: pd.DataFrame, df_macro: pd.DataFrame, derivatives: dict, btc_trend: str = 'NEUTRAL') -> dict:
    """V6.0 Sniper Entry: Structure + BTC Filter + Delta Momentum."""
    last_row = df_1h.iloc[-1]
    
    # 1. Filtre de Corrélation BTC V6.0
    if TRADING_CONFIG.get('use_btc_correlation') and btc_trend == 'BEARISH':
        return {'signal': False, 'ob_level': 0.0, 'tp_target': 0.0, 'reason': 'BTC BEARISH'}

    # 2. Identification Trend V5.0 (Structure)
    trend = check_market_structure_trend(df_1h)
    macro_trend = check_market_structure_trend(df_macro)
    if trend != 'BULLISH' and macro_trend != 'BULLISH':
        return {'signal': False, 'ob_level': 0.0, 'tp_target': 0.0, 'reason': 'TREND NEUTRAL'}
    
    # 3. Delta Momentum V6.0 (Anomalie de Volume Acheteur)
    volume_delta = derivatives.get('volume_delta', 0.0)
    # On cherche une pression acheteuse (delta > 0)
    if volume_delta < 0.05: # Seuil minimum de pression
         return {'signal': False, 'ob_level': 0.0, 'tp_target': 0.0, 'reason': 'LOW DELTA'}
    
    fvg_level = last_row.get('fvg_gap_level', pd.NA)
    ob_level = last_row.get('last_ob_bullish_level', pd.NA)
    
    entry_zone = fvg_level if not pd.isna(fvg_level) else ob_level
    if pd.isna(entry_zone): return {'signal': False, 'ob_level': 0.0, 'tp_target': 0.0, 'reason': 'NO ZONE'}
    
    is_in_zone = (last_row['low'] <= entry_zone * 1.003) and (last_row['close'] > entry_zone * 0.997)
    tp_target = last_row.get('swing_high', last_row['close'] * 1.05)
    
    signal = is_in_zone and (tp_target > last_row['close'])
    
    return {
        'signal': bool(signal),
        'ob_level': float(entry_zone) if signal else 0.0,
        'tp_target': float(tp_target),
        'macro_trend': macro_trend,
        'delta': volume_delta,
        'fvg_detected': "OUI" if not pd.isna(fvg_level) else "NON (OB uniquement)",
        'liquidity_zone': "Buy-side Liquidity (Swing High)"
    }

def check_sell_signal(df_1h: pd.DataFrame, df_macro: pd.DataFrame, derivatives: dict, btc_trend: str = 'NEUTRAL') -> dict:
    """V6.0 Sniper Entry SHORT: Structure + BTC Filter + Delta Momentum."""
    last_row = df_1h.iloc[-1]
    
    if TRADING_CONFIG.get('use_btc_correlation') and btc_trend == 'BULLISH':
        return {'signal': False, 'ob_level': 0.0, 'tp_target': 0.0, 'reason': 'BTC BULLISH'}

    trend = check_market_structure_trend(df_1h)
    macro_trend = check_market_structure_trend(df_macro)
    if trend != 'BEARISH' and macro_trend != 'BEARISH':
        return {'signal': False, 'ob_level': 0.0, 'tp_target': 0.0, 'reason': 'TREND NEUTRAL'}
        
    volume_delta = derivatives.get('volume_delta', 0.0)
    if volume_delta > -0.05: # Pression vendeuse requise (delta négatif)
         return {'signal': False, 'ob_level': 0.0, 'tp_target': 0.0, 'reason': 'LOW DELTA'}

    fvg_level = last_row.get('fvg_gap_level', pd.NA)
    ob_level = last_row.get('last_ob_bearish_level', pd.NA)
    
    entry_zone = fvg_level if not pd.isna(fvg_level) else ob_level
    if pd.isna(entry_zone): return {'signal': False, 'ob_level': 0.0, 'tp_target': 0.0, 'reason': 'NO ZONE'}
    
    is_in_zone = (last_row['high'] >= entry_zone * 0.997) and (last_row['close'] < entry_zone * 1.003)
    tp_target = last_row.get('swing_low', last_row['close'] * 0.95)
    
    signal = is_in_zone and (tp_target < last_row['close'])
    
    return {
        'signal': bool(signal),
        'ob_level': float(entry_zone) if signal else 0.0,
        'tp_target': float(tp_target),
        'macro_trend': macro_trend,
        'delta': volume_delta,
        'fvg_detected': "OUI" if not pd.isna(fvg_level) else "NON (OB uniquement)",
        'liquidity_zone': "Sell-side Liquidity (Swing Low)"
    }
