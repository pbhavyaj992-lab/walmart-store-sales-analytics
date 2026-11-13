# Data dictionary — Walmart (raw files, `data/raw/`)

| File | Rows | Grain | Key columns |
|---|---|---|---|
| train.csv | 421,570 | store x dept x week | Store, Dept, Date (ISO), Weekly_Sales (USD), IsHoliday |
| features.csv | 8,190 | store x week | Store, Date (**DD-MM-YYYY** — parse dayfirst=True), Temperature, Fuel_Price, MarkDown1–5, CPI, Unemployment, IsHoliday |
| stores.csv | 45 | store | Store, Type (A/B/C), Size (sq ft) |
| test.csv | 115,064 | store x dept x week | Store, Dept, Date, IsHoliday (no Weekly_Sales — that is the prediction task) |

Notes: 1,285 train rows have negative Weekly_Sales (returns/adjustments). Markdowns only
exist after Nov 2011 and cover 36–50% of feature rows. CPI/Unemployment are missing for
7.14% of feature rows. Forecast holdout in this project: train to 2012-04-27, test
2012-05-04 to 2012-10-26 (26 weeks, 76,903 rows); predictions in
`output/forecast_holdout_predictions.csv`.
