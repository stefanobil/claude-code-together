import pandas as pd
import numpy as np
import ta

def compute_smc(df: pd.DataFrame) -> pd.DataFrame:
    """SMC V2.0 + V4.2: FVG, Order Blocks institutionnels et Structural Flips."""
    
    # Validation "Baleines" par le Volume
    avg_volume = df['volume'].rolling(window=10).mean().shift(1)
    huge_institutional_volume = df['volume'] > (avg_volume * 1.3)
    
    # OB Haussier
    impulse_up = df['close'] > df['high'].shift(1)
    red_candle_t1 = df['close'].shift(1) < df['open'].shift(1)
    df['ob_bullish'] = impulse_up & red_candle_t1 & huge_institutional_volume
    df['ob_bullish_level'] = np.where(df['ob_bullish'], df['low'].shift(1), np.nan)
    
    # OB Baissier
    impulse_down = df['close'] < df['low'].shift(1)
    green_candle_t1 = df['close'].shift(1) > df['open'].shift(1)
    df['ob_bearish'] = impulse_down & green_candle_t1 & huge_institutional_volume
    df['ob_bearish_level'] = np.where(df['ob_bearish'], df['high'].shift(1), np.nan)
    
    # NOUVEAU V4.2 : ADX (Force de tendance)
    adx_ind = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
    df['adx'] = adx_ind.adx()
    
    # Détection simplifiée de Structural Flip (CHoCH)
    # Si le prix casse le plus haut/bas des 10 dernières bougies
    df['structure_flip_up'] = (df['close'] > df['high'].rolling(10).max().shift(1))
    df['structure_flip_down'] = (df['close'] < df['low'].rolling(10).min().shift(1))
    
    # NOUVEAU V5.0 : Zones de Liquidité (Swing High / Swing Low)
    df['swing_high'] = df['high'].rolling(30).max()
    df['swing_low'] = df['low'].rolling(30).min()
    
    # Fair Value Gaps (FVG) avec niveaux précis pour l'entrée
    df['fvg_bullish'] = df['low'] > df['high'].shift(2)
    df['fvg_bearish'] = df['high'] < df['low'].shift(2)
    df['fvg_gap_level'] = np.where(df['fvg_bullish'], df['high'].shift(2), np.where(df['fvg_bearish'], df['low'].shift(2), np.nan))
    
    return df

def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Moteur de calcul complet."""
    df_ta = df.copy()
    try:
        df_ta['sma_200'] = ta.trend.sma_indicator(df_ta['close'], window=200)
        df_ta['rsi'] = ta.momentum.rsi(df_ta['close'], window=14)
        df_ta['macd'] = ta.trend.macd(df_ta['close'])
        df_ta['macd_signal'] = ta.trend.macd_signal(df_ta['close'])
        df_ta['atr'] = ta.volatility.average_true_range(df_ta['high'], df_ta['low'], df_ta['close'], window=14)
        
        df_ta = compute_smc(df_ta)
        
        df_ta['last_ob_bullish_level'] = df_ta['ob_bullish_level'].ffill()
        df_ta['last_ob_bearish_level'] = df_ta['ob_bearish_level'].ffill()
        
        return df_ta.dropna(subset=['sma_200', 'macd', 'atr', 'rsi'])
    except Exception as e:
        print(f"Erreur indicateurs V4.2 : {e}")
        return df
