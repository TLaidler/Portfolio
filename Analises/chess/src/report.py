"""Geração automática do relatório final em Markdown (``REPORT.md``)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from .utils import PROJECT_ROOT, get_logger

log = get_logger(__name__)

REPORT_PATH = PROJECT_ROOT / "REPORT.md"

CONFIDENCE_LABELS = [
    (1.0, "oficial (snapshot Wayback de página da Chess.com)"),
    (0.9, "tabela agregada publicada (ChessGoals e similares)"),
    (0.7, "relato de usuário datado (Reddit)"),
    (0.6, "texto livre (fóruns/StackExchange/manuais)"),
    (0.4, "sem data precisa"),
]


def _md_table(df: pd.DataFrame, float_fmt: str = "{:.1f}") -> str:
    def fmt(v):
        if isinstance(v, float):
            return float_fmt.format(v) if pd.notna(v) else "—"
        return str(v)

    header = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "|".join(["---"] * len(df.columns)) + "|"
    rows = ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([header, sep, *rows])


def build_report(
    observations: pd.DataFrame,
    dropped: pd.DataFrame,
    targets: pd.DataFrame,
    fixed: pd.DataFrame,
    clean_stats: dict,
) -> Path:
    obs = observations
    today = date.today().isoformat()

    lines: list[str] = []
    add = lines.append

    add("# A inflação silenciosa dos percentis: o que um rating da Chess.com significa ao longo dos anos")
    add("")
    add(f"*Relatório gerado automaticamente em {today}.*")
    add("")

    # ------------------------------------------------------------------ dados
    add("## 1. Dados coletados")
    add("")
    add(f"- **Observações válidas:** {len(obs):,}".replace(",", "."))
    add(f"- **Anomalias descartadas** (violação grosseira de monotonicidade): {len(dropped):,}".replace(",", "."))
    add(f"- **Período coberto:** {obs.date.min().date()} a {obs.date.max().date()}")
    add("")
    add("Funil de limpeza: " + " → ".join(f"{k} {v:,}".replace(",", ".") for k, v in clean_stats.items()))
    add("")
    add("### Observações por fonte")
    add("")
    by_source = (
        obs.groupby("source")
        .agg(n=("rating", "size"), confianca=("confidence", "first"),
             de=("date", "min"), ate=("date", "max"))
        .reset_index()
    )
    by_source["de"] = by_source["de"].dt.date
    by_source["ate"] = by_source["ate"].dt.date
    add(_md_table(by_source, "{:.2f}"))
    add("")
    add("### Observações por ano × modalidade (Chess.com)")
    add("")
    pivot = (
        obs[obs.platform == "chesscom"]
        .pivot_table(index="year", columns="game_type", values="rating", aggfunc="size", fill_value=0)
        .reset_index()
    )
    add(_md_table(pivot, "{:.0f}"))
    add("")

    # ------------------------------------------------------------- metodologia
    add("## 2. Metodologia")
    add("")
    add(
        "1. **Fonte primária** — snapshots da Wayback Machine de páginas públicas de "
        "estatísticas de jogadores da Chess.com (`chess.com/stats/...`). Cada página "
        "arquivada embute o JSON oficial com `rating` e `percentile` do jogador na "
        "data da captura — ou seja, o percentil é o calculado pela própria Chess.com "
        "sobre toda a base de membros, e a amostragem do Wayback afeta apenas ONDE na "
        "curva enxergamos pontos, não o valor deles. O campo existe nas páginas desde "
        "~janeiro de 2021; anos anteriores dependem de fontes secundárias."
    )
    add(
        "2. **Fontes secundárias** — tabelas históricas do ChessGoals (via Wayback), "
        "relatos datados no Reddit/StackExchange e URLs curadas manualmente; todas "
        "recebem score de confiança menor e entram como peso na regressão."
    )
    add(
        "3. **Semântica do percentil** — convenção clássica (percentual de membros com "
        "rating igual ou inferior), verificada empiricamente em snapshots de jogadores "
        "fracos (ex.: rating 397 → percentil 8,5) e fortes (2118 → 99,9)."
    )
    add(
        "4. **Limpeza** — filtros de faixa, deduplicação, exclusão de contas com menos "
        "de 10 partidas ranqueadas (percentil provisório) e descarte de observações "
        "cujo resíduo contra um ajuste isotônico preliminar excede 25 pontos "
        "percentuais (bugs do próprio site aparecem nos snapshots)."
    )
    add(
        "5. **Reconstrução** — por (plataforma × modalidade × ano): regressão isotônica "
        "ponderada pela confiança (garante curva não-decrescente) suavizada por PCHIP; "
        "inversa por interpolação. Incerteza via bootstrap (300 reamostragens, IC 95%). "
        "Nunca extrapolamos além da faixa de ratings observada na célula."
    )
    add("")
    add("Scores de confiança: " + "; ".join(f"{c:.1f} = {d}" for c, d in CONFIDENCE_LABELS) + ".")
    add("")

    # ------------------------------------------------------------- resultados
    add("## 3. Resultados")
    add("")
    ch = fixed[(fixed.platform == "chesscom")]
    for gt in sorted(ch.game_type.unique()):
        g = ch[ch.game_type == gt]
        years = sorted(g.year.unique())
        if len(years) < 2:
            continue
        add(f"### {gt.capitalize()} — percentil de ratings fixos por ano")
        add("")
        p = g.pivot_table(index="rating", columns="year", values="percentile_est").round(1).reset_index()
        p["rating"] = p["rating"].astype(int)
        add(_md_table(p))
        add("")

    tg = targets[targets.platform == "chesscom"]
    for gt in sorted(tg.game_type.unique()):
        g = tg[tg.game_type == gt]
        if g.year.nunique() < 2:
            continue
        add(f"### {gt.capitalize()} — rating necessário para cada Top X% por ano")
        add("")
        p = g.pivot_table(index="top_share", columns="year", values="rating_est").round(0).reset_index()
        p = p.sort_values("top_share", ascending=False)
        p = p.rename(columns={"top_share": "Top %"})
        add(_md_table(p, "{:.0f}"))
        add("")

    # conclusões quantitativas automáticas (rating 1000, rapid)
    add("## 4. Conclusões principais")
    add("")
    focus = ch[(ch.game_type == "rapid") & (ch.rating == 1000)].sort_values("year")
    if len(focus) >= 2:
        first, last = focus.iloc[0], focus.iloc[-1]
        delta = last.percentile_est - first.percentile_est
        direction = "SUBIU" if delta > 0 else "CAIU"
        add(
            f"- **Rating 1000 (Rapid):** percentil {first.percentile_est:.1f} em "
            f"{int(first.year)} → {last.percentile_est:.1f} em {int(last.year)} "
            f"({direction} {abs(delta):.1f} p.p.). "
            + (
                "Um jogador de 1000 hoje está em posição relativa "
                + ("melhor" if delta > 0 else "pior")
                + " do que no início da janela observada."
            )
        )
    top1 = tg[(tg.game_type == "rapid") & (tg.top_share == 1.0)].sort_values("year")
    if len(top1) >= 2:
        f_, l_ = top1.iloc[0], top1.iloc[-1]
        d = l_.rating_est - f_.rating_est
        add(
            f"- **Top 1% (Rapid):** exigia ~{f_.rating_est:.0f} em {int(f_.year)}; "
            f"exige ~{l_.rating_est:.0f} em {int(l_.year)} "
            f"({'+' if d >= 0 else ''}{d:.0f} pontos)."
        )
    add("")
    add("*(Interprete junto com os ICs nas figuras `figures/` e as contagens de observações acima.)*")
    add("")

    # ------------------------------------------------------------- limitações
    add("## 5. Limitações e nível de confiança")
    add("")
    add(
        "- **Cobertura temporal assimétrica:** a fonte primária só existe a partir de "
        "~2021 (antes disso a página de stats não publicava percentil). Conclusões "
        "pré-2021 apoiam-se em fontes secundárias, mais esparsas — trate-as como "
        "indicativas, não definitivas."
    )
    add(
        "- **Amostragem do Wayback não é aleatória** (jogadores arquivados tendem a ser "
        "mais ativos). Isso concentra pontos em certas faixas de rating, alargando o IC "
        "nas caudas, mas NÃO enviesa o valor do percentil de cada ponto (que é oficial)."
    )
    add(
        "- **Mudanças estruturais da plataforma** (rating inicial padrão, tratamento de "
        "contas inativas, crescimento explosivo pós-2020) alteram a base sobre a qual a "
        "Chess.com calcula percentis; as curvas refletem essas mudanças, e é exatamente "
        "isso que medimos — o significado RELATIVO de um rating em cada momento."
    )
    add(
        "- **Ratings extremos (>2400 ou <400)** têm poucas observações; os alvos Top "
        "0,5% e 0,1% só são reportados quando caem dentro da faixa observada, e mesmo "
        "assim com ICs largos."
    )
    add(
        "- Células marcadas `low_confidence` (n < 15) aparecem com asterisco nas figuras."
    )
    add("")
    add("## 6. Reprodutibilidade")
    add("")
    add(
        "Pipeline completo: `python main.py all` (coleta é resumível — cache SQLite em "
        "`data/raw/cache.db`). Estágios individuais: `collect`, `parse`, `clean`, "
        "`fit`, `viz`, `report`. Dados intermediários em `data/processed/`."
    )
    add("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    log.info("relatório: %s", REPORT_PATH)
    return REPORT_PATH
