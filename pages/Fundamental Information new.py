import requests
import yfinance as yf
import streamlit as st
from bs4 import BeautifulSoup

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

def fetch_opinions(current_ticker, api_key): 
    url_3 = f"https://www.alphaspread.com/security/nasdaq/{current_ticker}/analyst-estimates#wall-street-price-targets"
    
    html_3 = requests.get(url_3).text
    soup_3 = BeautifulSoup(html_3, 'html.parser')

    # Extract expert opinions
    experts = soup_3.select(".desktop-only")
    companies = []
    estimates = []

    for expert in experts:
        company = expert.select_one(".ui.header").text
        estimate = float(expert.select_one("td:nth-child(2)").text)
        companies.append(company)
        estimates.append(estimate)

    return pd.DataFrame({"Company": companies, "Estimate 1-yr": estimates})

def main():
    st.title("Stock Analysis")
    api_key = 'YOUR_API_KEY'  # Replace with your Alpha Vantage API key
    
    ticker = st.text_input('Enter stock ticker').upper()  # Update with more tickers if needed
    
    if ticker:
        try:
            ticker = ticker.upper()  # Convert to uppercase if ticker is provided
            stock_info = yf.Ticker(ticker)
            company_name = stock_info.info['longName']
        
            st.header(company_name)
            
            # Fetch stock data
            stock_data = fetch_stock_data(ticker, api_key)
            for key, value in stock_data.items():
                st.write(f"{key}: {value}")
            
            # Fetch expert opinions
            st.subheader("Expert opinions")
            df_opinions = fetch_opinions(ticker, api_key)
            st.write(df_opinions)
            
        except Exception as e:
            st.error(f"Fill in a valid stock ticker e.g. AAPL {e}")     

if __name__ == "__main__":
    main()





