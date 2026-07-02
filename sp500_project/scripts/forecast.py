import os
import pickle
from datetime import datetime

import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")
MODEL_PATH = os.getenv("MODEL_PATH", os.path.join(os.path.dirname(__file__), "..", "models", "linear_regression_model.pkl"))
TICKER = os.getenv("FORECAST_TICKER", "AAPL")
LOOKBACK = int(os.getenv("FORECAST_LOOKBACK", "5"))


def fetch_series(ticker: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    params = {"ticker": ticker, "limit": 1000}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    response = requests.get(f"{API_BASE_URL}/api/mongo/records", params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    if not data:
        raise ValueError(f"No data returned for ticker {ticker}")

    df = pd.DataFrame(data)
    if "date" not in df.columns:
        raise ValueError("Expected a 'date' column from the API")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def prepare_features(series: pd.Series, lookback: int) -> tuple[np.ndarray, np.ndarray]:
    if len(series) <= lookback:
        raise ValueError("Not enough data to create lag features")

    rows = []
    targets = []
    for i in range(lookback, len(series)):
        rows.append(series.iloc[i-lookback:i].to_numpy())
        targets.append(series.iloc[i])
    return np.array(rows, dtype=float), np.array(targets, dtype=float)


def train_model(series: pd.Series, lookback: int):
    X, y = prepare_features(series, lookback)
    model = LinearRegression()
    model.fit(X, y)
    return model


def save_model(model, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        pickle.dump(model, fh)


def load_model(path: str):
    with open(path, "rb") as fh:
        return pickle.load(fh)


def make_forecast(model, history: pd.Series, lookback: int, horizon: int = 1):
    recent = history.iloc[-lookback:].to_numpy(dtype=float)
    features = recent.reshape(1, -1)
    prediction = model.predict(features)[0]
    return float(prediction)


def main() -> dict:
    df = fetch_series(TICKER)
    close = df["close"].astype(float).ffill().bfill()

    if os.path.exists(MODEL_PATH):
        model = load_model(MODEL_PATH)
    else:
        model = train_model(close, LOOKBACK)
        save_model(model, MODEL_PATH)

    forecast_value = make_forecast(model, close, LOOKBACK)
    return {
        "ticker": TICKER,
        "lookback": LOOKBACK,
        "last_date": df["date"].iloc[-1].date().isoformat(),
        "forecast_close": round(forecast_value, 4),
        "model_path": MODEL_PATH,
    }


if __name__ == "__main__":
    result = main()
    print(result)
