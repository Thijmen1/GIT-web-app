# Standard Libraries
from datetime import date

# External Libraries
import pandas as pd
import yfinance as yf
import streamlit as st
from prophet import Prophet
from prophet.plot import plot_plotly
from plotly import graph_objs as go

# Get today's date
TODAY = date.today()

# Set up Streamlit app title
st.title('Stock Forecast App')

# List of popular stock tickers to choose from
stocks = ('AAPL', 'AMZN', 'BABA', 'GOOGL', 'JNJ', 'JPM', 'META', 'MSFT', 'V')

# User input for selecting a stock either from the list or entering a custom ticker
user_input = st.radio("Select data source:", ("Choose from list", "Enter ticker"))
if user_input == "Choose from list":
    selected_stock = st.selectbox('Select dataset for prediction', stocks)
else:
    custom_ticker = st.text_input("Enter ticker:")
    selected_stock = custom_ticker.upper()

# Determine the full company name
stock_info = yf.Ticker(selected_stock)
company_name = stock_info.info['longName']

# Show selected company name
st.subheader(f'{company_name}')

# Years for backtesting
n_years_backtest = st.slider('Years for backtesting:', 1, 4)
period_backtest = n_years_backtest * 365

# Years for future prediction
n_years_future = st.slider('Years for future prediction:', 1, 4)
period_future = n_years_future * 365

# Fetch historical data for the selected stock
historical_data = yf.download(selected_stock, TODAY - pd.DateOffset(years=20), TODAY)
min_start_year = historical_data.index.min().year
max_start_year = TODAY.year

# Determine the first possible year with data available on January 1st
first_year_with_data = historical_data[historical_data.index.month == 1].index.min().year

# Set default start year to be 5 years ago if possible, otherwise use the first possible year
default_start_year = max(TODAY.year - 5, first_year_with_data)

# Start date selection
start_year = st.slider('Select start year:', first_year_with_data, max_start_year, default_start_year)
START = f'{start_year}-01-01'


# Function to load historical stock data
def load_data(ticker, start_date, end_date):
    data = yf.download(ticker, start_date, end_date)
    data.reset_index(inplace=True)
    return data


# Display a loading message while caching historical stock data
data_load_state = st.text('Loading data...')
data = load_data(selected_stock, START, TODAY.strftime("%Y-%m-%d"))
data_load_state.text('Loading data... done!')


# Function to plot raw data
def plot_raw_data():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Open'], name="Open"))
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], name="Close"))
    fig.layout.update(
        title_text=f'Stock Price of {company_name} since {START}',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        xaxis_rangeslider_visible=True)
    st.plotly_chart(fig, use_container_width=True)


# Plot raw data
plot_raw_data()

# Split data into training and testing sets
test_data_end_date = TODAY
test_data_start_date = TODAY.replace(year=TODAY.year - n_years_backtest)
train_data = data[data['Date'] <= test_data_start_date.strftime("%Y-%m-%d")]
test_data = data[(data['Date'] > test_data_start_date.strftime("%Y-%m-%d")) &
                 (data['Date'] <= test_data_end_date.strftime("%Y-%m-%d"))]

# Backtesting with Prophet
df_train_backtest = train_data[['Date', 'Close']]
df_train_backtest = df_train_backtest.rename(columns={"Date": "ds", "Close": "y"})

m_backtest = Prophet()
m_backtest.fit(df_train_backtest)
future_backtest = m_backtest.make_future_dataframe(periods=period_backtest)
forecast_backtest = m_backtest.predict(future_backtest)

# Backtest header
st.subheader('**Backtest**')


# Function to plot backtest forecast
def plot_backtest():
    fig_backtest = plot_plotly(m_backtest, forecast_backtest)
    fig_backtest.layout.update(
        title_text=f'Backtest Plot for {n_years_backtest} {"Year" if n_years_backtest == 1 else "Years"}',
        xaxis_title='Date',
        yaxis_title='Close Price (USD)'
    )
    st.plotly_chart(fig_backtest, use_container_width=True)


# Plot backtest forecast
plot_backtest()

# Backtest components
backtest_expander = st.expander("**Backtest components**", expanded=False)

with backtest_expander:
    # Plot components of the backtest forecast
    backtest_components = m_backtest.plot_components(forecast_backtest)
    st.write(backtest_components)

# Compare backtest forecast with actual values
compare_df = pd.merge(test_data[['Date', 'Close']], forecast_backtest[['ds', 'yhat']], how='inner', left_on='Date',
                      right_on='ds')


# Function to plot backtest comparison
def plot_backtest_comparison():
    fig_compare = go.Figure()
    fig_compare.add_trace(go.Scatter(x=compare_df['Date'], y=compare_df['Close'], name='Actual'))
    fig_compare.add_trace(go.Scatter(x=compare_df['Date'], y=compare_df['yhat'], name='Predicted'))
    fig_compare.layout.update(title_text='Backtest Comparison with Actual Values', xaxis_title='Date',
                              yaxis_title='Close Price (USD)')
    st.plotly_chart(fig_compare, use_container_width=True)


# Plot backtest comparison
plot_backtest_comparison()

# Future prediction with Prophet
df_train_future = data[['Date', 'Close']]
df_train_future = df_train_future.rename(columns={"Date": "ds", "Close": "y"})

m_future = Prophet()
m_future.fit(df_train_future)
future_future = m_future.make_future_dataframe(periods=period_future)
forecast_future = m_future.predict(future_future)

# Future header
st.subheader('**Future**')


# Function to plot future forecast
def plot_future():
    fig_future = plot_plotly(m_future, forecast_future)
    fig_future.layout.update(
        title_text=f'Future Plot for {n_years_future} {"Year" if n_years_future == 1 else "Years"}',
        xaxis_title='Date',
        yaxis_title='Close Price (USD)'
    )
    st.plotly_chart(fig_future, use_container_width=True)


# Plot future forecast
plot_future()

# Forecast components
forecast_expander = st.expander("**Forecast components**", expanded=False)

with forecast_expander:
    # Plot components of the future forecast
    forecast_components = m_future.plot_components(forecast_future)
    st.write(forecast_components)
