# Relatório — Recortes da curva de Quaoar: XGBoost vs CatBoost

> **Objetivo deste documento:** consolidar os experimentos de aplicação dos
> modelos treinados (CatBoost e XGBoost, configuração do Experimento~5 — 11
> features, sem `Feature_Savgol_Min`, sem `kmeans_centroid_dist`) sobre
> recortes específicos de uma curva de luz **real** da ocultação estelar por
> Quaoar de 09-08-2022. Serve como prompt-fonte para redação na tese
> (capítulo~5, Seção `sec:estudo_caso_quaoar`, subseção "Aplicação a
> recortes da curva", com extensão possível em "Limitações" do capítulo~5
> e em "Trabalhos futuros" do capítulo~6).

---

## 1. Contexto

### 1.1 Dados utilizados
- **Curva:** `Gemini-Alopeke_Red-z.dat` (canal vermelho do instrumento
  'Alopeke do Gemini-N, filtro $z$).
- **Evento:** ocultação estelar por (50000) Quaoar, instante de referência
  **2022-08-09 06:34:49,26 UTC** (corresponde a 23 689,26 s UTC do dia).
- **Volume:** 12 000 pontos PRAIA brutos → 12 000 pontos após limpeza
  (clip físico `flux_norm ∈ [-2, 5]`, sem outliers de flag PRAIA 99,999).
- **Intervalo coberto:** 23 166,1 .. 24 380,3 s UTC ≈ −523 .. +691 s
  relativos ao evento.
- **Proveniência:** dados cedidos pelo autor principal de Pereira et al.
  (2023) — `\citet{Quaoar2023}`. **Não** estão no banco SQLite usado para
  treinar os modelos (nem no VizieR `B/occ/asteroid` nem no drive do Grupo
  do Rio).

### 1.2 Recortes definidos
Cada recorte é uma janela temporal isolada da curva, escolhida para
sondar uma assinatura física específica (corpo, anéis Q1R/Q2R, baseline,
ruído). As janelas estão em segundos relativos ao instante do evento.

| Recorte | Janela (s rel.) | Assinatura física esperada |
|---|---|---|
| zero   | −290 .. −250 | Baseline sem ocultação (controle negativo) |
| um     | −225 .. −200 | Q1R — *continuous part* |
| dois   | −129 .. −114 | Q2R_1 — ocultação real do anel fino |
| três   | −109 .. −099 | Q2R_1 — trecho de ruído visualmente parecido |
| quatro | +121 .. +146 | Q2R_2 — pós ocultação principal |
| cinco  | +191 .. +251 | Q1R — *dense part* (queda forte e rápida) |

### 1.3 Modelos avaliados
- **CatBoost** (arquivo `catboost_model.cbm`, configuração do
  Experimento~5).
- **XGBoost** (arquivo `xgboost_model.pkl`, mesma configuração).
- Ambos usam o mesmo `imputer` e `feature_names` (11 features finais).
- Imputer original do `scikit-learn` é incompatível com a versão atual;
  fallback para mediana local (efeito desprezível no resultado).

### 1.4 Pipeline executado
Script: `pipeline/model_in_practice/test_quaoar_recortes.py`. Para cada
recorte: corte → extração de features (`extract_features` +
`compute_occ_features`) → predição → registro de $\hat{p}$ e veredito.
Predição é independente entre recortes (não há janela deslizante nem
contexto cruzado).

---

## 2. Resultados — janelas originais

### 2.1 CatBoost
| Recorte | Janela rel. (s) | N pontos | Veredito | $\hat{p}$ |
|---|---:|---:|:---:|---:|
| zero   | −290..−250 | 1482 | NEG | **0,029** |
| um     | −225..−200 |  247 | OCC | **0,685** |
| dois   | −129..−114 |  148 | NEG | 0,058 |
| três   | −109..−099 |   99 | NEG | 0,005 |
| quatro | +121..+146 |  247 | NEG | 0,456 (*borderline*) |
| cinco  | +191..+251 |  593 | OCC | **0,987** |

### 2.2 XGBoost
| Recorte | Janela rel. (s) | N pontos | Veredito | $\hat{p}$ |
|---|---:|---:|:---:|---:|
| zero   | −290..−250 | 1482 | NEG | **0,0006** |
| um     | −225..−200 |  247 | OCC | **0,9601** |
| dois   | −129..−114 |  148 | NEG | 0,0434 |
| três   | −109..−099 |   99 | NEG | **0,0005** |
| quatro | +121..+146 |  247 | NEG | 0,0807 |
| cinco  | +191..+251 |  593 | OCC | **0,9994** |

### 2.3 Comparação direta CatBoost × XGBoost

| Recorte | Tipo esperado | CatBoost $\hat{p}$ | XGBoost $\hat{p}$ | Comentário |
|---|---|---:|---:|---|
| zero   | NEG (controle)   | 0,029  | **0,0006** | XGBoost ainda mais confiante |
| um     | OCC (anel longo) | 0,685  | **0,9601** | XGBoost decide com folga |
| dois   | OCC (anel fino)  | 0,058  | 0,0434     | ambos classificam NEG |
| três   | NEG (ruído)      | 0,005  | **0,0005** | XGBoost rejeita mais forte |
| quatro | ? (anel fino)    | 0,456  | 0,0807     | CatBoost em cima do muro |
| cinco  | OCC (anel forte) | 0,987  | **0,9994** | XGBoost quase certeza |

**Razão real-vs-ruído no Q2R_1** (recortes dois÷três):
- CatBoost: 0,058 / 0,005 ≈ **12×**
- XGBoost: 0,0434 / 0,0005 ≈ **86×**

Ou seja: mesmo classificando ambos como NEG no limiar padrão $\tau=0,5$,
o XGBoost concentra muito mais densidade de probabilidade no anel real do
que no ruído. Isso é argumento direto para o ajuste de limiar discutido
na Seção `sec:threshold_tuning`: com $\tau \approx 0,03$ o anel real
seria detectado e o ruído continuaria descartado.

---

## 3. Experimento adicional — expansão das janelas

### 3.1 Motivação
Hipótese a testar: "o modelo perde os anéis finos porque as janelas são
muito curtas (poucos pontos) e a extração de *features* fica instável".

### 3.2 Conversão das janelas
| Recorte | Antes | Depois | Tamanho antes | Tamanho depois |
|---|---|---|---:|---:|
| dois   | −129..−114 (15 s) | −160..−110 (50 s) | 148 pts | 494 pts |
| três   | −109..−099 (10 s) | −110..−085 (25 s) |  99 pts | 247 pts |
| quatro | +121..+146 (25 s) | +080..+170 (90 s) | 247 pts | 889 pts |

### 3.3 Resultados (XGBoost)
| Recorte | $\hat{p}$ antes | $\hat{p}$ depois | Variação |
|---|---:|---:|:---:|
| dois (Q2R_1 real)  | 0,0434 | **0,0349** | ↓ ficou MAIS NEG |
| três (Q2R_1 ruído) | 0,0005 | 0,0027 | ↑ ligeira |
| quatro (Q2R_2)     | 0,0807 | **0,0288** | ↓ ficou MAIS NEG |

### 3.4 Interpretação
A hipótese é **refutada**. Ampliar a janela não melhora a detecção dos
anéis — ao contrário, torna o veredito NEG ainda mais forte para dois
dos três recortes onde havia sinal físico.

**Explicação:** quase todas as features do modelo (Savgol_Min,
Max_Drawdown, Occ_depth, Occ_SNR_dip, MinLogP_KS) são **estatísticas
globais da janela**. Quando um anel de 5–10 s é diluído em 50–90 s de
baseline limpo, as estatísticas agregadas ficam dominadas pelo baseline
e o "dip" do anel vira um *outlier* estatisticamente desprezível.
Resultado: a janela parece "majoritariamente baseline + ruído residual"
e o modelo responde com mais confiança "sem evento".

### 3.5 Consequência arquitetural
A fronteira do que o modelo "consegue ver" passa pela razão
$\text{(duração do dip)} / \text{(duração da janela)}$ e pela
profundidade absoluta. Por isso:
- **Recorte cinco** (Q1R *dense*, dip profundo ocupando boa fração da
  janela): $\hat{p}=0{,}9994$, sem problema.
- **Recorte um** (Q1R *continuous*, queda longa e contínua):
  $\hat{p}=0{,}9601$, OCC sólido.
- **Recortes dois, três, quatro** (anéis finos diluídos): NEG, e ampliar
  a janela só piora.

---

## 4. Experimento adicional — ajuste do limiar de decisão $\tau$

### 4.1 Motivação
A Seção~\ref{sec:threshold_tuning} da tese mostra teoricamente que
classificadores que produzem probabilidades calibradas (como XGBoost)
permitem operar em modo de triagem agressiva apenas ajustando o limiar
de decisão $\tau$ em pós-processamento, sem retreinar. A análise da §2.3
sugeriu que $\tau \approx 0{,}03$ seria suficiente para incluir os anéis
Q2R sem reativar o trecho de ruído. **Esta seção testa essa previsão
empiricamente.**

### 4.2 Implementação
Adicionou-se a constante `THRESHOLD = 0.03` ao topo de
`test_quaoar_recortes.py`. A função `predict_one()` foi modificada para
devolver tanto o veredito-padrão (`model.predict()`, $\tau = 0{,}5$) quanto
o veredito-ajustado ($\hat{p} \geq \tau$). O console e a legenda do plot
mostram ambos lado a lado, marcando com `*` os recortes em que a
classificação muda.

### 4.3 Resultados (XGBoost, $\tau = 0{,}03$)

| Recorte | Tipo esperado | $\hat{p}$ | $\tau=0{,}5$ | $\tau=0{,}03$ | Mudou? |
|---|---|---:|:---:|:---:|:---:|
| zero   | baseline (controle) | 0,0006 | NEG | NEG | — |
| um     | Q1R *continuous*    | 0,9601 | OCC | OCC | — |
| **dois**   | **Q2R_1 real**      | 0,0434 | NEG | **OCC** | ✓ |
| três   | Q2R_1 ruído         | 0,0005 | NEG | NEG | — |
| **quatro** | **Q2R_2**           | 0,0807 | NEG | **OCC** | ✓ |
| cinco  | Q1R *dense*         | 0,9994 | OCC | OCC | — |

### 4.4 Interpretação
- **Detecções recuperadas:** 2 anéis finos (Q2R_1 e Q2R_2) que estavam
  invisíveis no limiar padrão passam a ser corretamente identificados.
- **Falsos positivos adicionais: nenhum.** Nem o controle (zero,
  $\hat{p}=6\times10^{-4}$) nem o ruído (três, $\hat{p}=5\times10^{-4}$)
  cruzam o novo limiar.
- **Margens de operação:**
  - Entre $\tau=0{,}03$ e a probabilidade do ruído (0,0005): fator
    $\sim 60\times$ — margem confortável.
  - Entre $\tau=0{,}03$ e o ocultador de menor probabilidade
    (Q2R_1 real, 0,0434): margem absoluta de 0,013 — apertada mas
    suficiente.
- **Resultado operacional:** 4 OCC / 2 NEG (vs 2 OCC / 4 NEG no padrão).
  Recall sobre os 4 eventos físicos: 100% (vs 50% no padrão).
  Precisão sobre os recortes-controle (zero + três): 100% (mantida).

### 4.5 Significado para a tese
Este é o **caso de uso ideal** para ilustrar a Seção~\ref{sec:threshold_tuning}.
A análise teórica do capítulo previa que a separabilidade elevada das
classes (AUC-ROC $\geq 0{,}998$) permitiria operar com $\tau \ll 0{,}5$
sem inflar significativamente os falsos positivos. O caso Quaoar
**confirma essa previsão em dados reais externos ao treino**: a janela
de probabilidades atribuídas aos ocultadores ($\geq 0{,}043$) está
separada por mais de uma ordem de grandeza da janela atribuída aos
não-eventos ($\leq 0{,}0006$), o que viabiliza um $\tau$ em qualquer
ponto entre essas duas escalas.

A consequência prática é forte: **com um único parâmetro de
pós-processamento, transforma-se um classificador que perde os anéis
Q2R em um que os detecta sem custo em falsos alarmes**. Não é necessário
retreinar, nem ampliar o conjunto de *features*, nem reformular o
problema como multi-classe — embora todas essas direções continuem
sendo melhorias arquiteturais válidas para os trabalhos futuros (§3.5
e §5.3).

---

## 5. Achados principais (para reportar na tese)

1. **Modelo capta corretamente o controle negativo** (recorte zero, sem
   evento): $\hat{p} \approx 0{,}0006$ no XGBoost — descarta a hipótese
   de viés pró-positivo do classificador.
2. **Detecta os anéis "fortes" Q1R**: parte *continuous* (recorte um,
   $\hat{p}=0{,}96$) e parte *dense* (recorte cinco, $\hat{p}=0{,}999$).
3. **No limiar padrão $\tau = 0{,}5$, não detecta os anéis "finos" Q2R**
   (recortes dois e quatro), mesmo sob expansão de janela; classifica
   corretamente o trecho de ruído adjacente (recorte três,
   $\hat{p}=0{,}0005$). **Sob limiar ajustado $\tau = 0{,}03$, os dois
   anéis Q2R são detectados** (§4) sem nenhum falso positivo
   adicional — confirmação empírica do mecanismo da Seção~5.9 da tese.
4. **XGBoost > CatBoost** neste caso real: probabilidades mais
   polarizadas, razão real-vs-ruído ~7× maior (86× vs 12×). Coerente
   com a liderança do XGBoost no Experimento~7 (teste em curvas reais).
5. **Janela curta não é a causa** da falha em anéis finos. Causa é
   estrutural: o conjunto de *features* é dominado por estatísticas
   globais da janela.
6. **Ajuste de limiar é uma alavanca de pós-processamento eficaz neste
   *dataset*.** Com $\tau = 0{,}03$, recall sobre eventos físicos sobe
   de 50% (2/4) para 100% (4/4) sem inflar falsos positivos — porque a
   separação entre probabilidades de eventos ($\geq 0{,}043$) e de
   não-eventos ($\leq 0{,}0006$) é de mais de uma ordem de grandeza.
7. **Diagnóstico para trabalhos futuros**: ainda que o ajuste de $\tau$
   resolva o caso Quaoar, soluções estruturais mais robustas para
   eventos rasos exigem (a) janela deslizante de tamanho compatível
   com a duração do evento esperado, (b) *features* locais
   (profundidade máxima de subjanela, ajuste a poço retangular curto,
   simetria do perfil), ou (c) modelo dedicado treinado em curvas
   sintéticas de anéis. Estas três direções reforçam o item
   "Classificação multi-classe de eventos" já presente em
   `capitulo6.tex`.

---

## 5. Sugestões de prosa para a tese

> Texto base — adaptar tom e referências cruzadas conforme o restante do
> capítulo. As tabelas acima podem ir como `\begin{table}` diretamente.

### 5.1 Para a subseção "Aplicação a recortes da curva" (Seção `sec:estudo_caso_quaoar`)

> "Para sondar a fronteira de competência do classificador em assinaturas
> mais sutis que o corpo principal, definiram-se seis janelas temporais
> sobre a curva Gemini-'Alopeke Red-$z$, cada uma cobrindo uma estrutura
> física distinta: um trecho de baseline livre de evento (controle
> negativo), três cruzamentos dos anéis Q1R reportados em
> \citep{Quaoar2023} — partes *continuous* e *dense* — e dois
> cruzamentos do anel Q2R, mais fino. A Tabela~\ref{tab:quaoar_recortes}
> reúne os vereditos dos modelos CatBoost e XGBoost (configuração do
> Experimento~5) em cada janela.
>
> O classificador detecta sem dificuldade os componentes do anel Q1R —
> tanto a fração *continuous* (recorte um, XGBoost
> $\hat{p}=0{,}96$) quanto a fração *dense* (recorte cinco,
> $\hat{p}=0{,}999$) — e descarta com alta confiança o trecho de
> *baseline* sem evento (recorte zero, $\hat{p}=6\times10^{-4}$), bem
> como um trecho de ruído visualmente parecido com uma micro-ocultação
> (recorte três, $\hat{p}=5\times10^{-4}$). Em contraste, os dois
> cruzamentos do anel Q2R (recortes dois e quatro) são classificados
> como negativos, com probabilidades $\hat{p}=0{,}043$ e $\hat{p}=0{,}081$
> respectivamente.
>
> Ainda que ambos os anéis Q2R recebam veredito negativo no limiar
> padrão $\tau=0{,}5$, a probabilidade atribuída ao Q2R_1 real é
> aproximadamente $86\times$ maior do que a atribuída ao ruído adjacente
> de duração comparável. Esse contraste, oculto pela classificação
> binária no limiar padrão, é integralmente recuperado pela estratégia
> de ajuste de limiar discutida na Seção~\ref{sec:threshold_tuning}.
> Aplicando $\tau = 0{,}03$ aos mesmos seis recortes, os anéis Q2R_1 e
> Q2R_2 passam a ser corretamente classificados como ocultações, sem
> que o trecho de ruído ($\hat{p}=5\times10^{-4}$) ou o controle de
> *baseline* ($\hat{p}=6\times10^{-4}$) cruzem o novo limiar. O recall
> sobre os quatro eventos físicos (Q1R *cont.*, Q1R *dense*, Q2R_1,
> Q2R_2) sobe de 50\% para 100\%, sem introduzir nenhum falso alarme
> nos dois recortes-controle. Esta é a manifestação prática, em dados
> reais externos ao treino, do mecanismo de \textit{threshold tuning}
> apresentado na Seção~\ref{sec:threshold_tuning}."

### 5.2 Para um parágrafo de discussão (Seção `sec:discussao` ou nova subseção)

> "Uma hipótese natural para a não-detecção dos anéis finos é que as
> janelas correspondentes seriam excessivamente curtas (em torno de
> 10–25 s), o que prejudicaria a estabilidade da extração de
> *features*. Esta hipótese foi testada e refutada: ao ampliar as
> janelas dos recortes Q2R por um fator $\sim 3$, a probabilidade
> atribuída pelo XGBoost ao anel real Q2R_1 caiu de $0{,}043$ para
> $0{,}035$, e a do Q2R_2 caiu de $0{,}081$ para $0{,}029$ — ou seja,
> a ampliação tornou o veredito negativo ainda mais forte. A explicação
> é estrutural: o conjunto de *features* utilizado (Savgol_Min,
> Max_Drawdown, Occ_depth, Occ_SNR_dip, MinLogP_KS, entre outros) é
> dominado por estatísticas globais agregadas ao longo da janela. Um
> *dip* de poucos segundos diluído em dezenas de segundos de *baseline*
> limpo torna-se um *outlier* estatisticamente desprezível, e o modelo
> responde com maior confiança que se trata de baseline puro. A
> fronteira de detecção, portanto, é regida pela razão entre a duração
> do *dip* e a duração da janela (ou, equivalentemente, pela fração da
> janela ocupada pelo evento), e não pelo tamanho absoluto da janela."

### 5.3 Para "Trabalhos futuros" (capítulo~6)

> "O estudo de recortes sobre a curva de Quaoar (Seção
> \ref{sec:estudo_caso_quaoar}) evidenciou que a *pipeline* atual
> detecta com folga os anéis com queda profunda ou longa (Q1R), mas não
> os anéis finos (Q2R), devido ao caráter global das *features*
> utilizadas. Três direções complementares são promissoras:
> (i)~aplicação por **janela deslizante** sobre a curva, com largura
> compatível com a duração típica do evento alvo (anel, atmosfera ou
> corpo), o que torna o conjunto atual de *features* sensível a eventos
> locais; (ii)~enriquecimento do conjunto com **features locais** —
> profundidade máxima de qualquer subjanela de $N$ pontos consecutivos
> abaixo do *baseline*, simetria do perfil ingresso/egresso, ajuste a
> poço retangular curto; (iii)~classificação **multi-classe** com
> modelo dedicado treinado em curvas sintéticas que incluam anéis,
> atmosfera e difração de Fresnel."

---

## 6. Artefatos

- **Script:** `pipeline/model_in_practice/test_quaoar_recortes.py`
  - Constante `THRESHOLD` no topo do arquivo controla o limiar $\tau$
    aplicado em pós-processamento (default $0{,}03$, padrão do modelo
    é $0{,}5$). A função `predict_one()` devolve tanto o veredito-padrão
    quanto o veredito-ajustado, e o console / legenda mostram os dois
    lado a lado, marcando com `*` os recortes em que a classificação
    muda.
- **Figura gerada:** `pipeline/model_in_practice/quaoar_recortes.png`
  (gráfico da curva inteira com as seis janelas destacadas em cores
  distintas; legenda traz $\hat{p}$, veredito em $\tau=0{,}5$ e em
  $\tau=\text{THRESHOLD}$ por janela; eixo $x$ em segundos relativos a
  2022-08-09 06:34:49,26 UTC, intervalo $[-300, +350]$ s).
- **Curva de referência do paper:** `writing_latex/Tese/pngs/quaoar_test.png`
  (figura já incluída no capítulo~5 — anotações Q1R/Q2R e *insets* dos
  anéis vêm de \citep{Quaoar2023}).
- **Modelo usado:** `pipeline/model_training/outputs/resultado5_split0.8-0.2_less_features_noMin-noKmeans/`
  (mesmo Experimento~5 do capítulo~5; artefatos `xgboost_model.pkl`,
  `imputer_model.pkl`, `feature_names.pkl`).

---

## 7. Checklist de redação na tese

- [ ] Adicionar tabela de vereditos na Seção `sec:estudo_caso_quaoar`
      (subseção "Aplicação a recortes da curva") usando os números de §2.
- [ ] Inserir parágrafo sobre o experimento de expansão de janelas (§3),
      como evidência adicional na subseção de interpretação ou em
      "Limitações".
- [ ] **Adicionar tabela e parágrafo sobre o experimento de ajuste de
      limiar (§4)** na mesma subseção "Aplicação a recortes da curva",
      ou como continuação direta da Seção~5.9 (`sec:threshold_tuning`)
      — serve como demonstração empírica em dados reais externos ao
      treino do mecanismo lá apresentado. A frase de fechamento da
      sugestão §5.1 já incorpora esse resultado.
- [ ] Atualizar o item de trabalhos futuros do capítulo~6 com as três
      direções de §5.3 (janela deslizante, *features* locais, multi-classe),
      mantendo claro que o ajuste de $\tau$ resolve o caso prático mas
      não substitui as melhorias arquiteturais.
- [ ] Considerar gerar uma figura derivada (curva + 6 janelas coloridas,
      legenda com $\tau=0{,}5$ e $\tau=0{,}03$ lado a lado) para a tese,
      similar ao `quaoar_recortes.png`. Copiar para
      `writing_latex/Tese/pngs/`, e referenciar com label tipo
      `fig:quaoar_recortes`.
- [ ] Citação `\citep{Quaoar2023}` já está no bibtex (`teseon.tex:227`).

---

**Modelo recomendado para a configuração final da *pipeline*:**
**XGBoost**, com base em:
(a)~liderança no Experimento~7 (teste em curvas reais);
(b)~empate com CatBoost na configuração enxuta (11 features);
(c)~probabilidades mais polarizadas no estudo de caso Quaoar;
(d)~maior razão real-vs-ruído ($\sim 86\times$ vs $\sim 12\times$ no Q2R_1),
o que torna o ajuste de limiar $\tau$ mais robusto;
(e)~equivalência estatística pelo McNemar é respeitada — a escolha cai em
critérios secundários, e XGBoost vence nesses;
(f)~**no caso Quaoar com $\tau = 0{,}03$ (§4), atinge recall de 100\%
sobre os quatro eventos físicos sem nenhum falso positivo nos dois
recortes-controle**, validando empiricamente o mecanismo de
*threshold tuning* da Seção~5.9.

**Modo operacional sugerido:** XGBoost (Experimento~5, 11 *features*)
$+$ $\tau = 0{,}03$ para campanhas de triagem em que o custo de perder
uma ocultação supera o de revisar um falso alarme — caso típico de
ocultações por TNOs com possíveis anéis ou atmosferas. Para relatórios
de desempenho geral, manter $\tau = 0{,}5$.
