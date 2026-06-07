# FinSight — Financial Intelligence Dashboard

> A bank-grade Management Information (MI) analytics platform covering financial performance, risk monitoring, capital adequacy, and revenue forecasting across five major global banks — built using Python, SQL, Power BI, and automated regulatory reporting.

---

## Project Overview

FinSight simulates the end-to-end analytics workflow of a real bank finance and risk team. It ingests financial data, computes regulatory KPIs, surfaces insights through an interactive BI dashboard, and auto-generates a Basel III / IFRS 9-aligned regulatory report — all from a single integrated pipeline.

| Dimension | Detail |
|---|---|
| **Banks covered** | Barclays · HSBC · JPMorgan Chase · Goldman Sachs · Deutsche Bank |
| **Time period** | 2019–2024 (6 years, including COVID stress period) |
| **Data volume** | 7,830 stock price rows · 120 quarterly financials · 4,000 loan records |
| **Forecasting** | 4-quarter revenue and NPA outlook per bank |
| **Report output** | 5-page Basel III / IFRS 9-aligned regulatory PDF |

---

## Key Features

- **Financial KPI Engine** — NPA ratio trending, Basel III capital buffer calculations, cost-to-income efficiency scoring, Sharpe ratio and maximum drawdown per bank per year
- **Forecasting Model** — Polynomial regression (degree 2) calibrated on 24 quarters of history; MAPE < 5% on revenue forecasts (High Confidence)
- **Power BI Dashboard** — 4-page interactive MI dashboard with drill-downs, cross-filtering, and a bank slicer across Executive Overview, Financial Performance, Risk & NPA Monitor, and Loan Portfolio pages
- **Regulatory Report Generator** — Automated Python script producing a professional PDF report simulating a Basel III / IFRS 9 management information submission
- **SQL Database** — SQLite backend with 3 core tables, 5 KPI views, and a bank summary analytical view

---

## Tech Stack

| Layer | Tools |
|---|---|
| Data Engineering | Python 3.13, pandas, numpy |
| Database | SQLite via SQLAlchemy |
| Analysis & Modelling | scikit-learn (Polynomial Regression), numpy |
| Visualisation | Power BI Desktop |
| Reporting | reportlab (PDF), openpyxl |
| Version Control | Git + GitHub |

---

## Project Structure

```
finsight/
├── data/
│   ├── raw/                    # Source datasets (stock, financials, loans)
│   └── processed/              # Cleaned & enriched datasets with KPIs
├── database/
│   └── finsight.db             # SQLite database (3 tables, 5 KPI tables, 1 view)
├── scripts/
│   ├── 01_data_collection.py   # Synthetic data generation (GBM, financial modelling)
│   ├── 02_data_cleaning.py     # Data cleaning & SQL pipeline
│   ├── 03_eda.py               # Exploratory data analysis & validation
│   ├── 04_kpi_analysis.py      # KPI calculations (NPA, Basel III, Sharpe, ROE)
│   ├── 05_forecasting.py       # Revenue & NPA forecasting model
│   └── 06_regulatory_report.py # Automated regulatory PDF report generator
├── dashboard/
│   └── finsight.pbix           # Power BI dashboard (4 pages)
├── reports/
│   └── FinSight_Regulatory_Report.pdf
├── docs/
├── notebooks/
└── README.md
```

---

## Dashboard Pages

| Page | Visuals | Key Insight |
|---|---|---|
| Executive Overview | Scorecard table, health score bar chart, KPI cards, rating donut, bank slicer | JPMorgan leads at 93/100; HSBC weakest at 58/100 |
| Financial Performance | Revenue trend (2019–2024), profit margin, cost-to-income, revenue forecast | All banks show post-COVID recovery; JPMorgan revenue 6.6× Barclays |
| Risk & NPA Monitor | NPA trend over time, Basel III capital table, NPA by loan type, NPA by region | Deutsche Bank NPA peaked at ~5.5% during COVID stress |
| Loan Portfolio | Exposure by bank, loan type distribution, regional breakdown, status chart | Business loans dominate at 69% of total portfolio |

---

## Regulatory KPIs Tracked

- **NPA Ratio** — Non-Performing Asset ratio with Healthy / Watch / Stressed classification
- **Capital Adequacy Ratio** — vs Basel III minimum (10.5% including conservation buffer)
- **Capital Buffer** — excess above regulatory minimum, per institution
- **Cost-to-Income Ratio** — operational efficiency metric
- **Return on Equity (ROE)** — profitability relative to shareholder equity
- **Sharpe Ratio** — risk-adjusted return per bank per year
- **Maximum Drawdown** — peak-to-trough price decline per year
- **30-day Annualised Volatility** — rolling market risk indicator

---

## How to Run

```bash
# 1. Clone the repository
git clone https://github.com/Manjith-07/finsight.git
cd finsight

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install pandas numpy matplotlib seaborn sqlalchemy openpyxl scikit-learn plotly reportlab

# 4. Run the full pipeline in order
python scripts/01_data_collection.py
python scripts/02_data_cleaning.py
python scripts/03_eda.py
python scripts/04_kpi_analysis.py
python scripts/05_forecasting.py
python scripts/06_regulatory_report.py

# 5. Open the dashboard
# Launch Power BI Desktop and open dashboard/finsight.pbix
```

---

## Results Summary

| Bank | Health Score | NPA Ratio | Capital Ratio | Rating |
|---|---|---|---|---|
| JPMorgan Chase | 93/100 | 1.51% | 15.7% | Strong |
| Goldman Sachs | 85/100 | 1.77% | 15.1% | Strong |
| Barclays | 73/100 | 3.03% | 13.8% | Stable |
| Deutsche Bank | 70/100 | 4.91% | 13.5% | Stable |
| HSBC | 58/100 | 2.68% | 13.3% | Weak |

---

## Phases Completed

- [x] Phase 1 — Data generation, cleaning & SQL pipeline
- [x] Phase 2 — Financial KPI analysis & forecasting model
- [x] Phase 3 — Power BI MI dashboard (4 pages)
- [x] Phase 4 — Automated regulatory PDF report (Basel III / IFRS 9 style)
- [x] Phase 5 — Documentation & project packaging

---

*MCA, Cochin University of Science and Technology (CUSAT) · 2026*
