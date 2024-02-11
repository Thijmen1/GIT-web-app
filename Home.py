import streamlit as st
import random

st.set_page_config(
    page_title="Home"
)

st.markdown(
    """
    ## Stock Forecasting App

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
    """
)

# Add horizontal line
st.write("<hr>", unsafe_allow_html=True)

# List of investing-related quotes
investing_quotes = [
    ("*\"The stock market is filled with individuals who know the price of everything, but the value of nothing.\"*", "Philip Fisher"),
    ("*\"The four most dangerous words in investing are: 'This time it's different.\"*'", "Sir John Templeton"),
    ("*\"In the short run, the market is a voting machine, but in the long run, it is a weighing machine.\"*", "Benjamin Graham"),
    ("*\"The stock market is a device for transferring money from the impatient to the patient.\"*", "Warren Buffett"),
    ("*\"It's not how much money you make, but how much money you keep, how hard it works for you, and how many generations you keep it for.\"*", "Robert Kiyosaki"),
    ("*\"The individual investor should act consistently as an investor and not as a speculator.\"*", "Ben Graham"),
    ("*\"The goal of the non-professional should not be to pick winners—neither he nor his 'helpers' can do that—but should rather be to own a cross-section of businesses that in aggregate are bound to do well.\"*", "John Bogle"),
    ("*\"Risk comes from not knowing what you're doing.\"*", "Warren Buffett"),
    ("*\"Price is what you pay. Value is what you get.\"*", "Warren Buffett"),
    ("*\"The best investment you can make is in GIT Delta.\"*", "Warren Buffett"),
    ("*\"The market is a pendulum that forever swings between unsustainable optimism and unjustified pessimism.\"*", "Howard Marks"),
    ("*\"Investing should be more like watching paint dry or watching grass grow. If you want excitement, take $800 and go to Las Vegas.\"*", "Paul Samuelson"),
    ("*\"Be fearful when others are greedy. Be greedy when others are fearful.\"*", "Warren Buffett"),
]

# Display a random investing-related quote
random_quote, author = random.choice(investing_quotes)
st.write("")
st.write(f"{random_quote}")
st.write(f"<div style='text-align:right'>{author}</div>", unsafe_allow_html=True)
