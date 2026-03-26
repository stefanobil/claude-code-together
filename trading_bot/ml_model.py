import pandas as pd
from sklearn.ensemble import RandomForestClassifier

class MLPredictor:
    """Modèle V3.0: Prédiction d'espérance de Profit Quantitative."""
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=6)
        self.is_trained = False
        self.features = ['rsi', 'macd', 'close', 'sma_200', 'atr']
        
    def prepare_data(self, df: pd.DataFrame):
        data = df.copy()
        
        # V3.0 Target: L'Action des Prix touche-t-elle +2.0% dans les 24 prochaines heures ?
        # C'est un objectif institutionnel (Swing Trading) qui ignore le 'bruit' de la bougie immédiate.
        future_close = data['close'].shift(-24)
        data['target'] = (future_close > (data['close'] * 1.02)).astype(int)
        
        # Retrait des 24 dernières lignes (on ne connait pas encore leur futur pour s'entraîner)
        data = data.dropna(subset=self.features + ['target'])
        
        X = data[self.features]
        y = data['target']
        return X, y

    def train(self, df: pd.DataFrame):
        X, y = self.prepare_data(df)
        if len(X) < 100:
            return
            
        self.model.fit(X, y)
        self.is_trained = True
        
    def predict_next_candle(self, current_features: pd.DataFrame) -> dict:
        if not self.is_trained:
            return {"prediction": 0, "probability": 0.0}
            
        latest_data = current_features[self.features].tail(1)
        prob = self.model.predict_proba(latest_data)[0]
        
        return {
            "prediction": int(self.model.predict(latest_data)[0]),
            "probability": prob[1] # Probabilité mathématique de toucher +2% d'ici 24h.
        }
