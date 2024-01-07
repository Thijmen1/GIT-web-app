# Standard Libraries
from datetime import date

# External Libraries
import pandas as pd
import yfinance as yf
import streamlit as st
from plotly import graph_objs as go
import plotly.graph_objects as go
import numpy as np
from sklearn.cluster import KMeans
import ta


# Function to load historical stock data
def load_data(ticker, start_date, end_date):
    data = yf.download(ticker, start_date, end_date)
    data.reset_index(inplace=True)
    return data.set_index('Date')


# Function to plot raw data
def plot_raw_data():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Open'], name="Open"))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Close"))
    fig.layout.update(
        title_text=f'Stock Price since {START}',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        xaxis_rangeslider_visible=True,
        height=400)
    st.plotly_chart(fig, use_container_width=True)


# Function to find SR zones
def find_sr_zones(stock_data, num_clusters):
    closes = stock_data['Close'].values.reshape(-1, 1)

    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=num_clusters, random_state=42).fit(closes)

    # Get cluster centers
    cluster_centers = kmeans.cluster_centers_.flatten()

    # Sort cluster centers to get potential SR zones
    sr_zones = np.sort(cluster_centers)

    # Create SR zone columns in the dataset
    for i, zone in enumerate(sr_zones):
        stock_data[f'SR_Zone_{i + 1}'] = (stock_data['Close'] > zone - Zonewidth) & (
                    stock_data['Close'] < zone + Zonewidth)

    return stock_data


# Function to generate trading signals
def generate_trading_signals(data, num_clusters):
    # Buy Signal conditions
    buy_conditions = (data['RSI'] < 30) & (data['Close'] < data['LowerBand'])

    # Sell Signal conditions
    sell_conditions = (data['RSI'] > 70) & (data['Close'] > data['UpperBand'])

    # Take Action Signal conditions within SR zones
    take_action_conditions = data[[f'SR_Zone_{i + 1}' for i in range(num_clusters)]].any(axis=1) & (
                (data['RSI'] < 30) | (data['RSI'] > 70) | (data['Close'] < data['LowerBand']) | (
                    data['Close'] > data['UpperBand'])
                )

    # Create signals
    data['Buy_Signal'] = buy_conditions
    data['Sell_Signal'] = sell_conditions
    data['Take_Action_Signal'] = take_action_conditions

    return data


# Function to plot SR zones with signals
def plot_sr_zones_with_signals(stock_data, num_clusters):
    # Plot stock prices with Bollinger Bands
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], name='Close Price'))

    fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data['UpperBand'], name='Upper BB',
                              line=dict(color='royalblue')))
    fig1.add_trace(go.Scatter(x=stock_data.index, y=stock_data['LowerBand'], name='Lower BB',
                              line=dict(color='royalblue')))

    for i in range(1, num_clusters + 1):
        zone_column = f'SR_Zone_{i}'
        zone_price = stock_data.loc[stock_data[zone_column], 'Close'].mean()
        fig1.add_trace(go.Scatter(x=stock_data.index, y=[zone_price] * len(stock_data), name=f'SR Zone {i}',
                                  mode='lines', line=dict(color='lightgray', dash='dash')))

    # Highlight Buy signals
    fig1.add_trace(go.Scatter(x=stock_data[stock_data['Buy_Signal']].index,
                              y=stock_data['Close'][stock_data['Buy_Signal']],
                              mode='markers', marker=dict(color='green', symbol='triangle-up', size=12),
                              name='Buy Signal'))

    # Highlight Sell signals
    fig1.add_trace(go.Scatter(x=stock_data[stock_data['Sell_Signal']].index,
                              y=stock_data['Close'][stock_data['Sell_Signal']],
                              mode='markers', marker=dict(color='red', symbol='triangle-down', size=12),
                              name='Sell Signal'))

    fig1.update_layout(xaxis_title='Date', yaxis_title='Price (USD)', showlegend=True, height=600,
                       title_text="Stock Price with SR Zones, Bollinger Bands, and Signals",
                       xaxis_rangeslider_visible=True)
    st.plotly_chart(fig1, use_container_width=True)


# Function to plot RSI analysis
def plot_rsi_analysis(stock_data):
    fig2 = go.Figure()

    # Add vertical lines at RSI values 30 and 70 (behind other traces)
    fig2.add_shape(
        dict(type='line', x0=stock_data.index.min(), x1=stock_data.index.max(), y0=30, y1=30,
             line=dict(color='red', width=2)), layer='below'
    )
    fig2.add_shape(
        dict(type='line', x0=stock_data.index.min(), x1=stock_data.index.max(), y0=70, y1=70,
             line=dict(color='red', width=2)), layer='below'
    )

    # Plot RSI and Take Action Signal
    fig2.add_trace(go.Scatter(x=stock_data.index, y=stock_data['RSI'], name='RSI'))
    fig2.add_trace(go.Scatter(x=stock_data[stock_data['Take_Action_Signal']].index,
                              y=stock_data['RSI'][stock_data['Take_Action_Signal']],
                              mode='markers', marker=dict(size=4), name='Action Signal'))

    # Customize y-axis ticks
    fig2.update_yaxes(tickvals=[30, 50, 70], ticktext=['30', '50', '70'])

    fig2.update_layout(xaxis_title='Date', yaxis_title='RSI', showlegend=True, height=500, title_text="RSI Analysis",
                       xaxis_rangeslider_visible=True)
    st.plotly_chart(fig2, use_container_width=True)


# Get today's date
TODAY = date.today()

# Set up Streamlit app title
st.title('Buy & Sell Signals')

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

# Fetch historical data for the selected stock
historical_data = yf.download(selected_stock, TODAY - pd.DateOffset(years=20), TODAY)
min_start_year = historical_data.index.min().year
max_start_year = TODAY.year

# Determine the first possible year with data available on January 1st
first_year_with_data = historical_data[historical_data.index.month == 1].index.min().year

# Set default start year to be 1 year ago if possible, otherwise use the first possible year
default_start_year = max(TODAY.year - 1, first_year_with_data)

# Slider for choosing the start date
start_year = st.slider('Select start year:', TODAY.year - 20, TODAY.year, default_start_year)
START = f'{start_year}-01-01'

# Display a loading message while caching historical stock data
data_load_state = st.text('Loading data...')
data = load_data(selected_stock, START, TODAY.strftime("%Y-%m-%d"))
data_load_state.text('Loading data... done!')

# Plot raw data
plot_raw_data()

# Calculate RSI
data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()

# Calculate Bollinger Bands
data['MA20'] = data['Close'].rolling(window=20).mean()
data['UpperBand'] = data['MA20'] + 2 * data['Close'].rolling(window=20).std()
data['LowerBand'] = data['MA20'] - 2 * data['Close'].rolling(window=20).std()

# Find support and resistance zones and add them as columns
num_clusters = 5  # Set the desired number of clusters (SR zones)
Zonewidth = 15  # Set the width of the SD zones. This can also be a percentage of the current stock price.
data = find_sr_zones(data, num_clusters)

# Generate trading signals
data = generate_trading_signals(data, num_clusters)

# Plot stock prices with SR zones, Bollinger Bands, and RSI
plot_sr_zones_with_signals(data, num_clusters)
plot_rsi_analysis(data)
