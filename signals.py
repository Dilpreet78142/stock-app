import pandas as pd
from indicators import add_all_indicators

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate BUY / SELL / HOLD signals based on multiple indicators.
    Each indicator votes, and the majority wins.
    """
    df = add_all_indicators(df)
    df["Buy_Score"] = 0
    df["Sell_Score"] = 0

    # ── 1. RSI ──
    df.loc[df["RSI"] < 30, "Buy_Score"] += 2      # Oversold
    df.loc[df["RSI"] > 70, "Sell_Score"] += 2     # Overbought
    df.loc[(df["RSI"] >= 30) & (df["RSI"] <= 40), "Buy_Score"] += 1
    df.loc[(df["RSI"] >= 60) & (df["RSI"] <= 70), "Sell_Score"] += 1

    # ── 2. MACD Crossover ──
    df.loc[
        (df["MACD"] > df["MACD_Signal"]) &
        (df["MACD"].shift(1) <= df["MACD_Signal"].shift(1)),
        "Buy_Score"
    ] += 3
    df.loc[
        (df["MACD"] < df["MACD_Signal"]) &
        (df["MACD"].shift(1) >= df["MACD_Signal"].shift(1)),
        "Sell_Score"
    ] += 3

    # ── 3. MACD Histogram direction ──
    df.loc[df["MACD_Hist"] > 0, "Buy_Score"] += 1
    df.loc[df["MACD_Hist"] < 0, "Sell_Score"] += 1

    # ── 4. SMA Crossovers ──
    df.loc[df["SMA_20"] > df["SMA_50"], "Buy_Score"] += 1
    df.loc[df["SMA_20"] < df["SMA_50"], "Sell_Score"] += 1
    df.loc[df["SMA_50"] > df["SMA_200"], "Buy_Score"] += 2  # Golden cross
    df.loc[df["SMA_50"] < df["SMA_200"], "Sell_Score"] += 2  # Death cross

    # ── 5. Price vs SMA 200 ──
    df.loc[df["Close"] > df["SMA_200"], "Buy_Score"] += 1
    df.loc[df["Close"] < df["SMA_200"], "Sell_Score"] += 1

    # ── 6. Bollinger Bands ──
    df.loc[df["Close"] <= df["BB_Lower"], "Buy_Score"] += 2
    df.loc[df["Close"] >= df["BB_Upper"], "Sell_Score"] += 2

    # ── 7. Stochastic ──
    df.loc[df["Stoch_K"] < 20, "Buy_Score"] += 1
    df.loc[df["Stoch_K"] > 80, "Sell_Score"] += 1

    # ── 8. Volume Confirmation ──
    df.loc[df["Volume"] > df["Volume_SMA"] * 1.5, "Buy_Score"] += 1

    # ── Final Signal ──
    df["Net_Score"] = df["Buy_Score"] - df["Sell_Score"]
    df["Signal"] = "HOLD"
    df.loc[df["Net_Score"] >= 4, "Signal"] = "🟢 STRONG BUY"
    df.loc[(df["Net_Score"] >= 2) & (df["Net_Score"] < 4), "Signal"] = "🟢 BUY"
    df.loc[(df["Net_Score"] <= -4), "Signal"] = "🔴 STRONG SELL"
    df.loc[(df["Net_Score"] <= -2) & (df["Net_Score"] > -4), "Signal"] = "🔴 SELL"

    return df


def get_latest_signal(df: pd.DataFrame) -> dict:
    """Return the latest signal summary."""
    latest = df.iloc[-1]
    return {
        "date": latest.name.strftime("%Y-%m-%d") if hasattr(latest.name, "strftime") else str(latest.name),
        "close": round(latest["Close"], 2),
        "signal": latest["Signal"],
        "net_score": int(latest["Net_Score"]),
        "rsi": round(latest["RSI"], 2) if pd.notna(latest["RSI"]) else None,
        "macd": round(latest["MACD"], 4) if pd.notna(latest["MACD"]) else None,
        "macd_signal": round(latest["MACD_Signal"], 4) if pd.notna(latest["MACD_Signal"]) else None,
        "adx": round(latest["ADX"], 2) if pd.notna(latest["ADX"]) else None,
        "bb_position": _bb_position(latest),
    }

def _bb_position(row) -> str:
    if pd.isna(row.get("BB_Upper")) or pd.isna(row.get("BB_Lower")):
        return "N/A"
    if row["Close"] >= row["BB_Upper"]:
        return "Above Upper Band ⚠️"
    elif row["Close"] <= row["BB_Lower"]:
        return "Below Lower Band ⚠️"
    else:
        return "Within Bands ✅"