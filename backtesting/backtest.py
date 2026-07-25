import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime

DB_CONFIG = {
    "host": "172.18.0.2",
    "database": "devopsdb",
    "user": "devops",
    "password": "password",
    "port": 5432
}

def get_ohlcv(ticker):
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql(
        "SELECT date, open, high, low, close, volume FROM ohlcv WHERE ticker=%s ORDER BY date",
        conn, params=(ticker,)
    )
    conn.close()
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    return df

def get_rrg_signals(ticker, benchmark="^JKSE"):
    """
    Generate RRG signals historis:
    IMPROVING → potential entry
    LEADING   → hold
    WEAKENING → potential exit
    LAGGING   → avoid
    """
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql(
        "SELECT date, close, high, low, volume FROM ohlcv WHERE ticker=%s ORDER BY date",
        conn, params=(ticker,)
    )
    bm = pd.read_sql(
        "SELECT date, close FROM ohlcv WHERE ticker=%s ORDER BY date",
        conn, params=(benchmark,)
    )
    conn.close()

    df['date'] = pd.to_datetime(df['date'])
    bm['date'] = pd.to_datetime(bm['date'])
    df = df.set_index('date')
    bm = bm.set_index('date')

    # Hitung RS Ratio (Sumbu X)
    rs = df['close'] / bm['close']
    ema_rs = rs.ewm(span=14).mean()
    x_raw = ema_rs
    x_zscore = (x_raw - x_raw.mean()) / x_raw.std()
    x = x_zscore * 10 + 100

    # Hitung ATR
    df['h_l'] = df['high'] - df['low']
    df['atr'] = df['h_l'].rolling(14).mean()

    # Hitung Emotional Momentum (Sumbu Y)
    rvol = df['volume'] / df['volume'].rolling(20).mean()
    atr_roc = (df['atr'] - df['atr'].shift(5)) / df['atr'].shift(5)
    emotional = rvol * atr_roc
    y_zscore = (emotional - emotional.mean()) / emotional.std()
    y = y_zscore * 10 + 100

    # Classify kuadran
    signals = pd.DataFrame({'x': x, 'y': y, 'close': df['close']}).dropna()
    
    def classify(row):
        if row['x'] >= 100 and row['y'] >= 100: return 'LEADING'
        if row['x'] >= 100 and row['y'] < 100: return 'WEAKENING'
        if row['x'] < 100 and row['y'] >= 100: return 'IMPROVING'
        return 'LAGGING'
    
    signals['quadrant'] = signals.apply(classify, axis=1)
    return signals

def backtest(ticker, strategy="improving_to_leading", initial_capital=10_000_000):
    """
    Strategy: beli saat IMPROVING, jual saat WEAKENING
    """
    signals = get_rrg_signals(ticker)
    
    capital = initial_capital
    position = 0
    trades = []
    equity_curve = []

    prev_quadrant = None

    for date, row in signals.iterrows():
        quadrant = row['quadrant']
        price = row['close']

        # Entry: IMPROVING → beli
        if prev_quadrant != 'IMPROVING' and quadrant == 'IMPROVING' and position == 0:
            shares = int(capital / price / 100) * 100  # lot = 100 lembar
            if shares > 0:
                cost = shares * price
                capital -= cost
                position = shares
                trades.append({
                    'date': date,
                    'action': 'BUY',
                    'price': price,
                    'shares': shares,
                    'capital': capital
                })

        # Exit: WEAKENING → jual
        elif quadrant == 'WEAKENING' and position > 0:
            proceeds = position * price
            capital += proceeds
            trades.append({
                'date': date,
                'action': 'SELL',
                'price': price,
                'shares': position,
                'capital': capital
            })
            position = 0

        # Mark to market
        portfolio_value = capital + (position * price)
        equity_curve.append({
            'date': date,
            'value': portfolio_value,
            'quadrant': quadrant
        })

        prev_quadrant = quadrant

    # Liquidate jika masih ada posisi
    if position > 0:
        last_price = signals['close'].iloc[-1]
        capital += position * last_price
        position = 0

    # Metrics
    equity_df = pd.DataFrame(equity_curve).set_index('date')
    trades_df = pd.DataFrame(trades)

    total_return = (capital - initial_capital) / initial_capital * 100
    
    # Max drawdown
    rolling_max = equity_df['value'].cummax()
    drawdown = (equity_df['value'] - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min()

    # Win rate
    if len(trades_df) >= 2:
        buy_trades = trades_df[trades_df['action'] == 'BUY']['price'].values
        sell_trades = trades_df[trades_df['action'] == 'SELL']['price'].values
        min_len = min(len(buy_trades), len(sell_trades))
        if min_len > 0:
            wins = sum(sell_trades[:min_len] > buy_trades[:min_len])
            win_rate = wins / min_len * 100
        else:
            win_rate = 0
    else:
        win_rate = 0

    total_trades = len(trades_df[trades_df['action'] == 'BUY']) if len(trades_df) > 0 else 0

    print(f"\n{'='*40}")
    print(f"BACKTEST RESULT — {ticker}")
    print(f"{'='*40}")
    print(f"Strategy    : IMPROVING → LEADING → WEAKENING")
    print(f"Period      : {signals.index[0].date()} → {signals.index[-1].date()}")
    print(f"Capital     : Rp {initial_capital:,.0f}")
    print(f"Final Value : Rp {capital:,.0f}")
    print(f"Return      : {total_return:.2f}%")
    print(f"Max Drawdown: {max_drawdown:.2f}%")
    print(f"Total Trades: {total_trades}")
    print(f"Win Rate    : {win_rate:.1f}%")
    print(f"{'='*40}")

    return {
        "ticker": ticker,
        "total_return": total_return,
        "max_drawdown": max_drawdown,
        "total_trades": total_trades,
        "win_rate": win_rate,
        "equity_curve": equity_df,
        "trades": trades_df
    }

if __name__ == "__main__":
    # Test beberapa ticker
    tickers = ["BBCA.JK", "BBRI.JK", "ASII.JK", "TLKM.JK", "ADRO.JK"]
    results = []
    
    for ticker in tickers:
        try:
            result = backtest(ticker)
            results.append(result)
        except Exception as e:
            print(f"Error {ticker}: {e}")
    
    # Summary
    print(f"\n{'='*40}")
    print("SUMMARY ALL TICKERS")
    print(f"{'='*40}")
    for r in results:
        print(f"{r['ticker']:<12} Return: {r['total_return']:>7.2f}%  "
              f"Drawdown: {r['max_drawdown']:>7.2f}%  "
              f"Trades: {r['total_trades']:>3}  "
              f"WinRate: {r['win_rate']:>5.1f}%")
