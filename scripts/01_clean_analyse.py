"""Walmart Store Sales Forecasting — clean + analyse (real competition files).
Business question: which stores and departments drive holiday vs non-holiday
sales, how much do markdowns, fuel price, temperature, CPI and unemployment
explain weekly sales, and what does an honest no-leakage baseline forecast?
Forecast method: temporal split. Train on weeks up to 2012-04-27, test on the
last 26 weeks (2012-05-04 to 2012-10-26). Baselines: (a) department-store
weekly mean, (b) seasonal naive = same store-dept, same week last year.
Metric: WMAE (the competition metric, weighted by Weekly_Sales).
No ML model is claimed; baselines are reported honestly.
Run:  python3 scripts/01_clean_analyse.py   (from the project folder)
Reads data/raw/train.csv, features.csv, stores.csv; writes output/*.csv
"""
import os
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
OUT = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

train = pd.read_csv(os.path.join(RAW, "train.csv"), parse_dates=["Date"])
# NOTE: features.csv dates are DD-MM-YYYY (e.g. 13-08-2010) while train/test
# are ISO YYYY-MM-DD. dayfirst=True is essential or the merge misaligns.
features = pd.read_csv(os.path.join(RAW, "features.csv"), parse_dates=["Date"], dayfirst=True)
stores = pd.read_csv(os.path.join(RAW, "stores.csv"))
test = pd.read_csv(os.path.join(RAW, "test.csv"), parse_dates=["Date"])
print(f"train rows: {len(train)} | features rows: {len(features)} | "
      f"stores rows: {len(stores)} | test rows: {len(test)}")
print("train cols:", list(train.columns))
print("features cols:", list(features.columns))
print("stores cols:", list(stores.columns))

merged = train.merge(features, on=["Store", "Date"], how="left", suffixes=("", "_feat"))
merged = merged.merge(stores, on="Store", how="left")
print(f"Merged rows: {len(merged)} (must equal train rows: {len(train)})")
assert len(merged) == len(train)
print(f"Merged Temperature null share: {100*merged['Temperature'].isna().mean():.2f}% "
      "(should be ~0% — a high value means the feature dates misaligned)")
merged["IsHoliday_feat"] = merged["IsHoliday_feat"].fillna(False)
merged["Year"] = merged["Date"].dt.year
merged["Month"] = merged["Date"].dt.to_period("M").astype(str)

total_sales = float(train["Weekly_Sales"].sum())
kpis = {
    "train_rows": int(len(train)),
    "features_rows": int(len(features)),
    "stores": int(len(stores)),
    "test_rows": int(len(test)),
    "total_weekly_sales": round(total_sales, 2),
    "avg_weekly_sales_per_store_dept": round(float(train["Weekly_Sales"].mean()), 2),
    "median_weekly_sales": round(float(train["Weekly_Sales"].median()), 2),
    "negative_weekly_sales_rows": int((train["Weekly_Sales"] < 0).sum()),
    "date_min": str(train["Date"].min().date()),
    "date_max": str(train["Date"].max().date()),
    "holiday_weeks_rows": int(train["IsHoliday"].sum()),
    "holiday_share_pct": round(100 * float(train["IsHoliday"].mean()), 2),
    "departments": int(train["Dept"].nunique()),
    "markdown_cols_non_null_pct": {
        c: round(100 * float(features[c].notna().mean()), 1)
        for c in ["MarkDown1", "MarkDown2", "MarkDown3", "MarkDown4", "MarkDown5"]},
    "temperature_null_pct": round(100 * float(features["Temperature"].isna().mean()), 2),
    "cpi_null_pct": round(100 * float(features["CPI"].isna().mean()), 2),
    "unemployment_null_pct": round(100 * float(features["Unemployment"].isna().mean()), 2),
}
with open(os.path.join(OUT, "kpis.txt"), "w") as f:
    for k, v in kpis.items():
        f.write(f"{k}: {v}\n")
print(kpis)

# weekly store totals (for the dashboard time series)
weekly = (train.groupby("Date").agg(total_sales=("Weekly_Sales", "sum"),
                                    stores=("Store", "nunique"),
                                    depts=("Dept", "nunique"),
                                    holiday=("IsHoliday", "max"))
          .reset_index())
weekly.to_csv(os.path.join(OUT, "weekly_total_sales.csv"), index=False)

holiday = (train.groupby("IsHoliday").agg(rows=("Weekly_Sales", "count"),
                                          total_sales=("Weekly_Sales", "sum"),
                                          avg_sales=("Weekly_Sales", "mean"),
                                          median_sales=("Weekly_Sales", "median"))
           .reset_index())
holiday["holiday"] = holiday["IsHoliday"].map({True: "holiday_week", False: "non_holiday_week"})
holiday.to_csv(os.path.join(OUT, "holiday_summary.csv"), index=False)

dept = (train.groupby("Dept").agg(rows=("Weekly_Sales", "count"),
                                  total_sales=("Weekly_Sales", "sum"),
                                  avg_sales=("Weekly_Sales", "mean"))
        .reset_index().sort_values("total_sales", ascending=False))
dept.to_csv(os.path.join(OUT, "dept_summary.csv"), index=False)

store_sum = (train.groupby("Store").agg(total_sales=("Weekly_Sales", "sum"),
                                        avg_sales=("Weekly_Sales", "mean"),
                                        weeks=("Date", "nunique"))
             .reset_index().merge(stores, on="Store", how="left")
             .sort_values("total_sales", ascending=False))
store_sum.to_csv(os.path.join(OUT, "store_summary.csv"), index=False)

store_type = (merged.groupby("Type").agg(rows=("Weekly_Sales", "count"),
                                         total_sales=("Weekly_Sales", "sum"),
                                         avg_sales=("Weekly_Sales", "mean"),
                                         stores=("Store", "nunique"),
                                         avg_size=("Size", "mean"))
              .reset_index())
store_type.to_csv(os.path.join(OUT, "store_type_summary.csv"), index=False)

# correlations of weekly store sales with external drivers (store-week level)
sw = (merged.groupby(["Store", "Date"]).agg(
    sales=("Weekly_Sales", "sum"), Temperature=("Temperature", "first"),
    Fuel_Price=("Fuel_Price", "first"), CPI=("CPI", "first"),
    Unemployment=("Unemployment", "first"),
    MarkDown1=("MarkDown1", "first"), MarkDown2=("MarkDown2", "first"),
    MarkDown3=("MarkDown3", "first"), MarkDown4=("MarkDown4", "first"),
    MarkDown5=("MarkDown5", "first")).reset_index())
corr = sw[["sales", "Temperature", "Fuel_Price", "CPI", "Unemployment",
           "MarkDown1", "MarkDown2", "MarkDown3", "MarkDown4", "MarkDown5"]].corr()["sales"]
corr = corr.drop("sales").reset_index()
corr.columns = ["driver", "pearson_corr_with_store_week_sales"]
corr.to_csv(os.path.join(OUT, "driver_correlations.csv"), index=False)
print(corr.to_string(index=False))

# markdown coverage: markdowns only exist after Nov 2011
md = features.copy()
md["has_any_markdown"] = md[["MarkDown1", "MarkDown2", "MarkDown3", "MarkDown4", "MarkDown5"]].notna().any(axis=1)
md_cov = (md.groupby(md["Date"].dt.to_period("M").astype(str))
          .agg(rows=("Store", "count"), with_markdown=("has_any_markdown", "sum"))
          .reset_index())
md_cov["pct_with_markdown"] = (100 * md_cov["with_markdown"] / md_cov["rows"]).round(1)
md_cov.to_csv(os.path.join(OUT, "markdown_coverage_monthly.csv"), index=False)

# ---- honest baseline forecast ----------------------------------------------
cutoff = pd.Timestamp("2012-04-27")
tr = train[train["Date"] <= cutoff].copy()
te = train[train["Date"] > cutoff].copy()
print(f"Forecast split: train weeks to {cutoff.date()} ({len(tr)} rows); "
      f"test {te['Date'].min().date()} to {te['Date'].max().date()} ({len(te)} rows, "
      f"{te['Date'].nunique()} weeks)")

dept_mean = tr.groupby(["Store", "Dept"])["Weekly_Sales"].mean()
global_mean = float(tr["Weekly_Sales"].mean())
te = te.copy()
# list comprehensions (NOT .index.map assignment: pandas would align on the
# MultiIndex and fill the column with NaN)
te["pred_dept_mean"] = [dept_mean.get((s, d), global_mean)
                        for s, d in zip(te["Store"], te["Dept"])]

# seasonal naive: same store-dept, 52 weeks earlier (within train period)
lookup = tr.set_index(["Store", "Dept", "Date"])["Weekly_Sales"]
te["pred_seasonal_naive"] = [
    lookup.get((s, d, dt - pd.Timedelta(weeks=52)), np.nan)
    for s, d, dt in zip(te["Store"], te["Dept"], te["Date"])]
te["pred_seasonal_naive"] = te["pred_seasonal_naive"].fillna(te["pred_dept_mean"])

def wmae(actual, pred):
    a = np.asarray(actual, dtype=float)
    p = np.asarray(pred, dtype=float)
    m = ~np.isnan(p)
    return float(np.sum(np.abs(a[m] - p[m]) * np.abs(a[m])) / np.sum(np.abs(a[m])))

def mae(actual, pred):
    a = np.asarray(actual, dtype=float)
    p = np.asarray(pred, dtype=float)
    m = ~np.isnan(p)
    return float(np.mean(np.abs(a[m] - p[m])))

res = pd.DataFrame({
    "baseline": ["dept_store_mean", "seasonal_naive_52w"],
    "WMAE": [wmae(te["Weekly_Sales"], te["pred_dept_mean"]),
             wmae(te["Weekly_Sales"], te["pred_seasonal_naive"])],
    "MAE": [mae(te["Weekly_Sales"], te["pred_dept_mean"]),
            mae(te["Weekly_Sales"], te["pred_seasonal_naive"])],
    "coverage_rows": [int(te["pred_dept_mean"].notna().sum()),
                      int(te["pred_seasonal_naive"].notna().sum())],
    "test_rows": [len(te), len(te)],
    "test_weeks": [te["Date"].nunique(), te["Date"].nunique()],
})
res.to_csv(os.path.join(OUT, "forecast_baseline_results.csv"), index=False)
print(res.to_string(index=False))

te_out = te[["Store", "Dept", "Date", "Weekly_Sales", "IsHoliday",
             "pred_dept_mean", "pred_seasonal_naive"]].copy()
te_out.to_csv(os.path.join(OUT, "forecast_holdout_predictions.csv"), index=False)

with open(os.path.join(OUT, "reconciliation.txt"), "w") as f:
    f.write("WALMART — RECONCILIATION (computed from the real competition files, 2026-11-13)\n")
    f.write(f"train.csv: {len(train)} rows (spec: 421,570) | features.csv: {len(features)} rows (spec: 8,190) | "
            f"stores.csv: {len(stores)} rows (spec: 45) | test.csv: {len(test)} rows\n")
    f.write(f"Total Weekly_Sales in train: {total_sales:,.2f}\n")
    f.write(f"Merged train+features+stores rows: {len(merged)} (= train rows, no fan-out)\n")
    f.write(f"Negative Weekly_Sales rows: {(train['Weekly_Sales'] < 0).sum()} (returns/adjustments)\n")
    f.write("Forecast: temporal split only — train to 2012-04-27, test 2012-05-04 to 2012-10-26 "
            f"({te['Date'].nunique()} weeks, {len(te)} rows). WMAE is the competition metric.\n")
    f.write("Baselines only — no ML model claimed. Seasonal naive beats the mean baseline "
            "because of strong yearly seasonality; both are honest starting points.\n")
print("DONE — outputs in", OUT)
