import os
import csv
import json
import logging
from datetime import datetime

# Configuration des Chemins
LOG_DIR = "logs"
TRADE_LOG_FILE = os.path.join(LOG_DIR, "trade_history.csv")
SYSTEM_LOG_FILE = os.path.join(LOG_DIR, "system_audit.log")
PERFORMANCE_FILE = os.path.join(LOG_DIR, "performance_metrics.json")

# Assurer l'existence du dossier de logs
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configuration du logger système (Audit)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | [%(name)s] : %(message)s',
    handlers=[
        logging.FileHandler(SYSTEM_LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AUDITOR")

def log_trade(symbol, side, type_trade, entry_price, exit_price, pnl_usd, pnl_pct, duration, reason):
    """Enregistre un trade dans le fichier CSV d'audit."""
    file_exists = os.path.isfile(TRADE_LOG_FILE)
    
    with open(TRADE_LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Symbol', 'Side', 'Type', 'Entry', 'Exit', 'PnL_USD', 'PnL_Pct', 'Duration_Sec', 'Reason'])
        
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol, side, type_trade, entry_price, exit_price, 
            round(pnl_usd, 2), round(pnl_pct, 2), duration, reason
        ])
    
    # Mise à jour des métriques de performance
    if type_trade == "EXIT":
        update_performance_metrics(pnl_usd, pnl_pct > 0)

def log_error(module, message, critical=False):
    """Enregistre une erreur système pour l'audit technique."""
    level = logging.CRITICAL if critical else logging.ERROR
    logger.log(level, f"[{module}] {message}")

def update_performance_metrics(pnl_usd, is_win):
    """Met à jour le fichier JSON de performance en temps réel."""
    data = {"total_trades": 0, "wins": 0, "losses": 0, "total_pnl_usd": 0.0, "win_rate": 0.0}
    
    if os.path.exists(PERFORMANCE_FILE):
        with open(PERFORMANCE_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                pass
                
    data["total_trades"] += 1
    if is_win:
        data["wins"] += 1
    else:
        data["losses"] += 1
        
    data["total_pnl_usd"] += pnl_usd
    data["win_rate"] = (data["wins"] / data["total_trades"]) * 100
    
    with open(PERFORMANCE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_performance_summary():
    """Récupère les statistiques pour le dashboard."""
    if os.path.exists(PERFORMANCE_FILE):
        with open(PERFORMANCE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"total_trades": 0, "win_rate": 0.0, "total_pnl_usd": 0.0}
