# FinSight - Phase 1: Data Cleaning & SQL Storage
# Cleans all raw data and loads into SQLite database
# MJ - Barclays Analyst Project

import pandas as pd
import numpy as np
import sqlite3
import os
from sqlalchemy import create_engine

print("=" * 55)
print("  FinSight - Phase 1: Data Cleaning & SQL Load")
print("=" * 55)

BASE    = os.path.dirname(__file__) + '/..'
RAW     = BASE + '/data/raw'
PROC    = BASE + '/data/processed'
DB_PATH = BASE + '/database/finsight.db'

os.makedirs(PROC, exist_ok=True)

engine = create_engine(f'sqlite:///{DB_PATH}')

# ── 1. CLEAN STOCK DATA ───────────────────────────────────
print("\n  [1/3] Cleaning stock data...")
stock = pd.read_csv(f'{RAW}/all_banks_stock.csv', parse_dates=['Date'])

# drop rows where close is null or negative
stock = stock[stock['Close'] > 0].copy()
stock = stock.dropna(subset=['Close', 'Volume'])

# fill rolling indicators (first N rows will be NaN due to window)
stock['Volatility_30d'] = stock['Volatility_30d'].fillna(0)
stock['MA_50']          = stock['MA_50'].fillna(stock['Close'])
stock['MA_200']         = stock['MA_200'].fillna(stock['Close'])

# add year and quarter columns for easy slicing in Power BI
stock['Year']    = stock['Date'].dt.year
stock['Quarter'] = stock['Date'].dt.quarter
stock['Month']   = stock['Date'].dt.month
stock['YearQ']   = stock['Date'].dt.to_period('Q').astype(str)

stock.to_csv(f'{PROC}/stock_clean.csv', index=False)
stock.to_sql('stock_prices', engine, if_exists='replace', index=False)
print(f"    {len(stock):,} rows cleaned → stock_prices table")

# ── 2. CLEAN QUARTERLY FINANCIALS ─────────────────────────
print("\n  [2/3] Cleaning quarterly financials...")
fin = pd.read_csv(f'{RAW}/quarterly_financials.csv', parse_dates=['Date'])

fin = fin.dropna()
fin['Revenue_Bn']        = fin['Revenue_Bn'].clip(lower=0)
fin['Net_Income_Bn']     = fin['Net_Income_Bn']
fin['NPA_Ratio_Pct']     = fin['NPA_Ratio_Pct'].clip(lower=0, upper=15)
fin['Capital_Ratio_Pct'] = fin['Capital_Ratio_Pct'].clip(lower=8, upper=25)
fin['Year']              = fin['Date'].dt.year
fin['Quarter']           = fin['Date'].dt.quarter

# profit margin
fin['Profit_Margin_Pct'] = (fin['Net_Income_Bn'] / fin['Revenue_Bn'] * 100).round(2)

# NPA health flag
fin['NPA_Health'] = fin['NPA_Ratio_Pct'].apply(
    lambda x: 'Healthy' if x < 2.5 else ('Watch' if x < 4.0 else 'Stressed')
)

fin.to_csv(f'{PROC}/financials_clean.csv', index=False)
fin.to_sql('quarterly_financials', engine, if_exists='replace', index=False)
print(f"    {len(fin)} rows cleaned → quarterly_financials table")

# ── 3. CLEAN LOAN PORTFOLIO ───────────────────────────────
print("\n  [3/3] Cleaning loan portfolio...")
loans = pd.read_csv(f'{RAW}/loan_portfolio.csv', parse_dates=['Issue_Date'])

loans = loans[loans['Amount'] > 0]
loans = loans[loans['Interest_Rate'].between(1, 25)]
loans['Amount_Band'] = pd.cut(
    loans['Amount'],
    bins=[0, 10_000, 50_000, 200_000, 500_000, float('inf')],
    labels=['<10K', '10-50K', '50-200K', '200-500K', '500K+']
)
loans['Issue_Year']  = loans['Issue_Date'].dt.year
loans['Issue_Month'] = loans['Issue_Date'].dt.month

loans.to_csv(f'{PROC}/loans_clean.csv', index=False)
loans.to_sql('loan_portfolio', engine, if_exists='replace', index=False)
print(f"    {len(loans):,} rows cleaned → loan_portfolio table")

# ── 4. CREATE SUMMARY VIEW ────────────────────────────────
print("\n  Creating summary analytics view...")
conn = sqlite3.connect(DB_PATH)
conn.execute("""
CREATE VIEW IF NOT EXISTS bank_summary AS
SELECT
    q.Bank,
    q.Year,
    q.Quarter,
    q.Revenue_Bn,
    q.Net_Income_Bn,
    q.Cost_to_Income,
    q.NPA_Ratio_Pct,
    q.ROE_Pct,
    q.Capital_Ratio_Pct,
    q.NPA_Health,
    q.Profit_Margin_Pct
FROM quarterly_financials q
ORDER BY q.Bank, q.Year, q.Quarter
""")
conn.commit()

# quick verification
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' OR type='view'", conn)
print(f"\n  Database tables & views: {list(tables['name'])}")

# row counts
for t in ['stock_prices', 'quarterly_financials', 'loan_portfolio']:
    cnt = pd.read_sql(f"SELECT COUNT(*) as n FROM {t}", conn).iloc[0]['n']
    print(f"    {t}: {cnt:,} rows")

conn.close()

print("\n" + "=" * 55)
print("  DATA CLEANING & SQL LOAD COMPLETE")
print(f"  Database: database/finsight.db")
print("=" * 55)
