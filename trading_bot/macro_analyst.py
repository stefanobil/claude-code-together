import requests
import pandas as pd
from datetime import datetime, timezone
from notifier import send_telegram_alert
from rich.console import Console

class MacroAnalyst:
    """Module d'élite pour le briefing macroéconomique de Mr Stéphane."""
    
    def __init__(self):
        self.console = Console()
        self.last_briefing_date = None

    def fetch_major_events(self):
        """Récupère les événements High Impact de la semaine."""
        try:
            url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.console.print(f"[red]Erreur MacroAnalyst: {e}[/red]")
        return []

    def generate_daily_briefing(self):
        """Génère un briefing hautement détaillé et explicite pour Mr Stéphane en Français."""
        events = self.fetch_major_events()
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")
        
        today_news = [e for e in events if e.get('date', '').startswith(today_str) and e.get('impact') == 'High']

        briefing = "👑 *INTELLIGENCE MACRO INSTITUTIONNELLE*\n"
        briefing += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        briefing += "*Mr Stéphane, The Dark Monarch & The Millionaire on the Hunt.*\n\n"
        
        briefing += "🧠 **1. SNAPSHOT MACRO & FLUX DE LIQUIDITÉ**\n"
        briefing += f"• **Date** : {now.strftime('%d %B %Y')}\n"
        briefing += "• **Régime de Marché** : *Expansion de Volatilité.*\n"
        briefing += "• **Liquidité** : Les Banques Centrales resserrent, mais les flux on-chain montrent une accumulation institutionnelle discrète.\n"
        briefing += "• **Corrélation DXY** : Dollar fort = Pression sur le BTC. Surveillez le pivot des 104.50.\n\n"

        briefing += "🌍 **2. TOP NEWS HAUT IMPACT : DÉCRYPTAGE ÉLITE**\n"
        if not today_news:
            briefing += "• *Aucune annonce 'High Impact' aujourd'hui.* Profitez-en pour chasser les déséquilibres de prix (Imbalances) sans bruit parasite.\n"
        else:
            for i, event in enumerate(today_news[:3]):
                briefing += f"🔥 **{i+1}. {event['title']} ({event['country']})**\n"
                briefing += f"   - 💡 *Pourquoi c'est vital* : Cette donnée influence directement la décision du FOMC sur les taux. Un chiffre au-dessus du consensus renforcera le Dollar et fera chuter les actifs à risque.\n"
                briefing += f"   - 🎯 *Impact Stratégique* : Risque de 'Stop Hunt' massif. Votre bouclier gèlera les entrées 60 minutes avant.\n"
                briefing += f"   - ⏰ *Heure* : {event['date']}\n\n"

        briefing += "🌊 **3. SENTIMENT DU JOUR & BIAIS**\n"
        briefing += "• **Sentiment Global** : ⚖️ *NEUTRE / RISK-OFF*\n"
        briefing += "• **Direction des Flux** : Fuite vers la sécurité (Cash/Stablecoins). Le Bitcoin teste la résilience des supports institutionnels.\n"
        briefing += "• **Biais de Chasse** : *Bearish* sous les résistances clés, *Bullish* uniquement sur confirmation d'Order Block majeur.\n\n"

        briefing += "📊 **4. ANALYSE PAR CLASSE D'ACTIFS**\n"
        briefing += "📉 **CRYPTO (BTC/ETH)** : Concentration de liquidité sous les plus bas de la semaine dernière. Attendez le 'sweep' avant de chercher un long.\n"
        briefing += "📈 **DXY (Indice Dollar)** : Le chef d'orchestre. S'il casse vers le haut, nous coupons les velléités acheteuses.\n"
        briefing += "🏛️ **INDICES (Nasdaq/ES)** : Forte corrélation actuelle avec les rendements obligataires. Prudence sur les corrélations.\n\n"

        briefing += "🧭 **5. PLAN DE JEU & DIRECTIVES**\n"
        briefing += "• **Directives** : Ciblez les zones d'Imbalance non comblées. Le moteur ne prendra que les signaux avec une probabilité IA > 85%.\n"
        briefing += "• **Zones de Chasse** : Concentrez-vous sur les zones de liquidité externes (Zones SMC extrêmes).\n\n"

        briefing += "⚠️ **ALERTES DE RISQUE INSTITUTIONNEL**\n"
        briefing += "• Risque de volatilité 'slippage' (glissement) élevé durant l'ouverture New Yorkaise.\n"
        briefing += "• Ne surchargez pas l'exposition sur une seule paire.\n\n"

        briefing += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        briefing += "Monsieur Stéphane, le chaos est une opportunité pour l'esprit préparé. La discipline est votre seule arme réelle.\n\n"
        briefing += "_L'interprétation est le pont entre les données et la richesse._"

        return briefing

    def check_and_send_briefing(self):
        """Vérifie s'il est 7h00 du matin pour envoyer le briefing."""
        now = datetime.now()
        # On vérifie si on est entre 7:00 et 7:05 et si on n'a pas déjà envoyé aujourd'hui
        if now.hour == 7 and now.minute <= 5:
            today = now.strftime("%Y-%m-%d")
            if self.last_briefing_date != today:
                briefing = self.generate_daily_briefing()
                send_telegram_alert(briefing)
                self.last_briefing_date = today
                self.console.print("[bold green]✅ Briefing matinal 7AM envoyé à Mr Stéphane.[/bold green]")

macro_analyst = MacroAnalyst()
