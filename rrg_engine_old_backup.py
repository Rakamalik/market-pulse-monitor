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

def cross_sectional_zscore(series_dict, date):
    """Z-score terhadap semua saham pada tanggal yang sama"""
    values = {k: v.get(date, np.nan) for k, v in series_dict.items()}
    vals = pd.Series(values).dropna()
    if len(vals) < 2:
        return values
    mean, std = vals.mean(), vals.std()
    if std == 0:
        return {k: 0 for k in values}
    return {k: (v - mean) / std if not np.isnan(v) else np.nan 
            for k, v in values.items()}

def calculate_rrg_multi(tickers, benchmark_ticker=BENCHMARK):
    """Hitung RRG untuk semua ticker sekaligus — cross-sectional Z-score"""
    
    # Load benchmark
    bm = get_data(benchmark_ticker)
    bm_return20 = bm['close'].pct_change(20)
    
    # Load semua ticker
    ticker_data = {}
    for ticker in tickers:
        try:
            df = get_data(ticker)
            if len(df) < 25:
                continue
            ticker_data[ticker] = df
        except:
            continue
    
    if not ticker_data:
        return {}
    
    # Hitung metrik per ticker
    rr_series = {}      # Excess return untuk X
    rvol_series = {}    # Relative volume untuk Y
    absret_series = {}  # |Return| untuk Y
    natr_series = {}    # NATR untuk Y
    clv_series = {}     # CLV untuk Y

    for ticker, df in ticker_data.items():
        # Sumbu X — Excess Return (20 hari)
        ret20 = df['close'].pct_change(20)
        rr = ret20 - bm_return20.reindex(ret20.index)
        rr_ema = rr.ewm(span=10).mean()
        rr_series[ticker] = rr_ema

        # Sumbu Y — Emotion composite
        rvol = df['volume'] / df['volume'].rolling(20).mean()
        rvol_series[ticker] = rvol

        abs_ret = df['close'].pct_change().abs()
        absret_series[ticker] = abs_ret

        atr = (df['high'] - df['low']).rolling(14).mean()
        natr = atr / df['close'] * 100
        natr_series[ticker] = natr

        clv = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'] + 1e-10)
        clv_series[ticker] = clv

    # Ambil semua tanggal yang tersedia
    all_dates = sorted(set.intersection(*[set(s.index) for s in rr_series.values()]))
    
    # Hitung cross-sectional Z-score per tanggal
    results = {ticker: [] for ticker in rr_series.keys()}
    
    for date in all_dates:
        # X values pada tanggal ini
        x_vals = {t: rr_series[t].get(date, np.nan) for t in rr_series}
        x_vals_clean = pd.Series(x_vals).dropna()
        if len(x_vals_clean) < 2:
            continue
        x_mean, x_std = x_vals_clean.mean(), x_vals_clean.std()

        # Y composite pada tanggal ini
        for ticker in rr_series:
            try:
                # X
                x_raw = rr_series[ticker].get(date, np.nan)
                if np.isnan(x_raw) or x_std == 0:
                    continue
                x = 100 + 12 * (x_raw - x_mean) / x_std

                # Y — composite emotion
                rv = rvol_series[ticker].get(date, np.nan)
                ar = absret_series[ticker].get(date, np.nan)
                nt = natr_series[ticker].get(date, np.nan)
                cl = clv_series[ticker].get(date, np.nan)

                if any(np.isnan(v) for v in [rv, ar, nt, cl]):
                    continue

                # Cross-sectional Z untuk Y components
                def cs_z(series_dict, d):
                    vals = pd.Series({t: series_dict[t].get(d, np.nan) 
                                     for t in series_dict}).dropna()
                    if len(vals) < 2 or vals.std() == 0:
                        return np.nan
                    return (series_dict[series_dict.__class__({}).get(ticker, ticker)].get(d, np.nan) - vals.mean()) / vals.std()

                rv_vals = pd.Series({t: rvol_series[t].get(date, np.nan) for t in rvol_series}).dropna()
                ar_vals = pd.Series({t: absret_series[t].get(date, np.nan) for t in absret_series}).dropna()
                nt_vals = pd.Series({t: natr_series[t].get(date, np.nan) for t in natr_series}).dropna()
                cl_vals = pd.Series({t: clv_series[t].get(date, np.nan) for t in clv_series}).dropna()

                def zs(val, series):
                    if series.std() == 0: return 0
                    return (val - series.mean()) / series.std()

                emotion = (0.35 * zs(rv, rv_vals) +
                          0.25 * zs(ar, ar_vals) +
                          0.20 * zs(nt, nt_vals) +
                          0.20 * zs(cl, cl_vals))

                y = 100 + 12 * emotion

                results[ticker].append({'date': date, 'x': x, 'y': y})
            except:
                continue

    # Ambil 25 hari terakhir per ticker
    final = {}
    for ticker, data in results.items():
        if len(data) >= 5:
            final[ticker] = pd.DataFrame(data).set_index('date').tail(25)

    return final

def calculate_rrg(ticker, benchmark_df):
    """Wrapper untuk single ticker — compatible dengan endpoint /rrg"""
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
