# FinSight — Financial Intelligence Dashboard

> A bank-grade MI analytics platform simulating real-world financial reporting, risk monitoring, and regulatory MI — built for the Barclays Analyst role.

## Project Overview

FinSight is a full-stack financial analytics project covering data engineering, financial modelling, BI dashboards, and regulatory reporting across 5 major global banks (Barclays, HSBC, JPMorgan Chase, Goldman Sachs, Deutsche Bank) over a 6-year period (2019–2024).

## Tech Stack

| Layer | Tools |
|---|---|
| Data Engineering | Python, pandas, numpy |
| Database | SQLite via SQLAlchemy |
| Analysis & Modelling | Python, scikit-learn |
| Visualisation | Power BI, matplotlib, plotly |
| Reporting | openpyxl, reportlab |
| Version Control | Git + GitHub |

## Dataset

- **Stock prices**: 7,830 rows — daily OHLCV + volatility + moving averages
- **Quarterly financials**: 120 rows — revenue, NPA ratio, ROE, capital adequacy
- **Loan portfolio**: 4,000 rows — 5 banks × 800 loans across types, regions, risk bands

## Project Phases

- [x] Phase 1 — Data collection, cleaning & SQL pipeline
- [ ] Phase 2 — Financial KPI analysis & forecasting model
- [ ] Phase 3 — Power BI MI dashboard
- [ ] Phase 4 — Regulatory reporting component
- [ ] Phase 5 — Documentation & presentation

## Folder Structure

```
finsight/
├── data/
│   ├── raw/          # original generated datasets
│   └── processed/    # cleaned, enriched datasets
├── database/         # SQLite database (finsight.db)
├── scripts/          # Python scripts per phase
├── notebooks/        # Jupyter EDA notebooks
├── reports/          # PDF and Excel reports
├── dashboard/        # Power BI files
└── docs/             # documentation assets
```

## Key Metrics Tracked

- NPA Ratio (Non-Performing Assets)
- Cost-to-Income Ratio
- Return on Equity (ROE)
- Capital Adequacy Ratio (Basel III)
- 30-day Annualised Volatility
- Profit Margin

---
*Project by MJ | MCA, CUSAT 2026 | Built for Barclays Analyst Application*
