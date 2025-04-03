# 📁 timeseries_api.py

from fastapi import FastAPI, Request
from pydantic import BaseModel
from prophet import Prophet
import pandas as pd
import uuid
import os

app = FastAPI()

DATA_DIR = "/data"
os.makedirs(DATA_DIR, exist_ok=True)

class TimeSeriesInput(BaseModel):
    dates: list[str]
    values: list[float]

@app.post("/predict")
async def predict(data: TimeSeriesInput):
    df = pd.DataFrame({
        "ds": pd.to_datetime(data.dates),
        "y": data.values
    })
    
    model = Prophet()
    model.fit(df)
    
    future = model.make_future_dataframe(periods=7)
    forecast = model.predict(future)

    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(7).to_dict(orient="records")

@app.get("/health")
def health():
    return {"status": "ok"}
