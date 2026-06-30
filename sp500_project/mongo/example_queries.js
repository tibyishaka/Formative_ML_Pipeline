use("sp500_db");

// Query 1: Latest record for a given ticker
db.prices.find({ ticker: "AAPL" }).sort({ date: -1 }).limit(1);

// Query 2: Records within a date range for a given ticker
db.prices.find({
  ticker: "AAPL",
  date: { $gte: ISODate("2017-01-01"), $lte: ISODate("2017-03-01") }
}).sort({ date: 1 });

// Query 3: Top 10 tickers by average closing price
db.prices.aggregate([
  { $group: { _id: "$ticker", avgClose: { $avg: "$close" } } },
  { $sort: { avgClose: -1 } },
  { $limit: 10 }
]);

// Query 4 (bonus): Highest single-day trading volume across all stocks
db.prices.find().sort({ volume: -1 }).limit(5);