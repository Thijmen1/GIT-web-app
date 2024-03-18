import requests
import yfinance as yf
import streamlit as st

def get_pe_ratio(symbol, api_key):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    pe_ratio = data.get("PERatio")
    return pe_ratio

def fetch_stock_data(symbol, api_key):
    stock_data = {}
    
    # Fetch P/E ratio
    pe_ratio = get_pe_ratio(symbol, api_key)
    stock_data["P/E Ratio"] = pe_ratio
    
    # Fetch free cash flow and enterprise value using yfinance
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        free_cash_flow = info.get("freeCashflow")
        enterprise_value = info.get("enterpriseValue")
        stock_data["Free Cash Flow"] = free_cash_flow
        stock_data["Enterprise Value"] = enterprise_value
    except Exception as e:
        print(f"Failed to retrieve data for {symbol}: {e}")
    
    return stock_data

def main():
    st.title("Stock Analysis")
    api_key = 'YOUR_API_KEY'  # Replace with your Alpha Vantage API key
    
    symbolslist = ["AAPL"]  # List of stock symbols to analyze
    
    for symbol in symbolslist:
        st.header(f"Analysis for {symbol}")
        stock_data = fetch_stock_data(symbol, api_key)
        for key, value in stock_data.items():
            st.write(f"{key}: {value}")
    
if __name__ == "__main__":
    main()




