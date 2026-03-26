import requests
from config import TELEGRAM_CONFIG
from rich.console import Console

def send_telegram_alert(message: str):
    """Envoie une alerte propre sur l'application Telegram du trader."""
    token = TELEGRAM_CONFIG['bot_token']
    chat_id = TELEGRAM_CONFIG['chat_id']
    
    try:
        Console().print(f"\n[bold yellow]====================== ALERTE TELEGRAM ======================[/bold yellow]")
        Console().print(message)
    except:
        pass # Sécurité vitale contre les crashs d'affichage Windows liés aux Emojis
        
    # On bloque l'envoi web si les clés sont factices (pour éviter les crashs)
    if token == 'TON_TOKEN_TELEGRAM_ICI' or not token:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        Console().print(f"[red]⚠️ Impossible d'envoyer l'alerte Telegram : {e}[/red]")
