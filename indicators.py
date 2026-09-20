import pandas as pd
import numpy as np

def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicators using pure pandas/numpy math."""
    df = df.copy()

    # Moving Averages
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["SMA_50"] = df["Close"].rolling(window=50).mean()
    df["SMA_200"] = df["Close"].rolling(window=200).mean()
    
    df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA_26"] = df["Close"].ewm(span=26, adjust=False).mean()

    # RSI
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

    # Bollinger Bands
    df["BB_Middle"] = df["Close"].rolling(window=20).mean()
    std = df["Close"].rolling(window=20).std()
    df["BB_Upper"] = df["BB_Middle"] + (std * 2)
    df["BB_Lower"] = df["BB_Middle"] - (std * 2)

    # Volume SMA
    df["Volume_SMA"] = df["Volume"].rolling(window=20).mean()

    return df