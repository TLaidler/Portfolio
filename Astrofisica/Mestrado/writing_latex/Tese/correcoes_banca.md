# Correções da dissertação — carta da banca (Dra. Flavia L. Rommel, 21/08/2026)

> **Trabalho:** *Pipeline para Detecção Automatizada de Ocultações Estelares em Curvas de Luz com Técnicas de Machine Learning* — Thiago Laidler Vidal Cunha (ON).
> **Painel:** três revisores-agente inspirados em **Richard Feynman** (física, honestidade), **Carl Sagan** (comunicação, narrativa) e **Jim Simons** (rigor quantitativo, código), mais a coordenação, que verificou os achados decisivos.
> As vozes são homenagem; as críticas são reais, com arquivo:linha e números conferidos no código e nos *outputs*.
> **Nada foi alterado nos `.tex`.** Este documento só propõe as correções.
> As memórias completas das rodadas 1 e 2 estão em [`painel_memorias.md`](painel_memorias.md).

---

## 0. Como usar

1. Comece pela **Seção 5 (Prioridades)**. Os itens P0 são afirmações falsas ou números errados, que uma banca atenta vai encontrar.
2. Os blocos de correção (Partes A, B e C, no fim) seguem sempre o mesmo formato:
   - **Local:** `arquivo:linha`. Os números de linha são do estado atual dos `.tex`. Aplique de baixo para cima em cada arquivo, ou use busca pelo trecho.
   - **Trecho atual:** cópia literal do texto, conferida por busca exata nos `.tex`. Simons verificou 112 de 112 trechos; Feynman e Sagan também conferiram os seus.
   - **Proposta:** LaTeX pronto para colar.
   - **Status:** um dos três valores abaixo.
     - `aplicável direto`
     - `requer confirmação do autor` (o fato só você sabe)
     - `decisão autor+orientador`
3. Onde dois revisores propuseram coisas diferentes, vale a **Seção 6 (Reconciliação)**.
4. As referências novas trazem os metadados marcados como "verificados" ou "a verificar". Confira os marcados "a verificar" antes de entregar.

**Cobertura:** os 102 itens da carta.

| Parte da carta | Itens |
|---|---|
| Comentários gerais | a–p |
| Cap. 1 | q–aa |
| Cap. 2 | bb–nn |
| Cap. 3 | 1–26 |
| Cap. 4 | 1–19 |
| Cap. 5 | 1–11 |
| Cap. 6 | i–vi |

Os itens que só o autor pode resolver estão na Seção 1. Cada revisor acrescentou ainda até 8 "extras obrigatórios", que a banca não pediu.

| Parte | Revisor | Conteúdo |
|---|---|---|
| A | Sagan | Gerais a, b, c, d, e, g, h, k, l, n, o, p; Cap. 1 (q–aa); varreduras globais; 9 referências |
| B | Feynman | Gerais f, j, m; Cap. 2 (bb–nn); Cap. 4 (1–19); 15 referências |
| C | Simons | Cap. 3 (1–26); Cap. 5 (1–11); Cap. 6 (i–vi); 9 referências |

---

## 1. Itens que exigem o autor (excluídos do processo)

São intervenções em imagens ou dados que uma LLM não pode fazer. Foram comunicados no início e ficaram fora das propostas. As partes **textuais** desses itens (legendas LaTeX, transições, citações) estão tratadas nas Partes A–C.

| # | Item da carta | O que fazer na imagem ou nos dados |
|---|---|---|
| 1 | Geral i | Fonte (tamanho e tipo) de todas as figuras; traduzir para o português os textos dentro das imagens (eixos, legendas internas, títulos) |
| 2 | Geral j | Decidir se mantém ou troca a Fig. 2.1 (Chariklo). O texto de transição para Umbriel está na Parte B |
| 3 | Cap2 mm | Fundir as Figs. 2.3 e 2.4, sobrepor a curva sintética e marcar imersão e emersão com linha ou seta. As correções de legenda estão na Parte B |
| 4 | Cap3 24 | Substituir a Fig. 3.9 por um exemplo de astronomia ou traduzi-la. A citação a Zhong et al. 2023 está na Parte C; a figura tem 6 painéis, não 3 |
| 5 | Cap5 6 | Inset com zoom na Fig. 5.2 e nas figuras semelhantes do apêndice; título "precisão-revocação" dentro da imagem. A legenda provisória está na Parte C |
| 6 | Cap5 7 | Fig. 5.3 com os quatro modelos. **Já existe** `pngs/exp3/metrics_vs_threshold_2.png` (CatBoost e RegLog): basta incluí-la (Parte C) |
| 7 | Cap5 8 | Fig. 5.5 (recortes de Quaoar): fonte e rótulos coerentes com o texto e a Tabela 5.8 |
| 8 | Cap5 10 | Fig. 5.7: fonte e tradução. O reposicionamento do float está na Parte C |
| 9 | Cap6 ii | Nova figura comparando curvas de baixo e de alto SNR. A resposta textual está na Parte C |

---

## 2. Rodada 1 — leitura independente

Cada revisor leu os 10 `.tex` na íntegra, abriu figuras e conferiu o código. Ninguém leu a carta da banca nem as revisões anteriores (`critica_sagan_feynman.md`, `AUDITORIA_PIPELINE.md`), para não ancorar a leitura.

| Revisor | Nota R1 | Achado-manchete |
|---|---|---|
| Feynman | 6,5 | Física do Cap. 2 errada em quatro pontos; números "bons demais" com causa identificável |
| Sagan | 6,0 | A afirmação sobre Quaoar no resumo vai além da evidência; a narrativa abre em TNOs e fecha no K-means |
| Simons | 6,0 | Contagem de *features* errada nos experimentos; vazamento entre recortes-irmãos; seleção feita no próprio teste |

**Acertos em que os três concordam:**
- O Cap. 3 é didático de verdade, e os exemplos numéricos estão certos: Fresnel 1,22 km, ganho de Gini 0,30, Condorcet 25×65% → 94%.
- O exemplo da logística é a exceção (ver erros).
- A distinção entre o borrão da exposição (V_S·t_exp) e as lacunas do tempo morto é física de primeiros princípios.
- O Experimento 3 (simuladas só no treino, teste só com curvas reais) é a pergunta certa. A reexecução reproduz a tabela **exatamente** (`training_results.csv`).
- A exclusão da positiva-mãe dos recortes **funciona**: nenhuma das 125 mães sobra no dataset.
- Higiene de ML correta: o *imputer* e o *scaler* são ajustados só no treino, e o *scaler* só é usado na Regressão Logística.
- As tabelas de métricas conferem com os CSVs salvos. Não há número inventado.
- O sinal é real. A AUC contra negativas **reais** fica em ≈ 0,999, e o ML supera um limiar sobre uma única *feature* (F1 0,90–0,95 → 0,98–0,99, isto é, 3 a 10 vezes menos erros).
- A lição "importância ≠ insubstituibilidade" está certa. Com os números corretos, ela fica ainda melhor (ver Extras de Sagan).
- As ressalvas são honestas: não houve estudo de concordância de rótulos, as curvas defeituosas foram descartadas, o teste tem só 38 negativas reais e o caso Quaoar tem n pequeno.

---

## 3. Rodada 2 — debate (um loop)

Cada revisor leu as memórias dos outros dois e respondeu por escrito: concordâncias, divergências com evidência e nota revisada. O texto integral está em `painel_memorias.md`.

**Reconciliações:**
- **Vazamento, 18/38 (Feynman) contra 21/38 (Simons):** os dois estão certos, porque são splits diferentes.
  - No teste misto 80/20, 21 dos 38 recortes têm o irmão ("antes"/"depois" da mesma curva) no treino.
  - No Exp. 3, são 18 dos 37 recortes.
  - Além disso, 39 das 160 positivas do teste do Exp. 3 têm uma corda do mesmo evento no treino.
  - Em resumo, cerca de metade das negativas reais do teste tem um "gêmeo" no treino.
- **CatBoost em Quaoar, 2× contra 12×:** é a mesma tabela com denominadores diferentes. O Q2R₁ (0,058) fica 12× acima da janela de ruído (0,005) e 2× acima do controle de baseline (0,029). Conforme o modelo e a janela escolhida, a "separação" vai de 2× a 160×. Uma grandeza que varia 80 vezes com uma escolha arbitrária é um adjetivo, não uma medida (Feynman).
- **Sagan retirou um erro seu:** as 802 positivas não incluem as mães dos recortes. O banco tinha 927; o erro é só de redação (cap5:15, 206).
- **Feynman corrigiu o próprio E1:** o modelo não aprende "real × simulado". A separação contra negativas reais é genuína para eventos profundos. As simuladas inflam só a especificidade do teste misto.
- **Os três rejeitam as notas 8,0–8,5 da sessão anterior** (`critica_sagan_feynman.md`). Elas se apoiaram na concessão "τ = 0,03 recupera os Q2R sem nenhum falso positivo", que os próprios arquivos de predição refutam (Seção 4).

**Os achados mudam a conclusão da tese ou só a força das afirmações?** Os três concordaram:
1. **"Classificar ocultações bem definidas funciona."** Muda só a **força**. O número honesto é F1 ≈ 0,98 ± 0,005 (10 sementes, split agrupado por curva-mãe), com taxa de falsos positivos em negativas reais de 4–9% a τ = 0,5, e não "0,99 com precisão 1,000".
2. **"Um ajuste de limiar recupera eventos sutis sem falsos alarmes."** **Muda a conclusão**, de "demonstrado" para "ilustrado a posteriori, não validado".
3. **"A abordagem é comparável a CNN e à inspeção manual, e robusta em baixo SNR."** **Muda a conclusão**, para "não testado".

**Notas finais:** Feynman 6,0 (era 6,5); Sagan 6,0; Simons 6,0.
- Com a reescrita honesta e sem novos experimentos (resumo, tabela-mestra dos experimentos, física do Cap. 2, *baseline* na Tab. 5.9), a nota sobe para cerca de **7,5**.
- Com split agrupado por evento, τ escolhido por validação cruzada e uma varredura cega de Quaoar, sobe para cerca de **8**.

**"Frase honesta" para o resumo (consenso):**
```latex
Em curvas com ocultação bem definida, os classificadores separam eventos de não eventos com AUC-ROC acima de 0,995 e F1-score de 0,98 a 0,99, superando um limiar sobre uma única característica (F1 de 0,90 a 0,95). Como ilustração exploratória, a ferramenta foi aplicada a uma curva da ocultação por (50000) Quaoar externa ao treino: o corpo principal e o anel Q1R são detectados no limiar padrão, enquanto os cruzamentos do anel fino Q2R recebem probabilidades baixas, ainda que superiores às de uma janela de ruído vizinha. Um limiar reduzido, escolhido a posteriori ($\tau = 0{,}03$), os sinalizaria; esse mesmo limiar, porém, marca de 10\% a 18\% das curvas negativas reais do conjunto de teste. A recuperação de eventos sutis é, portanto, uma possibilidade promissora que exige validação sistemática, e não um resultado demonstrado.
```
O `foreignabstract` (teseon.tex:141) precisa espelhar a mesma mudança.

---

## 4. Verificações independentes da coordenação

Refeitas a partir dos artefatos do repositório, sem depender dos agentes.

| Afirmação | Verificação | Resultado |
|---|---|---|
| Contagem de *features* por experimento | `feature_names.pkl` de cada pasta em `pipeline/model_training/outputs/` | Exp1 = 28; **Exp4 = 13** (a tese diz 14); **Exp5 = 12** (a tese diz 13); Exp6 = 12, mas **mantém** `Feature_Savgol_Min`; Exp2 = 11 |
| Pasta "65/35" | `cmp` dos `training_results.csv` | `resultado6.1` é **idêntica** a `resultado5`: não é 65/35 |
| Falsos alarmes com τ = 0,03 | `resultado5/predictions_*.csv`, negativas reais do teste (n = 39) | XGBoost **4/39 = 10%** (e 1 FN); CatBoost **7/39 = 18%**; RF 36%; RegLog 44% |
| Recortes-irmãos | `split_train_curves.txt` × `split_test_curves.txt` (resultado5) | **21 dos 38** recortes do teste têm o irmão no treino. A frase de cap5:654 é falsa |
| `SNR_dip` em ruído puro | `compute_occ_features` em 400 séries gaussianas com N = 1000 | Mediana **5,3** (p5–p95: 4,5–6,5); depth/σ ≈ 3,2. A *feature* não é uma SNR |
| Gradiente do exemplo da logística (cap3:150) | Conta à mão | **−0,125** (o texto diz −0,15); J ≈ 0,678 |
| Aspas que "comem" o espaço (Geral n) | `on.cls:60` carrega `babel` com `brazil` | `"` é um atalho ativo e absorve o espaço seguinte. Correção: usar ` ``…'' ` |

---

## 5. Prioridades de aplicação

**P0 — afirmações falsas ou números errados.** A banca não pediu tudo isso, mas encontraria; corrija antes de qualquer outra coisa. Os blocos estão nos "Extras" de cada parte e em Cap5 1.
1. **Resumo e abstract:** trocar "duas ordens de grandeza … sem introduzir falsos alarmes" pela frase honesta da Seção 3 (Sagan Extra 1; Simons Extra 3).
2. **Contagem de *features* e nomes dos experimentos:**
   - 14 → 13 (Exp. 4) e 13 → 12 (Exp. 5).
   - O Exp. 6 mantém `Feature_Savgol_Min`.
   - Adicionar a tabela-mestra experimento ↔ *features* ↔ pasta (Simons Cap5 1 e Extra 4).
3. **Vazamento:** apagar a frase falsa de cap5:654 e declarar o número: cerca de metade das negativas reais do teste tem o irmão no treino (Simons Extra 1; Sagan Extra 8).
4. **Limiar:** τ foi escolhido no próprio teste, e o critério "≥ 99,5%" não foi aplicado na Tab. 5.7. Declarar isso e corrigir os pontos operacionais (Simons Extra 2).
5. **Hipótese:** sai "corroborada", entra "corroborada em parte". Adicionar o *baseline* de uma *feature* ao lado dos *ensembles* (Simons Extra 8; Sagan Extra 3).
6. **Teste de "baixo SNR" (cap6:18):**
   - É *in-sample*: 48 das 67 curvas estavam no treino.
   - Seleciona, na prática, ocultações **profundas**.
   - Reescrever (Simons Cap6 ii; Feynman Extra 4).
7. **Física do Cap. 2:**
   - O patamar não vai a zero, porque a luz do corpo continua na abertura (Cap2 ii).
   - A escala de Fresnel usa a distância observador–corpo e limita a resolução **ao longo** da corda (jj, kk).
   - A legenda da Fig. 2.3 está invertida (mm).
   - "Trânsito" → "ocultação".
8. **Números desatualizados:**
   - Faixas de F1: 0,974–0,994 / 0,975–0,982 → **0,984–0,994 / 0,978–0,991**.
   - Queda na variante 65/35: "≈ 2 pp" → **0,7 pp**.
   - AUC "≥ 0,998" (cap5:753) → **≥ 0,995** em todos os cenários (≥ 0,996 sem a variante 65/35, cujo RF tem 0,9956). Isso vale também para a proposta de Simons Extra 5.
   - CatBoost do Exp. 6 = 0,9874 (o texto diz ≥ 0,990).
   - "63%" → 69% ou 64%, conforme o experimento.
   - Banco: 802 → **927** positivas; amostras usadas: 1693 → **1692**, por causa do `dropna` (Simons Extras 5–7).
9. **Texto que contradiz o código:**
   - A importância do XGBoost é *gain*, não *weight*.
   - A *PredictionValuesChange* não usa permutação.
   - A Regressão Logística usa L2, C = 1 e solver L-BFGS: sem validação cruzada, sem Lasso, sem gradiente descendente.
   - O XGBoost não tem ponderação de classes.
   - A janela de suavização corta em 40 pontos, não em 120, e a média móvel não é calculada.
   - A região de ocultação dos recortes é automática (fluxo < 0,78), e a remoção de *outliers* só é aplicada aos negativos.
   - O tempo está em dias julianos nas 18 curvas do Grupo do Rio e em segundos nas do VizieR.
   - Simons Cap3 11/20 e Cap5 3; Feynman Cap4 5/8/12.
10. **Exemplo numérico da logística:** −0,125 e J ≈ 0,678 (Simons Cap3 10).
11. **LaTeX que quebra:**
    - `tab:features_final` sem `table` nem `\caption` (Simons Cap6 i).
    - Placeholders de banca e CDU em teseon.tex:69, 72–75.
    - TODO no Apêndice C.
    - URL errada do simulador (Feynman Cap4 6).

**P1 — itens da banca com status `aplicável direto`:** a maioria dos blocos.
- Comece pelas trocas mecânicas globais, que resolvem vários itens de uma vez:
  1. aspas ` ``…'' ` (Geral n);
  2. `\usepackage{indentfirst}` (b);
  3. `\raggedbottom` (s);
  4. `\usepackage{upquote}` (Cap4 18);
  5. S/N → SNR (k);
  6. "sintéticas" → "simuladas", 28 ocorrências (l);
  7. `\citet`/`\citep` (e).

**P2 — `decisão autor+orientador`:**
- renomear os experimentos (Simons propõe 1, 1.1, 1.2a, 1.2b, 2, 3, 3.1);
- a notação única (Seção 6);
- a política de estrangeirismos (Geral c);
- a lista de siglas (h);
- a reestruturação da Seção 4.4 (Feynman Cap4 6).

**P3 — `requer confirmação do autor`:** fatos que só você sabe.
- o valor de "~X anos";
- "a bordo de telescópios";
- os fóruns IOTA;
- os 11 descartes;
- se houve checagem manual de tempo;
- o URL e a tag do repositório.

**Reanálises opcionais (fortalecem a defesa, não são exigidas pela banca):**
1. split e CV com `StratifiedGroupKFold`, agrupando por curva-mãe e por evento;
2. τ escolhido por validação cruzada no treino;
3. varredura cega de Quaoar com janelas de mesma duração, para estimar a taxa de falso alarme;
4. converter os tempos para segundos e refazer `Occ_duration_s`;
5. teste de injeção e recuperação de anéis simulados em curvas reais.

Os scripts de apoio estão no scratchpad desta sessão (`repro_exp.py`, `seed_spread.py`, `baseline1f.py`, `reconcile_siblings.py`). Se quiser mantê-los, peça que eu os copie para `pipeline/`.

---

## 6. Reconciliação entre revisores (vale sobre as Partes A–C)

### 6.1 Notação única (Geral m; Cap3 15, 19, 23.2, 25)
Feynman propôs trocar 17 símbolos; Simons, o mínimo. Adota-se o **mínimo que elimina toda ambiguidade**. Onde os blocos de Feynman usam φ para o fluxo, leia **F** (φ_base → F_base, σ_φ → σ_F).

| Símbolo hoje | Problema | Adotar |
|---|---|---|
| f (Fresnel, Cap. 2) | colide com o classificador f (Cap. 3) | **L_F = √(λΔ/2)**, com **Δ** = distância observador–corpo (Feynman jj/kk) |
| f (classificador) / f(x) (verdade) / f̂ | — | **f** = classificador; **f\*** = relação verdadeira; **f̂** = estimativa (Simons 23.2) |
| f, f̃, f′, f″ (fluxo, Cap. 5) | colide com o classificador | **F, F̃, F′, F″**, coerente com o F(t) do Cap. 4 (Simons) |
| m (nº de exemplos na logística) e n (nº de exemplos em cap3:45) | dois símbolos para a mesma coisa; m também é a iteração do *boosting* | **n** = nº de exemplos em todo o texto (m = 4 → n = 4); **m** fica só para a iteração do *boosting* (Feynman). Isso substitui a troca m → t de Simons Cap3 15 |
| F_m (modelo de *boosting*) | colide com o fluxo F(t) | **f̂_m(x) = f̂_{m−1}(x) + η h_m(x)**: o modelo de *boosting* é a estimativa do classificador |
| k / K (K-means) | os dois no mesmo parágrafo | **K** sempre (Simons 19) |
| k (dobras) | colide com o K-means | **q** dobras, mantendo o nome "*k-fold*" (Simons 25) |
| σ (MAD no χ²) | colide com o desvio padrão | **s_MAD** (Feynman 17b); σ_baseline → **σ_base**; ruído irredutível → **σ_ε²** |
| β_j (coeficientes da RL, Cap. 5) | o Cap. 3 chama de θ | **θ_j**; β só em F_β |
| Opcionais | — | J da inércia do K-means → W; ΔI(n) → ΔG; `pred_i` → F̂_i (Feynman 17d). Sigmoide σ(z) pode ficar, porque com argumento não há ambiguidade |

### 6.2 Referências duplicadas entre Partes A e B
- Use **uma** entrada para cada referência:
  - `Ortiz2020`: as Partes A e B trazem a mesma entrada.
  - `Herald2020`: idem.
  - Gaia: adote as chaves **`Gaia2016`** e **`GaiaDR3`**, da Parte A. Na Parte B, onde aparece `GaiaMission2016`, use `Gaia2016`.
- Use a entrada `Simulator` da Parte B: **DOI 10.1140/epjs/s11734-023-01031-z**, verificado. Ela substitui o link quebrado em teseon.tex:232.
- Remova o `\bibitem` de **Zhu2022**, que deixa de ser citado (Parte A, t.i).
- Coloque a lista inteira em **ordem alfabética**, como pede o sistema autor-data da ABNT (NBR 6023).

### 6.3 Outros pontos
- **SORA (Cap2 jj.iv):** o acrônimo **já é aberto** em capitulo2.tex:65; a banca não viu. Use a forma `\textit{Stellar Occultation Reduction and Analysis} \citep[SORA,][]{SORA2022}` (Parte A, item e), que imprime exatamente o que a banca pediu.
- **PRAIA:** a expansão correta é *Platform for Reduction of Astronomical Images Automatically*, a do título do artigo. Introduza-a no parágrafo da fotometria (Feynman dd) e retire a expansão de capitulo2.tex:65 (Feynman ff).
- ***Features* × características (Cap4 1):** a opção mais barata é manter *\textit{features}*, que já está em itálico 194 vezes, e corrigir as 15 ocorrências sem itálico (Geral c). A alternativa é usar "características" em todo o texto (Feynman). É decisão autor+orientador; o importante é **não misturar**.
- **"Curva de luz de ocultação" (Geral d):**
  - Defina o termo uma vez, na Introdução (Sagan t.i).
  - Feynman dd dá a definição operacional no Cap. 2 (razão alvo/referência).
  - Use a forma completa na primeira ocorrência de cada capítulo e nos títulos.

---

## 7. Onde o painel discorda da banca (com fundamento)

Nesses pontos a sugestão literal da banca é imprecisa ou conflita com os dados. Os blocos trazem a alternativa.

| Item | Sugestão da banca | Problema | Alternativa |
|---|---|---|---|
| Cap2 bb | A escala 1:1 da sombra vale para TNOs, "não necessariamente para asteroides próximos" | Os raios são paralelos para qualquer corpo do Sistema Solar. O que quebra o 1:1 é o tamanho do corpo comparado a L_F e ao diâmetro estelar projetado, e ambos **crescem** com a distância | Feynman bb |
| Cap2 cc | V_S = velocidade orbital do corpo + rotação da Terra | Omite o **movimento orbital da Terra** (~30 km/s), o termo dominante para TNOs | Feynman cc |
| Cap2 cc.i | Uma corda "se traduz em uma medida precisa do perfil" | Uma corda dá **dois pontos** do limbo; o perfil vem do conjunto de cordas | Feynman cc.i |
| Cap2 jj.iv | Abrir o acrônimo SORA | Já está aberto em cap2:65 | Seção 6.3 |
| Cap4 9 | "Posição ao longo da corda" seria erro | Não é erro: o simulador usa x(t) = V_S(t − t₀). O que ele **não** modela é o parâmetro de impacto, porque usa só a corda central | Feynman Cap4 9 |
| Cap4 17a | Retirar "ruído de fótons" | O ruído de Poisson é a fonte fundamental, e o próprio simulador o inclui | Manter, com definição (Feynman 17a) |
| Cap4 19 | Conjunto "representativo da realidade das campanhas" | Os dados contradizem: 79% das negativas são simuladas, com ruído cerca de 3× menor (σ_base 0,021 × 0,058) | Feynman Cap4 19 |
| Cap5 9 | "Queda de ~2 pp" | O número correto é **0,7 pp** (0,9906 → 0,9838, reproduzido), e é hipótese, não resultado | Simons Cap5 9 |
| Cap5 11 | Falta o desvio padrão do F1 | A Tab. 5.10 **já o traz** (0,0062–0,0104). Falta o texto usá-lo | Simons Cap5 11 |
| Cap5 8 | "segundos a partir de 2022-08-09 06:35:49,26" | Erro de digitação: o instante de referência é **06:34:49,26**. A coluna do `.dat` está em segundos do dia (UTC) | Simons Cap5 8 |
| Cap3 10 | "a separação se consolida e o custo é minimizado" | Os 4 pontos são linearmente separáveis, então não há mínimo finito sem regularização. E o gradiente do exemplo está errado | Simons Cap3 10 |

---

## 8. Respostas factuais às perguntas da banca (do código e dos dados)

| Pergunta | Resposta | Fonte | Status |
|---|---|---|---|
| Quantas curvas foram baixadas do VizieR? (Cap4 2) | 923 baixadas (prévias `.png`) e 912 inseridas. O banco tem 931 observações (912 VizieR + 19 Grupo do Rio): 928 positivas e 3 negativas. Chiron tem **0 pontos** | `data_warehouse/plots/`, `stellar_occultations.db` | confirmar |
| O que eram as "curvas defeituosas"? (Cap4 4) | O código não marca defeitos. A triagem foi visual, pelas prévias: 11 de 923 descartadas. Duas curvas inseridas têm o tempo fora de ordem e cerca de 14% das positivas têm fluxo normalizado implausível (máximo de até 2453) | `insert_new_data.py` | confirmar |
| Como foi a checagem de alinhamento temporal? (Cap4 5) | **Não houve** no código: sem conversão de unidades e sem ordenação. São 19 curvas em dias contra segundos no VizieR | `insert_new_data_manually.py:69–120` | confirmar (checagem manual?) |
| Os rótulos do VizieR vêm "dos curadores"? (Cap4 7) | Não. Todas as curvas baixadas vão por padrão para a pasta `positive` | `insert_new_data.py:342–385` | confirmar |
| O que é "posição ao longo da corda" no simulador? (Cap4 9) | x(t) = V_S(t − t₀), com uma faixa opaca 1-D, isto é, só a corda central. Nas negativas, o diâmetro é 0 | `simulate_curve.py:483–493` | aplicável |
| Como a janela de suavização é escolhida? (Cap4 12) | w = max(3, ⌊N/3⌋) se N < 40; senão max(3, ⌊N/40⌋), ímpar. O corte é **40**, não 120. Curvas com menos de 5 pontos são descartadas | `build_dataset.py:310–321` | aplicável |
| Quantas *features* no teste de baixo SNR? (Cap6 ii) | **11** (modelos do Exp. 2, `resultado5`) | `test_low_snr.py:45–49` | aplicável |
| Onde está o código? (Cap6 iii) | github.com/TLaidler/Portfolio, em `Astrofisica/Mestrado/pipeline`. **Atenção:** `*.csv` está no `.gitignore`, então o dataset, os resultados e os `.dat` simulados não estão versionados | `.gitignore`, `git remote` | confirmar (tag, DOI, licença) |
| Ordem e número de colunas do `.dat`; barras de erro? (Cap6 v) | A 1ª coluna é o tempo e a 2ª o fluxo; a 3ª (erro) é lida e **descartada**. As barras de erro não são usadas em nenhuma etapa | `insert_new_data_manually.py:116`; `create_database.py:27–32` | aplicável |
| Por que a Fig. 5.3 tem só 2 modelos? (Cap5 7) | O código gera duas figuras, `_1` (RF + XGB) e `_2` (CB + RegLog), e só a `_1` entrou na tese | `train_model.py:861–890` | aplicável |
| Por que só XGBoost e CatBoost em Quaoar? (Cap5 8) | `test_quaoar.py` carrega o CatBoost e `test_quaoar_recortes.py` o XGBoost. O XGBoost foi acrescentado depois, por dar probabilidades mais polarizadas; isso deve constar no texto | scripts citados | aplicável |
| A *scikit-learn* foi usada? (Cap3 12.3) | Sim: Regressão Logística, RF, K-means, *imputer*, *scaler* e métricas | `train_model.py:31–47` | aplicável |
| O que é K e o que é k no K-means? (Cap3 19) | São a mesma coisa. Padronizar em K | — | aplicável |

---

*A seguir, os blocos completos de cada revisor, sem edição. Onde houver conflito, valem as Seções 6 e 7 acima.*


---

# PARTE A — Revisor Sagan: Comentários gerais e Capítulo 1


Escopo: Comentários gerais a, b, c, d, e, g, h, k, l, n, o, p; Capítulo 1 (q a aa); varreduras globais.
Base: SP\critica.txt, conferido contra os .tex em ROOT\writing_latex\Tese. Todos os trechos citados foram verificados por grep.
Varreduras próprias: SP\sagan_scan.py (termos em inglês sem itálico; padrão ")\citep"), SP\sagan_etc.py (listas entre parênteses)
e SP\terms_out.txt (saída bruta).
Nenhum arquivo do projeto foi editado.

Convenções deste arquivo:
- "Status" usa três valores: aplicável direto | requer confirmação do autor | decisão autor+orientador.
- Paragrafação da banca: conferida. Atenção ao item x: a banca escreve "Seção 1.2, parágrafo 2", mas o trecho está no
  parágrafo 3 (introducao.tex:24). Os itens w, y, z e aa batem com a numeração da banca.
- As normas ABNT só são citadas quando tenho segurança sobre o conteúdo; caso contrário, aparece "verificar norma".
  Observação útil: a NBR 6023 trata de referências e a NBR 10520 de citações; nenhuma das duas, até onde sei, regula o itálico de
  estrangeirismos no corpo do texto. Essa é uma convenção tipográfica (manuais de estilo, normas do programa) — verificar norma.

Resumo: 26 blocos (12 gerais + 14 do Cap. 1) e 9 novas referências bibliográficas.
- Aplicáveis direto: b, e, g, k, n, r, s, t.i, t.ii, u, w, x.i, x.ii, x.iii, y.
- Aplicáveis com decisões de política ou confirmação pontual: a, c, l, p.
- Dependem do autor (fato que só ele sabe, ou decisão com o orientador): d, h, o/q, v, z, aa.

=====================================================================================================
## PARTE A — COMENTÁRIOS GERAIS
=====================================================================================================

### Geral a — ordenação das ideias e ortografia
- Local e trechos atuais (todos verificados):
  1. teseon.tex:136 (resumo): "A \textit{pipeline} permite ainda o ajuste do limiar de decisão em pós-processamento, operando em regime de alta sensibilidade sem necessidade de retreinamento. Nesse contexto, o custo de perder um evento genuíno (falso negativo) supera o de revisar um alarme falso (falso positivo)."
  2. capitulo3.tex:94: "varios pontos positivos ficam proximos do limiar de decisão"
  3. capitulo3.tex:111: "Isso pois a saída continuará continua, mas dessa vez limitada entre 0 e 1."
  4. capitulo3.tex:75: "a solução completa desses problemas podem ser acompanhadas no capítulo 2 de \citep{Levada2026}"
  5. capitulo4.tex:101: "com suas classificação verdadeira (positiva ou negativa)"
  6. capitulo2.tex:116: "Notadamente, nos interessam também que sejam apontados eventos tênues"
- Proposta:
  1. `Como, na triagem, o custo de perder um evento genuíno (falso negativo) supera o de revisar um alarme falso (falso positivo), a \textit{pipeline} permite ajustar o limiar de decisão em pós-processamento e operar em regime de alta sensibilidade, sem necessidade de retreinamento.`
     A justificativa vem antes da consequência. No mesmo resumo, "Os resultados demonstram" aparece duas vezes; troque a segunda por `Esses resultados indicam o potencial da ferramenta...`.
  2. `vários pontos positivos ficam próximos do limiar de decisão`
  3. `Isso porque a saída continua contínua, mas agora limitada entre 0 e 1.`
  4. `a solução completa desses problemas pode ser acompanhada no Capítulo~2 de \citet{Levada2026}`
  5. `com sua classificação verdadeira (positiva ou negativa)`
  6. `Interessa-nos também que sejam apontados eventos tênues` (o resto da frase é tratado no item Cap. 2 nn, outro revisor).
- Justificativa: a banca considera a ortografia "praticamente sem erros"; os seis casos acima são os que restam no texto. A
  ordem justificativa → consequência é a que o leitor não especialista acompanha.
- Status: aplicável direto.

### Geral b — recuo do primeiro parágrafo
- Local: teseon.tex:20
- Trecho atual: `%\usepackage{indentfirst}`
- Proposta: `\usepackage{indentfirst}` (basta descomentar). Os `\noindent` deliberados (capitulo3.tex:130 e :201, títulos de
  "Exemplo numérico") continuam valendo.
- Justificativa: a classe `book` (on.cls:56) suprime o recuo do primeiro parágrafo após um título, o que explica a observação da banca; o pacote
  `indentfirst` padroniza o recuo de todos os parágrafos, como é o costume tipográfico brasileiro. NBR 14724: verificar norma.
- Status: aplicável direto.

### Geral c — palavras em inglês: itálico e tradução na primeira ocorrência
- Política proposta (vale para o documento inteiro):
  (i) Itálico para estrangeirismos comuns sem tradução consagrada: \textit{pipeline}, \textit{feature(s)}, \textit{ensemble(s)},
      \textit{baseline}, \textit{dip}, \textit{boosting}, \textit{gradient boosting}, \textit{bagging}, \textit{bootstrap},
      \textit{clustering}, \textit{outlier(s)}, \textit{batch}/\textit{mini-batch}, \textit{out-of-bag}, \textit{max drawdown},
      \textit{script(s)}, \textit{seeing}, \textit{big data}, \textit{grid search}, \textit{clip}, \textit{Debug Console}, \textit{logloss},
      \textit{insets}, \textit{trade-off}, \textit{top-down}.
  (ii) Preferir o termo em português quando ele existe e já foi definido no texto (melhor para o leitor não especialista):
      overfitting → sobreajuste; underfitting → subajuste; frames → quadros; folds/k-fold → dobras/validação cruzada com $k$ dobras;
      dataset → conjunto de dados; precision-recall → precisão-sensibilidade; recall → sensibilidade; threshold → limiar;
      download → transferência.
  (iii) Fonte redonda (sem itálico) para nomes próprios de métodos, programas e bibliotecas (Random Forest, XGBoost, CatBoost, K-means,
      Savitzky-Golay, Ridge, Lasso, Elastic Net, CART, SORA, PRAIA, VizieR, SQLite, Python), para siglas (ML, AUC-ROC, SNR, TNO, OOB)
      e para nomes de métricas (F1-score, F$_\beta$-score). → decisão autor+orientador; ver as 36 ocorrências de "score" abaixo.
  (iv) \texttt{} para identificadores de código. Hoje vários aparecem em \textit: capitulo3.tex:198 (\textit{max\_depth}, \textit{min\_samples\_leaf}),
      capitulo3.tex:264 e capitulo4.tex:255 (\textit{auto\_class\_weights='Balanced'}), capitulo4.tex:253-254 (\textit{n\_estimators},
      \textit{max\_depth}, \textit{class\_weight='balanced'}, \textit{learning\_rate}) e os itens de apendice_hiperparametros.tex:11-47.
  (v) Em títulos de capítulo e seção, use `\texorpdfstring{\textit{pipeline}}{pipeline}` para não gerar aviso do hyperref nos marcadores do PDF.
- Ocorrências SEM itálico a corrigir (varredura completa, excluindo math, \texttt, \cite, \ref, bibliografia e resumo em inglês):
  - pipeline(s): teseon.tex:48 (título → decisão autor+orientador), teseon.tex:166 (`\chapter{Metodologia: \texorpdfstring{\textit{pipeline}}{pipeline} de detecção}`),
    capitulo3.tex:47 ("nas pipelines de ML"), capitulo3.tex:78 (\section), capitulo4.tex:10 (\section), capitulo6.tex:31 (`\textbf{\textit{Pipeline} completa de detecção:}`).
    Gênero: "o \textit{pipeline}" → "a \textit{pipeline}" em capitulo5.tex:749, capitulo6.tex:35 ("do" → "da") e apendice_ambiente.tex:7.
  - Machine Learning: teseon.tex:48 (título: decisão autor+orientador), teseon.tex:88 (palavra-chave; ver Extras/Geral h), teseon.tex:162 →
    `\chapter{Modelos e algoritmos de aprendizado de máquina}`; capitulo3.tex:8 → `\section{Conceitos fundamentais de aprendizado de máquina}`;
    capitulo3.tex:5 "os modelos de Machine Learning" → `os modelos de aprendizado de máquina`.
  - big data: teseon.tex:89 (palavra-chave "Big Data"; ver Extras).
  - feature(s): introducao.tex:28; capitulo3.tex:19 (\textbf{feature} → \textbf{\textit{feature}}); capitulo3.tex:45, :131, :153, :224, :278, :328, :410;
    capitulo4.tex:127; capitulo5.tex:46 e :123 (cabeçalhos de tabela, \textbf{Feature(s)} → \textbf{\textit{Feature(s)}}).
  - ensemble(s): introducao.tex:32 (\textbf{ensembles} → \textbf{\textit{ensembles}}); capitulo3.tex:27; :220 (\textbf{ensemble}); :222 (2x); :318;
    capitulo4.tex:253; :258.
  - clustering: capitulo3.tex:35, :272.
  - threshold: capitulo3.tex:47 ('threshold' entre aspas simples → `\textit{threshold}`, ou "limiar", item Cap. 3 nº 5).
  - outlier(s): capitulo3.tex:94, :103.
  - overfitting: capitulo3.tex:153, :248, :390 (\subsection{Overfitting, underfitting...} → `\subsection{Sobreajuste, subajuste e o compromisso entre viés e variância}`), :393, :406;
    capitulo4.tex:276 ("possível overfitting" → "possível sobreajuste").
  - underfitting: capitulo3.tex:390, :393, :406.
  - out-of-bag: capitulo3.tex:220 (\textbf{out-of-bag} → \textbf{\textit{out-of-bag}}).
  - boosting / gradient boosting: capitulo3.tex:242 (\subsection{XGBoost (eXtreme Gradient Boosting)} → `(\textit{eXtreme Gradient Boosting})`), :244 (2x, em \textbf),
    :250, :292, :298, :311.
  - batch / mini-batch: capitulo3.tex:292 (2x: \textbf{Batch GD}, \textbf{Mini-batch GD}), :311 (2x, na tabela).
  - max drawdown: capitulo3.tex:328 (primeira ocorrência → `queda máxima acumulada (\textit{max drawdown})`), capitulo4.tex:158 (`\subsection{Queda máxima acumulada (\textit{max drawdown})}`),
    capitulo4.tex:167, :228.
  - precision-recall / recall: capitulo3.tex:388, capitulo4.tex:262, :264 → `curva precisão-sensibilidade` (no Cap. 5 já é assim: capitulo5.tex:364).
  - fold(s): capitulo3.tex:448 ("(k-fold)" → `(\textit{k-fold})`), capitulo5.tex:656 ("5-fold" → `com 5 dobras`), capitulo5.tex:737 (idem).
  - baseline: capitulo4.tex:17, :89, :91 (2x), :185 (\textbf{Baseline.}), :187, :193 (2x), :201 (2x), :207, :228 (3x), capitulo5.tex:78, :79.
    (As ocorrências em \mathrm{baseline} são nomes de variável e podem continuar como estão.)
  - dip: capitulo4.tex:187, :193, :195, :213, :222 (3x), :228 (2x); capitulo5.tex:76, :77, :80, :101.
  - frame(s): capitulo4.tex:201, :228; capitulo5.tex:79, :110 → `quadros`.
  - dataset: capitulo4.tex:101 (definição; ok em itálico), :119, :224, :236, :276; apendice_ambiente.tex:7 → `conjunto de dados`.
  - script(s): capitulo4.tex:47 ("Scripts em Python"), capitulo6.tex:56, apendice_hiperparametros.tex:7, :36, apendice_ambiente.tex:24.
  - download: capitulo4.tex:47.
  - clip: capitulo5.tex:465 (o sentido técnico é do item Cap. 5 nº 8).
  - Debug Console: capitulo5.tex:486.
  - Grid Search: apendice_hiperparametros.tex:50 → `\textit{grid search}`.
  - "score" (F1-score, F$_2$-score, F$_\beta$-score), 36 ocorrências: teseon.tex:136; introducao.tex:26; capitulo3.tex:364, :369 (2x), :388 (2x), :453;
    capitulo4.tex:23, :95(*), :245, :262 (2x), :266; capitulo5.tex:13, :242, :252, :268, :283, :314, :366, :374, :427 (2x), :546, :550, :654, :735;
    capitulo6.tex:6; apendice_experimentos.tex:21, :31, :53, :85, :109, :147; apendice_hiperparametros.tex:50. (*) capitulo4.tex:95 é "z-score".
    Recomendo manter em redondo, como nome de métrica (política iii), e definir na primeira ocorrência (capitulo3.tex:364): `\textbf{F1-score} (pontuação F1)`.
- Itálicos que ainda precisam de tradução ou explicação na primeira ocorrência:
  - introducao.tex:24 \textit{seeing} → ver item x.i;
  - introducao.tex:24 e capitulo2.tex:24 \textit{big data} → `grande volume de dados (\textit{big data})`;
  - capitulo4.tex:17, primeiro "baseline" → `linha de base (\textit{baseline}, o nível de fluxo fora da ocultação)`;
  - capitulo4.tex:187, primeiro "dip" → `Profundidade da queda (\textit{dip}).`;
  - capitulo3.tex:19 \textit{Mean Decrease Accuracy} → `(\textit{Mean Decrease Accuracy}, MDA, a queda média da acurácia)`;
  - capitulo4.tex:264 \textit{trade-off} → `o compromisso (\textit{trade-off})`;
  - capitulo4.tex:49 \textit{previews} → `pré-visualizações (\textit{previews})`;
  - capitulo5.tex:462 \textit{top-down} → `em estilo linear (\textit{top-down}), de cima para baixo`;
  - capitulo5.tex:478 \textit{insets} → `nos quatro quadros ampliados (\textit{insets})`;
  - capitulo5.tex:717 \textit{logloss} → `a perda logarítmica (\textit{logloss}), isto é, a entropia cruzada da Seção~\ref{sec:modelos_classificacao}`.
- Grafias a uniformizar (mesmo termo escrito de formas diferentes):
  - "K-Means" (12x: capitulo5.tex:58, :127, :270, :471, :574, :638, :749; capitulo6.tex:35; apendice_experimentos.tex:74, :95, :105, :123) ×
    "K-means" (10x: capitulo3.tex:269, :272, :278, :328; capitulo4.tex:127, :169, :171, :228; introducao.tex:32, :34). Proposta: "K-means" em todo o texto.
  - "StandardScaler": capitulo3.tex:169 sem formatação × \texttt{StandardScaler} em capitulo4.tex:127 e capitulo5.tex:175 → `\texttt{StandardScaler}` (item Cap. 3 nº 11).
  - "Floresta Aleatória" (capitulo3.tex:218, :229) × "Random Forest" (50x): ver item Cap. 3 nº 14 (outro revisor).
- Justificativa: a banca aponta estrangeirismos sem destaque e sem tradução sobretudo nos capítulos iniciais; a varredura confirma, e
  mostra que o problema maior está nos Caps. 3 e 4. A política (ii) reduz o número de itálicos e ajuda o leitor não especialista. Norma: verificar norma.
- Status: aplicável direto para as listas; decisão autor+orientador para a política (iii) — "Random Forest", "F1-score" e o título da dissertação.

### Geral d — "curva de luz de ocultação" (distinguir das curvas de rotação)
- Locais (primeira ocorrência por capítulo, mais títulos e resumo):
  teseon.tex:136 ("A análise da curva de luz resultante"); introducao.tex:14 ("A análise da \textbf{curva de luz} - a variação temporal do fluxo estelar -");
  capitulo2.tex:15 ("a curva de luz registra as quedas de fluxo"); capitulo2.tex:62 (\section{Da observação às curvas de luz: coleta e armazenamento});
  capitulo3.tex:5 ("podem produzir diversas curvas de luz"); capitulo4.tex:5 ("ocultações estelares em curvas de luz"); capitulo5.tex:11 (idem);
  capitulo6.tex:6 (idem). Há 62 ocorrências de "curva(s) de luz" nos capítulos e só 3 já com "de ocultação".
- Proposta:
  1. Definir uma vez, na Introdução (texto pronto no item t.i): `\textbf{curva de luz de ocultação} --- a variação temporal do fluxo da estrela registrada durante o evento, que não deve ser confundida com as curvas de luz rotacionais usadas para determinar períodos de rotação ---`.
  2. Usar a forma completa na primeira ocorrência de cada capítulo, nos títulos de seção e no resumo:
     teseon.tex:136 → `A análise da curva de luz de ocultação resultante`;
     capitulo2.tex:62 → `\section{Da observação às curvas de luz de ocultação: coleta e armazenamento}`;
     capitulo3.tex:5, capitulo4.tex:5, capitulo5.tex:11, capitulo6.tex:6 → `curvas de luz de ocultação`.
  3. No resto do texto, manter "curva de luz", já que a definição está feita. Trocar todas as 62 ocorrências pesaria a leitura.
     Com isso, capitulo4.tex:49 ("curvas de rotação") passa a dialogar com a definição.
- Justificativa: atende à banca sem tornar o texto repetitivo. O título da dissertação ("Ocultações Estelares em Curvas de Luz") já desambigua.
- Status: decisão autor+orientador (extensão da troca); a definição em si é aplicável direto.

### Geral e — parêntese seguido de citação, "(...) (Autor, ano)"
- Locais e trechos atuais (a varredura encontrou 7 casos de ")\citep" e mais 6 citações textuais escritas com \citep):
  1. introducao.tex:14 "estruturas periféricas (satélites, anéis) \citep{Cazeneuve2023};" → `estruturas periféricas, como satélites e anéis \citep{Ortiz2020, Sicardy2024};` (troca de referência explicada em t.i).
  2. capitulo2.tex:65 "O SORA (\textit{Stellar Occultation Reduction and Analysis}) \citep{SORA2022} é utilizado" → `O \textit{Stellar Occultation Reduction and Analysis} \citep[SORA,][]{SORA2022} é utilizado` (imprime "(SORA, Gomes-Júnior et al., 2022)", o formato pedido em Cap. 2 jj.iv).
  3. capitulo2.tex:77 "(perfis de temperatura e densidade em função da altitude) \citep{Sicardy2016};" → `, como perfis de temperatura e densidade em função da altitude \citep{Sicardy2016};`
  4. capitulo3.tex:56 (legenda) "(dados genéricos, não referentes a curvas de luz de ocultação) \citep{Levada2026}." → `Exemplo ilustrativo de regressão linear simples, com dados genéricos, não referentes a curvas de luz de ocultação. Fonte: \citet{Levada2026}.`
  5. capitulo3.tex:167 "(as \emph{dobras}, ou \textit{folds}, definidas na Seção~\ref{sec:validacao_modelos}) \citep{geron2019maos}." → `nas partições de validação \citep{geron2019maos}, as chamadas \emph{dobras} (\textit{folds}), definidas na Seção~\ref{sec:validacao_modelos}.`
  6. capitulo3.tex:198 "como profundidade máxima (\textit{max\_depth}) e número mínimo de amostras por nó ou por folha (\textit{min\_samples\_leaf}) \citep{geron2019maos}." → `como a profundidade máxima e o número mínimo de amostras por nó ou por folha \citep{geron2019maos} --- no \textit{scikit-learn}, os hiperparâmetros \texttt{max\_depth} e \texttt{min\_samples\_leaf}.`
  7. capitulo3.tex:373 "maior que o de investigar um alarme falso (FP) \citep{Saito2015}." → `maior que o de investigar um alarme falso, isto é, o custo de um FN supera o de um FP.` CONFLITO com a minha Rodada 1 (E19): \citet{Saito2015} não defende $\beta=2$. Retirar a citação daqui; ela continua justificada nas linhas 375 e 386.
  8. capitulo5.tex:301 "(geradas pelo simulador de Gomes-Ferrante \& Braga-Ribas~\citep{Simulator})" → `(geradas pelo simulador de \citealp{Simulator})`, que imprime "(geradas pelo simulador de Gomes-Ferrante & Braga-Ribas, 2023)". Hoje imprime os nomes duas vezes: "Gomes-Ferrante & Braga-Ribas (Gomes-Ferrante & Braga-Ribas, 2023)". O separador entre dois autores ("&", "e" ou ";", como pede a ABNT) segue os rótulos dos \bibitem — verificar norma (NBR 10520).
  9–11. capitulo4.tex:101, capitulo5.tex:15, capitulo5.tex:206: "Gomes-Ferrante \& Braga-Ribas~\citep{Simulator}" → `\citet{Simulator}` (imprime "Gomes-Ferrante & Braga-Ribas (2023)").
  12. capitulo2.tex:116 "descrito em \citep{Quaoar2023}" → `descrita por \citet{Quaoar2023}` (concordância com "descoberta"; o conteúdo é do item Cap. 2 nn).
  13. capitulo3.tex:75 "no capítulo 2 de \citep{Levada2026}" → `no Capítulo~2 de \citet{Levada2026}` (mesma linha do Geral a.4).
- Justificativa: com natbib (on.cls:57), \citet produz citação textual e \citep, parentética. "Parênteses duplos" e nomes duplicados são o efeito
  de usar \citep onde a NBR 10520 pede a forma "Autor (ano)" — verificar norma quanto à grafia dos sobrenomes (maiúsculas/minúsculas) na edição vigente.
- Status: aplicável direto.

### Geral g — "etc." ao final de listas de exemplos
- Locais, trechos atuais e propostas:
  - introducao.tex:24 "(nuvens, \textit{seeing})" → texto do item x.i (`(nuvens, \textit{seeing} ..., etc.)`).
  - introducao.tex:11 "(fotometria, espectroscopia, telescópios espaciais)" → `(fotometria, espectroscopia, radiometria térmica, etc.)`. "Telescópio espacial" não é método (texto no item o/q).
  - introducao.tex:32 "(estatísticas do fluxo, derivadas, testes entre quartis, distância entre centróides do K-means)" → acrescentar `, etc.` (item aa).
  - capitulo2.tex:65 "(objeto ocultante, data, observador, classificação positiva/negativa quando disponível)" → `(objeto ocultante, data, observador, classificação positiva/negativa quando disponível, etc.)`
  - capitulo4.tex:203 "(tamanho do objeto, velocidade)" → `(tamanho do objeto, velocidade da sombra, posição da corda, etc.)`
  - capitulo5.tex:711 "(interpretabilidade, velocidade de inferência, facilidade de implantação)" → `(interpretabilidade, velocidade de inferência, facilidade de implantação, etc.)`
  - capitulo6.tex:73 "(escala de Fresnel, opacidade parcial, diâmetro aparente da estrela)" → `(escala de Fresnel, opacidade parcial, diâmetro aparente da estrela, etc.)`
  - capitulo6.tex:75 "(baixo S/N, ocultações rasantes, eventos com poucos pontos no \textit{dip})" → `(baixo SNR, ocultações rasantes, eventos com poucos pontos na queda, etc.)`
  - Remissões: capitulo2.tex:57 "(extinção atmosférica, variações de transparência)" é o item Cap. 2 dd.ii; capitulo3.tex:34-35 ("Exemplos: ...") é o item Cap. 3 nº 3.
- Regra: só pôr "etc." em listas abertas. Listas exaustivas (os quatro modelos, as métricas, os componentes do simulador em capitulo4.tex:119)
  ficam como estão; listas já introduzidas por "por exemplo", "como" ou "e.g." dispensam o "etc." (redundância; a banca aceita "como ..., etc." em dd.ii — o autor decide).
- Justificativa: atende à banca e evita "etc." onde a lista é exaustiva.
- Status: aplicável direto.

### Geral h — acessibilidade para o leitor não especialista
- Local: teseon.tex:41-42 e :147-148 (listas de abreviaturas da classe, comentadas); introducao.tex:34 (promessa de linguagem acessível).
- Trecho atual: `%\makeloabbreviations` … `%\printloabbreviations`
- Proposta: incluir uma Lista de Abreviaturas e Siglas manual, depois de `\listoftables` (teseon.tex:146). É mais simples que `\abbrev`, que
  exige makeindex customizado no Overleaf:
```
\chapter*{Lista de Abreviaturas e Siglas}
\begin{description}
  \item[AUC-ROC] área sob a curva ROC (\textit{Area Under the Receiver Operating Characteristic Curve})
  \item[FN, FP, VN, VP] falso negativo, falso positivo, verdadeiro negativo, verdadeiro positivo
  \item[K-S] teste de Kolmogorov-Smirnov
  \item[MDI] queda média de impureza (\textit{Mean Decrease in Impurity})
  \item[ML] aprendizado de máquina (\textit{Machine Learning})
  \item[PRAIA] \textit{Platform for Reduction of Astronomical Images Automatically}
  \item[SNR] relação sinal-ruído (\textit{Signal-to-Noise Ratio})
  \item[SORA] \textit{Stellar Occultation Reduction and Analysis}
  \item[TNO] objeto transnetuniano (\textit{Trans-Neptunian Object})
  \item[UA] unidade astronômica
\end{description}
```
  Ajuste VP/VN conforme a decisão do item Cap. 3 nº 22 (TP/TN → VP/VN). Também é preciso unificar a sigla PRAIA: capitulo2.tex:65 diz
  "Package for the Reduction..." e teseon.tex:222 diz "Platform for Reduction...".
  Opcional: um Glossário pós-textual com os termos de ML mais frequentes (\textit{feature}, \textit{ensemble}, limiar, sobreajuste, validação cruzada).
- Justificativa: a banca pede "adaptação" de passagens específicas, que estão espalhadas pelos itens dos Caps. 2 a 5. Uma lista de siglas única é a
  ferramenta estrutural que mais ajuda quem lê a tese de forma não linear. Lista de abreviaturas (pré-textual) e glossário (pós-textual) são elementos opcionais da NBR 14724 — verificar norma.
- Status: decisão autor+orientador.

### Geral k — S/N × SNR: padronizar em SNR
- Locais (7 ocorrências de "S/N"; varredura completa):
  capitulo2.tex:92 (3x): "relação sinal-ruído (S/N) da curva", "S/N alto favorece", "curvas com S/N baixo";
  capitulo6.tex:60 (2x): "(alto S/N, queda pronunciada)", "Para curvas com baixo S/N ou eventos rasantes";
  capitulo6.tex:75 (2x): "\textbf{Detecção em regime de baixo S/N:}", "(baixo S/N, ocultações rasantes, ...)".
- Proposta: definir na primeira ocorrência (introducao.tex:24, texto do item x.iii): `relação sinal-ruído (do inglês, \textit{Signal-to-Noise Ratio}, SNR)`; depois:
  capitulo2.tex:92 → `relação sinal-ruído (SNR) da curva`, `SNR alto favorece`, `curvas com SNR baixo`;
  capitulo6.tex:60 → `(alto SNR, queda pronunciada)`, `baixo SNR`; capitulo6.tex:75 → `\textbf{Detecção em regime de baixo SNR:}`, `(baixo SNR, ...)`.
  As 13 ocorrências de "SNR" (capitulo4.tex:195, :197, :228; capitulo5.tex:77, :129, :488, :525; capitulo6.tex:18 (2x), :33, :73) já seguem o padrão.
- CONFLITO com as Rodadas 1 e 2: \texttt{Occ\_SNR\_dip} não é um SNR propriamente dito. O σ é estimado em meia distribuição (~0,60σ), e ruído
  puro dá "SNR" de ~6 (Feynman). Sugiro, em capitulo4.tex:195: `\textbf{Indicador de SNR da queda.} Neste trabalho, define-se um indicador da razão sinal-ruído da queda...`,
  com uma frase avisando que ele superestima o SNR real.
- Justificativa: atende à banca, e a sigla em inglês é a usual na literatura de ocultações.
- Status: aplicável direto (troca de sigla); decisão autor+orientador (renomear o indicador).

### Geral l — "sintéticas" → "simuladas" (curvas negativas do conjunto de ML)
- Locais e propostas (28 ocorrências em 22 linhas; varredura completa; não há ocorrências nos Caps. 2 e 3 nem nos apêndices):
  - introducao.tex:26 "em dados reais e sintéticos" → `em dados reais e simulados`
  - capitulo4.tex:7 "a incorporação de curvas sintéticas;" → `a incorporação de curvas simuladas;`
  - capitulo4.tex:19 "curvas sintéticas negativas são incorporadas" → `curvas negativas simuladas são incorporadas`
  - capitulo4.tex:45 "e às curvas sintéticas, totalizam" → `e às curvas simuladas, totalizam` (a reestruturação da frase é o item Cap. 4 nº 2)
  - capitulo4.tex:101 "geração de curvas sintéticas negativas com o simulador" → `geração de curvas negativas simuladas com o simulador`
  - capitulo4.tex:105 "curvas sintéticas, total de amostras" → `curvas simuladas, total de amostras`
  - capitulo4.tex:117 `\subsection{Curvas sintéticas negativas}` → `\subsection{Curvas negativas simuladas}`
  - capitulo4.tex:119 (2x) "\textbf{curvas de luz sintéticas}" → `\textbf{curvas de luz simuladas}`; "As curvas sintéticas são exportadas" → `As curvas simuladas são exportadas`
  - capitulo4.tex:121 (2x) "e curvas sintéticas negativas. Cabe" → `e curvas negativas simuladas. Cabe`; "(ii)~as curvas sintéticas, geradas" → `(ii)~as curvas simuladas, geradas`
  - capitulo4.tex:276 "e curvas sintéticas visa" → `e curvas simuladas visa`
  - capitulo5.tex:15 "702 curvas sintéticas negativas" → `702 curvas negativas simuladas`
  - capitulo5.tex:22 "(as sintéticas permanecem no treino)" → `(as simuladas permanecem no treino)`
  - capitulo5.tex:206 "\textbf{702 curvas sintéticas negativas}" → `\textbf{702 curvas negativas simuladas}`
  - capitulo5.tex:217 "Curvas sintéticas negativas (synthetic)" → `Curvas negativas simuladas (\texttt{synthetic})`
  - capitulo5.tex:301 (3x) "são \textbf{sintéticas}" → `são \textbf{simuladas}`; "mistura curvas reais e sintéticas" → `mistura curvas reais e simuladas`; "enquanto as curvas sintéticas são alocadas" → `enquanto as curvas simuladas são alocadas`
  - capitulo5.tex:326 e :576 "artefatos da distribuição sintética" → `artefatos da distribuição simulada`
  - capitulo5.tex:534 "mesmo treinado em curvas predominantemente sintéticas" → CONFLITO (R1 E13): o fato está errado — 41% do total e 0% das positivas.
    Proposta: `mesmo treinado com negativas majoritariamente simuladas (79\% das negativas)`.
  - capitulo5.tex:550 "sintéticas alocadas ao treino" → `simuladas alocadas ao treino`
  - capitulo6.tex:52 (3x) "\textbf{\textit{Dataset} parcialmente sintético:}" → `\textbf{Conjunto de dados parcialmente simulado:}`; "702 são sintéticas" → `702 são simuladas`;
    "Embora as curvas sintéticas tenham sido geradas com base em propriedades estatísticas de curvas reais" → CONFLITO (Feynman E19 / Simons E8): o simulador
    sorteia parâmetros uniformes em intervalos fixos. Proposta: `Embora as curvas simuladas incluam modelos de ruído fotométrico, seus parâmetros foram sorteados em intervalos fixos, e não ajustados às propriedades estatísticas das curvas reais;`
  - capitulo6.tex:71 "treinando apenas com curvas sintéticas e negativos por recorte" → `simuladas` + CONFLITO de lógica (R1 E25): esse treino não teria positivas. Ver Extras.
  - capitulo6.tex:79 "com apoio de curvas sintéticas geradas por simuladores" → `com apoio de curvas geradas por simuladores` ("simuladas geradas por simuladores" seria redundante)
- Justificativa: com isso, "sintética" fica reservada à curva-modelo ajustada às observações, que é o uso da área e o que a própria banca propõe nos itens Cap. 2 dd.vi e ll.
- Status: aplicável direto. Requerem confirmação do autor: capitulo5.tex:534 e capitulo6.tex:52.

### Geral n — falta de espaço depois de palavras entre aspas duplas
- Causa: on.cls:60 carrega `babel` com `brazil`, e nesse idioma o caractere " é um atalho ativo que absorve o espaço seguinte (diagnóstico do
  coordenador, confirmado pela banca no item Cap. 3 nº 1: "aprendem", "treinado", "caixa-preta"). O autor chegou a contornar o problema com `~`
  em alguns pontos ("positivo"~se), o que confirma a causa.
- Locais e propostas (25 pares em 17 linhas de capitulo3.tex, mais a epígrafe):
  - capitulo3.tex:13 "aprendem" → ``aprendem''; "treinado" → ``treinado''
  - capitulo3.tex:15 "caixa-preta" → ``caixa-preta''
  - capitulo3.tex:38 "ocultação presente" → ``ocultação presente''; "ausente" → ``ausente''
  - capitulo3.tex:45 "dimensionalidade'' (abre com " e fecha com '') → ``dimensionalidade''
  - capitulo3.tex:47 "positivo"~se → ``positivo'' se; "negativo"~caso → ``negativo'' caso; 'threshold' → \textit{threshold} (ou "limiar", item Cap. 3 nº 5)
  - capitulo3.tex:191 "nó"~ pergunta-se → ``nó'' pergunta-se; "o mínimo do fluxo suavizado é menor que 0,85?" → ``o mínimo do fluxo suavizado é menor que 0,85?''; "folha" → ``folha''
  - capitulo3.tex:220 "vota" → ``vota''; "fora da bolsa"~para → ``fora da bolsa'' para
  - capitulo3.tex:222 "votante" → ``votante''
  - capitulo3.tex:244 "fracos" → ``fracos''
  - capitulo3.tex:248 "resíduos" → ``resíduos''
  - capitulo3.tex:261 "oblivious" → \textit{oblivious} (termo em inglês; itálico em vez de aspas)
  - capitulo3.tex:278 "níveis" → ``níveis''; "fora da ocultação" → ``fora da ocultação''; "dentro da ocultação" → ``dentro da ocultação''
  - capitulo3.tex:318 "contas" → ``contas''
  - capitulo3.tex:352 "negativo" → ``negativo''
  - capitulo3.tex:393 "decora" → ``decora''
  - capitulo3.tex:408 "decore" → ``decore''
  - capitulo3.tex:450 "grade" → ``grade''
  - teseon.tex:123 (epígrafe) `\textit{"O primeiro princípio é que você não deve enganar a si mesmo - e você é a pessoa mais fácil de se enganar."}` →
    `\textit{``O primeiro princípio é que você não deve enganar a si mesmo --- e você é a pessoa mais fácil de enganar.''}`; e teseon.tex:125 `- Richard Feynman` → `--- Richard Feynman`.
- Problema vizinho (item Cap. 4 nº 18, outro revisor): as aspas simples dentro de \texttt saem curvas ('median', 'balanced', 'l2': capitulo4.tex:236,
  :253, :255; capitulo5.tex:737; apendice_hiperparametros.tex:11). Basta `\usepackage{upquote}` no preâmbulo (teseon.tex, depois de :13).
- Justificativa: ``…'' produz “…” e não interage com o babel.
- Status: aplicável direto.

### Geral o — motivação para estudar Centauros e TNOs (está breve)
- Local: introducao.tex:11-12 (o mesmo parágrafo dos itens q e r). Texto unificado no bloco Cap1 q.
- Proposta: ver o bloco q, que (1) abre com o "laboratório natural" na forma sugerida pela banca, (2) explica o papel de transição dos Centauros,
  (3) traz o que a técnica já revelou (anéis de Chariklo, Haumea e Quaoar, este último além do limite de Roche) e (4) corrige faixas de distância e tamanho.
  As novas referências estão no fim deste arquivo: Ortiz2020, Ortiz2017, Peixinho2020, Sicardy2024.
- Justificativa: a banca chama essa motivação de "a base que fundamenta todo o esforço". É também a lacuna narrativa principal que apontei na
  Rodada 1: a Introdução começa em dinâmica e formação, mas não diz por que esses corpos importam nem o que a técnica já revelou.
- Status: decisão autor+orientador (o enquadramento científico é do autor; as referências estão com metadados verificados).

### Geral p — o Apêndice C não é citado no texto
- Locais e trechos atuais: capitulo4.tex:270 "Os resultados numéricos e as figuras são a base da discussão do Capítulo 5."; capitulo6.tex:31
  "implementada em Python e disponível para reprodução."; nenhum \ref{ap:ambiente} no texto (verificado por grep).
- Proposta:
  1. capitulo4.tex:270, depois da frase: `O ambiente de software (versões do Python e das bibliotecas) necessário para reproduzir esse fluxo está documentado no Apêndice~\ref{ap:ambiente}.`
  2. capitulo6.tex:31: `implementada em Python, com o ambiente de software descrito no Apêndice~\ref{ap:ambiente} e o código disponível em \url{<URL>}.` (o item Cap. 6 iii pede o local do código)
  3. No próprio apêndice: apendice_ambiente.tex:26 "A data de geração do ambiente utilizado nos experimentos do Capítulo 5 deve ser registrada pelo autor ao finalizar a dissertação." → apagar e trocar por `Os experimentos do Capítulo~5 foram executados em <mês/ano>.`; apendice_ambiente.tex:11 "Python: 3.x (...)" → a versão exata.
     CONFLITO (Simons E14): as tabelas vieram de dois ambientes diferentes. Registrar os dois, ou rodar de novo num só.
- Justificativa: todo apêndice deve ser chamado no texto; um apêndice sem chamada parece um resto. Sobre a NBR 14724: verificar norma.
- Status: aplicável direto (chamadas 1 e 2). Requer confirmação do autor: URL do repositório (o remoto é github.com/TLaidler/Portfolio — confirmar se é público e se é o
  repositório que se quer citar), data e versões.

=====================================================================================================
## PARTE B — CAPÍTULO 1
=====================================================================================================

### Cap1 q — "laboratório natural": frase incompleta e ordem das ideias (unificado com o e r)
- Local: introducao.tex:11-12
- Trecho atual (início e fim): "Dentro desse panorama, o Sistema Solar Exterior surge como laboratório natural. Nele, destacam-se os \textbf{Centauros}, em órbitas instáveis entre Júpiter e Netuno, e os \textbf{Objetos Transnetunianos} (TNOs), além da órbita de Netuno. Esses corpos têm tamanhos típicos da ordem de centenas de quilômetros e distâncias de 15 a 100~UA do Sol; [...] passou a constituir uma técnica bastante relevante para a determinação de diâmetros e formas: \textbf{as ocultações estelares}."
- Proposta (substitui as linhas 11-12 inteiras; dois parágrafos):
```
Nesse contexto, o Sistema Solar exterior é a região menos processada pelo Sol desde a formação do sistema planetário e, portanto, um laboratório natural que preserva informações sobre as condições e os mecanismos primordiais \citep{Morbidelli2024, Tsiganis2009}. Nele se destacam os \textbf{Centauros} --- pequenos corpos com órbitas heliocêntricas instáveis entre Júpiter e Netuno, que fazem a transição entre a região transnetuniana e os cometas da família de Júpiter \citep{Peixinho2020} --- e os \textbf{Objetos Transnetunianos} (do inglês, \textit{Trans-Neptunian Objects}, TNOs), com órbitas além da de Netuno. A caracterização física desses corpos --- tamanho, forma, albedo, densidade e presença de atmosfera, anéis ou satélites --- é essencial para compreender a origem e a evolução dinâmica do nosso sistema planetário \citep{Ortiz2020}.

E esses corpos já surpreenderam. Ocultações estelares revelaram anéis em torno do Centauro (10199)~Chariklo \citep{BragaRibas2014}, do planeta anão (136108)~Haumea \citep{Ortiz2017} e de (50000)~Quaoar; neste último, um anel denso orbita muito além do limite de Roche, onde, pela teoria clássica, o material deveria ter se aglutinado em um satélite \citep{Morgado2023}. Medir esses objetos, porém, é difícil: seus tamanhos vão de dezenas a pouco mais de dois mil quilômetros, e suas distâncias ao Sol vão de cerca de 5~UA (Centauros mais internos) a dezenas ou mesmo centenas de UA (TNOs); a combinação de pequeno porte e grande distância resulta em baixo brilho aparente. Por muito tempo, propriedades físicas fundamentais só puderam ser estimadas por métodos indiretos (fotometria, espectroscopia, radiometria térmica, etc.), e a determinação de diâmetros dependia sobretudo de técnicas radiométricas baseadas em telescópios espaciais \citep{Fornasier2013}. No entanto, um tipo de observação feita a partir do solo, de custo relativamente baixo e acessível a telescópios modestos, tornou-se uma técnica de destaque para a determinação da forma e do tamanho de pequenos corpos do Sistema Solar: \textbf{as ocultações estelares}.
```
- Justificativa: segue a estrutura que a banca sugere ("por que é um laboratório natural?" → "por que é interessante?"). Três ajustes meus em relação ao texto da banca:
  (1) "menos processada pelo Sol" em vez de "sob menor influência do Sol desde sua formação", porque a própria Introdução (linha 9, Modelo de Nice) descreve
  essa região como dinamicamente reorganizada; o que se preservou foi o estado físico e químico dos corpos, não a configuração orbital;
  (2) a faixa "15 a 100 UA" excluía os Centauros internos, já que Júpiter está a ~5 UA (R1 E25);
  (3) sai "massa" da lista de propriedades, porque a ocultação não mede massa (que vem de satélites). Os casos de anéis respondem à banca (o)
  com fatos e preparam o leitor para o caso Quaoar do Cap. 5.
- Status: decisão autor+orientador (enquadramento científico); referências verificadas.

### Cap1 r — "diâmetros e formas" → "forma e tamanho de pequenos corpos"
- Local: introducao.tex:12
- Trecho atual: "passou a constituir uma técnica bastante relevante para a determinação de diâmetros e formas: \textbf{as ocultações estelares}."
- Proposta: `tornou-se uma técnica de destaque para a determinação da forma e do tamanho de pequenos corpos do Sistema Solar: \textbf{as ocultações estelares}.` (já incluída no bloco q)
- Justificativa: redação da banca.
- Status: aplicável direto.

### Cap1 s — espaço em branco excessivo entre os parágrafos 5 e 6 da Seção 1.1
- Local: preâmbulo, teseon.tex (depois da linha 21, `%\usepackage{parskip}`)
- Trecho atual: nenhum comando; on.cls:56 carrega `book` com `twoside`, que liga `\flushbottom`.
- Proposta: `\raggedbottom` (em linha própria no preâmbulo).
- Justificativa: com `\flushbottom`, o LaTeX estica a cola entre parágrafos para que todas as páginas terminem na mesma altura; em página com quebra
  difícil (antes de \section, com espaçamento 1,5), isso gera os vãos que a banca viu. `\raggedbottom` deixa o espaço que sobra no pé da página. Conferir visualmente
  depois de compilar: se o vão continuar, a causa é outra (por exemplo, um float).
- Status: aplicável direto.

### Cap1 t.i — referência geral sobre ocultações e "para um dado observador na Terra"
- Local: introducao.tex:14
- Trecho atual: "Ocultações estelares ocorrem quando um corpo do Sistema Solar passa diante de uma estrela distante, bloqueando temporariamente sua luz \citep{Knieling2024}. A técnica tornou-se uma das mais precisas para a determinação de dimensões e formas projetadas desses objetos, sendo superada nesse aspecto apenas por encontros diretos com sondas espaciais. A análise da \textbf{curva de luz} - a variação temporal do fluxo estelar - permite estimar a posição do objeto, inferir sua forma projetada e identificar estruturas periféricas (satélites, anéis) \citep{Cazeneuve2023}; sua versatilidade vai de asteroides próximos a TNOs extremamente distantes \citep{Fraser2024}. Ocultações são ainda empregadas há décadas no estudo de atmosferas planetárias \citep{Zhu2022}."
- Proposta (substitui a linha 14 inteira; incorpora t.ii, d, e):
```
Ocultações estelares ocorrem quando um corpo do Sistema Solar passa diante de uma estrela distante, bloqueando temporariamente sua luz para um dado observador na Terra \citep{Ortiz2020, Knieling2024}. A análise da \textbf{curva de luz de ocultação} --- a variação temporal do fluxo da estrela registrada durante o evento, que não deve ser confundida com as curvas de luz rotacionais usadas para determinar períodos de rotação --- permite estimar a posição do objeto, inferir sua forma projetada e identificar estruturas periféricas, como satélites e anéis \citep{Ortiz2020, Sicardy2024}; sua versatilidade vai de asteroides próximos \citep{Herald2020} a TNOs muito distantes \citep{Sicardy2024}. A técnica tornou-se uma das mais precisas para a determinação de dimensões e formas projetadas desses objetos, sendo superada nesse aspecto apenas por encontros diretos com sondas espaciais. Ocultações são ainda empregadas há décadas no estudo de atmosferas planetárias \citep{ElliotOlkin1996, Sicardy2016} --- e foi assim, de modo inesperado, que se descobriram os anéis de Urano, em 1977 \citep{Elliot1977}.
```
- Justificativa: atende a t.i (Ortiz et al. 2020; o referencial do observador). Ponho "para um dado observador na Terra" ANTES da citação para que ela feche a frase.
  Troco três citações que não sustentam as frases (minha R1 E19): Fraser2024 é um levantamento de TNOs por *shift-and-stack*, não trata de ocultação;
  Zhu2022 trata da sondagem da atmosfera TERRESTRE por satélites; Cazeneuve2023 é o artigo do ODNet, não uma referência sobre a física do fenômeno.
  Zhu2022 deixa de ser citado: remover o \bibitem (teseon.tex:239), porque toda referência listada precisa ser citada (NBR 6023/10520 — verificar norma).
  A oração sobre Urano é opcional (Sagan): é o arquétipo de "sinal sutil achado sem procurar", e prepara a motivação da tese.
- Status: aplicável direto (oração de Urano opcional; decisão do autor).

### Cap1 t.ii — mover "A técnica ... espaciais." para antes de "Ocultações são ainda ..."
- Local: introducao.tex:14
- Trecho atual: "A técnica tornou-se uma das mais precisas para a determinação de dimensões e formas projetadas desses objetos, sendo superada nesse aspecto apenas por encontros diretos com sondas espaciais."
- Proposta: já aplicada no texto do bloco t.i (a frase passa a ser a penúltima do parágrafo).
- Justificativa: redação da banca; a precisão fica sendo a conclusão do que a curva de luz permite medir.
- Status: aplicável direto.

### Cap1 u — por que o volume de dados cresceu; ODNet = Cazeneuve et al. (2023)
- Local: introducao.tex:16
- Trechos atuais: "O crescimento do volume de dados gerados por campanhas observacionais, porém, tem tornado a identificação manual dos eventos uma tarefa custosa, impulsionando a adoção de métodos computacionais, em particular técnicas de \textbf{aprendizado de máquina} (\textit{Machine Learning}, ML)." e "redes neurais convolucionais (como o ODNet) analisam séries temporais ou imagens [...]; em buscas por TNOs em campos densos, redes residuais fazem triagem dos candidatos gerados por técnicas de empilhamento e deslocamento (\textit{shift-and-stack}), reduzindo detecções espúrias \citep{Fraser2024}."
- Proposta:
  1. Primeira frase → `Esse sucesso tem um preço. O volume de dados gerados por campanhas observacionais cresceu muito, impulsionado (i) pela precisão astrométrica dos catálogos do satélite Gaia \citep{Gaia2016, GaiaDR3}, que tornou as previsões de ocultação muito mais confiáveis, e (ii) pelo barateamento de câmeras astronômicas rápidas e sensíveis, que popularizou esse tipo de observação entre astrônomos amadores e redes de ciência cidadã. Com isso, a identificação manual dos eventos tornou-se uma tarefa custosa, o que impulsiona a adoção de métodos computacionais, em particular de técnicas de \textbf{aprendizado de máquina} (do inglês, \textit{Machine Learning}, ML).`
  2. "redes neurais convolucionais (como o ODNet)" → `redes neurais convolucionais \citep[como a ODNet,][]{Cazeneuve2023}` (imprime "(como a ODNet, Cazeneuve et al., 2023)", que é a forma pedida pela banca).
  3. "em buscas por TNOs em campos densos, redes residuais" → `em um problema correlato --- a busca por novos TNOs em campos estelares densos ---, redes residuais`
- Justificativa: a banca pede os dois motivos do crescimento. O Gaia entra com referência própria; a mesma entrada atende ao item Cap. 2 cc.iv.
  O ajuste 3 deixa claro que o trabalho de Fraser não é de ocultação (R1).
- Status: aplicável direto (Gaia2016 e GaiaDR3 com metadados verificados).

### Cap1 v — período de crescimento dos dados com referência; "requerem atenção imediata"
- Local: introducao.tex:20
- Trecho atual: "O avanço instrumental e a multiplicação de redes de observação (incluindo ciência cidadã) expandiram fortemente o volume de dados de ocultações. [...] O desafio central é identificar rapidamente, nesse volume massivo, quais curvas de luz exibem um evento positivo."
- Proposta: `O avanço instrumental e a multiplicação de redes de observação (incluindo ciência cidadã) expandiram fortemente o volume de dados de ocultações coletados nos últimos $\sim$X anos \citep{Herald2020, Sicardy2024}.` … `O desafio central é identificar rapidamente, nesse grande volume, quais curvas de luz de ocultação exibem um evento positivo e, portanto, requerem atenção imediata.`
- Justificativa: redação da banca. Herald et al. (2020) descrevem um conjunto que já passa de 5000 ocultações por asteroides observadas e está em
  crescimento — é, aliás, o artigo que descreve a origem do catálogo usado na tese; Sicardy et al. (2024) fazem a revisão para TNOs. "Volume massivo" →
  "grande volume", porque a tese trabalha com 1693 curvas (tom Sagan).
- Status: requer confirmação do autor (o valor de X e a frase de Herald/Sicardy que o sustenta; sugestão: "desde a publicação do Gaia DR2, em 2018").

### Cap1 w — "queda" → "queda de fluxo"; "associada à detecção do corpo principal"
- Local: introducao.tex:22
- Trecho atual: "Detectar a queda profunda associada ao \textbf{corpo principal} do ocultante é o requisito mínimo"
- Proposta: `Detectar a queda de fluxo profunda associada à detecção do \textbf{corpo principal} é o requisito mínimo`
- Justificativa: redação da banca. No mesmo parágrafo há duas pendências: a atribuição dos anéis de Quaoar (Q1R → Morgado2023) é o item Geral f (outro revisor), e o
  "Esta dissertação demonstra [...] justamente essa capacidade" conflita com as Rodadas 1 e 2 (ver Extras, item 2).
- Status: aplicável direto.

### Cap1 x.i — primeira frase com 6 linhas: trocar o ponto e vírgula por ponto
- Local: introducao.tex:24 (a banca escreve "parágrafo 2", mas é o parágrafo 3 da Seção 1.2)
- Trecho atual: "A tarefa é complexa: ruídos observacionais e variabilidades atmosféricas (nuvens, \textit{seeing}) podem produzir quedas ou picos espúrios que mimetizam uma ocultação \citep{Cazeneuve2023, Knieling2024}; observações frequentemente operam no limite instrumental, exigindo definições cuidadosas de detecção e critérios estatísticos para não confundir excursões de ruído com sinal; em buscas por TNOs em regiões densas, sinais podem ser artefatos da subtração de estrelas fixas \citep{Fraser2024}."
- Proposta:
```
A tarefa é complexa. Ruídos observacionais e variabilidades atmosféricas (nuvens, \textit{seeing} --- o borramento da imagem estelar causado pela turbulência atmosférica ---, etc.) podem produzir quedas ou picos espúrios que imitam uma ocultação \citep{Cazeneuve2023, Knieling2024}. Além disso, as observações frequentemente operam no limite instrumental, o que exige definições cuidadosas de detecção e critérios estatísticos para não confundir excursões de ruído com sinal; em buscas por TNOs em regiões densas, sinais podem ainda ser artefatos da subtração de estrelas fixas \citep{Fraser2024}.
```
- Justificativa: atende a x.i, g ("etc.") e c (explicação de *seeing* para o leitor não especialista).
- Status: aplicável direto.

### Cap1 x.ii — novo parágrafo a partir de "A detecção ..."
- Local: introducao.tex:24
- Trecho atual: "A detecção rápida, precisa e escalável tornou-se um gargalo no fluxo de trabalho científico. Métodos que dispensam ML, por exemplo, janelas de suavização, podem ser limitados [...] \citep{Deisenroth2019, Fraser2024, CarleoMLPhysSci}, e se apresentam como caminho natural para os desafios de escalabilidade e precisão na era do \textit{big data} em astronomia \citep{Cazeneuve2023}."
- Proposta (novo parágrafo, logo depois do texto do bloco x.i):
```
A detecção rápida, precisa e escalável tornou-se, assim, um gargalo no fluxo de trabalho científico. Métodos que dispensam ML, como janelas de suavização, podem ser limitados em determinados regimes: a suavização tende a mascarar eventos muito rápidos (com tempos de ingresso e egresso menores que a janela escolhida), e o desempenho em estrelas com baixa relação sinal-ruído (do inglês, \textit{Signal-to-Noise Ratio}, SNR) depende fortemente da experiência do analista. Nesses casos, o sinal pode ser facilmente confundido com flutuações de ruído. Técnicas de ML surgem como alternativa: redes neurais e modelos de regressão modernos (como os processos gaussianos) já são usados para filtrar candidatos, reconstruir dados e apoiar levantamentos \citep{Knieling2024, Fraser2024, CarleoMLPhysSci}, e apresentam-se como caminho natural para os desafios de escalabilidade e precisão na era do grande volume de dados (\textit{big data}) em astronomia \citep{Cazeneuve2023}.
```
- Justificativa: atende a x.ii e x.iii. Troco Deisenroth2019 (livro de matemática, que não sustenta "já são usados") por Knieling2024 (processos gaussianos aplicados
  a ocultações), conforme a R1 E19; Deisenroth continua citado em :16 e no Cap. 3.
  CONFLITO de coerência (R1 E21; Feynman E14): a própria *pipeline* usa janelas de suavização de até N/3 pontos (capitulo4.tex:149). A crítica feita aqui exige uma
  frase de reconhecimento no Cap. 4, por exemplo: "Note-se que a própria \textit{pipeline} suaviza as curvas; a escolha da janela é discutida como limitação no Capítulo~6."
- Status: aplicável direto (texto); decisão autor+orientador (frase de reconhecimento no Cap. 4).

### Cap1 x.iii — "estrelas de baixo brilho ..." → "estrelas com baixo sinal-ruído (SNR)"
- Local: introducao.tex:24
- Trecho atual: "o desempenho em estrelas de baixo brilho aparente para o telescópio em uso depende fortemente da experiência do analista"
- Proposta: `o desempenho em estrelas com baixa relação sinal-ruído (do inglês, \textit{Signal-to-Noise Ratio}, SNR) depende fortemente da experiência do analista` (já incluído em x.ii)
- Justificativa: redação da banca. É também a primeira ocorrência da sigla SNR (ver Geral k).
- Status: aplicável direto.

### Cap1 y — negrito também em "reprodutibilidade" e "facilidade"
- Local: introducao.tex:28
- Trecho atual: "As razões são a \textbf{interpretabilidade}: é possível verificar quais grandezas (features) mais influenciam a decisão do modelo, o que é valioso para análise científica; a reprodutibilidade com volumes de dados moderados; e a facilidade de integração em fluxos já existentes."
- Proposta: `As razões são três: a \textbf{interpretabilidade} --- é possível verificar quais grandezas (\textit{features}) mais influenciam a decisão do modelo, o que é valioso para a análise científica ---, a \textbf{reprodutibilidade} com volumes de dados moderados e a \textbf{facilidade} de integração a \textit{pipelines} de análise já existentes.`
- Justificativa: redação da banca (y). Resolve também o itálico de "features" (c) e o "fluxos" no sentido de *workflow* (mesmo problema do item aa).
- Status: aplicável direto.

### Cap1 z — "a bordo de telescópios"
- Local: introducao.tex:30
- Trecho atual: "visando superar limitações atuais de precisão e velocidade e, no futuro, permitir implementações em tempo real a bordo de telescópios."
- Proposta (se a intenção são telescópios em solo): `visando superar limitações atuais de velocidade na triagem e, no futuro, permitir a classificação em tempo real, integrada aos sistemas de aquisição de dados dos telescópios.`
  Se a intenção são telescópios espaciais: `..., em tempo real, a bordo de telescópios espaciais.`
- Justificativa: "a bordo" só se usa para veículos e satélites (banca). Retiro "precisão": a tese não mostra precisão superior à de outros métodos (R1 E5; consistência com Extras, item 3).
- Status: requer confirmação do autor (qual era a intenção).

### Cap1 aa — "fluxo" no sentido de fluxo de trabalho
- Local: introducao.tex:32
- Trecho atual: "usando um fluxo baseado em características clássicas (estatísticas do fluxo, derivadas, testes entre quartis, distância entre centróides do K-means) e em \textbf{ensembles} de árvores"
- Proposta mínima (atende à banca): `usando uma \textit{pipeline} baseada em características clássicas (estatísticas do fluxo, derivadas, testes entre quartis, distância entre centróides do K-means, etc.) e em \textbf{\textit{ensembles}} de árvores`
- Varredura do mesmo problema ("fluxo" com sentido de *workflow*, em que o leitor pode entender fluxo luminoso):
  introducao.tex:28 (resolvido em y); capitulo2.tex:24 e :53 (legenda) "fluxo observacional" → `cadeia observacional`; capitulo2.tex:67 (2x) "o fluxo aqui descrito",
  "o fluxo de aquisição" → `o processo aqui descrito`, `o procedimento de aquisição`; capitulo3.tex:38 "no fluxo da \textit{pipeline}" → `nas etapas da \textit{pipeline}`;
  capitulo4.tex:13 "ilustra o fluxo desde as fontes" → `ilustra o encadeamento das etapas desde as fontes`; capitulo4.tex:67 "o fluxo de consolidação" → `o processo de consolidação`;
  capitulo4.tex:268 (\subsection{Fluxo de treinamento e persistência}) e :270 → `Etapas de treinamento e persistência` / `As etapas de treinamento são`; capitulo5.tex:462 "O fluxo é:" → `As etapas são:`.
  Podem ficar "fluxo de trabalho" (introducao.tex:24, :26) e "fluxograma" (capitulo3.tex:191), porque são explícitos.
- CONFLITO com as Rodadas 1 e 2: a mesma frase formula uma hipótese (desempenho "superior ou comparável" a CNNs e à inspeção manual) que não foi testada,
  e capitulo6.tex:23 a declara "corroborada". Ver Extras, item 3.
- Justificativa: a banca aponta a ambiguidade, e na mesma frase "fluxo" aparece nos dois sentidos.
- Status: aplicável direto (troca de palavra); decisão autor+orientador (reformular a hipótese).

=====================================================================================================
## REFERÊNCIAS NOVAS (\bibitem no formato já usado em teseon.tex)
=====================================================================================================
Inserir em ordem alfabética. A lista atual não está em ordem alfabética, o que o sistema autor-data da ABNT exige — verificar norma (NBR 6023).

\bibitem[Ortiz et al. (2020)]{Ortiz2020} ORTIZ, J. L.; SICARDY, B.; CAMARGO, J. I. B.; SANTOS-SANZ, P.; BRAGA-RIBAS, F. ``Stellar occultations by trans-Neptunian objects: from predictions to observations and prospects for the future''. In: PRIALNIK, D.; BARUCCI, M. A.; YOUNG, L. A. (ed.). \emph{The Trans-Neptunian Solar System}. Amsterdam: Elsevier, 2020. p. 413--437. \url{https://doi.org/10.1016/B978-0-12-816490-7.00019-9}.
  → Metadados verificados (título, livro, páginas 413–437, DOI). A verificar: o 5º autor (Braga-Ribas consta no arXiv:1905.04335) e o nome dos editores. O orientador é coautor.

\bibitem[Sicardy et al. (2024)]{Sicardy2024} SICARDY, B.; BRAGA-RIBAS, F.; BUIE, M. W.; ORTIZ, J. L.; ROQUES, F. ``Stellar occultations by trans-Neptunian objects''. \emph{The Astronomy and Astrophysics Review}, 32, 6, 2024. \url{https://doi.org/10.1007/s00159-024-00156-x}.
  → Metadados verificados.

\bibitem[Herald et al. (2020)]{Herald2020} HERALD, D.; GAULT, D.; ANDERSON, R.; DUNHAM, D.; FRAPPA, E.; HAYAMIZU, T.; KERR, S.; MIYASHITA, K.; MOORE, J.; PAVLOV, H.; PRESTON, S.; TALBOT, J.; TIMERSON, B. ``Precise astrometry and diameters of asteroids from occultations -- a data set of observations and their interpretation''. \emph{Monthly Notices of the Royal Astronomical Society}, 499(3), 4570--4590, 2020. \url{https://doi.org/10.1093/mnras/staa3077}.
  → Metadados verificados (13 autores, volume, páginas, DOI).

\bibitem[Gaia Collaboration et al. (2016)]{Gaia2016} GAIA COLLABORATION; PRUSTI, T.; DE BRUIJNE, J. H. J.; et al. ``The Gaia mission''. \emph{Astronomy \& Astrophysics}, 595, A1, 2016. \url{https://doi.org/10.1051/0004-6361/201629272}.
  → Metadados verificados.

\bibitem[Gaia Collaboration et al. (2023)]{GaiaDR3} GAIA COLLABORATION; VALLENARI, A.; BROWN, A. G. A.; PRUSTI, T.; et al. ``Gaia Data Release 3: summary of the content and survey properties''. \emph{Astronomy \& Astrophysics}, 674, A1, 2023. \url{https://doi.org/10.1051/0004-6361/202243940}.
  → Metadados verificados (A&A 674, A1; DOI). A verificar: a ordem dos coautores depois de Vallenari.

\bibitem[Ortiz et al. (2017)]{Ortiz2017} ORTIZ, J. L.; SANTOS-SANZ, P.; SICARDY, B.; et al. ``The size, shape, density and ring of the dwarf planet Haumea from a stellar occultation''. \emph{Nature}, 550(7675), 219--223, 2017. \url{https://doi.org/10.1038/nature24051}.
  → Metadados verificados (volume, páginas, DOI). A verificar: o número do fascículo (7675).

\bibitem[Peixinho et al. (2020)]{Peixinho2020} PEIXINHO, N.; THIROUIN, A.; TEGLER, S. C.; DI SISTO, R. P.; DELSANTI, A.; GUILBERT-LEPOUTRE, A.; BAUER, J. G. ``From Centaurs to comets: 40 years''. In: PRIALNIK, D.; BARUCCI, M. A.; YOUNG, L. A. (ed.). \emph{The Trans-Neptunian Solar System}. Amsterdam: Elsevier, 2020. p. 307--329. \url{https://doi.org/10.1016/B978-0-12-816490-7.00014-X}.
  → Metadados verificados.

\bibitem[Elliot \& Olkin (1996)]{ElliotOlkin1996} ELLIOT, J. L.; OLKIN, C. B. ``Probing planetary atmospheres with stellar occultations''. \emph{Annual Review of Earth and Planetary Sciences}, 24, 89--123, 1996. \url{https://doi.org/10.1146/annurev.earth.24.1.89}.
  → Metadados verificados.

\bibitem[Elliot et al. (1977)]{Elliot1977} ELLIOT, J. L.; DUNHAM, E.; MINK, D. ``The rings of Uranus''. \emph{Nature}, 267, 328--330, 1977. \url{https://doi.org/10.1038/267328a0}.
  → Metadados verificados. Só é necessário se a oração opcional do bloco t.i for mantida.

Remover: \bibitem{Zhu2022} (teseon.tex:239) deixa de ser citado depois do bloco t.i.

=====================================================================================================
## EXTRAS QUE A BANCA NÃO PEDIU MAS SÃO OBRIGATÓRIOS (comunicação e narrativa; das Rodadas 1–2)
=====================================================================================================
1. Resumo, frase de Quaoar (teseon.tex:136, de "Como validação em dados reais..." até "...ainda não identificados numa primeira análise.") → versão honesta:
   `Como ilustração exploratória, aplicou-se a ferramenta a uma curva da ocultação por (50000) Quaoar externa ao treino: o corpo principal e o anel Q1R são detectados no limiar padrão, enquanto os cruzamentos do anel fino Q2R recebem probabilidades baixas (4--8\% no XGBoost), ainda que superiores às de uma janela de ruído vizinha; um limiar reduzido, escolhido a posteriori, os recupera, mas a taxa de falsos alarmes desse regime ainda precisa ser medida.`
   O "sem introduzir falsos alarmes" atual é refutado pelos próprios dados: com τ=0,03 há 10–16% de falsos positivos em negativas reais (Simons), e o Q2R₂ com
   janela ampliada cai para 0,029, abaixo do limiar (capitulo5.tex:525). O resumo em inglês (teseon.tex:141) precisa espelhar a mudança.
2. introducao.tex:22 "Esta dissertação demonstra, entre seus resultados, justamente essa capacidade aplicada a uma curva real de Quaoar" → `Esta dissertação ilustra essa capacidade, ainda de forma exploratória, numa curva real de Quaoar`.
3. Hipótese (introducao.tex:32 e capitulo6.tex:23 "é \textbf{corroborada}"). Não houve comparação com CNN nem com inspeção humana. Reformular para:
   `A hipótese de pesquisa é a de que características clássicas extraídas das curvas, combinadas a \textit{ensembles} de árvores, bastam para separar com alto desempenho e de forma interpretável curvas com e sem ocultação; a comparação direta com redes convolucionais e com a inspeção humana, no mesmo conjunto de dados, fica como perspectiva.`
   No Cap. 6: `é sustentada no regime de ocultações profundas que domina o conjunto de dados; o regime de sinais sutis permanece em aberto.`
4. Cap. 6, abertura e tom (capitulo6.tex:6): abrir com a "espinha" do roteiro oral — `O que se construiu não é um juiz; é uma fila de prioridade para os olhos humanos.` — e organizar em três camadas: demonstrado / ilustrado (Quaoar) / em aberto.
5. Fechar o círculo científico no Cap. 6: um parágrafo final que retome Centauros, TNOs e anéis (bloco q). O anel de Quaoar além do limite de Roche só
   foi visto porque alguém revisitou os dados \citep{Morgado2023}; a ferramenta é um passo, ainda curto, para que o próximo não fique esquecido no arquivo.
6. Pôr a régua ao lado da floresta (Cap. 5): reportar o desempenho de um limiar único em uma *feature* de profundidade (F1 ~0,90–0,95, segundo as reanálises da
   sessão anterior e de Simons) junto aos ensembles (~0,99). Isso mostra que o ML se paga e, ao mesmo tempo, que a tarefa avaliada é a das quedas profundas. Requer rodar e confirmar os números.
7. "Importância ≠ insubstituibilidade" (capitulo5.tex:270; apendice_experimentos.tex:123): trocar "redistribuída ... sobretudo para Feature\_Savgol\_std" (falso no Exp. 6)
   pela cadeia verificada: Savgol\_Min 0,58 (13 *features*) → kmeans 0,69 (sem Savgol\_Min) → Savgol\_Min 0,64 (sem kmeans) → Savgol\_std 0,57 (sem os dois), com F1 estável.
   A lição continua de pé e fica mais clara. Isso depende da correção das contagens de *features* (Exp. 4 = 13, Exp. 5 = 12), que é o item Cap. 5 nº 1.
8. capitulo5.tex:654: apagar a afirmação falsa "todos os segmentos recortados de uma mesma curva ficam na mesma dobra" e declarar o vazamento com número:
   `cerca de metade das negativas reais de teste (18--21 de 38, conforme a partição) tem o recorte-irmão no treino`. O real holdout de capitulo6.tex:71, que não teria positivas, precisa ser reformulado.

---

# PARTE B — Revisor Feynman: Gerais f, j, m; Capítulos 2 e 4


Escopo: comentários gerais **f**, **j** (só a parte textual) e **m**; **Capítulo 2** inteiro (bb–nn); **Capítulo 4**
inteiro (1–19). Ficaram de fora, por instrução, as fontes e o texto dentro das imagens, a decisão sobre a Fig. 2.1, a
fusão das Figs. 2.3/2.4 e os marcadores de imersão/emersão.

Verificação: todo "Trecho atual" foi conferido por busca exata no .tex (scratchpad/chk_snips.py). Cada trecho ocorre
exatamente 1 vez, na linha indicada. As respostas factuais vêm do código e do banco em ROOT\pipeline; quando não há
evidência, o item está marcado "requer confirmação do autor".
Convenções: as citações novas usam as chaves definidas em "Referências novas", no fim. A notação segue a proposta do
item **Geral m** (L_F, Δ, φ etc.). Se o autor não adotar a notação nova, basta manter os símbolos antigos nos trechos.

---------------------------------------------------------------------
## COMENTÁRIOS GERAIS
---------------------------------------------------------------------

### Geral f — citar Morgado et al. (2023) junto de Pereira et al. (2023)
- **Local 1:** introducao.tex:22
- **Trecho atual:** `O exemplo emblemático é a descoberta dos anéis do objeto transnetuniano (50000) Quaoar, identificados apenas após uma \textbf{revisita} cuidadosa dos dados de ocultação pelo próprio autor da análise \citep{Quaoar2023}.`
- **Proposta:**
```latex
O exemplo emblemático são os anéis do objeto transnetuniano (50000) Quaoar. O primeiro anel (Q1R), denso e situado muito além do limite de Roche, foi identificado a partir de uma \textbf{revisita} a dados de ocultações anteriores, motivada por uma observação nova \citep{Morgado2023}; o segundo anel (Q2R), mais tênue, foi descoberto em ocultações posteriores \citep{Quaoar2023}.
```
- **Local 2:** capitulo5.tex:29. Trecho atual: `pelo objeto transnetuniano (50000) Quaoar~\citep{Quaoar2023}`. Proposta: `pelo objeto transnetuniano (50000) Quaoar~\citep{Morgado2023, Quaoar2023}`
- **Local 3:** capitulo5.tex:339. Trecho atual: `(como ilustra a própria história dos anéis de Quaoar, revelados só numa revisita dos dados)`. Proposta: `(como ilustra a história do primeiro anel de Quaoar, revelado numa revisita de dados antigos \citep{Morgado2023})`
- **Local 4:** capitulo5.tex:478 (legenda). Trecho atual: `são as assinaturas dos dois anéis denominados Q1R e Q2R em~\citep{Quaoar2023}`. Proposta: `são as assinaturas dos dois anéis, Q1R \citep{Morgado2023} e Q2R \citep{Quaoar2023}`
- **Local 5:** capitulo2.tex:116, tratado no item **Cap2 nn**. (capitulo5.tex:449 já cita os dois.)
- **Justificativa:** Q1R está em Morgado et al. (2023) e Q2R em Pereira et al. (2023). "Pelo próprio autor da análise" não
  tem como ser verificado e deve sair.
- **Status:** aplicável direto. Os detalhes da revisita (quais dados e qual observação nova) requerem confirmação do autor
  em Morgado et al. (2023).

### Geral j — transição Chariklo → Umbriel (somente texto)
- **Local:** capitulo2.tex:15 (frase da Fig. 2.1) e capitulo2.tex:24 (frase da Fig. 2.2)
- **Trecho atual (24):** `A Figura~\ref{fig:umbriel_painel} reúne um exemplo completo desse fluxo observacional --- do mapa de previsão da sombra e do posicionamento dos observadores aos quadros CCD e à curva de luz reduzida --- para a ocultação por Umbriel (satélite de Urano) em 2020.`
- **Proposta:** acrescentar ao fim do parágrafo da linha 15 (depois da frase da Fig. 2.1):
```latex
Chariklo serve aqui apenas como ilustração do fenômeno. Nas demais figuras deste capítulo adota-se como exemplo a ocultação por Umbriel, satélite de Urano, de 21 de setembro de 2020 \citep{Umbriel2020}: além de ser um caso bem documentado, as curvas de luz dessa campanha fazem parte do banco de dados utilizado nesta dissertação (Capítulo~4).
```
  e trocar a frase da linha 24 por:
```latex
A Figura~\ref{fig:umbriel_painel} percorre, para essa ocultação por Umbriel, o fluxo observacional completo --- do mapa de previsão da sombra e do posicionamento dos observadores aos quadros CCD e à curva de luz de ocultação reduzida.
```
- **Justificativa:** diz ao leitor por que o exemplo muda e qual é o papel de Umbriel: seus dados são usados, os de
  Chariklo não.
- **Status:** aplicável direto. Manter ou não a Fig. 2.1 é decisão do autor (fora do escopo).

### Geral m — símbolos reutilizados com sentidos diferentes: inventário e notação única
Inventário completo, conferido por grep nos .tex:

| Símbolo | Sentidos atuais (arquivo:linha) | Proposta única |
|---|---|---|
| **f** | escala de Fresnel (capitulo2.tex:77, 88, 90); classificador f: R^d→{0,1} (capitulo3.tex:38, 47, 49); "função verdadeira" f(x) e estimador \hat f (capitulo3.tex:397, 400); vetor de fluxo f, \tilde f, f′, f″ (capitulo5.tex:49–90) | escala de Fresnel **L_F**; classificador **g** (e \hat g no viés–variância); fluxo normalizado **φ**, \tilde φ, φ′, φ″ |
| **F** | fluxo F(t_i), F_i, F_min, F_max (capitulo4.tex:133–145, 209, 215); modelo de boosting F_m (capitulo3.tex:246); F_1, F_β, F_2 (capitulo3.tex:364–373; capitulo5.tex:374–378) | fluxo **φ_i** (normalizado) e **Φ** (absoluto, Cap. 2); boosting **\hat y^{(m)}**; F_1/F_β/F_2 só como nome de métrica |
| **σ** | sigmoide (capitulo3.tex:109, 125, 150, 179, 184); variância do ruído irredutível σ² (capitulo3.tex:397, 400); desvio padrão do fluxo (capitulo4.tex:137, 145); σ_baseline, std só dos pontos ≥ mediana (capitulo4.tex:193, 197); MAD (capitulo4.tex:209–215); σ(·) nas tabelas (capitulo5.tex:50–80) | sigmoide **𝒮(z)**; **σ_ε²** (ruído irredutível); **σ_φ** (std do fluxo); **σ_base** (std dos pontos ≥ mediana); **s_MAD** (MAD); manter σ(·) nas tabelas só com subscrito |
| **μ** | centróide \vec μ_i (capitulo3.tex:274, 276); média do fluxo (capitulo4.tex:136–137); μ = baseline = mediana (capitulo4.tex:209, 211) | centróides **\vec μ_j**; média **\bar φ**; baseline **φ_base** |
| **k / K** | classe k e regiões R_k (capitulo3.tex:49, 191–194); nº de grupos do K-means k (capitulo3.tex:272–276) e "K=2"/"k=2" no MESMO parágrafo (capitulo3.tex:278); nº de dobras k, k=5 (capitulo3.tex:431, 436, 448; capitulo5.tex:652) | classe **c ∈ {1,…,n_c}**; K-means **K** (sempre maiúsculo) e grupo **j**; dobras **Q** (= 5), mantendo o nome "\textit{k-fold}" |
| **c** | nº de classes (capitulo3.tex:47, 191–194); contagem c do McNemar (capitulo5.tex:682–693); custos c_FN, c_FP (capitulo5.tex:379) | classe c / n_c como acima; McNemar **n_01, n_10** (notação usual de pares discordantes); custos **κ_FN, κ_FP** |
| **m / n** | nº de exemplos m (capitulo3.tex:117–131, "m=4"); nº de exemplos n (capitulo3.tex:45, 63); iteração m do boosting (capitulo3.tex:244–248) | **n** = nº de exemplos em todo lugar; **m** só para a iteração do boosting |
| **D / d** | D = distância (capitulo2.tex:77, 86–88), e a tese fala de diâmetros; d = dimensão (capitulo3.tex:45, 47) | distância observador–corpo **Δ** (notação das efemérides; o próprio mapa da Fig. 2.2a usa "Delta"); **d** = nº de características |
| **p** | probabilidade p, \hat p (capitulo3.tex:116–119); proporções p_{i,k} (capitulo3.tex:191–194); p-valor (capitulo4.tex:179; capitulo5.tex:686); nº de features p (capitulo5.tex:172); O(p³) (capitulo3.tex:298) | **\hat p** = probabilidade; **π_{i,c}** = proporções; **p** = p-valor; **d** em capitulo5.tex:172 e O(d³) |
| **α** | intercepto da regressão (capitulo3.tex:61–65); força da regularização (capitulo3.tex:158–167) | regressão com **θ_0, θ_1**; α só para regularização |
| **β** | coeficientes da regressão linear (capitulo3.tex:51, 61–65); F_β (capitulo3.tex:369–373; capitulo5.tex:374–378); coeficientes β_j da RL (capitulo5.tex:169–175), que o Cap. 3 chama de θ | **θ_j** nos dois capítulos; β só em F_β |
| **H** | entropia H_i (capitulo3.tex:194–196); Hessiana H (capitulo3.tex:294–298) | entropia **𝓗_i**; Hessiana **∇²J** |
| **J** | função de custo (capitulo3.tex:63–67, 119, 125, 150, 290); inércia do K-means (capitulo3.tex:274) | inércia **W** (de WCSS) |
| **G / ΔI** | Gini G e ganho ΔG (capitulo3.tex:193, 204–215); a mesma grandeza como ΔI(n) (capitulo5.tex:146–149) | **ΔG** nos dois lugares |
| **T / t** | nº de árvores T e índice t (capitulo5.tex:146–149); iteração t (capitulo3.tex:290, 296); tempo t, t_i, t_exp (Caps. 2 e 4); "teste t" (capitulo4.tex:179) | árvores **B**, índice **b**; iteração **s** (θ^{(s)}); **t** só para tempo ("teste t" é nome próprio) |
| **ε** | erro ε_i (capitulo3.tex:51); constante 10⁻³⁰⁰ (capitulo4.tex:179) | constante **δ** |
| **X** | conjunto {x_i} (capitulo3.tex:45) e matriz n×d (capitulo3.tex:65–72) | definir X como matriz n×d já em capitulo3.tex:45 |
| τ, λ, η, V_S, r_t | τ = limiar (consistente); λ = comprimento de onda; η = passo no GD e no boosting (mesmo papel: aceitável, mas declarar) | manter. Se o simulador for descrito, não usar τ para a profundidade óptica dos anéis (o código usa `tau`) |

- **Proposta adicional:** ativar a lista de símbolos da classe (`\makelosymbols`/`\printlosymbols`, já comentados em
  teseon.tex:41 e :147) e registrar cada símbolo com `\symbl` na primeira ocorrência.
- **Justificativa:** a banca citou f; o problema é sistêmico (17 símbolos). Os casos de maior risco de leitura errada são
  f, σ, μ, k/K, m/n e D/d.
- **Status:** decisão autor+orientador (a escolha dos símbolos). A troca em si é mecânica.

---------------------------------------------------------------------
## CAPÍTULO 2
---------------------------------------------------------------------

### Cap2 bb — raios paralelos, escala 1:1, Fig. 2.1
- **Local:** capitulo2.tex:15
- **Trecho atual:** `Como a estrela ocultada está a distâncias muito maiores que a do corpo do Sistema Solar à Terra (a estrela em anos-luz, o corpo em horas-luz), os raios luminosos que chegam ao corpo são essencialmente paralelos: a sombra projetada na superfície terrestre preserva o limbo do corpo, com escala unitária.` … `a curva de luz registra as quedas de fluxo produzidas pela passagem dos anéis e do corpo principal diante da estrela.`
- **Proposta:**
```latex
Como a estrela ocultada está a distâncias muito maiores que a do corpo do Sistema Solar à Terra (a estrela a anos-luz; o corpo a minutos ou horas-luz), os raios luminosos da estrela que chegam ao corpo são essencialmente paralelos entre si. Por isso, no plano perpendicular à direção da estrela --- o plano do céu ---, a sombra reproduz o perfil do corpo em escala 1:1. Essa correspondência deixa de ser fiel quando o tamanho do corpo se torna comparável à escala de Fresnel ou ao diâmetro aparente da estrela projetado à distância do corpo (Seção~\ref{sec:caracteristicas_curvas}); sobre o solo, a sombra aparece ainda alongada pela inclinação da superfície terrestre em relação aos raios.
```
  e, no fim do parágrafo:
```latex
a curva de luz de ocultação (painel inferior) registra as quedas de fluxo estelar produzidas pela passagem dos anéis e do corpo principal diante da estrela, tal como medidas por um observador na superfície da Terra.
```
- **Justificativa:** a ressalva da banca ("vale para Centauros e TNOs, não necessariamente para asteroides próximos") é
  **fisicamente imprecisa**. Os raios são paralelos para qualquer corpo do Sistema Solar. O que estraga o 1:1 é o tamanho
  do corpo comparado a L_F = √(λΔ/2) e ao diâmetro estelar projetado θ★Δ, e ambos CRESCEM com a distância. A 1 UA,
  L_F ≈ 0,19 km; a 40 UA, L_F ≈ 1,2 km (e 0,1 mas ≈ 2,9 km). Os desvios pesam para corpos pequenos (Roques et al. 1987),
  não para "asteroides próximos" em geral. Corrigi também "horas-luz", que não vale para asteroides.
- **Status:** aplicável direto.

### Cap2 cc — sombra em movimento, cordas, previsão, Gaia
- **Local:** capitulo2.tex:24
- **Trecho atual (abertura):** `A sombra do corpo ocultante projeta-se na superfície terrestre.`
- **Proposta:**
```latex
A sombra do corpo ocultante projeta-se na superfície terrestre e move-se sobre ela com velocidade \(V_S\) --- de alguns a algumas dezenas de km\,s\(^{-1}\) ---, que é a velocidade do corpo \emph{relativa ao observador}, projetada no plano do céu. Ela combina o movimento orbital do corpo, o movimento orbital da Terra (termo dominante para Centauros e TNOs, que se deslocam a poucos km\,s\(^{-1}\)) e, em menor grau, a rotação da Terra (\(\lesssim 0{,}46\)\,km\,s\(^{-1}\)). Na ocultação por Umbriel de 2020, por exemplo, \(V_S \approx 17\)\,km\,s\(^{-1}\) (Figura~\ref{fig:umbriel_painel}a).
```
- **Justificativa:** a fórmula sugerida pela banca ("velocidade orbital do corpo + rotação da Terra") **omite o
  movimento orbital da Terra** (~30 km/s), que é justamente o termo dominante para TNOs: perto da oposição,
  V_S ≈ v⊕ − v_TNO ≈ 25 km/s. Quem se move é o corpo e o observador; a estrela fica parada.
- **Status:** aplicável direto.

#### cc.i
- **Trecho atual:** `Cada observador, em sua posição geográfica, registra um intervalo de tempo durante o qual a estrela é ocultada - uma \textbf{corda} no plano do céu.` e `a combinação dessas cordas permite reconstruir a forma e o tamanho do corpo no plano do céu com alta precisão \citep{SORA2022}.`
- **Proposta:**
```latex
Cada observador dentro do caminho da sombra registra o intervalo de tempo durante o qual a estrela permanece oculta --- uma \textbf{corda} positiva ---; os instantes de imersão e emersão, projetados no plano do céu, fornecem dois pontos do limbo do objeto. Observadores fora do caminho registram cordas negativas, que limitam até onde o limbo pode se estender.
```
  e `… a combinação dessas cordas permite reconstruir a forma e o tamanho do corpo no plano do céu com precisão quilométrica \citep{Ortiz2020, Umbriel2020}.`
- **Justificativa:** uma única corda dá dois pontos do limbo, e não "uma medida precisa do perfil", como diz a frase da
  banca. O perfil sai do conjunto de cordas. A citação troca o SORA por uma referência geral (Ortiz et al. 2020) e por um
  ajuste de forma com muitas cordas (Umbriel, 2023), como a banca pediu.
- **Status:** aplicável direto.

#### cc.ii / cc.iii
- **Trechos atuais:** `A previsão de ocultações depende criticamente da precisão das posições estelares e das efemérides do corpo;` e `tem ampliado o número de eventos previstos e observados, inserindo a técnica`
- **Proposta:** `No entanto, a previsão de ocultações depende criticamente …` e `tem ampliado o número de eventos previstos e observados com sucesso, inserindo a técnica`
- **Status:** aplicável direto.

#### cc.iv
- **Trecho atual:** `Graças à precisão astrométrica do catálogo Gaia, o gargalo atual`
- **Proposta:** `Graças à precisão astrométrica do catálogo Gaia \citep{GaiaMission2016, GaiaDR3}, o gargalo atual`
- **Justificativa:** para uma frase genérica, cita-se a missão (Prusti et al. 2016) e a release vigente (DR3, Vallenari et
  al. 2023). Se a frase se referir à previsão de Umbriel (set/2020), a release usada foi provavelmente a DR2, porque a
  EDR3 saiu em dez/2020.
- **Status:** aplicável direto para a frase genérica; a release específica requer confirmação do autor.

### Cap2 dd — parágrafo da fotometria e da curva de luz (i–vi)
- **Local:** capitulo2.tex:57 (o parágrafo todo)
- **Trechos atuais:**
  (i/ii) `A análise das imagens serve-se de \textbf{fotometria diferencial}: mede-se o fluxo da estrela alvo em relação a estrelas de referência no mesmo campo, de modo a cancelar efeitos sistemáticos, tendo em conta a curta duração do evento (extinção atmosférica, variações de transparência).`
  (iii) `O resultado da fotometria, ao longo do tempo, é uma \textbf{curva de luz} - a série temporal do fluxo (ou razão de fluxos) em função do tempo.`
  (iv) `uma queda relativamente abrupta (ingresso da estrela atrás do corpo), um patamar baixo (ocultação total ou parcial)`
  (v) `essa informação é igualmente útil para dar um limite superior ao tamanho da sombra e refinar modelos.`
  (vi) `A análise detalhada da curva (ajuste de modelos que incluem diâmetro aparente da estrela, difração de Fresnel e tempo de exposição) permite obter os instantes de imersão e emersão com alta precisão e, a partir deles, as dimensões e a forma do corpo \citep{SORA2022}.`
- **Proposta (substitui o parágrafo inteiro; já incorpora o item ee):**
```latex
A observação é tipicamente feita por telescópios amadores e profissionais, com detectores CCD ou câmeras de vídeo. A análise das imagens serve-se de \textbf{fotometria diferencial de abertura}, em que se mede o fluxo da estrela-alvo em relação ao de estrelas de referência no mesmo campo. Como a luz de todas atravessa praticamente a mesma coluna atmosférica no mesmo instante, cancelam-se efeitos sistemáticos comuns, como extinção atmosférica, variações de transparência etc. Essa fotometria é usualmente feita com pacotes dedicados, como o PRAIA (\textit{Platform for Reduction of Astronomical Images Automatically}) \citep{AssafinPRAIA}, que também implementa a \textbf{coronagrafia digital}: a subtração, imagem a imagem, de um modelo do halo de um objeto muito brilhante próximo ao alvo --- como Urano, no caso de Umbriel \citep{Assafin2023}. A \textbf{curva de luz de ocultação} é a razão entre o fluxo medido na abertura da estrela-alvo e o fluxo das estrelas de referência da mesma imagem, em função do tempo. Em geral, o corpo ocultante não é resolvido da estrela: a abertura contém a soma estrela + corpo, e a luz do corpo continua presente durante a ocultação (Seção~\ref{sec:caracteristicas_curvas}). Em uma detecção \textbf{positiva}, a curva exibe um trecho de fluxo aproximadamente constante (estrela ainda não ocultada), uma queda relativamente abrupta (a imersão: o corpo passa diante da estrela e o observador entra na sombra), um patamar de baixo fluxo e o retorno ao nível inicial (a emersão). Em uma detecção \textbf{negativa}, não há queda significativa; a curva permanece estável (ou com flutuações de ruído), e essa informação é igualmente útil: uma corda negativa delimita até onde o limbo do corpo pode se estender naquela direção. O ajuste de uma curva sintética --- que considera o diâmetro aparente da estrela projetado à distância do corpo, a difração de Fresnel e o tempo de exposição usado na observação --- permite obter os instantes de imersão e emersão com precisão da ordem de frações de segundo e, projetando esses instantes no plano do céu, as dimensões e a forma bidimensional do objeto \citep{Ortiz2020, SORA2022}.
```
- **Justificativa:** concordo com a banca em (i)–(vi), em especial (iv): a estrela não se move; quem se move é o corpo
  e a Terra. Acrescentei duas coisas que a física exige: (a) o cancelamento vem do caminho óptico comum, não da "curta
  duração"; (b) a abertura mede estrela + corpo, o que prepara o item ii (o patamar não vai a zero). O PRAIA é
  introduzido aqui com a forma "Platform", que é a do título do artigo (teseon.tex:222); capitulo2.tex:65 dizia
  "Package". "Curva sintética" (modelo de ocultação) fica reservado para isso; as negativas de ML passam a "simuladas",
  como pede o item geral l.
- **Status:** aplicável direto.

### Cap2 ee — PRAIA e coronagrafia digital (legenda da Fig. 2.2)
- **Local:** capitulo2.tex:53
- **Trecho atual:** `(c)~Exemplo de quadros CCD obtidos por uma das estações: são imagens como estas que alimentam os pacotes de fotometria (e.g.\ PRAIA) para a construção das curvas de luz. Neste caso, o brilho intenso de Urano exigiu a aplicação de coronagrafia digital para viabilizar a fotometria precisa de Umbriel. (d)~Curva de luz resultante da redução via PRAIA: fluxo normalizado de Umbriel (azul) e ruído de fundo (verde), com a queda de ocultação claramente visível.`
- **Proposta:**
```latex
(c)~Quadros CCD de uma das estações, processados pelo PRAIA: imagem original (esquerda), modelo do halo de Urano (centro) e imagem após a subtração por coronagrafia digital (direita), que viabiliza a fotometria de Umbriel e da estrela. (d)~Curva de luz de ocultação resultante: razão entre o fluxo da estrela somado ao de Umbriel e o fluxo de calibração (azul), e fundo de céu (verde). O patamar não chega a zero porque a luz de Umbriel permanece na abertura durante a ocultação.
```
- **Justificativa:** com o PRAIA e a coronagrafia definidos e citados no texto (item dd), a legenda só descreve. O eixo
  y da Fig. 2.2d é "(Umbriel + occ_star)/cal_flux": não é "fluxo de Umbriel".
- **Status:** aplicável direto. A leitura dos três painéis de (c) (original / modelo / subtraída) requer confirmação do
  autor.

### Cap2 ff — tempo morto; PRAIA já definido
- **Local:** capitulo2.tex:65
- **Trechos atuais:** `com o mínimo possível de tempo morto)` e `como o PRAIA (\textit{Package for the Reduction of Astronomical Images Automatically}), que automatiza a fotometria de abertura e a construção da curva de luz a partir das imagens \citep{Assafin2023}.`
- **Proposta:** `com o mínimo possível de intervalo entre imagens sucessivas --- o chamado tempo morto)` e `… é feita com o PRAIA, que automatiza a fotometria de abertura e a construção da curva de luz a partir das imagens \citep{Assafin2023}.`
- **Status:** aplicável direto.

### Cap2 gg — título da Seção 2.3
- **Local:** capitulo2.tex:70
- **Trecho atual:** `\section{Características das curvas de luz e detecção positiva/negativa}`
- **Proposta:** `\section{Caracterização das curvas de luz de ocultação}` (manter `\label{sec:caracteristicas_curvas}`)
- **Status:** aplicável direto.

### Cap2 hh — normalização e fatores da morfologia
- **Local:** capitulo2.tex:73
- **Trecho atual:** `Do ponto de vista observacional, uma curva de luz de ocultação é uma série temporal de fluxo (normalmente normalizado em relação ao nível fora da ocultação). Sua \textbf{morfologia} depende de vários fatores físicos e instrumentais.`
- **Proposta:**
```latex
Do ponto de vista observacional, uma curva de luz de ocultação é uma série temporal de fluxo, normalizada de modo que o nível fora da ocultação (estrela + corpo) valha 1. Sua \textbf{morfologia} depende de fatores físicos --- razão de brilho entre o corpo e a estrela, diâmetro aparente da estrela, difração de Fresnel, velocidade da sombra e presença de atmosfera, anéis ou satélites --- e de fatores instrumentais e atmosféricos --- tempo de exposição e tempo morto, cintilação, nuvens e qualidade da fotometria.
```
- **Status:** aplicável direto.

### Cap2 ii — profundidade da queda (erro físico central do capítulo)
- **Local:** capitulo2.tex:75
- **Trecho atual:** `Em uma detecção positiva, a curva exibe uma queda de fluxo durante o intervalo de tempo em que o trânsito ocorre. A profundidade da queda está relacionada à fração do disco estelar ocultada e à geometria da corda; em ocultações centrais ou próximas do centro, a queda pode ser total (fluxo próximo de zero no patamar).` … `as segundas ajudam a delimitar a borda da sombra e a descartar falsos positivos \citep{SORA2022}.`
- **Proposta (substitui o parágrafo):**
```latex
\textbf{Detecção positiva e negativa.} Em uma detecção positiva, a curva exibe uma queda de fluxo durante o intervalo em que o observador está dentro da sombra. Para um corpo sem atmosfera, muito maior que a estrela projetada e que a escala de Fresnel, qualquer corda que cruze o disco bloqueia toda a luz da estrela, seja ela central ou não: a posição da corda determina a \emph{duração} da queda, e não a sua profundidade. A profundidade depende da razão entre os brilhos do corpo e da estrela, porque a luz do próprio corpo continua a ser registrada na abertura. O patamar normalizado vale
\[
\phi_{\mathrm{oc}} = \frac{\Phi_{\mathrm{c}}}{\Phi_{\star}+\Phi_{\mathrm{c}}} = \frac{1}{1+10^{\,0{,}4\,(m_{\mathrm{c}}-m_{\star})}},
\]
em que \(\Phi\) e \(m\) são o fluxo e a magnitude do corpo (c) e da estrela (\(\star\)). Na ocultação por Umbriel (Figura~\ref{fig:umbriel_painel}d), o patamar \(\approx 0{,}24\) corresponde a \(m_{\mathrm{c}}-m_{\star} \approx 1{,}2\)\,mag; para TNOs, em geral muito mais fracos que a estrela ocultada, o patamar fica próximo de zero. Quedas apenas parciais surgem ainda quando o diâmetro aparente da estrela é comparável ao do corpo, em cordas rasantes, quando a exposição é mais longa que o evento ou em corpos pequenos dominados pela difração. Em corpos com atmosfera, a refração suaviza a imersão e a emersão e, em cordas centrais, pode produzir um \emph{flash} central --- um \emph{aumento} de fluxo no meio do evento \citep{Sicardy2016}. Em uma detecção negativa, o observador está fora da sombra; a curva não apresenta queda significativa, apenas flutuações típicas de ruído fotométrico, atmosférico e instrumental. Tanto positivas quanto negativas são úteis: as primeiras fornecem cordas para o ajuste de forma e tamanho; as últimas ajudam a delimitar a borda da sombra e a descartar soluções de forma incompatíveis \citep{SORA2022}.
```
- **Justificativa:** a banca está certa. O texto atual atribui a profundidade à "geometria da corda", o que é falso; em
  corda central de corpo com atmosfera o fluxo pode até subir (flash central). Conferi a fórmula com a própria tese: o
  patamar de 0,24 implica Δm = 2,5·log₁₀(1/0,24 − 1) ≈ 1,25 mag, compatível com a estrela G = 13,3 (mapa da Fig. 2.2a) e
  com Umbriel V ≈ 14,5. Na Fig. 2.4a o patamar é ≈ 0,18 (Δm ≈ 1,6). "Trânsito" é o termo errado e sai. "Descartar falsos
  positivos" vira "soluções incompatíveis", porque uma corda negativa restringe a forma, não detecta falsos positivos.
- **Status:** aplicável direto.

### Cap2 jj — fatores que afetam a forma (i–iv), mais a escala de Fresnel
- **Local:** capitulo2.tex:77
- **(i) Trecho atual:** `uma transição suave entre o nível desocultado e o ocultado.` → **Proposta:** `uma transição suave entre os níveis de fluxo desocultado e ocultado da estrela.`
- **(Fresnel — necessário, ver Extras) Trecho atual:** `a escala típica é da ordem de \(f = \sqrt{D\lambda/2}\), onde \(D\) é a distância entre o observador e o corpo ocultante (ou, em convenções equivalentes, a distância estrela--corpo) e \(\lambda\) o comprimento de onda \citep{Roques1987}.`
  **Proposta:**
```latex
a escala típica é a escala de Fresnel, \(L_{\mathrm{F}} = \sqrt{\lambda\Delta/2}\), em que \(\Delta\) é a distância entre o observador e o corpo ocultante e \(\lambda\) o comprimento de onda \citep{Roques1987}. A distância da estrela não entra: como ela está, para todos os efeitos, no infinito, a distância efetiva \(\Delta\,d_\star/(\Delta+d_\star)\) reduz-se a \(\Delta\).
```
- **(ii) Trecho atual:** `e \(t_{\mathrm{exp}}\) é o tempo de exposição; exposições longas podem suavizar ou mascarar detalhes da difração.` → **Proposta:** `e \(t_{\mathrm{exp}}\) é o tempo de exposição. Desse modo, exposições longas suavizam ou mascaram os detalhes da difração.` Além disso, remover a frase anterior que diz o mesmo (`exposições longas ou baixa resolução temporal podem mascarar os detalhes da difração e reduzir a precisão da extração dos tempos de imersão e emersão \citep{SORA2022}`), acrescentando `\citep{SORA2022}` à frase mantida.
- **(iii) Trecho atual:** `pelo \textbf{ciclo completo} entre quadros --- o tempo de exposição somado ao tempo morto de leitura (\textit{readout}):` → **Proposta:** `pelo \textbf{ciclo completo} entre quadros sucessivos --- o tempo de exposição somado ao tempo morto:`
- **(iv)** O acrônimo **já é aberto** em capitulo2.tex:65 (Seção 2.2, antes da 2.3): `O SORA (\textit{Stellar Occultation Reduction and Analysis}) \citep{SORA2022} é utilizado`. A banca não viu isso. Proposta só de harmonização na linha 65: `O \textit{Stellar Occultation Reduction and Analysis} (SORA) \citep{SORA2022} é utilizado`. Em :77 basta "SORA".
- **Justificativa:** (i)–(iii) como pede a banca. A "convenção equivalente" com a distância estrela–corpo é um erro
  físico: com 10 pc daria L ≈ 280 km em vez de ≈ 1,2 km.
- **Status:** aplicável direto. Em (iv) há discordância factual com a banca: o acrônimo já está aberto.

### Cap2 kk — resolução: "da ordem do quilômetro" (e a direção correta)
- **Local:** capitulo2.tex:86–90 (o exemplo numérico)
- **Trecho atual (90):** `Essa escala define a resolução espacial efetiva na direção perpendicular à corda: detalhes menores que $f$ são suavizados pela difração. Ainda assim, trata-se de uma resolução da ordem de quilômetros a dezenas de unidades astronômicas de distância - superior à de qualquer telescópio óptico terrestre operando por imageamento direto.`
- **Proposta:** nas linhas 86 e 88, trocar `$D = 40$` por `$\Delta = 40$` e `f = \sqrt{\frac{D\lambda}{2}}` por `L_{\mathrm{F}} = \sqrt{\frac{\lambda\Delta}{2}}` (a conta continua certa: 1,22 km). A linha 90 passa a:
```latex
A difração limita a resolução \emph{ao longo da corda}, isto é, na direção do movimento da sombra através do limbo: detalhes menores que \(L_{\mathrm{F}}\) nessa direção são suavizados. Na direção perpendicular às cordas, a resolução é dada pelo espaçamento entre os observadores. Na prática, a resolução efetiva ao longo da corda é o maior entre três comprimentos: \(L_{\mathrm{F}}\), o diâmetro aparente da estrela projetado à distância do corpo e o deslocamento da sombra durante um ciclo de aquisição, \(V_S\,(t_{\mathrm{exp}}+t_{\mathrm{morto}})\). Na campanha de Umbriel (\(\Delta \approx 19\)\,UA, \(V_S \approx 17\)\,km\,s\(^{-1}\)), por exemplo, \(L_{\mathrm{F}} \approx 0{,}9\)\,km, enquanto os ciclos das estações, de 0,13 a 4\,s, correspondem a cerca de 2 a 70\,km: ali é a amostragem temporal, e não a difração, que limita a resolução. Trata-se, ainda assim, de uma resolução da ordem do quilômetro na observação de objetos a dezenas de unidades astronômicas --- a 40\,UA, 1\,km subtende cerca de \(4\times10^{-5}\) segundo de arco, muito além do alcance de qualquer telescópio óptico terrestre operando por imageamento direto.
```
- **Justificativa:** a banca pediu a troca de redação; a física exige mais. "Perpendicular à corda" está errado: a
  difração age na direção da corda. "Essa escala define a resolução" é falso para os dados da própria tese: a cadência
  das 18 curvas de Umbriel no banco (dt mediano de 0,13 a 4,0 s) dá V_S·Δt de 2,3 a 68 km, contra L_F ≈ 0,9 km. O ângulo:
  1,2 km / 6,0×10¹² m = 2×10⁻¹⁰ rad ≈ 41 µas.
- **Status:** aplicável direto. As cadências são as do banco SQLite; o autor pode preferir citar só a faixa típica.

### Cap2 ll — "modelo" → "curva sintética"
- **Local:** capitulo2.tex:92
- **Trecho atual:** `o ajuste de um modelo a uma corda observada --- com os instantes de imersão e emersão marcados --- e o perfil do limbo reconstruído a partir do conjunto de cordas \citep{Umbriel2020}.`
- **Proposta:** `o ajuste de uma curva sintética a uma das curvas de luz de ocultação observadas nessa campanha --- com os instantes de imersão e emersão indicados --- e o perfil do limbo reconstruído a partir do conjunto de cordas \citep{Umbriel2020}.`
- **Status:** aplicável direto.

### Cap2 mm — legendas das Figs. 2.3 e 2.4 (só a parte textual)
- **Local:** capitulo2.tex:82 (Fig. 2.3)
- **Trecho atual:** `\caption{Componentes do modelo de curva de luz utilizado pelo SORA \citep{SORA2022}: difração de Fresnel (azul), tamanho angular da estrela, ciclo de integração do detector e, resultante da combinação dessas componentes, o modelo geométrico (verde). O ajuste simultâneo aos dados observados (pontos vermelhos) permite determinar com precisão os instantes de imersão e emersão, necessários para a reconstrução da forma do corpo.}`
- **Proposta:**
```latex
\caption{Componentes do modelo de curva de luz sintética utilizado pelo SORA \citep{SORA2022}. Verde: modelo geométrico, o ponto de partida --- corpo opaco de borda nítida ocultando uma estrela pontual, sem difração e com amostragem instantânea. Preto: o mesmo modelo incluindo a difração de Fresnel. Azul: incluindo também o diâmetro angular da estrela. Traços vermelhos: resposta instrumental, isto é, o valor que cada exposição registraria ao integrar a curva azul durante o tempo de exposição (a largura de cada traço). A curva sintética ajustada a dados reais combina todos esses efeitos (Figura~\ref{fig:curvas_cordas}a).}
```
- **Justificativa:** concordo com a banca: o preto é Fresnel, e o verde é o modelo inicial, não a combinação. Duas
  ressalvas. (1) Os traços vermelhos correspondem, sim, a uma imagem cada um, como diz a banca, mas nesta figura são
  valores do MODELO integrado na exposição (caem exatamente sobre a curva e não têm ruído), e não dados observados; o
  rótulo da própria figura é "Resposta Instrumental". (2) "Corpo esférico" não é necessário para o perfil 1-D: basta
  um limbo opaco e nítido.
- **Status:** aplicável direto.

- **Local:** capitulo2.tex:107 (Fig. 2.4)
- **Trecho atual:** `\caption{(a)~Curva de luz observada (preto) e modelo ajustado (vermelho) para uma das cordas da ocultação por Umbriel em 2020; os instantes de imersão e emersão, marcados por circunferências, definem a geometria da corda \citep{Umbriel2020}. (b)~Perfil do limbo de Umbriel; cada linha azul (incerteza vermelho) corresponde a uma corda projetada no plano do céu \citep{Umbriel2020}.}`
- **Proposta:**
```latex
\caption{(a)~Curva de luz de ocultação observada (preto) e curva sintética ajustada (vermelho) para uma das cordas da ocultação por Umbriel em 2020; os instantes de imersão e emersão encontram-se muito próximos dos pontos circulados nas bordas da queda \citep{Umbriel2020}. O patamar (\(\approx 0{,}18\)) não vai a zero porque a luz do próprio Umbriel permanece na abertura. (b)~Perfil do limbo de Umbriel no plano do céu: cada linha azul é uma corda positiva projetada, com as incertezas dos extremos em vermelho; as linhas verdes tracejadas são cordas negativas \citep{Umbriel2020}.}
```
- **Justificativa:** adota a alternativa textual da banca ("muito próximos"), explica o patamar e as linhas tracejadas.
- **Status:** aplicável direto. Que as linhas verdes tracejadas sejam cordas negativas (convenção dos gráficos do SORA)
  requer confirmação do autor.

### Cap2 nn — Seção 2.4 (geometria, Gaia, Q1R/Q2R)
- **Local:** capitulo2.tex:116
- **Trechos atuais:** `Destacamos o papel da geometria da sombra, das cordas e da precisão astrométrica na previsão e no aproveitamento dos eventos;` / `O volume crescente de dados produzidos por redes de telescópios e catálogos como o Gaia torna penosa a triagem manual de todas as curvas de luz;` / `como ocorreu, por exemplo, na descoberta dos anéis de Quaoar, descrito em \citep{Quaoar2023}.`
- **Proposta (substitui o parágrafo):**
```latex
Este capítulo situou as ocultações estelares como fenômeno astronômico e as curvas de luz de ocultação como produto observacional central. Vimos que a sombra do corpo, projetada em escala 1:1 no plano do céu, é amostrada pelas cordas dos observadores, e que é a combinação de cordas positivas e negativas que permite reconstruir forma e tamanho. Vimos também que a astrometria estelar do Gaia, ao tornar mais precisa a previsão de onde a sombra passará, aumentou o número de eventos observados com sucesso. A coleta e o armazenamento dos dados foram descritos em linhas gerais, e foram resumidas as características observacionais das curvas. A combinação de previsões mais precisas, da popularização de câmeras rápidas e de baixo custo e das redes de observadores multiplicou o número de curvas de luz de ocultação a analisar e tornou penosa a triagem manual de todas elas. Essa escala motiva o desenvolvimento de métodos automatizados de detecção baseados em aprendizado de máquina, cujos fundamentos são apresentados no Capítulo~3 e cuja implementação é detalhada no Capítulo~4. Interessa-nos, em particular, que sejam apontados eventos tênues que passaram despercebidos num primeiro tratamento das curvas --- como ocorreu com os anéis de Quaoar: o primeiro (Q1R) foi revelado pela revisita de dados antigos motivada por uma observação nova \citep{Morgado2023}, e o segundo (Q2R) foi descoberto em seguida \citep{Quaoar2023}. Um alerta confiável nesses casos é suporte para campanhas observacionais e descobertas importantes.
```
- **Justificativa:** o Gaia não produz curvas de luz; ele melhora a previsão. Cita Q1R e Q2R separadamente (item f). A
  mesma frase sobre o Gaia aparece no resumo (teseon.tex:136, `O crescimento do volume de dados produzido por redes de
  telescópios e catálogos como o Gaia, no entanto,`) e no abstract, e deve ser corrigida da mesma forma.
- **Status:** aplicável direto. O detalhe "descoberto em seguida", para o Q2R, requer confirmação do autor.

---------------------------------------------------------------------
## CAPÍTULO 4
---------------------------------------------------------------------

### Cap4 1 — "medidas derivadas"; features × características
- **Local:** capitulo4.tex:21
- **Trecho atual:** `para cada curva (série tempo--fluxo), são calculadas estatísticas e medidas derivadas (suavização, derivadas, comparações entre quartis, etc.), gerando a tabela de vetores da etapa 3.`
- **Proposta:** `para cada curva (série tempo--fluxo), calculam-se grandezas numéricas que a resumem --- estatísticas do fluxo, da série suavizada e de suas derivadas numéricas, e comparações estatísticas entre quartis temporais ---, gerando a tabela de vetores da etapa 3.`
- **Terminologia:** usar "características (\textit{features})" uma única vez (já definido em introducao.tex:26) e
  "características" no resto do texto. Os nomes de coluna do código ficam em `\texttt{}`.
- **Status:** a frase é aplicável direto; a padronização do termo é decisão autor+orientador.

### Cap4 2 — referência do B/occ, número de curvas, licença, ordem do texto
- **Local:** capitulo4.tex:45
- **Trechos atuais:** `catálogo \texttt{B/occ/asteroid}, totalizando centenas de curvas em formato \texttt{.dat}, contendo séries temporais de tempo e fluxo.` e `são centenas de curvas, que, somadas aos negativos por recorte e às curvas sintéticas, totalizam as 1693 amostras detalhadas na Seção~\ref{sec:config_experimental} (Capítulo~5).`
- **Evidência (código/dados):**
  - `pipeline/data_warehouse/plots/` tem **923** prévias .png, uma por curva baixada (insert_new_data.py:243–259).
  - O banco `stellar_occultations.db` tem **931** observações: 912 do VizieR + 19 do Grupo do Rio (18 de Umbriel, 1 de
    Chiron com **0 pontos**).
  - Rótulos no banco: 928 positivas e 3 negativas.
  - 125 positivas foram usadas para gerar os recortes e excluídas, restando 802; uma delas tem NaN e cai no `dropna`,
    ficando 801.
  - O nome do arquivo baixado trunca a data ao mês (insert_new_data.py:243): curvas do mesmo objeto, observador e mês
    sobrescrevem-se.
- **Proposta:**
```latex
\textbf{VizieR:} a maior parte das curvas foi obtida do catálogo \texttt{B/occ} do VizieR \citep{HeraldBocc2016}, tabela \texttt{B/occ/asteroid}, que reúne curvas de luz de ocultações por asteroides e é distribuído publicamente pelo CDS (licença CC-BY-4.0). Foram baixadas 923 curvas em formato \texttt{.dat}, com séries de tempo e fluxo; após a triagem descrita adiante, 912 foram inseridas no banco, que, somadas às 19 observações do Grupo do Rio, totalizam 931 observações (928 positivas e 3 negativas).
```
  e, no fim do parágrafo: `… são, portanto, centenas de curvas, que, somadas às curvas negativas (cuja obtenção é descrita na Seção~\ref{sec:construção_dataset}), totalizam as 1693 amostras do Capítulo~5.`
- **Status:** requer confirmação do autor. Os números saem dos artefatos (PNGs e banco), não de um log de download;
  a licença CC-BY-4.0 deve ser conferida na página do CDS (não consegui acessar o ReadMe nesta sessão).

### Cap4 3 — citar as bibliotecas
- **Local:** capitulo4.tex:47
- **Trecho atual:** `O processamento e a integração dos dados foram realizados com as bibliotecas \texttt{Astropy} e \texttt{Astroquery} (leitura e consulta a catálogos astronômicos), \texttt{asyncio} e \texttt{aiohttp} (coleta assíncrona, reduzindo o tempo total de aquisição), e \texttt{Pandas} (manipulação tabular).`
- **Proposta:** `… com as bibliotecas \texttt{Astropy} \citep{Astropy2022} e \texttt{Astroquery} \citep{Astroquery2019} (leitura e consulta a catálogos astronômicos), \texttt{asyncio} (biblioteca padrão do Python) e \texttt{aiohttp} (coleta assíncrona, reduzindo o tempo total de aquisição), e \texttt{Pandas} \citep{McKinney2010} (manipulação tabular). As rotinas numéricas de suavização e de testes estatísticos (Seção~\ref{sec:features}) usam a biblioteca SciPy \citep{SciPy2020}.`
- **Status:** aplicável direto (metadados verificados).

### Cap4 4 — o que eram as "curvas defeituosas"
- **Local:** capitulo4.tex:49
- **Trecho atual:** `Registra-se, ainda, que as curvas marcadas como defeituosas no \textit{download} foram descartadas sem caracterização do defeito nem tentativa de reaproveitamento (decisão de escopo e tempo que constitui uma fragilidade reconhecida da metodologia).`
- **Evidência:** o código não marca curvas como "defeituosas". Downloads com HTTP ≠ 200 apenas imprimem "Failed to fetch"
  e não salvam arquivo (insert_new_data.py:224–226); exceções são capturadas (:261–262). A triagem foi visual, pelas
  prévias .png: das 923 baixadas, 912 entraram no banco. Problemas que a triagem não removeu: 2 curvas com tempo não
  monotônico (uma delas, Toni 2014-03, totalmente invertida); 19 curvas com tempo em dias; 115 das 802 positivas com
  máximo suavizado > 1,5 (até 2453) e 40 com fluxo mínimo < −0,5, valores fisicamente impossíveis para fluxo normalizado.
- **Proposta:**
```latex
Na triagem visual das prévias, foram descartadas as curvas que não eram curvas de luz de ocultação (por exemplo, curvas de rotação), os arquivos em formato divergente e os arquivos vazios ou incompletos resultantes de falhas de \textit{download} --- ao todo, 11 das 923 curvas baixadas. Essas curvas não foram reaproveitadas, decisão de escopo que constitui uma fragilidade reconhecida da metodologia. A triagem tampouco eliminou todos os problemas de qualidade: duas curvas inseridas têm o tempo fora de ordem, e cerca de 14\% das positivas apresentam valores de fluxo normalizado fisicamente implausíveis (acima de 1,5 ou abaixo de \(-0{,}5\)), indicativos de falhas de normalização ou de fotometria na fonte.
```
- **Status:** requer confirmação do autor: a divisão dos 11 descartes por tipo e se houve descartes antes da geração das
  prévias.

### Cap4 5 — "checagem do alinhamento temporal"
- **Local:** capitulo4.tex:67
- **Trecho atual:** `Durante a inserção, buscou-se preservar ao máximo os valores originais, realizando apenas ajustes mínimos de consistência: uniformização de unidades quando necessário, checagem do alinhamento temporal e validação de metadados, sem alterar as características intrínsecas das curvas.`
- **Evidência:** o script de inserção (insert_new_data_manually.py:69–120) lê tempo, fluxo e erro e grava só tempo e
  fluxo (o erro é ignorado, linha 116), sem ordenar e sem converter unidades. No banco: 19 curvas em dias (Umbriel e
  Chiron; dt ≈ 1,2×10⁻⁵ d) contra segundos no VizieR; 2 curvas com tempo não monotônico. As datas ficam com resolução de
  mês (dia = 01, script :40–55). O observador cai para "Unknown" quando o nome tem caracteres fora de [A–Za–z0–9]
  (261 casos), e a checagem de duplicata por (objeto, data, observador) pode descartar curvas distintas.
- **Proposta:**
```latex
Durante a inserção, os valores de tempo e fluxo foram preservados exatamente como fornecidos pelas fontes; a coluna de incerteza fotométrica, quando presente, não foi armazenada. Não foram aplicadas conversão de unidades de tempo nem verificação automática de ordenação: as curvas do VizieR estão em segundos, as do Grupo do Rio em dias julianos, e duas curvas apresentam tempos fora de ordem. As datas das observações foram registradas com resolução de mês. Essas limitações afetam as características que dependem da escala de tempo (duração do evento) ou da ordem dos pontos (\textit{max drawdown}).
```
- **Justificativa:** a banca pergunta como e por que se checou o alinhamento temporal. O código mostra que essa checagem
  não existiu, e o efeito é concreto: Occ_duration_s fica em dias para 18 curvas, incluindo as 3 negativas nativas. A
  correção definitiva é converter tudo para segundos e ordenar antes de extrair as características.
- **Status:** requer confirmação do autor (se houve checagem manual fora do código).

### Cap4 6 — link quebrado do simulador; estrutura das subseções
- **Local:** capitulo4.tex:101 (`geração de curvas sintéticas negativas com o simulador físico de Gomes-Ferrante \& Braga-Ribas~\citep{Simulator}.`) e teseon.tex:232 (`\url{https://www.springernature.com/gp/researchers/text-and-data-mining}`)
- **Proposta:** substituir o \bibitem `Simulator` pela entrada com DOI (ver "Referências novas") e escrever `geração de curvas negativas simuladas com o simulador de curvas de luz de ocultação de \citet{Simulator}`. Estrutura sugerida para a Seção 4.4:
```latex
\section{Construção do conjunto de dados para aprendizado de máquina}
\subsection{Composição do conjunto de dados}            % tabela: 802 positivas; negativas = 3 nativas + 186 recortes + 702 simuladas
\subsection{Curvas reais: positivas, negativas e negativos por recorte}   % funde as atuais 4.4.2 e 4.4.3
\subsection{Curvas negativas simuladas}                  % atual 4.4.4
```
- **Justificativa:** o link atual aponta para uma página de mineração de dados da Springer; o DOI correto foi
  verificado. A sugestão da banca de apagar a 4.4.3 perderia a descrição do recorte, que é essencial (e é onde mora o
  problema de vazamento), por isso proponho fundir em vez de apagar.
- **Status:** a referência é aplicável direto; a reestruturação é decisão autor+orientador.

### Cap4 7 — "em muitos catálogos"; origem dos rótulos do VizieR
- **Local:** capitulo4.tex:109 e capitulo4.tex:85
- **Trechos atuais:** `O número de curvas negativas ``nativas'' (observações realmente sem ocultação) costuma ser menor que o de positivas em muitos catálogos. Além disso, o catálogo obtido via VizieR, que constitui a principal fonte de dados deste trabalho, contém exclusivamente curvas positivas.` e (85) `no VizieR, a classificação positiva/negativa provém dos curadores do catálogo \texttt{B/occ/asteroid}.`
- **Evidência:** a consulta ao VizieR usa só as colunas Dur, Date, Seq, Name e ObsName (insert_new_data.py:266–285),
  sem rótulo de detecção. Todas as curvas baixadas são movidas por padrão para a pasta `positive`
  (insert_new_data.py:342–385), e o rótulo vem do nome da pasta (insert_new_data_manually.py:25).
- **Proposta (109):** `No catálogo utilizado neste trabalho (\texttt{B/occ/asteroid}), praticamente não há curvas negativas: todas as curvas obtidas do VizieR foram tratadas como positivas e conferidas por inspeção visual das prévias. As únicas negativas reais do banco são três cordas negativas da campanha de Umbriel.`
  **Proposta (85):** `no VizieR, todas as curvas foram rotuladas como positivas por padrão e conferidas por inspeção visual; o catálogo não fornece um rótulo explícito de detecção.`
- **Justificativa:** restringe a afirmação ao catálogo usado, como pede a banca, e corrige uma afirmação contraditória
  com o código: os rótulos não vêm "dos curadores".
- **Status:** requer confirmação do autor (que o B/occ/asteroid não traz flag de detecção).

### Cap4 8 — "propriedades da estrela", "curva simples", vazamento repetido
- **Local:** capitulo4.tex:113 e :115
- **Trechos atuais:** `compartilham características intrínsecas da observação, como instrumentação, condições observacionais e propriedades da estrela observada.` / `Assim, para evitar vazamento de informação (\textit{data leakage}) e reduzir o risco de viés nos modelos, a curva positiva que originou os recortes deve ser removida do conjunto de dados utilizado no treinamento e na avaliação.` / `O procedimento adotado foi o seguinte: para cada curva positiva simples, identifica-se a região de ocultação de forma manual. Os segmentos antes e depois dessa região são recortados.`
- **Evidência:** build_dataset.py:69–214. A região é achada AUTOMATICAMENTE: primeiro e último ponto com fluxo < 0,78,
  após remover outliers a 3σ (:110, :117–124). Os segmentos precisam de pelo menos 20 pontos (:130, :136), e o humano só
  aceita ou rejeita (:177). Não existe critério de "curva simples". A exclusão da positiva-mãe funciona (0 das 125 mães
  no dataset). Os dois recortes de uma mesma mãe, porém, têm nomes distintos e podem cair em partições diferentes:
  18/38 no teste do Exp. 3 e 21/38 no teste misto.
- **Proposta (113, troca a última frase e apaga a frase sobre vazamento, que fica só na 115):**
```latex
Contudo, por serem derivados da mesma curva de luz de ocultação, os recortes compartilham com ela a mesma estrela (brilho, cor e diâmetro aparente), o mesmo instrumento e as mesmas condições de imagem daquela noite (PSF, \textit{seeing}, cadência, cintilação e transparência).
```
  **Proposta (115):**
```latex
O procedimento adotado foi o seguinte: em cada curva positiva de uma amostra aleatória, a região de ocultação é delimitada automaticamente pelo primeiro e pelo último ponto com fluxo normalizado inferior a 0,78, após a remoção de \textit{outliers} a \(3\sigma\); os segmentos anterior e posterior a essa região, com pelo menos 20 pontos cada, são exibidos e aceitos ou rejeitados manualmente. Se ao menos um segmento é aceito, a curva positiva original é excluída do conjunto de positivas, para que a mesma observação não apareça como positiva e como negativa. Os dois segmentos de uma mesma curva, no entanto, são tratados como amostras distintas na divisão treino/teste (Capítulo~5). Quedas rasas que não cruzam o limiar de 0,78 --- como as de anéis, atmosferas ou ocultações rasantes --- não são detectadas por esse critério e, se presentes fora do evento principal, permanecem nos segmentos rotulados como negativos; a inspeção visual é a única salvaguarda.
```
- **Justificativa:** responde às perguntas da banca, remove a repetição e descreve o que o código faz. A última frase é
  honestidade obrigatória: o critério pode rotular como negativo exatamente o tipo de sinal sutil que a tese quer achar.
- **Status:** aplicável direto. O tamanho da amostra recortada (o padrão do código é 50 por execução) requer confirmação
  do autor.

### Cap4 9 — "posição ao longo da corda" no simulador
- **Local:** capitulo4.tex:119
- **Trecho atual:** `(i)~geometria do evento (tempo, posição ao longo da corda); (ii)~difração de Fresnel nas bordas de imersão e emersão; (iii)~modelo de ruído (Poisson, ruído de leitura, cintilação atmosférica); (iv)~normalização pós-fotometria.` e `Para a classe negativa, são geradas curvas sem evento (ou com diâmetro efetivo nulo), submetidas ao mesmo tipo de ruído e normalização das curvas reais.`
- **Evidência:**
  - Em simulate_curve.py:483–493, cada instante vira posição na corda, x = V_S·(t − t₀) em km, no plano do céu.
  - O corpo é uma faixa opaca 1-D de largura igual ao diâmetro (:386–392, :173–193), o que equivale a uma corda
    central; o simulador não tem parâmetro de impacto nem latitude do observador.
  - Para as negativas o diâmetro é 0, logo a transmissão é T ≡ 1.
  - Os parâmetros são sorteados uniformemente (:745–747 e :794): duração de 20–60 s, t_exp de 0,05–0,25 s,
    magnitude 11–14,5 e seeing de 0,8–1,6″. As negativas vêm de `gerar_curvas_aleatorias(n_curvas=720,
    positivas=False, seed=422)` (:846), mas o dataset tem 702; a diferença requer confirmação do autor.
  - O ruído é branco: Poisson, leitura gaussiana e cintilação lognormal (:239–286).
  - O cabeçalho diz que o arquivo "reorganiza o antigo script monolítico".
- **Proposta:**
```latex
O simulador combina: (i)~a geometria do evento --- o instante de cada exposição é convertido na posição do observador ao longo da corda, \(x(t) = V_S\,(t-t_0)\), medida no plano do céu a partir do centro do evento; o corpo é representado por uma faixa opaca de largura igual ao seu diâmetro, o que equivale a uma corda central; (ii)~a difração de Fresnel nas bordas de imersão e emersão, o diâmetro aparente da estrela e a integração durante a exposição; (iii)~um modelo de ruído branco (Poisson da estrela e do céu, ruído de leitura gaussiano e cintilação multiplicativa lognormal); (iv)~a normalização pós-fotometria. Para a classe negativa, o diâmetro é nulo: a geometria e a difração não intervêm, e cada curva simulada consiste apenas na base de tempo (20 a 60\,s de duração, com exposições de 0,05 a 0,25\,s) e no ruído, com parâmetros sorteados uniformemente (estrela de magnitude 11 a 14,5; \textit{seeing} de 0,8 a 1,6\,''). Não foram incluídos ruído correlacionado, variações de transparência nem nuvens.
```
- **Justificativa:** não é erro ortográfico. "Posição ao longo da corda" é a coordenada x(t) = V_S(t − t₀), e o
  simulador, de fato, calcula a curva como função dessa posição. A alternativa da banca, "duração conforme a latitude do
  observador", descreve a dependência da duração com a distância transversal à trajetória da sombra (o parâmetro de
  impacto), que ESTE simulador não modela, pois usa só a corda central. A proposta deixa isso explícito.
- **Status:** a descrição é aplicável direto. Requer confirmação do autor se o código do repositório é o do artigo de
  Gomes-Ferrante & Braga-Ribas (2023) ou uma reimplementação.

### Cap4 10 — redefinição de curva de luz e frase repetida
- **Local:** capitulo4.tex:127
- **Trechos atuais:** `As curvas de luz são séries temporais (tempo \(\times\) fluxo).` e `O resultado é uma tabela em que cada linha é uma curva e cada coluna é uma dessas grandezas. As características foram padronizadas`
- **Proposta:** apagar as duas primeiras frases e a frase "O resultado é uma tabela…", que repete capitulo4.tex:19. O parágrafo começa assim: `Os modelos de classificação utilizados neste trabalho (Regressão Logística, Random Forest, XGBoost, CatBoost) recebem \textbf{vetores numéricos}, e não as séries brutas; por isso, cada curva é convertida no vetor de características descrito nesta seção. As características foram padronizadas …`
- **Status:** aplicável direto.

### Cap4 11 — título da 4.5.1; "curvas apenas ruidosas"
- **Local:** capitulo4.tex:131 e :145
- **Trechos atuais:** `\subsection{Estatísticas básicas do fluxo}` e `em curvas apenas ruidosas, \(\sigma\) e a amplitude podem ser menores.`
- **Proposta:** `\subsection{Amplitude e desvio padrão do fluxo}` e `em curvas negativas, o desvio padrão (\(\sigma_\phi\)) e a amplitude tendem a ser menores. Mesmo em ruído puro, porém, a amplitude não é nula: para \(N\) pontos de ruído gaussiano, ela é, em média, de cerca de \(6{,}5\,\sigma_\phi\) para \(N = 1000\), e cresce lentamente com \(N\).`
- **Justificativa:** o valor esperado da amplitude de 1000 gaussianas é ≈ 6,48σ. Sem esse número o leitor imagina que
  "sem evento" significa "amplitude ≈ 0".
- **Status:** aplicável direto.

### Cap4 12 — passa-baixa, janela, referência do Savitzky-Golay, derivadas
- **Local:** capitulo4.tex:149, 152, 153
- **Trechos atuais:** `A suavização atua como um filtro passa-baixa:` … `A janela é adaptativa ao tamanho da série: utiliza-se \(N/40\) para séries longas (ex.: \(N > 120\) pontos) e \(N/3\) para séries mais curtas, com mínimo de 3 pontos e ímpar para filtros simétricos.` / `\item Média móvel do fluxo; extraem-se o máximo e o mínimo da série suavizada.` / `\item Filtro de Savitzky-Golay (polinômio de ordem 2), que preserva melhor os picos e vales; do fluxo suavizado por Savitzky-Golay extraem-se máximo, mínimo e desvio padrão.`
- **Evidência:** build_dataset.py:316–321:
  `if len(flux) < 40: window = max(3, int(len(flux)/3)) else: window = max(3, int(len(flux)/40)); if window % 2 == 0: window += 1`.
  O corte é em **40** pontos, não em 120; para 40 ≤ N < 160 a janela é 3. Abaixo de 5 pontos a curva é descartada
  (:310). Com `use_filter='savgol'` a média móvel NÃO é calculada (:332–336); o dataset não tem colunas `mv_av`.
- **Proposta (substitui o parágrafo da 149 e a lista 151–154):**
```latex
Para reduzir o ruído de alta frequência sem perder a forma geral da curva, aplica-se uma suavização. Ela atua como um filtro passa-baixa --- um filtro que deixa passar as variações lentas (baixas frequências) e atenua as rápidas (altas frequências): as flutuações ponto a ponto, dominadas pelo ruído, são atenuadas, enquanto as variações lentas, que descrevem a forma da ocultação, são preservadas. Utiliza-se o filtro de Savitzky-Golay \citep{SavitzkyGolay1964}, implementado na função \texttt{savgol\_filter} da biblioteca SciPy \citep{SciPy2020}: em cada janela móvel de \(w\) pontos ajusta-se, por mínimos quadrados, um polinômio de grau 2, e o ponto central é substituído pelo valor do polinômio. Por isso o filtro preserva melhor a profundidade de picos e vales do que uma média móvel simples. A largura da janela depende do número \(N\) de pontos da série: \(w = \max(3, \lfloor N/3 \rfloor)\) para \(N < 40\) e \(w = \max(3, \lfloor N/40 \rfloor)\) para \(N \geq 40\), somando-se 1 quando o resultado é par (o filtro simétrico exige \(w\) ímpar). O valor mínimo de 3 refere-se à janela, e não à série; curvas com menos de 5 pontos são descartadas da extração de características. Do fluxo suavizado extraem-se máximo, mínimo e desvio padrão. A suavização é especialmente importante para as derivadas (subseção seguinte): a diferenciação numérica amplifica as componentes de alta frequência, nas quais domina o ruído, de modo que derivadas da série bruta refletiriam sobretudo o ruído, e não a forma da queda. Ressalta-se que a janela é proporcional ao comprimento do registro, e não a uma escala física do evento (escala de Fresnel, tempo de travessia de um anel): o mesmo evento é suavizado de forma diferente conforme a duração total da curva. Em uma série de 6000 pontos, por exemplo, a janela tem 151 pontos, o que pode apagar quedas que duram poucos pontos.
```
- **Justificativa:** responde às três perguntas da banca (passa-baixa, como a janela é escolhida, por que suavizar antes
  de derivar), corrige o limiar de 120 para 40 e apaga a média móvel, que não é usada. A última frase é a limitação
  física que explica parte do comportamento nos recortes de Quaoar.
- **Status:** aplicável direto.

### Cap4 13 — motivação do max drawdown
- **Local:** capitulo4.tex:160 e :167
- **Trechos atuais:** `O \textit{max drawdown} é a maior queda do fluxo em relação ao máximo acumulado até cada instante:` e `Em curvas com ocultação, o max drawdown tende a ser mais negativo; em curvas sem evento, permanece próximo de zero (apenas flutuações).`
- **Proposta (160):** `O \textit{max drawdown}, termo emprestado da análise de séries financeiras, é a maior queda do fluxo em relação ao máximo atingido \emph{anteriormente} na série:`
  **Proposta (167):**
```latex
A motivação é física: em uma ocultação, a queda ocorre a partir de um patamar alto (a estrela ainda visível). Ao contrário da amplitude, o \textit{max drawdown} respeita a ordem temporal --- só contam quedas que vêm depois de um máximo, como uma imersão. Em curvas com ocultação, ele tende a ser mais negativo, próximo de menos a profundidade da queda. Em curvas sem evento ele não é nulo: um pico de ruído seguido de uma flutuação para baixo já produz um valor de algumas vezes o desvio padrão do ruído. No conjunto de dados deste trabalho, a mediana é \(-0{,}19\) nas curvas negativas simuladas e \(-0{,}39\) nos negativos por recorte, contra \(-1{,}32\) nas positivas. Por depender da ordem dos pontos, essa característica é sensível a curvas com o tempo fora de ordem (Seção~\ref{sec:aquisição}).
```
- **Justificativa:** dá a motivação pedida e remove o falso "próximo de zero"; as medianas vêm de dataset_final.csv.
- **Status:** aplicável direto.

### Cap4 14 — K-means (i, ii, iii)
- **Local:** capitulo4.tex:171
- **Trechos atuais:** `(o nível fora do evento (\textit{baseline}) e o nível rebaixado durante a queda)` / `curvas com ocultação bem definida tendem a apresentar distância maior; curvas apenas ruidosas, distância menor.` / `Esse tipo de questão é o que motiva o objetivo dessa extração: testar a utilidade do algoritmo no contexto de ocultações.`
- **Proposta:** (i) `(o nível fora do evento, ou \textit{baseline}, e o nível de fluxo menor durante o evento)`; (ii)+(iii):
```latex
curvas com ocultação bem definida tendem a apresentar distâncias maiores, enquanto curvas negativas, cujas variações de fluxo se devem apenas ao ruído, apresentam distâncias menores. É importante notar que o K-means sempre encontra dois grupos, mesmo em ruído puro: para uma série gaussiana de desvio padrão \(\sigma_s\) (o da série suavizada), os centróides ficam em \(\pm\sigma_s\sqrt{2/\pi}\) em torno da média, e a distância entre eles vale \(\approx 1{,}6\,\sigma_s\). A característica só discrimina, portanto, quando a queda é algumas vezes maior que o ruído da série suavizada. Em quedas tênues, com profundidade comparável a \(1{,}6\,\sigma_s\), a distância de uma curva positiva pode coincidir com a de uma negativa ruidosa; verificar se, mesmo assim, a característica contribui para a classificação é o objetivo desta extração.
```
- **Justificativa:** responde a (iii), dizendo qual é a "questão" (as distâncias intermediárias), com um número de
  primeiros princípios. Conferi: K-means em 20 000 gaussianas dá 1,59σ (a teoria dá 1,596σ); nas negativas simuladas do
  dataset, a mediana de kmeans_centroid_dist / Savgol_std é 0,0348/0,0213 = 1,63.
- **Status:** aplicável direto.

### Cap4 15 — curtose; "transição de fluxo"
- **Local:** capitulo4.tex:175
- **Trechos atuais:** `assimetria (\textit{skewness}) e curtose da primeira derivada` e `capturam a ``forma'' da transição e ajudam`
- **Proposta:** `assimetria (\textit{skewness}, que mede o quanto a distribuição se afasta da simetria em torno da média) e curtose (\textit{kurtosis}, que mede o peso das caudas da distribuição em relação ao da gaussiana; a implementação usa o excesso de curtose, nulo para uma gaussiana) da primeira derivada` e `capturam a ``forma'' da transição de fluxo e ajudam`
- **Justificativa:** `pd.Series.kurtosis()` (build_dataset.py:372) devolve o excesso de curtose (Fisher). Uma imersão
  rápida produz poucos valores extremos de derivada sobre um fundo concentrado, isto é, curtose alta.
- **Status:** aplicável direto.

### Cap4 16 — referências de Welch e K-S
- **Local:** capitulo4.tex:179
- **Trecho atual:** `aplicam-se um teste \(t\) de Welch (diferença de médias) e um teste de Kolmogorov-Smirnov (K-S), que compara as funções de distribuição acumulada das duas amostras e fornece um \(p\)-valor sob a hipótese de que as distribuições são iguais \citep{Wall2003, Morettin2010}.`
- **Proposta:**
```latex
aplicam-se o teste \(t\) de Welch \citep{Welch1947}, que compara as médias sem supor variâncias iguais, e o teste de Kolmogorov-Smirnov (K-S) para duas amostras \citep{Kolmogorov1933, Smirnov1948}, que compara as funções de distribuição acumulada; ambos estão implementados no SciPy (\texttt{ttest\_ind} e \texttt{ks\_2samp}) \citep{SciPy2020} e fornecem um \(p\)-valor sob a hipótese de que as duas amostras vêm da mesma população \citep{Wall2003, Morettin2010}. Os dois testes supõem pontos independentes. Em curvas de luz com ruído correlacionado (cintilação, variações de transparência), os \(p\)-valores ficam menores do que seriam com ruído independente; por isso são usados aqui apenas como característica ordenável, e não como probabilidade calibrada.
```
- **Justificativa:** dá as referências pedidas e explicita a hipótese de independência, que é violada em séries
  temporais.
- **Status:** aplicável direto (metadados verificados).

### Cap4 17 — IOTA; (a) "ruído de fótons"; (b) σ; (c) poço retangular = modelo geométrico; (d) frase da predição
- **Local:** capitulo4.tex:183, 191, 193, 211, 213
- **IOTA. Trecho atual (183):** `inspiradas em critérios observacionais discutidos em fóruns entre astrônomos amadores para análise de curvas difíceis de ocultação.` → **Proposta:** `inspiradas em critérios práticos discutidos por observadores da \textit{International Occultation Timing Association} (IOTA) --- associação que coordena observações de ocultações por astrônomos amadores e profissionais e cujos resultados alimentam o catálogo \texttt{B/occ} \citep{HeraldBocc2016, Herald2020, IOTA} --- para a análise de curvas difíceis de ocultação.` **Status:** requer confirmação do autor (se os fóruns eram mesmo da IOTA, e quais).
- **(a) Trecho atual (193):** `decorrente das incertezas de medição (ruído de fótons, de leitura e de cintilação atmosférica).` → **Proposta:** `decorrente das incertezas de medição (ruído de fótons --- a flutuação de Poisson na contagem de fótons da estrela e do céu ---, ruído de leitura e cintilação atmosférica).`
  **Discordo da banca:** o ruído de fótons (ruído de Poisson) é a fonte fundamental de ruído do sinal estelar e muitas
  vezes a dominante; o próprio simulador da tese o inclui (simulate_curve.py:255). Removê-lo seria fisicamente errado.
  Basta defini-lo. **Status:** decisão autor+orientador (minha recomendação é manter, com a definição).
- **(b) Trechos atuais (191, 193, 211):** `Em curvas sem ocultação, \(\mathrm{depth} \approx 0\); em curvas com evento, \(\mathrm{depth}\) reflete a magnitude da queda.` / `O desvio padrão \(\sigma_{\mathrm{baseline}}\) é calculado apenas sobre os pontos com fluxo \(\geq \mathrm{baseline}\) (fora do dip).` / `com \(\mu = \mathrm{baseline}\) e \(\sigma\) uma escala robusta dos resíduos (por exemplo, MAD --- mediana do valor absoluto dos desvios em relação à mediana).`
  **Proposta (191):** `Mesmo em curvas sem ocultação, \(\mathrm{depth}\) não é nulo: o mínimo de \(N\) pontos de ruído fica, em média, cerca de \(3\,\sigma\) abaixo da mediana para \(N \sim 10^3\). Em curvas com evento, \(\mathrm{depth}\) reflete a magnitude da queda.`
  **Proposta (193):** `O desvio padrão \(\sigma_{\mathrm{base}}\) é calculado apenas sobre os pontos com fluxo \(\geq \phi_{\mathrm{base}}\). Para ruído gaussiano, isso equivale ao desvio padrão de uma meia-gaussiana, \(\sigma_{\mathrm{base}} \approx 0{,}60\,\sigma\); por isso \(\mathrm{SNR\_dip}\) não é uma razão sinal-ruído no sentido usual --- vale cerca de 5 em ruído puro com \(N\sim10^3\) e diminui quando a ocultação ocupa mais da metade da curva, porque a mediana passa a pertencer ao patamar.`
  **Proposta (211):** `com \(\phi_{\mathrm{base}}\) a mediana do fluxo e \(s_{\mathrm{MAD}}\), no lugar de \(\sigma\), a mediana de \(|\phi_i - \phi_{\mathrm{base}}|\) (MAD). Para ruído gaussiano, \(s_{\mathrm{MAD}} \approx 0{,}674\,\sigma\); como a implementação não aplica o fator 1,4826 que converteria a MAD em estimativa de \(\sigma\), os valores de \(\chi^2\) ficam multiplicados por \(\approx 2{,}2\), o que não afeta a razão \(\chi^2_{\mathrm{const}}/\chi^2_{\mathrm{sw}}\). Como as somas não são divididas pelo número de pontos, \(\chi^2_{\mathrm{const}}\) e \(\chi^2_{\mathrm{sw}}\) crescem com \(N\) e refletem também o comprimento da curva.` (usar \(s_{\mathrm{MAD}}\) também nas Eqs. das linhas 209 e 215)
  **Justificativa:** além do nome do símbolo (que a banca apontou), as afirmações atuais são quantitativamente falsas. No
  dataset, a mediana de Occ_depth nas negativas vai de 0,10 a 0,31 (não ≈ 0) e a de Occ_SNR_dip vai de 3,3 a 4,7 (contra
  7,3 nas positivas). O código (occ_features.py:80–104, 316–323, 368–370) confirma a meia distribuição e a MAD sem fator.
  **Status:** aplicável direto.
- **(c) Trecho atual (213):** `\textbf{Chi² do modelo ``square well''.} O modelo com dip assume nível constante fora da janela da maior sequência e nível constante (média do fluxo) dentro da janela, em formato de ``poço retangular''.` → **Proposta:** acrescentar `Esse modelo é a versão mais simples do modelo geométrico da Figura~\ref{fig:modelo_sora} (curva verde): bordas nítidas, sem difração nem integração temporal; difere dele por ajustar o nível interno (a média dos pontos da janela) em vez de fixá-lo, o que acomoda a luz residual do corpo ocultante.` **Status:** aplicável direto.
- **(d) Trecho atual (213):** `A predição \(\mathrm{pred}_i\) vale \(\mathrm{baseline}\) fora da janela e a média do fluxo na janela dentro dela.` → **Proposta:** `No modelo de poço retangular, o valor previsto para cada ponto, \(\hat{\phi}_i\), é igual ao \textit{baseline} fora da janela e à média dos fluxos dentro dela.` (e `\mathrm{pred}_i` → `\hat{\phi}_i` na Eq. da linha 215). **Status:** aplicável direto.

### Cap4 18 — aspa invertida em 'median' (e o que o código realmente faz)
- **Local:** capitulo4.tex:236
- **Trecho atual:** `(\texttt{SimpleImputer} com \texttt{strategy='median'})`
- **Proposta:** `(\texttt{SimpleImputer}, com estratégia \texttt{median})`. Se o autor quiser manter o código literal, usar `\verb|strategy='median'|`. Acrescentar ao fim do parágrafo: `Na prática, o carregamento do conjunto descarta as linhas com valores faltantes (\texttt{dropna}); apenas uma curva positiva foi descartada, de modo que foram usadas 1692 amostras, e o \textit{imputer} permanece no código como salvaguarda.`
- **Justificativa:** em `\texttt` com fontenc T1, o ' é tipografado como aspa curva, que parece invertida. O acréscimo
  descreve train_model.py:175 (`pd.read_csv(...).dropna()`, que remove Hera_2005-04-01_BAllen).
- **Status:** aplicável direto. A contagem de 1692 afeta o Cap. 5 (fora do meu escopo).

### Cap4 19 — "representativo da realidade das campanhas"
- **Local:** capitulo4.tex:276
- **Trecho atual:** `A combinação de dados reais (VizieR, Grupo do Rio), negativos por recorte (obtidos manualmente) e curvas sintéticas visa um conjunto de treino equilibrado e representativo.`
- **Proposta:**
```latex
A combinação de dados reais (VizieR, Grupo do Rio), negativos por recorte (com inspeção visual) e curvas negativas simuladas produz um conjunto de treino com classes aproximadamente equilibradas (47\% de positivas). Essa composição não reproduz a das campanhas observacionais reais: nelas, a proporção entre cordas positivas e negativas varia de evento para evento e as negativas têm ruído real, ao passo que 79\% das negativas deste conjunto são simuladas, com ruído em geral menor que o das curvas observadas. As implicações dessa diferença são discutidas no Capítulo~5.
```
- **Justificativa:** **discordo** da frase sugerida pela banca ("representativo da realidade das campanhas"): os dados a
  contradizem. A mediana de σ_base é 0,021 nas simuladas, contra 0,058 nos recortes e 0,104 nas positivas. Escrever
  "visa" um conjunto representativo, sabendo que ele não é, seria enganar o leitor.
- **Status:** decisão autor+orientador.

---------------------------------------------------------------------
## REFERÊNCIAS NOVAS (\bibitem prontos)
---------------------------------------------------------------------
```latex
\bibitem[Ortiz et al. (2020)]{Ortiz2020} ORTIZ, J. L.; SICARDY, B.; CAMARGO, J. I. B.; SANTOS-SANZ, P.; BRAGA-RIBAS, F. ``Stellar occultations by Trans-Neptunian objects: from predictions to observations and prospects for the future''. In: PRIALNIK, D.; BARUCCI, M. A.; YOUNG, L. A. (Ed.). \emph{The Trans-Neptunian Solar System}. Amsterdam: Elsevier, 2020. p. 413--437. DOI: 10.1016/B978-0-12-816490-7.00019-9.
```
Metadados verificados (autores, livro, páginas e DOI). Os editores foram escritos de memória: a verificar.
```latex
\bibitem[Gaia Collaboration et al. (2016)]{GaiaMission2016} GAIA COLLABORATION; PRUSTI, T.; DE BRUIJNE, J. H. J.; et al. ``The Gaia mission''. \emph{Astronomy \& Astrophysics}, 595, A1, 2016. DOI: 10.1051/0004-6361/201629272.

\bibitem[Gaia Collaboration et al. (2023)]{GaiaDR3} GAIA COLLABORATION; VALLENARI, A.; BROWN, A. G. A.; PRUSTI, T.; et al. ``Gaia Data Release 3: Summary of the content and survey properties''. \emph{Astronomy \& Astrophysics}, 674, A1, 2023. DOI: 10.1051/0004-6361/202243940.
```
Metadados verificados. Se for preciso citar a DR2 (previsão de Umbriel, 2020): Gaia Collaboration; Brown, A. G. A.;
et al., A&A 616, A1, 2018, DOI 10.1051/0004-6361/201833051 — de memória, a verificar.
```latex
\bibitem[Herald et al. (2016)]{HeraldBocc2016} HERALD, D.; BREIT, D.; DUNHAM, D.; FRAPPA, E.; et al. \textit{Occultation lights curves}. VizieR On-line Data Catalog: B/occ. Strasbourg: CDS, 2016. DOI: 10.26093/cds/vizier.102033. Disponível em: \url{https://cdsarc.cds.unistra.fr/viz-bin/cat/B/occ}. Acesso em: [data].
```
Parcialmente verificado: o DOI resolve para B/occ, e o bibcode ADS é 2016yCat....102033H. O título está grafado como no
VizieR ("lights"). A lista completa de autores e a licença CC-BY-4.0 estão a verificar no ReadMe do CDS, que não
consegui acessar.
```latex
\bibitem[Gomes-Ferrante \& Braga-Ribas (2023)]{Simulator} GOMES-FERRANTE, W.; BRAGA-RIBAS, F. ``Stellar Occultation Simulator: application to Planet 9''. \emph{The European Physical Journal Special Topics}, v. 232, n. 18-19, p. 3113--3118, 2023. DOI: 10.1140/epjs/s11734-023-01031-z.
```
Metadados verificados (DOI no ADS e na Springer). Substitui a entrada em teseon.tex:232.
```latex
\bibitem[Savitzky \& Golay (1964)]{SavitzkyGolay1964} SAVITZKY, A.; GOLAY, M. J. E. ``Smoothing and differentiation of data by simplified least squares procedures''. \emph{Analytical Chemistry}, v. 36, n. 8, p. 1627--1639, 1964. DOI: 10.1021/ac60214a047.

\bibitem[Welch (1947)]{Welch1947} WELCH, B. L. ``The generalization of `Student's' problem when several different population variances are involved''. \emph{Biometrika}, v. 34, n. 1-2, p. 28--35, 1947. DOI: 10.1093/biomet/34.1-2.28.

\bibitem[Kolmogorov (1933)]{Kolmogorov1933} KOLMOGOROV, A. N. ``Sulla determinazione empirica di una legge di distribuzione''. \emph{Giornale dell'Istituto Italiano degli Attuari}, v. 4, p. 83--91, 1933.

\bibitem[Smirnov (1948)]{Smirnov1948} SMIRNOV, N. ``Table for estimating the goodness of fit of empirical distributions''. \emph{Annals of Mathematical Statistics}, v. 19, n. 2, p. 279--281, 1948. DOI: 10.1214/aoms/1177730256.
```
Metadados verificados. Observação: a versão de duas amostras do teste é de Smirnov (1939), entrada a verificar se o
autor quiser a origem exata; a de 1948 é a referência usual das tabelas.
```latex
\bibitem[Virtanen et al. (2020)]{SciPy2020} VIRTANEN, P.; GOMMERS, R.; OLIPHANT, T. E.; et al. ``SciPy 1.0: fundamental algorithms for scientific computing in Python''. \emph{Nature Methods}, v. 17, p. 261--272, 2020. DOI: 10.1038/s41592-019-0686-2.

\bibitem[Astropy Collaboration et al. (2022)]{Astropy2022} ASTROPY COLLABORATION; PRICE-WHELAN, A. M.; LIM, P. L.; et al. ``The Astropy Project: Sustaining and Growing a Community-oriented Open-source Project and the Latest Major Release (v5.0) of the Core Package''. \emph{The Astrophysical Journal}, v. 935, n. 2, 167, 2022. DOI: 10.3847/1538-4357/ac7c74.

\bibitem[Ginsburg et al. (2019)]{Astroquery2019} GINSBURG, A.; SIPŐCZ, B. M.; BRASSEUR, C. E.; et al. ``astroquery: An Astronomical Web-querying Package in Python''. \emph{The Astronomical Journal}, v. 157, n. 3, 98, 2019. DOI: 10.3847/1538-3881/aafc33.

\bibitem[McKinney (2010)]{McKinney2010} McKINNEY, W. ``Data Structures for Statistical Computing in Python''. In: \emph{Proceedings of the 9th Python in Science Conference}, p. 56--61, 2010. DOI: 10.25080/Majora-92bf1922-00a.

\bibitem[Herald et al. (2020)]{Herald2020} HERALD, D.; GAULT, D.; ANDERSON, R.; DUNHAM, D.; FRAPPA, E.; et al. ``Precise astrometry and diameters of asteroids from occultations -- a data set of observations and their interpretation''. \emph{Monthly Notices of the Royal Astronomical Society}, v. 499, n. 3, p. 4570--4590, 2020. DOI: 10.1093/mnras/staa3077.

\bibitem[IOTA]{IOTA} INTERNATIONAL OCCULTATION TIMING ASSOCIATION (IOTA). Disponível em: \url{https://occultations.org}. Acesso em: [data].
```
Verificados: SciPy, Astroquery, McKinney e Herald 2020 (DOI, volume e páginas). Astropy 2022: título, revista, volume e
DOI verificados; os nomes dos dois primeiros autores individuais (Price-Whelan, Lim) são de memória, a verificar. IOTA:
URL de memória, a verificar.

---------------------------------------------------------------------
## EXTRAS OBRIGATÓRIOS QUE A BANCA NÃO PEDIU (física e honestidade)
---------------------------------------------------------------------
1. **O patamar não vai a zero; a profundidade não depende da corda** (capitulo2.tex:75; legendas capitulo2.tex:53 e
   :107). A luz do corpo permanece na abertura; corda central não implica queda total; corpos com atmosfera podem ter
   flash central. Proposta no item ii, com a fórmula e a conferência pelos números de Umbriel.
2. **Escala de Fresnel: distância observador–corpo, direção ao longo da corda, e a resolução efetiva é
   max(L_F, θ★Δ, V_S·Δt)** (capitulo2.tex:77, :90). A "convenção equivalente" estrela–corpo erra por um fator de ~200;
   nas curvas de Umbriel, a cadência (2–70 km) domina sobre L_F (0,9 km). Propostas nos itens jj e kk.
3. **Quem se move e quão rápido:** V_S é a velocidade relativa corpo–observador, dominada pelo movimento orbital da Terra
   no caso de TNOs. A própria sugestão da banca em cc o omitia. Proposta em cc.
4. **"SNR_dip" não é uma SNR; "depth" ≠ 0 sem evento** (capitulo4.tex:191–199). Meia-gaussiana (0,60σ) e estatística
   de extremo dão SNR_dip ≈ 5 em ruído puro, e o valor despenca quando o evento ocupa mais de 50% da curva. É por isso
   que o "teste de baixo S/N" do Cap. 6 seleciona ocultações profundas. Proposta em 17(b).
5. **Dados de entrada: unidades e ordem do tempo e fluxos impossíveis** (capitulo4.tex:67). 19 curvas em dias,
   2 com tempo fora de ordem, ~14% das positivas com fluxo normalizado > 1,5 ou < −0,5 (até 2453). Occ_duration_s não
   está em segundos para as curvas de Umbriel. Corrigir os dados ou declarar. Itens 4 e 5.
6. **O recorte de negativos é automático (fluxo < 0,78) e a remoção de outliers a 3σ só é aplicada aos negativos**
   (capitulo4.tex:115). O pré-processamento depende da classe, e quedas rasas (anéis!) podem ficar dentro de
   "negativos". Item 8.
7. **A janela de suavização é proporcional a N, não a uma escala física** (capitulo4.tex:149). O mesmo evento é tratado
   de modo diferente conforme a duração do registro; corte real em 40 pontos, não 120. Item 12.
8. **As negativas simuladas não são "do mesmo tipo de ruído das curvas reais"** (capitulo4.tex:119). Ruído branco, sem
   ruído vermelho nem transparência, e cerca de 3x mais limpo que o real (σ_base 0,021 contra 0,058/0,104). Além disso,
   a cintilação do simulador é proporcional ao *seeing* (simulate_curve.py:266–268), o que está fisicamente errado: a
   cintilação depende da abertura (∝ D^(−2/3)), da massa de ar, da altitude e de t_exp^(−1/2) (fórmula de Young), não do
   seeing. Declarar no texto (item 9) e não chamar o conjunto de "representativo" (item 19).

---

# PARTE C — Revisor Simons: Capítulos 3, 5 e 6


Carta de crítica da banca: Dra. Flavia L. Rommel (SP/critica.txt). Escopo deste revisor: Cap. 3 (itens 1–26), Cap. 5 (itens 1–11) e Cap. 6 (i–vi).
Arquivos-alvo: `T/` = `writing_latex/Tese/`; `P/` = `pipeline/`; `O/` = `P/model_training/outputs/`.
Todos os "Trecho atual" foram conferidos por `grep -F` (script SP/verify_trechos.py; resultado ao final).
Nada no projeto foi editado. Rótulos novos de bibliografia propostos: Breiman2001, Chen2016, Prokhorenkova2018, Strobl2007, Zhong2023, Condorcet1785, Davies2021, Calinski1974, Nocedal2006 (ver a seção "Referências novas").

Achado técnico que explica o comentário geral (n) da banca e o item 1 do Cap. 3:
- A classe carrega `\RequirePackage[english,brazil]{babel}` (T/on.cls:60). Com babel-portuguese, `"` é um caractere ativo (atalho) que lê o *próximo token como argumento*.
- O TeX descarta espaços ao ler um argumento não delimitado. Por isso, em `"aprendem" a partir`, o espaço depois do `"` de fechamento some.
- O autor já contornava isso com `~` (ex.: `"positivo"~se`, capitulo3.tex:47).
- Correção global: trocar `"…"` por ` ``…'' ` (o padrão que o resto da tese já usa) ou carregar `csquotes` e usar `\enquote{…}`.

---------------------------------------------------------------------
## CAPÍTULO 3
---------------------------------------------------------------------

### [Cap3 1]
- Local: T/capitulo3.tex:13, :15. Mesma correção em todas as aspas retas do capítulo: :38, :47, :191, :220, :222, :248, :261, :278, :318, :352, :393, :408, :450.
- Trecho atual:
```tex
é uma área na qual os sistemas "aprendem" a partir de dados
ao final, o modelo está "treinado" e pode ser aplicado a novas informações.
o ML costuma ser visto como "caixa-preta" que produz previsões sem explicação.
```
- Proposta:
```tex
é uma área na qual os sistemas ``aprendem'' a partir de dados
ao final, o modelo está ``treinado'' e pode ser aplicado a novas informações.
o ML costuma ser visto como uma ``caixa-preta'' que produz previsões sem explicação.
```
  Regra global (todo o .tex): regex `"([^"\n]+)"` → ``` ``\1'' ```. Onde houver `"…"~` (cap3:47, :191), remover o `~`.
- Justificativa: o espaço some porque o `"` ativo do babel-brazil (on.cls:60) consome o espaço seguinte. A troca resolve também o comentário geral (n) em toda a tese.
- Status: aplicável direto.

### [Cap3 2]
- Local: T/capitulo3.tex:17–25.
- Trecho atual:
```tex
\textbf{Sugerir a existência de algo novo:} ML pode encontrar padrões não previstos, indicando a existência de relações ainda não descobertas. Em matemática, algoritmos já auxiliaram a conjecturar teoremas que depois foram demonstrados formalmente \citep{gryak2018conjugacy}.
permitem avaliar o impacto de cada variável (\textbf{feature}, ou característica numérica de entrada) na predição.
por exemplo, na triagem automática de ocultações estelares em levantamentos astronômicos -
```
- Proposta (substitui os cinco parágrafos em negrito por uma lista com recuo; os textos dos itens (iii) e (iv) ficam como estão):
```tex
\begin{enumerate}
	\item[(i)] \textbf{Sugerir a existência de algo novo:} o ML pode encontrar padrões não previstos, indicando relações ainda não descobertas. Em matemática, por exemplo, modelos de aprendizado de máquina guiaram a descoberta de uma relação entre invariantes algébricos e geométricos de nós, depois demonstrada como teorema, e a formulação de uma conjectura sobre polinômios de Kazhdan--Lusztig \citep{Davies2021}; em teoria de grupos, foram usados para decidir o problema da conjugação \citep{gryak2018conjugacy}.
	\item[(ii)] \textbf{Descobrir o grau de importância das variáveis:} técnicas como \textit{Mean Decrease Accuracy} (MDA) avaliam o impacto de cada variável (\textit{feature}, ou característica numérica de entrada) sobre a saída do modelo de ML para exemplos novos --- aqui, ``predição'' é a resposta do classificador, e não a previsão de uma ocultação a partir de efemérides. [... restante do parágrafo atual ...]
	\item[(iii)] \textbf{Explorar relações de causa e efeito:} [... texto atual ...]
	\item[(iv)] \textbf{Redução e simplificação:} [... texto atual ...]
	\item[(v)] \textbf{Encontrar padrões desconhecidos:} o ML pode atuar na detecção de eventos raros ou de anomalias em grandes volumes de dados --- por exemplo, na triagem automática de curvas de luz de ocultação obtidas em campanhas dedicadas e por redes de observadores, como as reunidas no catálogo \texttt{B/occ/asteroid} do VizieR. A maioria dos levantamentos de imageamento de grande campo não tem tempos de exposição e cadência compatíveis com a duração de uma ocultação. O ML indica onde vale a pena investigar, mesmo sem explicar o mecanismo.
\end{enumerate}
```
- Justificativa: a banca pede o exemplo concreto do teorema. A referência atual (Gryak et al. 2018) trata de *decidir* conjugação em grupos, não de conjecturar teoremas depois demonstrados; Davies et al. 2021 é o exemplo canônico. A distinção predição × previsão evita confusão com a previsão de ocultações. O caso de uso de (v) é campanha ou rede, não levantamento.
- Status: requer confirmação do autor (qual exemplo ele tinha em mente; manter ou não Gryak).

### [Cap3 3]
- Local: T/capitulo3.tex:34, :35 (listas); créditos dos classificadores em :38.
- Trecho atual:
```tex
Exemplos: filtro de spam, previsão de preços.
Exemplos: segmentação de clientes, identificação de \textit{outliers} (anomalias).
```
- Proposta:
```tex
Exemplos: filtro de \textit{spam}, previsão de preços, etc.
Exemplos: segmentação de clientes, identificação de \textit{outliers} (anomalias), etc.
```
  E, ao final do parágrafo de :38, acrescentar:
```tex
Neste trabalho, os classificadores foram usados por meio de bibliotecas Python de código aberto, cujas documentações pedem a citação dos trabalhos originais: \textit{scikit-learn} \citep{ScikitLearn2011}, para a Regressão Logística e o \textit{Random Forest} \citep{Breiman2001}; XGBoost \citep{Chen2016}; e CatBoost \citep{Prokhorenkova2018}.
```
  Repetir a citação primária na abertura de cada subseção (3.3.3 → Breiman2001; 3.3.4 → Chen2016; 3.3.5 → Prokhorenkova2018).
- Justificativa: hoje os algoritmos só são citados via Géron. As bibliotecas (scikit-learn, XGBoost, CatBoost) pedem a citação dos artigos originais.
- Status: aplicável direto (as quatro referências estão com metadados verificados).

### [Cap3 4]
- Local: T/capitulo3.tex:45.
- Trecho atual:
```tex
Em notação matemática, uma amostra rotulada é representada pela tupla \(Z = (X, Y)\).
é um vetor com \(d\) números que resumem, no caso deste trabalho, uma curva de luz (amplitude, mínimo do fluxo suavizado, distância entre centróides, etc.). O número \(d\) é a "dimensionalidade'' do problema (neste caso, 14 ou 28 features).
```
- Proposta:
```tex
Em notação matemática, uma amostra rotulada é representada pelo par ordenado (ou \textbf{tupla}, isto é, uma sequência ordenada e finita de elementos) \(Z = (X, Y)\).
é um vetor com \(d\) números que resumem, no caso deste trabalho, uma curva de luz de ocultação (por exemplo, a amplitude e o mínimo do fluxo suavizado). O número \(d\) é a ``dimensionalidade'' do problema (neste trabalho, entre 11 e 28 \textit{features}, conforme o experimento; Capítulo~5).
```
- Justificativa: atende ao pedido da banca (definir tupla e tirar a menção a centróides) e corrige um número errado. Nenhum experimento usou 14 features; as contagens reais, pelo `feature_names.pkl` de cada pasta em `O/`, são 28/13/12/12/11.
- Status: aplicável direto.

### [Cap3 5]
- Local: T/capitulo3.tex:47.
- Trecho atual:
```tex
a decisão final é então "positivo"~se essa probabilidade for maior ou igual a 50 \%, e "negativo"~caso contrário. O uso do valor 0,5 é intuitivo, mas cabe frisar que é arbitrário e dependerá do objetivo do modelo que está sendo treinado (esse limite decisório é chamado de 'threshold' nas pipelines de ML, ou $\tau$, e será melhor explorado mais adiante).
```
- Proposta:
```tex
a decisão final é então ``positivo'' se essa probabilidade for maior ou igual a 50\,\%, e ``negativo'' caso contrário. O uso do valor 0,5 é intuitivo, mas é arbitrário e depende do objetivo do modelo. Esse valor de corte é chamado de \textbf{limiar} de decisão (em inglês, \textit{threshold}) e será denotado por $\tau$; seu ajuste é discutido na Seção~\ref{sec:threshold_tuning}.
```
- Justificativa: a aspa simples invertida e o termo inglês sem itálico violam a ABNT; uniformiza "limiar" com o Cap. 5. Também remove `"…"~`.
- Status: aplicável direto.

### [Cap3 6]
- Local: T/capitulo3.tex:49.
- Trecho atual:
```tex
de modo que \(f\) generalize bem para novos exemplos não vistos.
```
- Proposta:
```tex
de modo que \(f\) generalize bem para novos exemplos, não vistos durante o treinamento.
```
- Justificativa: pedido literal da banca.
- Status: aplicável direto.

### [Cap3 7]
- Local: T/capitulo3.tex:75. Primeira menção a "sigmoide"; a figura só aparece em :181–187.
- Trecho atual:
```tex
mas mapeia a saída ao intervalo $(0,1)$ por uma função sigmoide e utiliza o custo de entropia cruzada
```
- Proposta:
```tex
mas mapeia a saída ao intervalo $(0,1)$ por uma \textbf{função sigmoide}, $\sigma(z)=1/(1+e^{-z})$ --- uma curva em forma de ``S'' que leva qualquer número real a um valor entre 0 e 1 (Figura~\ref{fig:sigmoide}) --- e utiliza o custo de entropia cruzada
```
  Opcional: mover o ambiente da figura `fig:sigmoide` (:181–187) para logo após a equação de \(\hat p\) (:108–110).
- Justificativa: a definição aparece na primeira ocorrência, e o leitor ingressante vê a curva antes de usá-la.
- Status: aplicável direto (mover a figura: decisão do autor).

### [Cap3 8]
- Local: T/capitulo3.tex:90 (Fig. 3.2) e :99 (Fig. 3.3); texto em :85 e :94.
- Trecho atual:
```tex
\caption{Aplicação da regressão linear ao problema de classificação binária: a reta produz saídas fora do intervalo $[0,1]$ \citep{Levada2026}. Nosso conjunto de dados mostra quatro amostras de curvas de luz com grandes amplitudes e outras quatro com baixas amplitudes. Nesse exemplo simples, o valor de 0,5 para o recorte da reta divide perfeitamente as duas classificações.}
    \caption{O mesmo problema anterior, mas com a adição de um \textit{outlier}. Uma das curvas possui tamanho de amplitude muito diferente da escala normal, possivelmente resultado da falta de normalização. Veja como a reta de regressão se desloca e o limiar 0,5 passa a classificar incorretamente \citep{Levada2026}.}
A figura a seguir ilustra a aplicação da regressão linear em dados bem comportados.
```
- Proposta:
```tex
\caption{Classificação binária (sim = 1, não = 0) em função do tamanho da queda de fluxo (marcadores). A linha tracejada indica o limiar de decisão; a linha contínua, o resultado da regressão linear aplicada aos dados (ver discussão no texto). Fonte: adaptado de \citet{Levada2026}.}
\caption{Como na Figura~\ref{fig:reglin_classif_ex1}, com a adição de um ponto discrepante (\textit{outlier}). Fonte: adaptado de \citet{Levada2026}.}
```
  Em :85, trocar a última frase por:
```tex
A Figura~\ref{fig:reglin_classif_ex1} ilustra a aplicação da regressão linear a oito exemplos ilustrativos --- quatro com grandes quedas de fluxo e quatro com quedas pequenas: nesse caso simples, o limiar 0,5 sobre a reta separa perfeitamente as duas classes, embora a reta produza valores fora do intervalo $[0,1]$.
```
  Em :94, depois de "A Figura~\ref{fig:reglin_classif_ex2} ilustra a situação:", inserir:
```tex
a curva discrepante tem amplitude muito diferente das demais (por exemplo, por falta de normalização), a reta se desloca e
```
  e corrigir "varios" → "vários" e "proximos" → "próximos" na mesma linha.
- Justificativa: a legenda deve descrever a figura, e a discussão vai para o texto. "Nosso conjunto de dados" é falso: a figura é de Levada (2026). A NBR 14724 (item 5.8, a verificar) exige identificação e fonte, mas não regula a discussão na legenda.
- Status: legendas e textos aplicáveis direto; fundir as duas figuras numa só é decisão autor+orientador.

### [Cap3 9]
- Local: T/capitulo3.tex:103, :105, :111.
- Trecho atual:
```tex
O que podemos ver é a reta de regressão pode sofrer alterações significativas
fazem da regressão linear uma abordagem inadequada para tarefas de classificação.
Nesse sentido, a regressão logística funcionará de forma similar a modelos lineares (saída contínua), mas será adaptado. O primeiro ponto será a interpretação probabilística
Isso pois a saída continuará continua, mas dessa vez limitada entre 0 e 1.
```
- Proposta:
```tex
O que podemos ver é que a reta de regressão pode sofrer alterações significativas
fazem da regressão linear uma abordagem inadequada para as tarefas de classificação necessárias a este trabalho.
Mais adequada a esse fim, a regressão logística funciona de forma similar aos modelos lineares (saída contínua), mas é adaptada ao nosso problema. O primeiro ponto de adaptação é a interpretação probabilística
Isso porque a saída continua sendo contínua, mas agora limitada ao intervalo $(0,1)$.
```
- Justificativa: 9.1–9.3 aplicados. Uso "Mais adequada a esse fim" porque "Mais adequada," isolado, como sugere a banca, fica truncado. Corrijo também "continuará continua".
- Status: aplicável direto.

### [Cap3 10]
- Local: T/capitulo3.tex:150. A banca pergunta se "o custo é minimizado" é verdade. Ao refazer a conta, o exemplo tem erro numérico.
- Trecho atual:
```tex
$\partial J / \partial \theta_1 = \frac{1}{4}\sum_i (\hat{p}_i - y_i)\,x_i = -0{,}15$. Com taxa de aprendizado $\eta = 1{,}0$, a atualização dá $\theta_1 \leftarrow 0 - 1{,}0 \times (-0{,}15) = 0{,}15$. Recalculando as probabilidades com o novo $\theta_1$, obtemos $\hat{p}_1 = \sigma(0{,}03) \approx 0{,}507$, $\hat{p}_2 \approx 0{,}515$, $\hat{p}_3 \approx 0{,}526$ e $\hat{p}_4 \approx 0{,}534$. O custo cai para $J \approx 0{,}685$.
Após centenas de iterações, a separação se consolida.
```
- Proposta:
```tex
$\partial J / \partial \theta_1 = \frac{1}{4}\sum_i (\hat{p}_i - y_i)\,x_i = \frac{1}{4}(0{,}1 + 0{,}2 - 0{,}35 - 0{,}45) = -0{,}125$. Com taxa de aprendizado $\eta = 1{,}0$, a atualização dá $\theta_1 \leftarrow 0 - 1{,}0 \times (-0{,}125) = 0{,}125$. Recalculando as probabilidades com o novo $\theta_1$, obtemos $\hat{p}_1 = \sigma(0{,}025) \approx 0{,}506$, $\hat{p}_2 \approx 0{,}512$, $\hat{p}_3 \approx 0{,}522$ e $\hat{p}_4 \approx 0{,}528$. O custo cai para $J \approx 0{,}678$.
Após centenas de iterações, a separação se consolida e o custo diminui continuamente. Como esses quatro pontos são linearmente separáveis (todo $x \le 0{,}4$ é negativo e todo $x \ge 0{,}7$ é positivo), sem regularização o custo só tende a zero no limite $|\theta_1| \to \infty$: não existe mínimo finito. Essa é uma das motivações para a regularização apresentada a seguir.
```
- Justificativa: refeito em Python. O gradiente é −0,125, não −0,15. Com θ₁=0,125, J=0,678; o texto atual dá 0,685, que nem corresponde a θ₁=0,15 (J=0,676). Em dados separáveis, o estimador de máxima verossimilhança diverge: "o custo é minimizado" só vale no limite. Os revisores Feynman e Sagan chegaram ao mesmo número.
- Status: aplicável direto.

### [Cap3 11]
- Local: T/capitulo3.tex:169 (e :408, mesmo problema Ridge/Lasso).
- Trecho atual:
```tex
É essencial \textbf{escalonar} as \textit{features} (e.g.\ StandardScaler) antes de aplicar Ridge ou Lasso, pois ambas as penalidades são sensíveis à escala dos dados: um atributo medido em quilômetros
Nesta dissertação, utiliza-se Ridge ou Lasso na Regressão Logística, conforme documentado no Apêndice~\ref{ap:hiperparametros}.
Nesta dissertação, o foco está na penalização de pesos em modelos lineares (Ridge/Lasso) e nos critérios de parada e poda nas árvores.
```
- Proposta:
```tex
É essencial \textbf{escalonar} as \textit{features} (por exemplo, com o \texttt{StandardScaler} do \textit{scikit-learn}) antes de aplicar Ridge ou Lasso, pois ambas as penalidades são sensíveis à escala dos dados. Por exemplo, um atributo medido em quilômetros
Nesta dissertação, utiliza-se apenas a penalidade Ridge ($\ell_2$), com $C = 1$ (valor padrão do \textit{scikit-learn}, sem busca por validação cruzada), conforme o Apêndice~\ref{ap:hiperparametros}.
Nesta dissertação, o foco está na penalização $\ell_2$ da Regressão Logística e nos limites de profundidade e de número mínimo de amostras por nó e por folha nas árvores (não se aplica poda).
```
  Uniformizar `\texttt{StandardScaler}` (já é assim em capitulo4.tex:127 e capitulo5.tex:175).
- Justificativa: o código não usa Lasso nem poda. `LR_PARAMS` (P/model_training/train_model.py:143-148) usa o padrão l2, C=1, lbfgs, o que conferi no modelo salvo (`O/resultado5/logistic_regression_model.pkl`: `penalty='l2', C=1.0, solver='lbfgs'`). `RF_PARAMS` (:113-121) usa `max_depth` e `min_samples_*`, sem `ccp_alpha`.
- Status: aplicável direto.

### [Cap3 12]
- Local: T/capitulo3.tex:191.
- Trecho atual:
```tex
O espaço de entradas (vetores de características) fica assim particionado em regiões (hiper-retângulos), cada uma associada a uma classe \citep{Levada2026}. Uma das maiores vantagens é a \textbf{interpretabilidade}
O \textit{scikit-learn} \citep{ScikitLearn2011} utiliza o algoritmo \textbf{CART}
```
- Proposta:
```tex
O espaço de entradas (vetores de características) fica assim particionado em regiões (chamadas de hiper-retângulos), cada uma associada a uma classe \citep{Levada2026}. Uma das maiores vantagens desses modelos é a \textbf{interpretabilidade}
A biblioteca Python \textit{scikit-learn} \citep{ScikitLearn2011}, usada neste trabalho na Regressão Logística, no \textit{Random Forest}, no K-means, na imputação, na padronização e no cálculo das métricas, utiliza o algoritmo \textbf{CART}
```
- Justificativa: atende a 12.1–12.3 e responde à pergunta da banca ("Essa biblioteca foi usada?"): sim, foi (train_model.py:31-47; build_dataset.py:24). Mantenho o hífen em "hiper-retângulos" (Acordo Ortográfico: prefixo *hiper-* + palavra iniciada por *r*).
- Status: aplicável direto.

### [Cap3 13]
- Local: T/capitulo3.tex:222.
- Trecho atual:
```tex
O \textbf{Teorema do Júri de Condorcet} ilustra a ideia:
```
- Proposta:
```tex
O \textbf{Teorema do Júri de Condorcet}\footnote{Formulado por \citet{Condorcet1785}: se $n$ votantes independentes acertam, cada um, com probabilidade $p > 1/2$, a probabilidade de a maioria acertar é $P_n = \sum_{k > n/2} \binom{n}{k} p^k (1-p)^{n-k}$, que cresce com $n$ e tende a 1. Para $n = 25$ e $p = 0{,}65$, obtém-se $P_{25} \approx 0{,}94$ (Figura~\ref{fig:ensemble_acuracia}). Como as árvores de uma floresta não são independentes, o ganho real é menor; ver \citet{geron2019maos}.} ilustra a ideia:
```
  Na legenda de `fig:ensemble_acuracia` (:237), acrescentar "Fonte: ..." (hoje está sem fonte).
- Justificativa: a nota pedida pela banca, com a fórmula e o número da Figura 3.7, conferido (0,9396). A hipótese de independência é a ressalva relevante.
- Status: aplicável direto (falta a fonte da figura manual_2: requer o autor).

### [Cap3 14]
- Local: T/capitulo3.tex:218, :229 (e :191, :220, demais ocorrências de "Random Forest").
- Trecho atual:
```tex
\subsection{Random Forest (Floresta Aleatória)}
\caption{Esquema simplificado do funcionamento de uma Floresta Aleatória.}
```
- Proposta:
```tex
\subsection{\textit{Random Forest} (floresta aleatória)}
\caption{Esquema simplificado do funcionamento de um \textit{Random Forest}.}
```
  A tradução fica só no título da subseção; no restante, `\textit{Random Forest}` (masculino: "o modelo").
- Justificativa: uniformidade terminológica (item 14) e uso de itálico em termo estrangeiro (comentário geral c).
- Status: aplicável direto.

### [Cap3 15]
- Local: T/capitulo3.tex:244–248.
- Trecho atual:
```tex
O \textbf{gradient boosting} utiliza um modelo aditivo: na iteração \(m\),
F_m(\vec{x}) = F_{m-1}(\vec{x}) + \eta \, h_m(\vec{x}),
onde \(h_m\) é um novo aprendiz fraco
O XGBoost (\textit{eXtreme Gradient Boosting}) aprimora esse esquema ao adicionar termos de regularização explícitos na função de custo (penalizando o número de folhas e os pesos das folhas) e ao utilizar uma expansão de Taylor de segunda ordem da perda para otimizar a atualização de cada árvore, o que resulta em implementação eficiente e alto desempenho \citep{geron2019maos}.
```
- Proposta:
```tex
O \textit{gradient boosting} utiliza um modelo aditivo: na iteração \(t\),
F_t(\vec{x}) = F_{t-1}(\vec{x}) + \eta \, h_t(\vec{x}),
onde \(h_t\) é um novo aprendiz fraco
O XGBoost (\textit{eXtreme Gradient Boosting}) \citep{Chen2016} aprimora esse esquema de duas maneiras. Primeiro, adiciona à função de custo termos de regularização explícitos, que penalizam o número de folhas e os pesos das folhas. Segundo, usa uma expansão de Taylor de segunda ordem da perda para calcular a atualização de cada árvore. O resultado é uma implementação eficiente e de alto desempenho.
```
  (e trocar \(F_{m-1}\) → \(F_{t-1}\) no restante de :248)
- Justificativa: \(m\) já é o número de exemplos (cap3:117). \(t\) é o índice de iteração usado no gradiente descendente (cap3:290), o que mantém a coerência. A frase longa foi dividida em três. Acrescento a citação primária.
- Status: aplicável direto.

### [Cap3 16]
- Local: T/capitulo3.tex:250.
- Trecho atual:
```tex
O XGBoost tornou-se muito popular em competições e aplicações práticas por sua precisão e velocidade.
Na \textit{pipeline} desta dissertação, o XGBoost é um dos quatro classificadores treinados e avaliados (Regressão Logística, Random Forest, XGBoost, CatBoost) (Capítulo 4).
```
- Proposta:
```tex
O XGBoost tornou-se muito popular em competições de ciência de dados --- por exemplo, foi usado em 17 das 29 soluções vencedoras de desafios publicadas pela plataforma Kaggle em 2015 \citep{Chen2016} --- e em aplicações práticas, por sua precisão e velocidade.
```
  (remover a segunda frase)
- Justificativa: responde "competições de quê?". O número consta da introdução de Chen & Guestrin (2016), a conferir na página 785. A frase removida repete o fim da Seção 3.3.5.
- Status: aplicável direto (o número 17/29 deve ser conferido no PDF pelo autor; os metadados da referência estão verificados).

### [Cap3 17]
- Local: T/capitulo3.tex:254, :256.
- Trecho atual:
```tex
desenvolvido pela Yandex, que incorpora inovações voltadas à robustez e à eficiência do treinamento.
Entretanto, difere em dois aspectos arquiteturais relevantes:
```
- Proposta:
```tex
desenvolvido pela Yandex, empresa russa de tecnologia conhecida por seu mecanismo de busca \citep{Prokhorenkova2018}, que incorpora inovações voltadas à robustez e à eficiência do treinamento.
Entretanto, sua arquitetura difere em dois aspectos relevantes:
```
- Justificativa: atende ao pedido literal da banca e acrescenta a citação primária.
- Status: aplicável direto.

### [Cap3 18]
- Local: T/capitulo3.tex:264.
- Trecho atual:
```tex
codificando-as internamente sem necessidade de \textit{one-hot encoding} --- e opções para lidar com desbalanceamento de classes
```
- Proposta:
```tex
codificando-as internamente sem necessidade de \textit{one-hot encoding} (codificação que substitui uma variável categórica com $c$ valores possíveis por $c$ colunas binárias, uma por categoria) --- e opções para lidar com desbalanceamento de classes
```
  Ao fim do parágrafo: "Neste trabalho, todas as \textit{features} são numéricas, de modo que o tratamento de variáveis categóricas não é utilizado."
- Justificativa: define o termo. O dataset tem 28 colunas numéricas (dataset_final.csv), então o recurso que dá nome ao CatBoost não é usado aqui.
- Status: aplicável direto.

### [Cap3 19]
- Local: T/capitulo3.tex:272, :274, :276, :278.
- Trecho atual:
```tex
apenas particiona os dados em \(k\) grupos de modo a minimizar
J = \sum_{i=1}^{k} \sum_{\vec{x} \in S_i} \|\vec{x} - \vec{\mu}_i\|^2,
Em aplicações em que \(k\) não é fixo, a inércia (WCSS) é frequentemente usada no \textbf{método do cotovelo} (gráfico de WCSS em função de \(k\))
índices como o de \textbf{Calinski-Harabasz} medem a razão entre dispersão inter e intra-cluster
Nesta dissertação, o K-means \textbf{não} é usado como classificador de curvas
No uso aqui, \(k=2\) e a variável é unidimensional (fluxo), o que simplifica a interpretação.
```
- Proposta:
```tex
apenas particiona os dados em \(K\) grupos de modo a minimizar
J = \sum_{i=1}^{K} \sum_{\vec{x} \in S_i} \|\vec{x} - \vec{\mu}_i\|^2,
Em aplicações em que \(K\) não é fixo, a inércia (WCSS) é frequentemente usada no \textbf{método do cotovelo} (gráfico de WCSS em função de \(K\))
índices como o de \textbf{Caliński--Harabasz}\footnote{Índice proposto por \citet{Calinski1974}: $CH(K) = \dfrac{\mathrm{tr}(B_K)/(K-1)}{\mathrm{tr}(W_K)/(n-K)}$, em que $B_K$ e $W_K$ são as matrizes de dispersão entre os grupos e dentro dos grupos, e $n$ é o número de pontos. Valores maiores indicam grupos mais compactos e mais bem separados.} medem a razão entre dispersão inter e intra-\textit{cluster}
Como mencionado na Seção~\ref{sec:fundamentos_ml}, os classificadores utilizados neste trabalho são supervisionados; o uso do K-means limita-se à etapa de extração de características numéricas das curvas de luz de ocultação. Assim, nesta dissertação, o K-means \textbf{não} é usado como classificador de curvas
No uso aqui, \(K=2\) e a variável é unidimensional (fluxo), o que simplifica a interpretação.
```
- Justificativa: atende à nota de rodapé pedida e resolve a aparente contradição supervisionado × não supervisionado. Resposta à banca: K e k eram a mesma coisa. Padronizo em \(K\) maiúsculo, coerente com o nome do método e com o Cap. 4, e libero \(k\) (ver item 25).
- Status: aplicável direto.

### [Cap3 20]
- Local: T/capitulo3.tex:294, :298 (Hessiana, BFGS), :305 (largura da tabela) e :311, :313 (linhas da tabela). Correções associadas: :123 e :292.
- Trecho atual:
```tex
O \textbf{método de Newton} utiliza o gradiente e a \textbf{Hessiana} da função de custo:
Variantes \textbf{quasi-Newton} (como BFGS) aproximam a Hessiana sem calculá-la explicitamente.
\begin{tabular}{@{}p{2.2cm}p{4.1cm}p{5.2cm}@{}}
Primeira ordem (iterativo) & Gradiente descendente (Batch, SGD, Mini-batch) & Regressão Logística, redes neurais, gradient boosting \\
Segunda ordem (iterativo) & Newton, quasi-Newton (BFGS), Taylor & XGBoost (Taylor da perda); otimização convexa em geral \\
O ajuste é realizado por gradiente descendente (veremos mais detalhes sobre os algoritmos de otimização na Seção~\ref{sec:otimizacao}).
Como vimos na Seção~\ref{sec:modelos_classificacao}, a Regressão Logística é ajustada por gradiente descendente;
```
- Proposta:
```tex
O \textbf{método de Newton} utiliza o gradiente e a \textbf{Hessiana}\footnote{Matriz das derivadas parciais de segunda ordem da função de custo, $H_{ij} = \partial^2 J / \partial\theta_i\,\partial\theta_j$, que descreve a curvatura local de $J$ \citep{Nocedal2006}.} da função de custo:
Variantes \textbf{quasi-Newton}, como o BFGS\footnote{Sigla de Broyden--Fletcher--Goldfarb--Shanno: o método atualiza, a cada iteração, uma aproximação de $H^{-1}$ usando apenas as variações sucessivas dos parâmetros e do gradiente \citep[cap.~6]{Nocedal2006}. Sua versão de memória limitada (L-BFGS) é o \textit{solver} padrão da Regressão Logística do \textit{scikit-learn}, usado nesta dissertação.}, aproximam a Hessiana sem calculá-la explicitamente.
\begin{tabular}{@{}p{3.0cm}p{4.8cm}p{6.2cm}@{}}
Primeira ordem (iterativo) & Gradiente descendente (\textit{Batch}, SGD, \textit{Mini-batch}) & Redes neurais; \textit{gradient boosting} (cada árvore ajustada ao gradiente da perda); exposição didática da Regressão Logística (Seção~\ref{sec:modelos_classificacao}) \\
Segunda ordem (iterativo) & Newton, quasi-Newton (BFGS, L-BFGS), Taylor & Regressão Logística desta dissertação (L-BFGS); XGBoost (Taylor da perda); otimização convexa em geral \\
O ajuste é iterativo. Descrevemos a seguir o gradiente descendente, por ser o esquema mais intuitivo; na implementação usada neste trabalho (\textit{scikit-learn}), o padrão é o método quasi-Newton L-BFGS (Seção~\ref{sec:otimizacao}).
A Regressão Logística pode ser ajustada por gradiente descendente (Seção~\ref{sec:modelos_classificacao}), embora o \textit{solver} padrão do \textit{scikit-learn}, usado neste trabalho, seja o L-BFGS;
```
- Justificativa: as notas pedidas pela banca e a tabela mais larga (14 cm, assumindo texto de ~16 cm em A4). Corrige ainda um erro de fato: o código não usa gradiente descendente, mas `solver='lbfgs'`, como também diz o Apêndice B.
- Status: aplicável direto (largura final a conferir na compilação).

### [Cap3 21]
- Local: T/capitulo3.tex:321.
- Trecho atual:
```tex
\section{Engenharia de características e validação de modelos}
```
- Proposta:
```tex
\section{Características dos dados e validação dos modelos}
```
- Justificativa: sugestão opcional da banca. "Engenharia de características" é tradução consagrada de *feature engineering* e também é aceitável; nesse caso, acrescentar "(\textit{feature engineering})".
- Status: requer confirmação do autor.

### [Cap3 22]
- Local: T/capitulo3.tex:336–339 (definições); fórmulas em :347, :356, :361, :366, :375. Uso no Cap. 5: capitulo5.tex:13.
- Trecho atual:
```tex
	\item \textbf{Verdadeiro Positivo (TP):} $\hat{y}_i = 1$ e $y_i = 1$ (acerto na classe positiva).
	\item \textbf{Verdadeiro Negativo (TN):} $\hat{y}_i = 0$ e $y_i = 0$ (acerto na classe negativa).
	\item \textbf{Falso Positivo (FP):} $\hat{y}_i = 1$ e $y_i = 0$ (alarme falso).
	\item \textbf{Falso Negativo (FN):} $\hat{y}_i = 0$ e $y_i = 1$ (evento perdido).
```
- Proposta:
```tex
	\item \textbf{Verdadeiro Positivo (VP; em inglês, \textit{True Positive}, TP):} $\hat{y}_i = 1$ e $y_i = 1$ (acerto na classe positiva).
	\item \textbf{Verdadeiro Negativo (VN; \textit{True Negative}, TN):} $\hat{y}_i = 0$ e $y_i = 0$ (acerto na classe negativa).
	\item \textbf{Falso Positivo (FP; \textit{False Positive}):} $\hat{y}_i = 1$ e $y_i = 0$ (alarme falso).
	\item \textbf{Falso Negativo (FN; \textit{False Negative}):} $\hat{y}_i = 0$ e $y_i = 1$ (evento perdido).
```
  Nas fórmulas: TP → VP e TN → VN (por exemplo, `\frac{2\,VP}{2\,VP + FP + FN}` em :366 e `$FP/(FP+VN)$` em :375). FP e FN valem nas duas línguas.
- Justificativa: atende à banca com o mínimo de mudanças, pois FP/FN não mudam. As matrizes de confusão (figuras) vêm do código sem siglas, só "Negativa/Positiva" (train_model.py:645-646), e não precisam ser refeitas.
- Status: decisão autor+orientador (convém padronizar em toda a tese, inclusive capitulo5.tex:13).

### [Cap3 23.1]
- Local: T/capitulo3.tex:380 + :384 (Fig. 3.8); mesmo mecanismo em :422 + :426 (Fig. 3.9) e :436 + :440 (Fig. 3.10).
- Trecho atual:
```tex
Fonte: adaptado de \emph{Ciência e Negócios}\protect\footnotemark.}
\footnotetext{Disponível em: \url{https://cienciaenegocios.com/curva-roc-e-auc-em-machine-learning}. Acesso em: 6 abr. 2026.}
```
- Proposta (Fig. 3.8; legenda só descritiva, e a analogia médica vai para o texto em :375):
```tex
\caption[Exemplos de curvas ROC]{Exemplos de curvas ROC para classificadores de diferentes qualidades; a diagonal corresponde a um classificador aleatório (AUC = 0,5). Fonte: adaptado de Ciência e Negócios. Disponível em: \url{https://cienciaenegocios.com/curva-roc-e-auc-em-machine-learning}. Acesso em: 6 abr. 2026.}
```
  Remover o `\footnotetext{...}` de :384. Em :375, depois de "como mostrado na imagem \ref{fig:roc_auc}", inserir: "(Figura~\ref{fig:roc_auc}). Um exemplo intuitivo é um teste médico: a taxa de verdadeiros positivos é a fração de doentes corretamente identificados, a taxa de falsos positivos é a fração de saudáveis apontados como doentes, e variar o limiar move o teste ao longo da curva." Fazer o mesmo nas Figs. 3.9 e 3.10.
- Justificativa: `\footnotemark` dentro de um *float* com `\footnotetext` fora dele quebra quando o *float* muda de página, que é o defeito apontado. A fonte com URL na própria legenda (padrão ABNT de "Fonte:") elimina o problema, e o título curto em `\caption[...]` mantém limpa a Lista de Figuras.
- Status: aplicável direto.

### [Cap3 23.2]
- Local: T/capitulo3.tex:395, :400 (viés–variância), :38, :47, :49 (classificador \(f\)). Conflitos fora do capítulo: capitulo2.tex:77, :86-89 (escala de Fresnel \(f\)) e capitulo5.tex:90 (\(f\) = vetor de fluxo).
- Trecho atual:
```tex
Formalmente, para um modelo $\hat{f}$ treinado em diferentes amostras do mesmo processo gerador
onde $\text{Viés}^2[\hat{f}] = \left(\mathbb{E}[\hat{f}(\vec{x})] - f(\vec{x})\right)^2$ mede o erro sistemático do modelo
```
- Proposta (mapa de notação; mudanças mínimas):
```tex
Formalmente, seja $f^\star(\vec{x})$ a relação verdadeira (desconhecida) entre entrada e saída e $\hat{f}$ o modelo --- a função $f$ da Seção~\ref{sec:problema_classificacao} --- estimado a partir de diferentes amostras de treino do mesmo processo gerador; o erro quadrático médio esperado em um ponto $\vec{x}$ é:
onde $\text{Viés}^2[\hat{f}] = \left(\mathbb{E}[\hat{f}(\vec{x})] - f^\star(\vec{x})\right)^2$ mede o erro sistemático do modelo
```
  Na Eq.~\eqref{eq:bias_variance}, o \(y\) é \(y = f^\star(\vec x) + \varepsilon\), com \(\mathrm{Var}(\varepsilon)=\sigma^2\); dizer isso explicitamente. Fora do Cap. 3 (coordenar com o revisor desses capítulos): escala de Fresnel \(f \to \ell_F\) no Cap. 2; vetor de fluxo \(f, \tilde f, f', f''\) → \(F, \tilde F, F', F''\) no Cap. 5 (capitulo5.tex:49-85, :90, Tab. 5.1), coerente com \(F(t)\) do Cap. 4.
- Justificativa: em todo o Cap. 3, \(f\) passa a significar uma única coisa (o classificador); \(f^\star\) é a verdade e \(\hat f\) a estimativa. No restante da tese, cada símbolo fica com um só significado (comentário geral m).
- Status: decisão autor+orientador (notação global).

### [Cap3 23.3]
- Local: T/capitulo3.tex:408 (fim) + :410.
- Trecho atual:
```tex
Na \textit{pipeline} desta dissertação, as features não são padronizadas antes de todos os treinos (Capítulo 4); a justificativa é discutida naquele capítulo.
```
- Proposta (apagar a linha 410 e anexar ao fim do parágrafo 408):
```tex
No entanto, nesta dissertação a padronização é aplicada apenas à Regressão Logística; os modelos baseados em árvores recebem as \textit{features} na escala original, pois são insensíveis a transformações monotônicas de cada variável (Capítulo~4).
```
- Justificativa: junta as frases com "No entanto", como pede a banca, e desfaz a ambiguidade de "não são padronizadas antes de todos os treinos". O código confirma: `StandardScaler` só na RegLog (train_model.py:1249-1251).
- Status: aplicável direto.

### [Cap3 24]
- Local: T/capitulo3.tex:417 (texto), :422 (legenda) e :426 (rodapé).
- Trecho atual:
```tex
A Figura~\ref{fig:learning_curves} ilustra o conceito com curvas de aprendizado reais de três classificadores (XGBoost, Random Forest e Árvore de Decisão) em uma tarefa de classificação.
Um modelo bem ajustado é aquele cujas duas curvas convergem para um patamar alto com vão pequeno.
```
- Proposta:
```tex
A Figura~\ref{fig:learning_curves} ilustra o conceito com curvas de aprendizado de seis classificadores --- (A)~XGBoost, (B)~\textit{Random Forest}, (C)~árvore de decisão, (D)~\textit{Extra Trees}, (E)~\textit{Naive Bayes} gaussiano e (F)~Regressão Logística --- aplicados a um problema de classificação em medicina \citep{Zhong2023}.
Um modelo bem ajustado é aquele cujas duas curvas convergem para um patamar alto com vão pequeno; na figura, é o caso do XGBoost (painel A), cujas curvas convergem para $\approx 0{,}96$. Os painéis E e F ilustram o subajuste: as curvas se encontram, mas num patamar baixo ($\approx 0{,}67$ e $\approx 0{,}74$). Com poucos exemplos de treino, todos os modelos mostram o vão largo típico do sobreajuste.
```
  Na legenda (:422), trocar "para três classificadores: (A)~XGBoost, (B)~Random Forest e (C)~Árvore de Decisão" pela lista de seis painéis, e "Fonte: adaptado de \emph{ResearchGate}" por "Fonte: \citet{Zhong2023}", com o mesmo tratamento do item 23.1 para o rodapé.
- Justificativa: responde "qual painel é o bem ajustado?" pela leitura direta da imagem (abri o PNG). Corrige também um erro factual: a figura tem seis painéis, não três. A fonte primária é Zhong et al. (2023), cujos metadados conferi no Crossref. O número da figura no artigo está a verificar (o identificador "fig2" do ResearchGate sugere a Fig. 2). A tradução ou substituição da figura fica com o autor (item excluído).
- Status: aplicável direto (texto e citação); o número da figura no artigo deve ser confirmado pelo autor.

### [Cap3 25]
- Local: T/capitulo3.tex:431, :436, :448; Cap. 5: capitulo5.tex:652, :656, :661.
- Trecho atual:
```tex
roda-se o experimento $k$ vezes, cada vez deixando uma fatia diferente de fora. A média dos $k$ resultados
\caption{Esquema da validação cruzada com $k=5$:
\item \textbf{Validação cruzada (k-fold):} os dados são divididos em \(k\) partes (dobras); em cada rodada, \(k-1\) dobras são usadas para treino e uma para validação; a métrica final é a média sobre as \(k\) rodadas.
```
- Proposta:
```tex
roda-se o experimento $q$ vezes, cada vez deixando uma fatia diferente de fora (Figura~\ref{fig:kfold}). A média dos $q$ resultados
\caption{Esquema da validação cruzada com $q = 5$ dobras:
\item \textbf{Validação cruzada em $q$ dobras} (em inglês, \textit{k-fold cross-validation}): os dados são divididos em \(q\) partes (dobras); em cada rodada, \(q-1\) dobras são usadas para treino e uma para validação; a métrica final é a média sobre as \(q\) rodadas.
```
  No Cap. 5: "validação cruzada com $k=5$ dobras" → "com $q=5$ dobras" (:652) e "($k=5$)" → "($q=5$)" (:661).
- Justificativa: menciona a Fig. 3.10 no primeiro parágrafo. \(K\) fica reservado para o K-means (item 19) e \(q\) para o número de dobras; o nome do método em inglês é mantido.
- Status: aplicável direto.

### [Cap3 26]
- Local: T/capitulo3.tex:318 (último parágrafo da 3.5) → fim da 3.6 (após :453).
- Trecho atual:
```tex
Com isso, o leitor dispõe de uma referência clara sobre o significado das "contas" envolvidas no treinamento de modelos de aprendizado de máquina.
a divisão treino/teste é feita de forma estratificada (mantendo a proporção de positivas e negativas em cada parte) ou por seleção manual de curvas para o teste.
Com isso, o capítulo fornece a base conceitual necessária para interpretar a metodologia e os resultados descritos no Capítulo 4.
```
- Proposta: remover o parágrafo de :318; em :453, trocar "ou por seleção manual de curvas para o teste" por "(a seleção manual de curvas de teste está implementada no código, mas não foi usada nos experimentos)" e fechar o capítulo com:
```tex
Em resumo, este capítulo apresentou o problema de classificação supervisionada e os quatro classificadores usados na \textit{pipeline} --- Regressão Logística, \textit{Random Forest}, XGBoost e CatBoost ---, além do K-means, empregado apenas como extrator de uma característica numérica. Mostrou também como o treinamento se reduz à minimização de uma função de custo: por solução fechada (mínimos quadrados), por métodos de primeira ordem (gradiente descendente) ou de segunda ordem (L-BFGS, na Regressão Logística deste trabalho; aproximação de Taylor de segunda ordem, no XGBoost). Por fim, apresentou as métricas e os procedimentos de validação usados para medir a generalização. Esses conceitos são a base para a metodologia (Capítulo~4) e os resultados (Capítulo~5).
```
- Justificativa: o capítulo passa a fechar em sua última seção, como pede a banca. O fecho corrige o "gradiente descendente" e a referência a "Capítulo 4" para os resultados (que estão no Cap. 5). A seleção manual nunca foi usada: `TEST_CURVES = None` em train_model.py:1366.
- Status: aplicável direto.

---------------------------------------------------------------------
## CAPÍTULO 5
---------------------------------------------------------------------

### [Cap5 1] Renomear os experimentos
- Fatos (cada pasta de `O/` conferida pelo `feature_names.pkl` e pelo md5 dos CSVs):

| Nome atual | Pasta em O/ (ordem de execução) | Figuras em T/pngs/ | Nº real de features | Conteúdo |
|---|---|---|---|---|
| Exp 1 | resultado1_split0.8-0.2_all-features | exp1 | 28 | completo |
| Exp 4 | resultado2_split0.8-0.2_less_features | exp2 | **13** (tese diz 14) | as 13 da Tabela "final" (tab:features_final) |
| Exp 5 | resultado3_..._noMin | exp3 | **12** (tese diz 13) | 13 − Savgol_Min |
| Exp 6 | resultado4_..._noKmeans | exp4 | 12 | 13 − kmeans (**mantém** Savgol_Min; apêndice:77 diz o contrário) |
| Exp 2 | resultado5_..._noMin-noKmeans | exp5 | 11 | 13 − ambas |
| — | resultado6.1_split0.65-0.35_... | exp6 | 11 | **cópia idêntica de resultado5** (md5 igual); NÃO é 65/35 |
| variante 65/35 do Exp 3 | resultado6.2_applyTestOnlyRealCurves | exp7 | 11 | teste só reais 65/35 (347 = 281 + 66) |
| Exp 3 | **sem pasta** | **sem figura** | 11 | teste só reais 80/20 (198 = 160 + 38); reproduzido exatamente com SP/repro_exp.py |

- Proposta de esquema (segue a sugestão da banca: preserva a ordem de execução e mantém os números 1, 2 e 3 do texto; muda só os três intermediários e a variante):

| Novo nome | Antigo | Features | Teste |
|---|---|---|---|
| Experimento 1 | Exp 1 | 28 | misto 80/20 |
| Experimento 1.1 | Exp 4 | 13 | misto 80/20 |
| Experimento 1.2a | Exp 5 | 12 (1.1 − Savgol_Min) | misto 80/20 |
| Experimento 1.2b | Exp 6 | 12 (1.1 − kmeans) | misto 80/20 |
| Experimento 2 | Exp 2 | 11 (1.1 − ambas) | misto 80/20 |
| Experimento 3 | Exp 3 | 11 | só reais 80/20 |
| Experimento 3.1 | variante 65/35 | 11 | só reais 65/35 |

  Tabela LaTeX para o Apêndice A (início do apêndice; resolve também o item 8.3):
```tex
\begin{table}[htbp]
\centering
\small
\caption{Correspondência entre os experimentos, os conjuntos de \textit{features}, a divisão treino/teste e os diretórios de saída do código.}
\label{tab:mapa_experimentos}
\begin{tabular}{@{}llccl@{}}
\hline
\textbf{Experimento} & \textbf{Conjunto de \textit{features}} & \textbf{Nº} & \textbf{Teste} & \textbf{Diretório em \texttt{outputs/}} \\
\hline
1    & completo (Tabela~\ref{tab:features_completo})                & 28 & misto 80/20     & \texttt{resultado1\_*} \\
1.1  & sem as 15 redundantes (Tabela~\ref{tab:features_final})      & 13 & misto 80/20     & \texttt{resultado2\_*} \\
1.2a & 1.1 sem \texttt{Feature\_Savgol\_Min}                        & 12 & misto 80/20     & \texttt{resultado3\_*} \\
1.2b & 1.1 sem \texttt{kmeans\_centroid\_dist}                      & 12 & misto 80/20     & \texttt{resultado4\_*} \\
2    & 1.1 sem as duas anteriores                                   & 11 & misto 80/20     & \texttt{resultado5\_*} \\
3    & igual ao 2                                                   & 11 & só reais 80/20  & (a arquivar) \\
3.1  & igual ao 2                                                   & 11 & só reais 65/35  & \texttt{resultado6.2\_*} \\
\hline
\end{tabular}
\end{table}
```
- Linhas a alterar (renomear 4 → 1.1, 5 → 1.2a, 6 → 1.2b e "variante 65/35 do Exp 3" → "Experimento 3.1"; e, nas mesmas linhas, corrigir 14 → 13 e 13 → 12):
  - **capitulo5.tex**: :25 (reescrever: "a redução para 13 (Experimento~1.1) e 12 variáveis (Experimentos~1.2a e 1.2b)…"), :116, :268 (reescrever; ver abaixo), :270, :387, :391, :414, :419, :427, :550 (legenda), :555 e :556 (cabeçalho "14 f." → "13 f.", "13 f." → "12 f."), :570, :572, :574, :636, :656, :661, :688, :693, :741 ("Experimentos 1 (28) e 1.1 (13)"); legenda de `tab:features_final` (:119–131): "(Experimento~1.1)".
  - **capitulo6.tex**: :11 e :33 ("13--14" → "11--13"), :13 ("Experimento~6" → "Experimento~1.2b").
  - **apendice_experimentos.tex**: :7, :10, :13 (lista de remoções: incluir `Occ\_n\_frames\_below\_baseline`: são três métricas observacionais, não duas), :17, :31, :36, :42, :45, :49, :63, :68, :74, :77 ("as 13 do Experimento~1.1 sem `kmeans\_centroid\_dist`; `Feature\_Savgol\_Min` permanece"), :81, :95, :100, :105, :109, :113, :136, :139, :143, :157, :162, :170, :179, :184, :192, :200, :214, :217, :221, :246, :252, :277.
  - **capitulo3.tex**: :45 (ver Cap3 4).
  - **Código e arquivos** (não é texto, mas evita a confusão do item 8.3): renomear as pastas de `O/` para `exp1_28f`, `exp1.1_13f`, `exp1.2a_12f_noSGmin`, `exp1.2b_12f_noKmeans`, `exp2_11f`, `exp3_11f_real80-20` (arquivar o run), `exp3.1_11f_real65-35`; apagar `resultado6.1` (duplicata) e `pngs/exp6` (não usado em nenhum .tex); atualizar `MODEL_DIR` em test_quaoar.py:34-36, test_quaoar_recortes.py:36-39 e test_low_snr.py:46-49.
  - Reescrita de capitulo5.tex:268:
```tex
Partindo das 28 \textit{features} do Experimento~1, o conjunto de variáveis foi reduzido em etapas. O Experimento~1.1 (13 \textit{features}) elimina de uma só vez as 15 variáveis redundantes da Seção~\ref{sec:features_redundancia}. Os Experimentos~1.2a e 1.2b (12 \textit{features} cada) removem, além delas, respectivamente \texttt{Feature\_Savgol\_Min} e \texttt{kmeans\_centroid\_dist}. O Experimento~2 (11 \textit{features}) remove ambas.
```
- Justificativa: a numeração atual não segue a ordem de execução (banca). Além disso, as contagens de dois experimentos estão erradas e o Exp 6 é descrito ao contrário. O "Exp 2" atual NÃO difere do Exp 6 por "remover simultaneamente as duas": o Exp 6 já não tem kmeans, e o Exp 2 tira Savgol_Min dele. Com o esquema 1.x, isso fica explícito.
- Status: decisão autor+orientador.

### [Cap5 2]
- Local: T/capitulo5.tex:20.
- Trecho atual:
```tex
\item \textbf{Experimento 1:} conjunto completo de 28 \textit{features}, divisão 80\%/20\%.
```
- Proposta:
```tex
\item \textbf{Experimento 1:} conjunto completo de 28 \textit{features} (Tabela~\ref{tab:features_completo}), divisão 80\%/20\%.
```
- Justificativa: pedido literal da banca.
- Status: aplicável direto.

### [Cap5 3]
- Local: T/capitulo5.tex:153. Correções associadas na mesma seção: :155, :157, :159, :163 e Tab. 5.2 (:193).
- Trecho atual:
```tex
Uma limitação conhecida do MDI é o viés em favor de variáveis contínuas de alta cardinalidade, que oferecem mais candidatos para \textit{split}.
\subsection{XGBoost --- \textit{Weight} (contagem de \textit{splits})}
o atributo \texttt{feature\_importances\_} retorna, por padrão, a métrica \textbf{\textit{weight}}
calcula-se a mudança média no valor de predição do modelo quando os valores de $x_j$ são permutados aleatoriamente.
XGBoost & \textit{Weight} (contagem de \textit{splits}) & $\sum = 1$ & 0 a $\approx$0,15 \\
```
- Proposta:
```tex
Uma limitação conhecida do MDI é o viés em favor de variáveis contínuas ou com muitas categorias, que oferecem mais pontos de corte candidatos, e de variáveis correlacionadas \citep{Strobl2007}.
\subsection{XGBoost --- \textit{Gain} (redução média da perda)}
o atributo \texttt{feature\_importances\_} retorna, por padrão (para árvores), a métrica \textbf{\textit{gain}}: para cada \textit{feature} $x_j$, a redução média da função de perda obtida nos \textit{splits} que usam $x_j$, normalizada para somar~1. A métrica \textit{weight} (número de \textit{splits}) e a \textit{cover} (número médio de amostras afetadas) são alternativas disponíveis; neste trabalho, utilizou-se o padrão \textit{gain}.
mede-se o quanto, em média, a predição muda quando o valor de $x_j$ muda, ponderando as diferenças entre os valores das folhas das árvores pelo número de exemplos em cada folha. O cálculo é feito a partir da estrutura das árvores e não envolve permutação; a variante baseada na perda chama-se \textit{LossFunctionChange}.
XGBoost & \textit{Gain} (redução média da perda) & $\sum = 1$ & 0 a $\approx$0,7 \\
```
- Justificativa: a referência pedida pela banca é Strobl et al. (2007), com metadados verificados. Na mesma seção há dois erros de fato:
  - O XGBoost salvo (`O/resultado5/xgboost_model.pkl`, `importance_type=None`) devolve *gain*. Para `Feature_Savgol_std`: `feature_importances_` = 0,566 = gain normalizado; por *weight* seria 0,085, e a feature de topo seria `Occ_duration_s` (0,166). Os valores 0,57–0,69 citados no texto são de gain, não cabem na escala "0 a 0,15" da tabela, e a interpretação "frequência de uso" está errada.
  - A *PredictionValuesChange* não usa permutação. O Cap. 3 (:266) a descreve corretamente, e o Cap. 5 a contradiz.
- Status: Strobl aplicável direto; a correção de gain e da PVC também (verificada no modelo salvo). A descrição da PVC deve ser conferida pelo autor na documentação do CatBoost (https://catboost.ai/docs/en/concepts/fstr — URL a verificar).

### [Cap5 4]
- Local: T/capitulo5.tex:254.
- Trecho atual:
```tex
A Figura~\ref{fig:confusao_1} apresenta as matrizes de confusão dos quatro modelos no Experimento 1.
```
- Proposta:
```tex
A Figura~\ref{fig:confusao_1} apresenta as matrizes de confusão dos quatro modelos no Experimento~1. Em cada matriz, as linhas indicam a classe real e as colunas a classe predita. A diagonal principal contém os acertos: verdadeiros negativos no canto superior esquerdo e verdadeiros positivos no canto inferior direito. Fora da diagonal ficam os erros: falsos positivos (superior direito) e falsos negativos (inferior esquerdo). Por exemplo, o \textit{Random Forest} classifica corretamente as 179 curvas negativas e 158 das 160 positivas, com 2 falsos negativos e nenhum falso positivo.
```
- Justificativa: atende ao pedido da banca com um exemplo numérico. Os números foram conferidos: RF no Exp 1 tem precisão 1,0 e sensibilidade 0,9875 = 158/160, num teste de 160 positivas e 179 negativas (O/resultado1/predictions_*.csv).
- Status: aplicável direto.

### [Cap5 5]
- Local: T/capitulo5.tex:299, :303–304, :324.
- Trecho atual:
```tex
\subsection{Motivação}
\subsection{Resultados do Experimento 3}
\subsection{Interpretação}
```
- Proposta: apagar as três linhas `\subsection{...}` da Seção 5.7 e o `\label{sec:resultados_exp7}`, que não é referenciado em lugar nenhum (grep). Na transição para a tabela, escrever "Os resultados estão na Tabela~\ref{tab:metricas_7}." Atenção: as linhas :447 e :529 também têm `\subsection{Motivação}` e `\subsection{Interpretação}`, mas pertencem à Seção 5.9 e devem ficar.
- Justificativa: a seção é curta (banca).
- Status: aplicável direto.

### [Cap5 6]
- Local: T/capitulo5.tex:419 (legenda da Fig. 5.2).
- Trecho atual:
```tex
Cada ponto da curva corresponde a um valor de limiar $\tau$: variando $\tau$ de 1 a 0, percorre-se a curva da esquerda (alta precisão, baixa sensibilidade) para a direita (alta sensibilidade, menor precisão).
```
- Proposta (legenda descritiva; a interpretação vai para o texto em :414):
```tex
\caption{Curvas precisão-sensibilidade dos quatro modelos no Experimento~1.2a. Cada posição ao longo de uma curva corresponde a um valor do limiar $\tau$. No gráfico, ``revocação'' é sinônimo de sensibilidade (\textit{recall}).}
```
  Em :414, acrescentar: "Variando $\tau$ de 1 a 0, percorre-se cada curva da esquerda (alta precisão, baixa sensibilidade) para a direita (alta sensibilidade, menor precisão); quanto mais a curva se aproxima do canto superior direito, melhor o modelo."
- Justificativa: não são pontos, é uma linha. "Revocação" vem do título e do eixo gerados pelo código (P/model_training/train_model.py:847-849, `'Revocação (Recall)'` e `'Curva Precisão-Revocação'`). Enquanto a imagem não for refeita (o inset e o título estão excluídos), a legenda explica a sinonímia. Ao regenerar, trocar no código por "Sensibilidade".
- Status: aplicável direto (texto); a imagem fica com o autor.

### [Cap5 7]
- Local: T/capitulo5.tex:379 (custos); :424–430 (Fig. 5.3).
- Trecho atual:
```tex
\textbf{Análise de custo:} atribuir custos explícitos $c_{\text{FN}}$ e $c_{\text{FP}}$ e minimizar o custo esperado total.
	\includegraphics[width=0.75\linewidth]{Tese/pngs/exp3/metrics_vs_threshold_1.png}
```
- Proposta:
```tex
\textbf{Análise de custo:} atribuir um custo $c_{\text{FN}}$ a cada falso negativo (evento perdido) e um custo $c_{\text{FP}}$ a cada falso positivo (alarme a ser revisado) e escolher $\tau$ que minimize o custo total $C(\tau) = c_{\text{FN}}\,\mathrm{FN}(\tau) + c_{\text{FP}}\,\mathrm{FP}(\tau)$. Se as probabilidades forem bem calibradas, o limiar ótimo é $\tau^\star = c_{\text{FP}}/(c_{\text{FP}} + c_{\text{FN}})$; por exemplo, $c_{\text{FN}} = 9\,c_{\text{FP}}$ dá $\tau^\star = 0{,}1$. Quando $c_{\text{FN}} \gg c_{\text{FP}}$, o limiar ótimo desloca-se para baixo.
```
  Figura (os dois arquivos já existem em T/pngs/exp3/):
```tex
\begin{figure}[htbp]
\centering
\begin{minipage}[t]{0.49\textwidth}\centering
	\includegraphics[width=\linewidth]{Tese/pngs/exp3/metrics_vs_threshold_1.png}\\ \small (a) \textit{Random Forest} e XGBoost
\end{minipage}\hfill
\begin{minipage}[t]{0.49\textwidth}\centering
	\includegraphics[width=\linewidth]{Tese/pngs/exp3/metrics_vs_threshold_2.png}\\ \small (b) CatBoost e Regressão Logística
\end{minipage}
\caption{Precisão, sensibilidade, F1-score e F$_2$-score em função do limiar de decisão $\tau$ (Experimento~1.2a). (a)~\textit{Random Forest} e XGBoost; (b)~CatBoost e Regressão Logística.}
\label{fig:metrics_vs_threshold}
\end{figure}
```
- Justificativa: define os símbolos pedidos e dá a regra de decisão de Bayes, que liga a escolha de τ à razão de custos. Resposta à pergunta "por que só dois modelos?": o código grava duas figuras de dois modelos cada (train_model.py:861-890: `_1` = RF + XGB, `_2` = CatBoost + RegLog) e a tese incluiu só a `_1`. A `_2` já existe, então incluí-la não exige regenerar nada.
- Status: aplicável direto.

### [Cap5 8] (Seção 5.9, estudo de caso de Quaoar)
- Local e trechos atuais:
```tex
\item Verificar se o modelo treinado generaliza para curvas reais \textbf{nunca vistas}
são removidos por um clip físico no intervalo $[-2,\ 5]$
um dicionário \texttt{CUT\_RANGES} permite restringir cada curva a um intervalo $(t_{\mathrm{início}},\ t_{\mathrm{fim}})$ em segundos UTC.
extraindo apenas a coluna de tempo (segundos UTC)
é carregado a partir do diretório \texttt{outputs/resultado5}; o \textit{imputer} é recuperado
um trecho de ruído visualmente parecido com uma micrococultação, adjacente ao Q2R.
A inferência foi aplicada a cada janela com os modelos CatBoost e XGBoost do Experimento~2.
```
  (capitulo5.tex:453, :465, :466, :465, :468, :488, :488)
- Proposta:
```tex
\item Verificar se o modelo CatBoost do Experimento~2 (11 \textit{features}; na análise de recortes, também o XGBoost do mesmo experimento) generaliza para curvas reais \textbf{nunca vistas}
são descartados por um filtro de validade física: mantêm-se apenas os pontos com fluxo normalizado no intervalo $[-2,\ 5]$
um dicionário \texttt{CUT\_RANGES}, preenchido manualmente pelo autor a partir da inspeção visual da curva e das posições dos anéis publicadas por \citet{Morgado2023} e \citet{Quaoar2023}, permite restringir cada curva a um intervalo $(t_{\mathrm{início}},\ t_{\mathrm{fim}})$, em segundos contados a partir de 00:00:00~UTC de 2022-08-09 (segundos do dia).
extraindo apenas a coluna de tempo (segundos do dia, em UTC)
é carregado a partir do diretório \texttt{outputs/resultado5} (correspondência na Tabela~\ref{tab:mapa_experimentos}); o \textit{imputer} --- objeto \texttt{SimpleImputer} do \textit{scikit-learn}, ajustado no treino, que substitui valores ausentes de uma \textit{feature} pela mediana do conjunto de treino --- é recuperado
um trecho curto de ruído que se assemelha visualmente a uma ocultação, adjacente ao Q2R (janelas destacadas na Figura~\ref{fig:quaoar_recortes}).
A inferência foi aplicada a cada janela com os modelos CatBoost (o modelo de referência da Seção~\ref{sec:estudo_caso_quaoar}) e XGBoost do Experimento~2; o \textit{Random Forest} e a Regressão Logística não foram avaliados nos recortes.
```
  No início da 5.9 (após :449), acrescentar: "Foram analisadas três curvas do mesmo evento: CFHT/WIRCam (banda $K_s$) e Gemini-Norte/`Alopeke, nos canais azul (filtro $r$) e vermelho (filtro $z$)." Corrigir também a legenda (:520): "filtro $z$ (visível-vermelho)" → "filtro $z$ (infravermelho próximo, $\approx$0,9~$\mu$m)".
- Justificativa (bullet a bullet):
  - "Clip": o código remove os pontos por máscara (P/model_in_practice/test_quaoar_recortes.py:109-110; test_quaoar.py:106), não satura os valores.
  - `CUT_RANGES` / `RECORTES`: são valores digitados no código (test_quaoar.py:66; test_quaoar_recortes.py:64-86). As janelas não são cegas: foram escolhidas sabendo onde estão os anéis, e isso deve ser dito. Cito também Morgado et al. 2023 (Q1R), em linha com o comentário geral (f).
  - Tempo: a coluna 4 do .dat do PRAIA é "segundos UTC do dia" (test_quaoar.py:46-50). A época que a banca sugere, "06:35:49,26", tem um erro de digitação: a tese e o código usam 06:34:49,26 (test_quaoar_recortes.py:48; capitulo5.tex:478, :492), e só os eixos dos gráficos e a tabela usam tempo relativo.
  - "micrococultação" não é termo da área.
  - Só XGB e CatBoost: test_quaoar.py carrega apenas o CatBoost (:211-214) e test_quaoar_recortes.py apenas o XGBoost (:203). O XGBoost foi acrescentado depois, por dar probabilidades mais polarizadas; isso deve constar.
  - Três curvas: os arquivos estão em test_quaoar.py:40-43, mas só a Red-z tem números na tese.
- Status: aplicável direto, exceto rodar RF e RegLog nos recortes e tabelar as curvas CFHT e Blue-r, o que requer o autor (o .dat de Quaoar não está no repositório).

### [Cap5 9]
- Local: T/capitulo5.tex:326 e :576 (também T/apendice_experimentos.tex:139, :157).
- Trecho atual:
```tex
Vale registrar que a queda de $\approx$2 pontos percentuais observada na variante 65\%/35\% (Apêndice~\ref{ap:experimentos}) decorre, em parte, da redução do conjunto de treino, e não apenas da composição do teste.
A queda de $\approx$2~pp observada na variante 65/35 (Apêndice~\ref{ap:experimentos}) decorre, em parte, da redução do conjunto de treino.
```
- Proposta:
```tex
No Experimento~3.1 (divisão 65\%/35\%; Apêndice~\ref{ap:experimentos}), o melhor F1 passa de 0,9906 para 0,9838, uma diferença de 0,7 ponto percentual (pp). Como essa variante altera ao mesmo tempo o treino ($-19\,\%$ das curvas reais de treino, ou $-10\,\%$ do treino total) e o conjunto de teste (198 $\to$ 347 curvas), não é possível atribuir a diferença à redução do treino: trata-se de uma hipótese, não de um resultado. A diferença tem, de todo modo, a mesma ordem da flutuação entre partições (desvio padrão do F1 na validação cruzada de 0,006 a 0,010; Tabela~\ref{tab:cross_validation}).
A queda de 0,7~pp no Experimento~3.1 (Apêndice~\ref{ap:experimentos}) é compatível com a flutuação entre partições.
```
  No apêndice, :139 e :157: "Ao remover cerca de 15\% dos dados de treinamento" e "com 15\% menos dados de treino" → "com 19\% menos curvas reais de treino (10\% menos dados de treino no total)".
- Justificativa: a sugestão da banca conflita com o dado. O número correto é **0,7 pp**, e não ≈2 pp: o próprio apêndice (:157) dá 0,9906 → 0,9838, que reproduzi bit a bit com SP/repro_exp.py. O "2 pp" é resquício do run antigo. Respondendo à pergunta da banca: é hipótese, porque o desenho muda treino e teste ao mesmo tempo. As contagens de treino conferem no código (1494 → 1345 amostras, das quais 792 → 643 reais). Defino "pp" na primeira ocorrência.
- Status: aplicável direto.

### [Cap5 10]
- Local: T/capitulo5.tex:605 (figura `fig:feature_importance_enxuto`), citada em :594.
- Trecho atual:
```tex
\begin{figure}[p]
```
- Proposta: trocar por `\begin{figure}[!htbp]` e mover o bloco :605–634 para logo após o parágrafo de :594, antes da lista `itemize` de :598.
- Justificativa: com `[p]`, o LaTeX manda a figura para uma página só de *floats*, longe da menção. A melhoria de fonte e a tradução estão excluídas (ficam com o autor).
- Status: aplicável direto.

### [Cap5 11]
- Local: T/capitulo5.tex:663–672 (Tab. 5.10) e :675.
- Resposta factual: a Tabela 5.10 do .tex atual **já traz** o desvio padrão do F1 em cada linha (CatBoost 0,9868 ± 0,0072; XGBoost 0,9856 ± 0,0062; Reg. Log. 0,9836 ± 0,0104; RF 0,9831 ± 0,0072). Os valores conferem com O/resultado3/cross_validation_summary.csv (Experimento 1.2a, 12 features). Provavelmente a banca leu uma versão anterior. O que falta é o texto usar esse número, já que hoje há só uma frase-molde condicional.
- Trecho atual:
```tex
Se o desvio padrão do F1 for pequeno (e.g., $< 0{,}01$), isso reforça a conclusão de que o desempenho é robusto; se for grande, pode indicar sensibilidade à composição do conjunto de teste.
```
- Proposta:
```tex
O desvio padrão do F1 entre as dobras vai de 0,0062 (XGBoost) a 0,0104 (Regressão Logística) (Tabela~\ref{tab:cross_validation}). As diferenças entre as médias dos quatro modelos (no máximo 0,0037) são menores que um desvio padrão; a validação cruzada, portanto, não distingue os classificadores, o que é coerente com o teste de McNemar (Seção~\ref{sec:mcnemar}).
```
- Justificativa: substitui a frase-molde condicional pelo número de fato (máxima diferença entre médias: 0,9868 − 0,9831 = 0,0037).
- Status: aplicável direto.

---------------------------------------------------------------------
## CAPÍTULO 6
---------------------------------------------------------------------

### [Cap6 i]
- Local: T/capitulo6.tex:11 e T/capitulo5.tex:121–131 (a tabela citada tem o label quebrado).
- Trecho atual:
```tex
A redução de 28 para 13--14 \textit{features} (remoção de variáveis redundantes) não degradou o desempenho
\begin{tabular}{lp{8.6cm}}
\label{tab:features_final}
```
- Proposta (Cap. 6):
```tex
A redução de 28 (Tabela~\ref{tab:features_completo}) para 11--13 \textit{features} (Tabela~\ref{tab:features_final}), com a remoção de variáveis redundantes, não degradou o desempenho
```
  Proposta (capitulo5.tex:121–131; hoje o `\label` está dentro de um `tabular` sem `table` e sem `\caption`, então o `\ref` imprime um número de seção e a tabela não entra na Lista de Tabelas):
```tex
\begin{table}[htbp]
\centering
\caption{Conjunto de 13 \textit{features} após a análise de redundância (Experimento~1.1). O conjunto de referência operacional (Experimento~2) remove ainda \texttt{Feature\_Savgol\_Min} e \texttt{kmeans\_centroid\_dist}, restando 11.}
\label{tab:features_final}
\begin{tabular}{lp{8.6cm}}
\hline
\textbf{Família} & \textbf{Features} \\
\hline
Savitzky-Golay & \texttt{Feature\_Savgol\_Min}, \texttt{Feature\_Savgol\_std} \\
Fluxo bruto & \texttt{Max\_Drawdown} \\
K-Means & \texttt{kmeans\_centroid\_dist} \\
Testes de quartis & \texttt{MinLogP\_Ttest}, \texttt{MinLogP\_KS} \\
Observacionais & \texttt{Occ\_depth}, \texttt{Occ\_SNR\_dip}, \texttt{Occ\_duration\_s}, \texttt{Occ\_baseline\_std}, \texttt{Occ\_chi2\_constant}, \texttt{Occ\_chi2\_square\_well}, \texttt{Occ\_chi2\_ratio} \\
\hline
\end{tabular}
\end{table}
```
  Fazer a mesma troca "13--14" → "11--13" em capitulo6.tex:33.
- Justificativa: atende ao pedido da banca. Sem envolver a tabela num ambiente `table`, a citação não funciona. O conjunto da tabela é exatamente o do Exp 1.1 (`O/resultado2/feature_names.pkl`).
- Status: aplicável direto.

### [Cap6 ii]
- Resposta factual: o teste de baixo SNR usou **11 features**, com os quatro modelos do Experimento 2 (`DEFAULT_MODEL_DIR = .../resultado5_...`, P/model_in_practice/test_low_snr.py:45-49). As colunas são lidas de `feature_names.pkl` (:273-277).
  - As 67 curvas são todas positivas, recalculadas a partir do banco (test_low_snr.py:158-179).
  - Pelo split do Exp 2, 48 estão no treino, 10 no teste e 9 não pertencem ao dataset (são curvas-mãe de recortes).
  - O critério `Occ_SNR_dip < 3` seleciona sobretudo ocultações profundas, nas quais a linha de base pela mediana falha porque o evento ocupa mais da metade da série (mediana de `Feature_Savgol_Min` = 0,058; 85% com amplitude > 0,5). Não são curvas ruidosas.
- Local: T/capitulo6.tex:18.
- Trecho atual:
```tex
Como verificação complementar, as 67 curvas do banco com $\mathrm{Occ\_SNR\_dip} < 3$ foram submetidas aos modelos treinados
```
- Proposta (substitui o parágrafo :18 inteiro):
```tex
Como verificação complementar, as 67 curvas positivas do banco com $\mathrm{Occ\_SNR\_dip} < 3$ foram submetidas aos quatro modelos do Experimento~2 (11 \textit{features}). Os três \textit{ensembles} classificaram todas como positivas (67/67), e a Regressão Logística, 66 das 67. Três ressalvas limitam o alcance desse resultado. Primeiro, 48 dessas curvas fizeram parte do treino, e só 19 são externas a ele (10 do teste e 9 curvas-mãe de recortes, fora do \textit{dataset}). Segundo, não há negativas no conjunto, de modo que falsos positivos não podem ser avaliados. Terceiro, nessas curvas o valor baixo de $\mathrm{Occ\_SNR\_dip}$ decorre, na maioria dos casos, de ocultações profundas que ocupam mais da metade da série, o que desloca a linha de base estimada pela mediana (mediana de \texttt{Feature\_Savgol\_Min} = 0,06), e não de baixo sinal-ruído. Um teste no regime de baixo S/N propriamente dito permanece como trabalho futuro.
```
- Justificativa: responde à pergunta da banca (11 features). Também evita afirmar o que o teste não mede. Os três revisores (Simons, Feynman, Sagan) chegaram ao mesmo diagnóstico. A nova figura está excluída.
- Status: requer confirmação do autor (formulação da afirmação científica).

### [Cap6 iii]
- Resposta factual: o código está no repositório público **https://github.com/TLaidler/Portfolio**, diretório `Astrofisica/Mestrado/pipeline` (git remote; HTTP 200 sem autenticação). Atenção:
  - `*.csv` está no `.gitignore` (linha 3). Ficam fora do repositório `dataset_final.csv`, `training_results.csv`, as predições e os CSVs de CV e limiar.
  - As 702 curvas simuladas estão versionadas só como PNG; os `.dat` não estão.
  - O `.dat` de Quaoar não está (dado cedido).
  - Os recortes dependem de decisões manuais registradas só no `dataset_final.csv`.
  - Resultado: hoje não é possível reproduzir as tabelas a partir do repositório. O banco `stellar_occultations.db` está versionado.
- Local: T/capitulo6.tex:31.
- Trecho atual:
```tex
implementada em Python e disponível para reprodução.
```
- Proposta:
```tex
implementada em Python e disponível em \url{https://github.com/TLaidler/Portfolio} (diretório \texttt{Astrofisica/Mestrado/pipeline}); as versões das bibliotecas e o ambiente de execução estão no Apêndice~\ref{ap:ambiente}.
```
- Justificativa: responde à banca e cita o Apêndice C, que hoje não é mencionado em lugar nenhum (comentário geral p; grep confirma que `ap:ambiente` só aparece na própria definição). Recomendações: fixar um *commit* ou *tag*; depositar no Zenodo (com DOI) o `dataset_final.csv`, as pastas de saída e os `.dat` simulados; e declarar uma licença.
- Status: requer confirmação do autor (tag, DOI e licença).

### [Cap6 iv]
- Local: T/capitulo6.tex:37.
- Trecho atual:
```tex
orientando futuras decisões sobre coleta de dados.
```
- Proposta (substitui o item 4 inteiro):
```tex
\item \textbf{Análise de curvas de aprendizado:} o \textit{logloss} por iteração (Seção~\ref{sec:curvas_aprendizado_exp}) indica que as 100 iterações de \textit{boosting} não levam a sobreajuste, e o Experimento~3.1 (Apêndice~\ref{ap:experimentos}) sugere que reduzir em 19\,\% as curvas reais de treino altera pouco o desempenho ($-0{,}7$~pp no melhor F1). Isso orienta a coleta de \emph{novas curvas de luz rotuladas para o treinamento} --- não a aquisição de imagens: acrescentar mais curvas do mesmo tipo tende a trazer pouco ganho; mais valiosas seriam curvas negativas reais independentes e eventos rasos ou de baixo S/N.
```
- Justificativa: esclarece o que é a "coleta de dados" que a banca perguntou. Também modera "saturação em duas dimensões": são dois pontos, com conjuntos de teste diferentes (ver Cap5 9).
- Status: requer confirmação do autor.

### [Cap6 v]
- Resposta factual:
  - **Ordem e número de colunas importam.** A ingestão (P/data_warehouse/insert_new_data_manually.py:69-86) lê arquivos separados por espaço, ignora linhas vazias e as iniciadas por `#`, e toma a 1ª coluna como tempo e a 2ª como fluxo. Uma 3ª coluna, se existir, é lida como erro, mas **descartada** na inserção (:116, "Ignoramos o valor de erro por enquanto"). Colunas além da 3ª são ignoradas.
  - O rótulo vem do nome da pasta (`positive`/`negative`, :25) e a data é truncada ao mês (:54).
  - As unidades não são convertidas: as curvas de Umbriel estão em dias julianos, as do VizieR em segundos. Por isso `Occ_duration_s` não está em segundos para 18 curvas (15 positivas + as 3 negativas nativas).
  - O VizieR (`vizgraph`) fornece só tempo e fluxo (insert_new_data.py:235-238).
  - Os .dat do PRAIA de Quaoar usam outra ordem: coluna 4 = tempo, coluna 9 = fluxo normalizado (test_quaoar.py:46-50), lida por um script próprio.
  - **Barras de erro fotométricas não são usadas em nenhuma etapa.** A tabela `light_curves` só tem `time` e `flux` (create_database.py:27-32). As escalas de ruído das features são estimadas dos próprios dados: o MAD no χ² (occ_features.py:369) e o desvio padrão dos pontos ≥ mediana no `Occ_SNR_dip`.
- Local: T/capitulo6.tex:56.
- Trecho atual:
```tex
contanto que estejam em formato \texttt{.dat}.
```
- Proposta:
```tex
contanto que estejam em formato \texttt{.dat} de texto, com colunas separadas por espaço, a primeira coluna com o tempo e a segunda com o fluxo (uma terceira coluna, com a incerteza fotométrica, é lida mas não utilizada). Os tempos devem estar em uma única unidade: neste trabalho, as curvas do Grupo do Rio (em dias julianos) e as do VizieR (em segundos) não foram uniformizadas, o que afeta a \textit{feature} \texttt{Occ\_duration\_s} de 18 curvas.
```
  E acrescentar uma limitação nova na Seção 6.4:
```tex
\item \textbf{Barras de erro fotométricas não utilizadas:} as incertezas fotométricas de cada ponto não são armazenadas no banco nem usadas nas \textit{features}. As escalas de ruído (por exemplo, no $\chi^2$ e no SNR do \textit{dip}) são estimadas da dispersão da própria curva. Incorporá-las permitiria um $\chi^2$ propriamente dito e uma comparação mais justa entre curvas de qualidades diferentes.
```
- Justificativa: responde às duas perguntas da banca com o código. A falta de uniformização de tempo é um achado verificável, que contradiz a "uniformização de unidades quando necessário" de capitulo4.tex:67.
- Status: aplicável direto (factual); decidir se as barras de erro serão usadas no futuro fica com o autor.

### [Cap6 vi]
- A banca não pede ação. Aproveito para corrigir uma inconsistência lógica nos trabalhos futuros, que a banca não apontou.
- Local: T/capitulo6.tex:71.
- Trecho atual:
```tex
\item \textbf{Experimento \textit{real holdout}:} reservar todas as curvas reais
```
- Proposta (substitui o item inteiro):
```tex
\item \textbf{Teste em negativas reais independentes:} reunir curvas negativas reais de outras campanhas (não recortadas das positivas usadas no treino) e usá-las apenas como teste, com a partição treino/teste agrupada por evento e por curva-mãe dos recortes.
```
- Justificativa: o texto atual propõe treinar "apenas com curvas sintéticas e negativos por recorte". Isso deixaria o treino sem nenhuma positiva, já que as simuladas são todas negativas, e os recortes são curvas reais.
- Status: requer confirmação do autor.

---------------------------------------------------------------------
## Extras obrigatórios que a banca não pediu (quantitativos)
---------------------------------------------------------------------

### [Extra 1] Vazamento entre recortes-irmãos e entre cordas do mesmo evento
- Local: T/capitulo5.tex:654 (e :226).
- Trecho atual:
```tex
respeitam o \textbf{agrupamento por curva} (todos os segmentos recortados de uma mesma curva ficam na mesma dobra, para que o modelo nunca seja testado em um pedaço de uma curva que viu no treino, o que inflaria artificialmente o desempenho)
```
- Proposta (se não houver nova rodada; com rodada nova, usar `StratifiedGroupKFold` com grupo = curva-mãe, ou seja, o nome sem `_antes/_depois_artificial`, e evento = objeto + data):
```tex
são estratificadas por classe e agrupadas por curva (\texttt{curve\_name}). Como os dois recortes de uma mesma curva-mãe (``antes'' e ``depois'') recebem nomes distintos, eles podem cair em dobras diferentes; o mesmo vale para cordas de um mesmo evento obtidas por observadores diferentes. No teste 80/20 misto, 21 dos 38 recortes têm o recorte-irmão no treino; no Experimento~3, 18 dos 37. Esse acoplamento tende a tornar a estimativa de especificidade em negativas reais otimista.
```
- Justificativa: verificado com SP/reconcile_siblings.py. Além disso, 39 das 160 positivas do teste do Exp 3 têm corda do mesmo evento no treino (contagem do revisor Feynman, confirmada).
- Status: requer confirmação do autor (corrigir o texto ou rodar de novo com agrupamento).

### [Extra 2] Limiar escolhido no próprio teste, e critério declarado não aplicado
- Local: T/capitulo5.tex:382, :387, :399–407, :412.
- Trecho atual:
```tex
\textbf{Destaque:} A Regressão Logística com $\tau = 0{,}16$ atinge sensibilidade de 100\% com apenas 1 falso positivo
```
- Proposta: reportar, para cada modelo, o maior τ com sensibilidade de 100% no conjunto analisado, segundo O/resultado3/threshold_analysis.csv: RF τ=0,33 (3 FP/0 FN), XGB τ=0,12 (3/0), CatBoost τ=0,29 (3/0), RegLog τ=0,16 (1/0). E incluir:
```tex
Como os limiares foram escolhidos no próprio conjunto de teste, as métricas da Tabela~\ref{tab:threshold_comparacao} são otimistas; para uso operacional, $\tau$ deve ser escolhido por validação cruzada no treino. Com 160 positivas, uma sensibilidade observada de 100\,\% tem intervalo de confiança de 95\,\% de $[97{,}7\,\%;\ 100\,\%]$.
```
- Justificativa: os pontos "sensíveis" da tabela atual (RF 0,45; XGB 0,30; CB 0,37) deixam 1–2 FN e não seguem o critério de "sensibilidade mínima garantida". O IC é de Clopper–Pearson.
- Status: aplicável direto (o texto); escolher τ por CV requer rodada nova.

### [Extra 3] Falsos alarmes com τ = 0,03 (Quaoar)
- Local: T/capitulo5.tex:515; T/capitulo6.tex:43; resumo (T/teseon.tex:136).
- Trecho atual:
```tex
\emph{sem} que o controle ($6\times10^{-4}$) ou o ruído ($5\times10^{-4}$) cruzem o novo limiar.
```
- Proposta (acrescentar logo depois):
```tex
Esse limiar foi escolhido depois de observar as probabilidades das seis janelas, e só duas delas são controles. Aplicado ao conjunto de teste do Experimento~3, o mesmo XGBoost com $\tau = 0{,}03$ classifica como positivas 6 das 38 curvas negativas reais (16\,\%); no teste do Experimento~2, 4 de 39. A recuperação dos anéis Q2R deve ser lida como ilustração a posteriori: estimar a taxa de falso alarme exigiria uma varredura cega de janelas de mesma duração sobre toda a curva.
```
  No resumo e em capitulo6.tex:43, trocar "sem introduzir falsos alarmes" por "sem falsos alarmes nas duas janelas de controle examinadas". Trocar também "duas ordens de grandeza" por "cerca de 86 vezes no XGBoost (12 vezes no CatBoost) em relação a um trecho de ruído".
- Justificativa: números calculados nas predições salvas (O/resultado5/predictions_xgboost.csv) e no Exp 3 reproduzido. Em 10 sementes, a taxa fica em 15–17% para o XGBoost (SP/seed_spread.py).
- Status: requer confirmação do autor (é a afirmação principal do resumo).

### [Extra 4] Contagens de features e descrição dos experimentos
- Detalhado em Cap5 1. Pontos obrigatórios:
  - capitulo5.tex:268, :556, :570, :688, :741: 14 → 13 (Exp 1.1).
  - capitulo5.tex:25, :387, :391, :656 e apêndice:42-49: 13 → 12 (Exp 1.2a).
  - apêndice:77: o Exp 1.2b **mantém** Savgol_Min.
  - capitulo6.tex:11, :33: "13–14" → "11–13".
  - capitulo3.tex:45: "14 ou 28" → "entre 11 e 28".
- Status: aplicável direto (independe do esquema de nomes).

### [Extra 5] Faixas de F1/AUC e afirmações numéricas desatualizadas
- Local: T/capitulo5.tex:735, :753, :574.
- Trecho atual:
```tex
F1-score entre 0,974 e 0,994 no teste misto (todos os experimentos, exceto o Experimento~3) e entre 0,975 e 0,982 no teste exclusivamente em curvas reais (Experimento~3)
e que a separabilidade elevada entre as classes (AUC-ROC $\geq 0{,}998$) garante
XGBoost e CatBoost mantêm F1 $\geq 0{,}990$.
```
- Proposta:
```tex
F1-score entre 0,984 e 0,994 no teste misto (todos os experimentos, exceto o Experimento~3) e entre 0,978 e 0,991 no teste exclusivamente em curvas reais (Experimento~3)
e que a separabilidade elevada entre as classes (AUC-ROC $\geq 0{,}996$ em todos os cenários) permite
o XGBoost mantém F1 $\geq 0{,}990$ nos dois experimentos, e o CatBoost, no Experimento~2 (0,9905; 0,9874 no Experimento~1.2b).
```
- Justificativa: as faixas atuais são do run antigo (resultado6.2). As tabelas atuais dão 0,9841–0,9937 no misto e 0,9778–0,9906 no Exp 3; a AUC mínima é 0,9965 (RF, Exp 3); o CatBoost do Exp 6/1.2b tem 0,9874. Além disso, AUC alta não "garante" precisão, que depende da prevalência.
- Status: aplicável direto.

### [Extra 6] Feature que absorve a importância quando o kmeans sai
- Local: T/capitulo5.tex:270; T/apendice_experimentos.tex:123; T/capitulo5.tex:749.
- Trecho atual:
```tex
a capacidade preditiva é simplesmente redistribuída para variáveis colineares, sobretudo \texttt{Feature\_Savgol\_std}
chegando a 63\% de importância no XGBoost
```
- Proposta:
```tex
a capacidade preditiva é simplesmente redistribuída para variáveis colineares: no Experimento~1.2b, sobretudo para \texttt{Feature\_Savgol\_Min} (\textit{gain} de 0,64 no XGBoost); no Experimento~2, que também remove \texttt{Feature\_Savgol\_Min}, para \texttt{Feature\_Savgol\_std} (0,57)
chegando a 69\% de importância (\textit{gain}) no XGBoost do Experimento~1.2a
```
- Justificativa: medido nos modelos salvos. Em resultado4 (Exp 1.2b), Savgol_Min tem 0,641 e Savgol_std 0,157. Em resultado3 (Exp 1.2a), kmeans tem 0,689. O valor de 63% não aparece em nenhum run. As correlações confirmam a colinearidade: kmeans × Savgol_Min r = −0,949; kmeans × Savgol_std r = 0,941.
- Status: aplicável direto.

### [Extra 7] Contagens do banco e do dataset; tabela × figura no Exp 3.1
- Local: T/capitulo5.tex:15, :206, :27; T/apendice_experimentos.tex:143–155 × figura em :161.
- Trecho atual:
```tex
o banco dispunha de 802 curvas positivas e apenas 3 negativas.
```
- Proposta:
```tex
o banco dispunha de 927 curvas positivas e apenas 3 negativas; 125 positivas foram usadas para gerar os 186 negativos por recorte e, por isso, excluídas, restando 802.
```
  Em :27: "preenchimento de valores faltantes pela mediana calculada no treino" → "descarte da única curva com valor faltante (1692 amostras usadas: 801 positivas e 891 negativas) e imputação pela mediana do treino, que não chega a ser acionada". No Exp 3.1, regenerar a figura `pngs/exp7` a partir do run que gerou a tabela, ou vice-versa: a figura atual mostra XGB com acurácia 0,971 e 3 FP, e a tabela, 0,9741 e 2 FP.
- Justificativa:
  - No DB há 928 observações positivas (927 com pontos), e nenhuma das 125 mães sobra no dataset (0/125). A exclusão funciona; o texto é que está errado.
  - O `.dropna()` está em train_model.py:175.
  - A tabela do 65/35 vem de uma reexecução com bibliotecas mais novas; a figura vem do run arquivado.
- Status: aplicável direto (texto); regenerar a figura requer o autor.

### [Extra 8] Hipótese "corroborada" sem termo de comparação
- Local: T/capitulo6.tex:23.
- Trecho atual:
```tex
é \textbf{corroborada} pelos resultados obtidos.
```
- Proposta:
```tex
é corroborada apenas em parte. Os \textit{ensembles} superam com folga um classificador trivial de uma única \textit{feature} no mesmo conjunto de teste: F1 $\approx 0{,}93$ com \texttt{Feature\_Savgol\_std} no teste misto e $\approx 0{,}95$ com \texttt{Max\_Drawdown} no teste só com curvas reais, contra $0{,}98$--$0{,}99$ dos \textit{ensembles}. Não foi feita, porém, comparação direta com redes convolucionais (como o ODNet) nem com inspeção manual nos mesmos dados, de modo que essa parte da hipótese permanece não testada.
```
- Justificativa: baselines calculados no mesmo split (SP/baseline1f.py). A sessão anterior do autor obteve `Occ_depth`: F1 0,905 no misto e 0,948 no só-real 65/35, valores compatíveis. Incluir na tese a linha do baseline ao lado da Tab. 5.9 custa pouco e justifica o ML.
- Status: requer confirmação do autor.

---------------------------------------------------------------------
## Referências novas (para teseon.tex, no estilo da lista manual)
---------------------------------------------------------------------
```tex
\bibitem[Breiman (2001)]{Breiman2001} BREIMAN, Leo. ``Random Forests''. \emph{Machine Learning}, 45(1), 5--32, 2001. \url{https://doi.org/10.1023/A:1010933404324}.

\bibitem[Chen \& Guestrin (2016)]{Chen2016} CHEN, Tianqi; GUESTRIN, Carlos. ``XGBoost: A Scalable Tree Boosting System''. In: \emph{Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining}. San Francisco: ACM, 2016. p. 785--794. \url{https://doi.org/10.1145/2939672.2939785}.

\bibitem[Prokhorenkova et al. (2018)]{Prokhorenkova2018} PROKHORENKOVA, Liudmila; GUSEV, Gleb; VOROBEV, Aleksandr; DOROGUSH, Anna Veronika; GULIN, Andrey. ``CatBoost: unbiased boosting with categorical features''. In: \emph{Advances in Neural Information Processing Systems 31 (NeurIPS 2018)}, p. 6639--6649, 2018. arXiv:1706.09516.

\bibitem[Strobl et al. (2007)]{Strobl2007} STROBL, Carolin; BOULESTEIX, Anne-Laure; ZEILEIS, Achim; HOTHORN, Torsten. ``Bias in random forest variable importance measures: Illustrations, sources and a solution''. \emph{BMC Bioinformatics}, 8, 25, 2007. \url{https://doi.org/10.1186/1471-2105-8-25}.

\bibitem[Zhong et al. (2023)]{Zhong2023} ZHONG, Xugang; LIN, Yanze; ZHANG, Wei; BI, Qing. ``Predicting diagnosis and survival of bone metastasis in breast cancer using machine learning''. \emph{Scientific Reports}, 13, 18301, 2023. \url{https://doi.org/10.1038/s41598-023-45438-z}.

\bibitem[Condorcet (1785)]{Condorcet1785} CONDORCET, Marie Jean Antoine Nicolas de Caritat, marquis de. \textit{Essai sur l'application de l'analyse à la probabilité des décisions rendues à la pluralité des voix}. Paris: Imprimerie Royale, 1785.

\bibitem[Davies et al. (2021)]{Davies2021} DAVIES, Alex; VELIČKOVIĆ, Petar; BUESING, Lars; et al. ``Advancing mathematics by guiding human intuition with AI''. \emph{Nature}, 600(7887), 70--74, 2021. \url{https://doi.org/10.1038/s41586-021-04086-x}.

\bibitem[Caliński \& Harabasz (1974)]{Calinski1974} CALIŃSKI, T.; HARABASZ, J. ``A dendrite method for cluster analysis''. \emph{Communications in Statistics}, 3(1), 1--27, 1974. \url{https://doi.org/10.1080/03610927408827101}.

\bibitem[Nocedal \& Wright (2006)]{Nocedal2006} NOCEDAL, Jorge; WRIGHT, Stephen J. \textit{Numerical Optimization}. 2. ed. New York: Springer, 2006. (Springer Series in Operations Research and Financial Engineering). \url{https://doi.org/10.1007/978-0-387-40065-5}.
```
Situação dos metadados:
- Verificados no Crossref: Zhong2023, Strobl2007, Davies2021, Calinski1974, Chen2016.
- Verificados por busca (Springer, dblp, NeurIPS, WorldCat): Breiman2001 (vol. 45, p. 5–32; número "(1)" a verificar); Prokhorenkova2018 (NeurIPS 2018, p. 6639–6649; arXiv:1706.09516); Nocedal2006 (2. ed., 2006, DOI); Condorcet1785 (Paris, Imprimerie Royale, 1785).
- Os caracteres "Č/ć" (Veličković) e "ń" (Caliński) podem exigir `\v{C}`/`\'{c}`/`\'{n}` com `fontenc T1` (a verificar na compilação).
- A verificar: o número da figura de Zhong et al. (2023) que corresponde à Fig. 3.9; o dado "17 de 29 soluções vencedoras do Kaggle" em Chen & Guestrin (2016).

Fontes consultadas: [Zhong et al. 2023 — Nature/Sci Rep](https://www.nature.com/articles/s41598-023-45438-z), [Crossref API](https://api.crossref.org), [Breiman 2001 — Springer](https://link.springer.com/article/10.1023/A:1010933404324), [Chen & Guestrin 2016 — ACM DL](https://dl.acm.org/doi/10.1145/2939672.2939785), [CatBoost — dblp](https://dblp.org/rec/conf/nips/ProkhorenkovaGV18.html), [CatBoost — arXiv](https://arxiv.org/pdf/1706.09516), [Strobl 2007 — Semantic Scholar](https://www.semanticscholar.org/paper/Bias-in-random-forest-variable-importance-measures:-Strobl-Boulesteix/33b1c59f1db83adf63696d4ed9718b20e290a943), [Condorcet 1785 — WorldCat](https://www.worldcat.org/title/essai-sur-lapplication-de-lanalyse-a-la-probabilite-des-decisions-rendues-a-la-pluralite-des-voix/oclc/1429244), [Condorcet 1785 — Gallica](https://gallica.bnf.fr/ark:/12148/bpt6k417181.image), [Nocedal & Wright — Amazon/Springer](https://www.amazon.com/Numerical-Optimization-Operations-Financial-Engineering/dp/0387303030), [ResearchGate (origem da Fig. 3.9)](https://www.researchgate.net/publication/374986649_Predicting_diagnosis_and_survival_of_bone_metastasis_in_breast_cancer_using_machine_learning).

---------------------------------------------------------------------
## Verificação dos trechos
SP/verify_trechos.py extraiu os 112 fragmentos citados em "Trecho atual" e procurou cada um, literalmente, nos .tex de T/. Resultado: **112/112 encontrados** (detalhe em SP/verify_trechos.out). Os números de linha em "Local" correspondem às ocorrências encontradas.
