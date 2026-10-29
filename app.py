import streamlit as st
from fredapi import Fred
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Macro Dashboard", layout="wide")
st.title("Macroeconomic Dashboard")

# Securely fetch the API key from Streamlit's backend
if "FRED_API_KEY" in st.secrets:
    api_key = st.secrets["19d76f858cd1c2d6c01a6f10a2825a24 "]
else:
    st.error("Please add your FRED_API_KEY to the Streamlit Secrets menu.")
    st.stop()

try:
    fred = Fred(api_key=api_key)
    
    st.subheader("10-Year Treasury Constant Maturity Rate (DGS10)")
    
    # Fetch data and structure the data table
    data = fred.get_series('DGS10')
    df = pd.DataFrame(data, columns=['Yield (%)'])
    df.index.name = 'Date'
    df = df.dropna().reset_index()
    
    # Filter to the last 5 years
    df = df.tail(250 * 5)
    
    # Generate the interactive chart
    fig = px.line(df, x='Date', y='Yield (%)')
    st.plotly_chart(fig, use_container_width=True)
    
    # Display the raw data table
    with st.expander("View Raw Data Table"):
        st.dataframe(df.sort_values(by='Date', ascending=False), use_container_width=True)
        
except Exception as e:
    st.error(f"Error fetching data: {e}")
