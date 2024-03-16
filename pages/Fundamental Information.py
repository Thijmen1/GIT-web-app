# -*- coding: utf-8 -*-
"""
Created on Sun Mar  3 14:50:40 2024

@author: cjtev
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import yahoofinance as yf

cases = ["base", "bull", "bear"]

# Create an empty list to store the data
values = []

def get_values(current_ticker):
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

        current_data[f"DCF_value_{case}"] = numeric_dcf_value
        current_data[f"Signal_DCF_{case}"] = "Undervalued" if numeric_dcf_value > numeric_current_price else "Overvalued"
    return pd.DataFrame(values)
        




def main():
    st.title("Stock Analysis")
    
    ticker = st.text_input('Enter stock ticker').upper()  # Update with more tickers if needed

    if ticker:
        ticker = ticker.upper()  # Convert to uppercase if ticker is provided
        stock_info = yf.Ticker(ticker)
        company_name = stock_info.info['longName']

        df = get_values(ticker)  # Call get_values function to fetch data
        st.write(df)  # Display the retrieved data frame
    
    else:
        st.write("Please enter a valid stock ticker.")
    
    
if __name__ == "__main__":
    main()
