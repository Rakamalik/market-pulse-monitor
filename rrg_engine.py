import psycopg2
import pandas as pd
import numpy as np

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
    "BMRI.JK", "BNGA.JK", "BRIS.JK", "BRPT.JK", "BSDE.JK",
    "BUKA.JK", "BYAN.JK", "CPIN.JK", "CTRA.JK", "EMTK.JK",
    "ESSA.JK", "EXCL.JK", "GOTO.JK", "HRUM.JK", "ICBP.JK",
    "INCO.JK", "INDF.JK", "INKP.JK", "INTP.JK", "ITMG.JK",
    "JSMR.JK", "KLBF.JK", "MAPI.JK", "MBMA.JK", "MDKA.JK",
    "MEDC.JK", "MIKA.JK", "MYOR.JK", "PGAS.JK", "PGEO.JK",
    "PTBA.JK", "PTPP.JK", "SIDO.JK", "SMGR.JK", "SRTG.JK",
    "TBIG.JK", "TKIM.JK", "TLKM.JK", "TPIA.JK", "UNTR.JK",
    "UNVR.JK", "WIKA.JK",
]

BENCHMARK = "^JKLQ45"

WMA_PERIOD = 10
MOMENTUM_LOOKBACK = 10
TAIL_LENGTH = 12
NORMALIZE_WINDOW = 100
NORMALIZE_MIN_PERIODS = 20


def get_data(ticker):
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql(
        "SELECT date, open, high, low, close, volume FROM ohlcv WHERE ticker=%s ORDER BY date",
        conn, params=(ticker,)
    )
    conn.close()
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    return df


def wma(series, period):
    weights = np.arange(1, period + 1)
    return series.rolling(period).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )


def calculate_rs_ratio_momentum(ticker_close, benchmark_close):
    df = pd.DataFrame({
        'ticker': ticker_close,
        'benchmark': benchmark_close
    }).dropna()

    if len(df) < (WMA_PERIOD * 2 + MOMENTUM_LOOKBACK + NORMALIZE_MIN_PERIODS):
        return pd.DataFrame()

    rs_raw = (df['ticker'] / df['benchmark']) * 100
    rs_smooth1 = wma(rs_raw, WMA_PERIOD)
    rs_ratio_raw = wma(rs_smooth1, WMA_PERIOD)

    # Normalisasi: re-center ke 100 berdasarkan rata-rata historis sendiri
    rs_ratio_mean = rs_ratio_raw.rolling(NORMALIZE_WINDOW, min_periods=NORMALIZE_MIN_PERIODS).mean()
    rs_ratio = (rs_ratio_raw / rs_ratio_mean) * 100

    rs_momentum = (rs_ratio / rs_ratio.shift(MOMENTUM_LOOKBACK)) * 100

    out = pd.DataFrame({'x': rs_ratio, 'y': rs_momentum}).dropna()
    return out


def calculate_rrg_multi(tickers, benchmark_ticker=BENCHMARK):
    try:
        bm = get_data(benchmark_ticker)
    except Exception:
        return {}

    if bm.empty:
        return {}

    final = {}
    for ticker in tickers:
        try:
            df = get_data(ticker)
            if df.empty:
                continue

            result = calculate_rs_ratio_momentum(df['close'], bm['close'])
            if result.empty:
                continue

            final[ticker] = result.tail(TAIL_LENGTH)
        except Exception:
            continue

    return final


def calculate_rrg(ticker, benchmark_df=None):
    result = calculate_rrg_multi([ticker])
    if ticker in result:
        return result[ticker]
    return pd.DataFrame()


def run_rrg():
    results = calculate_rrg_multi(TICKERS)
    for ticker, df in results.items():
        if not df.empty:
            latest = df.iloc[-1]
            print(f"{ticker}: X={latest['x']:.2f}, Y={latest['y']:.2f}")
    return {t: df.to_dict('records') for t, df in results.items()}


if __name__ == "__main__":
    run_rrg()
