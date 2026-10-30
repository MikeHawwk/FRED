import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fredapi import Fred
import yfinance as yf
import datetime
import calendar

# ==============================================================================
# 1. PAGE CONFIG & HIGH-CONTRAST DARK STYLING
# ==============================================================================
st.set_page_config(
    page_title="Macroeconomic & Financial Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"  # Opened sidebar by default
)

st.markdown("""
<style>
    /* Hide top header bar & reduce top whitespace */
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 98% !important;
    }
    
    .stApp {
        background-color: #0b0f19 !important;
        color: #f8fafc !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.9rem !important;
        font-weight: 800 !important;
    }

    .analysis-box {
        background-color: #161e2e;
        border: 1px solid #2a364f;
        border-radius: 8px;
        padding: 10px 12px;
        margin-top: 8px;
        font-size: 0.84rem;
        line-height: 1.45;
        color: #e2e8f0;
    }
    .analysis-title {
        color: #38bdf8;
        font-weight: 700;
        font-size: 0.88rem;
        margin-bottom: 4px;
    }
    
    div[data-testid="column"] {
        background-color: #111827;
        border: 1px solid #1f2937;
        padding: 14px;
        border-radius: 10px;
    }

    /* Industry Return Ticker Tape Styling */
    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 6px 0;
        margin-bottom: 6px;
        white-space: nowrap;
    }
    .ticker-move {
        display: inline-block;
        white-space: nowrap;
        padding-left: 100%;
        animation: ticker 35s linear infinite;
    }
    @keyframes ticker {
        0% { transform: translate3d(0, 0, 0); }
        100% { transform: translate3d(-100%, 0, 0); }
    }
    .ticker-item {
        display: inline-block;
        padding: 0 18px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .pos { color: #34d399; }
    .neg { color: #f87171; }

    /* Calendar Styling */
    .cal-table {
        width: 100%;
        border-collapse: collapse;
        text-align: center;
        font-size: 0.85rem;
        margin-top: 5px;
    }
    .cal-table th {
        color: #94a3b8;
        padding: 4px;
        font-weight: 600;
    }
    .cal-table td {
        padding: 6px 2px;
        border: 1px solid #1e293b;
        border-radius: 4px;
    }
    .cal-today {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        font-weight: bold;
        border: 2px solid #38bdf8 !important;
    }
    .cal-event-jobs { background-color: #065f46; color: #34d399; font-weight: bold; }
    .cal-event-cpi { background-color: #831843; color: #f472b6; font-weight: bold; }
    .cal-event-fomc { background-color: #581c87; color: #c084fc; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. API KEY SETUP & SESSION STATE
# ==============================================================================
API_KEY = "19d76f858cd1c2d6c01a6f10a2825a24"

if "FRED_API_KEY" in st.secrets and st.secrets["FRED_API_KEY"]:
    ACTIVE_API_KEY = st.secrets["FRED_API_KEY"]
else:
    ACTIVE_API_KEY = API_KEY

now_date = datetime.datetime.now()
if "cal_year" not in st.session_state:
    st.session_state.cal_year = now_date.year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = now_date.month

# ==============================================================================
# 3. HELPER FUNCTIONS
# ==============================================================================
@st.cache_data(ttl=3600)
def fetch_fred_series(series_id: str, start_date: str = "2018-01-01") -> pd.Series:
    try:
        fred = Fred(api_key=ACTIVE_API_KEY)
        data = fred.get_series(series_id, observation_start=start_date)
        return data.dropna()
    except Exception as e:
        st.error(f"Error fetching {series_id}: {e}")
        return pd.Series(dtype=float)

@st.cache_data(ttl=3600)
def get_live_sector_returns():
    """Fetches real-time YTD performance for S&P 500 Sector ETFs via Yahoo Finance."""
    sectors = {
        "S&P 500 (SPY)": "SPY",
        "Tech (XLK)": "XLK",
        "Comm Services (XLC)": "XLC",
        "Utilities (XLU)": "XLU",
        "Financials (XLF)": "XLF",
        "Discretionary (XLY)": "XLY",
        "Industrials (XLI)": "XLI",
        "Healthcare (XLV)": "XLV",
        "Staples (XLP)": "XLP",
        "Real Estate (XLRE)": "XLRE",
        "Energy (XLE)": "XLE",
    }
    results = []
    try:
        curr_year = datetime.datetime.now().year
        data = yf.download(list(sectors.values()), start=f"{curr_year}-01-01", progress=False)
        close_data = data['Close'] if 'Close' in data.columns else data
            
        for name, ticker in sectors.items():
            if ticker in close_data.columns:
                series = close_data[ticker].dropna()
                if len(series) >= 2:
                    start_price = series.iloc[0]
                    curr_price = series.iloc[-1]
                    ytd_ret = ((curr_price - start_price) / start_price) * 100
                    results.append((name, f"{ytd_ret:+.1f}% YTD", ytd_ret >= 0))
    except Exception:
        pass
    
    if not results:
        results = [("Market Data Syncing...", "0.0%", True)]
    return results

@st.cache_data(ttl=900)
def get_live_daily_returns():
    """Fetches Today's 1-Day performance for major market indices and sector ETFs."""
    items = {
        "S&P 500": "^GSPC",
        "Nasdaq": "^IXIC",
        "Dow Jones": "^DJI",
        "Russell 2000": "^RUT",
        "VIX Volatility": "^VIX",
        "Tech (XLK)": "XLK",
        "Comm Services (XLC)": "XLC",
        "Financials (XLF)": "XLF",
        "Discretionary (XLY)": "XLY",
        "Industrials (XLI)": "XLI",
        "Healthcare (XLV)": "XLV",
        "Staples (XLP)": "XLP",
        "Energy (XLE)": "XLE",
        "Utilities (XLU)": "XLU",
        "Real Estate (XLRE)": "XLRE"
    }
    results = []
    try:
        data = yf.download(list(items.values()), period="5d", progress=False)
        close_data = data['Close'] if 'Close' in data.columns else data
        
        for name, ticker in items.items():
            if ticker in close_data.columns:
                series = close_data[ticker].dropna()
                if len(series) >= 2:
                    prev_close = series.iloc[-2]
                    curr_close = series.iloc[-1]
                    daily_change = ((curr_close - prev_close) / prev_close) * 100
                    results.append((name, f"{daily_change:+.2f}% Today", daily_change >= 0))
    except Exception:
        pass
        
    if not results:
        results = [("Market Data Syncing...", "0.0%", True)]
    return results

def create_dark_chart(df: pd.DataFrame, y_col: str, title: str, color: str = "#00f2fe", hlines: list = None) -> go.Figure:
    fig = px.line(df, x=df.index, y=y_col)
    fig.update_traces(line=dict(color=color, width=2.5))
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.8)",
        margin=dict(l=10, r=10, t=30, b=10),
        height=200,
        title=dict(text=title, font=dict(color="#ffffff", size=13, weight="bold")),
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color="#cbd5e1", size=10), title=""),
        yaxis=dict(showgrid=True, gridcolor="#1f2937", zeroline=False, tickfont=dict(color="#cbd5e1", size=10), title=""),
        font=dict(color="#f8fafc", size=11)
    )
    
    if hlines:
        for line in hlines:
            fig.add_hline(
                y=line.get('value'), 
                line_dash=line.get('dash', 'dash'), 
                line_color=line.get('color', '#ff4b4b'),
                annotation_text=line.get('text', ''),
                annotation_position="top right",
                annotation_font=dict(color=line.get('color', '#ff4b4b'), size=10)
            )
            
    return fig

def render_dual_ticker_tapes():
    """Renders two stacked ticker tapes: YTD Sector Returns and Today's Market Returns."""
    # Tape 1: YTD Returns
    ytd_sectors = get_live_sector_returns()
    ytd_html = ""
    for name, ret, is_pos in ytd_sectors:
        color_cls = "pos" if is_pos else "neg"
        ytd_html += f'<div class="ticker-item"><span>{name}:</span> <span class="{color_cls}">{ret}</span></div> • '
    
    # Tape 2: Today's Daily Returns
    daily_items = get_live_daily_returns()
    daily_html = ""
    for name, ret, is_pos in daily_items:
        color_cls = "pos" if is_pos else "neg"
        daily_html += f'<div class="ticker-item"><span>{name}:</span> <span class="{color_cls}">{ret}</span></div> • '
    
    return f"""
    <div style="margin-bottom: 6px;">
        <div style="font-size: 0.78rem; font-weight: bold; color: #38bdf8; margin-bottom: 2px;">📈 YTD SECTOR RETURNS</div>
        <div class="ticker-wrap"><div class="ticker-move">{ytd_html} {ytd_html}</div></div>
    </div>
    <div style="margin-bottom: 18px;">
        <div style="font-size: 0.78rem; font-weight: bold; color: #34d399; margin-bottom: 2px;">⚡ TODAY'S MARKET & SECTOR RETURNS (1-DAY)</div>
        <div class="ticker-wrap"><div class="ticker-move">{daily_html} {daily_html}</div></div>
    </div>
    """

def render_monthly_calendar(year, month):
    today = datetime.datetime.now()
    month_name = calendar.month_name[month]
    
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)
    
    fomc_dates_2026 = {
        (2026, 1): [27, 28], (2026, 3): [17, 18], (2026, 4): [28, 29],
        (2026, 6): [16, 17], (2026, 7): [28, 29], (2026, 9): [15, 16],
        (2026, 10): [27, 28], (2026, 12): [15, 16],
    }
    
    first_friday = [w[5] for w in month_days if w[5] != 0][0]
    cpi_day = [w[3] for w in month_days if w[3] != 0][1] if len([w[3] for w in month_days if w[3] != 0]) > 1 else 13
    current_fomc_days = fomc_dates_2026.get((year, month), [17, 18])
    
    html = '<table class="cal-table"><tr><th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th></tr>'
    
    for week in month_days:
        html += "<tr>"
        for day in week:
            if day == 0:
                html += "<td></td>"
            else:
                classes = []
                if (year == today.year and month == today.month and day == today.day):
                    classes.append("cal-today")
                elif day in current_fomc_days:
                    classes.append("cal-event-fomc")
                elif day == first_friday:
                    classes.append("cal-event-jobs")
                elif day == cpi_day:
                    classes.append("cal-event-cpi")
                
                class_str = " ".join(classes)
                html += f'<td class="{class_str}">{day}</td>'
        html += "</tr>"
    
    html += "</table>"
    html += f"""
    <div style="margin-top: 10px; font-size: 0.78rem; line-height: 1.4; color: #cbd5e1;">
        <span style="color:#38bdf8;"><b>🔵 Today:</b> {today.strftime('%b %d, %Y')}</span><br>
        <span style="color:#c084fc;"><b>🟣 FOMC Decision:</b> {month_name} {', '.join(map(str, current_fomc_days))}</span><br>
        <span style="color:#34d399;"><b>🟢 Jobs Report:</b> Day {first_friday} (Unemployment)</span><br>
        <span style="color:#f472b6;"><b>🔴 CPI Inflation:</b> Day {cpi_day}</span>
    </div>
    """
    return html

# ==============================================================================
# 4. TILE RENDER FUNCTIONS
# ==============================================================================
def render_fed_funds():
    s_fed = fetch_fred_series('FEDFUNDS')
    if not s_fed.empty:
        df = pd.DataFrame({'Rate (%)': s_fed})
        latest = df['Rate (%)'].iloc[-1]
        prev = df['Rate (%)'].iloc[-2] if len(df) > 1 else latest
        st.metric("Federal Funds Effective Rate", f"{latest:.2f}%", f"{latest - prev:+.2f}% MoM")
        st.plotly_chart(create_dark_chart(df, 'Rate (%)', "Fed Funds Rate Trend", color="#00d2ff"), use_container_width=True)
        st.markdown("""<div class="analysis-box"><div class="analysis-title">📊 Economic Analysis</div>
        <b>📌 What it means:</b> Benchmark rate set by the Fed for overnight lending.<br>
        <b>📍 Where we are:</b> Adjusting target ranges following FOMC policy decisions.<br>
        <b>🚦 Assessment:</b> 🟨 <b>Neutral / Easing</b> — Rate recalibration supports liquidity.<br>
        <b>🎯 Target Level:</b> <b>2.50% – 3.25%</b> (Estimated neutral rate).</div>""", unsafe_allow_html=True)

def render_cpi():
    s_cpi = fetch_fred_series('CPIAUCSL')
    if not s_cpi.empty:
        s_cpi_yoy = s_cpi.pct_change(12) * 100
        df = pd.DataFrame({'CPI YoY (%)': s_cpi_yoy}).dropna()
        latest = df['CPI YoY (%)'].iloc[-1]
        st.metric("CPI Inflation (YoY % Change)", f"{latest:.2f}%", f"{latest - 2.0:+.2f}% vs Fed Target", delta_color="inverse")
        st.plotly_chart(create_dark_chart(df, 'CPI YoY (%)', "CPI YoY Inflation Trend", color="#f72585", hlines=[{'value': 2.0, 'dash': 'dot', 'color': '#00ff88', 'text': '2% Target'}]), use_container_width=True)
        st.markdown("""<div class="analysis-box"><div class="analysis-title">📊 Economic Analysis</div>
        <b>📌 What it means:</b> Annual percentage change in prices paid by consumers.<br>
        <b>📍 Where we are:</b> Moderating steadily toward the 2.0% target.<br>
        <b>🚦 Assessment:</b> 🟩 <b>Improving</b> — Preserves household purchasing power.<br>
        <b>🎯 Target Level:</b> <b>2.00%</b> (Federal Reserve target).</div>""", unsafe_allow_html=True)

def render_gdp():
    s_gdp = fetch_fred_series('A191RL1Q225SBEA')
    if not s_gdp.empty:
        df = pd.DataFrame({'GDP Growth (%)': s_gdp}).dropna()
        latest = df['GDP Growth (%)'].iloc[-1]
        st.metric("Real GDP Growth Rate (SAAR)", f"{latest:.1f}%", "Expanding" if latest > 0 else "Contracting")
        st.plotly_chart(create_dark_chart(df, 'GDP Growth (%)', "Real GDP Growth Rate (SAAR)", color="#4895ef", hlines=[{'value': 0.0, 'dash': 'solid', 'color': '#ff0055', 'text': '0% Boundary'}]), use_container_width=True)
        st.markdown("""<div class="analysis-box"><div class="analysis-title">📊 Economic Analysis</div>
        <b>📌 What it means:</b> Seasonally adjusted annualized percentage change in real GDP.<br>
        <b>📍 Where we are:</b> Expanding solidly (~2.0%–2.8% pace), avoiding recession.<br>
        <b>🚦 Assessment:</b> 🟩 <b>Good</b> — Sustained output growth across sectors.<br>
        <b>🎯 Target Level:</b> <b>2.0% – 3.0%</b> (Sustainable long-term GDP pace).</div>""", unsafe_allow_html=True)

def render_housing_starts():
    s_houst = fetch_fred_series('HOUST')
    if not s_houst.empty:
        df = pd.DataFrame({'Starts (K)': s_houst})
        latest = df['Starts (K)'].iloc[-1]
        avg = df['Starts (K)'].mean()
        st.metric("Housing Starts (New Construction)", f"{latest:,.0f}K", f"{latest - avg:+,.0f}K vs Avg")
        st.plotly_chart(create_dark_chart(df, 'Starts (K)', "Privately Owned Housing Starts (K)", color="#38bdf8", hlines=[{'value': avg, 'dash': 'dash', 'color': '#ffaa00', 'text': 'Avg'}]), use_container_width=True)
        st.markdown("""<div class="analysis-box"><div class="analysis-title">📊 Economic Analysis</div>
        <b>📌 What it means:</b> Annualized number of new residential building projects started.<br>
        <b>📍 Where we are:</b> Moderating under prevailing developer financing costs.<br>
        <b>🚦 Assessment:</b> 🟨 <b>Sensitive</b> — Construction activity reacts to credit availability.<br>
        <b>🎯 Target Level:</b> <b>1,400K – 1,600K</b> (Healthy expansion level).</div>""", unsafe_allow_html=True)

def render_calendar_tile():
    col_p, col_t, col_n = st.columns([1, 2, 1])
    with col_p:
        if st.button("◀ Prev", key="btn_prev"):
            if st.session_state.cal_month == 1:
                st.session_state.cal_month = 12
                st.session_state.cal_year -= 1
            else:
                st.session_state.cal_month -= 1
            st.rerun()
    with col_t:
        month_label = calendar.month_name[st.session_state.cal_month]
        st.markdown(f"<h4 style='text-align: center; color: #38bdf8; margin: 0;'>{month_label} {st.session_state.cal_year}</h4>", unsafe_allow_html=True)
    with col_n:
        if st.button("Next ▶", key="btn_next"):
            if st.session_state.cal_month == 12:
                st.session_state.cal_month = 1
                st.session_state.cal_year += 1
            else:
                st.session_state.cal_month += 1
            st.rerun()

    st.markdown(render_monthly_calendar(st.session_state.cal_year, st.session_state.cal_month), unsafe_allow_html=True)

def render_home_sales():
    s_sales = fetch_fred_series('HSN1F')
    if not s_sales.empty:
        df = pd.DataFrame({'Sales (K)': s_sales})
        latest = df['Sales (K)'].iloc[-1]
        avg = df['Sales (K)'].mean()
        st.metric("New Single-Family Home Sales", f"{latest:,.0f}K", f"{latest - avg:+,.0f}K vs Avg")
        st.plotly_chart(create_dark_chart(df, 'Sales (K)', "New Home Sales Pace (Annualized K)", color="#a855f7", hlines=[{'value': avg, 'dash': 'dash', 'color': '#ffaa00', 'text': 'Avg'}]), use_container_width=True)
        st.markdown("""<div class="analysis-box"><div class="analysis-title">📊 Economic Analysis</div>
        <b>📌 What it means:</b> Annualized rate of new single-family home sales.<br>
        <b>📍 Where we are:</b> Homebuilders utilizing rate buy-downs to maintain sales pace.<br>
        <b>🚦 Assessment:</b> 🟨 <b>Resilient</b> — Benefiting from existing home supply shortages.<br>
        <b>🎯 Target Level:</b> <b>700K – 800K</b> (Healthy market pace).</div>""", unsafe_allow_html=True)

def render_unemployment():
    s_unrate = fetch_fred_series('UNRATE')
    if not s_unrate.empty:
        df = pd.DataFrame({'Unemployment (%)': s_unrate})
        latest = df['Unemployment (%)'].iloc[-1]
        avg = df['Unemployment (%)'].mean()
        st.metric("Unemployment Rate", f"{latest:.1f}%", f"{latest - avg:+.1f}% vs Avg", delta_color="inverse")
        st.plotly_chart(create_dark_chart(df, 'Unemployment (%)', "Unemployment Trend", color="#4cc9f0", hlines=[{'value': avg, 'dash': 'dash', 'color': '#f72585', 'text': 'Avg'}]), use_container_width=True)
        st.markdown("""<div class="analysis-box"><div class="analysis-title">📊 Economic Analysis</div>
        <b>📌 What it means:</b> Share of active workforce seeking employment.<br>
        <b>📍 Where we are:</b> Healthy full employment baseline (~4.0%–4.3%).<br>
        <b>🚦 Assessment:</b> 🟩 <b>Good</b> — Sustained wage income supports spending.<br>
        <b>🎯 Target Level:</b> <b>3.5% – 4.5%</b> (Full employment range).</div>""", unsafe_allow_html=True)

def render_pmi():
    s_pmi = fetch_fred_series('IPMAN')
    if not s_pmi.empty:
        df = pd.DataFrame({'Index': s_pmi})
        latest = df['Index'].iloc[-1]
        avg = df['Index'].mean()
        st.metric("Industrial Production: Manufacturing", f"{latest:.1f}", f"{latest - avg:+.1f} vs Avg")
        st.plotly_chart(create_dark_chart(df, 'Index', "Manufacturing Output Index", color="#ffaa00", hlines=[{'value': avg, 'dash': 'dash', 'color': '#888888', 'text': 'Avg'}]), use_container_width=True)
        st.markdown("""<div class="analysis-box"><div class="analysis-title">📊 Economic Analysis</div>
        <b>📌 What it means:</b> Physical output from factory supply chains.<br>
        <b>📍 Where we are:</b> Stable output (~99.4) amid steady capital expenditure.<br>
        <b>🚦 Assessment:</b> 🟨 <b>Neutral</b> — Factory activity holding firm.<br>
        <b>🎯 Target Level:</b> <b>> 100.0</b> (Clear industrial expansion).</div>""", unsafe_allow_html=True)

def render_mortgage():
    s_mort = fetch_fred_series('MORTGAGE30US')
    if not s_mort.empty:
        df = pd.DataFrame({'Rate (%)': s_mort})
        latest = df['Rate (%)'].iloc[-1]
        avg = df['Rate (%)'].mean()
        st.metric("30-Year Fixed Mortgage Rate", f"{latest:.2f}%", f"{latest - avg:+.2f}% vs Avg", delta_color="inverse")
        st.plotly_chart(create_dark_chart(df, 'Rate (%)', "30Y Mortgage Rate Trend", color="#ff4b4b", hlines=[{'value': avg, 'dash': 'dash', 'color': '#ffaa00', 'text': 'Avg'}]), use_container_width=True)
        st.markdown("""<div class="analysis-box"><div class="analysis-title">📊 Economic Analysis</div>
        <b>📌 What it means:</b> Primary benchmark for long-term mortgage borrowing costs.<br>
        <b>📍 Where we are:</b> Elevated compared to historical baselines.<br>
        <b>🚦 Assessment:</b> 🟥 <b>Restrictive</b> — Influences homebuyer affordability.<br>
        <b>🎯 Target Level:</b> <b>4.50% – 5.50%</b> (Balanced range).</div>""", unsafe_allow_html=True)

def render_total_debt():
    s_debt = fetch_fred_series('GFDEBTN')
    if not s_debt.empty:
        df = pd.DataFrame({'Debt ($M)': s_debt})
        latest_trillions = df['Debt ($M)'].iloc[-1] / 1e6
        prev_trillions = df['Debt ($M)'].iloc[-2] / 1e6 if len(df) > 1 else latest_trillions
        st.metric("Federal Debt: Total Public Debt", f"${latest_trillions:.2f}T", f"{latest_trillions - prev_trillions:+.2f}T QoQ", delta_color="inverse")
        df['Debt ($T)'] = df['Debt ($M)'] / 1e6
        st.plotly_chart(create_dark_chart(df, 'Debt ($T)', "Total Public Debt ($ Trillions)", color="#f43f5e"), use_container_width=True)
        st.markdown("""<div class="analysis-box"><div class="analysis-title">📊 Economic Analysis</div>
        <b>📌 What it means:</b> Gross national debt owed by the U.S. Federal Government.<br>
        <b>📍 Where we are:</b> Expanding continuously due to fiscal deficit spending.<br>
        <b>🚦 Assessment:</b> 🟥 <b>High Debt Load</b> — Increases federal net interest outlay.<br>
        <b>🎯 Target Level:</b> Sustainable fiscal trajectory relative to GDP.</div>""", unsafe_allow_html=True)

def render_debt_pct_gdp():
    s_dgdp = fetch_fred_series('GFDEGDQ188S')
    if not s_dgdp.empty:
        df = pd.DataFrame({'Debt % GDP': s_dgdp})
        latest = df['Debt % GDP'].iloc[-1]
        avg = df['Debt % GDP'].mean()
        st.metric("Federal Debt as % of GDP", f"{latest:.1f}%", f"{latest - avg:+.1f}% vs Avg", delta_color="inverse")
        st.plotly_chart(create_dark_chart(df, 'Debt % GDP', "Federal Debt % of GDP Trend", color="#e11d48", hlines=[{'value': avg, 'dash': 'dash', 'color': '#ffaa00', 'text': 'Avg'}]), use_container_width=True)
        st.markdown("""<div class="analysis-box"><div class="analysis-title">📊 Economic Analysis</div>
        <b>📌 What it means:</b> Federal debt relative to the total output capacity of the economy.<br>
        <b>📍 Where we are:</b> Exceeds 120%, above post-WWII historical peaks.<br>
        <b>🚦 Assessment:</b> 🟥 <b>Elevated</b> — Elevated ratio places focus on long-term fiscal policy.<br>
        <b>🎯 Target Level:</b> <b>< 80.0%</b> (Sustainable threshold).</div>""", unsafe_allow_html=True)

def render_debt_service():
    s_tdsp = fetch_fred_series('TDSP')
    if not s_tdsp.empty:
        df = pd.DataFrame({'Service % Income': s_tdsp})
        latest = df['Service % Income'].iloc[-1]
        avg = df['Service % Income'].mean()
        st.metric("Household Debt Service % Income", f"{latest:.2f}%", f"{latest - avg:+.2f}% vs Avg", delta_color="inverse")
        st.plotly_chart(create_dark_chart(df, 'Service % Income', "Household Debt Service Ratio Trend", color="#fb7185", hlines=[{'value': avg, 'dash': 'dash', 'color': '#ffaa00', 'text': 'Avg'}]), use_container_width=True)
        st.markdown("""<div class="analysis-box"><div class="analysis-title">📊 Economic Analysis</div>
        <b>📌 What it means:</b> Share of disposable income required for household debt payments.<br>
        <b>📍 Where we are:</b> Moderate level (~9.8%), showing strong household balance sheets.<br>
        <b>🚦 Assessment:</b> 🟩 <b>Healthy</b> — Consumers manage debt burdens without distress.<br>
        <b>🎯 Target Level:</b> <b>< 10.0%</b> (Safe consumer leverage boundary).</div>""", unsafe_allow_html=True)

# Map of all available tiles
TILE_MAP = {
    "Fed Funds Rate": render_fed_funds,
    "CPI Inflation YoY": render_cpi,
    "Real GDP Growth Rate": render_gdp,
    "Housing Starts": render_housing_starts,
    "Interactive Calendar": render_calendar_tile,
    "New Home Sales": render_home_sales,
    "Unemployment Rate": render_unemployment,
    "Manufacturing Output (PMI)": render_pmi,
    "30Y Mortgage Rate": render_mortgage,
    "Federal Debt ($ Total)": render_total_debt,
    "Federal Debt (% of GDP)": render_debt_pct_gdp,
    "Household Debt Service %": render_debt_service,
}

DEFAULT_ORDER = [
    "Fed Funds Rate", "CPI Inflation YoY", "Real GDP Growth Rate",
    "Housing Starts", "Interactive Calendar", "New Home Sales",
    "Unemployment Rate", "Manufacturing Output (PMI)", "30Y Mortgage Rate",
    "Federal Debt ($ Total)", "Federal Debt (% of GDP)", "Household Debt Service %"
]

# Header Title & Ticker Tapes
st.title("🌐 Macroeconomic & Financial Dashboard")
st.caption("Real-time FRED economic indicators, debt metrics, sector returns, and policy tracking.")

# Render Dual Ticker Tapes (YTD Returns + Today's Returns)
st.markdown(render_dual_ticker_tapes(), unsafe_allow_html=True)

# ==============================================================================
# 5. INLINE & SIDEBAR LAYOUT CONFIGURATOR
# ==============================================================================
with st.expander("🔀 Reorder Dashboard Layout (Change Slot Positions)", expanded=False):
    st.write("Select which indicator or component appears in each position on your 4x3 grid:")
    cfg_cols = st.columns(3)
    user_layout = []
    
    for i in range(12):
        col_target = cfg_cols[i % 3]
        default_item = DEFAULT_ORDER[i]
        with col_target:
            chosen = st.selectbox(
                f"Position {i+1}", 
                list(TILE_MAP.keys()), 
                index=list(TILE_MAP.keys()).index(default_item), 
                key=f"slot_main_{i}"
            )
            user_layout.append(chosen)

# Sidebar mirror configuration
st.sidebar.title("⚙️ Position Customizer")
st.sidebar.caption("You can also reorder slots here in the sidebar:")
for i in range(12):
    st.sidebar.caption(f"Slot {i+1}: {user_layout[i]}")

# ==============================================================================
# 6. RENDER 4x3 GRID BASED ON SELECTED POSITIONS
# ==============================================================================
for row_idx in range(4):
    cols = st.columns(3)
    for col_idx in range(3):
        tile_index = row_idx * 3 + col_idx
        metric_name = user_layout[tile_index]
        with cols[col_idx]:
            TILE_MAP[metric_name]()
    st.markdown("<br>", unsafe_allow_html=True)
