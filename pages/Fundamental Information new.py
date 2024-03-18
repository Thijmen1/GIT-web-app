import requests
import pandas as pd
import streamlit as st
import yfinance as yf

def get_pe_ratio(symbol, api_key):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    pe_ratio = data.get("PERatio")
    return pe_ratio

def main():
    st.title("Stock Analysis")
    api_key = 'YOUR_API_KEY'  # Replace with your Alpha Vantage API key
    
    ticker = st.text_input('Enter stock ticker').upper()  # Update with more tickers if needed
    
    if ticker:
        try:
            ticker = ticker.upper()  # Convert to uppercase if ticker is provided
            stock_info = yf.Ticker(ticker)
            company_name = stock_info.info['longName']
        
            # Fetch P/E ratio using Alpha Vantage
            pe_ratio = get_pe_ratio(ticker, api_key)
            
            if pe_ratio:
                st.write(f"The P/E ratio of {ticker} is {pe_ratio}")
            else:
                st.write(f"Failed to retrieve P/E ratio for {ticker}")
                
            # Fetch free cash flow and enterprise value using yfinance
            info = stock_info.info
            free_cash_flow = info.get("freeCashflow")
            enterprise_value = info.get("enterpriseValue")
            st.write(f"For {ticker}:")
            st.write(f"Free Cash Flow: {free_cash_flow}")
            st.write(f"Enterprise Value: {enterprise_value}")
            
        except Exception as e:
            st.error(f"Failed to retrieve data for {ticker}: {e}")     

if __name__ == "__main__":
    main()




