USE sp500_db;

-- Query 1: Latest record for a given ticker
SELECT c.ticker, dp.price_date, dp.close_price
FROM daily_prices dp
JOIN companies c ON dp.company_id = c.id
WHERE c.ticker = 'AAPL'
ORDER BY dp.price_date DESC
LIMIT 1;

-- Query 2: Records within a date range for a given ticker
SELECT c.ticker, dp.price_date, dp.open_price, dp.close_price, dp.volume
FROM daily_prices dp
JOIN companies c ON dp.company_id = c.id
WHERE c.ticker = 'AAPL'
  AND dp.price_date BETWEEN '2017-01-01' AND '2017-03-01'
ORDER BY dp.price_date;

-- Query 3: Top 10 companies by average closing price
SELECT c.ticker, AVG(dp.close_price) AS avg_close
FROM daily_prices dp
JOIN companies c ON dp.company_id = c.id
GROUP BY c.ticker
ORDER BY avg_close DESC
LIMIT 10;

-- Query 4 (bonus): Highest single-day trading volume across all stocks
SELECT c.ticker, dp.price_date, dp.volume
FROM daily_prices dp
JOIN companies c ON dp.company_id = c.id
ORDER BY dp.volume DESC
LIMIT 5;