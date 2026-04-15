#!/usr/bin/env python3
# coding: utf-8
"""
=============================================================================
Coleta de Dados — Binance Futures + Fear & Greed + Conversao de XLSX
=============================================================================

Script assincrono para baixar dados historicos de:
  1. BTCUSDT 1-min klines (Binance Futures)
  2. Funding rate (Binance Futures)
  3. Fear & Greed Index (Alternative.me)
  4. Converte xlsx externos (DXY, VIX, ETF) para csv padronizado

Suporta atualizacao incremental: detecta ultimo timestamp no CSV e
baixa apenas dados novos.

Uso:
  python fetch_binance_data.py
  python fetch_binance_data.py --symbol ETHUSDT --years 3
"""

import argparse
import asyncio
import os
import platform
import sys
import time
from typing import List, Optional

import aiohttp
import numpy as np
import pandas as pd
import requests


# ===========================================================================
# CONSTANTES
# ===========================================================================
BINANCE_FUTURES_BASE = "https://fapi.binance.com"
KLINES_ENDPOINT = "/fapi/v1/klines"
FUNDING_RATE_ENDPOINT = "/fapi/v1/fundingRate"
FEAR_GREED_URL = "https://api.alternative.me/fng/"

KLINES_LIMIT = 1500        # max por request
FUNDING_LIMIT = 1000       # max por request
KLINES_INTERVAL_MS = KLINES_LIMIT * 60 * 1000   # 1500 min em ms
FUNDING_INTERVAL_MS = FUNDING_LIMIT * 8 * 3600 * 1000  # ~333 dias em ms

MAX_CONCURRENT = 8          # semaphore limit
CONNECTOR_LIMIT = 8         # aiohttp connector limit
WEIGHT_PAUSE_THRESHOLD = 1000  # pausa se weight > este valor
WEIGHT_PAUSE_SECS = 61     # segundos de pausa
RETRY_STATUSES = {429, 418}
MAX_RETRIES = 5


# ===========================================================================
# BINANCE DATA FETCHER
# ===========================================================================
class BinanceDataFetcher:
    """
    Coleta assincrona de dados Binance Futures com paginacao e rate limiting.

    Inspirado no padrao de market_data.py:
    - aiohttp.TCPConnector com pool limitado
    - Semaphore para controle de concorrencia
    - Monitoramento do header x-mbx-used-weight-1m
    - Retry com backoff em 429/418
    """

    def __init__(
        self,
        symbol: str = "BTCUSDT",
        years_history: int = 5,
        data_dir: str = "data",
    ):
        self.symbol = symbol.upper()
        self.years_history = years_history
        self.data_dir = data_dir
        self._weight_used = 0

    # -----------------------------------------------------------------------
    # Request core
    # -----------------------------------------------------------------------
    async def _request(
        self,
        session: aiohttp.ClientSession,
        sem: asyncio.Semaphore,
        url: str,
        params: dict,
        attempt: int = 0,
    ) -> list:
        """Request com rate-limit monitoring e retry."""
        async with sem:
            try:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    # Monitorar weight
                    weight_str = resp.headers.get("x-mbx-used-weight-1m", "0")
                    self._weight_used = int(weight_str)
                    if self._weight_used >= WEIGHT_PAUSE_THRESHOLD:
                        print(f"    [RATE] Weight={self._weight_used}, pausando {WEIGHT_PAUSE_SECS}s...")
                        await asyncio.sleep(WEIGHT_PAUSE_SECS)

                    if resp.status in RETRY_STATUSES:
                        if attempt >= MAX_RETRIES:
                            print(f"    [ERRO] Max retries atingido ({resp.status})")
                            return []
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        jitter = np.random.uniform(0.5, 2.0)
                        wait = retry_after + jitter
                        print(f"    [RETRY] Status {resp.status}, aguardando {wait:.1f}s (tentativa {attempt+1})")
                        await asyncio.sleep(wait)
                        return await self._request(session, sem, url, params, attempt + 1)

                    resp.raise_for_status()
                    return await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt >= MAX_RETRIES:
                    print(f"    [ERRO] {type(e).__name__}: {e}")
                    return []
                await asyncio.sleep(2 ** attempt)
                return await self._request(session, sem, url, params, attempt + 1)

    # -----------------------------------------------------------------------
    # Klines
    # -----------------------------------------------------------------------
    async def _fetch_klines_all(
        self,
        session: aiohttp.ClientSession,
        sem: asyncio.Semaphore,
        start_ms: int,
        end_ms: int,
    ) -> List[list]:
        """Pagina klines 1m de start_ms ate end_ms."""
        all_rows = []
        current = start_ms
        total_expected = (end_ms - start_ms) / (60 * 1000)
        fetched = 0

        while current < end_ms:
            url = BINANCE_FUTURES_BASE + KLINES_ENDPOINT
            params = {
                "symbol": self.symbol,
                "interval": "1m",
                "startTime": current,
                "endTime": end_ms,
                "limit": KLINES_LIMIT,
            }
            data = await self._request(session, sem, url, params)
            if not data:
                break

            all_rows.extend(data)
            fetched += len(data)
            last_open_time = data[-1][0]
            current = last_open_time + 60_000

            # Progresso
            pct = min(fetched / max(total_expected, 1) * 100, 100)
            print(f"\r    Klines: {fetched:,} barras ({pct:.1f}%) weight={self._weight_used}", end="", flush=True)

            # Mini pausa entre paginas
            await asyncio.sleep(0.1)

        print()  # newline
        return all_rows

    # -----------------------------------------------------------------------
    # Funding Rate
    # -----------------------------------------------------------------------
    async def _fetch_funding_rate_all(
        self,
        session: aiohttp.ClientSession,
        sem: asyncio.Semaphore,
        start_ms: int,
        end_ms: int,
    ) -> List[dict]:
        """Pagina funding rate de start_ms ate end_ms."""
        all_rows = []
        current = start_ms

        while current < end_ms:
            url = BINANCE_FUTURES_BASE + FUNDING_RATE_ENDPOINT
            params = {
                "symbol": self.symbol,
                "startTime": current,
                "endTime": end_ms,
                "limit": FUNDING_LIMIT,
            }
            data = await self._request(session, sem, url, params)
            if not data:
                break

            all_rows.extend(data)
            last_time = data[-1]["fundingTime"]
            current = last_time + 1

            print(f"\r    Funding rate: {len(all_rows):,} registros", end="", flush=True)
            await asyncio.sleep(0.1)

        print()
        return all_rows

    # -----------------------------------------------------------------------
    # Incremental start
    # -----------------------------------------------------------------------
    def _load_incremental_start(
        self, csv_path: str, default_start_ms: int, interval_ms: int = 60_000
    ) -> int:
        """Se CSV existe, retorna timestamp da ultima linha + intervalo."""
        if not os.path.exists(csv_path):
            return default_start_ms

        # Ler apenas ultima linha eficientemente
        df = pd.read_csv(csv_path, usecols=["timestamp"])
        if len(df) == 0:
            return default_start_ms

        last_ts = pd.to_datetime(df["timestamp"].iloc[-1])
        if last_ts.tzinfo is None:
            last_ts = last_ts.tz_localize("UTC")
        return int(last_ts.timestamp() * 1000) + interval_ms

    # -----------------------------------------------------------------------
    # Persistencia: Klines
    # -----------------------------------------------------------------------
    def _save_klines(self, rows: List[list], csv_path: str) -> None:
        """Salva/appenda klines no formato timestamp,open,high,low,close,volume."""
        if not rows:
            print("    Nenhum dado novo de klines para salvar.")
            return

        df = pd.DataFrame(
            rows,
            columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades",
                "taker_buy_base", "taker_buy_quote", "ignore",
            ],
        )
        df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        out = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()
        out = out.drop_duplicates(subset=["timestamp"]).sort_values("timestamp")

        # Append ou criar
        if os.path.exists(csv_path):
            existing = pd.read_csv(csv_path, parse_dates=["timestamp"])
            combined = pd.concat([existing, out], ignore_index=True)
            combined = combined.drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
            combined.to_csv(csv_path, index=False)
            new_count = len(combined) - len(existing)
            print(f"    Klines: {new_count:,} novas barras adicionadas (total: {len(combined):,})")
        else:
            out.to_csv(csv_path, index=False)
            print(f"    Klines: {len(out):,} barras salvas em {csv_path}")

    # -----------------------------------------------------------------------
    # Persistencia: Funding Rate
    # -----------------------------------------------------------------------
    def _save_funding_rate(self, rows: List[dict], csv_path: str) -> None:
        """Salva/appenda funding rate no formato timestamp,funding_rate."""
        if not rows:
            print("    Nenhum dado novo de funding rate para salvar.")
            return

        records = []
        for r in rows:
            ts = pd.to_datetime(int(r["fundingTime"]), unit="ms", utc=True)
            fr = float(r["fundingRate"])
            records.append({"timestamp": ts, "funding_rate": fr})

        df = pd.DataFrame(records)
        df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp")

        if os.path.exists(csv_path):
            existing = pd.read_csv(csv_path, parse_dates=["timestamp"])
            combined = pd.concat([existing, df], ignore_index=True)
            combined = combined.drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
            combined.to_csv(csv_path, index=False)
            new_count = len(combined) - len(existing)
            print(f"    Funding rate: {new_count:,} novos registros (total: {len(combined):,})")
        else:
            df.to_csv(csv_path, index=False)
            print(f"    Funding rate: {len(df):,} registros salvos em {csv_path}")

    # -----------------------------------------------------------------------
    # Fear & Greed (sync)
    # -----------------------------------------------------------------------
    def _fetch_fear_greed(self) -> pd.DataFrame:
        """Busca historico completo do Fear & Greed Index (Alternative.me)."""
        print("    Buscando Fear & Greed Index...")
        resp = requests.get(FEAR_GREED_URL, params={"limit": 0}, timeout=30)
        resp.raise_for_status()
        j = resp.json()

        rows = []
        for d in j.get("data", []):
            ts = pd.Timestamp(int(d["timestamp"]), unit="s", tz="UTC")
            value = int(d["value"])
            rows.append({"timestamp": ts, "fear_greed": value})

        df = pd.DataFrame(rows)
        df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
        return df

    # -----------------------------------------------------------------------
    # Main: fetch_all
    # -----------------------------------------------------------------------
    async def fetch_all(self) -> None:
        """Executa coleta completa: klines + funding rate + fear & greed."""
        os.makedirs(self.data_dir, exist_ok=True)

        end_ms = int(pd.Timestamp.utcnow().timestamp() * 1000)
        default_start_ms = int(end_ms - self.years_history * 365.25 * 24 * 3600 * 1000)

        klines_path = os.path.join(self.data_dir, f"{self.symbol.lower()}_1m.csv")
        funding_path = os.path.join(self.data_dir, "funding_rate.csv")
        fng_path = os.path.join(self.data_dir, "fear_greed.csv")

        # Incremental starts
        klines_start = self._load_incremental_start(klines_path, default_start_ms, 60_000)
        funding_start = self._load_incremental_start(funding_path, default_start_ms, 1)

        connector = aiohttp.TCPConnector(limit=CONNECTOR_LIMIT)
        sem = asyncio.Semaphore(MAX_CONCURRENT)

        async with aiohttp.ClientSession(connector=connector) as session:
            # Klines
            klines_start_dt = pd.to_datetime(klines_start, unit="ms", utc=True)
            if klines_start < end_ms:
                print(f"\n  [1/3] Baixando klines {self.symbol} 1m desde {klines_start_dt}...")
                klines_data = await self._fetch_klines_all(session, sem, klines_start, end_ms)
                self._save_klines(klines_data, klines_path)
            else:
                print(f"\n  [1/3] Klines ja atualizadas.")

            # Funding rate
            funding_start_dt = pd.to_datetime(funding_start, unit="ms", utc=True)
            if funding_start < end_ms:
                print(f"\n  [2/3] Baixando funding rate {self.symbol} desde {funding_start_dt}...")
                funding_data = await self._fetch_funding_rate_all(session, sem, funding_start, end_ms)
                self._save_funding_rate(funding_data, funding_path)
            else:
                print(f"\n  [2/3] Funding rate ja atualizado.")

        # Fear & Greed (sync, simples)
        print(f"\n  [3/3] Fear & Greed Index...")
        try:
            fng_df = self._fetch_fear_greed()
            fng_df.to_csv(fng_path, index=False)
            print(f"    Fear & Greed: {len(fng_df):,} registros salvos em {fng_path}")
        except Exception as e:
            print(f"    [AVISO] Falha ao buscar Fear & Greed: {e}")

        # Converter xlsx externos
        print(f"\n  [+] Verificando arquivos xlsx externos...")
        convert_external_xlsx(self.data_dir)

        print(f"\n  Coleta concluida! Dados em: {self.data_dir}/")


# ===========================================================================
# CONVERSAO DE XLSX EXTERNOS
# ===========================================================================
def convert_external_xlsx(data_dir: str) -> None:
    """
    Converte arquivos xlsx externos para csv padronizado.

    Formato de saida padrao: timestamp,<value_column>
    Todos os timestamps sao normalizados para UTC.
    """
    try:
        import openpyxl  # noqa: F401 — verifica se disponivel
    except ImportError:
        print("    [AVISO] openpyxl nao instalado — pulando conversao xlsx.")
        print("    Instale com: pip install openpyxl")
        return

    conversions = [
        {
            "xlsx": "DXY.xlsx",
            "csv": "dxy.csv",
            "col_map": {"Dates": "timestamp", "PX_LAST": "close"},
            "output_cols": ["timestamp", "close"],
            "label": "DXY (Dollar Index)",
        },
        {
            "xlsx": "vix.xlsx",
            "csv": "vix.csv",
            "col_map": {"date": "timestamp", "price": "close"},
            "output_cols": ["timestamp", "close"],
            "label": "VIX (Volatility Index)",
        },
        {
            "xlsx": "ibit_etf_btc.xlsx",
            "csv": "etf_btc_volume.csv",
            "col_map": {"date": "timestamp", "volume": "volume"},
            "output_cols": ["timestamp", "volume"],
            "label": "ETF BTC (iShares IBIT)",
        },
    ]

    for conv in conversions:
        xlsx_path = os.path.join(data_dir, conv["xlsx"])
        csv_path = os.path.join(data_dir, conv["csv"])

        if not os.path.exists(xlsx_path):
            continue

        if os.path.exists(csv_path):
            print(f"    {conv['label']}: csv ja existe ({csv_path}), pulando.")
            continue

        try:
            df = pd.read_excel(xlsx_path)
            df = df.rename(columns=conv["col_map"])

            # Normalizar timestamp
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            df = df.dropna(subset=["timestamp"])
            df = df.sort_values("timestamp").reset_index(drop=True)

            # Selecionar colunas de saida
            df[conv["output_cols"]].to_csv(csv_path, index=False)
            print(f"    {conv['label']}: {len(df)} registros -> {csv_path}")
        except Exception as e:
            print(f"    [ERRO] {conv['label']}: {e}")


# ===========================================================================
# MAIN
# ===========================================================================
async def async_main(symbol: str, years: int, data_dir: str) -> None:
    fetcher = BinanceDataFetcher(
        symbol=symbol,
        years_history=years,
        data_dir=data_dir,
    )
    await fetcher.fetch_all()


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta de dados Binance + externos")
    parser.add_argument("--symbol", default="BTCUSDT", help="Par de trading (default: BTCUSDT)")
    parser.add_argument("--years", type=int, default=5, help="Anos de historico (default: 5)")
    parser.add_argument("--data-dir", default="data", help="Diretorio de saida (default: data)")
    args = parser.parse_args()

    # Resolver data_dir relativo ao script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, args.data_dir)

    print("=" * 70)
    print(f"  COLETA DE DADOS — {args.symbol}")
    print(f"  Historico: {args.years} anos")
    print(f"  Diretorio: {data_dir}")
    print("=" * 70)

    # Compatibilidade Windows + aiohttp
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(async_main(args.symbol, args.years, data_dir))


if __name__ == "__main__":
    main()
