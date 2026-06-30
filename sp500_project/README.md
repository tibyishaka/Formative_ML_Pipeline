## Task 2 and 3 Project Structure

```
sp500_project/
├── README.md                  # this file
├── .env.example                # template for environment variables (copy to .env)
├── .gitignore
├── app.py                      # Task 3: Flask REST API (CRUD + time-series endpoints)
├── TESTING.md                  # curl commands to manually test every API endpoint
├── data/
│   └── all_stocks_5yr.csv      # dataset (download separately)
├── sql/
│   ├── schema.sql               # Task 2: MySQL schema (3 tables) — creates sp500_db
│   └── example_queries.sql      # Task 2: 4 example SQL queries
├── mongo/
│   └── example_queries.js       # Task 2: 4 example MongoDB queries
├── scripts/
│   └── load_data.py             # loads the CSV into both MySQL and MongoDB
└── notebooks/                   # Task 1: EDA, analytical questions, model training (Thierry)
```

## Dataset

**Source:** https://www.kaggle.com/datasets/camnugent/sandp500
**File used:** `all_stocks_5yr.csv` (the merged file, not the per-ticker folder)
**Columns:** `Date`, `Open`, `High`, `Low`, `Close`, `Volume`, `Name` (ticker symbol)
**Coverage:** ~5 years of daily prices, 505 tickers, ~619,000 rows total

The CSV is not committed to this repo (large, and easy to re-download). Each team member must download it from Kaggle and place it at `data/all_stocks_5yr.csv` before running anything.

## Architecture Overview

- **MySQL** — relational schema with 3 tables: `sectors` → `companies` → `daily_prices` (one row per company per trading day). See `sql/schema.sql` for full DDL and the ERD in the report.
- **MongoDB (Atlas)** — single `prices` collection, one document per company per day, mirroring the same data. Hosted on a shared Atlas cluster so the whole team can connect without anyone running a local Mongo server.
- **Flask API (`app.py`)** — exposes both databases through identical REST endpoints under `/api/sql/...` and `/api/mongo/...`.

## Prerequisites

- Python 3.10+ (`python3 --version`)
- MySQL installed locally (`mysql --version`) — see setup steps below
- A MongoDB Atlas account with access to the shared cluster (ask the team for the connection string) — OR your own local/Atlas MongoDB if testing independently
- pip packages: `flask`, `pymysql`, `pymongo`, `python-dotenv`, `pandas`, `sqlalchemy`

Install everything with:
```bash
pip3 install pandas pymysql pymongo flask python-dotenv sqlalchemy
```

> **Mac note:** if `python`/`pip` aren't recognized, use `python3`/`pip3` instead — this is normal with the python.org installer on macOS. If MongoDB connections fail with an SSL/certificate error, run:
> `open "/Applications/Python 3.x/Install Certificates.command"` (match your installed version folder).

## Setup — Step by Step

### 1. Clone the repo and enter the project folder
```bash
git clone <repo-url>
cd <repo-name>/sp500_project
```

### 2. Download the dataset
Download `all_stocks_5yr.csv` from Kaggle (link above) and place it at:
```
sp500_project/data/all_stocks_5yr.csv
```

### 3. Set up environment variables
```bash
cp .env.example .env
```
Then open `.env` and fill in:
- `MYSQL_PASSWORD` — your local MySQL root password
- `MONGO_URI` — the shared Atlas connection string (ask a teammate, or use your own Atlas cluster for solo testing)

**Never commit `.env`** — it's already in `.gitignore`. Only `.env.example` (no real secrets) is tracked.

### 4. Set up MySQL
```bash
mysql -u root -p < sql/schema.sql
```
This creates the `sp500_db` database and all 3 tables. Safe to re-run — it drops and recreates the tables each time.

### 5. Load the data into both databases
```bash
python3 scripts/load_data.py
```
This reads the CSV and inserts it into MySQL (~619K rows) and MongoDB (~619K documents). Takes a few minutes. It's safe to re-run for MySQL (uses `INSERT IGNORE`); MongoDB inserts are cleared and reloaded fresh each run.

### 6. Start the API
```bash
python3 app.py
```
The API is now live at `http://127.0.0.1:5000`. Visiting that URL in a browser (or `curl http://127.0.0.1:5000`) shows a JSON list of all available endpoints.

### 7. Test the endpoints
See `TESTING.md` for ready-to-use curl commands covering every CRUD and time-series endpoint, for both databases.

## API Reference

All endpoints exist twice — once under `/api/sql/...` (MySQL) and once under `/api/mongo/...` (MongoDB) — with identical behavior and shape.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/records` | Create a new daily price record |
| GET | `/records` | List records (optional `?ticker=` filter, `?limit=`, `?offset=`) |
| GET | `/records/<id>` | Get a single record by id |
| PUT | `/records/<id>` | Update a record |
| DELETE | `/records/<id>` | Delete a record |
| GET | `/records/latest?ticker=AAPL` | Most recent record for a ticker |
| GET | `/records/range?ticker=AAPL&start=2017-01-01&end=2017-03-01` | Records within a date range |

Example:
```bash
curl "http://127.0.0.1:5000/api/sql/records/latest?ticker=AAPL"
curl "http://127.0.0.1:5000/api/mongo/records/range?ticker=AAPL&start=2017-01-01T00:00:00&end=2017-03-01T00:00:00"
```

Note the date format difference: MySQL endpoints take plain dates (`2017-01-01`), MongoDB endpoints expect ISO datetimes (`2017-01-01T00:00:00`).

## Notes for Task 4 (Forecast Script) Favor's Task

- The API must be running (`python3 app.py`) for the forecast script's "fetch from API" step to work. Run it locally on your own machine — no need to deploy anywhere.
- Easiest path: use the **MongoDB endpoints** (`/api/mongo/...`) since they connect to the shared Atlas cluster — no local database setup needed, just fill in the shared `MONGO_URI` in your own `.env`.
- If you want to test the SQL endpoints too, you'll need your own local MySQL with `schema.sql` run and `load_data.py` executed against it (steps 4–5 above).
- Suggested fetch call for a forecast script:
  ```python
  import requests
  resp = requests.get("http://127.0.0.1:5000/api/mongo/records/range",
                       params={"ticker": "AAPL", "start": "2017-01-01T00:00:00", "end": "2018-02-01T00:00:00"})
  data = resp.json()
  ```
- Preprocessing should mirror whatever pipeline was used in Task 1 (same scaling, lag features, moving averages, etc.) so the trained model receives data in the same shape it was trained on.

## Database Design Summary (Task 2)

**MySQL — 3 tables:**
- `sectors(id, sector_name)` — lookup table
- `companies(id, ticker, sector_id → sectors.id)` — one row per stock
- `daily_prices(id, company_id → companies.id, price_date, open_price, high_price, low_price, close_price, volume)` — the time-series table

**MongoDB — 1 collection (`prices`):**
One document per company per trading day:
```json
{
  "_id": "ObjectId(...)",
  "ticker": "AAPL",
  "date": "2017-01-03T00:00:00Z",
  "open": 115.8,
  "high": 116.33,
  "low": 114.76,
  "close": 116.15,
  "volume": 28781865
}
```

ERD diagram and full query results with screenshots are included in the team report.