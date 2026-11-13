# Power BI model — Walmart Store Sales Analytics

No .pbix is in this repo (no Power BI Desktop here). Build it from this document:
load the raw CSVs in `data/raw/` (or the merged logic in `scripts/01_clean_analyse.py`),
or connect Power BI to the PostgreSQL schema in `sql/schema.sql`.

## Star schema
- **FactWeeklySales** (grain: store x dept x week) — train.csv.
  Weekly_Sales, IsHoliday.
- **DimStore** — stores.csv: Store, Type (A/B/C), Size.
- **DimDept** — Dept (81 values).
- **DimDate** — Date, year, month, week, IsHoliday.
- **DimFeatures** — features.csv: Temperature, Fuel_Price, MarkDown1-5, CPI, Unemployment.
- Relationships: FactWeeklySales → DimStore, → DimDept, → DimDate, → DimFeatures
  (on Store + Date).

## DAX measures
```dax
Total Sales = SUM(FactWeeklySales[Weekly_Sales])
Avg Weekly Sales = AVERAGE(FactWeeklySales[Weekly_Sales])
Holiday Sales = CALCULATE([Total Sales], FactWeeklySales[IsHoliday] = TRUE())
Non-Holiday Sales = CALCULATE([Total Sales], FactWeeklySales[IsHoliday] = FALSE())
Holiday Lift % = 100 * DIVIDE([Holiday Sales], [Non-Holiday Sales]) - 100
Sales LY Same Week = CALCULATE([Total Sales], SAMEPERIODLASTYEAR(DimDate[Date]))
YoY Change % = DIVIDE([Total Sales] - [Sales LY Same Week], [Sales LY Same Week])
-- Forecast baselines live in output/forecast_baseline_results.csv:
-- seasonal naive WMAE 4,219.36 beats dept-store mean WMAE 5,989.65.
-- Any model must beat 4,219.36 WMAE on the same 26-week holdout to claim value.
```

## Pages
1. **Overview** — total sales USD 6.74bn, weekly trend line, sales by store type.
2. **Stores & departments** — top departments (92, 95), store ranking, Type A vs B vs C.
3. **Holidays** — holiday vs non-holiday comparison; the four Super Bowl / Thanksgiving / Christmas peaks.
4. **Drivers & forecast** — markdown coverage and correlations; honest baseline results (WMAE table).
