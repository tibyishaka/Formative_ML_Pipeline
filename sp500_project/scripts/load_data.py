import os
import pandas as pd
import pymysql
from pymongo import MongoClient
from dotenv import load_dotenv

# ── Load credentials from .env ───────────────────────────────────────────────
load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "all_stocks_5yr.csv")


def load_csv():
    print(f"Reading {CSV_PATH} ...")
    df = pd.read_csv(CSV_PATH)
    # Standardize column names (the CSV's columns are: date, open, high, low, close, volume, Name)
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.rename(columns={"name": "ticker"})
    df["date"] = pd.to_datetime(df["date"])
    # Drop rows with missing essential values
    before = len(df)
    df = df.dropna(subset=["open", "high", "low", "close", "volume"])
    print(f"Loaded {len(df)} rows (dropped {before - len(df)} rows with missing values)")
    return df


def load_into_mysql(df):
    print("\n--- Loading into MySQL ---")
    conn = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        autocommit=False,
    )
    cursor = conn.cursor()

    # Insert unique tickers into companies table
    tickers = df["ticker"].unique()
    print(f"Inserting {len(tickers)} companies...")
    for ticker in tickers:
        cursor.execute(
            "INSERT IGNORE INTO companies (ticker, sector_id) VALUES (%s, 1)",
            (ticker,)
        )
    conn.commit()

    # Build a ticker -> company_id lookup
    cursor.execute("SELECT id, ticker FROM companies")
    ticker_to_id = {row[1]: row[0] for row in cursor.fetchall()}

    # Insert daily prices in batches
    print("Inserting daily price records (this may take a few minutes)...")
    insert_sql = """
        INSERT IGNORE INTO daily_prices
        (company_id, price_date, open_price, high_price, low_price, close_price, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    batch = []
    batch_size = 5000
    total_inserted = 0

    for _, row in df.iterrows():
        company_id = ticker_to_id.get(row["ticker"])
        if company_id is None:
            continue
        batch.append((
            company_id,
            row["date"].strftime("%Y-%m-%d"),
            float(row["open"]),
            float(row["high"]),
            float(row["low"]),
            float(row["close"]),
            int(row["volume"]),
        ))
        if len(batch) >= batch_size:
            cursor.executemany(insert_sql, batch)
            conn.commit()
            total_inserted += len(batch)
            print(f"  ...{total_inserted} rows inserted")
            batch = []

    if batch:
        cursor.executemany(insert_sql, batch)
        conn.commit()
        total_inserted += len(batch)

    print(f"MySQL load complete. Total rows inserted: {total_inserted}")
    cursor.close()
    conn.close()


def load_into_mongo(df):
    print("\n--- Loading into MongoDB ---")
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    collection = db["prices"]

    # Clear existing data for a clean re-run
    collection.delete_many({})

    records = df.rename(columns={
        "date": "date",
        "ticker": "ticker",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    })[["ticker", "date", "open", "high", "low", "close", "volume"]].to_dict("records")

    print(f"Inserting {len(records)} documents into MongoDB (this may take a few minutes)...")
    batch_size = 5000
    for i in range(0, len(records), batch_size):
        collection.insert_many(records[i:i + batch_size])
        print(f"  ...{min(i + batch_size, len(records))} documents inserted")

    # Create indexes for fast time-series queries
    collection.create_index([("ticker", 1), ("date", -1)])
    print("MongoDB load complete.")
    client.close()


if __name__ == "__main__":
    df = load_csv()
    load_into_mysql(df)
    load_into_mongo(df)
    print("\nAll done! Both databases are populated.")