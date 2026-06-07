# FinSight - Phase 4: Regulatory Report Generator
# Generates a professional Basel III / IFRS-style PDF regulatory report
# Simulates the kind of MI report produced by bank finance & risk teams
# MJ - FinSight Project

import sqlite3
import os
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

print("=" * 60)
print("  FinSight - Phase 4: Regulatory Report Generator")
print("=" * 60)

BASE      = os.path.dirname(__file__) + '/..'
DB_PATH   = BASE + '/database/finsight.db'
REPORT_DIR= BASE + '/reports'
os.makedirs(REPORT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)

# ── LOAD DATA ─────────────────────────────────────────────
scorecard = pd.read_sql("SELECT * FROM bank_scorecard ORDER BY Overall_Health_Score DESC", conn)
fin       = pd.read_sql("""
    SELECT Bank, Year, Quarter, Revenue_Bn, Net_Income_Bn,
           Cost_to_Income, NPA_Ratio_Pct, ROE_Pct,
           Capital_Ratio_Pct, Basel_Status, NPA_Health
    FROM kpi_financials
    WHERE Year = (SELECT MAX(Year) FROM kpi_financials)
    ORDER BY Bank, Quarter
""", conn)
loans     = pd.read_sql("SELECT * FROM kpi_loan_summary ORDER BY Bank", conn)
forecasts = pd.read_sql("""
    SELECT Bank, Period, Forecast_Value, Confidence
    FROM forecasts
    WHERE Metric = 'Revenue_Bn'
    ORDER BY Bank, Forecast_Year, Forecast_Quarter
""", conn)
conn.close()

REPORT_DATE = datetime.now().strftime("%d %B %Y")
PERIOD      = "Q4 2024"

# ── COLOUR PALETTE ────────────────────────────────────────
NAVY      = colors.HexColor('#0D1F3C')
BLUE      = colors.HexColor('#00AEEF')
LIGHT_BLUE= colors.HexColor('#E8F4FD')
WHITE     = colors.white
DARK_GREY = colors.HexColor('#2D3748')
MID_GREY  = colors.HexColor('#718096')
LIGHT_GREY= colors.HexColor('#F7FAFC')
GREEN     = colors.HexColor('#00C853')
AMBER     = colors.HexColor('#FFB300')
RED       = colors.HexColor('#E53E3E')
ALT_ROW   = colors.HexColor('#EBF8FF')

# ── STYLES ────────────────────────────────────────────────
styles = getSampleStyleSheet()

def style(name, **kwargs):
    return ParagraphStyle(name, **kwargs)

S = {
    'cover_title':  style('ct',  fontSize=28, textColor=WHITE,     fontName='Helvetica-Bold',  alignment=TA_CENTER, spaceAfter=8),
    'cover_sub':    style('cs',  fontSize=14, textColor=LIGHT_BLUE,fontName='Helvetica',        alignment=TA_CENTER, spaceAfter=6),
    'cover_detail': style('cd',  fontSize=10, textColor=LIGHT_BLUE,fontName='Helvetica',        alignment=TA_CENTER, spaceAfter=4),
    'section':      style('sh',  fontSize=14, textColor=NAVY,      fontName='Helvetica-Bold',  spaceBefore=16, spaceAfter=6),
    'subsection':   style('ssh', fontSize=11, textColor=DARK_GREY, fontName='Helvetica-Bold',  spaceBefore=10, spaceAfter=4),
    'body':         style('bd',  fontSize=9,  textColor=DARK_GREY, fontName='Helvetica',       spaceAfter=4,   leading=14),
    'small':        style('sm',  fontSize=8,  textColor=MID_GREY,  fontName='Helvetica',       spaceAfter=2),
    'footer':       style('ft',  fontSize=8,  textColor=MID_GREY,  fontName='Helvetica',       alignment=TA_CENTER),
    'right':        style('rt',  fontSize=9,  textColor=DARK_GREY, fontName='Helvetica',       alignment=TA_RIGHT),
    'highlight':    style('hl',  fontSize=9,  textColor=NAVY,      fontName='Helvetica-Bold',  spaceAfter=4),
}

def hr(color=BLUE, thickness=1):
    return HRFlowable(width='100%', thickness=thickness, color=color, spaceAfter=6, spaceBefore=2)

def section_header(title, subtitle=None):
    elems = []
    elems.append(Spacer(1, 0.3*cm))
    elems.append(Paragraph(title, S['section']))
    elems.append(hr(BLUE, 1.5))
    if subtitle:
        elems.append(Paragraph(subtitle, S['body']))
    return elems

def health_color(val, metric='npa'):
    if metric == 'npa':
        return GREEN if val < 2 else (AMBER if val < 4 else RED)
    if metric == 'capital':
        return GREEN if val >= 15 else (AMBER if val >= 10 else RED)
    if metric == 'roe':
        return GREEN if val >= 12 else (AMBER if val >= 8 else RED)
    return DARK_GREY

def status_color(status):
    mapping = {
        'Strong': GREEN, 'Healthy': GREEN, 'Well Capitalised': GREEN,
        'Stable': BLUE,  'Watch': AMBER,   'Adequately Capitalised': AMBER,
        'Weak': RED,     'Stressed': RED,  'Under Pressure': RED,
        'Improving': GREEN, 'Worsening': RED, 'Critical': RED,
    }
    return mapping.get(status, DARK_GREY)

# ── TABLE STYLE HELPER ────────────────────────────────────
def base_table_style(header_color=NAVY, alt=True):
    cmds = [
        ('BACKGROUND',   (0,0), (-1,0), header_color),
        ('TEXTCOLOR',    (0,0), (-1,0), WHITE),
        ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,0), 9),
        ('ALIGN',        (0,0), (-1,-1),'CENTER'),
        ('ALIGN',        (0,1), (0,-1), 'LEFT'),
        ('FONTNAME',     (0,1), (-1,-1),'Helvetica'),
        ('FONTSIZE',     (0,1), (-1,-1), 8.5),
        ('ROWBACKGROUND',(0,1), (-1,-1), [WHITE, ALT_ROW] if alt else [WHITE]),
        ('GRID',         (0,0), (-1,-1), 0.3, colors.HexColor('#CBD5E0')),
        ('TOPPADDING',   (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0), (-1,-1), 5),
        ('LEFTPADDING',  (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW',    (0,0), (-1,0),  1.2, BLUE),
        ('ROWBACKGROUND',(0,0), (-1,0),  header_color),
    ]
    return cmds

# ── BUILD PDF ─────────────────────────────────────────────
output_path = os.path.join(REPORT_DIR, f'FinSight_Regulatory_Report_{datetime.now().strftime("%Y%m%d")}.pdf')

doc = SimpleDocTemplate(
    output_path,
    pagesize=A4,
    rightMargin=1.8*cm, leftMargin=1.8*cm,
    topMargin=1.5*cm,   bottomMargin=1.5*cm,
)

story = []
W = A4[0] - 3.6*cm  # usable width

# ══════════════════════════════════════════════════════════
# PAGE 1 — COVER
# ══════════════════════════════════════════════════════════
cover_data = [['']]
cover_table = Table(cover_data, colWidths=[W], rowHeights=[22*cm])
cover_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), NAVY),
    ('ROUNDEDCORNERS', [8]),
]))
story.append(cover_table)

# overlay text on cover using a nested table
story.pop()  # remove blank table
cover_content = [
    Spacer(1, 3.5*cm),
    Paragraph("FINSIGHT", style('logo', fontSize=11, textColor=BLUE, fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=2)),
    Paragraph("Financial Intelligence Dashboard", S['cover_title']),
    Spacer(1, 0.4*cm),
    HRFlowable(width='40%', thickness=2, color=BLUE, hAlign='CENTER', spaceAfter=16, spaceBefore=8),
    Paragraph("REGULATORY &amp; MANAGEMENT INFORMATION REPORT", S['cover_sub']),
    Spacer(1, 0.6*cm),
    Paragraph(f"Reporting Period: {PERIOD}", S['cover_detail']),
    Paragraph(f"Report Date: {REPORT_DATE}", S['cover_detail']),
    Paragraph("Classification: INTERNAL — CONFIDENTIAL", S['cover_detail']),
    Spacer(1, 2*cm),
    Paragraph("Prepared by: FinSight Analytics Platform", S['cover_detail']),
    Paragraph("Coverage: Barclays · HSBC · JPMorgan Chase · Goldman Sachs · Deutsche Bank", S['cover_detail']),
    Spacer(1, 3*cm),
    Paragraph("This report contains forward-looking statements and financial metrics prepared in accordance with Basel III capital framework and IFRS 9 provisioning standards. For internal use only.", 
              style('disc', fontSize=7.5, textColor=MID_GREY, fontName='Helvetica', alignment=TA_CENTER, leading=11)),
]

cover_bg = Table([['']], colWidths=[W], rowHeights=[24*cm])
cover_bg.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), NAVY)]))
story.append(cover_bg)
story.pop()

# build cover as a blue background table with text inside
inner = []
for elem in cover_content:
    inner.append([elem])
cover_frame = Table(inner, colWidths=[W])
cover_frame.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), NAVY),
    ('LEFTPADDING',  (0,0), (-1,-1), 30),
    ('RIGHTPADDING', (0,0), (-1,-1), 30),
    ('TOPPADDING',   (0,0), (-1,-1), 0),
    ('BOTTOMPADDING',(0,0), (-1,-1), 0),
]))
story.append(cover_frame)
story.append(PageBreak())

# ══════════════════════════════════════════════════════════
# PAGE 2 — EXECUTIVE SUMMARY
# ══════════════════════════════════════════════════════════
story += section_header("1. Executive Summary",
    "This report presents a comprehensive analysis of financial performance, risk metrics, "
    "and capital adequacy across five major global banking institutions for the reporting period ending Q4 2024. "
    "Key findings are summarised below.")

# KPI summary cards as a table
avg_npa     = scorecard['NPA_Ratio_Pct'].mean()
avg_capital = scorecard['Capital_Ratio_Pct'].mean()
avg_roe     = scorecard['ROE_Pct'].mean()
avg_health  = scorecard['Overall_Health_Score'].mean()
strong_count= len(scorecard[scorecard['Overall_Rating']=='Strong'])
weak_count  = len(scorecard[scorecard['Overall_Rating'].isin(['Weak','Critical'])])

kpi_data = [
    ['METRIC', 'VALUE', 'BENCHMARK', 'STATUS'],
    ['Average NPA Ratio',         f"{avg_npa:.2f}%",     '< 3.0%',   'Watch' if avg_npa >= 3 else 'Healthy'],
    ['Average Capital Ratio',     f"{avg_capital:.2f}%", '≥ 10.5%',  'Adequate' if avg_capital >= 10.5 else 'Below'],
    ['Average ROE',               f"{avg_roe:.2f}%",     '≥ 10.0%',  'Adequate' if avg_roe >= 10 else 'Below'],
    ['Portfolio Health Score',    f"{avg_health:.1f}/100","≥ 70",     'Strong' if avg_health >= 70 else 'Watch'],
    ['Banks Rated Strong',        f"{strong_count} of 5", '≥ 3 of 5','Good' if strong_count >= 3 else 'Monitor'],
    ['Banks Under Stress',        f"{weak_count} of 5",  '0 of 5',   'Elevated' if weak_count > 0 else 'Clear'],
]

kpi_table = Table(kpi_data, colWidths=[W*0.35, W*0.18, W*0.22, W*0.25])
cmds = base_table_style(NAVY)
# colour status column
for i, row in enumerate(kpi_data[1:], 1):
    status = row[3]
    c = status_color(status)
    cmds += [
        ('TEXTCOLOR', (3,i), (3,i), c),
        ('FONTNAME',  (3,i), (3,i), 'Helvetica-Bold'),
    ]
kpi_table.setStyle(TableStyle(cmds))
story.append(kpi_table)
story.append(Spacer(1, 0.4*cm))

story.append(Paragraph(
    f"<b>Key Observations:</b> As of {PERIOD}, the consolidated banking portfolio demonstrates "
    f"broadly stable financial health with an average portfolio health score of <b>{avg_health:.0f}/100</b>. "
    f"JPMorgan Chase and Goldman Sachs maintain <b>Strong</b> ratings driven by superior capital buffers "
    f"and low NPA ratios. Deutsche Bank remains the highest-risk institution with an NPA ratio exceeding "
    f"4.0% and Stressed NPA health classification, warranting heightened supervisory attention. "
    f"HSBC is rated <b>Weak</b> due to elevated cost-to-income ratios. "
    f"All five institutions maintain capital ratios above the Basel III minimum threshold of 8%.",
    S['body']))

story.append(PageBreak())

# ══════════════════════════════════════════════════════════
# PAGE 3 — BANK SCORECARD
# ══════════════════════════════════════════════════════════
story += section_header("2. Institution Scorecard",
    "The following scorecard presents consolidated financial health metrics for each institution "
    "as at the end of the reporting period.")

sc_cols = ['Bank','Revenue_Bn','Profit_Margin_Pct','NPA_Ratio_Pct',
           'ROE_Pct','Capital_Ratio_Pct','NPA_Health','Basel_Status','Overall_Rating','Overall_Health_Score']
sc_data = [['Institution','Revenue\n(Bn)','Profit\nMargin %','NPA\nRatio %',
            'ROE %','Capital\nRatio %','NPA\nHealth','Basel\nStatus','Overall\nRating','Score']]

for _, row in scorecard.iterrows():
    sc_data.append([
        row['Bank'],
        f"{row['Revenue_Bn']:.2f}",
        f"{row['Profit_Margin_Pct']:.1f}%",
        f"{row['NPA_Ratio_Pct']:.2f}%",
        f"{row['ROE_Pct']:.1f}%",
        f"{row['Capital_Ratio_Pct']:.1f}%",
        row['NPA_Health'],
        row['Basel_Status'],
        row['Overall_Rating'],
        f"{row['Overall_Health_Score']:.0f}",
    ])

sc_table = Table(sc_data, colWidths=[W*0.16,W*0.08,W*0.09,W*0.08,
                                      W*0.07,W*0.09,W*0.09,W*0.14,W*0.1,W*0.1])
cmds = base_table_style(NAVY)
for i, row in enumerate(scorecard.itertuples(), 1):
    npa_c = health_color(row.NPA_Ratio_Pct, 'npa')
    cap_c = health_color(row.Capital_Ratio_Pct, 'capital')
    roe_c = health_color(row.ROE_Pct, 'roe')
    rat_c = status_color(row.Overall_Rating)
    cmds += [
        ('TEXTCOLOR', (3,i),(3,i), npa_c),  ('FONTNAME',(3,i),(3,i),'Helvetica-Bold'),
        ('TEXTCOLOR', (5,i),(5,i), cap_c),  ('FONTNAME',(5,i),(5,i),'Helvetica-Bold'),
        ('TEXTCOLOR', (4,i),(4,i), roe_c),  ('FONTNAME',(4,i),(4,i),'Helvetica-Bold'),
        ('TEXTCOLOR', (8,i),(8,i), rat_c),  ('FONTNAME',(8,i),(8,i),'Helvetica-Bold'),
    ]
sc_table.setStyle(TableStyle(cmds))
story.append(sc_table)
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "Note: NPA Ratio colour coding: Green < 2.0%, Amber 2.0–4.0%, Red > 4.0%. "
    "Capital Ratio: Green ≥ 15%, Amber 10–15%, Red < 10%. "
    "Score out of 100 based on composite weighted metric across profitability, asset quality, "
    "capital adequacy, and return on equity.",
    S['small']))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════
# PAGE 4 — CAPITAL ADEQUACY (BASEL III)
# ══════════════════════════════════════════════════════════
story += section_header("3. Capital Adequacy — Basel III Framework",
    "Under the Basel III framework, institutions are required to maintain a minimum Common Equity "
    "Tier 1 (CET1) ratio of 4.5%, a Tier 1 capital ratio of 6.0%, and a total capital ratio of 8.0%, "
    "plus a capital conservation buffer of 2.5%. The table below presents each institution's "
    "compliance status as of the reporting period.")

cap_data = [['Institution','Capital\nRatio %','Regulatory\nMinimum','Capital\nBuffer %',
             'Basel III\nStatus','Assessment']]
for _, row in scorecard.iterrows():
    cap_ratio = row['Capital_Ratio_Pct']
    buffer    = cap_ratio - 10.5
    status    = row['Basel_Status']
    assess    = ('Well above minimum — strong capital position' if cap_ratio >= 15
                 else 'Above minimum — adequate buffer maintained'  if cap_ratio >= 12
                 else 'Meets minimum — limited buffer, monitor closely')
    cap_data.append([
        row['Bank'],
        f"{cap_ratio:.1f}%",
        "10.5%",
        f"{buffer:+.1f}%",
        status,
        assess,
    ])

cap_table = Table(cap_data, colWidths=[W*0.16,W*0.10,W*0.11,W*0.10,W*0.18,W*0.35])
cmds = base_table_style(colors.HexColor('#1A365D'))
for i, row in enumerate(scorecard.itertuples(), 1):
    c = health_color(row.Capital_Ratio_Pct, 'capital')
    cmds += [('TEXTCOLOR',(1,i),(1,i),c), ('FONTNAME',(1,i),(1,i),'Helvetica-Bold')]
    s_c = status_color(row.Basel_Status)
    cmds += [('TEXTCOLOR',(4,i),(4,i),s_c), ('FONTNAME',(4,i),(4,i),'Helvetica-Bold')]
    buf = row.Capital_Ratio_Pct - 10.5
    buf_c = GREEN if buf >= 4 else (AMBER if buf >= 0 else RED)
    cmds += [('TEXTCOLOR',(3,i),(3,i),buf_c), ('FONTNAME',(3,i),(3,i),'Helvetica-Bold')]
cap_table.setStyle(TableStyle(cmds))
story.append(cap_table)
story.append(Spacer(1, 0.5*cm))
story += section_header("4. Asset Quality — NPA Analysis",
    "Non-Performing Assets (NPAs) represent loans where the borrower has defaulted or is "
    "significantly past due. A rising NPA ratio is an early warning indicator of credit stress "
    "and potential provisioning requirements under IFRS 9.")

npa_data = [['Institution','Avg NPA\nRatio %','NPA\nHealth','NPA\nTrend',
             'Loan\nExposure (Mn)','NPA\nLoans','Portfolio\nHealth']]
for _, row in scorecard.iterrows():
    loan_row = loans[loans['Bank']==row['Bank']].iloc[0] if len(loans[loans['Bank']==row['Bank']]) > 0 else None
    npa_data.append([
        row['Bank'],
        f"{row['NPA_Ratio_Pct']:.2f}%",
        row['NPA_Health'],
        '—',
        f"{loan_row['Total_Exposure_Mn']:.1f}" if loan_row is not None else '—',
        f"{int(loan_row['NPA_Count'])}"         if loan_row is not None else '—',
        row.get('Portfolio_Health', '—') if isinstance(row, dict) else '—',
    ])

npa_table = Table(npa_data, colWidths=[W*0.16,W*0.10,W*0.11,W*0.10,W*0.16,W*0.10,W*0.27])
cmds = base_table_style(colors.HexColor('#1A365D'))
for i, row in enumerate(scorecard.itertuples(), 1):
    c = health_color(row.NPA_Ratio_Pct, 'npa')
    cmds += [('TEXTCOLOR',(1,i),(1,i),c), ('FONTNAME',(1,i),(1,i),'Helvetica-Bold')]
    h_c = status_color(row.NPA_Health)
    cmds += [('TEXTCOLOR',(2,i),(2,i),h_c), ('FONTNAME',(2,i),(2,i),'Helvetica-Bold')]
npa_table.setStyle(TableStyle(cmds))
story.append(npa_table)
story.append(PageBreak())

# ══════════════════════════════════════════════════════════
# PAGE 5 — REVENUE FORECAST
# ══════════════════════════════════════════════════════════
story += section_header("5. Revenue Outlook — Forward Guidance",
    "The following revenue forecasts are generated using a polynomial regression model "
    "calibrated on 24 quarters of historical data (2019–2024). Forecast intervals represent "
    "±1 standard deviation confidence bands.")

fcast_pivot = forecasts.pivot(index='Bank', columns='Period', values='Forecast_Value').round(2)
fcast_pivot = fcast_pivot.reset_index()
periods     = [c for c in fcast_pivot.columns if c != 'Bank']
fcast_data  = [['Institution'] + periods + ['Confidence']]
for _, row in fcast_pivot.iterrows():
    conf_row = forecasts[forecasts['Bank']==row['Bank']].iloc[0]
    conf     = conf_row['Confidence'] if not conf_row.empty else '—'
    fcast_data.append([row['Bank']] + [f"{row[p]:.2f}" for p in periods] + [conf])

col_w = [W*0.18] + [W*0.13]*len(periods) + [W*0.12]
fcast_table = Table(fcast_data, colWidths=col_w)
cmds = base_table_style(colors.HexColor('#1A365D'))
for i in range(1, len(fcast_data)):
    conf = fcast_data[i][-1]
    c    = GREEN if conf == 'High' else (AMBER if conf == 'Medium' else RED)
    cmds+= [('TEXTCOLOR',(-1,i),(-1,i),c), ('FONTNAME',(-1,i),(-1,i),'Helvetica-Bold')]
fcast_table.setStyle(TableStyle(cmds))
story.append(fcast_table)
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "All revenue figures in USD billions. Forecast accuracy assessed using Mean Absolute "
    "Percentage Error (MAPE): High Confidence = MAPE < 5%, Medium = MAPE 5–10%, Low = MAPE > 10%. "
    "Forecasts are indicative only and subject to macroeconomic conditions.",
    S['small']))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════
# PAGE 6 — LOAN PORTFOLIO & DISCLAIMER
# ══════════════════════════════════════════════════════════
story += section_header("6. Loan Portfolio Summary",
    "The consolidated loan portfolio across all five institutions comprises 4,000 facilities "
    "spanning five product categories and five geographic regions.")

loan_data = [['Institution','Total\nLoans','Exposure\n(Mn)','Avg Loan\nSize','Avg Rate %',
              'NPA\nCount','NPA\nRate %','Portfolio\nHealth']]
for _, row in loans.iterrows():
    loan_data.append([
        row['Bank'],
        f"{int(row['Total_Loans']):,}",
        f"{row['Total_Exposure_Mn']:.1f}",
        f"{row['Avg_Loan_Size']:,.0f}",
        f"{row['Avg_Interest_Rate']:.2f}%",
        f"{int(row['NPA_Count'])}",
        f"{row['NPA_Rate_Pct']:.2f}%",
        row['Portfolio_Health'],
    ])

loan_table = Table(loan_data, colWidths=[W*0.16,W*0.08,W*0.10,W*0.11,W*0.09,W*0.08,W*0.09,W*0.29])
cmds = base_table_style(colors.HexColor('#1A365D'))
for i, row in enumerate(loans.itertuples(), 1):
    c   = health_color(row.NPA_Rate_Pct, 'npa')
    h_c = status_color(row.Portfolio_Health)
    cmds += [
        ('TEXTCOLOR',(6,i),(6,i),c),   ('FONTNAME',(6,i),(6,i),'Helvetica-Bold'),
        ('TEXTCOLOR',(7,i),(7,i),h_c), ('FONTNAME',(7,i),(7,i),'Helvetica-Bold'),
    ]
loan_table.setStyle(TableStyle(cmds))
story.append(loan_table)
story.append(Spacer(1, 1*cm))

# disclaimer box
disc_data = [[Paragraph(
    "<b>DISCLAIMER &amp; REGULATORY NOTICE</b><br/><br/>"
    "This report has been prepared by the FinSight Analytics Platform for internal management "
    "information purposes only. The financial data presented is based on synthetic datasets "
    "generated using statistical modelling techniques including Geometric Brownian Motion for "
    "market prices and polynomial regression for forward projections.<br/><br/>"
    "This report does not constitute financial advice, investment guidance, or a formal regulatory "
    "submission. References to Basel III, IFRS 9, and other regulatory frameworks are included "
    "for illustrative and educational purposes only. No reliance should be placed on this report "
    "for regulatory compliance decisions.<br/><br/>"
    f"Report generated: {REPORT_DATE} | FinSight v1.0 | Classification: INTERNAL ONLY",
    style('disc2', fontSize=8, textColor=DARK_GREY, fontName='Helvetica', leading=12))
]]
disc_table = Table(disc_data, colWidths=[W])
disc_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0),(-1,-1), LIGHT_GREY),
    ('BOX',           (0,0),(-1,-1), 0.8, MID_GREY),
    ('LEFTPADDING',   (0,0),(-1,-1), 12),
    ('RIGHTPADDING',  (0,0),(-1,-1), 12),
    ('TOPPADDING',    (0,0),(-1,-1), 10),
    ('BOTTOMPADDING', (0,0),(-1,-1), 10),
]))
story.append(disc_table)

# ── BUILD ─────────────────────────────────────────────────
doc.build(story)

print(f"\n  Report generated successfully!")
print(f"  Pages: 6")
print(f"  File: {os.path.basename(output_path)}")
print(f"  Location: reports/")
print("=" * 60)
