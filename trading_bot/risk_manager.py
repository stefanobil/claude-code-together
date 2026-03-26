from config import TRADING_CONFIG

def calculate_smc_sl_tp(side: str, entry_price: float, ob_level: float, atr: float, tp_target: float = 0.0) -> tuple:
    """V5.0 : Stop-Loss Price Action et Take-Profit sur Zone de Liquidite Swing."""
    
    if side == 'LONG':
        # SL place SOUS l'Order Block ou l'Imbalance
        stop_loss = ob_level - (atr * 0.5)
        if stop_loss >= entry_price:
            stop_loss = entry_price - (atr * 0.5)
            
        # TP V5.0 : Cible la liquidite du Swing High si fournie
        if tp_target > entry_price:
            take_profit = tp_target
        else:
            distance_to_sl = abs(entry_price - stop_loss)
            take_profit = entry_price + (distance_to_sl * TRADING_CONFIG['risk_reward_ratio'])
            
    else: # SHORT
        # SL place AU DESSUS de la zone d'invalidation
        stop_loss = ob_level + (atr * 0.5)
        if stop_loss <= entry_price:
            stop_loss = entry_price + (atr * 0.5)
            
        # TP V5.0 : Cible la liquidite du Swing Low
        if tp_target > 0 and tp_target < entry_price:
            take_profit = tp_target
        else:
            distance_to_sl = abs(stop_loss - entry_price)
            take_profit = entry_price - (distance_to_sl * TRADING_CONFIG['risk_reward_ratio'])
        
    return stop_loss, take_profit

def calculate_futures_position_size(total_capital: float, entry_price: float, stop_loss_price: float) -> float:
    risk_dollars = total_capital * TRADING_CONFIG['max_risk_per_trade_pct']
    risk_per_token_usd = abs(entry_price - stop_loss_price)
    if risk_per_token_usd == 0: return 0.0
    return risk_dollars / risk_per_token_usd
