# Formative ML Pipeline: S&P 500 Time-Series

An end-to-end machine learning pipeline built around 5 years of daily S&P 500 stock
prices. The project takes raw market data all the way from exploratory analysis and
model training, through relational and non-relational storage, out to a REST API, and
finally into a forecast script that predicts the next closing price.

The formative aims to strengthen data preprocessing and database skills, including
working with relational (MySQL) and non-relational (MongoDB) databases, and wiring a
trained model into a serving pipeline.

## Dataset

- **Source:** [S&P 500 Stock Data](https://www.kaggle.com/datasets/camnugent/sandp500) (camnugent, Kaggle)
- **File used:** `all_stocks_5yr.csv` (the single merged file)
- **Columns:** `Date`, `Open`, `High`, `Low`, `Close`, `Volume`, `Name` (ticker)
- **Coverage:** about 5 years of daily prices through February 2018, 505 tickers, roughly 619,000 rows

The CSV is not committed (it is large and easy to re-download). Download it from Kaggle
and place it at `sp500_project/data/all_stocks_5yr.csv` before running the loaders.

## Pipeline at a Glance

```text
Kaggle CSV
    |
    v
[Task 1] EDA + Forecasting notebook  ->  trained model (.pkl)
    |
    v
[Task 2] MySQL schema + MongoDB collection  <-  scripts/load_data.py
    |
    v
[Task 3] Flask REST API (/api/sql/... and /api/mongo/...)
    |
    v
[Task 4] scripts/forecast.py  ->  fetch via API, predict next close
```

## Repository Layout

```text
Formative_ML_Pipeline/
├── README.md                       # this file (pipeline overview)
├── Formative_notebook.ipynb        # Task 1: EDA, analytical questions, model training
├── best_model_lr_lookback5.pkl     # exported Linear Regression model (lookback = 5)
└── sp500_project/                  # Tasks 2 to 4: databases, API, forecast script
    ├── README.md                   # detailed setup and API reference
    ├── Testing.md                  # ready-to-run curl commands for every endpoint
    ├── .env.example                # template for environment variables
    ├── app.py                      # Task 3: Flask REST API
    ├── sql/
    │   ├── schema.sql              # Task 2: MySQL schema (sectors, companies, daily_prices)
    │   └── example_queries.sql     # Task 2: 4 example SQL queries
    ├── mongo/
    │   └── example_queries.js      # Task 2: 4 example MongoDB queries
    ├── scripts/
    │   ├── load_data.py            # loads the CSV into both MySQL and MongoDB
    │   └── forecast.py             # Task 4: fetch from API, run the model, print a forecast
    └── tests/
        └── test_forecast_script.py # unit test for feature preparation
```

## The Four Tasks

### Task 1: Exploratory Analysis and Forecasting (`Formative_notebook.ipynb`)

Time-series preprocessing and EDA on a single ticker, followed by forecasting. The
notebook answers five analytical questions (price trend and moving averages, lag effects
in daily returns, volume versus price movement, evolving volatility, and the distribution
of daily returns), then trains and compares two model families:

- **Linear Regression** with lag features (experiments at lookback = 5 and 20 days)
- **LSTM** neural network (experiments at lookback = 30 and 60 days)

Missing values are handled with forward-fill to respect the trading-day calendar. The
best Linear Regression model is exported to `best_model_lr_lookback5.pkl`.

### Task 2: Database Design (`sp500_project/sql/` and `sp500_project/mongo/`)

The same data is modeled two ways:

- **MySQL:** three normalized tables, `sectors` -> `companies` -> `daily_prices`, with
  one row per company per trading day. See `sql/schema.sql`.
- **MongoDB (Atlas):** a single `prices` collection, one document per company per day,
  indexed on `(ticker, date)` for fast time-series queries.

Four example queries are provided for each store (latest record, date range, top companies
by average close, highest single-day volume).

### Task 3: REST API (`sp500_project/app.py`)

A Flask API that exposes both databases through identical endpoints. Every endpoint exists
twice, once under `/api/sql/...` (MySQL) and once under `/api/mongo/...` (MongoDB), with
the same shape and behavior.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/records` | Create a daily price record |
| GET | `/records` | List records (`?ticker=`, `?limit=`, `?offset=`) |
| GET | `/records/<id>` | Get one record by id |
| PUT | `/records/<id>` | Update a record |
| DELETE | `/records/<id>` | Delete a record |
| GET | `/records/latest?ticker=AAPL` | Most recent record for a ticker |
| GET | `/records/range?ticker=AAPL&start=...&end=...` | Records within a date range |

Note the date format difference: SQL endpoints take plain dates (`2017-01-01`), Mongo
endpoints expect ISO datetimes (`2017-01-01T00:00:00`). See `sp500_project/Testing.md` for
copy-paste curl commands covering every endpoint.

### Task 4: Forecast Script (`sp500_project/scripts/forecast.py`)

Pulls a ticker's price history from the running API (Mongo endpoints by default), builds
lag features, loads the trained model (or trains one if none is saved), and prints a
one-step forecast of the next closing price. Behavior is configurable through environment
variables: `API_BASE_URL`, `MODEL_PATH`, `FORECAST_TICKER`, `FORECAST_LOOKBACK`.

## Quick Start

Full step-by-step setup lives in [sp500_project/README.md](sp500_project/README.md). The
short version:

```bash
# 1. Install dependencies
pip3 install pandas pymysql pymongo flask python-dotenv sqlalchemy scikit-learn numpy requests

# 2. Configure credentials
cd sp500_project
cp .env.example .env        # then fill in MYSQL_PASSWORD and MONGO_URI

# 3. Create the MySQL schema
mysql -u root -p < sql/schema.sql

# 4. Load the CSV into both databases
python3 scripts/load_data.py

# 5. Start the API
python3 app.py              # serves http://127.0.0.1:5000

# 6. Run the forecast (in a second terminal, with the API running)
python3 scripts/forecast.py
```

## Requirements

- Python 3.10 or newer
- MySQL installed locally (for the SQL side)
- A MongoDB Atlas connection string, or a local MongoDB instance (for the Mongo side)
- Python packages: `flask`, `pymysql`, `pymongo`, `python-dotenv`, `pandas`, `sqlalchemy`,
  `scikit-learn`, `numpy`, `requests` (plus `tensorflow` and `kagglehub` for the notebook)

## Testing

```bash
cd sp500_project
python3 -m pytest tests/
```

Manual API testing commands are in [sp500_project/Testing.md](sp500_project/Testing.md).

## Notes

- The dataset CSV and the trained model are the two artifacts the pipeline depends on but
  does not regenerate on every run, so keep them in place once produced.
