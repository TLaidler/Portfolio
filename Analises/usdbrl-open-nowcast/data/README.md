# Data

## `processed/dataset_daily.csv` (committed)

One row per trading day (Dec 2023 → Aug 2024, 154 rows). Built by `src/build_dataset.py`
with a strict 8:50 BRT point-in-time snapshot. Columns:

| Group | Columns |
|---|---|
| Target & anchor | `open_bloom`, `open_ts`, `dolar_cc_snap`, `y_log_resid` |
| Model features | `ret_fut_on`, `ret_dxy_on`, `vol_6l_on`, `event_day`, `basis_lag1`, `asym_gap` |
| USDT block (ablation only) | `ret_usdt_on`, `usdt_premium_snap` |
| Audit / info | `fut_snap_ts`, `*_stale_min`, `selic`, `us_rate_pit`, `du_to_expiry`, `cc_vintage_diff_bp`, `us_gdp_real_last`, `br_pib_real_last` |

## `reference/` (committed)

- `macro_releases.csv` — hand-curated macro release calendar (US real GDP, BR real GDP,
  CPI, IPCA, payrolls, COPOM/FOMC decisions and minutes) with **publication timestamps in BRT**.
  Values were curated from public release archives (BEA/IBGE/BLS/BCB/Fed); double-check
  before production use.
- `dgs1mo_gap_fill.csv` — DGS1MO 2024-07-19 → 2024-08-08 from FRED's public CSV endpoint,
  validated against the local series at the seam.

## `raw/` (NOT versioned)

Licensed tick data. To rebuild `dataset_daily.csv`, point the two env vars at local folders:

- `USDBRL_RAW_CONTRACTS` — monthly CME 6L contract files (`janeiro_futuro_BRLUSD.csv` …
  `outubro_futuro_BRLUSD.csv`; 1-min, BRT timestamps; mixed separators/date formats are
  handled by the loader).
- `USDBRL_RAW_MARKET` — market CSVs: `usdbrl_bloom.csv` (1-min USDBRL spot, BRT),
  `DXY.csv` (1-min, BRT−3h convention), `binance-usdtbrl-1.csv` (1-min OHLCV, UTC),
  `selic.csv` (daily), `treasury_bond_1m.csv` (daily FRED DGS1MO).

Timezone conventions were validated empirically (see
`docs/debate_transcript.md`): Binance = UTC (matched minute volumes), DXY = BRT−3h
(matched the Friday 17:00 ET FX close), raw contracts and Bloomberg = BRT.
