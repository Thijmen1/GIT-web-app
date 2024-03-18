# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 11:12:02 2024

@author: cjtev
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import yfinance as yf

cases = ["base", "bull", "bear"]
values = []

def get_values(current_ticker, api_key):
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
    current_data["Signal_intrinsic"] = "Undervalued" if numeric_int_value > numeric_current_price else "Overvalued"
    
    # Fetch P/E ratio using Alpha Vantage
    alpha_vantage_pe_ratio = get_pe_ratio(current_ticker, api_key)
    current_data["P/E Ratio"] = alpha_vantage_pe_ratio

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
        current_data[f"Signal_DCF_{case}_AS"] = "Undervalued" if numeric_dcf_value > numeric_current_price else "Overvalued"
    
    return pd.DataFrame(values)

def get_pe_ratio(symbol, api_key):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    pe_ratio = data.get("PERatio")
    return pe_ratio

def fetch_opinions(current_ticker): 
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
        
            df = get_values(ticker, api_key)  # Call get_values function to fetch data
            df = df.transpose()
            st.header(company_name)
            st.write(df)
            
            st.subheader("Expert opinions")
            df_2 = fetch_opinions(ticker)
            st.write(df_2)
            
        except Exception as e:
            st.error(f"Fill in a valid stock ticker e.g. AAPL {e}")     

if __name__ == "__main__":
    main()



