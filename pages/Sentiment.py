import streamlit as st
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
# Download VADER lexicon file
import nltk
nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer

import datetime


# Function to get news from FinViz
def get_news(ticker):
    finviz_url = 'https://finviz.com/quote.ashx?t='
    url = finviz_url + ticker
    req = Request(url=url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urlopen(req)
    html = BeautifulSoup(response, 'html.parser')
    news_table = html.find(id='news-table')
    return news_table


# Parse news into DataFrame
def parse_news(news_table):
    parsed_news = []
    today_string = datetime.datetime.today().strftime('%Y-%m-%d')

    for x in news_table.findAll('tr'):
        try:
            text = x.a.get_text()
            date_scrape = x.td.text.split()

            if len(date_scrape) == 1:
                time = date_scrape[0]
            else:
                date = date_scrape[0]
                time = date_scrape[1]

            # Specify date and time formats
            datetime_string = f"{date}-{time}"
            datetime_obj = datetime.datetime.strptime(datetime_string, "%b-%d-%y-%I:%M%p")
            parsed_news.append([datetime_obj, text])
        except Exception as e:
            print(f"Error parsing news: {e}")

    columns = ['Datetime', 'Headline']
    parsed_news_df = pd.DataFrame(parsed_news, columns=columns)
    return parsed_news_df


# Score news sentiment
def score_news(parsed_news_df):
    vader = SentimentIntensityAnalyzer()
    scores = parsed_news_df['Headline'].apply(vader.polarity_scores).tolist()
    scores_df = pd.DataFrame(scores)

    parsed_and_scored_news = parsed_news_df.join(scores_df, rsuffix='_right')
    parsed_and_scored_news = parsed_and_scored_news.set_index('Datetime')
    
    # Check if 'Date' and 'Time' columns exist before dropping them
    if 'Date' in parsed_and_scored_news.columns and 'Time' in parsed_and_scored_news.columns:
        parsed_and_scored_news = parsed_and_scored_news.drop(['Date', 'Time'], axis=1)
        
    parsed_and_scored_news = parsed_and_scored_news.rename(columns={"compound": "Sentiment Score"})

    return parsed_and_scored_news


# Plot hourly sentiment
def plot_hourly_sentiment(parsed_and_scored_news, ticker):
    # Select only numeric columns for resampling
    numeric_columns = parsed_and_scored_news.select_dtypes(include='number')
    
    # Calculate mean sentiment scores
    mean_scores = numeric_columns.resample('H').mean()
    
    fig = px.bar(mean_scores, x=mean_scores.index, y='Sentiment Score', title=ticker + ' Hourly Sentiment Scores')
    fig.update_xaxes(title="Time")
    fig.update_yaxes(title="Sentiment Score")
    return fig


# Plot daily sentiment
def plot_daily_sentiment(parsed_and_scored_news, ticker):
    mean_scores = parsed_and_scored_news.resample('D').mean()
    fig = px.bar(mean_scores, x=mean_scores.index, y='Sentiment Score', title=ticker + ' Daily Sentiment Scores')
    fig.update_xaxes(title="Date")
    fig.update_yaxes(title="Sentiment Score")
    return fig


with st.sidebar.expander("ℹ️ Information", expanded=False):
    st.write(
        "This page provides news sentiments, which are determined by analyzing financial headlines scraped from the FinViz website.")
    st.write("The charts display the average sentiment scores of the selected stock on an hourly and daily basis.")

    # Easter egg
    st.write("""<style>
    .stButton>button {
        opacity: 0.03;
    }
    </style>""", unsafe_allow_html=True)
    if st.button("🥚"):
        st.write("""<style>
            .stButton>button {
                opacity: 1;
            }
            </style>""", unsafe_allow_html=True)
        st.write("Congratulations! You found the Easter egg 🎉")
        st.balloons()

st.header("News Sentiment Analyzer")

# List of popular stock tickers
stocks = ('AAPL', 'AMZN', 'BABA', 'GOOGL', 'JNJ', 'JPM', 'META', 'MSFT', 'V')

# User input for selecting a stock either from the list or entering a custom ticker
ticker_option = st.radio("Select ticker", ("Choose from list", "Enter custom ticker"))

if ticker_option == "Choose from list":
    ticker = st.selectbox('Select stock ticker', stocks)
else:
    ticker = st.text_input('Enter stock ticker', '').upper()

# Check if ticker is provided
if ticker:
        news_table = get_news(ticker)
        if news_table:
            parsed_news_df = parse_news(news_table)
            if not parsed_news_df.empty:
                parsed_and_scored_news = score_news(parsed_news_df)
                fig_hourly = plot_hourly_sentiment(parsed_and_scored_news, ticker)
                fig_daily = plot_daily_sentiment(parsed_and_scored_news, ticker)

                st.plotly_chart(fig_hourly)
                st.plotly_chart(fig_daily)

                # Display table with customized column labels
                st.subheader('**News Headlines and Sentiment Scores**')
                st.write(parsed_and_scored_news.reset_index().rename(
                    columns={"Datetime": "Date Time", "compound": "Sentiment Score"}))
            else:
                st.warning("No news headlines found for the provided ticker.")
        else:
            st.warning("No news found for the provided ticker.")
else:
    st.warning("Enter a stock ticker to start analyzing news sentiment.")
