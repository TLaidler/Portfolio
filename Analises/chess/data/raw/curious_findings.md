# Curious Findings — Chess.com / Lichess rating→percentile histórico

Coletado em 2026-07-21 por agente de pesquisa web. Convenção: `percentil` = % de jogadores ABAIXO do rating; quando a fonte diz "top X%", anotado como `top_x=X`.

## 1. Reddit — menções datadas de rating + percentil

| url | data | modalidade | rating | percentil | confiança | nota |
|---|---|---|---|---|---|---|

## 2. Fóruns Chess.com — tabelas de distribuição/percentil

| url | data | modalidade | rating | percentil | confiança | nota |
|---|---|---|---|---|---|---|
| https://www.chess.com/forum/view/general/til-5-years-ago-a-1000-rapid-rating-was-49th-percentile-today-its-the-81st | 2024-08-16 (post) | rapid | 1000 | 81 (em 2024) | alta | **FONTE-CHAVE**: OP compara 1000 rapid ao longo do tempo |
| (mesma thread acima) | ~2019 (referido) | rapid | 1000 | 49 | média | "5 anos atrás" = ~2019; OP não cita fonte direta (provável Wayback da página de stats) — verificar no Wayback |
| (mesma thread acima) | ~2016 (referido) | rapid | 1000 | 39 | média | "8 anos atrás" = ~2016 |
| https://www.chess.com/forum/view/community/ratings-distribution-across-the-chess-com-community | 2022-12-28 (tabela; thread 2022-09-24) | rapid | 1200 | 89.92 | alta | **FONTE-CHAVE**: tabela completa 100–3400, ~15.3M jogadores rapid |
| (mesma thread acima) | 2022-12-28 | rapid | 1400 | 95.40 | alta | |
| (mesma thread acima) | 2022-12-28 | rapid | 1600 | 98.09 | alta | |
| (mesma thread acima) | 2022-12-28 | rapid | 1800 | 99.30 | alta | |
| (mesma thread acima) | 2022-12-28 | rapid | 2000 | 99.79 | alta | |
| https://www.chess.com/forum/view/community/chess-com-rating-distribution | 2023-05 | rapid | 664 (média) | — | alta | Martin_Stahl (staff): média rapid 664, pool ~51M jogadores |
| https://www.chess.com/forum/view/community/chess-com-rating-distribution | 2024-09 | rapid | ~620 | 50 | média | usuário basketstorm reporta mediana ~620 |
| https://www.chess.com/forum/view/livechess/blitz-stats-what-s-up-with-the-percentile | 2016-12-20 | blitz | rank 401.930 de 2.346.931 | 62.1 (exibido) vs 82.9 (rank-based) | alta | **pool blitz dez/2016 ≈ 2,35M**; percentil exibido já divergia do rank simples em 2016 (pool/critério diferente) |
| https://www.chess.com/forum/view/general/blitz-ratings-and-percentile | 2013-11-03 | blitz | — | — | média | sem números, mas confirma que em 2013 a página "view stats → view all players" mostrava a curva de distribuição completa com percentil por rating — alvo de Wayback |
| https://www.chess.com/forum/view/livechess/rating-distribution-graph | 2017-11-27 | live (provável blitz — confirmar) | 800 | 25 | alta | **FONTE-CHAVE pré-boom**: OP relata percentil exibido no site em 2017 |
| (mesma thread acima) | 2017-11-27 | live (provável blitz) | 1000 | 33 | alta | idem; par consistente com 1000 rapid=39th em 2016 do TIL |
| https://www.chess.com/forum/view/community/about-the-percentile-in-stats | 2024-02-20 | rapid | 1745 | 98.7 | alta | Jani_1987; mesmo rating era 99.2 em 2023-03 |
| (mesma thread acima) | 2023-03 | rapid | 1745 | 99.2 | alta | |
| (mesma thread acima) | 2023-03 | rapid | 1801 | 99.5 | alta | série de cortes de percentil alto de mar/2023 |
| (mesma thread acima) | 2023-03 | rapid | 1825 | 99.6 | alta | |
| (mesma thread acima) | 2023-03 | rapid | 1865 | 99.7 | alta | |
| (mesma thread acima) | 2023-03 | rapid | 1932 | 99.8 | alta | |
| (mesma thread acima) | 2023-03 | rapid | 2039 | 99.9 | alta | |
| https://www.chess.com/forum/view/site-feedback/how-does-chess-com-count-percentile | 2024-09-05 | (não claro) | rank 246.881 de 29.376.390 | 96.3 (exibido) vs 99.15 (calculado) | média | evidência de que percentil exibido ≠ ranking simples; janela de 90 dias de atividade |
| https://www.chess.com/forum/view/livechess/why-is-a-live-chess-rating-of-1200-high-in-percentile | 2020-09-15 | live/blitz | 1200 | 70–80 | alta | **FONTE-CHAVE meio-boom**: OP em set/2020 |
| (mesma thread acima) | 2020-09-15 | blitz | 1125 | 69.7 | alta | notmtwain lê do site |
| (mesma thread acima) | 2020-09-15 | blitz | ~800 | ~50 | média | mediana blitz estimada do gráfico do leaderboard |
| (mesma thread acima) | 2020-09-15 | daily | 1100–1200 | ~50 | média | mediana daily |
| (mesma thread acima) | 2023-06-26 | rapid | 850 | 70 | alta | usuário arzanish1 |
| (mesma thread acima) | 2023-06-26 | daily | 930 | 70 | alta | idem |
| (mesma thread acima) | 2023-11-18 | rapid | 1220 | "1,6%" (anômalo — provavelmente bug ou top_x) | baixa | descartar ou investigar |
| https://www.chess.com/forum/view/general/rapid-rating-percentiles | 2023-07-08 | rapid | curva completa: 514→37; 600→46.4; 632→49.9; 699→56.7; 790→65.5; 866→72; 918→75.8; 967→79; 1099→86.3; 1192→90.1; 1447→96.4 (31 pontos no total) | vários | alta | **FONTE-CHAVE**: curva empírica inteira coletada de stats pages em jul/2023; mediana ≈630 |
| https://www.chess.com/forum/view/general/rating-distribution | 2018-01-03 | live (modalidade não explícita — confirmar na thread) | 1400 | 87 | alta | **FONTE-CHAVE pré-boom**: percentil exibido em jan/2018 |
| (mesma thread acima) | 2021-10-02 | rapid | média 1126 (2018) → 812 (2021-10) | — | alta | OP volta 3,5 anos depois: média rapid caiu 1126→812 |
| https://www.chess.com/forum/view/for-beginners/for-beginners-rating-distribution-guide | 2021-01-15 | rapid | 1100 | 71 (top_x=29) | alta | guia de jan/2021; média rapid 894 na época |
| (mesma thread acima) | 2021-01-15 | rapid | 1300 | ~85 | média | "+85% percentile" |
| (mesma thread acima) | 2024-08-26 | blitz | 1536 | 95.3 | alta | comentário posterior |
| https://www.chess.com/forum/view/community/how-good-is-1600-blitz-rating-on-chess-com | 2019-07-13 | blitz | 1600 | top_x=10 (~90) | alta | **ponto pré-boom 2019** para blitz |
| https://www.chess.com/forum/view/general/true-reflexion-of-elo-on-playing-ability-and-what-percentiles-say | 2023-10-25 | rapid | 1260 | 92.8 | alta | OP cita percentil exibido; discute inflação de percentil pós-COVID |
| https://www.chess.com/forum/view/community/chess-com-rating-distribution | 2024-09 | rapid | 400 | ~50 (contestado) | baixa | usuário kaeche cita 400 como mediana; thread aponta inconsistências nos gráficos oficiais |

## 3. Artigos / blogs / StackExchange com tabelas datadas

| url | data | modalidade | rating | percentil | confiança | nota |
|---|---|---|---|---|---|---|
| https://chessgrandmonkey.com/chess-rating-percentile-calculator-graph | 2026-03 (last updated) | rapid chess.com | 1000 | ~50 (afirmação do site; conflita com mediana ~620 de 2024 — checar) | baixa | calculadora de percentil; também: 1200→70th, 2000→"1%" (provável top_x=1) — números internos inconsistentes, extração via modelo pode ter confundido "top X%" |
| https://chessgrandmonkey.com/chess-rating-percentile-calculator-graph | 2026-03 | rapid lichess | 1400 | ~50 | média | mediana lichess rapid ~1400 |
| https://www.quora.com/Why-does-everyone-think-that-an-average-chess-player-is-rated-1200-I-mean-on-chess-com-1112-is-in-the-79-5-percentile-and-people-here-are-writing-misleading-answers-saying-50th-percentile | sem data (estimativa ~2021-2023 — datar pela página) | provável rapid | 1112 | 79.5 | média | percentil exibido ao autor da pergunta no Quora; datar via Wayback/respostas |
| https://betterchess.co/chess-rating/1200 | ~2025 | rapid chess.com | 1200 | top_x≈30 (ver página) | baixa | página SEO moderna; útil só como snapshot 2025 |
| https://chess.wine/rating-percentile | ~2025-2026 | várias | calculadora | — | baixa | calculadora moderna; checar fonte dos dados |
| https://chessgoals.com/descriptive-data/ | 2020-04-27 | — | — | — | baixa | NÃO tem percentis de rating; é sobre ganho anual de rating (n=384). Descartar para o objetivo principal |
| https://chessgoals.com/rating-comparison/ | 2026-07 (atualizado) | várias | — | — | alta | SEM percentis diretos, mas tabela de conversão entre plataformas com ~20k jogadores; observa deriva ano-a-ano (lichess blitz ~-30 pts, bullet +40, rapid -25 vs ano anterior) — útil como fonte de mudança estrutural |
| https://www.chessref.com/tools/rating-percentile | 2026-03-11 | lichess blitz | 1175 / 1475 / 1750 / 2000 / 2125 / 2375 | 25 / 50 / 75 / 90 / 95 / 99 | alta | baseado na distribuição semanal oficial do lichess; pool 691.328 blitz ativos |
| https://lichess.org/forum/general-chess-discussion/historical-rating-percentiles | 2017-02 (dados) | lichess classical/standard | decis: 1199/1319/1411/1500/1518/1604/1689/1789/1927 | 10/20/.../90 | alta | **FONTE-CHAVE lichess**: decis calculados do dump database.lichess.org; média 1554.6; ≥2000 = 6.59% |
| (mesma thread acima) | 2024-01 (dados) | lichess standard | decis: 948/1103/1229/1343/1458/1535/1659/1797/1979 | 10/20/.../90 | alta | média 1455.6; ≥2000 = 9.15%; mostra deslocamento da cauda baixa 2017→2024 |
| https://www.chess.com/forum/view/general/comparing-percentile-ratings-between-sites | 2025-11-01 | blitz chess.com | 1150 | 87 | alta | OP reporta percentil exibido; jarrs123 (2025-11-02): média rapid caiu para 614; thread menciona "ajuste recente" na distribuição do chess.com |

## 4. Datasets públicos (Kaggle, GitHub)

| url | data | modalidade | rating | percentil | confiança | nota |
|---|---|---|---|---|---|---|
| https://database.lichess.org/ | 2013-01 → presente (mensal) | todas (lichess) | dados brutos | — | alta | **MELHOR fonte primária Lichess**: dumps mensais com rating de ambos jogadores em cada partida; permite reconstruir a distribuição de ratings de jogadores ativos mês a mês, 2013–2026 (foi o que o usuário do fórum lichess fez para 2017 vs 2024) |
| https://www.kaggle.com/datasets/aakashshinde1507/chess-players-by-rating | 2023-02 | chess.com (leaderboard) | 12.500 jogadores | — | baixa | provável scrape de leaderboard (topo da distribuição apenas); pouco útil para percentil geral |
| https://www.kaggle.com/datasets/datasnaek/chess | ~2017 | lichess | 20k partidas | — | baixa | pequeno; ratings de partidas lichess ~2017 — pode dar distribuição aproximada de jogadores ativos da época |
| https://github.com/JaseZiv/chessR | ativo | chess.com + lichess | — | — | média | pacote R para extrair dados de jogos/jogadores; útil como ferramenta, não como snapshot histórico |
| https://news.ycombinator.com/item?id=42237878 | 2024-11 | lichess | — | — | média | discussão HN sobre dados públicos de população do lichess (Glicko-2 modificado) — links úteis |

## 5. Mudanças estruturais (contexto para interpretar quebras)

### Rating inicial padrão (Chess.com)
- **Até ~2017-2019**: todos começavam em **1200** (Glicko default). Fonte: https://www.chess.com/forum/view/community/what-rating-do-new-starters-begin-with-has-something-changed (mod justbefair, 2022-10-28) e https://www.chess.com/forum/view/general/chess-com-changed-the-starting-ratings (Martin_Stahl: "the site has changed the starting ratings a few different times").
- **~2020 (abril)**: auto-avaliação; "beginner" começava em **1000** (fonte: busca em threads do fórum; confirmar data exata no Wayback do support.chess.com).
- **~2020-2021 → hoje**: níveis por auto-avaliação: new=**400**, beginner=**800**, intermediate=**1200**, advanced=**1600**, expert=**2000**; opção 2000 removida ~início de 2021 ("several months ago" relativo a jul/2021). Fonte: https://www.chess.com/forum/view/community/how-does-chess-com-decide-initial-ratings
- **2025-12**: usuários observam contas começando em **300** e **1500** — nova mudança de tiers. Fonte: https://www.chess.com/forum/view/general/chess-com-changed-the-starting-ratings (post 2025-12-25).
- CONSEQUÊNCIA: a queda do rating inicial (1200→800/400) desloca a massa da distribuição para baixo → um mesmo rating "sobe" de percentil mecanicamente, sem ganho de habilidade relativa.

### Política de percentil / contas inativas
- Percentil exibido usa **apenas jogadores ativos nos últimos 90 dias** (fontes: forum "how-does-chess-com-count-percentile", 2024-09/2025-01; e chess-com-rating-distribution, 2023). Percentil ≠ ranking/total de contas (caso documentado: rank 246.881/29.4M = 99.15% calculado vs 96.3% exibido, set/2024).
- Percentil não é recalculado em tempo real; jogadores com mesmo rating podem exibir percentis diferentes (mod em about-the-percentile-in-stats, 2024-02).
- **Critérios oficiais do pool (2026-02-09)**: conta ≥7 dias, ≥20 partidas na modalidade, ≥1 partida nos últimos 90 dias, conta ativa em situação regular. Fonte: https://support.chess.com/en/articles/8572866-what-does-percentile-mean — IMPORTANTE: capturas antigas desse artigo (e do antecessor) no Wayback podem revelar se os critérios mudaram ao longo do tempo.
- **2021-01-22**: ratings de Daily >1500 e Daily960 >1300 aumentados em +50 a +400 pts (para alinhar com blitz) — e depois **revertidos** (nota no próprio anúncio). Fonte: https://www.chess.com/news/view/daily-chess-ratings-adjusted — quebra (e des-quebra) na série de daily.
- **Ecossistema/atividade** (saychess.substack.com, 2022-05-17): pico mar/2021 com 705M partidas/mês e ~19M usuários ativos; +128% out/2020→mar/2021; -21% partidas mar/2021→abr/2022. Fonte: https://saychess.substack.com/p/is-the-chess-twitch-boom-over-looking
- LIMITAÇÃO DE COLETA: reddit.com bloqueia o crawler (WebSearch/WebFetch) — posts do Reddit precisam ser buscados via Wayback/Pushshift no pipeline Python.

### Boom pandemia / Queen's Gambit
- **2020-03**: DAU de 280k → >1M em março/2020; ~1M novos membros/mês desde o lockdown. Fonte: Bloomberg https://www.bloomberg.com/graphics/2020-chess-boom/ (2020-12).
- **2020-10-23**: estreia de The Queen's Gambit (62M households/28 dias); >100k novos jogadores/dia no mês seguinte; 2.8M novos membros em nov/2020; ~13M novos membros mar–dez/2020. Fontes: Bloomberg, Washington Post (2020-11-27), Sportico (2020-12).
- **2022-12**: Chess.com atinge **100M membros** (14 meses após 50M ⇒ 50M ~out/2021). Segundo boom dez/2022–fev/2023 (streamers/"chess boom 2.0").
- CONSEQUÊNCIA: enxurrada de iniciantes baixa a mediana (rapid: mediana ~660 em 2023, ~620 em 2024, média 614 em nov/2025) e infla o percentil de ratings médios (1000 rapid: 39th em ~2016 → 49th em ~2019 → 81st em 2024).

### Sistema de rating / recalibrações
- **2020-09-10/11 — MUDANÇA CRÍTICA**: 10|0 reclassificado de blitz para **rapid**; ratings rapid recalculados (se blitz > rapid, rapid = blitz); **bullet +150 pts** para alinhar com blitz. Fonte oficial: https://www.chess.com/news/view/10-minute-chess-now-rapid-rated-bullet-ratings-increased e tweet https://x.com/chesscom/status/1304036644232847360 — QUEBRA estrutural nas séries de rapid, blitz e bullet em set/2020. Logo após a mudança, média rapid ~1025, caindo diariamente até ~864 (relato de forum, início 2021).
- **Médias rapid documentadas em fóruns**: ~1025 (set/2020, pós-reclassificação) → 887.78 (jan/2021) → 894 (jan/2021, outra thread) → 846 (fev/2021) → 664 (mai/2023) → 614 (nov/2025). Série útil de deflação da média.
- **llama36 (blog chess.com, 2022-12-11)**: https://www.chess.com/blog/llama36/average-chess-com-rating — média blitz caiu ~120 pts em ~20 meses (abr/2021→dez/2022); blitz ativos 12,7M→10M; média blitz <800 em dez/2022; autor simula efeito de novos jogadores no ecossistema (deflação).
- Chess.com usa **Glicko-1** (com RD); Lichess usa **Glicko-2** com início em **1500** — escalas não comparáveis diretamente.
- **2025-10**: Chess.com re-classificou TODO o sistema de Puzzles (novo sistema, ~17 bilhões de tentativas reprocessadas; ratings de puzzle caíram). Fonte: https://www.chess.com/news/view/announcing-new-puzzles-rating-system — não afeta live chess, mas contamina séries de puzzle percentile.
- **Daily/Daily960 ajustados**: https://www.chess.com/news/view/daily-chess-ratings-adjusted (pegar data no fetch/Wayback) — quebra estrutural nas séries de daily.
- **2025 (~out-nov)**: thread de nov/2025 menciona que "Chess.com recently adjusted its rating distribution" — investigar anúncio exato.
- Deriva contínua entre plataformas (ChessGoals, jul/2026): lichess blitz ~-30 pts, bullet +40, rapid -25 vs ano anterior; "500 chess.com blitz ≈ 925 USCF agora vs 500 antes".

## 6. URLs para Wayback Machine (baixar via pipeline Python)

| url original | anos prováveis de captura | o que esperar |
|---|---|---|
| https://lichess.org/stat/rating/distribution/blitz | 2016–2026 (muitas capturas) | **página oficial de distribuição semanal do Lichess** — histograma completo; percentis exatos por data de captura |
| https://lichess.org/stat/rating/distribution/rapid | 2018–2026 | idem (rapid existe desde ~2017 no lichess) |
| https://lichess.org/stat/rating/distribution/bullet | 2016–2026 | idem |
| https://lichess.org/stat/rating/distribution/classical | 2016–2026 | idem |
| https://chessgoals.com/rating-comparison/ | 2019–2026 | tabelas de conversão entre plataformas em versões anuais; medianas citadas em algumas versões |
| https://chessgoals.com/chess-ratings-percentile/ (verificar slug) | 2020–2024 | possível página de percentis do chessgoals |
| https://www.chess.com/forum/view/livechess/rating-distribution-graph | capturas 2017–2019 | thread de 2017 com relatos de percentil da época |
| https://support.chess.com/article/... ("What is the default rating for new players?") | 2019–2025 | documenta mudanças do rating inicial (1200→1000→800/400) com datas de captura |
| https://www.chess.com/article/view/chess-ratings---how-they-work | 2011–2020 | artigo de erik com histograma de distribuição antigo (pré-boom) |
| https://database.lichess.org/ | n/a (dados brutos) | dumps mensais de TODAS as partidas lichess desde 2013 — permite reconstruir distribuição exata por mês (fonte primária Lichess, sem Wayback) |
| https://www.chess.com/leaderboard/live | 2014–2021 | página de leaderboard que exibia GRÁFICO de distribuição de ratings live (citado em thread de 2020: "mediana ~800 no gráfico do leaderboard") |
| https://www.chess.com/leaderboard/live/rapid e /blitz e /bullet | 2017–2023 | idem por modalidade |
| https://www.chess.com/livechess/players | 2010–2016 | página antiga "view all players" com curva de distribuição completa e percentil por rating (citada em thread de 2013) |
| https://www.chess.com/stats/live/rapid/hikaru (ou outro usuário famoso) | 2018–2026 | stats page individual mostra percentil do jogador — capturas datadas dão pares (rating, percentil) do topo da distribuição |
| https://www.quora.com/Why-does-everyone-think-that-an-average-chess-player-is-rated-1200-I-mean-on-chess-com-1112-is-in-the-79-5-percentile-... | 2021–2023 | datar a alegação 1112→79.5 |
| reddit.com/r/chess e r/chessbeginners (busca "percentile") | 2016–2024 | reddit bloqueia crawler da Anthropic; usar Wayback/PullPush/Arctic Shift no pipeline para queries como "rapid percentile", "top 25%", "1000 rapid percentile" |

## 7. Síntese preliminar — resposta provisória à pergunta do projeto

Linha do tempo do percentil de um **1000 rapid** no Chess.com (pontos coletados acima):
- ~2016: **39º** percentil (thread TIL, 2024)
- 2017-11: 1000 live ≈ **33º** (thread rating-distribution-graph — live/blitz)
- ~2019: **49º** (thread TIL)
- 2020-09: (quebra: 10|0 vira rapid; rapid recalculado a partir do blitz)
- 2021-01: média rapid 894 ⇒ 1000 ≈ 55–60º (interpolação)
- 2022-12: tabela completa ⇒ 1000 ≈ **~82º** (interpolando 967→79 e 1099→86.3 da curva de 2023-07; tabela de dez/2022 dá 1200→89.9)
- 2023-07: 967→79º, 1099→86.3º ⇒ 1000 ≈ **80º**
- 2024-08: **81º** (thread TIL)
⇒ SIM: um 1000 rapid hoje está muito melhor posicionado relativamente do que em 2018 — mas grande parte do efeito é composicional (rating inicial 1200→800/400, influxo de iniciantes pós-2020, reclassificação do 10|0 em set/2020), não ganho de habilidade. A thread TIL inclusive mediu accuracy de partidas 1000-rated 2019 vs 2024: diferença de só ~2%.

### Top 5 fontes mais valiosas
1. https://www.chess.com/forum/view/community/ratings-distribution-across-the-chess-com-community — tabela rapid completa, 2022-12-28, ~15,3M jogadores.
2. https://www.chess.com/forum/view/general/rapid-rating-percentiles — curva empírica com 31 pontos (rapid, 2023-07-08).
3. https://www.chess.com/forum/view/general/til-5-years-ago-a-1000-rapid-rating-was-49th-percentile-today-its-the-81st — série 2016/2019/2024 para 1000 rapid + teste de accuracy.
4. https://database.lichess.org/ + https://lichess.org/stat/rating/distribution/{modalidade} (com Wayback) — reconstrução mês a mês da distribuição Lichess 2013–2026.
5. https://www.chess.com/news/view/10-minute-chess-now-rapid-rated-bullet-ratings-increased (2020-09-10) — a maior quebra estrutural das séries (10|0→rapid, bullet +150).

## 6. URLs para Wayback Machine (baixar via pipeline Python)

| url original | anos prováveis de captura | o que esperar |
|---|---|---|
