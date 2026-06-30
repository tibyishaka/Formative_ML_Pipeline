CREATE DATABASE IF NOT EXISTS sp500_db;
USE sp500_db;

-- Drop tables if re-running (clean slate)
DROP TABLE IF EXISTS daily_prices;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS sectors;

-- Table 1: Sectors (lookup table)
CREATE TABLE sectors (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sector_name VARCHAR(100) NOT NULL UNIQUE
);

-- Table 2: Companies (one row per stock ticker)
CREATE TABLE companies (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ticker VARCHAR(10) NOT NULL UNIQUE,
    sector_id INT,
    FOREIGN KEY (sector_id) REFERENCES sectors(id)
);

-- Table 3: Daily Prices (the time-series table, one row per company per day)
CREATE TABLE daily_prices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    price_date DATE NOT NULL,
    open_price FLOAT,
    high_price FLOAT,
    low_price FLOAT,
    close_price FLOAT,
    volume BIGINT,
    FOREIGN KEY (company_id) REFERENCES companies(id),
    UNIQUE KEY unique_company_date (company_id, price_date),
    INDEX idx_date (price_date)
);

-- Insert a default "Unknown" sector so company inserts always have something to link to
INSERT INTO sectors (sector_name) VALUES ('Unknown');