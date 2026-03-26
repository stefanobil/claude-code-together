import requests
from datetime import datetime, timezone
import pandas as pd

def check():
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    try:
        data = requests.get(url, timeout=5).json()
        now = datetime.now(timezone.utc)
        print(f"Heure UTC : {now}")
        
        active_news = []
        for event in data:
            if event.get('impact') == 'High' and event.get('country') == 'USD':
                dt = pd.to_datetime(event['date'], utc=True)
                diff_min = abs((now - dt).total_seconds()) / 60
                if diff_min <= 60:
                    active_news.append(event['title'])
        
        if active_news:
            print(f"ALERTE ACTIVE : {', '.join(active_news)}")
        else:
            print("Aucune news majeure en ce moment.")
            
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    check()
