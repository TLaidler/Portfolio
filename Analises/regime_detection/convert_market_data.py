#!/usr/bin/env python3
# coding: utf-8
"""
Converte dados de S&P500 e IBOVESPA (.xlsx) para formato padrao (.csv).

Formato alvo (identico ao btcusdt_1m.csv):
  timestamp, open, high, low, close, volume

Para dados minutely de ETF que so possuem close+volume:
  open = high = low = close (aproximacao — sem OHLC real)

Para dados diarios de indice:
  Converte para barras diarias com open=high=low=close=price
"""

import os
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")


def convert_etf_minutely(input_file: str, output_file: str, label: str) -> None:
    """Converte ETF minutely xlsx (date, close, volume) -> csv padrao."""
    df = pd.read_excel(os.path.join(DATA_DIR, input_file))
    df = df.rename(columns={"date": "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Sem OHLC real — usar close para todas
    out = pd.DataFrame({
        "timestamp": df["timestamp"],
        "open": df["close"],
        "high": df["close"],
        "low": df["close"],
        "close": df["close"],
        "volume": df["volume"],
    })

    # Remover linhas com volume zero ou NaN
    out = out.dropna(subset=["close", "volume"])
    out = out[out["volume"] > 0].reset_index(drop=True)

    path = os.path.join(DATA_DIR, output_file)
    out.to_csv(path, index=False)
    print(f"  {label}: {len(out)} barras -> {path}")
    print(f"    Periodo: {out['timestamp'].min()} a {out['timestamp'].max()}")


def convert_index_daily(input_file: str, output_file: str, label: str) -> None:
    """Converte indice diario xlsx (date, price, volume) -> csv padrao."""
    df = pd.read_excel(os.path.join(DATA_DIR, input_file))
    df = df.rename(columns={"date": "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    out = pd.DataFrame({
        "timestamp": df["timestamp"],
        "open": df["price"],
        "high": df["price"],
        "low": df["price"],
        "close": df["price"],
        "volume": df["volume"],
    })

    out = out.dropna(subset=["close", "volume"])
    out = out[out["volume"] > 0].reset_index(drop=True)

    path = os.path.join(DATA_DIR, output_file)
    out.to_csv(path, index=False)
    print(f"  {label}: {len(out)} barras -> {path}")
    print(f"    Periodo: {out['timestamp'].min()} a {out['timestamp'].max()}")


def main():
    print("=" * 60)
    print("  Conversao de dados de mercado (.xlsx -> .csv)")
    print("=" * 60)

    convert_etf_minutely("SP500_etf_minutely.xlsx", "sp500_etf_1m.csv",
                          "S&P500 ETF (SPY) 1-min")
    convert_etf_minutely("ibov_etf_minutely.xlsx", "ibov_etf_1m.csv",
                          "IBOVESPA ETF (BOVA11) 1-min")
    convert_index_daily("SP500_daily.xlsx", "sp500_daily.csv",
                         "S&P500 Index diario")
    convert_index_daily("ibov_dailyxlsx.xlsx", "ibov_daily.csv",
                         "IBOVESPA Index diario")

    print("\nConversao concluida.")


if __name__ == "__main__":
    main()
