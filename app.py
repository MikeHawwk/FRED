import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fredapi import Fred
import datetime
import calendar

# ==============================================================================
# 1. PAGE CONFIG & HIGH-CONTRAST DARK STYLING
# ==============================================================================
st.set_page_config(
    page_title="Macroeconomic & Financial Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-Contrast CSS
st.markdown("""
<style>
    /* Hide header white bar & remove default padding */
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .block-container {
        padding-top: 0.2rem !important;
        padding-bottom: 1rem !important;
        max-width: 98% !important;
    }
    
    /* Overall dark theme */
    .stApp {
        background-color: #0b0f19 !important;
        color: #f8fafc !important;
    }
    
    /* Frozen / Sticky Top Ticker Tape */
    .ticker-container {
        position: sticky;
        top: 0;
        z-index: 9999;
        background-color: #111827;
        border-bottom: 2px solid #1f2937;
        padding: 8px 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    
    /* Metric styling */
    [data-testid="stMetricLabel"] {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
        font-size: 1.02rem !important;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
    }

    /* Analysis Box Styling */
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
    
    /* Column tiles */
    div[data-testid="column"] {
        background-color: #111827;
        border: 1px solid #1f2937;
        padding: 14px;
        border-radius: 10px;
    }

    /* Monthly Calendar Table Styling */
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
        border-radius: 50% !important;
    }
    .cal-event-jobs { background-color: #065f46; color: #34d399; font-weight: bold; }
    .cal-event-cpi { background-color: #831843; color: #f472b6; font-weight: bold; }
    .cal-event-fomc { background-color: #581c87; color: #c084fc; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. API KEY SETUP
# ==============================================================================
API_KEY = "19d76f858cd1c2d6c01a6f10a2825a24"

if "FRED_API_KEY" in st.secrets and st.secrets["FRED_API_KEY"]:
    ACTIVE_API_KEY = st.secrets["FRED_API_KEY"]
else:
    ACTIVE_API_KEY = API_KEY

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

def create_dark_chart(df: pd.DataFrame, y_col: str, title: str, color: str = "#00f2fe", hlines: list = None) -> go.Figure:
    fig = px.line(df, x=df.index, y=y_col)
    fig.update_traces(line=dict(color=color, width=2.5))
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.8)",
        margin=dict(l=10, r=10, t=30, b=10),
        height=195,
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

def render_monthly_calendar():
    """Generates an HTML monthly calendar highlighting today and key economic releases."""
    now = datetime.datetime.now()
    year, month, today_day = now.year, now.month, now.day
    month_name = calendar.month_name[month]
    
    cal = calendar.Calendar(firstweekday=6) # Sunday start
    month_days = cal.monthdayscalendar(year, month)
    
    # Recurring release windows
    first_friday = [week[5] for week in month_days if week[5] != 0][0]
    cpi_day = 12
    fomc_day = 18
    
    html = f"""
    <div style="text-align: center; font-weight: bold; font-size: 1.1rem; color: #38bdf8; margin-bottom: 6px;">
        📅 {month_name} {year} Economic Calendar
    </div>
    <table class="cal-table">
        <tr><th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th></tr>
    """
    
    for week in month_days:
        html += "<tr>"
        for day in week:
            if day == 0:
                html += "<td></td>"
            else:
                classes = []
                if day == today_day:
                    classes.append("cal-today")
                elif day == first_friday:
                    classes.append("cal-event-jobs")
                elif day == cpi_day:
                    classes.append("cal-event-cpi")
                elif day == fomc_day:
                    classes.append("cal-event-fomc")
                
                class_str = " ".join(classes)
                html += f'<td class="{class_str}">{day}</td>'
        html += "</tr>"
    
    html += "</table>"
    
    html += f"""
    <div style="margin-top: 10px; font-size: 0.78rem; line-height: 1.4; color: #cbd5e1;">
        <span style="color:#38bdf8;"><b>🔵 Today:</b> {month_name} {today_day}</span><br>
        <span style="color:#34d399;"><b>🟢 Jobs Report:</b> Day {first_friday} (Unemployment)</span><br>
        <span style="color:#f472b6;"><b>🔴 CPI Inflation:</b> ~Day {cpi_day}</span><br>
        <span style="color:#c084fc;"><b>🟣 FOMC Decision:</b> ~Day {fomc_day}</span>
    </div>
    """
    return html

# ==============================================================================
# 4. FROZEN TOP TICKER TAPE (S&P 500, DOW JONES, NASDAQ)
# ==============================================================================
s_sp500 = fetch_fred_series('SP500', start_date="2024-01-01")
s_djia = fetch_fred_series('DJIA', start_date="2024-01-01")
s_nasdaq = fetch_fred_series('NASDAQCOM', start_date="2024-01-01")

t_col1, t_col2, t_col3 = st.columns(3)

with t_col1:
    if not s_sp500.empty:
        val = s_sp500.iloc[-1]
        prev = s_sp500.iloc[-2] if len(s_sp500) > 1 else val
        diff = val - prev
        pct = (diff / prev) * 100
        st.metric("S&P 500", f"{val:,.2f}", f"{diff:+.2f} ({pct:+.2f}%)")

with t_col2:
    if not s_djia.empty:
        val = s_djia.iloc[-1]
        prev = s_djia.iloc[-2] if len(s_djia) > 1 else val
        diff = val - prev
        pct = (diff / prev) * 100
        st.metric("Dow Jones Industrial Average", f"{val:,.2f}", f"{diff:+.2f} ({pct:+.2f}%)")

with t_col3:
    if not s_nasdaq.empty:
        val = s_nasdaq.iloc[-1]
        prev = s_nasdaq.iloc[-2] if len(s_nasdaq) > 1 else val
        diff = val - prev
        pct = (diff / prev) * 100
        st.metric("Nasdaq Composite", f"{val:,.2f}", f"{diff:+.2f} ({pct:+.2f}%)")

st.markdown("<hr style='border: 1px solid #1f2937; margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

# ==============================================================================
# 5. DASHBOARD GRID (3x3)
# ==============================================================================

# --- ROW 1 ---
col1, col2, col3 = st.columns(3)

# 1. Federal Funds Rate
with col1:
    s_fed = fetch_fred_series('FEDFUNDS')
    if not s_fed.empty:
        df_fed = pd.DataFrame({'Rate (%)': s_fed})
        latest_fed = df_fed['Rate (%)'].iloc[-1]
        prev_fed = df_fed['Rate (%)'].iloc[-2] if len(df_fed) > 1 else latest_fed
        
        st.metric("Federal Funds Effective Rate", f"{latest_fed:.2f}%", f"{latest_fed - prev_fed:+.2f}% MoM")
        st.plotly_chart(create_dark_chart(df_fed, 'Rate (%)', "Fed Funds Rate Trend", color="#00d2ff"), use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Benchmark rate set by the Fed for interbank lending.<br>
            <b>📍 Where we are:</b> Transitioning toward neutral rates following inflation cooling.<br>
            <b>🚦 Assessment:</b> 🟨 <b>Easing Policy</b> — Reduces cost of debt across short-term yields.<br>
            <b>🎯 Target Level:</b> <b>2.50% – 3.25%</b> (Estimated long-term neutral rate).
        </div>
        """, unsafe_allow_html=True)

# 2. PMI Manufacturing Index (ISM / Industrial Production Manufacturing)
with col2:
    s_pmi = fetch_fred_series('NAPM')  # ISM Manufacturing PMI
    if s_pmi.empty:
        s_pmi = fetch_fred_series('IPMAN') # Fallback to Industrial Production Manufacturing
    
    if not s_pmi.empty:
        df_pmi = pd.DataFrame({'Index': s_pmi})
        latest_pmi = df_pmi['Index'].iloc[-1]
        prev_pmi = df_pmi['Index'].iloc[-2] if len(df_pmi) > 1 else latest_pmi
        
        st.metric("PMI Manufacturing Index", f"{latest_pmi:.1f}", f"{latest_pmi - prev_pmi:+.1f} MoM")
        fig_pmi = create_dark_chart(df_pmi, 'Index', "PMI Manufacturing Trend", color="#ffaa00", 
                                    hlines=[{'value': 50.0, 'dash': 'dash', 'color': '#00ff88', 'text': 'Expansion (50)'}])
        st.plotly_chart(fig_pmi, use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Gauge of manufacturing activity. Above 50 = Expansion, Below 50 = Contraction.<br>
            <b>📍 Where we are:</b> Oscillating near the 50 expansion/contraction boundary.<br>
            <b>🚦 Assessment:</b> 🟨 <b>Neutral</b> — Factory sector stabilized after past rate hikes.<br>
            <b>🎯 Target Level:</b> <b>52.0 – 55.0+</b> (Healthy sustained manufacturing growth).
        </div>
        """, unsafe_allow_html=True)

# 3. CPI Inflation YoY
with col3:
    s_cpi = fetch_fred_series('CPIAUCSL')
    if not s_cpi.empty:
        s_cpi_yoy = s_cpi.pct_change(12) * 100
        df_cpi = pd.DataFrame({'CPI YoY (%)': s_cpi_yoy}).dropna()
        latest_cpi = df_cpi['CPI YoY (%)'].iloc[-1]
        
        st.metric("CPI Inflation (YoY % Change)", f"{latest_cpi:.2f}%", f"{latest_cpi - 2.0:+.2f}% vs Fed Target", delta_color="inverse")
        fig_cpi = create_dark_chart(df_cpi, 'CPI YoY (%)', "CPI YoY Inflation Trend", color="#f72585",
                                    hlines=[{'value': 2.0, 'dash': 'dot', 'color': '#00ff88', 'text': '2% Fed Target'}])
        st.plotly_chart(fig_cpi, use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Annual rate of price increases across household goods.<br>
            <b>📍 Where we are:</b> Moderating closer to the Fed's 2.0% target price corridor.<br>
            <b>🚦 Assessment:</b> 🟩 <b>Improving</b> — Easing headline pressure supports consumer wages.<br>
            <b>🎯 Target Level:</b> <b>2.00%</b> (The Fed's explicit inflation mandate).
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- ROW 2 ---
col4, col5, col6 = st.columns(3)

# 4. 30-Year Mortgage Rate
with col4:
    s_mort = fetch_fred_series('MORTGAGE30US')
    if not s_mort.empty:
        df_mort = pd.DataFrame({'Rate (%)': s_mort})
        latest_mort = df_mort['Rate (%)'].iloc[-1]
        avg_mort = df_mort['Rate (%)'].mean()
        
        st.metric("30-Year Fixed Mortgage Rate", f"{latest_mort:.2f}%", f"{latest_mort - avg_mort:+.2f}% vs Hist Avg", delta_color="inverse")
        fig_mort = create_dark_chart(df_mort, 'Rate (%)', "30Y Mortgage Rate Trend", color="#ff4b4b",
                                     hlines=[{'value': avg_mort, 'dash': 'dash', 'color': '#ffaa00', 'text': 'Avg'}])
        st.plotly_chart(fig_mort, use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Primary borrowing cost for U.S. residential property buyers.<br>
            <b>📍 Where we are:</b> Moderating off recent peaks as treasury yields adjust lower.<br>
            <b>🚦 Assessment:</b> 🟨 <b>Restrictive</b> — High relative rates constrain housing liquidity.<br>
            <b>🎯 Target Level:</b> <b>4.50% – 5.50%</b> (Balanced range for buyers & builders).
        </div>
        """, unsafe_allow_html=True)

# 5. MIDDLE CENTER: DYNAMIC MONTHLY CALENDAR
with col5:
    st.markdown(render_monthly_calendar(), unsafe_allow_html=True)
    st.markdown("""
    <div class="analysis-box" style="margin-top: 10px;">
        <div class="analysis-title">📊 Release Schedule Focus</div>
        <b>📌 Key Events:</b> Track the 1st Friday Jobs report and mid-month CPI inflation for policy cues.
    </div>
    """, unsafe_allow_html=True)

# 6. Unemployment Rate
with col6:
    s_unrate = fetch_fred_series('UNRATE')
    if not s_unrate.empty:
        df_unrate = pd.DataFrame({'Unemployment (%)': s_unrate})
        latest_unrate = df_unrate['Unemployment (%)'].iloc[-1]
        avg_unrate = df_unrate['Unemployment (%)'].mean()
        
        st.metric("Unemployment Rate", f"{latest_unrate:.1f}%", f"{latest_unrate - avg_unrate:+.1f}% vs Hist Avg", delta_color="inverse")
        fig_unrate = create_dark_chart(df_unrate, 'Unemployment (%)', "Unemployment Rate Trend", color="#4cc9f0",
                                       hlines=[{'value': avg_unrate, 'dash': 'dash', 'color': '#f72585', 'text': 'Avg'}])
        st.plotly_chart(fig_unrate, use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Share of active workforce looking for employment.<br>
            <b>📍 Where we are:</b> Low (~4.0%–4.3%), signaling sustained overall labor stability.<br>
            <b>🚦 Assessment:</b> 🟩 <b>Good</b> — Strong employment fuels consumer purchasing power.<br>
            <b>🎯 Target Level:</b> <b>3.5% – 4.5%</b> (Full employment range).
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- ROW 3 ---
col7, col8, col9 = st.columns(3)

# 7. Housing Starts (HOUST)
with col7:
    s_houst = fetch_fred_series('HOUST')
    if not s_houst.empty:
        df_houst = pd.DataFrame({'Starts (Thousands)': s_houst})
        latest_houst = df_houst['Starts (Thousands)'].iloc[-1]
        avg_houst = df_houst['Starts (Thousands)'].mean()
        
        st.metric("Housing Starts (Annual Rate)", f"{latest_houst:,.0f}K", f"{latest_houst - avg_houst:+.0f}K vs Avg")
        fig_houst = create_dark_chart(df_houst, 'Starts (Thousands)', "New Housing Starts (Thousands)", color="#00ff88",
                                      hlines=[{'value': avg_houst, 'dash': 'dash', 'color': '#ffaa00', 'text': 'Avg'}])
        st.plotly_chart(fig_houst, use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Annualized number of new residential building construction projects started.<br>
            <b>📍 Where we are:</b> Hovering near historical baseline averages (~1,350K–1,450K).<br>
            <b>🚦 Assessment:</b> 🟨 <b>Neutral</b> — Homebuilders remain cautious on financing costs.<br>
            <b>🎯 Target Level:</b> <b>> 1,500K</b> (Sustained pace needed to satisfy nationwide housing demand).
        </div>
        """, unsafe_allow_html=True)

# 8. Housing Sales (HSN1F - New Single Family Houses Sold)
with col8:
    s_sales = fetch_fred_series('HSN1F')
    if not s_sales.empty:
        df_sales = pd.DataFrame({'Sales (Thousands)': s_sales})
        latest_sales = df_sales['Sales (Thousands)'].iloc[-1]
        avg_sales = df_sales['Sales (Thousands)'].mean()
        
        st.metric("New Home Sales (Annual Rate)", f"{latest_sales:,.0f}K", f"{latest_sales - avg_sales:+.0f}K vs Avg")
        fig_sales = create_dark_chart(df_sales, 'Sales (Thousands)', "New Single-Family Home Sales", color="#9d4edd",
                                      hlines=[{'value': avg_sales, 'dash': 'dash', 'color': '#ffaa00', 'text': 'Avg'}])
        st.plotly_chart(fig_sales, use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Annualized rate of newly constructed single-family homes sold.<br>
            <b>📍 Where we are:</b> Moderate turnover (~650K–750K range) supported by builder incentives.<br>
            <b>🚦 Assessment:</b> 🟩 <b>Stable</b> — Buyers leveraging builder rate buydowns.<br>
            <b>🎯 Target Level:</b> <b>750K – 850K</b> (Robust new housing demand).
        </div>
        """, unsafe_allow_html=True)

# 9. Real GDP Growth YoY (GDPC1)
with col9:
    s_gdp = fetch_fred_series('GDPC1')
    if not s_gdp.empty:
        s_gdp_yoy = s_gdp.pct_change(4) * 100
        df_gdp = pd.DataFrame({'GDP Growth YoY (%)': s_gdp_yoy}).dropna()
        latest_gdp = df_gdp['GDP Growth YoY (%)'].iloc[-1]
        
        st.metric("Real GDP Growth (YoY %)", f"{latest_gdp:.2f}%", "Expanding" if latest_gdp > 0 else "Contracting")
        fig_gdp = create_dark_chart(df_gdp, 'GDP Growth YoY (%)', "Real GDP YoY Growth", color="#4895ef",
                                    hlines=[{'value': 0.0, 'dash': 'solid', 'color': '#ff0055', 'text': '0% Boundary'}])
        st.plotly_chart(fig_gdp, use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Overall inflation-adjusted economic growth rate.<br>
            <b>📍 Where we are:</b> Expanding at a solid ~2.0%–2.8% pace.<br>
            <b>🚦 Assessment:</b> 🟩 <b>Good</b> — Positive output growth maintains economic expansion.<br>
            <b>🎯 Target Level:</b> <b>2.0% – 3.0%</b> (Sustainable long-term growth pace).
        </div>
        """, unsafe_allow_html=True)
