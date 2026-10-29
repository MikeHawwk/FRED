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
    /* Hide header white bar & remove whitespace */
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 98% !important;
    }
    
    /* Overall dark theme */
    .stApp {
        background-color: #0b0f19 !important;
        color: #f8fafc !important;
    }
    
    /* Metric styling */
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

    /* Analysis box */
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

def render_monthly_calendar():
    """Generates an HTML monthly calendar highlighting today and key economic releases."""
    now = datetime.datetime.now()
    year, month, today_day = now.year, now.month, now.day
    month_name = calendar.month_name[month]
    
    cal = calendar.Calendar(firstweekday=6) # Sunday start
    month_days = cal.monthdayscalendar(year, month)
    
    # Identify recurring monthly key release dates (approximate rules)
    # 1st Friday = Employment/Jobs Report
    first_friday = [week[5] for week in month_days if week[5] != 0][0]
    cpi_day = 12 # CPI usually released around 10th-13th
    fomc_day = 18 # FOMC meetings / announcements
    
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
                badge = ""
                if day == today_day:
                    classes.append("cal-today")
                elif day == first_friday:
                    classes.append("cal-event-jobs")
                    badge = " (Jobs)"
                elif day == cpi_day:
                    classes.append("cal-event-cpi")
                    badge = " (CPI)"
                elif day == fomc_day:
                    classes.append("cal-event-fomc")
                    badge = " (FOMC)"
                
                class_str = " ".join(classes)
                html += f'<td class="{class_str}">{day}</td>'
        html += "</tr>"
    
    html += "</table>"
    
    # Event Legend
    html += f"""
    <div style="margin-top: 10px; font-size: 0.78rem; line-height: 1.4; color: #cbd5e1;">
        <span style="color:#38bdf8;"><b>🔵 Today:</b> {month_name} {today_day}</span><br>
        <span style="color:#34d399;"><b>🟢 Jobs Report:</b> Day {first_friday} (Unemployment & NFP)</span><br>
        <span style="color:#f472b6;"><b>🔴 CPI Inflation:</b> ~Day {cpi_day}</span><br>
        <span style="color:#c084fc;"><b>🟣 FOMC / Fed Rate Decision:</b> ~Day {fomc_day}</span>
    </div>
    """
    return html

# Title Header
st.title("🌐 Macroeconomic & Financial Dashboard")
st.caption("Real-time FRED economic indicators, yield curve analysis, and monetary policy tracking.")
st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# 4. DASHBOARD GRID (3x3)
# ==============================================================================

# --- ROW 1 ---
col1, col2, col3 = st.columns(3)

# 1. Fed Funds Rate
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
            <b>📌 What it means:</b> Benchmark rate set by the Fed for overnight interbank lending.<br>
            <b>📍 Where we are:</b> Transitioning toward neutral rates after restrictive tightening.<br>
            <b>🚦 Assessment:</b> 🟨 <b>Neutral / Easing</b> — Lowering rate reduces debt burden.<br>
            <b>🎯 Target Level:</b> <b>2.50% – 3.25%</b> (Long-term neutral rate).
        </div>
        """, unsafe_allow_html=True)

# 2. S&P 500 Index
with col2:
    s_sp = fetch_fred_series('SP500')
    if not s_sp.empty:
        df_sp = pd.DataFrame({'S&P 500': s_sp})
        latest_sp = df_sp['S&P 500'].iloc[-1]
        prev_sp = df_sp['S&P 500'].iloc[-2] if len(df_sp) > 1 else latest_sp
        
        st.metric("S&P 500 Index", f"{latest_sp:,.2f}", f"{((latest_sp - prev_sp)/prev_sp)*100:+.2f}% Daily")
        st.plotly_chart(create_dark_chart(df_sp, 'S&P 500', "S&P 500 Performance", color="#00f2fe"), use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Primary benchmark for US public equity market value.<br>
            <b>📍 Where we are:</b> Trading near upper ranges on corporate earnings strength.<br>
            <b>🚦 Assessment:</b> 🟩 <b>Positive</b> — Boosts corporate capital & wealth effect.<br>
            <b>🎯 Target Level:</b> <b>8% – 10%</b> annualized historical return slope.
        </div>
        """, unsafe_allow_html=True)

# 3. Manufacturing Output Index
with col3:
    s_pmi = fetch_fred_series('IPMAN')
    if not s_pmi.empty:
        df_pmi = pd.DataFrame({'Index': s_pmi})
        latest_pmi = df_pmi['Index'].iloc[-1]
        avg_pmi = df_pmi['Index'].mean()
        
        st.metric("Industrial Production: Manufacturing", f"{latest_pmi:.1f}", f"{latest_pmi - avg_pmi:+.1f} vs Avg")
        fig_pmi = create_dark_chart(df_pmi, 'Index', "Manufacturing Output", color="#ffaa00", 
                                    hlines=[{'value': avg_pmi, 'dash': 'dash', 'color': '#888888', 'text': 'Avg'}])
        st.plotly_chart(fig_pmi, use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Physical output from factory and industrial supply chains.<br>
            <b>📍 Where we are:</b> Subdued (~99.4 range) amid cautious business investment.<br>
            <b>🚦 Assessment:</b> 🟨 <b>Neutral</b> — Stable output, but lacking acceleration.<br>
            <b>🎯 Target Level:</b> <b>> 100.0</b> (Clear expansion above historical baseline).
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
        
        st.metric("30-Year Fixed Mortgage Rate", f"{latest_mort:.2f}%", f"{latest_mort - avg_mort:+.2f}% vs Avg", delta_color="inverse")
        fig_mort = create_dark_chart(df_mort, 'Rate (%)', "30Y Mortgage Rate", color="#ff4b4b",
                                     hlines=[{'value': avg_mort, 'dash': 'dash', 'color': '#ffaa00', 'text': 'Avg'}])
        st.plotly_chart(fig_mort, use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Standard long-term borrowing cost for U.S. home buyers.<br>
            <b>📍 Where we are:</b> Elevated compared to the decade following 2008.<br>
            <b>🚦 Assessment:</b> 🟥 <b>Restrictive</b> — Weighs on housing market volume.<br>
            <b>🎯 Target Level:</b> <b>4.50% – 5.50%</b> (Healthy balance for buyers/lenders).
        </div>
        """, unsafe_allow_html=True)

# 5. MIDDLE CENTER: DYNAMIC MONTHLY CALENDAR
with col5:
    st.markdown(render_monthly_calendar(), unsafe_allow_html=True)
    st.markdown("""
    <div class="analysis-box" style="margin-top: 12px;">
        <div class="analysis-title">📊 Release Schedule Strategy</div>
        <b>📌 Focus:</b> Watch the 1st Friday Jobs report and mid-month CPI inflation for market direction.
    </div>
    """, unsafe_allow_html=True)

# 6. FIXED Unemployment Rate
with col6:
    s_unrate = fetch_fred_series('UNRATE')
    if not s_unrate.empty:
        df_unrate = pd.DataFrame({'Unemployment (%)': s_unrate})
        latest_unrate = df_unrate['Unemployment (%)'].iloc[-1]
        avg_unrate = df_unrate['Unemployment (%)'].mean()
        
        st.metric("Unemployment Rate", f"{latest_unrate:.1f}%", f"{latest_unrate - avg_unrate:+.1f}% vs Avg", delta_color="inverse")
        fig_unrate = create_dark_chart(df_unrate, 'Unemployment (%)', "Unemployment Trend", color="#4cc9f0",
                                       hlines=[{'value': avg_unrate, 'dash': 'dash', 'color': '#f72585', 'text': 'Avg'}])
        st.plotly_chart(fig_unrate, use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Share of active workforce looking for employment.<br>
            <b>📍 Where we are:</b> Low (~4.0%–4.3%), signaling sustained full employment.<br>
            <b>🚦 Assessment:</b> 🟩 <b>Good</b> — Strong job market provides wage income.<br>
            <b>🎯 Target Level:</b> <b>3.5% – 4.5%</b> (Full employment range).
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- ROW 3 ---
col7, col8, col9 = st.columns(3)

# 7. CPI Inflation YoY
with col7:
    s_cpi = fetch_fred_series('CPIAUCSL')
    if not s_cpi.empty:
        s_cpi_yoy = s_cpi.pct_change(12) * 100
        df_cpi = pd.DataFrame({'CPI YoY (%)': s_cpi_yoy}).dropna()
        latest_cpi = df_cpi['CPI YoY (%)'].iloc[-1]
        avg_cpi = df_cpi['CPI YoY (%)'].mean()
        
        st.metric("CPI Inflation (YoY % Change)", f"{latest_cpi:.2f}%", f"{latest_cpi - 2.0:+.2f}% vs Fed Target", delta_color="inverse")
        fig_cpi = create_dark_chart(df_cpi, 'CPI YoY (%)', "CPI YoY Trend", color="#f72585",
                                    hlines=[{'value': 2.0, 'dash': 'dot', 'color': '#00ff88', 'text': '2% Target'}])
        st.plotly_chart(fig_cpi, use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Annual rate of price increases across household goods.<br>
            <b>📍 Where we are:</b> Cooling down toward the ~2.5% band from peaks.<br>
            <b>🚦 Assessment:</b> 🟩 <b>Improving</b> — Moderating prices protect real income.<br>
            <b>🎯 Target Level:</b> <b>2.00%</b> (The Fed's explicit inflation target).
        </div>
        """, unsafe_allow_html=True)

# 8. 10Y-2Y Yield Spread
with col8:
    s_yc = fetch_fred_series('T10Y2Y')
    if not s_yc.empty:
        df_yc = pd.DataFrame({'Spread (%)': s_yc})
        latest_yc = df_yc['Spread (%)'].iloc[-1]
        is_inverted = latest_yc < 0
        
        st.metric("10Y-2Y Treasury Yield Spread", f"{latest_yc:.2f}%", "Inverted" if is_inverted else "Un-inverted", delta_color="inverse" if is_inverted else "normal")
        fig_yc = create_dark_chart(df_yc, 'Spread (%)', "Yield Spread (10Y minus 2Y)", color="#7209b7",
                                   hlines=[{'value': 0.0, 'dash': 'solid', 'color': '#ff0055', 'text': 'Inversion (0%)'}])
        st.plotly_chart(fig_yc, use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Yield difference between 10Y and 2Y U.S. bonds.<br>
            <b>📍 Where we are:</b> Un-inverting back into positive territory.<br>
            <b>🚦 Assessment:</b> 🟨 <b>Caution</b> — Un-inversion historically accompanies cycle shifts.<br>
            <b>🎯 Target Level:</b> <b>+0.50% to +1.50%</b> (Normal upward-sloping yield curve).
        </div>
        """, unsafe_allow_html=True)

# 9. Real GDP Growth Rate YoY
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
            <b>📌 What it means:</b> Inflation-adjusted measure of overall national economic output.<br>
            <b>📍 Where we are:</b> Growing at a solid ~2.0%–2.8% pace.<br>
            <b>🚦 Assessment:</b> 🟩 <b>Good</b> — Positive growth avoids recessionary contraction.<br>
            <b>🎯 Target Level:</b> <b>2.0% – 3.0%</b> (Sustainable long-term GDP pace).
        </div>
        """, unsafe_allow_html=True)
