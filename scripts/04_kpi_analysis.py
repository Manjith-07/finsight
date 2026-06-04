# FinSight - Phase 2: Financial KPI Analysis
# Calculates all key banking metrics used in real MI reporting
# MJ - FinSight Project

import pandas as pd
import numpy as np
import sqlite3
import os

print("=" * 60)
print("  FinSight - Phase 2: KPI Analysis")
print("=" * 60)

BASE    = os.path.dirname(__file__) + '/..'
DB_PATH = BASE + '/database/finsight.db'
PROC    = BASE + '/data/processed'

conn = sqlite3.connect(DB_PATH)

# ── 1. PROFITABILITY KPIs ─────────────────────────────────
print("\n  [1/5] Calculating profitability KPIs...")
fin = pd.read_sql("SELECT * FROM quarterly_financials", conn, parse_dates=['Date'])

fin['Profit_Margin_Pct']    = (fin['Net_Income_Bn'] / fin['Revenue_Bn'] * 100).round(2)
fin['Revenue_Growth_Pct']   = fin.groupby('Bank')['Revenue_Bn'].pct_change() * 100
fin['Income_Growth_Pct']    = fin.groupby('Bank')['Net_Income_Bn'].pct_change() * 100
fin['Efficiency_Score']     = (100 - fin['Cost_to_Income']).round(2)

# YoY revenue growth (compare same quarter previous year)
fin = fin.sort_values(['Bank', 'Year', 'Quarter'])
fin['Revenue_YoY_Pct'] = fin.groupby(['Bank', 'Quarter'])['Revenue_Bn'].pct_change() * 100

fin['Profitability_Rating'] = fin['Profit_Margin_Pct'].apply(
    lambda x: 'Excellent' if x > 25 else ('Good' if x > 15 else ('Fair' if x > 8 else 'Poor'))
)

print(f"    Profitability KPIs calculated for {fin['Bank'].nunique()} banks")

# ── 2. RISK KPIs ──────────────────────────────────────────
print("\n  [2/5] Calculating risk KPIs...")

# NPA trend: is it improving or worsening quarter on quarter?
fin['NPA_QoQ_Change']  = fin.groupby('Bank')['NPA_Ratio_Pct'].diff().round(3)
fin['NPA_Trend']       = fin['NPA_QoQ_Change'].apply(
    lambda x: 'Improving' if pd.notna(x) and x < -0.05
              else ('Worsening' if pd.notna(x) and x > 0.05 else 'Stable')
)

# capital buffer above Basel III minimum (8%)
fin['Capital_Buffer_Pct'] = (fin['Capital_Ratio_Pct'] - 8.0).round(2)
fin['Basel_Status']       = fin['Capital_Ratio_Pct'].apply(
    lambda x: 'Well Capitalised' if x >= 15
              else ('Adequately Capitalised' if x >= 10 else 'Under Pressure')
)

print(f"    Risk KPIs calculated")

# ── 3. STOCK PERFORMANCE KPIs ─────────────────────────────
print("\n  [3/5] Calculating stock performance KPIs...")
stock = pd.read_sql("SELECT * FROM stock_prices", conn, parse_dates=['Date'])
stock = stock.sort_values(['Bank', 'Date'])

# sharpe ratio per bank per year (risk-adjusted return)
# using 2% as risk-free rate
RISK_FREE = 0.02 / 252

sharpe_rows = []
for bank in stock['Bank'].unique():
    bdf = stock[stock['Bank'] == bank].copy()
    for year in bdf['Year'].unique():
        ydf = bdf[bdf['Year'] == year]
        excess = ydf['Daily_Return'] - RISK_FREE
        sharpe = (excess.mean() / excess.std() * np.sqrt(252)) if excess.std() > 0 else 0
        annual_return = ((1 + ydf['Daily_Return']).prod() - 1) * 100
        max_dd = ((ydf['Close'] / ydf['Close'].cummax()) - 1).min() * 100

        sharpe_rows.append({
            'Bank':           bank,
            'Year':           year,
            'Sharpe_Ratio':   round(sharpe, 3),
            'Annual_Return_Pct': round(annual_return, 2),
            'Max_Drawdown_Pct': round(max_dd, 2),
            'Avg_Volatility_Pct': round(ydf['Volatility_30d'].mean() * 100, 2),
        })

sharpe_df = pd.DataFrame(sharpe_rows)
print(f"    Sharpe ratios and annual returns calculated for {len(sharpe_df)} bank-year pairs")

# ── 4. LOAN PORTFOLIO KPIs ────────────────────────────────
print("\n  [4/5] Calculating loan portfolio KPIs...")
loans = pd.read_sql("SELECT * FROM loan_portfolio", conn)

loan_kpi = loans.groupby('Bank').agg(
    Total_Loans        = ('Amount', 'count'),
    Total_Exposure_Mn  = ('Amount', lambda x: round(x.sum() / 1e6, 2)),
    Avg_Loan_Size      = ('Amount', lambda x: round(x.mean(), 0)),
    Avg_Interest_Rate  = ('Interest_Rate', 'mean'),
    NPA_Count          = ('Is_NPA', 'sum'),
    NPA_Rate_Pct       = ('Is_NPA', lambda x: round(x.mean() * 100, 2)),
).reset_index()

loan_kpi['Avg_Interest_Rate'] = loan_kpi['Avg_Interest_Rate'].round(2)
loan_kpi['Portfolio_Health']  = loan_kpi['NPA_Rate_Pct'].apply(
    lambda x: 'Healthy' if x < 1.5 else ('Watch' if x < 3.0 else 'Stressed')
)

# loan type breakdown
loan_type_kpi = loans.groupby(['Bank', 'Loan_Type']).agg(
    Count             = ('Amount', 'count'),
    Exposure_Mn       = ('Amount', lambda x: round(x.sum() / 1e6, 2)),
    NPA_Rate_Pct      = ('Is_NPA', lambda x: round(x.mean() * 100, 2)),
    Avg_Rate          = ('Interest_Rate', lambda x: round(x.mean(), 2)),
).reset_index()

print(f"    Loan KPIs calculated across {loan_kpi['Bank'].nunique()} banks")

# ── 5. BANK SCORECARD (EXECUTIVE SUMMARY) ─────────────────
print("\n  [5/5] Building executive bank scorecard...")

# get latest quarter financials per bank
latest_fin = fin.sort_values('Date').groupby('Bank').last().reset_index()

scorecard = latest_fin[['Bank', 'Revenue_Bn', 'Net_Income_Bn',
                          'Profit_Margin_Pct', 'Cost_to_Income',
                          'NPA_Ratio_Pct', 'ROE_Pct',
                          'Capital_Ratio_Pct', 'NPA_Health',
                          'Basel_Status', 'Profitability_Rating']].copy()

# merge in loan health
scorecard = scorecard.merge(
    loan_kpi[['Bank', 'NPA_Rate_Pct', 'Portfolio_Health', 'Total_Exposure_Mn']],
    on='Bank', suffixes=('_Fin', '_Loan')
)

# overall health score (0-100)
def health_score(row):
    score = 0
    score += 25 if row['Profitability_Rating'] == 'Excellent' else \
             18 if row['Profitability_Rating'] == 'Good' else \
             10 if row['Profitability_Rating'] == 'Fair' else 3
    score += 25 if row['NPA_Health'] == 'Healthy' else \
             15 if row['NPA_Health'] == 'Watch' else 5
    score += 25 if row['Basel_Status'] == 'Well Capitalised' else \
             15 if row['Basel_Status'] == 'Adequately Capitalised' else 5
    score += 25 if row['ROE_Pct'] > 12 else \
             18 if row['ROE_Pct'] > 9 else \
             10 if row['ROE_Pct'] > 6 else 3
    return score

scorecard['Overall_Health_Score'] = scorecard.apply(health_score, axis=1)
scorecard['Overall_Rating'] = scorecard['Overall_Health_Score'].apply(
    lambda x: 'Strong' if x >= 80 else ('Stable' if x >= 60 else ('Weak' if x >= 40 else 'Critical'))
)
scorecard = scorecard.sort_values('Overall_Health_Score', ascending=False)

# ── SAVE ALL KPIs TO DB AND CSV ───────────────────────────
fin.to_sql('kpi_financials', conn, if_exists='replace', index=False)
sharpe_df.to_sql('kpi_stock_performance', conn, if_exists='replace', index=False)
loan_kpi.to_sql('kpi_loan_summary', conn, if_exists='replace', index=False)
loan_type_kpi.to_sql('kpi_loan_by_type', conn, if_exists='replace', index=False)
scorecard.to_sql('bank_scorecard', conn, if_exists='replace', index=False)

fin.to_csv(f'{PROC}/kpi_financials.csv', index=False)
sharpe_df.to_csv(f'{PROC}/kpi_stock_performance.csv', index=False)
loan_kpi.to_csv(f'{PROC}/kpi_loan_summary.csv', index=False)
scorecard.to_csv(f'{PROC}/bank_scorecard.csv', index=False)

# ── PRINT EXECUTIVE SCORECARD ─────────────────────────────
print("\n" + "=" * 60)
print("  EXECUTIVE BANK SCORECARD (Latest Quarter)")
print("=" * 60)
cols = ['Bank', 'Revenue_Bn', 'Profit_Margin_Pct',
        'NPA_Ratio_Pct', 'ROE_Pct', 'Overall_Health_Score', 'Overall_Rating']
print(scorecard[cols].to_string(index=False))

print("\n" + "=" * 60)
print("  Phase 2 KPI Analysis COMPLETE")
print("  Tables added: kpi_financials, kpi_stock_performance,")
print("                kpi_loan_summary, kpi_loan_by_type, bank_scorecard")
print("=" * 60)

conn.close()
