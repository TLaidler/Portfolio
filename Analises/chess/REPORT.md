# A inflação silenciosa dos percentis: o que um rating da Chess.com significa ao longo dos anos

*Relatório gerado automaticamente em 2026-07-21.*

## 1. Dados coletados

- **Observações válidas:** 66
- **Anomalias descartadas** (violação grosseira de monotonicidade): 0
- **Período coberto:** 2016-07-01 a 2026-03-11

Funil de limpeza: input 66 → after_range_filter 66 → after_date_filter 66 → after_rated_count_filter 66 → after_dedup 66 → after_anomaly_filter 66

### Observações por fonte

| source | n | confianca | de | ate |
|---|---|---|---|---|
| forum | 60 | 0.50 | 2016-07-01 | 2025-11-01 |
| manual | 6 | 0.80 | 2026-03-11 | 2026-03-11 |

### Observações por ano × modalidade (Chess.com)

| year | blitz | daily | rapid |
|---|---|---|---|
| 2016 | 0 | 0 | 1 |
| 2017 | 2 | 0 | 0 |
| 2018 | 1 | 0 | 0 |
| 2019 | 1 | 0 | 1 |
| 2020 | 3 | 1 | 0 |
| 2021 | 0 | 0 | 2 |
| 2022 | 0 | 0 | 5 |
| 2023 | 0 | 1 | 19 |
| 2024 | 1 | 0 | 3 |
| 2025 | 1 | 0 | 0 |

## 2. Metodologia

1. **Fonte primária** — snapshots da Wayback Machine de páginas públicas de estatísticas de jogadores da Chess.com (`chess.com/stats/...`). Cada página arquivada embute o JSON oficial com `rating` e `percentile` do jogador na data da captura — ou seja, o percentil é o calculado pela própria Chess.com sobre toda a base de membros, e a amostragem do Wayback afeta apenas ONDE na curva enxergamos pontos, não o valor deles. O campo existe nas páginas desde ~janeiro de 2021; anos anteriores dependem de fontes secundárias.
2. **Fontes secundárias** — tabelas históricas do ChessGoals (via Wayback), relatos datados no Reddit/StackExchange e URLs curadas manualmente; todas recebem score de confiança menor e entram como peso na regressão.
3. **Semântica do percentil** — convenção clássica (percentual de membros com rating igual ou inferior), verificada empiricamente em snapshots de jogadores fracos (ex.: rating 397 → percentil 8,5) e fortes (2118 → 99,9).
4. **Limpeza** — filtros de faixa, deduplicação, exclusão de contas com menos de 10 partidas ranqueadas (percentil provisório) e descarte de observações cujo resíduo contra um ajuste isotônico preliminar excede 25 pontos percentuais (bugs do próprio site aparecem nos snapshots).
5. **Reconstrução** — por (plataforma × modalidade × ano): regressão isotônica ponderada pela confiança (garante curva não-decrescente) suavizada por PCHIP; inversa por interpolação. Incerteza via bootstrap (300 reamostragens, IC 95%). Nunca extrapolamos além da faixa de ratings observada na célula.

Scores de confiança: 1.0 = oficial (snapshot Wayback de página da Chess.com); 0.9 = tabela agregada publicada (ChessGoals e similares); 0.7 = relato de usuário datado (Reddit); 0.6 = texto livre (fóruns/StackExchange/manuais); 0.4 = sem data precisa.

## 3. Resultados

### Rapid — percentil de ratings fixos por ano

| rating | 2022 | 2023 |
|---|---|---|
| 800 | — | 66.3 |
| 1000 | — | 81.0 |
| 1200 | 89.9 | 90.4 |
| 1500 | 97.0 | 97.0 |
| 1800 | 99.3 | 99.5 |
| 2000 | 99.8 | 99.9 |

### Rapid — rating necessário para cada Top X% por ano

| Top % | 2022 | 2023 |
|---|---|---|
| 50 | — | 633 |
| 25 | — | 906 |
| 10 | 1202 | 1190 |
| 5 | 1379 | 1357 |
| 1 | 1732 | 1715 |
| 0 | 1860 | 1801 |
| 0 | — | 2039 |

## 4. Conclusões principais

- **Top 1% (Rapid):** exigia ~1732 em 2022; exige ~1715 em 2023 (-17 pontos).

*(Interprete junto com os ICs nas figuras `figures/` e as contagens de observações acima.)*

## 5. Limitações e nível de confiança

- **Cobertura temporal assimétrica:** a fonte primária só existe a partir de ~2021 (antes disso a página de stats não publicava percentil). Conclusões pré-2021 apoiam-se em fontes secundárias, mais esparsas — trate-as como indicativas, não definitivas.
- **Amostragem do Wayback não é aleatória** (jogadores arquivados tendem a ser mais ativos). Isso concentra pontos em certas faixas de rating, alargando o IC nas caudas, mas NÃO enviesa o valor do percentil de cada ponto (que é oficial).
- **Mudanças estruturais da plataforma** (rating inicial padrão, tratamento de contas inativas, crescimento explosivo pós-2020) alteram a base sobre a qual a Chess.com calcula percentis; as curvas refletem essas mudanças, e é exatamente isso que medimos — o significado RELATIVO de um rating em cada momento.
- **Ratings extremos (>2400 ou <400)** têm poucas observações; os alvos Top 0,5% e 0,1% só são reportados quando caem dentro da faixa observada, e mesmo assim com ICs largos.
- Células marcadas `low_confidence` (n < 15) aparecem com asterisco nas figuras.

## 6. Reprodutibilidade

Pipeline completo: `python main.py all` (coleta é resumível — cache SQLite em `data/raw/cache.db`). Estágios individuais: `collect`, `parse`, `clean`, `fit`, `viz`, `report`. Dados intermediários em `data/processed/`.
