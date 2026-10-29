import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fredapi import Fred
import datetime

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Macroeconomic & Financial Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark theme styling override for Streamlit components
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    div[data-testid="metric-container"] {
        background-color: #1e222d;
        border: 1px solid #2e3545;
        padding: 12px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🔑 FRED API KEY SETUP
# ==============================================================================
# OPTION 1 (Fallback): Paste your API key here for direct local testing.
API_KEY = "19d76f858cd1c2d6c01a6f10a2825a24"

# OPTION 2 (GitHub / Streamlit Cloud Deployment):
# Store your key in Streamlit Secrets (`.streamlit/secrets.toml` or Streamlit Cloud Settings -> Secrets):
# FRED_API_KEY = "your_actual_api_key_here"

if "FRED_API_KEY" in st.secrets and st.secrets["FRED_API_KEY"]:
    ACTIVE_API_KEY = st.secrets["FRED_API_KEY"]
else:
    ACTIVE_API_KEY = API_KEY

# Stop execution if API key has not been configured
if ACTIVE_API_KEY == "YOUR_FRED_API_KEY_HERE" or not ACTIVE_API_KEY:
    st.error("⚠️ **FRED API Key Missing**: Please set your key in `API_KEY` at the top of `app.py` or inside Streamlit Secrets (`FRED_API_KEY`).")
    st.info("Get a free key from the St. Louis Fed: https://fred.stlouisfed.org/docs/api/api_key.html")
    st.stop()

# ==============================================================================
# DATA FETCHING & CACHING
# ==============================================================================
@st.cache_data(ttl=3600)  # Cache data for 1 hour to prevent hitting FRED API rate limits
def fetch_fred_series(series_id: str, start_date: str = "2015-01-01") -> pd.Series:
    """Fetch series from FRED API with exception handling and clean formatting."""
    try:
        fred = Fred(api_key=ACTIVE_API_KEY)
        data = fred.get_series(series_id, observation_start=start_date)
        data = data.dropna()
        return data
    except Exception as e:
        st.warning(f"Failed to fetch series {series_id}: {e}")
        return pd.Series(dtype=float)

def create_dark_chart(df: pd.DataFrame, y_col: str, title: str, color: str = "#00f2fe", hlines: list = None) -> go.Figure:
    """Utility to generate consistent dark-themed Plotly line charts."""
    fig = px.line(df, x=df.index, y=y_col, title=title)
    fig.update_traces(line=dict(color=color, width=2))
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(30,34,45,0.6)",
        margin=dict(l=20, r=20, t=40, b=20),
        height=260,
        xaxis=dict(showgrid=False, title=""),
        yaxis=dict(showgrid=True, gridcolor="#2e3545", title=""),
        font=dict(color="#e0e0e0", size=11)
    )
    
    if hlines:
        for line in hlines:
            fig.add_hline(
                y=line.get('value'), 
                line_dash=line.get('dash', 'dash'), 
                line_color=line.get('color', '#ff4b4b'),
                annotation_text=line.get('text', ''),
                annotation_position="top right"
            )
            
    return fig

# Title Header
st.title("🌐 Macroeconomic & Financial Markets Dashboard")
st.caption("Real-time FRED economic indicators, yield curve analysis, and monetary policy tracking.")
st.markdown("---")

# ==============================================================================
# 3x3 DASHBOARD GRID LAYOUT
# ==============================================================================

# ------------------------------------------------------------------------------
# ROW 1
# ------------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)

# 1. TOP LEFT: Fed Funds Rate (FEDFUNDS)
with col1:
    s_fed = fetch_fred_series('FEDFUNDS', start_date="2018-01-01")
    if not s_fed.empty:
        df_fed = pd.DataFrame({'Rate (%)': s_fed})
        latest_fed = df_fed['Rate (%)'].iloc[-1]
        prev_fed = df_fed['Rate (%)'].iloc[-2] if len(df_fed) > 1 else latest_fed
        
        st.metric(
            label="Federal Funds Effective Rate", 
            value=f"{latest_fed:.2f}%", 
            delta=f"{latest_fed - prev_fed:+.2f}% vs prev"
        )
        fig_fed = create_dark_chart(df_fed, 'Rate (%)', "Fed Funds Rate Trend", color="#00d2ff")
        st.plotly_chart(fig_fed, use_container_width=True)
        
        st.caption("📅 **Next Est. FOMC Rate Decision:** Dec 16–17, 2026")

# 2. TOP MIDDLE: S&P 500 Index (SP500)
with col2:
    s_sp = fetch_fred_series('SP500', start_date="2020-01-01")
    if not s_sp.empty:
        df_sp = pd.DataFrame({'S&P 500': s_sp})
        latest_sp = df_sp['S&P 500'].iloc[-1]
        prev_sp = df_sp['S&P 500'].iloc[-2] if len(df_sp) > 1 else latest_sp
        pct_change = ((latest_sp - prev_sp) / prev_sp) * 100
        
        st.metric(
            label="S&P 500 Index", 
            value=f"{latest_sp:,.2f}", 
            delta=f"{pct_change:+.2f}% 1-Day"
        )
        fig_sp = create_dark_chart(df_sp, 'S&P 500', "S&P 500 Performance", color="#00f2fe")
        st.plotly_chart(fig_sp, use_container_width=True)
        st.caption("📈 **Equity Reaction:** Broad market pricing relative to macro trends.")

# 3. TOP RIGHT: Manufacturing Activity Index (IPMAN)
with col3:
    s_pmi = fetch_fred_series('IPMAN', start_date="2018-01-01")
    if not s_pmi.empty:
        df_pmi = pd.DataFrame({'Index': s_pmi})
        latest_pmi = df_pmi['Index'].iloc[-1]
        hist_avg_pmi = df_pmi['Index'].mean()
        
        st.metric(
            label="Industrial Production: Manufacturing", 
            value=f"{latest_pmi:.1f}", 
            delta=f"{latest_pmi - hist_avg_pmi:+.1f} vs Hist Avg"
        )
        fig_pmi = create_dark_chart(
            df_pmi, 'Index', "Manufacturing Output Index", color="#ffaa00",
            hlines=[
                {'value': hist_avg_pmi, 'dash': 'dash', 'color': '#888888', 'text': 'Hist Avg'},
                {'value': 100.0, 'dash': 'dot', 'color': '#00ff88', 'text': 'Base (100)'}
            ]
        )
        st.plotly_chart(fig_pmi, use_container_width=True)
        st.caption("📅 **Next Release:** Monthly (15th–17th window)")

st.markdown("---")

# ------------------------------------------------------------------------------
# ROW 2
# ------------------------------------------------------------------------------
col4, col5, col6 = st.columns(3)

# 4. MIDDLE LEFT: 30-Year Mortgage Rate (MORTGAGE30US)
with col4:
    s_mort = fetch_fred_series('MORTGAGE30US', start_date="2018-01-01")
    if not s_mort.empty:
        df_mort = pd.DataFrame({'Rate (%)': s_mort})
        latest_mort = df_mort['Rate (%)'].iloc[-1]
        avg_mort = df_mort['Rate (%)'].mean()
        diff_mort = latest_mort - avg_mort
        status_mort = "ABOVE Avg" if diff_mort > 0 else "BELOW Avg"
        
        st.metric(
            label="30-Year Fixed Mortgage Rate", 
            value=f"{latest_mort:.2f}%", 
            delta=f"{diff_mort:+.2f}% ({status_mort})",
            delta_color="inverse"
        )
        fig_mort = create_dark_chart(
            df_mort, 'Rate (%)', "30Y Mortgage Rate Trend", color="#ff4b4b",
            hlines=[{'value': avg_mort, 'dash': 'dash', 'color': '#ffaa00', 'text': f'Avg ({avg_mort:.2f}%)'}]
        )
        st.plotly_chart(fig_mort, use_container_width=True)
        st.caption("📅 **Next Release:** Thursdays at 10:00 AM ET")

# 5. MIDDLE MIDDLE: Consumer Sentiment Index (UMCSENT)
with col5:
    s_sent = fetch_fred_series('UMCSENT', start_date="2018-01-01")
    if not s_sent.empty:
        df_sent = pd.DataFrame({'Index': s_sent})
        latest_sent = df_sent['Index'].iloc[-1]
        prev_sent = df_sent['Index'].iloc[-2] if len(df_sent) > 1 else latest_sent
        
        st.metric(
            label="U. of Michigan Consumer Sentiment", 
            value=f"{latest_sent:.1f}", 
            delta=f"{latest_sent - prev_sent:+.1f} MoM"
        )
        fig_sent = create_dark_chart(df_sent, 'Index', "Consumer Sentiment Trend", color="#9d4edd")
        st.plotly_chart(fig_sent, use_container_width=True)
        st.caption("🧠 **Sentiment vs Data:** Gauges consumer confidence & spending intentions.")

# 6. MIDDLE RIGHT: Unemployment Rate (UNRATE)
with col6:
    s_unrate = fetch_fred_series('UNRATE', start_date="2018-01-01")
    if not s_unrate.empty:
        df_unrate = pd.DataFrame({'Unemployment (%)': s_unrate})
        latest_unrate = df_unrate['Unemployment (%)'].iloc[-1]
        avg_unrate = df_unrate['Unemployment (%)'].mean()
        
        # Logic: Unemployment below 4.5% is generally considered strong/healthy
        is_good = latest_unrate <= 4.5
        eval_label = "GOOD (Low)" if is_good else "ELEVATED"
        
        st.metric(
            label="Unemployment Rate", 
            value=f"{latest_unrate:.1f}%", 
            delta=f"{eval_label} (Hist Avg: {avg_unrate:.1f}%)",
            delta_color="normal" if is_good else "inverse"
        )
        fig_unrate = create_dark_chart(
            df_unrate, 'Unemployment (%)', "Unemployment Rate Trend", color="#4cc9f0",
            hlines=[{'value': avg_unrate, 'dash': 'dash', 'color': '#f72585', 'text': f'Avg ({avg_unrate:.1f}%)'}]
        )
        st.plotly_chart(fig_unrate, use_container_width=True)
        st.caption("💼 **Labor Market Status:** Threshold ~4.5% denotes strong employment.")

st.markdown("---")

# ------------------------------------------------------------------------------
# ROW 3
# ------------------------------------------------------------------------------
col7, col8, col9 = st.columns(3)

# 7. BOTTOM LEFT: Consumer Price Index YoY Inflation (CPIAUCSL)
with col7:
    s_cpi = fetch_fred_series('CPIAUCSL', start_date="2017-01-01")
    if not s_cpi.empty:
        # Calculate YoY percentage change
        s_cpi_yoy = s_cpi.pct_change(12) * 100
        df_cpi = pd.DataFrame({'CPI YoY (%)': s_cpi_yoy}).dropna()
        latest_cpi = df_cpi['CPI YoY (%)'].iloc[-1]
        avg_cpi = df_cpi['CPI YoY (%)'].mean()
        status_cpi = "ABOVE Avg" if latest_cpi > avg_cpi else "BELOW Avg"
        
        st.metric(
            label="CPI Inflation (YoY % Change)", 
            value=f"{latest_cpi:.2f}%", 
            delta=f"{status_cpi} (Avg: {avg_cpi:.2f}%)",
            delta_color="inverse" if latest_cpi > 2.0 else "normal"
        )
        fig_cpi = create_dark_chart(
            df_cpi, 'CPI YoY (%)', "CPI Inflation YoY Trend", color="#f72585",
            hlines=[
                {'value': avg_cpi, 'dash': 'dash', 'color': '#ffaa00', 'text': f'Avg ({avg_cpi:.2f}%)'},
                {'value': 2.0, 'dash': 'dot', 'color': '#00ff88', 'text': 'Fed Target (2%)'}
            ]
        )
        st.plotly_chart(fig_cpi, use_container_width=True)
        st.caption("📅 **Next Release:** Monthly (approx. 10th–13th window)")

# 8. BOTTOM MIDDLE: Yield Curve Spread 10Y minus 2Y (T10Y2Y)
with col8:
    s_yc = fetch_fred_series('T10Y2Y', start_date="2018-01-01")
    if not s_yc.empty:
        df_yc = pd.DataFrame({'Spread (%)': s_yc})
        latest_yc = df_yc['Spread (%)'].iloc[-1]
        
        is_inverted = latest_yc < 0
        yc_status = "INVERTED (Recession Warning)" if is_inverted else "NORMAL (Uninverted)"
        
        st.metric(
            label="10Y-2Y Treasury Yield Spread", 
            value=f"{latest_yc:.2f}%", 
            delta=yc_status,
            delta_color="inverse" if is_inverted else "normal"
        )
        fig_yc = create_dark_chart(
            df_yc, 'Spread (%)', "Yield Curve (10Y minus 2Y)", color="#7209b7",
            hlines=[{'value': 0.0, 'dash': 'solid', 'color': '#ff0055', 'text': 'Inversion Line (0%)'}]
        )
        st.plotly_chart(fig_yc, use_container_width=True)
        st.caption("⚠️ **Recession Indicator:** Negative spread signals curve inversion.")

# 9. BOTTOM RIGHT: Real GDP Growth Rate (GDPC1 YoY Change)
with col9:
    s_gdp = fetch_fred_series('GDPC1', start_date="2017-01-01")
    if not s_gdp.empty:
        # Calculate YoY quarterly growth rate
        s_gdp_yoy = s_gdp.pct_change(4) * 100
        df_gdp = pd.DataFrame({'GDP Growth YoY (%)': s_gdp_yoy}).dropna()
        latest_gdp = df_gdp['GDP Growth YoY (%)'].iloc[-1]
        
        is_gdp_good = latest_gdp > 0
        gdp_status = "GOOD (Expanding)" if is_gdp_good else "BAD (Contracting)"
        
        st.metric(
            label="Real GDP Growth (YoY %)", 
            value=f"{latest_gdp:.2f}%", 
            delta=gdp_status,
            delta_color="normal" if is_gdp_good else "inverse"
        )
        fig_gdp = create_dark_chart(
            df_gdp, 'GDP Growth YoY (%)', "Quarterly Real GDP YoY Trend", color="#4895ef",
            hlines=[{'value': 0.0, 'dash': 'solid', 'color': '#ff0055', 'text': 'Contraction Boundary (0%)'}]
        )
        st.plotly_chart(fig_gdp, use_container_width=True)
        st.caption("📊 **Economic Expansion:** Positive values indicate expanding economic output.")
