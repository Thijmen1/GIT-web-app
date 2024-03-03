import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import statsmodels.api as sm
from filterpy.kalman import KalmanFilter
from math import sqrt
import plotly.graph_objects as go
import warnings
import time

# Set display options and ignore warnings
pd.set_option('display.max_columns', None)
warnings.filterwarnings('ignore')

# Define stock symbols for different sectors
Symbols_energy = ["APA", "BKR", "COP", "CTRA", "CVX", "DVN", "EOG", "EQT", "FANG",
                  "HAL", "HES", "KMI", "MPC", "MRO", "OKE", "OXY", "PSX", "PXD", "SLB",
                  "TRGP", "VLO", "WMB", "XOM"]

Symbols_financial = ["ACGL", "AFL", "AIG", "AIZ", "AJG", "ALL", "AMP", "AON",
                     "AXP", "BAC", "BEN", "BK", "BLK", "BRK.B", "BRO", "BX", "C",
                     "CB", "CBOE", "CFG", "CINF", "CMA", "CME", "COF", "DFS", "EG",
                     "FDS", "FI", "FIS", "FITB", "FLT", "GL", "GPN", "GS", "HBAN", "HIG",
                     "ICE", "IVZ", "JPM", "JKHY", "KEY", "L", "MA", "MCO", "MET", "MKTX",
                     "MMC", "MSCI", "MS", "MTB", "NDAQ", "NTRS", "PFG", "PGR", "PNC",
                     "PRU", "PYPL", "RF", "RJF", "SCHW", "SPGI", "STT", "SYF", "TFC",
                     "TROW", "TRV", "USB", "V", "VTRS", "WFC", "WTW", "WRB", "ZION"]

Symbols_healthcare = ['A', 'ABBV', 'ABT', 'ALGN', 'AMGN', 'BAX', 'BDX', 'BIIB',
                      'BIO', 'BMY', 'BSX', 'CAH', 'CI', 'CNC', 'COO', 'COR', 'CRL',
                      'CTLT', 'CVS', 'DGX', 'DHR', 'DVA', 'DXCM', 'ELV', 'EW', 'GEHC',
                      'GILD', 'HCA', 'HOLX', 'HSIC', 'HUM', 'IDXX', 'ILMN', 'INCY', 'IQV',
                      'ISRG', 'JNJ', 'LH', 'LLY', 'MCK', 'MDT', 'MOH', 'MRK', 'MRNA', 'MTD',
                      'PFE', 'PODD', 'REGN', 'RMD', 'RVTY', 'STE', 'SYK', 'TECH', 'TFX', 'TMO',
                      'UHS', 'UNH', 'VRTX', 'VTRS', 'WAT', 'WST', 'XRAY', 'ZBH', 'ZTS']

Symbols_utility = ["AES", "AEP", "ATO", "AWK", "CMS", "CNP", "CEG", "D", "DUK",
                   "DTE", "ED", "EIX", "ES", "ETR", "EVRG", "EXC", "FE", "LNT", "NEE",
                   "NI", "NRG", "PCG", "PEG", "PNW", "PPL", "SRE", "SO", "WEC", "XEL"]


# Function to fetch historical stock prices
def get_symbols(symbols, ohlc, begin_date=None, end_date=None):
    out = []
    new_symbols = []
    for symbol in symbols:
        try:
            df = yf.download(symbol, start=begin_date, end=end_date)[ohlc]
            new_symbols.append(symbol)
            out.append(df.astype('float'))
        except KeyError:
            st.warning(f"No data available for symbol: {symbol}. Skipping...")
        except Exception as e:
            st.error(f"An error occurred while fetching data for symbol {symbol}: {e}")
    if not out:
        st.error("No data available for any symbol. Please adjust the date range.")
        return None
    data = pd.concat(out, axis=1)
    data.columns = new_symbols
    data = data.dropna(axis=1)
    return data.dropna(axis=1)


# Function to find cointegrated pairs
def find_cointegrated_pairs(dataframe, cointegration_threshold=0.05, top_n=10):
    n = dataframe.shape[1]
    pvalue_matrix = np.ones((n, n))
    correlation_matrix = np.zeros((n, n))
    keys = dataframe.columns
    pairs = []

    for i in range(n):
        for j in range(i + 1, n):
            stock1 = dataframe[keys[i]]
            stock2 = dataframe[keys[j]]
            result = sm.tsa.stattools.coint(stock1, stock2)
            pvalue = result[1]
            pvalue_matrix[i, j] = pvalue
            correlation = stock1.corr(stock2)
            correlation_matrix[i, j] = correlation
            if pvalue < cointegration_threshold:
                pairs.append(
                    (keys[i], keys[j], pvalue, correlation, stock1, stock2))

    results_df = pd.DataFrame(pairs,
                              columns=['Stock1', 'Stock2', 'P-Value', 'Correlation', 'Stock1_Price', 'Stock2_Price'])

    top_pairs = results_df.nlargest(top_n, 'Correlation')

    return pvalue_matrix, correlation_matrix, top_pairs


# Function to calculate half-life of mean reversion
def half_life(spread):
    spread_lag = spread.shift(1)
    spread_lag.iloc[0] = spread_lag.iloc[1]
    spread_ret = spread - spread_lag
    spread_ret.iloc[0] = spread_ret.iloc[1]
    spread_lag2 = sm.add_constant(spread_lag)
    model = sm.OLS(spread_ret, spread_lag2)
    res = model.fit()
    halflife = int(round(-np.log(2) / res.params[1], 0))
    if halflife <= 0:
        halflife = 1
    return halflife


# Function to backtest the strategy for a pair
def backtest_pair(stock1_price_data, stock2_price_data):
    x = stock1_price_data
    y = stock2_price_data

    df1 = pd.DataFrame({'y': y, 'x': x})
    df1.index = pd.to_datetime(df1.index)
    state_means = KalmanFilterRegression(KalmanFilterAverage(x), KalmanFilterAverage(y))
    df1['hr'] = - state_means[:, 0]
    df1['spread'] = df1.y + (df1.x * df1.hr)

    halflife = half_life(df1['spread'])

    meanSpread = df1.spread.rolling(window=halflife).mean()
    stdSpread = df1.spread.rolling(window=halflife).std()
    df1['zScore'] = (df1.spread - meanSpread) / stdSpread

    entryZscore = 1.5
    exitZscore = -0.05

    df1['long entry'] = ((df1.zScore < -entryZscore) & (df1.zScore.shift(1) > -entryZscore))
    df1['long exit'] = ((df1.zScore > -exitZscore) & (df1.zScore.shift(1) < -exitZscore))
    df1['num units long'] = np.nan
    df1.loc[df1['long entry'], 'num units long'] = 1
    df1.loc[df1['long exit'], 'num units long'] = 0
    df1['num units long'][0] = 0
    df1['num units long'] = df1['num units long'].fillna(method='pad')

    df1['short entry'] = ((df1.zScore > entryZscore) & (df1.zScore.shift(1) < entryZscore))
    df1['short exit'] = ((df1.zScore < exitZscore) & (df1.zScore.shift(1) > exitZscore))
    df1.loc[df1['short entry'], 'num units short'] = -1
    df1.loc[df1['short exit'], 'num units short'] = 0
    df1['num units short'][0] = 0
    df1['num units short'] = df1['num units short'].fillna(method='pad')

    df1['numUnits'] = df1['num units long'] + df1['num units short']
    df1['spread pct ch'] = (df1['spread'] - df1['spread'].shift(1)) / ((df1['x'] * abs(df1['hr'])) + df1['y'])
    df1['port rets'] = df1['spread pct ch'] * df1['numUnits'].shift(1)
    df1['cum rets'] = df1['port rets'].cumsum()
    df1['cum rets'] = df1['cum rets'] + 1

    try:
        sharpe = ((df1['port rets'].mean() / df1['port rets'].std()) * sqrt(252))
    except ZeroDivisionError:
        sharpe = 0.0

    start_val = 1
    end_val = df1['cum rets'].iat[-1]
    start_date = df1.index[0]
    end_date = df1.index[-1]
    days = (end_date - start_date).days
    CAGR = (end_val / start_val) ** (252.0 / days) - 1

    num_trades_long = 0
    num_trades_short = 0

    for i in range(1, len(df1)):
        if df1['long entry'].iloc[i] and not df1['long entry'].iloc[i - 1]:
            num_trades_long += 1
        elif df1['short entry'].iloc[i] and not df1['short entry'].iloc[i - 1]:
            num_trades_short += 1

    total_trades = num_trades_long + num_trades_short

    # Calculate average hedge ratio for display purposes
    average_hedge_ratio = df1['hr'].mean()

    return {
        'cum_rets': df1['cum rets'],
        'sharpe': sharpe,
        'CAGR': CAGR,
        'num_trades': total_trades,
        'halflife': halflife,
        'entryZscore': entryZscore,
        'exitZscore': exitZscore,
        'average_hedge_ratio': average_hedge_ratio,  # Include hedge ratio in the return
    }


# Kalman filter average
def KalmanFilterAverage(x):
    kf = KalmanFilter(dim_x=1, dim_z=1)
    kf.x = np.array([0.])
    kf.F = np.array([[1.]])
    kf.H = np.array([[1.]])
    kf.P *= 1000.
    kf.R = 5
    kf.Q = np.array([[0.1]])

    means = []
    for measurement in x:
        kf.predict()
        kf.update(np.array([measurement]))
        means.append(kf.x[0])
    return np.array(means)


# Kalman filter regression
def KalmanFilterRegression(x, y):
    delta = 1e-3
    kf = KalmanFilter(dim_x=2, dim_z=1)
    kf.x = np.array([0., 0.])
    kf.F = np.eye(2)
    kf.H = np.array([[0., 1.]])
    kf.P *= 1000.
    kf.R = 5
    kf.Q = np.array([[delta, 0], [0, delta]])

    means = []
    for i in range(len(x)):
        kf.H = np.array([[x[i], 1.]])
        kf.predict()
        kf.update(np.array([y[i]]))
        means.append(kf.x.copy())
    return np.array(means)


# Streamlit application setup
st.title('Pairs Trading Strategy Backtester')

# Main page parameter settings with dropdown menu
sector_options = ['Energy', 'Financial', 'Healthcare', 'Utility']
sector = st.selectbox('Select Sector', options=sector_options)
cointegration_threshold = st.slider('Cointegration Threshold', 0.01, 0.5, 0.05, 0.01)
top_n_pairs = st.slider('Top N Pairs', 5, 50, 10, 5)
start_date = st.date_input('Start Date', value=pd.to_datetime('2023-01-01'))
end_date = st.date_input('End Date', value=pd.to_datetime('2023-12-31'))

# Mapping sector selection to corresponding symbols
if sector == 'Healthcare':
    symbols = Symbols_healthcare
elif sector == 'Energy':
    symbols = Symbols_energy
elif sector == 'Utility':
    symbols = Symbols_utility
else:  # Default to Financial if none of the above
    symbols = Symbols_financial

df = get_symbols(symbols, 'Adj Close', begin_date=start_date, end_date=end_date)

# Find cointegrated pairs
pvalue_matrix, correlation_matrix, top_pairs = find_cointegrated_pairs(df,
                                                                       cointegration_threshold=cointegration_threshold,
                                                                       top_n=top_n_pairs)

# Display top N cointegrated pairs
st.subheader(f'Top {top_n_pairs} Cointegrated Pairs')
for i, pair in enumerate(top_pairs.iterrows(), start=1):
    stock1, stock2, pvalue, correlation, stock1_price_data, stock2_price_data = pair[1]
    pair_id = f"{stock1.lower()}-{stock2.lower()}"
    st.write(f"{i}. **Pair:** {stock1} - {stock2}, **P-Value:** {pvalue:.4f}, **Correlation:** {correlation:.4f}")
    st.write(f"[*Analyze Pair*](#{pair_id})")
    st.write('---')

# Display detailed analysis for each pair
for pair in top_pairs.iterrows():
    stock1, stock2, pvalue, correlation, stock1_price_data, stock2_price_data = pair[1]
    pair_id = f"{stock1.lower()}-{stock2.lower()}"
    st.write(f'<h2 id="{pair_id}">{stock1} - {stock2}</h2>', unsafe_allow_html=True)
    st.write(f"**Pair:** {stock1} - {stock2}")
    st.write(f"**P-Value:** {pvalue:.4f}")
    st.write(f"**Correlation:** {correlation:.4f}")

    # Backtest the pair and display results
    backtest_results = backtest_pair(stock1_price_data, stock2_price_data)
    st.write(f"**Cumulative Returns:** {backtest_results['cum_rets'].iat[-1]:.2f}")
    st.write(f"**Sharpe Ratio:** {backtest_results['sharpe']:.2f}")
    st.write(f"**CAGR:** {backtest_results['CAGR']:.2%}")
    st.write(f"**Number of Trades:** {backtest_results['num_trades']}")
    st.write(f"**Half-Life:** {backtest_results['halflife']}")
    st.write(f"**Entry Z-Score:** {backtest_results['entryZscore']}")
    st.write(f"**Exit Z-Score:** {backtest_results['exitZscore']}")
    st.write(f"**Average Hedge Ratio:** {backtest_results['average_hedge_ratio']:.2f}")  # Display hedge ratio

    # Plot spread and z-score graph
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=stock1_price_data.index, y=stock1_price_data.values, mode='lines', name=stock1))
    fig.add_trace(go.Scatter(x=stock2_price_data.index, y=stock2_price_data.values, mode='lines', name=stock2))
    fig.update_layout(title='Stock Prices', xaxis_title='Date', yaxis_title='Price')
    st.plotly_chart(fig)
    st.write('---')
