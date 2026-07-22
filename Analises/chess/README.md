# Evolução da Distribuição de Ratings da Chess.com (2016–2026)

Reconstrução histórica, baseada em evidências, da distribuição de ratings da
Chess.com — para responder quantitativamente:

> **"O significado competitivo de um determinado rating mudou ao longo dos anos?"**

Spoiler (ver `REPORT.md` para os números e incertezas): sim — um rating 1000
de Rapid saiu de ~percentil 39 (2016) para ~percentil 80+ (2024+), impulsionado
por mudanças no rating inicial padrão, pelo influxo de iniciantes pós-2020 e
pela reclassificação do time control 10|0 (set/2020).

## Como funciona

### Fontes de dados

| Fonte | O quê | Confiança |
|---|---|---|
| **Wayback Machine × páginas de stats** | Snapshots de `chess.com/stats/{live/rapid,live/blitz,live/bullet,daily}/<user>` contêm JSON oficial com `rating` e `percentile` do jogador na data da captura (campo existe desde ~jan/2021) | 1.0 |
| **Páginas atuais da Chess.com** | Mesmos usuários, página de hoje → curva atual | 1.0 |
| **Lichess `stat/rating/distribution/*`** | Histograma semanal oficial completo (atual + Wayback mensal desde 2016) | 1.0 |
| **Tabelas agregadas** (ChessGoals via Wayback) | Percentil × rating publicados periodicamente | 0.9 |
| **Fóruns/Reddit/StackExchange** | Relatos datados "rating X = percentil Y" | 0.4–0.85 |
| **`data/raw/manual_observations.csv`** | Pares curados de threads históricas (cobre 2016–2020, antes da fonte primária) | 0.45–0.85 |

Convenção de percentil: **clássica** (% de jogadores com rating ≤ X) — a mesma
usada pela Chess.com, verificada empiricamente (jogador 397 → 8.5; 2118 → 99.9).

### Metodologia estatística

Por (plataforma × modalidade × ano): regressão **isotônica** ponderada pela
confiança → suavização **PCHIP** (monotônica) → inversa por interpolação →
**bootstrap** (300×, IC 95%). Anomalias (resíduo > 25 p.p. contra ajuste
preliminar) são descartadas e registradas. Nunca extrapolamos além da faixa de
ratings observada em cada célula.

## Uso

```bash
pip install -r requirements.txt

python main.py all              # pipeline completo
# ou por estágio:
python main.py collect          # Wayback/CDX + fontes atuais (horas; resumível)
python main.py parse            # -> data/processed/observations_raw.csv
python main.py clean            # -> observations_clean.csv (+ anomalias)
python main.py fit              # -> curves.csv, targets.csv, fixed_ratings.csv
python main.py viz              # -> figures/*.png + *.html (plotly)
python main.py report           # -> REPORT.md
```

Opções úteis: `--per-year 150` (snapshots por modalidade/ano), `--game-types
rapid,blitz`, `--year-from/--year-to`, `--skip-live`, `--n-boot`.

A coleta usa cache SQLite (`data/raw/cache.db`) com rate-limit educado
(~1 req/s por host) — pode ser interrompida e retomada à vontade.

## Estrutura

```
src/
  utils.py          # Observation, sessão HTTP cacheada, rate-limit
  archive.py        # CDX API + amostragem estratificada + download
  chesscom.py       # páginas atuais da Chess.com (Pub API não tem percentil)
  scraper.py        # Reddit, StackExchange, Lichess atual, URLs extras
  parser.py         # extratores por era (JSON embutido, texto livre, lichess)
  statistics.py     # limpeza, anomalias, ajuste por célula, bootstrap
  interpolation.py  # isotônica + PCHIP + inversa
  visualization.py  # matplotlib + plotly (paleta validada p/ daltonismo)
  report.py         # REPORT.md automático
tests/              # pytest com fixtures de HTML real
data/raw/           # cache, índice de snapshots, achados da pesquisa
data/processed/     # observações e curvas
figures/            # PNG + HTML interativo
notebooks/          # exploração
```

## Notas de engenharia

- Requer Python ≥ 3.11.
- Snapshots do Wayback são baixados com sufixo `id_` (bytes originais, sem
  toolbar); alguns vêm gzip cru — o parser descomprime por magic bytes.
- O eixo da distribuição do Lichess começa em **800 antes de 2019-07-01 e 600
  depois** (mudança do piso de rating; lila commit `67637670e8`) — o parser
  ajusta pelo timestamp do snapshot.
- Páginas de stats da era Angular (2018–2020) não publicavam percentil; por
  isso os anos pré-2021 dependem das fontes secundárias curadas.
- Contas com < 10 partidas ranqueadas são descartadas (percentil provisório).
