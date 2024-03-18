import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import yfinance as yf

cases = ["base", "bull", "bear"]
api_key = 'YOUR_API_KEY'

def get_values(current_ticker, alpha):
    values = []  # Initialize values list here
    url_1 = f"https://www.alphaspread.com/security/nasdaq/{current_ticker}/summary"
    current_data = {"Ticker": current_ticker}

    # Read the HTML content from the summary webpage
    html_1 = requests.get(url_1).text
    soup_1 = BeautifulSoup(html_1, 'html.parser')

    selector_int_price = "#main > div:nth-child(4) > div:nth-child(1) > div > div:nth-child(3) > div > div > div.six.wide.computer.sixteen.wide.tablet.center.aligned.flex-column.mobile-no-horizontal-padding.column.appear.only-opacity > div:nth-child(1) > div > div:nth-child(1) > div.ui.intrinsic-value-color.no-margin.valuation-scenario-value.header.restriction-sensitive-data"
    selector_current = "#main > div:nth-child(4) > div:nth-child(1) > div > div:nth-child(3) > div > div > div.ten.wide.computer.sixteen.wide.tablet.flex-column.mobile-no-horizontal-padding.column > div:nth-child(1) > div > div:nth-child(2) > p > span:nth-child(5)"
    
    # Get the current price
    current_price = soup_1.select_one(selector_current).get_text()
    numeric_current_price = float(''.join(c for c in current_price if c.isdigit() or c == '.'))

    # Get the intrinsic value
    int_value = soup_1.select_one(selector_int_price).get_text()
    numeric_int_value = float(''.join(c for c in int_value if c.isdigit() or c == '.'))

    # Store the base case values
    current_data["Current_Price"] = numeric_current_price
    current_data["Intrinsic_Value_base"] = numeric_int_value
    if numeric_int_value < numeric_current_price - alpha * numeric_current_price:
        current_data["Signal_intrinsic"] = "Overvalued"
    elif numeric_int_value < numeric_current_price + alpha * numeric_current_price:
        current_data["Signal_intrinsic"] = "Properly Valued"
    else:
        current_data["Signal_intrinsic"] = "Undervalued"
    
    # Wall street estimates
    url_3 = f"https://www.alphaspread.com/security/nasdaq/{current_ticker}/analyst-estimates#wall-street-price-targets"
    
    html_3 = requests.get(url_3).text
    soup_3 = BeautifulSoup(html_3, 'html.parser')
    
    # Lowest estimate
    selector_estimate_low = "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(3) > div > div:nth-child(7) > div:nth-child(1) > div.right-aligned > div.ui.header"
    estimate_low = soup_3.select_one(selector_estimate_low).get_text()
    numeric_estimate_low = float(''.join(c for c in estimate_low if c.isdigit() or c == '.'))
    
    current_data["Wall street lowest estimate 1-yr"] = numeric_estimate_low
    
    # Avg estimate
    selector_estimate_avg = "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(3) > div > div:nth-child(7) > div:nth-child(3) > div.right-aligned > div.ui.header"
    estimate_avg = soup_3.select_one(selector_estimate_avg).get_text()
    numeric_estimate_avg = float(''.join(c for c in estimate_avg if c.isdigit() or c == '.'))
    
    current_data["Wall street average estimate 1-yr"] = numeric_estimate_avg
    
    # Highest estimate
    selector_estimate_high = "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(3) > div > div:nth-child(7) > div:nth-child(5) > div.right-aligned > div.ui.header"
    estimate_high = soup_3.select_one(selector_estimate_high).get_text()
    numeric_estimate_high = float(''.join(c for c in estimate_high if c.isdigit() or c == '.'))
    
    current_data["Wall street highest estimate 1-yr"] = numeric_estimate_high
    
    # Append the dictionary to the list
    values.append(current_data)

    # Fetch data for other cases
    for case in cases[0:]:
        url_2 = f"https://www.alphaspread.com/security/nasdaq/{current_ticker}/dcf-valuation/{case}-case"
        html_2 = requests.get(url_2).text
        soup_2 = BeautifulSoup(html_2, 'html.parser')

        selector_dcf = "#scenario-valuation > div.no-sticky-part > div > div:nth-child(1) > div > div:nth-child(1) > div.ui.dcf-value-color.no-margin.valuation-scenario-value.header.restriction-sensitive-data"
        dcf_value = soup_2.select_one(selector_dcf).get_text()
        numeric_dcf_value = float(''.join(c for c in dcf_value if c.isdigit() or c == '.'))

        current_data[f"DCF_value_{case}_AS"] = numeric_dcf_value
        if numeric_dcf_value < numeric_current_price - alpha * numeric_current_price: 
            current_data[f"Signal_DCF_{case}_AS"] = "Overvalued"
        elif numeric_dcf_value < numeric_current_price + alpha * numeric_current_price:
            current_data[f"Signal_DCF_{case}_AS"] = "Properly Valued"
        else: 
            current_data[f"Signal_DCF_{case}_AS"] = "Undervalued"
                
    return pd.DataFrame(values).set_index("Ticker").transpose()

def get_pe_ratio(symbol, api_key):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    pe_ratio = data.get("PERatio")
    return pe_ratio

def get_values_comp(ticker):
    ticker_yf = yf.Ticker(ticker)
    info = ticker_yf.info
    free_cash_flow = info.get("freeCashflow")
    enterprise_value = info.get("enterpriseValue")
    ls = {"FCF": free_cash_flow, "EV": enterprise_value}
    index = [ticker]  # Assuming you want the ticker as the index
    df = pd.DataFrame(ls, index=index)
    return df.T

def main():
    st.title("Stock Analysis")
    
    tickers = st.text_input('Enter stock tickers separated by commas (e.g., AAPL, MSFT)').upper()  
    alpha = st.radio("Error margin (alpha) " , (0.01, 0.02, 0.05 ))
    if tickers:
        try:
            tickers_list = tickers.split(",")  # Convert input to list of tickers
            dfs = []
            
            for ticker in tickers_list:
                ticker = ticker.strip()  # Remove leading/trailing whitespace
                stock_info = yf.Ticker(ticker)
                company_name = stock_info.info['longName']
                df = get_values(ticker, alpha)  # Call get_values function to fetch data
                pe_ratio = get_pe_ratio(ticker, api_key)  # Get PE ratio
                df["PE_Ratio"] = pe_ratio  # Add PE ratio to the DataFrame
                df.columns = pd.MultiIndex.from_product([[company_name], df.columns])  # Add company name as column level
                dfs.append(df)  # Append dataframe without transposing
                
            # Concatenate dataframes along columns (axis=1)
            df_concat = pd.concat(dfs, axis=1)
            
            st.header("Combined Data for Multiple Stocks")
            st.write(df_concat)
            
        except Exception as e:
            st.error(f"Fill in valid stock tickers (e.g., AAPL, MSFT) separated by commas. {e}")     

if __name__ == "__main__":
    main()



    
