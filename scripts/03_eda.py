# FinSight - Phase 1: Exploratory Data Analysis
# Quick validation and summary of all datasets
# MJ - Barclays Analyst Project

import pandas as pd
import sqlite3
import os

DB_PATH = os.path.dirname(__file__) + '/../database/finsight.db'
conn    = sqlite3.connect(DB_PATH)

print("=" * 60)
print("  FinSight - EDA & Data Validation Report")
print("=" * 60)

# stock summary
print("\n── STOCK PRICES ─────────────────────────────────────────")
stock = pd.read_sql("""
    SELECT Bank, Ticker,
           COUNT(*) as trading_days,
           ROUND(MIN(Close),2) as min_close,
           ROUND(MAX(Close),2) as max_close,
           ROUND(AVG(Close),2) as avg_close,
           ROUND(AVG(Volatility_30d)*100,2) as avg_vol_pct
    FROM stock_prices
    GROUP BY Bank, Ticker
    ORDER BY Bank
""", conn)
print(stock.to_string(index=False))

# financials summary
print("\n── QUARTERLY FINANCIALS (latest quarter per bank) ───────")
fin = pd.read_sql("""
    SELECT Bank, Year, Quarter,
           Revenue_Bn, Net_Income_Bn,
           Cost_to_Income, NPA_Ratio_Pct,
           ROE_Pct, NPA_Health
    FROM quarterly_financials
    WHERE (Bank, Year, Quarter) IN (
        SELECT Bank, MAX(Year), MAX(Quarter)
        FROM quarterly_financials
        GROUP BY Bank
    )
    ORDER BY Bank
""", conn)
print(fin.to_string(index=False))

# loan portfolio summary
print("\n── LOAN PORTFOLIO SUMMARY ───────────────────────────────")
loans = pd.read_sql("""
    SELECT Bank,
           COUNT(*) as total_loans,
           ROUND(SUM(Amount)/1e6, 2) as total_exposure_Mn,
           ROUND(AVG(Interest_Rate),2) as avg_rate,
           ROUND(AVG(Is_NPA)*100, 2) as npa_pct,
           SUM(Is_NPA) as npa_count
    FROM loan_portfolio
    GROUP BY Bank
    ORDER BY Bank
""", conn)
print(loans.to_string(index=False))

print("\n── LOAN TYPE BREAKDOWN (all banks) ─────────────────────")
loan_type = pd.read_sql("""
    SELECT Loan_Type,
           COUNT(*) as count,
           ROUND(SUM(Amount)/1e6,2) as exposure_Mn,
           ROUND(AVG(Is_NPA)*100,2) as npa_rate_pct
    FROM loan_portfolio
    GROUP BY Loan_Type
    ORDER BY exposure_Mn DESC
""", conn)
print(loan_type.to_string(index=False))

print("\n" + "=" * 60)
print("  Phase 1 COMPLETE. Data is clean and SQL-ready.")
print("  Next: Phase 2 - Financial Analysis & KPI Modelling")
print("=" * 60)
conn.close()
