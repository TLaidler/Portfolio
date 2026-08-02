# -*- coding: utf-8 -*-
"""
01_build_dataset.py — Dataset diário point-in-time para nowcast da abertura USDBRL.

Uma linha por dia útil D:
  - snapshot de features às 08:50 BRT (nada com timestamp > 08:50 entra)
  - target = log(primeira cotação Bloomberg >= 09:00 de D) - log(dolar_cc às 08:50)

Convenção de timezone: TODAS as séries são convertidas para BRT e mantidas naive.
BRT é UTC-3 fixo desde 2019 (sem horário de verão) -> offsets constantes são exatos:
  - contratos mensais 6L brutos: já em BRT
  - usdbrl_bloom.csv: já em BRT
  - binance-usdtbrl-1.csv: UTC -> -3h (validado: volume 12:00 UTC == 09:00 BRT do spread_volume)
  - DXY.csv (processado): BRT-3h -> +3h (validado: close de sexta 15:59 = 17:00 ET)
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                   # raiz do repo
REF = os.path.join(ROOT, "data", "reference")
PROC = os.path.join(ROOT, "data", "processed")
# Dados brutos sao licenciados (Bloomberg/terminal) e NAO sao versionados.
# Aponte para os diretorios locais via env vars -- ver data/README.md.
BUILD = os.environ.get("USDBRL_RAW_CONTRACTS", os.path.join(ROOT, "data", "raw"))
UPD = os.environ.get("USDBRL_RAW_MARKET", os.path.join(ROOT, "data", "raw"))

SNAPSHOT = "08:50"          # revisado por 02_diagnostics.py (8:50 vs 8:55)
OPEN_TIME = "09:00"
STALE_LIMIT_MIN = {"fut": 240, "dxy": 240, "binan": 15}

# ---------------------------------------------------------------- loaders
def _read_prices(path, sep, dayfirst):
    df = pd.read_csv(path, sep=sep, header=None, names=["date", "close"])
    df["date"] = pd.to_datetime(df["date"], dayfirst=dayfirst, format="mixed")
    return df.dropna().set_index("date").sort_index()

# (arquivo, sep, dayfirst) — formatos heterogêneos dos arquivos de origem
MONTHLY = [
    ("janeiro_futuro_BRLUSD.csv", ",", False),
    ("fevereiro_futuro_BRLUSD.csv", ",", False),
    ("março_futuro_BRLUSD.csv", ",", False),
    ("abril_futuro_BRLUSD.csv", ";", True),
    ("maio_futuro_BRLUSD.csv", ",", False),
    ("junho_futuro_BRLUSD.csv", ",", False),
    ("julho_futuro_BRLUSD.csv", ",", False),
    ("agosto_futuro_BRLUSD.csv", ";", True),
    ("setembro_futuro_BRLUSD.csv", ";", True),
    ("outubro_futuro_BRLUSD.csv", ";", True),
]

def build_6l_continuous():
    """Stitch dos contratos mensais (BRT bruto, sem shift). Retorna (série, expiries)."""
    cont, expiries = None, []
    for fname, sep, dayfirst in MONTHLY:
        df = _read_prices(os.path.join(BUILD, fname), sep, dayfirst)
        if cont is None:
            cont = df
        else:
            cont = cont.combine_first(df[cont.index[-1]:])
        expiries.append(cont.index[-1])
    # últimos contratos truncados em 2024-08-08 não são vencimentos reais:
    # vencimento real = último dia útil do mês anterior ao nome do contrato.
    return cont["close"], expiries

def load_bloom():
    df = pd.read_csv(os.path.join(UPD, "usdbrl_bloom.csv"))
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%y %H:%M")
    df["close"] = pd.to_numeric(df["close"].astype(str).str.strip())
    return df.set_index("date")["close"].sort_index()

def load_binance():
    df = pd.read_csv(os.path.join(UPD, "binance-usdtbrl-1.csv"),
                     usecols=["date", "close"], parse_dates=["date"])
    df["date"] = df["date"] - pd.Timedelta(hours=3)   # UTC -> BRT
    return df.set_index("date")["close"].sort_index()

def load_dxy():
    df = pd.read_csv(os.path.join(UPD, "DXY.csv"))
    df["date"] = pd.to_datetime(df["date"], format="mixed") + pd.Timedelta(hours=3)  # BRT-3h -> BRT
    return df.set_index("date")["close"].sort_index()

def load_daily_rates():
    selic = pd.read_csv(os.path.join(UPD, "selic.csv"),
                        parse_dates=["Date"]).set_index("Date")["selic"]
    # Selic é meta anunciada: conhecida em tempo real. Constante 10.50 de 08/05 a 18/09/2024
    # -> ffill até o fim do range é factualmente correto.
    dgs = pd.read_csv(os.path.join(UPD, "treasury_bond_1m.csv"),
                      parse_dates=["DATE"]).set_index("DATE")["DGS1MO"]
    gap = pd.read_csv(os.path.join(REF, "dgs1mo_gap_fill.csv"),
                      parse_dates=["observation_date"]).set_index("observation_date")["DGS1MO"]
    dgs = pd.concat([dgs, gap[~gap.index.isin(dgs.index)]]).sort_index().dropna()
    return selic.sort_index().dropna(), dgs

# ---------------------------------------------------------------- helpers
def asof_with_staleness(series, ts, limit_min):
    """Último valor <= ts. Retorna (valor, staleness_min) ou (nan, nan) se estourar o limite."""
    s = series.loc[:ts]
    if s.empty:
        return np.nan, np.nan
    stale = (ts - s.index[-1]).total_seconds() / 60.0
    if stale > limit_min:
        return np.nan, stale
    return s.iloc[-1], stale

def main():
    print("Carregando séries...")
    fut, _ = build_6l_continuous()          # preço 6L (USD por 1000 BRL), BRT
    bloom = load_bloom()                    # USDBRL spot Bloomberg, BRT, on-market
    binan = load_binance()                  # USDT/BRL Binance, BRT, 24/7
    dxy = load_dxy()                        # DXY, BRT
    selic, dgs = load_daily_rates()
    fut_usdbrl = 100.0 / fut                # USDBRL implícito no 6L

    # vencimentos reais do contrato front (último dia útil do mês anterior ao contrato)
    expiry_dates = pd.to_datetime([
        "2023-12-28", "2024-01-31", "2024-02-29", "2024-03-28", "2024-04-30",
        "2024-05-31", "2024-06-28", "2024-07-31", "2024-08-30", "2024-09-30"])

    macro = pd.read_csv(os.path.join(REF, "macro_releases.csv"),
                        parse_dates=["published_at"])

    start = max(fut.index[0], bloom.index[0]).normalize() + pd.Timedelta(days=1)
    end = min(fut.index[-1], bloom.index[-1]).normalize()
    days = pd.bdate_range(start, end)
    print(f"Range diário: {days[0].date()} -> {days[-1].date()} ({len(days)} dias úteis de calendário)")

    rows, skipped = [], []
    for d in days:
        snap = pd.Timestamp(f"{d.date()} {SNAPSHOT}")
        open_cut = pd.Timestamp(f"{d.date()} {OPEN_TIME}")

        # --- target: primeira cotação Bloomberg >= 09:00 do dia D
        bl_day = bloom.loc[open_cut:pd.Timestamp(f"{d.date()} 12:00")]
        if bl_day.empty:
            skipped.append((d.date(), "sem abertura Bloomberg (feriado B3?)")); continue
        open_ts, open_px = bl_day.index[0], bl_day.iloc[0]

        # --- snapshot 6L às 08:50
        fut_px, fut_stale = asof_with_staleness(fut_usdbrl, snap, STALE_LIMIT_MIN["fut"])
        if np.isnan(fut_px):
            skipped.append((d.date(), f"6L stale ({fut_stale:.0f}min) ou ausente")); continue
        fut_ts = fut_usdbrl.loc[:snap].index[-1]

        # --- cupom cambial point-in-time
        #   selic: meta vigente (conhecida em D); dgs: último valor PUBLICADO até 8:50 de D
        #   H.15 sai ~16:15 ET do próprio dia -> às 8:50 BRT só o valor de D-1 está disponível.
        selic_d = selic.asof(d)
        if pd.isna(selic_d):
            selic_d = selic.iloc[-1]          # 10.50 constante até o fim do range
        us_pit = dgs.asof(d - pd.Timedelta(days=1))
        us_naive = dgs.asof(d)                # variante sem lag de publicação (auditoria vintage)
        expiry = expiry_dates[expiry_dates >= d][0]
        du = int(np.busday_count(d.date(), expiry.date())) + 1
        cc_pit = ((1 + selic_d / 100) / (1 + us_pit / 100)) ** (du / 252)
        cc_naive = ((1 + selic_d / 100) / (1 + us_naive / 100)) ** (du / 252)
        dolar_cc = fut_px / cc_pit

        # --- referência de fechamento do último pregão (asof em D-1 17:58; para
        #     segundas/pós-feriado o asof recua até o último tick real, ex.: sexta)
        prev_cut = snap - pd.Timedelta(hours=14, minutes=52)   # 17:58 de D-1
        fut_prev, _ = asof_with_staleness(fut_usdbrl, prev_cut, 5 * 24 * 60)
        dxy_now, dxy_stale = asof_with_staleness(dxy, snap, STALE_LIMIT_MIN["dxy"])
        dxy_prev, _ = asof_with_staleness(dxy, prev_cut, 5 * 24 * 60)
        bin_now, bin_stale = asof_with_staleness(binan, snap, STALE_LIMIT_MIN["binan"])
        bin_prev, _ = asof_with_staleness(binan, prev_cut, 5 * 24 * 60)
        bloom_prev = bloom.loc[:prev_cut]
        bloom_prev_px = bloom_prev.iloc[-1] if not bloom_prev.empty else np.nan

        # --- vol realizada overnight do 6L (último pregão 17:58 -> snapshot);
        #     janela de 1h era inviável (6L fino às 5-6am CT)
        win = fut_usdbrl.loc[prev_cut:snap]
        vol_1h = np.log(win).diff().std() if len(win) >= 10 else np.nan
        n_ticks_1h = len(win)

        # --- dummy de evento macro (calendário conhecido ex-ante)
        ev = macro[macro["published_at"].dt.date == d.date()]
        event_day = int(len(ev) > 0)
        # valores macro informativos: último PUBLICADO até o snapshot
        pub = macro[macro["published_at"] <= snap]
        def last_pub(s):
            x = pub[pub["series"] == s]
            return x["value"].iloc[-1] if len(x) else np.nan
        us_gdp_last = last_pub("US_GDP_REAL_QOQ_ANN")
        br_pib_last = last_pub("BR_PIB_REAL_QOQ")

        rows.append({
            "date": d.date(),
            # target e âncora
            "open_bloom": open_px, "open_ts": open_ts,
            "dolar_cc_snap": dolar_cc,
            "y_log_resid": np.log(open_px) - np.log(dolar_cc),
            # features do consenso
            "ret_fut_on": np.log(fut_px / fut_prev) if fut_prev else np.nan,
            "ret_dxy_on": np.log(dxy_now / dxy_prev) if dxy_prev else np.nan,
            "vol_6l_on": vol_1h,
            "event_day": event_day,
            # bloco USDT/BRL (ablação — ver ressalva no README)
            "ret_usdt_on": np.log(bin_now / bin_prev) if bin_prev else np.nan,
            "usdt_premium_snap": (bin_now - bloom_prev_px) / bloom_prev_px if bloom_prev_px else np.nan,
            # informativas / auditoria (NÃO são features do modelo)
            "fut_snap_px": fut_px, "fut_snap_ts": fut_ts, "fut_stale_min": fut_stale,
            "dxy_stale_min": dxy_stale, "binan_stale_min": bin_stale,
            "n_ticks_6l_1h": n_ticks_1h,
            "selic": selic_d, "us_rate_pit": us_pit, "du_to_expiry": du,
            "cc_vintage_diff_bp": (dolar_cc - fut_px / cc_naive) / dolar_cc * 1e4,
            "us_gdp_real_last": us_gdp_last, "br_pib_real_last": br_pib_last,
        })

    df = pd.DataFrame(rows).set_index("date")

    # basis defasada + feriados assimétricos (gap >1 dia útil entre linhas consecutivas)
    idx = pd.to_datetime(df.index)
    gap_bd = [np.busday_count(a.date(), b.date()) for a, b in zip(idx[:-1], idx[1:])]
    df["asym_gap"] = [0] + [int(g > 1) for g in gap_bd]
    df["basis_lag1"] = df["y_log_resid"].shift(1)
    df.loc[df["asym_gap"] == 1, "basis_lag1"] = 0.0   # regime de carrego misto -> neutraliza
    df.loc[df.index[0], "basis_lag1"] = 0.0

    # ---------------- asserts anti-leakage ----------------
    snap_ts = pd.to_datetime([f"{d} {SNAPSHOT}" for d in df.index])
    assert (pd.to_datetime(df["fut_snap_ts"].values) <= snap_ts).all(), "6L snapshot > 08:50!"
    assert (pd.to_datetime(df["open_ts"].values) >= pd.to_datetime(
        [f"{d} {OPEN_TIME}" for d in df.index])).all(), "target antes das 09:00!"
    assert (macro[macro["published_at"] <= pd.Timestamp("2024-12-31")]["published_at"]
            .dt.time.astype(str) != "").all()

    out = os.path.join(PROC, "dataset_daily.csv")
    df.to_csv(out)

    # ---------------- sumário ----------------
    model_feats = ["ret_fut_on", "ret_dxy_on", "vol_6l_on", "event_day", "basis_lag1"]
    print(f"\nDataset salvo: {out}")
    print(f"Linhas: {len(df)} | dias pulados: {len(skipped)}")
    for d, r in skipped:
        print(f"  - {d}: {r}")
    print(f"\nNaN nas features do modelo:\n{df[model_feats + ['ret_usdt_on']].isna().sum()}")
    print(f"\nTarget y_log_resid (bps): media={df['y_log_resid'].mean()*1e4:.1f}, "
          f"sd={df['y_log_resid'].std()*1e4:.1f}, |max|={df['y_log_resid'].abs().max()*1e4:.1f}")
    print(f"Staleness 6L às 8:50 (min): mediana={df['fut_stale_min'].median():.0f}, "
          f"p95={df['fut_stale_min'].quantile(.95):.0f}")
    print(f"Auditoria vintage cupom (dolar_cc PIT vs ingênuo, bps): "
          f"|max|={df['cc_vintage_diff_bp'].abs().max():.2f}")
    print(f"Horário real da abertura: {pd.to_datetime(df['open_ts']).dt.time.value_counts().head(3).to_dict()}")
    print(f"Dias de evento macro: {df['event_day'].sum()}")

if __name__ == "__main__":
    main()
