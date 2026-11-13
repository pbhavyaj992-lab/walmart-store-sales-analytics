-- Walmart — PostgreSQL schema. Grain of train: one row per store x dept x week.
CREATE SCHEMA IF NOT EXISTS walmart;

CREATE TABLE walmart.stores (
    store INT PRIMARY KEY, type CHAR(1), size INT);

CREATE TABLE walmart.features (
    store INT REFERENCES walmart.stores(store), date DATE,
    temperature NUMERIC(5,2), fuel_price NUMERIC(5,3),
    markdown1 NUMERIC(10,2), markdown2 NUMERIC(10,2), markdown3 NUMERIC(10,2),
    markdown4 NUMERIC(10,2), markdown5 NUMERIC(10,2),
    cpi NUMERIC(8,3), unemployment NUMERIC(4,2), is_holiday BOOLEAN,
    PRIMARY KEY (store, date));

CREATE TABLE walmart.train (
    store INT REFERENCES walmart.stores(store), dept INT, date DATE,
    weekly_sales NUMERIC(12,2), is_holiday BOOLEAN,
    PRIMARY KEY (store, dept, date));

CREATE INDEX idx_train_date ON walmart.train (date);
CREATE INDEX idx_train_store_dept ON walmart.train (store, dept);
-- NOTE: features.csv dates are DD-MM-YYYY; train/test dates are ISO YYYY-MM-DD.
-- Parse features with dayfirst=True or the join misaligns (see the Python script).
