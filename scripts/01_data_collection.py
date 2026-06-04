# FinSight - Phase 1: Data Generation
# Generates realistic bank financial data using statistical modeling
# This mirrors real-world practice - banks use synthetic data for testing & MI dev
# MJ - Barclays Analyst Project

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

print("=" * 55)
print("  FinSight - Financial Intelligence Dashboard")
print("  Phase 1: Data Generation (Synthetic)")
print("=" * 55)

np.random.seed(42)

raw_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
os.makedirs(raw_dir, exist_ok=True)

# ── 1. BANK STOCK PRICE DATA ──────────────────────────────
# realistic starting prices and volatility per bank
BANKS = {
    "Barclays":       {"ticker": "BCS",  "start_price": 8.50,  "vol": 0.28, "drift": 0.04},
    "HSBC":           {"ticker": "HSBC", "start_price": 38.00, "vol": 0.22, "drift": 0.05},
    "JPMorgan Chase": {"ticker": "JPM",  "start_price": 104.0, "vol": 0.20, "drift": 0.08},
    "Goldman Sachs":  {"ticker": "GS",   "start_price": 200.0, "vol": 0.25, "drift": 0.07},
    "Deutsche Bank":  {"ticker": "DB",   "start_price": 9.00,  "vol": 0.35, "drift": 0.02},
}

dates = pd.date_range(start="2019-01-01", end="2024-12-31", freq="B")  # business days only
all_stock_data = []

for bank_name, params in BANKS.items():
    print(f"\n  Generating stock data for {bank_name}...")

    n = len(dates)
    dt = 1 / 252

    # geometric Brownian motion - same model used by quant teams
    daily_returns = np.random.normal(
        loc   = params['drift'] * dt,
        scale = params['vol'] * np.sqrt(dt),
        size  = n
    )

    # covid crash in early 2020
    covid_mask = (dates >= "2020-02-15") & (dates <= "2020-03-25")
    daily_returns[covid_mask] += np.random.uniform(-0.04, -0.01, covid_mask.sum())

    # recovery boost mid 2020
    recovery_mask = (dates >= "2020-04-01") & (dates <= "2020-06-30")
    daily_returns[recovery_mask] += np.random.uniform(0.005, 0.015, recovery_mask.sum())

    # 2022 rate hike impact
    rate_mask = (dates >= "2022-03-01") & (dates <= "2022-10-31")
    daily_returns[rate_mask] += np.random.uniform(-0.008, 0.008, rate_mask.sum())

    prices = [params['start_price']]
    for r in daily_returns[1:]:
        prices.append(prices[-1] * (1 + r))

    prices = np.array(prices)

    # OHLV from close
    high   = prices * (1 + np.abs(np.random.normal(0, 0.008, n)))
    low    = prices * (1 - np.abs(np.random.normal(0, 0.008, n)))
    open_  = prices * (1 + np.random.normal(0, 0.005, n))
    volume = np.random.randint(5_000_000, 25_000_000, n)

    df = pd.DataFrame({
        'Date':          dates,
        'Bank':          bank_name,
        'Ticker':        params['ticker'],
        'Open':          open_.round(2),
        'High':          high.round(2),
        'Low':           low.round(2),
        'Close':         prices.round(2),
        'Volume':        volume,
        'Daily_Return':  daily_returns.round(6),
    })

    df['Volatility_30d'] = df['Daily_Return'].rolling(30).std() * np.sqrt(252)
    df['MA_50']          = df['Close'].rolling(50).mean().round(2)
    df['MA_200']         = df['Close'].rolling(200).mean().round(2)
    df['Risk_Flag']      = df['Volatility_30d'].apply(
        lambda x: 'High' if pd.notna(x) and x > 0.30
                  else ('Medium' if pd.notna(x) and x > 0.15 else 'Low')
    )

    fname = os.path.join(raw_dir, f"{params['ticker']}_stock.csv")
    df.to_csv(fname, index=False)
    print(f"    {len(df):,} trading days saved → {params['ticker']}_stock.csv")
    all_stock_data.append(df)

master_stock = pd.concat(all_stock_data, ignore_index=True)
master_stock.to_csv(os.path.join(raw_dir, "all_banks_stock.csv"), index=False)

# ── 2. QUARTERLY FINANCIALS ───────────────────────────────
print("\n\n  Generating quarterly financial statements...")

quarters = pd.date_range(start="2019-01-01", end="2024-12-31", freq="QE")
fin_rows = []

FINANCIALS = {
    "Barclays":       {"revenue": 5.2,  "growth": 0.04, "npa_base": 0.032},
    "HSBC":           {"revenue": 13.5, "growth": 0.05, "npa_base": 0.025},
    "JPMorgan Chase": {"revenue": 28.0, "growth": 0.07, "npa_base": 0.018},
    "Goldman Sachs":  {"revenue": 9.5,  "growth": 0.06, "npa_base": 0.012},
    "Deutsche Bank":  {"revenue": 6.8,  "growth": 0.02, "npa_base": 0.045},
}

for bank_name, params in FINANCIALS.items():
    for i, q in enumerate(quarters):
        revenue   = params['revenue'] * (1 + params['growth']) ** (i / 4)
        revenue  += np.random.normal(0, revenue * 0.05)

        cost_ratio    = np.random.uniform(0.58, 0.72)
        op_costs      = revenue * cost_ratio
        net_income    = (revenue - op_costs) * np.random.uniform(0.65, 0.80)
        npa_ratio     = params['npa_base'] + np.random.normal(0, 0.003)

        # covid shock on financials
        if q.year == 2020 and q.quarter in [1, 2]:
            net_income *= np.random.uniform(0.4, 0.7)
            npa_ratio  *= np.random.uniform(1.3, 1.8)

        fin_rows.append({
            'Quarter':           f'{q.year}-Q{q.quarter}',
            'Date':              q,
            'Bank':              bank_name,
            'Revenue_Bn':        round(max(revenue, 0.1), 3),
            'Operating_Cost_Bn': round(op_costs, 3),
            'Net_Income_Bn':     round(net_income, 3),
            'Cost_to_Income':    round(cost_ratio * 100, 2),
            'NPA_Ratio_Pct':     round(max(npa_ratio * 100, 0.5), 3),
            'ROE_Pct':           round(np.random.uniform(6, 14), 2),
            'Capital_Ratio_Pct': round(np.random.uniform(13, 18), 2),
        })

fin_df = pd.DataFrame(fin_rows)
fin_df.to_csv(os.path.join(raw_dir, "quarterly_financials.csv"), index=False)
print(f"    {len(fin_df)} quarterly records saved → quarterly_financials.csv")

# ── 3. LOAN PORTFOLIO ─────────────────────────────────────
print("\n  Generating loan portfolio data...")

loan_types   = ['Mortgage', 'Personal Loan', 'Business Loan', 'Auto Loan', 'Credit Card']
loan_rows    = []

for bank_name in BANKS:
    for _ in range(800):
        loan_type   = np.random.choice(loan_types, p=[0.35, 0.20, 0.25, 0.10, 0.10])
        amount      = {
            'Mortgage':      np.random.uniform(80_000,  500_000),
            'Personal Loan': np.random.uniform(5_000,   50_000),
            'Business Loan': np.random.uniform(50_000,  2_000_000),
            'Auto Loan':     np.random.uniform(8_000,   60_000),
            'Credit Card':   np.random.uniform(1_000,   25_000),
        }[loan_type]

        issue_date  = datetime(2019,1,1) + timedelta(days=np.random.randint(0, 365*5))
        tenor_years = np.random.choice([1, 2, 3, 5, 10, 15, 20, 25, 30])
        int_rate    = np.random.uniform(3.5, 12.5)
        status      = np.random.choice(
            ['Current', 'Current', 'Current', 'Current', 'Current',
             '30-day DPD', '60-day DPD', '90+ DPD', 'Written Off'],
            p=[0.70, 0.10, 0.07, 0.05, 0.02, 0.02, 0.02, 0.01, 0.01]
        )

        loan_rows.append({
            'Bank':         bank_name,
            'Loan_Type':    loan_type,
            'Amount':       round(amount, 2),
            'Interest_Rate':round(int_rate, 2),
            'Issue_Date':   issue_date.strftime('%Y-%m-%d'),
            'Tenor_Years':  tenor_years,
            'Status':       status,
            'Is_NPA':       1 if status in ['90+ DPD', 'Written Off'] else 0,
            'Region':       np.random.choice(['UK', 'US', 'Europe', 'Asia', 'Middle East'],
                                             p=[0.35, 0.25, 0.20, 0.15, 0.05]),
        })

loan_df = pd.DataFrame(loan_rows)
loan_df.to_csv(os.path.join(raw_dir, "loan_portfolio.csv"), index=False)
print(f"    {len(loan_df):,} loan records saved → loan_portfolio.csv")

# ── SUMMARY ───────────────────────────────────────────────
print("\n" + "=" * 55)
print("  DATA COLLECTION COMPLETE")
print("=" * 55)
print(f"  Stock data:     {len(master_stock):,} rows  (5 banks × ~1,500 trading days)")
print(f"  Financials:     {len(fin_df)} rows  (5 banks × 24 quarters)")
print(f"  Loan portfolio: {len(loan_df):,} rows  (5 banks × 800 loans each)")
print(f"\n  All files saved to: data/raw/")
print("=" * 55)
