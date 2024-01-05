# Standard Libraries
from datetime import date

# External Libraries
import pandas as pd
import yfinance as yf
import streamlit as st
from prophet import Prophet
from prophet.plot import plot_plotly
from plotly import graph_objs as go

TODAY = date.today()

st.title('Stock Forecast App')

stocks = ('AAPL', 'AMZN', 'BABA', 'GOOGL', 'JNJ', 'JPM', 'META', 'MSFT', 'V')
user_input = st.radio("Select data source:", ("Choose from list", "Enter ticker"))

if user_input == "Choose from list":
    selected_stock = st.selectbox('Select dataset for prediction', stocks)
else:
    custom_ticker = st.text_input("Enter ticker:")
    selected_stock = custom_ticker.upper()

# Years for future prediction
n_years_future = st.slider('Years for future prediction:', 1, 4)
period_future = n_years_future * 365

# Years for backtesting
n_years_backtest = st.slider('Years for backtesting:', 1, 4)
period_backtest = n_years_backtest * 365

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
START = f"{start_year}-01-01"


# Remove @st.cache_data() decorator
def load_data(ticker, start_date, end_date):
    data = yf.download(ticker, start_date, end_date)
    data.reset_index(inplace=True)
    return data


# Use st.cache_data without allow_output_mutation
data_load_state = st.text('Loading data...')
data = load_data(selected_stock, START, TODAY.strftime("%Y-%m-%d"))
data_load_state.text('Loading data... done!')

# Split data into training and testing sets
test_data_start_date = TODAY
test_data_end_date = TODAY.replace(year=TODAY.year - n_years_backtest)
train_data = data[data['Date'] <= test_data_end_date.strftime("%Y-%m-%d")]
test_data = data[(data['Date'] > test_data_end_date.strftime("%Y-%m-%d")) & (
        data['Date'] <= test_data_start_date.strftime("%Y-%m-%d"))]


# Plot raw data
def plot_raw_data():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Open'], name="Open"))
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], name="Close"))
    fig.layout.update(
        title_text=f'Stock Price of {selected_stock} since {START}',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        xaxis_rangeslider_visible=True)
    st.plotly_chart(fig)


plot_raw_data()

# Backtesting with Prophet
df_train_backtest = train_data[['Date', 'Close']]
df_train_backtest = df_train_backtest.rename(columns={"Date": "ds", "Close": "y"})

m_backtest = Prophet()
m_backtest.fit(df_train_backtest)
future_backtest = m_backtest.make_future_dataframe(periods=period_backtest)
forecast_backtest = m_backtest.predict(future_backtest)

# Backtest header
st.subheader('**Backtest**')


# Define plot backtest forecast
def plot_backtest():
    fig_backtest = plot_plotly(m_backtest, forecast_backtest)
    fig_backtest.layout.update(
        title_text=f'Backtest Plot for {n_years_backtest} Years',
        xaxis_title='Date',
        yaxis_title='Close Price (USD)'
    )
    st.plotly_chart(fig_backtest)


# Plot backtest forecast
plot_backtest()

# Backtest components
st.write("**Backtest components**")
backtest_components = m_backtest.plot_components(forecast_backtest)
st.write(backtest_components)

# Compare backtest forecast with actual values
compare_df = pd.merge(test_data[['Date', 'Close']], forecast_backtest[['ds', 'yhat']], how='inner', left_on='Date',
                      right_on='ds')

# Plot backtest comparison
fig_compare = go.Figure()
fig_compare.add_trace(go.Scatter(x=compare_df['Date'], y=compare_df['Close'], name='Actual'))
fig_compare.add_trace(go.Scatter(x=compare_df['Date'], y=compare_df['yhat'], name='Predicted'))
fig_compare.layout.update(title_text='Backtest Comparison with Actual Values', xaxis_title='Date',
                          yaxis_title='Close Price (USD)')
st.plotly_chart(fig_compare)

# Future prediction with Prophet
df_train_future = data[['Date', 'Close']]
df_train_future = df_train_future.rename(columns={"Date": "ds", "Close": "y"})

m_future = Prophet()
m_future.fit(df_train_future)
future_future = m_future.make_future_dataframe(periods=period_future)
forecast_future = m_future.predict(future_future)

# Future header
st.subheader('**Future**')


# Define plot future forecast
def plot_future():
    fig_future = plot_plotly(m_future, forecast_future)
    fig_future.layout.update(
        title_text=f'Future Plot for {n_years_backtest} Years',
        xaxis_title='Date',
        yaxis_title='Close Price (USD)'
    )
    st.plotly_chart(fig_future)


# Plot future forecast
plot_future()

# Forecast components
st.write('**Forecast components**')
forecast_components = m_future.plot_components(forecast_future)
st.write(forecast_components)
