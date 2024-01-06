# sr_zones_app_page.py
import streamlit as st
import yfinance as yf
import numpy as np
from sklearn.cluster import KMeans
import ta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def find_sr_zones(stock_data, num_clusters=5, Zonewidth=15):
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

def plot_sr_zones_with_signals(stock_data, num_clusters):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})

    # Plot stock prices with Bollinger Bands
    dates = stock_data.index
    prices = stock_data['Close'].values
    ax1.plot(dates, prices, label='Closing Prices', color='black')

    # Plot SR zones as horizontal lines
    for i in range(1, num_clusters + 1):
        zone_column = f'SR_Zone_{i}'
        zone_price = stock_data.loc[stock_data[zone_column], 'Close'].mean()
        ax1.axhline(y=zone_price, label=f'SR Zone {i}', color='red', linestyle='--')

    ax1.plot(dates, stock_data['UpperBand'], label='Upper Bollinger Band', color='lightblue', linestyle='-')
    ax1.plot(dates, stock_data['LowerBand'], label='Lower Bollinger Band', color='lightblue', linestyle='-')

    # Highlight Buy signals
    ax1.plot(stock_data[stock_data['Buy_Signal']].index, stock_data['Close'][stock_data['Buy_Signal']], '^',
             markersize=10, color='g', label='Buy Signal')

    # Highlight Sell signals
    ax1.plot(stock_data[stock_data['Sell_Signal']].index, stock_data['Close'][stock_data['Sell_Signal']], 'v',
             markersize=10, color='r', label='Sell Signal')

    ax1.set_xlabel('Date')
    ax1.set_ylabel('Closing Prices')
    ax1.set_title('Stock Price with SR Zones, Bollinger Bands, and Signals')
    ax1.grid(False)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator())
    fig.autofmt_xdate()

    # Plot RSI
    ax2.plot(dates, stock_data['RSI'], label='RSI', color='blue')
    ax2.axhline(y=70, color='red', linestyle='--', linewidth=1, label='Overbought (RSI > 70)')
    ax2.axhline(y=30, color='green', linestyle='--', linewidth=1, label='Oversold (RSI < 30)')

    # Highlight Take Action signals
    ax2.plot(stock_data[stock_data['Take_Action_Signal']].index, stock_data['RSI'][stock_data['Take_Action_Signal']],
             'o', markersize=8, color='purple', label='Take Action Signal')

    ax2.set_xlabel('Date')
    ax2.set_ylabel('RSI')
    ax2.grid(False)

    st.pyplot(fig)

def main():
    st.title('SR Zones Analysis')

    # User input for selecting a stock either from the list or entering a custom ticker
    ticker = st.text_input("Enter Ticker:", 'TSLA')

    # Slider for selecting start date
    start_date = st.date_input("Select start date:", pd.to_datetime('2021-01-01'))

    # Fetch the stock data
    stock_data = yf.download(ticker, start=start_date, end='2024-01-01')

    # Calculate RSI
    stock_data['RSI'] = ta.momentum.RSIIndicator(stock_data['Close'], window=14).rsi()

    # Calculate Bollinger Bands
    stock_data['MA20'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['UpperBand'] = stock_data['MA20'] + 2 * stock_data['Close'].rolling(window=20).std()
    stock_data['LowerBand'] = stock_data['MA20'] - 2 * stock_data['Close'].rolling(window=20).std()

    # Find support and resistance zones and add them as columns
    num_clusters = 5  # Set the desired number of clusters (SR zones)
    stock_data = find_sr_zones(stock_data, num_clusters)

    # Generate trading signals
    stock_data = generate_trading_signals(stock_data, num_clusters)

    # Plot stock prices with SR zones, Bollinger Bands, and RSI
    plot_sr_zones_with_signals(stock_data, num_clusters)

if __name__ == "__main__":
    main()
