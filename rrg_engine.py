import psycopg2
import pandas as pd
import numpy as np
import os

DB_CONFIG = {
    "host": "172.18.0.2",
    "database": "devopsdb",
    "user": "devops",
    "password": "password",
    "port": 5432
}

TICKERS = [
    "ACES.JK", "ADRO.JK", "AKRA.JK", "AMRT.JK", "ANTM.JK",
    "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BBTN.JK",
    "BIKA.JK", "BMRI.JK", "BNGA.JK", "BRIS.JK", "BRPT.JK",
    "BSDE.JK", "BUKA.JK", "BYAN.JK", "CPIN.JK", "CTRA.JK",
    "EMTK.JK", "ESSA.JK", "EXCL.JK", "GOTO.JK", "HRUM.JK",
    "ICBP.JK", "INCO.JK", "INDF.JK", "INKP.JK", "INTP.JK",
    "ITMG.JK", "JSMR.JK", "KLBF.JK", "MAPI.JK", "MBMA.JK",
    "MDKA.JK", "MEDC.JK", "MIKA.JK", "MYOR.JK", "PGAS.JK",
    "PGEO.JK", "PTBA.JK", "PTPP.JK", "SIDO.JK", "SMGR.JK",
    "SRTG.JK", "TBIG.JK", "TKIM.JK", "TLKM.JK", "TPIA.JK",
    "UNTR.JK", "UNVR.JK", "WIKA.JK",
]
BENCHMARK = "^JKSE"

def get_data(ticker):
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql(
        "SELECT date, close, high, low, volume FROM ohlcv WHERE ticker=%s ORDER BY date",
        conn, params=(ticker,)
    )
    conn.close()
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    return df

def calculate_atr(df, period=14):
    df['h_l'] = df['high'] - df['low']
    df['atr'] = df['h_l'].rolling(period).mean()
    return df

def calculate_rrg(ticker, benchmark_df):
    df = get_data(ticker)
    df = calculate_atr(df)

    # Sumbu X — RS Ratio
    rs = df['close'] / benchmark_df['close']
    ema_rs = rs.ewm(span=14).mean()
    x_raw = ema_rs.dropna()
    x_zscore = (x_raw - x_raw.mean()) / x_raw.std()
    x = x_zscore * 10 + 100

    # Sumbu Y — Emotional Momentum
    rvol = df['volume'] / df['volume'].rolling(20).mean()
    atr_roc = (df['atr'] - df['atr'].shift(5)) / df['atr'].shift(5)
    emotional = rvol * atr_roc
    emotional = emotional.dropna()
    y_zscore = (emotional - emotional.mean()) / emotional.std()
    y = y_zscore * 10 + 100

    # Ambil 10 hari terakhir untuk tail
    common_idx = x.index.intersection(y.index)
    tail = pd.DataFrame({'x': x[common_idx], 'y': y[common_idx]}).tail(10)

    return tail

def run_rrg():
    benchmark_df = get_data(BENCHMARK)
    results = {}

    for ticker in TICKERS:
        try:
            tail = calculate_rrg(ticker, benchmark_df)
            results[ticker] = tail.to_dict('records')
            latest = tail.iloc[-1]
            print(f"{ticker}: X={latest['x']:.2f}, Y={latest['y']:.2f}")
        except Exception as e:
            print(f"Error {ticker}: {e}")

    return results

if __name__ == "__main__":
    run_rrg()
