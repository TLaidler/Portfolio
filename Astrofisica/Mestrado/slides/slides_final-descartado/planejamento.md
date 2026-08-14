# Planejamento — Slides finais da defesa (45 min)

> **Arquivo:** `apresentacao_defesa.pptx` (40 slides: 35 principais + divisor de apoio + 4 backups)
> **Gerador:** `build_deck.py` (reexecutável; assets preparados por `prepare_assets.py`)
> **Regra de ouro:** imagem narra, orador fala, texto é andaime. Uma única tabela no fluxo principal.

## Decisões de design

| Decisão | Justificativa |
|---|---|
| Paleta navy 29,45,84 + azul 72,150,222 + **vermelho 196,30,58 só para resultados** | Herdada do `main.tex`; sóbria e "ON-like"; o vermelho vira sinal visual de "isto é um resultado" |
| 16:9, Calibri | Padrão do projetor/Office da defesa; sem dependência de fontes exóticas |
| Banca de astrônomos → ML didático | Seção 2 inteira sem equação: sigmoide (probabilidade), árvore "Vou para praia?", floresta que vota, K-fold |
| Slides favoritos do seminário recriados | Curva → **seta vermelha** (asset original do part1) → tabela de features, em par positivo/negativo |
| Estrutura de suspense em Quaoar | Curva inteira passa → anéis finos "reprovam" → reviravolta do τ=0,03 e a separação de 86× |
| Baseline trivial (análise pós-tese) **só em backup** | Não está na dissertação; disponível se a banca perguntar "precisava de ML?" |
| Números idênticos aos da tese | F1 por experimento = Tabela de comparação do Cap. 5; 1693/802/891; 86×; τ=0,03 |

## Estrutura e mapa de tempo (~42 min + 3 de folga)

| Seção | Slides | Min | Conteúdo |
|---|---|---|---|
| A. Abertura | 1–2 | 2 | Capa (telescópio + navy), roteiro em 5 âncoras |
| B. Ocultações | 3–7 | 7 | Chariklo; sombra na Terra; frames→curva; cordas/limbo |
| C. Problema e dados | 8–13 | 8 | Gargalo; pipeline; BD; 1693 curvas; **curva→números (setas)** ×2 |
| D. ML didático | 14–19 | 7 | Supervisão; árvores/floresta; comitês; K-fold; 28→11 features |
| E. Resultados | 20–26 | 9 | **Tabela única** (6 exps); ROC/confusão; teste real; ablação K-Means; erros; limiar τ |
| F. Quaoar | 27–31 | 6 | Curva completa; recortes; **86× / τ=0,03 / 0 falsos alarmes**; janelas diluem |
| G. Fechamento | 32–35 | 3 | Dificuldades; conclusões (3 números); futuros; obrigado |
| Backup | 36–40 | — | Baseline trivial; Umbriel teste cego; recortes detalhe; física SORA |

**Picos de tempo:** slide 21 (tabela, ~2 min) e slide 30 (clímax Quaoar, ~2 min).
**Válvulas de escape se atrasar:** encurtar slide 7 (cordas) e pular slide 25 (onde erra).

## Fonte de cada figura

| Slide | Figura | Origem |
|---|---|---|
| 1 | telescópio (painel) | part1 `image12.png` |
| 4 | Chariklo + curva esquemática | tese `curva.png` (L. Maquet) |
| 5 | mapas da sombra (Umbriel 2020) | tese `OccUmbriel_mapa/mapa2.png` |
| 6 | frames CCD + curva reduzida | tese `OccUmbriel_outputExemplo/2.png` |
| 7 | cordas + ajuste de limbo | tese `Cordas atualizadas.png`, `Bardecker12.png` |
| 8 | ilustração ocultação | figs `ocultacao_ilustracao.png` |
| 9 | diagrama da pipeline | figs `pipeline.png` |
| 10 | fluxo de aquisição + BD SQLite | tese `fluxo1.png`, part1 `image27.jpg` |
| 12–13 | curva positiva/negativa + **seta** + tabela NATIVA (valores reais do dataset) | part1 `image25/51/21.png` + `dataset_final.csv` |
| 15 | sigmoide | tese `sigmoide.png` |
| 16 | árvore "Vou para praia?" + floresta | part1 `image38.png`, tese `RF_img.png` |
| 17 | acurácia do comitê | tese `manual_2.png` |
| 18 | K-fold | tese `kfold.png` |
| 19 | Savitzky-Golay + importância RF | part1 `image28.png`, figs `feat_importance_rf.png` |
| 22–23 | ROC + matrizes (Exp1, Exp3-real) | figs `exp1_*/exp3real_*.png` |
| 24 | histograma K-Means por classe | tese `resultado3/histograma_kmeans_por_classe.png` |
| 25 | falsos negativos | tese `resultado3/RF_curva_FN_1/2.png` |
| 26 | métricas × limiar | figs `metrics_vs_threshold.png` |
| 28–31 | Quaoar (curva; recortes só-τ=0,5 p/ preservar suspense; τ ajustado; janelas expandidas) | tese `quaoar_test`, `Quaoar_XgBoost_full_pict`, `quaoar_recorte_tau_ajustado`, `quaoar_recortes_janelas_expandidas` |
| 32 | fluxo de construção do dataset | tese `fluxo2.png` |
| 34 | pipeline (esmaecida) | figs `pipeline.png` |
| 38–40 | Umbriel, recortes XGBoost, modelo SORA | part1 `image51.png`, tese `Quaoar_XgBoost_*`, `ModelosSORA.png` |

## Log dos loops de crítica

### Loop 1 — painel Feynman / Sagan / professor (14 achados, todos tratados)
- **[ALTA]** "30 mil séries" (sl. 10) não rastreável → substituído por descrição sem número.
- **[ALTA]** "0 falsos alarmes" sem escopo no clímax → "falsos alarmes **nesta curva**" +
  resposta pronta no roteiro (no teste, τ=0,03 custa 5 alarmes/179 negativas).
- "~100% sensibilidade" (2×) → **99,4%** com escopo (teste, +5 alarmes).
- Legenda da tabela: "0,978–0,994" → "Melhor F1 por experimento: 0,982–0,994" (o que a
  tela mostra); nota no roteiro para justificar o 0,978 da tese se perguntado.
- Nomenclatura dos anéis unificada: "as duas travessias do anel fino Q2R".
- Sobreposição imagem/legenda nos slides 8 e 30 (bignum+imagem) → imagem termina em 6,55".
- Slides 12–13 (setas): tabela de features ampliada (layout diagonal, ~7,1" de largura).
- "milhares de curvas/ano" → "milhares de curvas acumuladas em arquivos e novas campanhas".
- Slide "0,994 → 0,991" cortado (redundante com a tabela); mensagem fundida na fala do sl. 21.
- Ordem dos autores do simulador unificada: **Gomes-Ferrante & Braga-Ribas** (ordem da tese).
- "Blind test" removido do backup de Umbriel; legenda do Exp3 moderada ("consistente com
  aprender a física"); ponte de abertura "três coisas / cinco paradas" alinhada.
- ⚠ Achado sobre ground truth (não é do deck): `resultado6.1/training_results.csv` é cópia
  byte a byte do `resultado5` — experimento 65/35 não é usado no deck, mas conferir na tese.

### Loop 2 — painel Feynman / Sagan / professor (8 achados; veredito GO)
- Fixes do Loop 1 todos confirmados no PPTX; tabela do sl. 21 reconciliada célula a célula
  com os CSVs; nenhuma referência de slide obsoleta nos markdowns.
- **[ALTA]** Tabela dos sl. 12–13 não continha as curvas apontadas → substituída por tabela
  NATIVA com valores reais do `dataset_final.csv` (Umbriel A. Scheck vs N. Carlson), linha
  destacada por slide; captions e roteiro citando os valores verdadeiros (0,43/7,0 vs 0,31/4,4).
- **[ALTA]** Sl. 29 entregava o spoiler (figura já mostrava τ=0,03) → trocado para
  `Quaoar_XgBoost_full_pict.png` (só τ=0,5); o reveal visual fica no sl. 30.
- Sl. 11: "conjunto de treino" → "conjunto de dados rotulado" (inclui teste; roteiro cita 80/20).
- Roteiro: "anéis finos do Q2R" → "as duas travessias do anel fino Q2R" (2×); "~100%" → "99,4%".
- Promessa "cinco paradas" removida da fala de abertura (divisores são 4).
- Backup de Umbriel: caption agora explica que a figura É a curva divergente do teste cego.
- Veredito do painel: **GO para o ensaio.**
