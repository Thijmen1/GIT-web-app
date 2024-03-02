import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import statsmodels.api as sm
from filterpy.kalman import KalmanFilter
from math import sqrt
import plotly.graph_objects as go
import warnings

# Set display options and ignore warnings
pd.set_option('display.max_columns', None)
warnings.filterwarnings('ignore')

# Define stock symbols for different sectors
Symbols_healthcare = ['A', 'ABBV', 'ABT', 'ALGN', 'AMGN', 'BAX', 'BDX', 'BIIB',
                      'BIO', 'BMY', 'BSX', 'CAH', 'CI', 'CNC', 'COO', 'COR', 'CRL',
                      'CTLT', 'CVS', 'DGX', 'DHR', 'DVA', 'DXCM', 'ELV', 'EW', 'GEHC',
                      'GILD', 'HCA', 'HOLX', 'HSIC', 'HUM', 'IDXX', 'ILMN', 'INCY', 'IQV',
                      'ISRG', 'JNJ', 'LH', 'LLY', 'MCK', 'MDT', 'MOH', 'MRK', 'MRNA', 'MTD',
                      'PFE', 'PODD', 'REGN', 'RMD', 'RVTY', 'STE', 'SYK', 'TECH', 'TFX', 'TMO',
                      'UHS', 'UNH', 'VRTX', 'VTRS', 'WAT', 'WST', 'XRAY', 'ZBH', 'ZTS']

Symbols_energy = ["APA", "BKR", "COP", "CTRA", "CVX", "DVN", "EOG", "EQT", "FANG",
                  "HAL", "HES", "KMI", "MPC", "MRO", "OKE", "OXY", "PSX", "PXD", "SLB",
                  "TRGP", "VLO", "WMB", "XOM"]

Symbols_utility = ["AES", "AEP", "ATO", "AWK", "CMS", "CNP", "CEG", "D", "DUK",
                   "DTE", "ED", "EIX", "ES", "ETR", "EVRG", "EXC", "FE", "LNT", "NEE",
                   "NI", "NRG", "PCG", "PEG", "PNW", "PPL", "SRE", "SO", "WEC", "XEL"]

Symbols_financial = ["ACGL", "AFL", "AIG", "AIZ", "AJG", "ALL", "AMP", "AON",
                     "AXP", "BAC", "BEN", "BK", "BLK", "BRK.B", "BRO", "BX", "C",
                     "CB", "CBOE", "CFG", "CINF", "CMA", "CME", "COF", "DFS", "EG",
                     "FDS", "FI", "FIS", "FITB", "FLT", "GL", "GPN", "GS", "HBAN", "HIG",
                     "ICE", "IVZ", "JPM", "JKHY", "KEY", "L", "MA", "MCO", "MET", "MKTX",
                     "MMC", "MSCI", "MS", "MTB", "NDAQ", "NTRS", "PFG", "PGR", "PNC",
                     "PRU", "PYPL", "RF", "RJF", "SCHW", "SPGI", "STT", "SYF", "TFC",
                     "TROW", "TRV", "USB", "V", "VTRS", "WFC", "WTW", "WRB", "ZION"]

# Function to fetch historical stock prices
def get_symbols(symbols, ohlc, begin_date=None, end_date=None):
    out = []
    new_symbols = []
    for symbol in symbols:
        # Check if data is available for the symbol
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
    n = dataframe.shape[1]  # the length of the dataframe
    pvalue_matrix = np.ones((n, n))  # initialize the matrix of p-values
    correlation_matrix = np.zeros((n, n))  # initialize the matrix of correlation
    keys = dataframe.columns  # get the column names
    pairs = []  # initialize the list for cointegration pairs

    for i in range(n):
        for j in range(i + 1, n):  # for j bigger than i
            stock1 = dataframe[keys[i]]  # obtain the price of "stock1"
            stock2 = dataframe[keys[j]]  # obtain the price of "stock2"

            # Test for cointegration and get the result
            result = sm.tsa.stattools.coint(stock1, stock2)
            pvalue = result[1]  # get the p-value
            pvalue_matrix[i, j] = pvalue

            # Calculate correlation
            correlation = stock1.corr(stock2)
            correlation_matrix[i, j] = correlation

            if pvalue < cointegration_threshold:  # if p-value less than the cointegration threshold
                pairs.append(
                    (keys[i], keys[j], pvalue, correlation, stock1, stock2))  # add all data to pairs

    # Create a DataFrame to store the results
    results_df = pd.DataFrame(pairs,
                              columns=['Stock1', 'Stock2', 'P-Value', 'Correlation', 'Stock1_Price', 'Stock2_Price'])

    # Select the top N cointegrating pairs based on level of correlation i.e high to low
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

    # Run regression (including Kalman Filter) to find hedge ratio and then create spread series
    df1 = pd.DataFrame({'y': y, 'x': x})
    df1.index = pd.to_datetime(df1.index)
    state_means = KalmanFilterRegression(KalmanFilterAverage(x), KalmanFilterAverage(y))
    df1['hr'] = - state_means[:, 0]
    df1['spread'] = df1.y + (df1.x * df1.hr)

    # Calculate half life
    halflife = half_life(df1['spread'])

    # Calculate z-score with a window = half life period i.e no forward bias.
    meanSpread = df1.spread.rolling(window=halflife).mean()
    stdSpread = df1.spread.rolling(window=halflife).std()
    df1['zScore'] = (df1.spread - meanSpread) / stdSpread

    # Trading thresholds
    entryZscore = 1.5
    exitZscore = -0.05

    # Set up num units long
    df1['long entry'] = ((df1.zScore < -entryZscore) & (df1.zScore.shift(1) > -entryZscore))
    df1['long exit'] = ((df1.zScore > -exitZscore) & (df1.zScore.shift(1) < -exitZscore))
    df1['num units long'] = np.nan
    df1.loc[df1['long entry'], 'num units long'] = 1
    df1.loc[df1['long exit'], 'num units long'] = 0
    df1['num units long'][0] = 0
    df1['num units long'] = df1['num units long'].fillna(method='pad')

    # Set up num units short
    df1['short entry'] = ((df1.zScore > entryZscore) & (df1.zScore.shift(1) < entryZscore))
    df1['short exit'] = ((df1.zScore < exitZscore) & (df1.zScore.shift(1) > exitZscore))
    df1.loc[df1['short entry'], 'num units short'] = -1
    df1.loc[df1['short exit'], 'num units short'] = 0
    df1['num units short'][0] = 0
    df1['num units short'] = df1['num units short'].fillna(method='pad')

    # Set up totals: num units and returns
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

    # Initialize trade counters
    num_trades_long = 0
    num_trades_short = 0

    # Count trades in the same loop
    for i in range(1, len(df1)):
        if df1['long entry'].iloc[i] and not df1['long entry'].iloc[i - 1]:
            num_trades_long += 1
        elif df1['short entry'].iloc[i] and not df1['short entry'].iloc[i - 1]:
            num_trades_short += 1

    # Calculate total number of trades
    total_trades = num_trades_long + num_trades_short

    return {
        'cum_rets': df1['cum rets'],
        'sharpe': sharpe,
        'CAGR': CAGR,
        'num_trades': total_trades,
        'halflife': halflife,
        'entryZscore': entryZscore,
        'exitZscore': exitZscore
    }


# Kalman filter average
def KalmanFilterAverage(x):
    kf = KalmanFilter(dim_x=1, dim_z=1)
    kf.x = np.array([0.])  # Initial state
    kf.F = np.array([[1.]])  # State transition matrix
    kf.H = np.array([[1.]])  # Measurement function
    kf.P *= 1000.  # Covariance matrix
    kf.R = 5  # State uncertainty
    kf.Q = np.array([[0.1]])  # Process uncertainty, adjusted for one-dimensional system

    means = []
    for measurement in x:
        kf.predict()
        kf.update(np.array([measurement]))
        means.append(kf.x[0])
    return np.array(means)


# Kalman filter regression
def KalmanFilterRegression(x, y):
    delta = 1e-3  # Small value representing process noise variance
    kf = KalmanFilter(dim_x=2, dim_z=1)
    kf.x = np.array([0., 0.])  # Initial state (e.g., slope and intercept for linear regression)
    kf.F = np.eye(2)  # State transition matrix
    kf.H = np.array([[0., 1.]])  # Measurement function initialized
    kf.P *= 1000.  # Initial covariance matrix
    kf.R = 5  # Measurement noise
    kf.Q = np.array([[delta, 0],  # Process noise for the slope
                     [0,

 delta]])  # Process noise for the intercept

    means = []
    for i in range(len(x)):
        kf.H = np.array([[x[i], 1.]])  # Update measurement function for each observation
        kf.predict()
        kf.update(np.array([y[i]]))
        means.append(kf.x.copy())
    return np.array(means)  # Return the entire state estimate array


# Streamlit application
st.title('Pairs Trading Strategy Backtester')

# Sidebar
st.sidebar.header('Parameters')
sector = st.sidebar.radio('Select Sector', ('Healthcare', 'Energy', 'Utility', 'Financial'))
cointegration_threshold = st.sidebar.slider('Cointegration Threshold', 0.01, 0.5, 0.05, 0.01)
top_n_pairs = st.sidebar.slider('Top N Pairs', 5, 50, 10, 5)
start_date = st.sidebar.date_input('Start Date', value=pd.to_datetime('2023-01-01'))
end_date = st.sidebar.date_input('End Date', value=pd.to_datetime('2023-12-31'))

# Fetch data for selected sector
if sector == 'Healthcare':
    symbols = Symbols_healthcare
elif sector == 'Energy':
    symbols = Symbols_energy
elif sector == 'Utility':
    symbols = Symbols_utility
else:
    symbols = Symbols_financial

df = get_symbols(symbols, 'Adj Close', begin_date=start_date, end_date=end_date)

# Find cointegrated pairs
pvalue_matrix, correlation_matrix, top_pairs = find_cointegrated_pairs(df, cointegration_threshold=cointegration_threshold,
                                                                       top_n=top_n_pairs)

# Display cointegration matrix
cointegration_df = pd.DataFrame(pvalue_matrix, index=df.columns, columns=df.columns)
with st.expander("Cointegration Matrix"):
    st.write(cointegration_df)

# Display correlation matrix
correlation_df = pd.DataFrame(correlation_matrix, columns=df.columns, index=df.columns)
with st.expander("Correlation Matrix"):
    st.write(correlation_df)

# Display top N cointegrated pairs
st.subheader(f'Top {top_n_pairs} Cointegrated Pairs')

# Show the pairs with a link to more detailed analysis
for i, pair in enumerate(top_pairs.iterrows(), start=1):
    stock1, stock2, pvalue, correlation, stock1_price_data, stock2_price_data = pair[1]
    st.write(f"{i}. **Pair:** {stock1} - {stock2}, **P-Value:** {pvalue:.4f}, **Correlation:** {correlation:.4f}")
    st.write(f"[*Analyze Pair*](#{stock1}_{stock2})")
    st.write('---')

# Display detailed analysis for each pair
for pair in top_pairs.iterrows():
    stock1, stock2, _, _, stock1_price_data, stock2_price_data = pair[1]
    st.write(f'<h2 id="{stock1}_{stock2}">{stock1} - {stock2}</h2>', unsafe_allow_html=True)
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

    # Plot spread and z-score graph
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=stock1_price_data.index, y=stock1_price_data.values, mode='lines', name=stock1))
    fig.add_trace(go.Scatter(x=stock2_price_data.index, y=stock2_price_data.values, mode='lines', name=stock2))
    fig.update_layout(title='Stock Prices', xaxis_title='Date', yaxis_title='Price')
    st.plotly_chart(fig)
    st.write('---')
