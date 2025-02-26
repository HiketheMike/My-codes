import yfinance as yf
import streamlit as st
import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Cache functions
@st.cache_data
def get_sp500_components():
    df = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    df = df[0]
    tickers = df["Symbol"].to_list()
    tickers_companies_dict = dict(zip(df["Symbol"], df["Security"]))
    return tickers, tickers_companies_dict

@st.cache_data
def load_data(symbol, start, end):
    data = yf.download(symbol, start, end)
    data.columns = data.columns.get_level_values(0)
    return data

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv().encode("utf-8")

# Sidebar
st.sidebar.header("Stock Parameters")
available_tickers, tickers_companies_dict = get_sp500_components()
ticker = st.sidebar.selectbox("Ticker", available_tickers, format_func=tickers_companies_dict.get)
start_date = st.sidebar.date_input("Start date", datetime.date(2019, 1, 1))
end_date = st.sidebar.date_input("End date", datetime.date.today())
if start_date > end_date:
    st.sidebar.error("The end date must fall after the start date")

# Technical Analysis Parameters
st.sidebar.header("Technical Analysis Parameters")
volume_flag = st.sidebar.checkbox(label="Add volume")
exp_sma = st.sidebar.expander("SMA")
sma_flag = exp_sma.checkbox(label="Add SMA")
sma_periods = exp_sma.number_input(label="SMA Periods", min_value=1, max_value=50, value=20, step=1)

exp_bb = st.sidebar.expander("Bollinger Bands")
bb_flag = exp_bb.checkbox(label="Add Bollinger Bands")
bb_periods = exp_bb.number_input(label="BB Periods", min_value=1, max_value=50, value=20, step=1)
bb_std = exp_bb.number_input(label="# of standard deviations", min_value=1, max_value=4, value=2, step=1)

exp_rsi = st.sidebar.expander("Relative Strength Index")
rsi_flag = exp_rsi.checkbox(label="Add RSI")
rsi_periods = exp_rsi.number_input(label="RSI Periods", min_value=1, max_value=50, value=20, step=1)
rsi_upper = exp_rsi.number_input(label="RSI Upper", min_value=50, max_value=90, value=70, step=1)
rsi_lower = exp_rsi.number_input(label="RSI Lower", min_value=10, max_value=50, value=30, step=1)

# Title
st.title("A simple web app for technical analysis")
st.write("""
### User manual
* You can select any company from the S&P 500 constituents
""")

# Load stock data
df = load_data(ticker, start_date, end_date)

# Preview Data
data_exp = st.expander("Preview data")
available_cols = df.columns.tolist()
columns_to_show = data_exp.multiselect("Columns", available_cols, default=available_cols)
data_exp.dataframe(df[columns_to_show])
csv_file = convert_df_to_csv(df[columns_to_show])
data_exp.download_button(
    label="Download selected as CSV",
    data=csv_file,
    file_name=f"{ticker}_stock_prices.csv",
    mime="text/csv",
)

# Debugging: Check if data is loaded correctly
st.write(f"Data loaded for {ticker}:")
st.write(df.head())

# Ensure that the index is a DatetimeIndex
if not isinstance(df.index, pd.DatetimeIndex):
    st.error("The data index is not a DatetimeIndex, which is required for time series plotting.")
else:
    st.write(f"Index is a {type(df.index)}")

# Plotting the data using plotly
title_str = f"{tickers_companies_dict[ticker]}'s stock price"

# Create the figure
fig = go.Figure()

# Check if data has valid values
if df.empty:
    st.error("No data available for the selected stock symbol and date range.")
else:
    # Candlestick trace (Open, High, Low, Close)
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="Price"
    ))

    # Volume trace (if enabled)
    if volume_flag:
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['Volume'],
            name="Volume",
            marker_color='rgba(255, 153, 51, 0.6)'
        ))

    # Add SMA (if selected)
    if sma_flag:
        sma = df['Close'].rolling(window=sma_periods).mean()
        fig.add_trace(go.Scatter(
            x=df.index,
            y=sma,
            mode='lines',
            name=f"SMA {sma_periods}",
            line=dict(color='blue')
        ))

    # Add Bollinger Bands (if selected)
    if bb_flag:
        rolling_mean = df['Close'].rolling(window=bb_periods).mean()
        rolling_std = df['Close'].rolling(window=bb_periods).std()
        upper_band = rolling_mean + bb_std * rolling_std
        lower_band = rolling_mean - bb_std * rolling_std

        fig.add_trace(go.Scatter(
            x=df.index,
            y=upper_band,
            mode='lines',
            name="Upper Bollinger Band",
            line=dict(color='red', dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=df.index,
            y=lower_band,
            mode='lines',
            name="Lower Bollinger Band",
            line=dict(color='red', dash='dash')
        ))

    # Add RSI (if selected)
    if rsi_flag:
        rsi = 100 - (100 / (1 + (df['Close'].pct_change().dropna() + 1).rolling(window=rsi_periods).mean()))
        fig.add_trace(go.Scatter(
            x=df.index,
            y=rsi,
            mode='lines',
            name=f"RSI {rsi_periods}",
            line=dict(color='green')
        ))
        fig.add_hline(y=rsi_upper, line=dict(color='red', dash='dot'))
        fig.add_hline(y=rsi_lower, line=dict(color='red', dash='dot'))

    # Update layout
    config = {'scrollZoom': True}
    fig.update_layout(
        title=title_str,
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        dragmode = 'pan'
    )
    fig.show(config = config)

    # Display plot
    st.plotly_chart(fig)
