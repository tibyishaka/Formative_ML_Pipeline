import os
from datetime import datetime
from flask import Flask, request, jsonify
import pymysql
from pymysql.cursors import DictCursor
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────────────────────
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB")

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB_NAME]
mongo_collection = mongo_db["prices"]


def get_mysql_conn():
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        cursorclass=DictCursor,
        autocommit=True,
    )


# ════════════════════════════════════════════════════════════════════════
# ROOT
# ════════════════════════════════════════════════════════════════════════

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "S&P 500 Time-Series API",
        "sql_endpoints": {
            "create": "POST /api/sql/records",
            "list": "GET /api/sql/records",
            "get_one": "GET /api/sql/records/<id>",
            "update": "PUT /api/sql/records/<id>",
            "delete": "DELETE /api/sql/records/<id>",
            "latest": "GET /api/sql/records/latest?ticker=AAPL",
            "range": "GET /api/sql/records/range?ticker=AAPL&start=2017-01-01&end=2017-03-01",
        },
        "mongo_endpoints": {
            "create": "POST /api/mongo/records",
            "list": "GET /api/mongo/records",
            "get_one": "GET /api/mongo/records/<id>",
            "update": "PUT /api/mongo/records/<id>",
            "delete": "DELETE /api/mongo/records/<id>",
            "latest": "GET /api/mongo/records/latest?ticker=AAPL",
            "range": "GET /api/mongo/records/range?ticker=AAPL&start=2017-01-01&end=2017-03-01",
        }
    })


# ════════════════════════════════════════════════════════════════════════
# MYSQL ENDPOINTS
# ════════════════════════════════════════════════════════════════════════

@app.route("/api/sql/records", methods=["POST"])
def sql_create_record():
    """Create a new daily price record. Requires the ticker to already exist."""
    data = request.get_json()
    required = ["ticker", "date", "open", "high", "low", "close", "volume"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    conn = get_mysql_conn()
    cursor = conn.cursor()

    # Find or create the company
    cursor.execute("SELECT id FROM companies WHERE ticker = %s", (data["ticker"],))
    row = cursor.fetchone()
    if row is None:
        cursor.execute(
            "INSERT INTO companies (ticker, sector_id) VALUES (%s, 1)",
            (data["ticker"],)
        )
        company_id = cursor.lastrowid
    else:
        company_id = row["id"]

    cursor.execute(
        """INSERT INTO daily_prices
           (company_id, price_date, open_price, high_price, low_price, close_price, volume)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (company_id, data["date"], data["open"], data["high"],
         data["low"], data["close"], data["volume"])
    )
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Record created", "id": new_id}), 201


@app.route("/api/sql/records", methods=["GET"])
def sql_list_records():
    """List records, optionally filtered by ?ticker=AAPL, paginated with ?limit=&offset="""
    ticker = request.args.get("ticker")
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))

    conn = get_mysql_conn()
    cursor = conn.cursor()
    if ticker:
        cursor.execute(
            """SELECT dp.id, c.ticker, dp.price_date, dp.open_price, dp.high_price,
                      dp.low_price, dp.close_price, dp.volume
               FROM daily_prices dp JOIN companies c ON dp.company_id = c.id
               WHERE c.ticker = %s ORDER BY dp.price_date DESC LIMIT %s OFFSET %s""",
            (ticker, limit, offset)
        )
    else:
        cursor.execute(
            """SELECT dp.id, c.ticker, dp.price_date, dp.open_price, dp.high_price,
                      dp.low_price, dp.close_price, dp.volume
               FROM daily_prices dp JOIN companies c ON dp.company_id = c.id
               ORDER BY dp.price_date DESC LIMIT %s OFFSET %s""",
            (limit, offset)
        )
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results), 200


@app.route("/api/sql/records/latest", methods=["GET"])
def sql_latest_record():
    """Get the most recent record for a ticker. REQUIRED endpoint."""
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error": "ticker query param is required"}), 400

    conn = get_mysql_conn()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT dp.id, c.ticker, dp.price_date, dp.open_price, dp.high_price,
                  dp.low_price, dp.close_price, dp.volume
           FROM daily_prices dp JOIN companies c ON dp.company_id = c.id
           WHERE c.ticker = %s ORDER BY dp.price_date DESC LIMIT 1""",
        (ticker,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result is None:
        return jsonify({"error": "No records found for that ticker"}), 404
    return jsonify(result), 200


@app.route("/api/sql/records/range", methods=["GET"])
def sql_range_records():
    """Get records in a date range for a ticker. REQUIRED endpoint.
    Example: /api/sql/records/range?ticker=AAPL&start=2017-01-01&end=2017-03-01
    """
    ticker = request.args.get("ticker")
    start = request.args.get("start")
    end = request.args.get("end")
    if not all([ticker, start, end]):
        return jsonify({"error": "ticker, start, and end query params are required"}), 400

    conn = get_mysql_conn()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT dp.id, c.ticker, dp.price_date, dp.open_price, dp.high_price,
                  dp.low_price, dp.close_price, dp.volume
           FROM daily_prices dp JOIN companies c ON dp.company_id = c.id
           WHERE c.ticker = %s AND dp.price_date BETWEEN %s AND %s
           ORDER BY dp.price_date""",
        (ticker, start, end)
    )
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results), 200


@app.route("/api/sql/records/<int:record_id>", methods=["GET"])
def sql_get_record(record_id):
    conn = get_mysql_conn()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT dp.id, c.ticker, dp.price_date, dp.open_price, dp.high_price,
                  dp.low_price, dp.close_price, dp.volume
           FROM daily_prices dp JOIN companies c ON dp.company_id = c.id
           WHERE dp.id = %s""",
        (record_id,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result is None:
        return jsonify({"error": "Record not found"}), 404
    return jsonify(result), 200


@app.route("/api/sql/records/<int:record_id>", methods=["PUT"])
def sql_update_record(record_id):
    data = request.get_json()
    allowed_fields = {
        "open": "open_price", "high": "high_price", "low": "low_price",
        "close": "close_price", "volume": "volume", "date": "price_date"
    }
    updates = []
    values = []
    for key, column in allowed_fields.items():
        if key in data:
            updates.append(f"{column} = %s")
            values.append(data[key])

    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    conn = get_mysql_conn()
    cursor = conn.cursor()
    values.append(record_id)
    cursor.execute(f"UPDATE daily_prices SET {', '.join(updates)} WHERE id = %s", values)
    affected = cursor.rowcount
    cursor.close()
    conn.close()

    if affected == 0:
        return jsonify({"error": "Record not found"}), 404
    return jsonify({"message": "Record updated", "id": record_id}), 200


@app.route("/api/sql/records/<int:record_id>", methods=["DELETE"])
def sql_delete_record(record_id):
    conn = get_mysql_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM daily_prices WHERE id = %s", (record_id,))
    affected = cursor.rowcount
    cursor.close()
    conn.close()

    if affected == 0:
        return jsonify({"error": "Record not found"}), 404
    return jsonify({"message": "Record deleted", "id": record_id}), 200


# ════════════════════════════════════════════════════════════════════════
# MONGODB ENDPOINTS
# ════════════════════════════════════════════════════════════════════════

def serialize_doc(doc):
    """Convert Mongo's ObjectId and datetime into JSON-friendly strings."""
    if doc is None:
        return None
    doc["_id"] = str(doc["_id"])
    if isinstance(doc.get("date"), datetime):
        doc["date"] = doc["date"].isoformat()
    return doc


@app.route("/api/mongo/records", methods=["POST"])
def mongo_create_record():
    data = request.get_json()
    required = ["ticker", "date", "open", "high", "low", "close", "volume"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    data["date"] = datetime.fromisoformat(data["date"])
    result = mongo_collection.insert_one(data)
    return jsonify({"message": "Record created", "id": str(result.inserted_id)}), 201


@app.route("/api/mongo/records", methods=["GET"])
def mongo_list_records():
    ticker = request.args.get("ticker")
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))

    query = {"ticker": ticker} if ticker else {}
    cursor = mongo_collection.find(query).sort("date", -1).skip(offset).limit(limit)
    results = [serialize_doc(doc) for doc in cursor]
    return jsonify(results), 200


@app.route("/api/mongo/records/latest", methods=["GET"])
def mongo_latest_record():
    """REQUIRED endpoint: latest record for a ticker."""
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error": "ticker query param is required"}), 400

    doc = mongo_collection.find_one({"ticker": ticker}, sort=[("date", -1)])
    if doc is None:
        return jsonify({"error": "No records found for that ticker"}), 404
    return jsonify(serialize_doc(doc)), 200


@app.route("/api/mongo/records/range", methods=["GET"])
def mongo_range_records():
    """REQUIRED endpoint: records in a date range for a ticker.
    Example: /api/mongo/records/range?ticker=AAPL&start=2017-01-01&end=2017-03-01
    """
    ticker = request.args.get("ticker")
    start = request.args.get("start")
    end = request.args.get("end")
    if not all([ticker, start, end]):
        return jsonify({"error": "ticker, start, and end query params are required"}), 400

    query = {
        "ticker": ticker,
        "date": {
            "$gte": datetime.fromisoformat(start),
            "$lte": datetime.fromisoformat(end),
        }
    }
    cursor = mongo_collection.find(query).sort("date", 1)
    results = [serialize_doc(doc) for doc in cursor]
    return jsonify(results), 200


@app.route("/api/mongo/records/<record_id>", methods=["GET"])
def mongo_get_record(record_id):
    try:
        doc = mongo_collection.find_one({"_id": ObjectId(record_id)})
    except Exception:
        return jsonify({"error": "Invalid id format"}), 400
    if doc is None:
        return jsonify({"error": "Record not found"}), 404
    return jsonify(serialize_doc(doc)), 200


@app.route("/api/mongo/records/<record_id>", methods=["PUT"])
def mongo_update_record(record_id):
    data = request.get_json()
    allowed_fields = ["open", "high", "low", "close", "volume", "date"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400
    if "date" in updates:
        updates["date"] = datetime.fromisoformat(updates["date"])

    try:
        result = mongo_collection.update_one(
            {"_id": ObjectId(record_id)}, {"$set": updates}
        )
    except Exception:
        return jsonify({"error": "Invalid id format"}), 400

    if result.matched_count == 0:
        return jsonify({"error": "Record not found"}), 404
    return jsonify({"message": "Record updated", "id": record_id}), 200


@app.route("/api/mongo/records/<record_id>", methods=["DELETE"])
def mongo_delete_record(record_id):
    try:
        result = mongo_collection.delete_one({"_id": ObjectId(record_id)})
    except Exception:
        return jsonify({"error": "Invalid id format"}), 400

    if result.deleted_count == 0:
        return jsonify({"error": "Record not found"}), 404
    return jsonify({"message": "Record deleted", "id": record_id}), 200


# ════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run(debug=True, port=5000)