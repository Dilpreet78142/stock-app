import pandas as pd
import numpy as np
import ta

def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all technical indicators to the dataframe."""
    df = df.copy()

    # --- Moving Averages ---
    df["SMA_20"] = ta.trend.sma_indicator(df["Close"], window=20)
    df["SMA_50"] = ta.trend.sma_indicator(df["Close"], window=50)
    df["SMA_200"] = ta.trend.sma_indicator(df["Close"], window=200)
    df["EMA_12"] = ta.trend.ema_indicator(df["Close"], window=12)
    df["EMA_26"] = ta.trend.ema_indicator(df["Close"], window=26)

    # --- RSI ---
    df["RSI"] = ta.momentum.rsi(df["Close"], window=14)

    # --- MACD ---
    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()
    df["MACD_Hist"] = macd.macd_diff()

    # --- Bollinger Bands ---
    bb = ta.volatility.BollingerBands(df["Close"])
    df["BB_Upper"] = bb.bollinger_hband()
    df["BB_Middle"] = bb.bollinger_mavg()
    df["BB_Lower"] = bb.bollinger_lband()

    # --- Stochastic Oscillator ---
    stoch = ta.momentum.StochasticOscillator(
        df["High"], df["Low"], df["Close"]
    )
    df["Stoch_K"] = stoch.stoch()
    df["Stoch_D"] = stoch.stoch_signal()

    # --- ADX (Trend Strength) ---
    df["ADX"] = ta.trend.adx(df["High"], df["Low"], df["Close"], window=14)

    # --- Volume SMA ---
    df["Volume_SMA"] = df["Volume"].rolling(window=20).mean()

    return df