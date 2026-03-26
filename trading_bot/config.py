# config.py
# Fichier de configuration avancé V2.0 (Institutionnel / Smart Money)

EXCHANGE_CONFIG = {
    'exchange_id': 'binance',
    'api_key': 'TON_API_KEY_ICI',
    'secret': 'TON_SECRET_ICI',
    'enableRateLimit': True,
    'options': {'defaultType': 'future'} 
}

TELEGRAM_CONFIG = {
    'bot_token': '8690194673:AAHXahzxC7lead7OxT2VOatazx5XL02uNpQ',
    'chat_id': '985942050',
}

TRADING_CONFIG = {
    # Portefeuille SMC
    'symbols': [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'HYPE/USDT', 
        'UNI/USDT', 'TRX/USDT', 'AAVE/USDT', 
        'SKY/USDT', 'ENA/USDT', 'LDO/USDT', 'VIRTUAL/USDT'
    ],
    
    # V2.0 Multi-Timeframe (MTF)
    'timeframe': '1h',          # Unité d'entrée chirurgicale
    'macro_timeframe': '4h',    # Tendance MACRO (Bouclier directionnel automatique)
    
    'paper_trading': True,      
    
    # Futures & Margin
    'leverage': 5,
    'margin_type': 'ISOLATED',
    
    # Gestion du risque (Blindée)
    'max_risk_per_trade_pct': 0.01, 
    'risk_reward_ratio': 2.5,

    # V3.0 : Sécurisation Automatique
    'break_even_at_r': 1.0,         # Au bout de +1R (Rapport risque validé x1), le SL est remonté au prix d'entrée neutre.
    'trailing_activation_r': 1.5,   # Dès +1.5R, le bot traque mathématiquement le meilleur prix et remonte son SL en continu.
    'trailing_distance_pct': 0.015, # Stop suiveur à 1.5% de distance du plus haut sommet local.
    
    # V3.1 : Bouclier Anti-Distribution
    'consecutive_loss_limit': 3,    # Si 3 SL d'affilée sur une même paire, on arrête les frais.
    'freeze_duration_hours': 6,     # Durée de la mise en quarantaine de l'actif (en heures).
    
    # V4.2 : Mode Hedge Institutionnel
    'hedge_mode_enabled': True,     # Permet d'ouvrir une protection inverse plutôt que de sortir.
    'adx_min_strength': 20,         # AUCUN trade (standard ou hedge) ne s'ouvre si ADX < 20 (Marché sans tendance).
    'hedge_risk_percent': 0.5,      # La position de couverture risque seulement 0.5% (Moitié de la principale).
    
    # V6.0 : Corrélation & Momentum
    'use_btc_correlation': True,    # Bloque les alts si le BTC est contre-tendance.
    'reentry_allowed': True,        # Autorise une 2ème tentative si la structure reste intacte.
    'reentry_max_attempts': 1,      # Maximum une seule ré-entrée par setup.
    'delta_anomaly_threshold': 2.0, # Seuil d'anomalie de volume acheteur/vendeur (2x la moyenne).
    
    # V2.0 Filtres Institutionnels Anti-Squeeze
    'use_oi_filter': True,          # Bloque les Longs si la foule est déjà 100% Long (Squeeze warning)
    'use_volume_profile': True,     # Validation par le Point of Control des Order Blocks
    
    # Conformité IA (Filtre Haute Précision)
    'use_ml_confirmation': True,
    'ml_min_probability': 0.70,     # L'IA doit être sûre à 70% pour déclencher le trade
}
