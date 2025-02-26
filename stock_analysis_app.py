import yfinance as yf
import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
import plotly.express as px
import talib

# Step 1: Load in the neccesary Cache data
@st.cache_data
def get_sp500_components():
    df = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    df = df[0]
    tickers = df['Symbol']
    tickers_companies_dict = dict(zip(df['Symbol'], df['Security']))
    return tickers, tickers_companies_dict

@st.cache_data
def load_data(symbol, start, end):
    data = yf.download(symbol, start, end)
    data.columns = data.columns.get_level_values(0)
    return data

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv().encode('utf-8')

# Step 2: Add in Stocks Parameters
st.sidebar.header('Stock Parameters')
available_tickers, tickers_companies_dict = get_sp500_components()
ticker = st.sidebar.selectbox('Ticker', available_tickers, format_func = tickers_companies_dict.get)
start_date = st.sidebar.date_input('Start Date', datetime.date(2018, 1, 1))
end_date = st.sidebar.date_input('End Date', datetime.date.today())
if start_date > end_date:
    st.sidebar.error('The End Date must fall after the Start Date')

# Step 3: Technical Analysis Parameters
st.sidebar.header('Technical Analysis Paramters')
sma_exp = st.sidebar.expander('SMA')
sma_flag = sma_exp.checkbox('Enable SMA')
sma_periods = sma_exp.number_input('SMA Periods', 1, 50)

bb_exp = st.sidebar.expander('Bollinger Bands')
bb_flag = bb_exp.checkbox('Enable Bollinger Bands')
bb_periods = bb_exp.number_input('BB Periods', 1, 50)
bb_std = bb_exp.number_input('BB Stanard Deviations', 1, 4)

rsi_exp = st.sidebar.expander('Relative Strength Index')
rsi_flag = rsi_exp.checkbox('Enable Relative Strength Index')
rsi_periods = rsi_exp.number_input('RSI Periods', 1, 20)
rsi_upper = rsi_exp.number_input('RSI Upper', 50, 90)  
rsi_lower = rsi_exp.number_input('RSI Lower', 10, 50)                           

# Step 4: The Content
st.title('Technical Analysis of Companies listed in S&P 500')
st.write("""
### User manual
* You can Select any single Company from the S&P 500
* Stock prices is updated daily
* 3 Technical Indicators are Available
* You are able to download the data from Yahoo into a CSV file         
""")

df = load_data(ticker, start_date, end_date)
df_exp = st.expander('Preview Data')
available_cols = df.columns.to_list()
columns_to_show = df_exp.multiselect('Columns', available_cols, default = available_cols)
df_exp.dataframe(df[columns_to_show])
df_exp.download_button("Download selected as CSV", 
                       data = csv_file, 
                       file_name = f'{ticker} Daily Stock Prices',
                       mime = 'text/csv')

# Step 5: The plotting
fig = go.Figure()

if df.empty:
    st.error('No Data Available for the Selected Stock and Date range')
else:
    # Candlestick Trace
    fig.add_trace(go.Candlestick(open = df['Open'],
                                 close = df['Close'],
                                 high = df['High'],
                                 low = df['Low'],
                                 name = 'Price'))

    if rsi_flag:
        rsi = talib.RSI(df['Close'], timeperiod = rsi_periods)
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
    title_str = f"{tickers_companies_dict[ticker]}'s Stock Price"
    config = {'scrollZoom': True}
    fig.update_layout(
        title=title_str,
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_dark",
        xaxis_rangeslider_visible = True,
        dragmode = 'pan'
    )
    fig.show(config = config)

    # Display plot
    st.plotly_chart(fig)
    
