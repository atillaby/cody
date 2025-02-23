import logging

import uvicorn
from fastapi import BackgroundTasks, FastAPI
from ml.services.model_service import ModelService
from ml.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)
app = FastAPI(title="Trading Bot ML Service")

model_service = ModelService()
prediction_service = PredictionService()


@app.get("/")
async def root():
    return {"status": "ML service is running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/train/{model_type}")
async def train_model(model_type: str, background_tasks: BackgroundTasks):
    """Model eğitimini başlat"""
    try:
        background_tasks.add_task(model_service.train_model, model_type)
        return {"status": "training_started", "model_type": model_type}
    except Exception as e:
        logger.error(f"Training error: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/predict/{symbol}")
async def get_prediction(symbol: str):
    """Fiyat tahmini al"""
    try:
        prediction = await prediction_service.get_prediction(symbol)
        return prediction
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
