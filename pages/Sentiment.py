# Standard Libraries
import datetime

# External Libraries
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import nltk
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer


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

    # Define custom color scale for the bar chart
    def get_color(score):
        if score > 0:
            return f'rgba(0, {int(score*255)}, 0, 0.7)'  # Green gradient
        elif score < 0:
            return f'rgba({int(-score*255)}, 0, 0, 0.7)'  # Red gradient
        else:
            return 'rgba(255, 255, 255, 0.7)'  # White for neutral sentiment

    colors = mean_scores['Sentiment Score'].apply(get_color)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=mean_scores.index, y=mean_scores['Sentiment Score'],
                         marker=dict(color=colors)),
                  )

    fig.update_layout(title=ticker + ' Hourly Sentiment Scores',
                      xaxis_title="Time",
                      yaxis_title="Sentiment Score")

    # Set x-axis date format
    fig.update_layout(xaxis=dict(tickmode='linear',
                                 tickformat='%Y-%m-%d',
                                 tickvals=pd.date_range(mean_scores.index.min(), mean_scores.index.max(), freq='D')))

    return fig


# Plot daily sentiment
def plot_daily_sentiment(parsed_and_scored_news, ticker):
    # Select only numeric columns for resampling
    numeric_columns = parsed_and_scored_news.select_dtypes(include='number')

    # Calculate mean sentiment scores
    mean_scores = numeric_columns.resample('D').mean()

    # Define custom color scale for the bar chart
    def get_color(score):
        if score > 0:
            return f'rgba(0, {int(score*255)}, 0, 0.7)'  # Green gradient
        elif score < 0:
            return f'rgba({int(-score*255)}, 0, 0, 0.7)'  # Red gradient
        else:
            return 'rgba(255, 255, 255, 0.7)'  # White for neutral sentiment

    colors = mean_scores['Sentiment Score'].apply(get_color)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=mean_scores.index, y=mean_scores['Sentiment Score'],
                         marker=dict(color=colors)),
                  )

    fig.update_layout(title=ticker + ' Daily Sentiment Scores',
                      xaxis_title="Date",
                      yaxis_title="Sentiment Score")

    # Set x-axis date format
    fig.update_layout(xaxis=dict(tickmode='linear',
                                 tickformat='%Y-%m-%d',
                                 tickvals=pd.date_range(mean_scores.index.min(), mean_scores.index.max(), freq='D')))

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

# Determine the full company name
stock_info = yf.Ticker(selected_stock)
company_name = stock_info.info['longName']

# Show selected company name
st.subheader(f'{company_name}')

# Check if ticker is provided
if ticker:
    try:
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
    except Exception as e:
        st.warning("Enter a correct stock ticker, e.g. 'AAPL' above and hit Enter.")
else:
    st.warning("Enter a stock ticker to start analyzing news sentiment.")
