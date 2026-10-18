import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Pine Script Backtester", layout="wide")
st.title("📈 Pine Script Backtester (Mobile)")

# Controls
st.sidebar.header("Configuration")
ticker = st.sidebar.text_input("Ticker Symbol", value="AAPL")
timeframe = st.sidebar.selectbox("Interval", options=["1d", "1h", "15m", "5m"], index=0)
period = st.sidebar.selectbox("Period", options=["1mo", "3mo", "6mo", "1y", "2y"], index=3)

pine_code = st.text_area("Pine Script Logic:", height=150, value="""//@version=5
strategy("SMA Cross", overlay=true)
smaFast = ta.sma(close, 14)
smaSlow = ta.sma(close, 28)
longCondition = ta.crossover(smaFast, smaSlow)
if (longCondition)
    strategy.entry("Long", strategy.long)
""")

def run_backtest():
    with st.spinner("Calculating..."):
        try:
            data = yf.download(ticker, period=period, interval=timeframe, progress=False)
            if data.empty:
                st.error("No data found for this symbol.")
                return

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [col[0] for col in data.columns]

            df = data.copy()
            df['SMA14'] = df['Close'].rolling(window=14).mean()
            df['SMA28'] = df['Close'].rolling(window=28).mean()
            
            df['Signal'] = np.where(df['SMA14'] > df['SMA28'], 1, 0)
            df['Position'] = df['Signal'].diff()

            trades = []
            position = 0
            buy_price = 0.0

            for idx, row in df.iterrows():
                if row['Position'] == 1 and position == 0:
                    position = 1
                    buy_price = float(row['Close'])
                elif row['Position'] == -1 and position == 1:
                    position = 0
                    sell_price = float(row['Close'])
                    pnl = ((sell_price - buy_price) / buy_price) * 100
                    trades.append({'Date': idx, 'Buy': buy_price, 'Sell': sell_price, 'PnL%': pnl})

            trades_df = pd.DataFrame(trades)
            total_trades = len(trades_df)
            win_rate = (len(trades_df[trades_df['PnL%'] > 0]) / total_trades * 100) if total_trades > 0 else 0
            total_pnl = trades_df['PnL%'].sum() if total_trades > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Trades", total_trades)
            col2.metric("Win Rate", f"{win_rate:.1f}%")
            col3.metric("Total PnL", f"{total_pnl:.2f}%")

            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA14'], line=dict(color='orange'), name='SMA 14'))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA28'], line=dict(color='blue'), name='SMA 28'))
            fig.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            if not trades_df.empty:
                st.dataframe(trades_df.tail(10), use_container_width=True)

        except Exception as e:
            st.error(f"Error: {e}")

if st.button("🚀 Run Backtest", use_container_width=True):
    run_backtest()
          
