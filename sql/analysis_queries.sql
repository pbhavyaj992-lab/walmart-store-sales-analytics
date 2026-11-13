-- 1. Total weekly sales over time
SELECT date, SUM(weekly_sales) AS total_sales
FROM walmart.train GROUP BY 1 ORDER BY 1;

-- 2. Holiday vs non-holiday
SELECT is_holiday, COUNT(*) AS rows, SUM(weekly_sales) AS total_sales,
       AVG(weekly_sales) AS avg_sales
FROM walmart.train GROUP BY 1;

-- 3. Top departments
SELECT dept, SUM(weekly_sales) AS total_sales, AVG(weekly_sales) AS avg_sales
FROM walmart.train GROUP BY 1 ORDER BY total_sales DESC LIMIT 10;

-- 4. Store type summary (join stores)
SELECT s.type, COUNT(DISTINCT s.store) AS stores, SUM(t.weekly_sales) AS total_sales,
       AVG(t.weekly_sales) AS avg_sales
FROM walmart.train t JOIN walmart.stores s USING (store)
GROUP BY 1 ORDER BY total_sales DESC;

-- 5. Driver correlations (store-week level; use the merged output, not raw SQL corr on mismatched dates)
-- See output/driver_correlations.csv — MarkDown1 r=0.32, MarkDown5 r=0.31, the rest near zero.

-- 6. Seasonal-naive baseline check (same store-dept, 52 weeks earlier)
SELECT a.store, a.dept, a.date, a.weekly_sales AS actual,
       b.weekly_sales AS pred_seasonal_naive
FROM walmart.train a
LEFT JOIN walmart.train b
  ON b.store = a.store AND b.dept = a.dept AND b.date = a.date - INTERVAL '52 weeks'
WHERE a.date > DATE '2012-04-27'
ORDER BY a.date, a.store, a.dept;
