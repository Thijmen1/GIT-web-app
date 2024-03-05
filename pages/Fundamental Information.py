# -*- coding: utf-8 -*-
"""
Created on Sun Mar  3 14:50:40 2024

@author: cjtev
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd

ticker_list = ["JPM"]
values = []

for current_ticker in ticker_list:
    url_1 = f"https://www.alphaspread.com/security/nasdaq/{current_ticker}/summary"
    url_2 = f"https://www.alphaspread.com/security/nasdaq/{current_ticker}/dcf-valuation/base-case"

    # Read the HTML content from the webpage
    html_1 = requests.get(url_1).text
    html_2 = requests.get(url_2).text

    soup_1 = BeautifulSoup(html_1, 'html.parser')
    soup_2 = BeautifulSoup(html_2, 'html.parser')

    selector_int_price = "#main > div:nth-child(4) > div:nth-child(1) > div > div:nth-child(3) > div > div > div.six.wide.computer.sixteen.wide.tablet.center.aligned.flex-column.mobile-no-horizontal-padding.column.appear.only-opacity > div:nth-child(1) > div > div:nth-child(1) > div.ui.intrinsic-value-color.no-margin.valuation-scenario-value.header.restriction-sensitive-data"
    selector_current = "#main > div:nth-child(4) > div:nth-child(1) > div > div:nth-child(3) > div > div > div.ten.wide.computer.sixteen.wide.tablet.flex-column.mobile-no-horizontal-padding.column > div:nth-child(1) > div > div:nth-child(2) > p > span:nth-child(5)"
    selector_dcf = "#scenario-valuation > div.no-sticky-part > div > div:nth-child(1) > div > div:nth-child(1) > div.ui.dcf-value-color.no-margin.valuation-scenario-value.header.restriction-sensitive-data"

    dcf_value = soup_2.select_one(selector_dcf).get_text()
    numeric_dcf_value = float(''.join(c for c in dcf_value if c.isdigit() or c == '.'))

    int_value = soup_1.select_one(selector_int_price).get_text()
    numeric_int_value = float(''.join(c for c in int_value if c.isdigit() or c == '.'))

    current_price = soup_1.select_one(selector_current).get_text()
    numeric_current_price = float(''.join(c for c in current_price if c.isdigit() or c == '.'))

    signal_intrinsic = "Undervalued" if numeric_int_value > numeric_current_price else "Overvalued"
    signal_dcf = "Buy" if numeric_dcf_value > numeric_current_price else "Sell"

    # Create a list with the current values
    current_data = {
        'Stock': current_ticker,
        'Current Price': numeric_current_price,
        'Intrinsic Value':  numeric_int_value,
        'DCF Value': numeric_dcf_value,
        'Intrinsic/price': signal_intrinsic,
        'DCF/price ':signal_dcf
    }

    # Append the list to the main list
    values.append(current_data)

# Print the resulting list
print(values)