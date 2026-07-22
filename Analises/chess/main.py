"""Pipeline CLI: reconstrução histórica da distribuição de ratings da Chess.com.

Estágios (cada um lê os artefatos do anterior; a coleta é resumível):

    python main.py collect   # Wayback CDX + snapshots + fontes atuais -> cache
    python main.py parse     # cache -> data/processed/observations_raw.csv
    python main.py clean     # -> observations_clean.csv (+ anomalias)
    python main.py fit       # -> curves.csv, targets.csv, fixed_ratings.csv
    python main.py viz       # -> figures/*.png|.html
    python main.py report    # -> REPORT.md
    python main.py all
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.archive import (
    WaybackClient,
    append_to_index,
    read_index,
)
from src.chesscom import ChessComClient
from src.parser import (
    decode_html,
    parse_chesscom_stats_page,
    parse_chessgoals_tables,
    parse_lichess_distribution,
    snapshot_date_from_fetch_url,
)
from src.scraper import (
    RedditSearcher,
    StackExchangeSearcher,
    fetch_current_lichess,
    fetch_extra_urls,
)
from src.statistics import (
    clean_observations,
    curves_long_frame,
    fit_cells,
    fixed_ratings_frame,
    flag_anomalies,
    load_observations,
    observations_to_frame,
    percentile_targets_frame,
)
from src.utils import (
    DATA_PROCESSED,
    DATA_RAW,
    GAME_TYPES,
    CachedSession,
    get_logger,
)

log = get_logger("main")

RAW_OBS = DATA_PROCESSED / "observations_raw.csv"
CLEAN_OBS = DATA_PROCESSED / "observations_clean.csv"
DROPPED_OBS = DATA_PROCESSED / "observations_dropped.csv"
CLEAN_STATS = DATA_PROCESSED / "clean_stats.json"
CURVES = DATA_PROCESSED / "curves.csv"
TARGETS = DATA_PROCESSED / "targets.csv"
FIXED = DATA_PROCESSED / "fixed_ratings.csv"
MANUAL_OBS = DATA_RAW / "manual_observations.csv"


# ---------------------------------------------------------------------------
# collect
# ---------------------------------------------------------------------------
def stage_collect(args: argparse.Namespace) -> None:
    http = CachedSession()
    wb = WaybackClient(http)

    years = range(args.year_from, args.year_to + 1)
    game_types = args.game_types.split(",")

    # 1. páginas de stats de jogadores (fonte primária)
    # índice ANTES do download: interrupções não perdem trabalho (cache resume)
    if not args.skip_stats:
        for gt in game_types:
            for year in years:
                rows = wb.sample_stats_snapshots(gt, year, target=args.per_year)
                if not rows:
                    continue
                append_to_index([
                    dict(kind="stats", source="wayback_stats", game_type=gt,
                         timestamp=r.timestamp, original=r.original,
                         fetch_url=r.fetch_url, status=200)
                    for r in rows
                ])
                wb.download(rows, desc=f"{gt}/{year}")

    # 2. páginas agregadas (chessgoals, distribuição da lichess)
    if not args.skip_aggregates:
        agg = wb.list_aggregate_snapshots()
        append_to_index([
            dict(kind="aggregate", source=source, game_type=gt or "",
                 timestamp=r.timestamp, original=r.original,
                 fetch_url=r.fetch_url, status=200)
            for source, gt, r in agg
        ])
        wb.download([r for _, _, r in agg], desc="agregados")

    # 3. páginas de stats ATUAIS dos mesmos usuários (curva de hoje)
    if not args.skip_live:
        cc = ChessComClient(http)
        stats_urls = [e["original"] for e in read_index() if e["kind"] == "stats"]
        cc.fetch_current_stats_observations(stats_urls, limit_per_type=args.live_per_type)

    http.close()
    log.info("collect concluído — índice: %d entradas", len(read_index()))


# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------
def stage_parse(args: argparse.Namespace) -> None:
    http = CachedSession()
    observations = []

    index = read_index()
    log.info("parse: %d entradas no índice", len(index))
    from tqdm import tqdm

    for entry in tqdm(index, desc="parse snapshots", unit="snap"):
        status, body = http.get(entry["fetch_url"])
        if status != 200 or not body:
            continue
        snap_date = snapshot_date_from_fetch_url(entry["fetch_url"])
        if snap_date is None:
            continue
        html = decode_html(body)
        if entry["kind"] == "stats":
            obs = parse_chesscom_stats_page(html, entry["original"], snap_date)
            if obs:
                observations.append(obs)
        elif entry["source"] == "chessgoals":
            observations.extend(parse_chessgoals_tables(html, entry["original"], snap_date))
        elif entry["source"] == "lichess_dist":
            observations.extend(
                parse_lichess_distribution(html, entry["original"], snap_date,
                                           entry["game_type"] or "blitz")
            )

    # fontes atuais e secundárias (rede com cache)
    if not args.skip_live:
        cc = ChessComClient(http)
        stats_urls = [e["original"] for e in index if e["kind"] == "stats"]
        observations.extend(
            cc.fetch_current_stats_observations(stats_urls, limit_per_type=args.live_per_type)
        )
        observations.extend(fetch_current_lichess(http))
    observations.extend(RedditSearcher(http).search())
    observations.extend(StackExchangeSearcher(http).search())
    observations.extend(fetch_extra_urls(http))
    http.close()

    df = observations_to_frame(observations)

    # observações manuais (curadas a partir da pesquisa do agente)
    if MANUAL_OBS.exists():
        manual = pd.read_csv(MANUAL_OBS, parse_dates=["date"])
        manual["note"] = manual.get("note", "").fillna("") if "note" in manual else ""
        df = pd.concat([df, manual], ignore_index=True)
        log.info("manuais: +%d observações", len(manual))

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_OBS, index=False)
    log.info("parse: %d observações -> %s", len(df), RAW_OBS)


# ---------------------------------------------------------------------------
# clean / fit / viz / report
# ---------------------------------------------------------------------------
def stage_clean(args: argparse.Namespace) -> None:
    df = load_observations(RAW_OBS)
    clean, stats = clean_observations(df)
    kept, dropped = flag_anomalies(clean)
    stats["after_anomaly_filter"] = len(kept)
    kept.to_csv(CLEAN_OBS, index=False)
    dropped.to_csv(DROPPED_OBS, index=False)
    CLEAN_STATS.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    log.info("clean: %s", stats)


def stage_fit(args: argparse.Namespace) -> None:
    df = load_observations(CLEAN_OBS)
    df["year"] = df["date"].dt.year
    fits = fit_cells(df, n_boot=args.n_boot)
    curves_long_frame(fits).to_csv(CURVES, index=False)
    percentile_targets_frame(fits).to_csv(TARGETS, index=False)
    fixed_ratings_frame(fits).to_csv(FIXED, index=False)
    log.info("fit: %d células -> %s, %s, %s", len(fits), CURVES.name, TARGETS.name, FIXED.name)


def stage_viz(args: argparse.Namespace) -> None:
    from src.visualization import generate_all

    curves = pd.read_csv(CURVES)
    targets = pd.read_csv(TARGETS)
    fixed = pd.read_csv(FIXED)
    paths = generate_all(curves, targets, fixed)
    log.info("viz: %d figuras geradas", len(paths))


def stage_report(args: argparse.Namespace) -> None:
    from src.report import build_report

    obs = load_observations(CLEAN_OBS)
    obs["year"] = obs["date"].dt.year
    dropped = (
        load_observations(DROPPED_OBS)
        if DROPPED_OBS.exists() and DROPPED_OBS.stat().st_size > 10
        else obs.iloc[0:0]
    )
    stats = json.loads(CLEAN_STATS.read_text(encoding="utf-8")) if CLEAN_STATS.exists() else {}
    build_report(
        obs, dropped,
        pd.read_csv(TARGETS), pd.read_csv(FIXED),
        stats,
    )


STAGES = {
    "collect": stage_collect,
    "parse": stage_parse,
    "clean": stage_clean,
    "fit": stage_fit,
    "viz": stage_viz,
    "report": stage_report,
}


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("stage", choices=[*STAGES, "all"])
    p.add_argument("--year-from", type=int, default=2017)
    p.add_argument("--year-to", type=int, default=date.today().year)
    p.add_argument("--per-year", type=int, default=250,
                   help="snapshots de stats por modalidade por ano")
    p.add_argument("--game-types", default=",".join(GAME_TYPES))
    p.add_argument("--live-per-type", type=int, default=200,
                   help="páginas atuais da chess.com por modalidade")
    p.add_argument("--skip-live", action="store_true",
                   help="não buscar páginas atuais da chess.com/lichess")
    p.add_argument("--skip-stats", action="store_true",
                   help="collect: pular snapshots de stats de jogadores")
    p.add_argument("--skip-aggregates", action="store_true",
                   help="collect: pular páginas agregadas (chessgoals/lichess)")
    p.add_argument("--n-boot", type=int, default=300, help="reamostragens bootstrap")
    return p


def main() -> None:
    args = build_argparser().parse_args()
    stages = list(STAGES) if args.stage == "all" else [args.stage]
    for name in stages:
        log.info("=== estágio: %s ===", name)
        STAGES[name](args)


if __name__ == "__main__":
    main()
