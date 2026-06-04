# FinSight - Phase 2: Financial Forecasting Model
# Forecasts revenue and NPA ratio for next 4 quarters per bank
# Uses Linear Regression + trend analysis - same approach used in bank planning teams
# MJ - FinSight Project

import pandas as pd
import numpy as np
import sqlite3
import os
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_absolute_percentage_error

print("=" * 60)
print("  FinSight - Phase 2: Forecasting Model")
print("=" * 60)

BASE    = os.path.dirname(__file__) + '/..'
DB_PATH = BASE + '/database/finsight.db'
PROC    = BASE + '/data/processed'

conn = sqlite3.connect(DB_PATH)
fin  = pd.read_sql("SELECT * FROM kpi_financials ORDER BY Bank, Year, Quarter", conn)

forecast_rows = []

for bank in fin['Bank'].unique():
    print(f"\n  Forecasting for {bank}...")
    bdf = fin[fin['Bank'] == bank].copy().reset_index(drop=True)
    bdf['t'] = np.arange(len(bdf))

    for metric, label in [('Revenue_Bn', 'Revenue'), ('NPA_Ratio_Pct', 'NPA Ratio')]:
        y = bdf[metric].values
        t = bdf['t'].values.reshape(-1, 1)

        # polynomial degree 2 captures curves better than straight line
        poly   = PolynomialFeatures(degree=2)
        t_poly = poly.fit_transform(t)
        model  = LinearRegression()
        model.fit(t_poly, y)

        # in-sample accuracy
        y_pred = model.predict(t_poly)
        mape   = mean_absolute_percentage_error(y, y_pred) * 100

        # forecast next 4 quarters
        last_t  = len(bdf)
        last_yr = int(bdf['Year'].iloc[-1])
        last_q  = int(bdf['Quarter'].iloc[-1])

        for i in range(1, 5):
            fq = last_q + i
            fy = last_yr + (fq - 1) // 4
            fq = ((fq - 1) % 4) + 1
            ft = np.array([[last_t + i]])
            ft_poly = poly.transform(ft)
            fval = model.predict(ft_poly)[0]

            # add realistic uncertainty band (widens further out)
            uncertainty = abs(fval) * 0.03 * i

            forecast_rows.append({
                'Bank':            bank,
                'Metric':          metric,
                'Metric_Label':    label,
                'Forecast_Year':   fy,
                'Forecast_Quarter':fq,
                'Period':          f'{fy}-Q{fq}',
                'Forecast_Value':  round(max(fval, 0), 3),
                'Lower_Bound':     round(max(fval - uncertainty, 0), 3),
                'Upper_Bound':     round(fval + uncertainty, 3),
                'Model_MAPE_Pct':  round(mape, 2),
                'Confidence':      'High' if mape < 5 else ('Medium' if mape < 10 else 'Low'),
            })

        print(f"    {label}: MAPE = {mape:.2f}% → "
              f"{'High' if mape < 5 else 'Medium' if mape < 10 else 'Low'} confidence")

forecast_df = pd.DataFrame(forecast_rows)

# pivot for easy reading: revenue forecast
rev_forecast = forecast_df[forecast_df['Metric'] == 'Revenue_Bn'].pivot(
    index='Period', columns='Bank', values='Forecast_Value'
).round(3)

npa_forecast = forecast_df[forecast_df['Metric'] == 'NPA_Ratio_Pct'].pivot(
    index='Period', columns='Bank', values='Forecast_Value'
).round(3)

# save
forecast_df.to_sql('forecasts', conn, if_exists='replace', index=False)
forecast_df.to_csv(f'{PROC}/forecasts.csv', index=False)

print("\n" + "=" * 60)
print("  REVENUE FORECAST — Next 4 Quarters (Bn)")
print("=" * 60)
print(rev_forecast.to_string())

print("\n" + "=" * 60)
print("  NPA RATIO FORECAST — Next 4 Quarters (%)")
print("=" * 60)
print(npa_forecast.to_string())

print("\n" + "=" * 60)
print("  Forecasting Model COMPLETE")
print(f"  {len(forecast_df)} forecast data points saved → forecasts table")
print("=" * 60)

conn.close()
