import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fredapi import Fred

# ==============================================================================
# 1. PAGE CONFIG & HIGH-CONTRAST DARK STYLING
# ==============================================================================
st.set_page_config(
    page_title="Macroeconomic & Financial Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-Contrast CSS Injection
st.markdown("""
<style>
    /* Hide top header white bar and minimize top whitespace */
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 98% !important;
    }
    
    /* Overall dark theme setup */
    .stApp {
        background-color: #0b0f19 !important;
        color: #f8fafc !important;
    }
    
    /* Make metric labels & numbers bright & readable */
    [data-testid="stMetricLabel"] {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
    }

    /* Style for the analysis callout box */
    .analysis-box {
        background-color: #161e2e;
        border: 1px solid #2a364f;
        border-radius: 8px;
        padding: 10px 12px;
        margin-top: 8px;
        font-size: 0.85rem;
        line-height: 1.45;
        color: #e2e8f0;
    }
    .analysis-title {
        color: #38bdf8;
        font-weight: 700;
        font-size: 0.9rem;
        margin-bottom: 4px;
    }
    
    /* Clean container tile border */
    div[data-testid="column"] {
        background-color: #111827;
        border: 1px solid #1f2937;
        padding: 14px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. FRED API KEY SETUP
# ==============================================================================
API_KEY = "19d76f858cd1c2d6c01a6f10a2825a24"

if "FRED_API_KEY" in st.secrets and st.secrets["FRED_API_KEY"]:
    ACTIVE_API_KEY = st.secrets["FRED_API_KEY"]
else:
    ACTIVE_API_KEY = API_KEY

if ACTIVE_API_KEY == "YOUR_FRED_API_KEY_HERE" or not ACTIVE_API_KEY:
    st.error("⚠️ **FRED API Key Missing**: Please set your key in `API_KEY` at the top of `app.py` or inside Streamlit Secrets (`FRED_API_KEY`).")
    st.stop()

# ==============================================================================
# 3. HELPER FUNCTIONS FOR DATA & CHARTS
# ==============================================================================
@st.cache_data(ttl=3600)
def fetch_fred_series(series_id: str, start_date: str = "2018-01-01") -> pd.Series:
    try:
        fred = Fred(api_key=ACTIVE_API_KEY)
        data = fred.get_series(series_id, observation_start=start_date)
        return data.dropna()
    except Exception as e:
        st.warning(f"Failed to fetch {series_id}: {e}")
        return pd.Series(dtype=float)

def create_dark_chart(df: pd.DataFrame, y_col: str, title: str, color: str = "#00f2fe", hlines: list = None) -> go.Figure:
    fig = px.line(df, x=df.index, y=y_col)
    fig.update_traces(line=dict(color=color, width=2.5))
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.8)",
        margin=dict(l=10, r=10, t=30, b=10),
        height=210,
        title=dict(text=title, font=dict(color="#ffffff", size=13, weight="bold")),
        xaxis=dict(
            showgrid=False, 
            showline=False,
            zeroline=False,  # Disables bright white line at x=0
            tickfont=dict(color="#cbd5e1", size=10),
            title=""
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor="#1f2937", 
            zeroline=False,  # Disables bright white line at y=0
            showline=False,
            tickfont=dict(color="#cbd5e1", size=10),
            title=""
        ),
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

# Title Header
st.title("🌐 Macroeconomic & Financial Dashboard")
st.caption("Real-time FRED economic indicators, yield curve analysis, and monetary policy tracking.")
st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# 4. DASHBOARD GRID (3x3) WITH ECONOMIC ANALYSIS
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
            <b>🚦 Assessment:</b> 🟨 <b>Neutral / Easing</b> — Lowering rate reduces debt burden without sparking inflation.<br>
            <b>🎯 Target Level:</b> <b>2.50% – 3.25%</b> (Estimated long-term neutral rate).
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
            <b>📍 Where we are:</b> Trading near upper ranges on earnings strength & liquidity.<br>
            <b>🚦 Assessment:</b> 🟩 <b>Positive</b> — Boosts corporate capital & consumer wealth effect.<br>
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
            <b>🚦 Assessment:</b> 🟥 <b>Restrictive</b> — Weighs on housing turnover & buyer affordability.<br>
            <b>🎯 Target Level:</b> <b>4.50% – 5.50%</b> (Healthy balance for buyers and lenders).
        </div>
        """, unsafe_allow_html=True)

# 5. Consumer Sentiment Index
with col5:
    s_sent = fetch_fred_series('UMCSENT')
    if not s_sent.empty:
        df_sent = pd.DataFrame({'Index': s_sent})
        latest_sent = df_sent['Index'].iloc[-1]
        prev_sent = df_sent['Index'].iloc[-2] if len(df_sent) > 1 else latest_sent
        
        st.metric("U. of Michigan Consumer Sentiment", f"{latest_sent:.1f}", f"{latest_sent - prev_sent:+.1f} MoM")
        st.plotly_chart(create_dark_chart(df_sent, 'Index', "Consumer Sentiment", color="#9d4edd"), use_container_width=True)
        
        st.markdown("""
        <div class="analysis-box">
            <div class="analysis-title">📊 Economic Analysis</div>
            <b>📌 What it means:</b> Household confidence in personal finances and economic outlook.<br>
            <b>📍 Where we are:</b> Muted due to cumulative price inflation in everyday expenses.<br>
            <b>🚦 Assessment:</b> 🟥 <b>Subdued</b> — Low confidence poses a risk to discretionary spending.<br>
            <b>🎯 Target Level:</b> <b>80.0 – 90.0+</b> (Signals optimistic consumer base).
        </div>
        """, unsafe_allow_html=True)

# 6. Unemployment Rate
with col6:
    s_unrate = fetch_fred_series('UNRATE')
    if not s_unrate.empty:
        df_unrate = pd.DataFrame({'Unemployment (%)': s_unrate})
        latest_unrate = df_unrate['Unemployment (%)'].iloc[-1]
        avg_unrate = df_unrate['Unemployment (%)'].mean()
        
        st.metric("Unemployment Rate", f"{latest_unrate:.1f}%", f"{latest_unrate - avg_unrate:+.1f}% vs Avg", delta_color="inverse")
        fig_unrate = create_dark_chart(df_unrate, 'Unemployment (%)', "Unemployment Trend", color="#4cc9f0",
                                       hlines=[{'value': avg_unrate, 'dash': 'dash', 'color': '#f72585', 'text': 'Avg'}])
        st
