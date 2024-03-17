# -*- coding: utf-8 -*-
"""
Created on Sun Mar  3 14:50:40 2024

@author: cjtev
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import yfinance as yf


cases = ["base", "bull", "bear"]


# Create an empty list to store the data
values = []
estimates = []

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
    
    #wll estimates
    url_3 = f"https://www.alphaspread.com/security/nasdaq/{current_ticker}/analyst-estimates#wall-street-price-targets"
    
    html_3 = requests.get(url_3).text
    soup_3 = BeautifulSoup(html_3, 'html.parser')
    
    #lowest estimate
    selector_estimate_low = "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(3) > div > div:nth-child(7) > div:nth-child(1) > div.right-aligned > div.ui.header"
    estimate_low = soup_3.select_one(selector_estimate_low).get_text()
    numeric_estimate_low = float(''.join(c for c in estimate_low if c.isdigit() or c == '.'))
    
    current_data["Wall street lowest estimate 1-yr"] = numeric_estimate_low
    
    #avg estimate
    selector_estimate_avg = "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(3) > div > div:nth-child(7) > div:nth-child(3) > div.right-aligned > div.ui.header"
    estimate_avg = soup_3.select_one(selector_estimate_avg).get_text()
    numeric_estimate_avg = float(''.join(c for c in estimate_avg if c.isdigit() or c == '.'))
    
    current_data["Wall street average estimate 1-yr"] = numeric_estimate_avg
    
    #highest estimate
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
        current_data[f"Signal_DCF_{case}_AS"] = "Undervalued" if numeric_dcf_value > numeric_current_price else "Overvalued"
        
    
    return pd.DataFrame(values)
        
def fetch_opinions(current_ticker): 
    url_3 = f"https://www.alphaspread.com/security/nasdaq/{current_ticker}/analyst-estimates#wall-street-price-targets"
    
    html_3 = requests.get(url_3).text
    soup_3 = BeautifulSoup(html_3, 'html.parser')
    
    # Initialize lists to store the extracted data
    persons = []
    companies = []
    estimates = []
    
    # Selectors for person, company, and estimate elements
    person_selectors = [
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(1) > div.ui.header > div.content",
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(2) > div.ui.header > div.content",
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(3) > div.ui.header > div.content",
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(4) > div.ui.header > div.content",
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(5) > div.ui.header > div.content"
    ]
    
    company_selectors = [
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(1) > div.ui.header > div.content > div",
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(2) > div.ui.header > div.content > div",
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(3) > div.ui.header > div.content > div",
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(4) > div.ui.header > div.content > div",
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(5) > div.ui.header > div.content > div"
    ]
    
    estimate_selectors = [
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(1) > table > tbody > tr:nth-child(1) > td:nth-child(2)",
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(2) > table > tbody > tr:nth-child(1) > td:nth-child(2)",
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(3) > table > tbody > tr:nth-child(1) > td:nth-child(2)",
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(4) > table > tbody > tr:nth-child(1) > td:nth-child(2)",
        "#main > div:nth-child(3) > div:nth-child(1) > div > div:nth-child(5) > div > div.mobile-only > div > div:nth-child(5) > table > tbody > tr:nth-child(1) > td:nth-child(2)"
    ]
    
    # Loop through selectors to extract data
    for person_selector, company_selector, estimate_selector in zip(person_selectors, company_selectors, estimate_selectors):
        person = soup_3.select_one(person_selector)
        company = soup_3.select_one(company_selector)
        estimate = soup_3.select_one(estimate_selector)
        
        if person:
            persons.append(person.get_text().strip())
        else:
            persons.append(None)
        
        if company:
            companies.append(company.get_text().strip())
        else:
            companies.append(None)
        
        if estimate:
            estimate_text = estimate.get_text().strip()
            numeric_estimate = float(''.join(c for c in estimate_text if c.isdigit() or c == '.'))
            estimates.append(numeric_estimate)
        else:
            estimates.append(None)
    
    # Create a DataFrame from the extracted data
    df = pd.DataFrame({
        "Person": persons,
        "Company": companies,
        "Estimate 1-yr": estimates
    })
    
    # Append the DataFrame to the list
    estimates.append(df)
    
    return estimates



def main():
    st.title("Stock Analysis")
    
    ticker = st.text_input('Enter stock ticker').upper()  # Update with more tickers if needed
    
    if ticker:
        try:
            ticker = ticker.upper()  # Convert to uppercase if ticker is provided
            stock_info = yf.Ticker(ticker)
            company_name = stock_info.info['longName']
        
            df = get_values(ticker)  # Call get_values function to fetch data
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
    
