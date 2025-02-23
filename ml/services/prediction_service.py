import glob
import logging
import os
from datetime import datetime

import joblib
import pandas as pd

logger = logging.getLogger(__name__)


class PredictionService:
    def __init__(self):
        self.model_path = os.getenv("MODEL_PATH", "/app/models")
        self.current_model = None
        self.load_latest_model()

    def load_latest_model(self):
        try:
            model_files = glob.glob(f"{self.model_path}/xgboost_*.model")
            if model_files:
                latest_model = max(model_files, key=os.path.getctime)
                self.current_model = joblib.load(latest_model)
                logger.info(f"Loaded model from {latest_model}")
            else:
                logger.warning("No model files found")
        except Exception as e:
            logger.error(f"Error loading model: {e}")

    async def get_prediction(self, symbol: str):
        try:
            if not self.current_model:
                return {"error": "No model loaded"}

            # TODO: Gerçek veriyi al
            features = self._get_current_features(symbol)

            prediction = self.current_model.predict(features)

            return {
                "symbol": symbol,
                "prediction": float(prediction[0]),
                "timestamp": str(datetime.now()),
            }

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {"error": str(e)}

    def _get_current_features(self, symbol):
        # TODO: Gerçek veriyi al
        return pd.DataFrame(
            [[50000, 51000, 49000, 100]], columns=["open", "high", "low", "volume"]
        )
