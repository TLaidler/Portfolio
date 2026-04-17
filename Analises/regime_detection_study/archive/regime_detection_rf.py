#!/usr/bin/env python3
# coding: utf-8
"""
Pipeline de detecção de regimes de mercado com Random Forest.

Baixa OHLCV (Binance Futures) e Fear & Greed (Alternative.me), constrói features
sem data leakage, define regimes por regras quantitativas, treina um
RandomForestClassifier com split temporal e avalia/plota resultados.
"""

import os
import time
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# Constantes
RNG_SEED = 42
BINANCE_KLINES_URL = "https://fapi.binance.com/fapi/v1/klines"
FEAR_GREED_URL = "https://api.alternative.me/fng/"
DATA_DIR = "data"
SAVE_POINT_DIR = "save_point"
INTERVAL_1M = "1m"
LIMIT_PER_REQUEST = 1500
SLEEP_BETWEEN_REQUESTS = 0.2
YEARS_HISTORY = 1
TRAIN_RATIO = 0.8
REGIME_NAMES = ["high_volatility", "trend_down", "mean_reversion", "trend_up"]


# -----------------------------------------------------------------------------
# Coleta de dados
# -----------------------------------------------------------------------------

def fetch_binance_klines(
    symbol: str,
    interval: str,
    start_ts: int,
    end_ts: Optional[int] = None,
    limit: int = LIMIT_PER_REQUEST,
) -> List[list]:
    """
    Obtém uma página de klines da API Binance Futures (USD-M).
    start_ts/end_ts em milissegundos.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_ts,
        "limit": limit,
    }
    if end_ts is not None:
        params["endTime"] = end_ts
    resp = requests.get(BINANCE_KLINES_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def download_binance_historical(
    symbol: str,
    years: int = YEARS_HISTORY,
    data_dir: str = DATA_DIR,
) -> pd.DataFrame:
    """
    Baixa histórico de klines 1m via paginação e salva CSV em data_dir.
    """
    end_ms = int(pd.Timestamp.utcnow().timestamp() * 1000)
    start_ms = int(end_ms - years * 365 * 24 * 60 * 60 * 1000)
    all_rows: List[list] = []
    current_start = start_ms

    while current_start < end_ms:
        data = fetch_binance_klines(
            symbol=symbol,
            interval=INTERVAL_1M,
            start_ts=current_start,
            end_ts=end_ms,
            limit=LIMIT_PER_REQUEST,
        )
        if not data:
            break
        all_rows.extend(data)
        last_ts = data[-1][0]
        current_start = last_ts + 60 * 1000  # próximo minuto
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    df = pd.DataFrame(
        all_rows,
        columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore",
        ],
    )
    df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    out = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    out = out.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    os.makedirs(data_dir, exist_ok=True)
    filename = os.path.join(data_dir, f"{symbol.lower()}_1m.csv")
    out.to_csv(filename, index=False)
    return out


def fetch_fear_greed(limit: int = 0) -> pd.DataFrame:
    """
    Obtém histórico do Fear & Greed Index (Alternative.me).
    limit=0 retorna todos os dados disponíveis.
    """
    resp = requests.get(FEAR_GREED_URL, params={"limit": limit}, timeout=30)
    resp.raise_for_status()
    j = resp.json()
    rows = []
    for d in j.get("data", []):
        ts = int(d["timestamp"])  # Unix em segundos
        value = int(d["value"])
        rows.append({"timestamp": pd.Timestamp(ts, unit="s", tz="UTC"), "fear_greed": value})
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    return df


def load_or_download_all(data_dir: str = DATA_DIR) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Carrega BTC, ETH e Fear & Greed dos CSVs em data_dir; se não existirem, baixa e salva.
    Retorna (btc_df, eth_df, fng_df).
    """
    os.makedirs(data_dir, exist_ok=True)
    btc_path = os.path.join(data_dir, "btcusdt_1m.csv")
    eth_path = os.path.join(data_dir, "ethusdt_1m.csv")
    fng_path = os.path.join(data_dir, "fear_greed.csv")

    if os.path.isfile(btc_path):
        btc_df = pd.read_csv(btc_path, parse_dates=["timestamp"])#, utc=True)
    else:
        btc_df = download_binance_historical("BTCUSDT", data_dir=data_dir)

    if os.path.isfile(eth_path):
        eth_df = pd.read_csv(eth_path, parse_dates=["timestamp"])#, utc=True)
    else:
        eth_df = download_binance_historical("ETHUSDT", data_dir=data_dir)

    if os.path.isfile(fng_path):
        fng_df = pd.read_csv(fng_path, parse_dates=["timestamp"])#, utc=True)
    else:
        fng_df = fetch_fear_greed(limit=0)
        fng_df.to_csv(fng_path, index=False)

    return btc_df, eth_df, fng_df


# -----------------------------------------------------------------------------
# Limpeza e merge
# -----------------------------------------------------------------------------

def clean_and_merge(
    btc_df: pd.DataFrame,
    eth_df: pd.DataFrame,
    fng_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Limpa timestamps, remove duplicatas e faz merge: base BTC 1m + ETH (close, volume)
    + Fear & Greed com atraso de 1 dia (valor do dia é de fechamento; usamos dia anterior
    para evitar data leakage).
    """
    btc = btc_df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)
    eth = eth_df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)
    fng = fng_df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)

    # Normalizar timezone se necessário
    for df in [btc, eth, fng]:
        if df["timestamp"].dt.tz is None:
            df["timestamp"] = df["timestamp"].dt.tz_localize("UTC", ambiguous="infer")

    # Fear & Greed: atrasar 1 dia (valor publicado é do fechamento do dia; usamos dia anterior para evitar leakage)
    fng = fng.copy()
    fng["date"] = fng["timestamp"].dt.date
    fng_by_date = fng.set_index("date")["fear_greed"].to_dict()

    # Merge base: BTC
    out = btc[["timestamp", "close", "volume"]].copy()
    out = out.rename(columns={"close": "close_btc", "volume": "volume_btc"})

    # Merge ETH: por timestamp (inner para alinhar)
    eth_sel = eth[["timestamp", "close", "volume"]].rename(
        columns={"close": "close_eth", "volume": "volume_eth"}
    )
    out = out.merge(eth_sel, on="timestamp", how="inner")

    # Merge Fear & Greed: para cada timestamp, usar valor do dia anterior (calendário)
    out["date"] = out["timestamp"].dt.date
    out["date_prev"] = (out["timestamp"] - pd.Timedelta(days=1)).dt.date
    out["fear_greed"] = out["date_prev"].map(fng_by_date)
    out = out.drop(columns=["date", "date_prev"])
    # Forward-fill para dias sem dado e para minutos dentro do mesmo dia
    out["fear_greed"] = out["fear_greed"].ffill()
    out = out.dropna(subset=["fear_greed"]).reset_index(drop=True)
    return out


# -----------------------------------------------------------------------------
# Feature engineering (sem data leakage: só dados até t inclusive)
# -----------------------------------------------------------------------------

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constrói features de momentum, volatilidade e estrutura sobre close_btc/close_eth e fear_greed.
    """
    d = df.copy()
    d = d.sort_values("timestamp").reset_index(drop=True)

    close_btc = d["close_btc"].astype(float)
    close_eth = d["close_eth"].astype(float)

    # Retornos (simples)
    ret_btc = close_btc.pct_change()
    ret_eth = close_eth.pct_change()

    # Momentum / tendência (BTC)
    d["ret_5"] = (close_btc - close_btc.shift(5)) / close_btc.shift(5)
    d["ret_20"] = (close_btc - close_btc.shift(20)) / close_btc.shift(20)
    ma50 = close_btc.rolling(50, min_periods=50).mean()
    ma20 = close_btc.rolling(20, min_periods=20).mean()
    ma100 = close_btc.rolling(100, min_periods=100).mean()
    d["price_minus_ma50"] = close_btc - ma50
    d["ma20_ma100_ratio"] = ma20 / ma100.replace(0, np.nan)

    # slope_regression_30: coeficiente angular da regressão linear dos últimos 30 closes
    def slope_30(series: pd.Series) -> pd.Series:
        def one_slope(w: np.ndarray) -> float:
            if len(w) < 30 or np.any(np.isnan(w)):
                return np.nan
            x = np.arange(len(w), dtype=float)
            return np.polyfit(x, w, 1)[0]
        return series.rolling(30, min_periods=30).apply(one_slope, raw=True)
    d["slope_regression_30"] = slope_30(close_btc)

    # Volatilidade (std dos retornos)
    d["vol_5"] = ret_btc.rolling(5, min_periods=5).std()
    d["vol_20"] = ret_btc.rolling(20, min_periods=20).std()
    d["vol_60"] = ret_btc.rolling(60, min_periods=60).std()
    d["vol_ratio"] = d["vol_5"] / d["vol_60"].replace(0, np.nan)

    # Estrutura de preço (high/low 20 e 60)
    high_20 = d["close_btc"].rolling(20, min_periods=20).max()
    low_20 = d["close_btc"].rolling(20, min_periods=20).min()
    high_60 = d["close_btc"].rolling(60, min_periods=60).max()
    low_60 = d["close_btc"].rolling(60, min_periods=60).min()
    range_20 = high_20 - low_20
    range_60 = high_60 - low_60
    d["distance_to_high_20"] = (high_20 - close_btc) / high_20.replace(0, np.nan)
    d["distance_to_low_20"] = (close_btc - low_20) / low_20.replace(0, np.nan)
    d["range_20"] = range_20
    d["range_compression"] = range_20 / range_60.replace(0, np.nan)

    # ETH momentum (opcional, enriquece)
    d["ret_5_eth"] = (close_eth - close_eth.shift(5)) / close_eth.shift(5)
    d["ret_20_eth"] = (close_eth - close_eth.shift(20)) / close_eth.shift(20)

    # fear_greed já está em d
    feature_cols = [
        "ret_5", "ret_20", "slope_regression_30", "price_minus_ma50", "ma20_ma100_ratio",
        "vol_5", "vol_20", "vol_60", "vol_ratio",
        "distance_to_high_20", "distance_to_low_20", "range_20", "range_compression",
        "fear_greed", "ret_5_eth", "ret_20_eth",
    ]
    out = d[["timestamp", "close_btc", "volume_btc", "close_eth", "volume_eth"] + feature_cols].copy()
    out = out.dropna().reset_index(drop=True)
    return out


# -----------------------------------------------------------------------------
# Regimes (target) e split temporal
# -----------------------------------------------------------------------------

def create_regime_labels(
    df: pd.DataFrame,
    train_mask: pd.Series,
    vol_q: float = 0.9,
    ret_q_low: float = 0.33,
    ret_q_high: float = 0.67,
) -> pd.Series:
    """
    Define regimes com base em return_20 e vol_20. Limiares calculados apenas no treino
    para evitar data leakage; mesmos limiares aplicados ao teste.
    Ordem: high_volatility -> trend_down -> trend_up -> mean_reversion.
    """
    return_20 = (df["close_btc"] - df["close_btc"].shift(20)) / df["close_btc"].shift(20)
    ret_btc = df["close_btc"].pct_change()
    vol_20 = ret_btc.rolling(20, min_periods=20).std()

    train_return = return_20.loc[train_mask]
    train_vol = vol_20.loc[train_mask]
    train_return = train_return.dropna()
    train_vol = train_vol.dropna()

    vol_threshold = train_vol.quantile(vol_q)
    ret_low = train_return.quantile(ret_q_low)
    ret_high = train_return.quantile(ret_q_high)

    regime = pd.Series(index=df.index, dtype=object)
    hv = vol_20 >= vol_threshold
    regime[hv] = "high_volatility"
    regime[~hv & (return_20 < ret_low)] = "trend_down"
    regime[~hv & (return_20 > ret_high)] = "trend_up"
    regime[regime.isna()] = "mean_reversion"
    return regime


def temporal_split(
    df: pd.DataFrame,
    train_ratio: float = TRAIN_RATIO,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Split temporal: primeiros train_ratio para treino, resto para teste.
    Retorna (X_train, X_test, y_train, y_test, train_mask sobre df).
    """
    n = len(df)
    train_end = int(n * train_ratio)
    train_mask = pd.Series(False, index=df.index)
    train_mask.iloc[:train_end] = True

    feature_cols = [
        "ret_5", "ret_20", "slope_regression_30", "price_minus_ma50", "ma20_ma100_ratio",
        "vol_5", "vol_20", "vol_60", "vol_ratio",
        "distance_to_high_20", "distance_to_low_20", "range_20", "range_compression",
        "fear_greed", "ret_5_eth", "ret_20_eth",
    ]
    X = df[feature_cols]
    X_train = X.loc[train_mask].values
    X_test = X.loc[~train_mask].values
    return X_train, X_test, train_mask, df.loc[train_mask].index, df.loc[~train_mask].index


# -----------------------------------------------------------------------------
# Modelo e avaliação
# -----------------------------------------------------------------------------

def train_model(X_train: np.ndarray, y_train: np.ndarray) -> RandomForestClassifier:
    """Treina RandomForestClassifier com hiperparâmetros robustos."""
    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=6,
        min_samples_leaf=50,
        max_features="sqrt",
        random_state=RNG_SEED,
    )
    model.fit(X_train, y_train)
    return model


def evaluate(
    model: RandomForestClassifier,
    X_test: np.ndarray,
    y_test: np.ndarray,
    target_names: Optional[List[str]] = None,
) -> Tuple[float, np.ndarray, str]:
    """Calcula acurácia, matriz de confusão e classification report."""
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    labels = target_names if target_names is not None else list(model.classes_)
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    report = classification_report(y_test, y_pred, labels=labels, zero_division=0)
    return acc, cm, report


# -----------------------------------------------------------------------------
# Visualização
# -----------------------------------------------------------------------------

def plot_feature_importance(
    model: RandomForestClassifier,
    feature_names: List[str],
    save_dir: str = SAVE_POINT_DIR,
) -> None:
    """Ranking de importância das features e salva em save_point."""
    imp = model.feature_importances_
    idx = np.argsort(imp)[::-1]
    names = [feature_names[i] for i in idx]
    values = imp[idx]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(range(len(names)), values, align="center")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel("Importância")
    ax.set_title("Feature importance (Random Forest)")
    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    fig.savefig(os.path.join(save_dir, "feature_importance.png"), dpi=150, bbox_inches="tight")
    plt.close()


def plot_price_and_regimes(
    dates,
    price: np.ndarray,
    regimes_pred: np.ndarray,
    title: str = "BTC close e regimes previstos",
    save_path: Optional[str] = None,
) -> None:
    """
    Gráfico do preço BTC com regimes previstos marcados (cores por regime).
    Salva em save_point se save_path for None (usa nome padrão).
    dates: array-like de timestamps (ex.: DatetimeIndex.values).
    """
    dates = np.asarray(dates)
    os.makedirs(SAVE_POINT_DIR, exist_ok=True)
    if save_path is None:
        save_path = os.path.join(SAVE_POINT_DIR, "price_and_regimes.png")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(dates, price, color="black", linewidth=0.8, alpha=0.9, label="BTC close")

    uniq = np.unique(regimes_pred)
    colors = {"high_volatility": "red", "trend_down": "blue", "mean_reversion": "gray", "trend_up": "green"}
    for r in uniq:
        mask = regimes_pred == r
        ax.scatter(
            dates[mask],
            price[mask],
            c=colors.get(r, "gray"),
            s=4,
            alpha=0.5,
            label=r,
        )
    ax.set_xlabel("Data")
    ax.set_ylabel("Preço (BTC close)")
    ax.set_title(title)
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> None:
    np.random.seed(RNG_SEED)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, DATA_DIR)
    save_dir = os.path.join(script_dir, SAVE_POINT_DIR)
    os.makedirs(save_dir, exist_ok=True)

    # 1) Coleta
    print("Carregando ou baixando dados...")
    btc_df, eth_df, fng_df = load_or_download_all(data_dir)

    # 2) Limpeza e merge
    print("Limpando e mesclando...")
    merged = clean_and_merge(btc_df, eth_df, fng_df)

    # 3) Features
    print("Construindo features...")
    df = build_features(merged)

    # 4) Split temporal (antes dos labels para calcular limiares só no treino)
    feature_cols = [
        "ret_5", "ret_20", "slope_regression_30", "price_minus_ma50", "ma20_ma100_ratio",
        "vol_5", "vol_20", "vol_60", "vol_ratio",
        "distance_to_high_20", "distance_to_low_20", "range_20", "range_compression",
        "fear_greed", "ret_5_eth", "ret_20_eth",
    ]
    X_train, X_test, train_mask, train_idx, test_idx = temporal_split(df, train_ratio=TRAIN_RATIO)

    # 5) Regimes (limiares só no treino)
    df["regime"] = create_regime_labels(df, train_mask, vol_q=0.9, ret_q_low=0.33, ret_q_high=0.67)
    y_train = df.loc[train_idx, "regime"].values
    y_test = df.loc[test_idx, "regime"].values

    # 6) Treino
    print("Treinando Random Forest...")
    model = train_model(X_train, y_train)

    # 7) Avaliação
    acc, cm, report = evaluate(model, X_test, y_test)
    print("\n--- Avaliação (conjunto de teste) ---")
    print(f"Acurácia: {acc:.4f}")
    print("\nMatriz de confusão:")
    print(cm)
    print("\nClassification report:")
    print(report)

    # 8) Feature importance
    plot_feature_importance(model, feature_cols, save_dir=save_dir)
    print("\nFeature importance salva em save_point/feature_importance.png")

    # 9) Gráfico final: BTC close com predições no teste (validação)
    dates_test = df.loc[test_idx, "timestamp"]
    price_test = df.loc[test_idx, "close_btc"].values
    y_pred_test = model.predict(X_test)
    plot_price_and_regimes(
        dates_test.values,
        price_test,
        y_pred_test,
        title="BTC close (validação) e regimes previstos pelo modelo",
        save_path=os.path.join(save_dir, "price_and_regimes.png"),
    )
    print("Gráfico de validação (preço + regimes) salvo em save_point/price_and_regimes.png")


if __name__ == "__main__":
    main()
