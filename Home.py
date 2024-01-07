import streamlit as st

st.set_page_config(
    page_title="Home"
)

st.markdown(
    """
    # Stock Forecasting App

    Welcome to the Stock Forecasting App! Developed by the GIT Delta team, this app allows you to explore historical
    stock data, perform backtesting, and predict future stock prices with advanced forecasting tools.

    ### How to Use:
    1. Navigate to a page on the left-hand menu to get started.
    2. Select a stock from the dropdown menu or enter a custom ticker.
    3. Explore the visualizations to analyze historical trends, backtest results, and future predictions.

    ### Important:
    - Keep in mind that all predictions are based on historical data and may not accurately reflect future market
    conditions.

    If you have any questions or feedback, feel free to reach out! Suggestions are always welcome!

    Enjoy exploring the world of stock forecasting!
    
    #### Tip:
    - Enhance visibility with dark mode for better contrast. Easily customize the app theme by accessing 'Settings' from the top-right menu.

    *Last updated on 7-9-2024*
    """
)
