# Memórias do painel — Rodadas 1 (leitura independente) e 2 (debate)

Registro integral escrito pelos três revisores-agente (Feynman, Sagan, Simons) antes da leitura da carta da banca.
As correções derivadas estão em [correcoes_banca.md](correcoes_banca.md). Referências a `SP/` apontam para scripts do scratchpad da sessão (não versionados).


---

# Memória do revisor "Feynman" — Rodada 1

Dissertação: "Pipeline para Detecção Automatizada de Ocultações Estelares em Curvas de Luz com Técnicas de ML" (T. L. V. Cunha, ON).
Lente: correção física, primeiros princípios, refazer as contas, "não se enganar" (a epígrafe da tese, teseon.tex:123), desconfiar de números bons demais.
Arquivos lidos por inteiro: teseon.tex, introducao.tex, capitulo2..6.tex, apendice_experimentos/hiperparametros/ambiente.tex. Figuras do Cap. 2 abertas (curva, ModelosSORA, Bardecker12, OccUmbriel_*, LimbFitCircle) e também quaoar_test.png e quaoar_recorte_tau_ajustado.png.
Código conferido: occ_features.py, build_dataset.py, train_model.py, astro_data_access.py (normalize_flux, remove_outliers), simulate_curve.py, test_quaoar.py, test_quaoar_recortes.py, test_low_snr.py e as saídas em pipeline/model_training/outputs/resultado1.../dataset_final.csv.
NÃO lidos (de propósito): critica.pdf, critica_sagan_feynman.md, AUDITORIA_PIPELINE.md.
Nota da memória do projeto: NÃO apontar `pngs/` vs `Tese/pngs/` (intencional, funciona no Overleaf).

---------------------------------------------------------------------
## 0. Evidência computada por mim (para reutilizar no debate)
---------------------------------------------------------------------
(scripts rodados no dataset_final.csv do Exp.1; 1693 linhas)
- Medianas por fonte (sintética | recorte | db_neg | positiva):
  Occ_baseline_std 0,021 | 0,058 | 0,072 | 0,104   -> as sintéticas têm ruído ~3x menor que o real.
  Occ_depth        0,10  | 0,19  | 0,31  | 0,87    -> "depth ≈ 0 sem ocultação" é falso.
  Occ_SNR_dip      4,7   | 3,3   | 4,3   | 7,3     -> o "SNR" de ruído puro vale 3–5.
  Occ_duration_s   0,85  | 0,40  | 8e-5  | 4,2     -> db_negative em DIAS (Grupo do Rio).
- AUC de UMA feature só (positivas vs cada tipo de negativa): Feature_Savgol_Min 0,992 (sint.) / 0,980 (recortes);
  kmeans_centroid_dist 0,992/0,945; Feature_Savgol_std 0,990/0,922. No dataset inteiro: Savgol_Min AUC 0,989,
  F1 com um único limiar = 0,963 (in-sample). Ou seja, o problema montado é quase separável por um único número.
- Simulação: ruído gaussiano puro, N=1000 -> (mediana−mín)/σ = 3,8; SNR_dip (com σ de meia amostra) = 6,5;
  std(f≥mediana)/σ = 0,59; MAD/σ = 0,64 (sem o fator 1,4826).
- Positivas com SNR_dip<3: 58 no dataset (a tese fala em 67 via test_low_snr); 40/58 têm mediana do fluxo < 0,6
  (o dip ocupa > metade do registro) e mediana de Savgol_Min = 0,058 -> são ocultações PROFUNDAS, não fracas.
- Pais dos recortes: 125 positivas, nenhuma sobrou no dataset (a exclusão funciona). Logo o banco tinha ≥ 927 positivas.
- Reproduzindo o split do Exp.3 (seed 42, por curve_name, após dropna): 38 negativas de teste (bate com a tese);
  18 de 61 pares antes/depois ficam separados entre treino e teste -> 18 das 38 negativas reais de teste têm o "irmão"
  (mesma estrela/noite/telescópio) no treino. 39/160 positivas de teste têm cordas do mesmo evento no treino.
- O dataset tem 1 linha com NaN (Hera_2005-04-01_BAllen, Occ_flux_min_over_baseline); load_dataset faz .dropna()
  (train_model.py:175) -> são usadas 1692 amostras, e o SimpleImputer não tem efeito.
- O default de XGBClassifier.feature_importances_ é "gain" (conferido no código-fonte do xgboost: dft() -> "gain"
  para booster de árvores), NÃO "weight".
- Exemplo da logística: ∂J/∂θ1 = −0,125 (e não −0,15). Com θ1=0,15: J=0,6755 (e não 0,685); com θ1=0,125:
  p = 0,506/0,513/0,522/0,528 e J = 0,678.
- Fresnel: 40 UA, 500 nm -> 1,22 km (certo). Quaoar (~43 UA, z ~900 nm) ≈ 1,7 km; Umbriel (Δ=19,02 UA do mapa) ≈ 0,9 km.
  Usando a distância estrela–corpo (10 pc) -> ~280 km (absurdo).
- Condorcet: 25 árvores com p=0,65 -> P(maioria) = 0,940 (certo, sob independência).
- Intervalo de Clopper–Pearson para 1 FP em 38 negativas reais: 0,07%–13,8%.
- Quaoar (figura quaoar_test): corpo de −26 a +22 s (≈48 s); Q2R em −125,5 e +130,5 s com ~0,5 s e ~5% de profundidade;
  Q1R contínuo em −216 s com ~4 s e ~3%; Q1R denso em +223 s, fundo ~0,2. v ≈ 2520 km/128 s ≈ 20 km/s -> corda do corpo
  ≈ 950 km (consistente com Quaoar fora do centro); largura do Q2R ≈ 10 km. Dados brutos de Quaoar NÃO estão no repositório
  (pipeline/model_in_practice/quaoar/ só tem um jpeg) -> a cadência não pôde ser verificada.

---------------------------------------------------------------------
## 1. ACERTOS principais
---------------------------------------------------------------------
A1. capitulo2.tex:86-89 — O exemplo numérico da escala de Fresnel está certo (√(6,0e12·5e-7/2) ≈ 1,22 km) e é bem motivado.
A2. capitulo2.tex:77 — A distinção entre o borrão da exposição (V_S·t_exp) e as lacunas do tempo morto
    (o ciclo completo exposição + readout) é física de primeiros princípios, correta e rara de ver bem explicada.
A3. capitulo3.tex:201-215 (Gini 0,5 -> 0,20, ganho 0,30), capitulo3.tex:220 (OOB 63%/37%) e capitulo3.tex:237
    (Condorcet: 25×65% -> 94%) estão numericamente corretos.
A4. As tabelas de métricas são internamente consistentes com contagens inteiras: capitulo5.tex:244-247, 285-288, 316-319,
    399-407 e apendice_experimentos.tex:149-152 (ex.: Exp.1 com P=160/N=179; RF com TP=158, FN=2, FP=0; Exp.3 com
    XGB TP=158, FP=1, TN=37). Não há número inventado nas tabelas.
A5. A exclusão da positiva-mãe dos recortes está de fato implementada (build_dataset.py:204-208, 459-461; verifiquei
    sobreposição zero), coerente com capitulo4.tex:113-115.
A6. Higiene de ML correta: imputer e scaler ajustados só no treino, scaler só para a Regressão Logística, split por curva
    e semente fixa (capitulo4.tex:127, 236-241; train_model.py:224-249).
A7. O resultado da ablação, "importância ≠ insubstituibilidade" (capitulo5.tex:270, 749), é correto e didático, e testar
    uma hipótese alternativa ("a janela curta não é a causa", capitulo5.tex:525) é bom hábito científico.
A8. Várias limitações são admitidas com honestidade: rótulos sem concordância entre anotadores (capitulo4.tex:85),
    curvas defeituosas descartadas (capitulo4.tex:49), só 38 negativas reais (capitulo5.tex:326), baixo poder do
    McNemar (capitulo5.tex:711) e limitações explícitas (capitulo6.tex:52-60).
A9. capitulo4.tex:45 — O esclarecimento quadros × curvas desfaz uma confusão real de escala.
A10. Formular o limiar como pós-processamento (capitulo5.tex:434) e distinguir modo balanceado de modo triagem é a
     maneira certa de pensar a assimetria de custo.

---------------------------------------------------------------------
## 2. ERROS principais (ordem ≈ de importância)
---------------------------------------------------------------------
Formato: [ID] arquivo:linha — "citação" — categoria — severidade — por quê.

E1. capitulo5.tex:252 — "A AUC-ROC muito alta (≥0,9997) confirma excelente capacidade de separação" (e capitulo5.tex:326,
    "essencialmente preservado") — ML/estatística — ALTA.
    Números bons demais, com causa identificável. 79% das negativas são sintéticas, com ruído ~3x menor que o real
    (baseline_std 0,021 contra 0,058/0,104). Uma única feature (Savgol_Min) já dá AUC 0,99, e a Regressão Logística
    dá AUC = 1,0000. O teste mede "tem queda profunda / é real × simulado", não o regime difícil. Nas negativas REAIS a
    taxa de FP é 1/38 (IC95% 0,07–13,8%) e 2–4/66 (3–6%) na variante 65/35, contra ~0–1,7% no teste misto. Ou seja, a
    "preservação" vale para a sensibilidade, não para os falsos alarmes.

E2. capitulo5.tex:654 — "todos os segmentos recortados de uma mesma curva ficam na mesma dobra" (e :226, "cada curva
    aparece integralmente em treino ou em teste") — ML — ALTA.
    O código agrupa por curve_name (train_model.py:294-304, 732-747), mas os recortes se chamam
    "<obj>_<data>_<obs>_antes_artificial" e "..._depois_artificial" (build_dataset.py:505). Reproduzi o split do Exp.3:
    18 das 38 negativas reais de teste têm o recorte-irmão (mesma estrela/noite/telescópio) no treino. Além disso,
    39/160 positivas de teste têm cordas do mesmo evento no treino. A afirmação é falsa e há vazamento. A correção é
    agrupar por curva-mãe e por evento (StratifiedGroupKFold).

E3. capitulo5.tex:387-412 — "Regressão Logística com τ=0,16 atinge sensibilidade de 100% com apenas 1 falso positivo —
    ponto operacional ideal" — ML/estatística — ALTA.
    O limiar é escolhido no próprio conjunto de teste (train_model.py:801-836 usa y_test), e a métrica é reportada no
    mesmo conjunto: viés otimista. Na mesma linha, a seleção de features e de configurações foi feita olhando o
    desempenho no MESMO split de teste em 6 experimentos (capitulo5.tex:116, "No Experimento 4, a remoção ... não causou
    perda"): isso é data snooping. Precisa de validação (ou predições out-of-fold) separada do teste.

E4. teseon.tex:136 (resumo), capitulo5.tex:513-515 e 527, capitulo6.tex:43 — "cerca de duas ordens de grandeza
    superiores às atribuídas a trechos de ruído semelhantes ... sem introduzir falsos alarmes" — ML/honestidade — ALTA.
    (i) "Trechos" são UM trecho escolhido a olho. (ii) O modelo operacional declarado (CatBoost) dá Q2R₁ = 0,058,
    contra 0,029 no controle de baseline (só 2x) e 0,005 no ruído (12x); o XGBoost foi escolhido DEPOIS de ver qual
    separa melhor ("Por que XGBoost"). (iii) τ=0,03 foi escolhido depois de ver as 6 probabilidades. (iv) "Sem falsos
    alarmes" se apoia em 2 janelas de controle. Uma varredura por janela deslizante sobre todo o baseline seria
    necessária para estimar a taxa de falso alarme em τ=0,03. É a afirmação mais forte do resumo e a de evidência mais
    fraca. Observação: há um script quaoar_baseline_vs_ml.py (ML × baseline de 1 feature nos mesmos recortes) cujo
    resultado não aparece na tese.

E5. capitulo4.tex:191 — "Em curvas sem ocultação, depth ≈ 0" e capitulo4.tex:193-199 (SNR_dip) — física/estatística — ALTA.
    depth = mediana − mín é estatística de extremo (≈ σ√(2 ln N)), e σ_baseline = std dos pontos ≥ mediana é de meia
    distribuição (≈ 0,59σ). Para ruído puro com N=1000, SNR_dip ≈ 6,5 (simulado); no dataset, a mediana das negativas
    é 3,3–4,7 e a das positivas 7,3. Um "SNR" que dá ~6 para ruído puro não mede SNR. Além disso, baseline = mediana
    falha quando o dip ocupa > 50% do registro (45 positivas).

E6. capitulo6.tex:18 — "as 67 curvas do banco com Occ_SNR_dip < 3 ... todas foram corretamente classificadas" —
    física/estatística — ALTA.
    (i) São curvas de treino (admitido): a "verificação" é acurácia in-sample. (ii) Pior: das 58 que localizei no
    dataset, 40 têm a ocultação cobrindo mais de metade do registro, e a mediana do mínimo suavizado é 0,058. São
    ocultações profundas, quase totais, nas quais a linha de base pela mediana quebra, e não eventos fracos. O teste não
    toca no regime de baixo S/N.

E7. capitulo6.tex:23 — "desempenho comparável a abordagens baseadas em redes convolucionais ou inspeção manual ... é
    corroborada" (hipótese em introducao.tex:32) — honestidade/ML — ALTA.
    Não se fez nenhuma comparação com ODNet/CNN, com inspeção manual nem mesmo com um baseline trivial nos mesmos dados.
    Um único limiar em Savgol_Min já dá AUC 0,989. A hipótese não foi testada, logo não pode ser "corroborada".

E8. capitulo2.tex:75 — "em ocultações centrais ou próximas do centro, a queda pode ser total (fluxo próximo de zero no
    patamar)" — física — ALTA.
    Quando o corpo é muito maior que a estrela projetada e que a escala de Fresnel, QUALQUER corda que cruza o disco
    oculta a estrela por inteiro; central ou não, isso não muda a profundidade. O patamar é dado pela luz do próprio
    ocultante na abertura, F_corpo/(F_estrela+F_corpo), mais atmosfera, diâmetro estelar ou exposição maior que o
    evento. As figuras da própria tese mostram isso: Umbriel com patamar em 0,18–0,24 (Bardecker12.png;
    OccUmbriel_outputExemplo2, eixo "(Umbriel + occ_star)"). Em corpos com atmosfera, a corda central produz um
    *flash* central (o fluxo SOBE). Nada disso é explicado. Menor: "o trânsito ocorre" (:75) é o termo errado (trânsito
    ≠ ocultação).

E9. capitulo2.tex:77 — "D é a distância entre o observador e o corpo ocultante (ou, em convenções equivalentes, a
    distância estrela–corpo)" — física — MÉDIA-ALTA.
    Não é equivalente. Com a estrela praticamente no infinito, D_eff = D_obs·D_★/(D_obs+D_★) ≈ D_obs. A distância
    estrela–corpo (10 pc) daria ≈ 280 km em vez de ≈ 1,2 km.

E10. capitulo2.tex:90 — "Essa escala define a resolução espacial efetiva na direção perpendicular à corda" — física — MÉDIA.
    A difração suaviza o perfil ao longo da corda, isto é, a travessia do limbo; a resolução perpendicular às cordas é
    o espaçamento entre observadores. Além disso, a resolução efetiva é max(F, diâmetro estelar projetado, V·Δt_ciclo):
    em Umbriel (Δ=19,02 UA, v=17,12 km/s, do próprio mapa), F≈0,9 km, enquanto v·Δt ~ alguns km (a cadência exata está
    a verificar). Na prática Fresnel raramente é o fator limitante, o que contradiz "essa escala define".

E11. capitulo2.tex:82 (legenda da Fig. ModelosSORA) — "difração de Fresnel (azul) ... resultante da combinação dessas
    componentes, o modelo geométrico (verde) ... dados observados (pontos vermelhos)" — física/escrita — MÉDIA (alta
    pela leitura física).
    Na figura, o preto é Fresnel, o azul é o tamanho angular da estrela, o verde é o modelo geométrico (o poço quadrado
    de PARTIDA, não o resultado), e o vermelho, com barras horizontais, é a resposta instrumental (o modelo integrado
    na exposição), não dados observados. A legenda inverte a lógica de construção do modelo.

E12. build_dataset.py:110, 117-138 × capitulo4.tex:115 — "identifica-se a região de ocultação de forma manual" —
    ML/física — MÉDIA-ALTA.
    (a) A região é achada automaticamente (fluxo < 0,78, do primeiro ao último ponto), e o humano só aceita ou rejeita.
    (b) Os recortes passam por remoção de outliers 3σ, mas as positivas e as sintéticas não (build_dataset.py:456-467):
    é um pré-processamento dependente da classe, que reduz por construção os extremos (depth, drawdown, mínimo) da
    classe negativa. (c) Quedas rasas acima de 0,78 (anéis, atmosfera, rasantes, ocultante brilhante) ficam DENTRO dos
    "negativos": o modelo é treinado para chamar de negativo justamente o sinal sutil que a tese diz querer achar
    (introducao.tex:22). (d) O limite do recorte "antes" inclui pontos do ingresso.

E13. capitulo5.tex:110 — "A duração em unidade física (segundos) é mais interpretável e invariante a mudanças de
    cadência" — física/consistência — MÉDIA-ALTA.
    Occ_duration_s mistura unidades: as curvas do Grupo do Rio estão em dias (db_negative com mediana 8e-5; 11
    positivas de Umbriel < 0,01 "s" para um evento de ~60 s). A "uniformização de unidades" (capitulo4.tex:67) não
    ocorreu para o tempo.

E14. capitulo4.tex:149 — "janela N/40 para séries longas (ex.: N > 120) e N/3 para séries curtas" — física/metodologia — MÉDIA.
    (a) O código usa N<40 -> N/3, senão N/40, com mínimo 3 (build_dataset.py:316-321): o texto diverge. (b) De
    primeiros princípios, a janela deveria seguir a escala física (Fresnel ~0,1 s, travessia do Q2R ~0,5 s), não o
    comprimento do registro. O mesmo evento é suavizado de forma diferente conforme quanto baseline o observador gravou.
    Isso explica, melhor que a "diluição", a queda de p̂ ao ampliar as janelas de Quaoar (capitulo5.tex:525): a janela
    de 3 vira ~11 pontos e apaga um dip de 0,5 s e 5% (a verificar com a cadência). E contradiz a crítica que a própria
    Introdução faz à suavização (introducao.tex:24).

E15. capitulo3.tex:224, capitulo4.tex:258 × capitulo5.tex:157, 163 — importância: "queda média na impureza (Gini) ...
    RF, XGBoost, CatBoost"; "XGBoost ... por padrão, a métrica weight"; "PredictionValuesChange ... valores de x_j são
    permutados" — ML — MÉDIA.
    Três versões que se contradizem, e duas são falsas: o default do XGBClassifier é "gain" (conferi no código-fonte), e
    PredictionValuesChange não usa permutação (vem das diferenças de valor de folha; a métrica baseada em perda é a
    LossFunctionChange). Além disso, a Tabela de métodos (capitulo5.tex:193) dá a escala do XGB como "0 a ≈0,15",
    mas o texto cita 0,57 e 63% (capitulo5.tex:599, 749).

E16. capitulo4.tex:252 — "C ou α escolhido via validação cruzada"; capitulo3.tex:169 "Ridge ou Lasso"; capitulo5.tex:228
    "ponderação das classes nos quatro algoritmos" — consistência — MÉDIA.
    O apêndice (apendice_hiperparametros.tex:7-15, 36, 50) diz C=1 fixo, só l2, sem CV, e XGBoost sem ponderação
    ("tratado indiretamente pelo algoritmo" é falso: o XGBoost não trata desbalanceamento de forma implícita).

E17. capitulo5.tex:735 — "F1 entre 0,974 e 0,994 no teste misto ... e entre 0,975 e 0,982 no teste real (Exp.3)" —
    consistência numérica — MÉDIA.
    As tabelas dão 0,9841–0,9937 (misto) e 0,9778–0,9906 (Exp.3); o resumo e o Cap. 6 dão 0,978–0,994. Outras
    divergências: :753, "AUC-ROC ≥ 0,998", contra 0,9965 (RF no Exp.3); :326 e :576, "queda ≈2 pp", contra
    apendice_experimentos.tex:157, "≈0,7 pp"; capitulo6.tex:13, "degradação ≤0,3 pp", quando as tabelas não mostram
    degradação nenhuma.

E18. capitulo5.tex:15, 206 — "o banco dispunha de 802 curvas positivas ... a partir delas, foram obtidos 186 negativos"
    — consistência — MÉDIA.
    Os 186 recortes vêm de 125 OUTRAS positivas, excluídas; o banco tinha ≥ 927. Também: 1 linha com NaN é descartada
    por .dropna() (train_model.py:175), então treina-se com 1692 e o imputer é inócuo (capitulo4.tex:236). A contagem
    de features também não fecha: capitulo5.tex:119, "conjunto final 13" (com Savgol_Min e kmeans, sem n_frames), não é
    o Exp.5, "13 (sem Savgol_Min)" (apendice_experimentos.tex:45); capitulo5.tex:268 descreve 12 remoções e chega a
    "14"; :741 diz "15 removidas → Exp.4 (14)" (28−15=13); o Exp.2 (11) tira n_frames sem dizer, em relação ao Exp.6
    (12). Desbalanceamento: capitulo4.tex:266, "dados desbalanceados (muitas curvas sem ocultação)", e
    capitulo5.tex:228, contra 802/891 (47/53%). capitulo4.tex:109, "VizieR contém exclusivamente positivas", contra
    capitulo4.tex:85, "no VizieR a classificação positiva/negativa provém dos curadores".

E19. capitulo6.tex:71 — "real holdout: ... treinando apenas com curvas sintéticas e negativos por recorte" — lógica — MÉDIA.
    O treino ficaria sem nenhuma positiva (as sintéticas são todas negativas). E capitulo6.tex:52, "sintéticas geradas
    com base em propriedades estatísticas de curvas reais", contradiz capitulo4.tex:119 e o código: o simulador é
    paramétrico, com mag 11–14,5, t_exp 0,05–0,25 s e duração 20–60 s sorteados uniformemente (simulate_curve.py), sem
    ruído vermelho/transparência; o ruído resultante é 3x menor que o real. Na física do simulador, a cintilação
    ∝ seeing (simulate_curve.py:266-268) está errada: a fórmula de Young depende de abertura^(-2/3), massa de ar^1,75,
    altitude e t^(-1/2), não do seeing. Oportunidade perdida: o simulador gera positivas com anéis, e um teste de
    injeção e recuperação (completeza × profundidade × duração) era o experimento natural.

E20. capitulo5.tex:682-709 — "Nenhum par ... os quatro classificadores podem ser considerados equivalentes" —
    ML/estatística — MÉDIA.
    O χ² com correção de continuidade não serve para b+c ≤ 6; o teste exato binomial é o adequado. Com b=c=1, o χ²
    corrigido dá p=0,48 (artefato; o exato dá p=1). E não significativo ≠ equivalente (ausência de evidência). O teste
    usa o Exp.4, a CV usa o Exp.5, o operacional é o Exp.2: está fragmentado.

E21. capitulo3.tex:150 — "∂J/∂θ1 = ... = −0,15 ... O custo cai para J ≈ 0,685" — consistência numérica — BAIXA-MÉDIA.
    Refazendo: (1/4)(0,1+0,2−0,35−0,45) = −0,125. Com o θ1=0,15 do texto, J = 0,6755; com o correto (0,125),
    p = 0,506/0,513/0,522/0,528 e J = 0,678. Nota: as probabilidades das NEGATIVAS também sobem, porque θ0=0 e x não
    está centrado; "na direção correta" é meia verdade.

E22. capitulo4.tex:207-222 / occ_features.py:316-323, 368-369 — "σ uma escala robusta (MAD)"; "escala ~ desvio padrão"
    — estatística — BAIXA-MÉDIA.
    O MAD sem o fator 1,4826 vale ≈ 0,67σ, o que infla o χ² ~2,2–2,4x. O χ² não é reduzido (∝ N), então vira proxy do
    COMPRIMENTO do registro, que difere por fonte. χ²_ratio ≥ 1 sempre (modelo aninhado, sem penalizar graus de
    liberdade) e é cortado em 10.

E23. capitulo5.tex:477-478 (quaoar_test.png) — figura com eixos em inglês e insets com ajuste de modelo, aparentemente
    reproduzida de Pereira et al. (2023), sem "Fonte" — ABNT/ética — MÉDIA (A VERIFICAR a origem).
    Na mesma linha, capitulo3.tex:90 traz uma figura de Levada (2026) descrita como "Nosso conjunto de dados mostra
    quatro amostras de curvas de luz", misturando figura emprestada com dados próprios.

E24. capitulo5.tex:121-131 — `\begin{tabular}` com `\label{tab:features_final}` sem ambiente table e sem caption —
    formatação LaTeX — BAIXA-MÉDIA.
    O \ref aponta para a numeração errada. Bibliografia/ABNT: chave Tsiganis2009 para "Gomes (2009)" sem veículo
    (teseon.tex:237); "[1]" solto em Knieling (teseon.tex:205); URL do Simulator não é DOI (teseon.tex:232); PRAIA
    como "Package" (capitulo2.tex:65) × "Platform" (teseon.tex:222); AssafinPRAIA sem veículo; Fraser2024 (um
    levantamento de TNOs) citado para a "versatilidade das ocultações" (introducao.tex:14); Zhu2022 (constelação para
    ocultação na atmosfera terrestre) citado para "atmosferas planetárias" (introducao.tex:14); Saito2015 citado como
    respaldo para β=2 (capitulo3.tex:373), o que não é o tema do artigo (a verificar).

E25. Diversos de física/escrita — BAIXA.
    introducao.tex:14, "superada apenas por sondas", × capitulo2.tex:15, "precisão comparável à de sondas";
    capitulo2.tex:15, "a sombra na superfície terrestre ... escala unitária" (vale no plano fundamental; no solo há
    projeção oblíqua); introducao.tex:11, "15 a 100 UA", exclui Centauros a 5–15 UA (Chiron tem periélio a ~8,5 UA);
    capitulo2.tex:57, "cancelar efeitos sistemáticos, tendo em conta a curta duração do evento (extinção...)", é
    confuso: o cancelamento vem do caminho óptico comum às estrelas de comparação, não da duração;
    capitulo5.tex:534, "treinado em curvas predominantemente sintéticas" (são 41% do total) e "classifica corretamente
    ... três bandas e dois telescópios", quando só a Red-z está tabelada (a verificar); introducao.tex:22, a história
    de que os anéis de Quaoar foram "identificados apenas após uma revisita ... pelo próprio autor" (Q1R vem de Morgado
    et al. 2023, com vários eventos; Q2R de Pereira et al. 2023) está A VERIFICAR; erros de digitação: "continuará
    continua" (capitulo3.tex:111), "varios", "proximos" (capitulo3.tex:94), "a solução ... podem ser acompanhadas"
    (capitulo3.tex:75).

---------------------------------------------------------------------
## 3. Qualidade da escrita
---------------------------------------------------------------------
O texto é claro, organizado e didático, com bons exemplos numéricos para um leitor da física, e o português é em geral
correto. Os pontos fracos: (i) repetição excessiva das mesmas mensagens em vários capítulos (Quaoar/revisita,
"importância ≠ insubstituibilidade", limiar); (ii) a renumeração dos experimentos deixou resíduos (rótulos tab:metricas_5
para o Exp.2, pastas exp3 = Exp.5, resultado5 = Exp.2) e números que não batem entre capítulos; (iii) um tom promocional
justamente onde a evidência é mais fraca ("ponto operacional ideal", "com folga", "trivial", "corroborada", "sem
falsos alarmes"); (iv) legendas que leem errado as próprias figuras (ModelosSORA). Cuida-se melhor da forma do que da
crítica às próprias conclusões, o que contrasta com a epígrafe escolhida.

---------------------------------------------------------------------
## 4. Nota
---------------------------------------------------------------------
NOTA: 6,5 / 10.
A engenharia é sólida, transparente e reprodutível, as tabelas são internamente coerentes e há boa autocrítica pontual.
Mas o Cap. 2 tem erros de física (profundidade, convenção de Fresnel, leitura do modelo SORA), e a evidência central
(AUC≈1, recuperação dos anéis de Quaoar, baixo S/N) é inflada por negativas fáceis, vazamento entre recortes irmãos,
limiar escolhido no teste e escolhas post hoc.

---------------------------------------------------------------------
## 5. Notas para as próximas rodadas
---------------------------------------------------------------------
- Para o debate com "Sagan" (comunicação/escopo) e "Simons" (estatística/dados), minha posição central: o problema
  montado é fácil demais para medir o que a tese promete (sinais sutis); os números são verdadeiros, mas não respondem
  à pergunta científica. Prioridades de correção: (1) split agrupado por curva-mãe e evento; (2) limiar via CV/validação;
  (3) negativas reais e injeção de anéis sintéticos em curvas reais (curva de completeza); (4) varredura com janela
  deslizante em Quaoar para a taxa de falso alarme; (5) corrigir a física do Cap. 2 (E8–E11); (6) reescrever as
  conclusões (E7, E4, E6) com a força que a evidência permite.
- Correções rápidas e baratas: E11 (legenda), E9 (tirar a "convenção equivalente"), E8 (reescrever a profundidade com
  F_corpo), E21 (−0,125; J), E15/E16/E17/E18 (harmonizar texto e apêndice), E24 (envolver em table + caption).
- Pontos que posso ceder no debate: E23 e a história de Quaoar (introducao.tex:22) estão "a verificar"; a cadência de
  Quaoar/Umbriel não foi verificada (os dados não estão no repositório).

---------------------------------------------------------------------
## Rodada 2 — Debate
---------------------------------------------------------------------
(Li memoria_sagan.md, memoria_simons.md, critica_sagan_feynman.md e AUDITORIA_PIPELINE.md. Não li critica.pdf nem
SP\critica.txt. Rodei de novo os splits para reconciliar números; os scripts estão inline nesta sessão.)

Sagan, Simons: vou começar pelo que é mais barato, que é concordar. Depois vem a parte divertida, onde alguém errou
(às vezes fui eu).

### R2.1 Concordâncias (confirmo, com o item de cada um)
- **Limiar escolhido no teste.** Sagan E2, Simons E5 e meu E3. São três leituras independentes do mesmo código
  (train_model.py:801-836 usa y_test). Fechado.
- **Quaoar com τ e modelo escolhidos a posteriori.** Sagan E1, Simons E3/E4 e meu E4. Os três temos "2x contra o
  controle" no CatBoost. Fechado.
- **Hipótese "corroborada" sem nenhum comparador.** Sagan E5, Simons E6 e meu E7. Fechado.
- **Vazamento entre recortes-irmãos.** Simons E2 e meu E2. Simons chegou a isso pelo código e eu pela reprodução do
  split. Fechado. A reconciliação dos números está em R2.2.
- **"Teste de baixo S/N" que seleciona ocultações profundas.** Simons E10 e meu E6. Simons viu 48 curvas no treino, 10
  no teste e 9 fora; eu achei 40/58 com dip > 50% do registro. Os dois chegamos a mediana de Savgol_Min = 0,058, de
  forma independente. Fechado: a feature "SNR_dip" quebra quando o evento ocupa mais de metade da curva.
- **Física do Cap. 2:** Fresnel com a distância errada e na direção errada (Sagan E15, Simons E23, meu E9/E10); a
  legenda do SORA lida ao contrário (Sagan E16, meu E11); profundidade e "trânsito" (Sagan E17, meu E8). Os três vimos
  que a curva de Umbriel cai para ~0,25 por causa da luz do próprio Umbriel. Fechado.
- **Sintéticas mais limpas que o real** (σ_baseline 0,021 contra 0,058/0,104): Simons E8 e meu E1/E19. Os números
  batem.
- **Pré-processamento condicional à classe** (o z-score só nos recortes; a região do evento achada automaticamente em
  0,78): Simons E9 e meu E12. Fechado.
- Exemplo da logística (−0,125; J ≈ 0,676–0,678): Sagan E18, Simons E24, meu E21. A importância do XGB é "gain" e não
  "weight", e PVC não é permutação: Sagan E11, Simons E11, meu E15 (Simons confirmou o 0,566 = gain no modelo salvo).
  Faixas de F1 desatualizadas e "2 pp × 0,7 pp": Sagan E6/E7, Simons E13, meu E17. Tabela solta sem caption: os três.
  Unidades de tempo em JD: Simons E18, meu E13.

### R2.2 Discordâncias, correções e reconciliações
**(a) 18/38 (eu) × 21/38 (Simons): os dois estamos certos. São splits diferentes, com a mesma definição.**
Rodei os dois com a mesma definição ("recorte de teste cujo irmão antes/depois está no treino"; seed 42; após
.dropna()):
- Split MISTO 80/20 (Exp. 1/2, train_model.split_by_curve sobre todas as 1692 curvas): 38 recortes + 1 negativa nativa
  no teste; **21** dos 38 recortes têm o irmão no treino. É o número de Simons.
- Split REAL 80/20 (Exp. 3, split_real_holdout, sorteado só entre as 991 curvas reais elegíveis): 37 recortes + 1
  nativa = 38 negativas reais; **18** recortes têm o irmão no treino. É o meu número.
- Real 65/35: 26 dos 65 recortes (bate com Simons).
O "38" coincide por acaso: no misto são 38 recortes (39 negativas reais), no Exp. 3 são 38 negativas reais (37
recortes). Em todos os casos cerca de metade das negativas reais de teste tem um gêmeo no treino. Sagan, quando você
escreveu (sua A7) que a CV agrupa por curva, estava repetindo capitulo5.tex:654; o código não faz isso.

**(b) CatBoost "2x × 12x": os dois números estão na mesma tabela, só muda o denominador** (capitulo5.tex:501-504).
- Q2R₁ / controle de baseline = 0,058/0,029 = **2,0x**. Esse é o meu número e o de Sagan.
- Q2R₁ / "ruído parecido com anel" = 0,058/0,005 = **11,6x**. Esse é o de Simons e o do texto (:527, "~12x").
- Para completar: Q2R₂/controle = 15,7x; Q2R₂/ruído = 91x. XGBoost: Q2R₁/controle = 72x, Q2R₁/ruído = 87x;
  Q2R₂/controle = 134x, Q2R₂/ruído = 161x.
A lição de primeiros princípios: dependendo do modelo e de qual pedaço de céu vazio se escolhe para dividir, a "razão
de separação" vai de 2 a 160. Uma grandeza que muda 80 vezes com uma escolha arbitrária não é uma medida, é um
adjetivo. O controle honesto é a DISTRIBUIÇÃO de p̂ em muitas janelas de baseline da mesma duração, e o posto do anel
dentro dela.

**(c) Corrijo a mim mesmo: o meu E1 estava forte demais.** Escrevi que "o teste mede ... real × simulado". Os números
de Simons (AUC ≈ 0,999 das positivas contra negativas REAIS no Exp. 2; o Exp. 3 reproduz bit a bit com AUC
0,997–0,998) mostram que o classificador não está só reconhecendo o simulador. A formulação certa é que o teste mede
"há uma queda profunda?". As sintéticas inflam a ESPECIFICIDADE do teste misto (FPR sintético ≈ 0), mas a separação
positiva × negativa real é genuína para eventos profundos. O que continua de pé: o regime sutil não é testado, e as
negativas reais também são fáceis (minha AUC de uma única feature, Savgol_Min, contra recortes = 0,98).

**(d) O ML se paga. Aceito, e retiro qualquer insinuação contrária.** Três baselines independentes concordam:
critica_sagan_feynman.md:72-86 (Occ_depth sozinho: F1 0,905 no misto, 0,948 no só-real 65/35); Simons (LR com uma
feature: 0,926 no misto e 0,945 no real); eu (um limiar em Savgol_Min, in-sample: F1 0,963). Os ensembles levam isso a
~0,98–0,99, isto é, 3 a 10 vezes menos erros. A falha é de APRESENTAÇÃO: a tese não mostra a régua ao lado da floresta.

**(e) Sagan, sua E3 ("as 802 estão todas no dataset", ou seja, a mãe não foi excluída) está errada no mecanismo.**
Simons e eu verificamos que nenhuma das 125 mães sobra no dataset; o banco tinha 927/928 positivas. O que está errado
é a frase "o banco dispunha de 802 ... a partir delas" (capitulo5.tex:15, 206). O vazamento que existe é outro: o dos
irmãos (R2.2a) e o de cordas do mesmo evento (39/160 positivas de teste têm uma "corda-irmã" no treino).

**(f) Discordo do que o "Feynman" de antes (critica_sagan_feynman.md:190-204) concedeu.** Ele aceitou que Quaoar "é o
teste adversarial ... o modelo passou ... com τ=0,03 sem nenhum falso positivo". Não passou num sentido que eu possa
assinar:
(i) há uma janela de ruído, escolhida a olho, e dois controles;
(ii) τ foi fixado depois de ver as seis janelas;
(iii) o mais importante, conferido por mim em outputs/resultado5/predictions_*.csv: no PRÓPRIO conjunto de teste do
     Exp. 2, τ = 0,03 marca como positivas **4 das 39 negativas reais no XGBoost (10%)**, com 1 FN, e **7/39 (18%) no
     CatBoost**. Simons achou 6/38 (15,8%) no Exp. 3 e 15–17% em 10 sementes.
Se ~1 em cada 6 trechos reais sem evento passa de τ = 0,03, uma varredura de uma curva como a de Quaoar (~640 s,
~25–30 janelas de baseline de 20 s) produziria alguns falsos alarmes. É ordem de grandeza: o ruído do Gemini é baixo,
e precisaria rodar. A frase do resumo "sem introduzir falsos alarmes" é refutada pelos dados da própria tese.
Outro erro factual daquele texto: "você tinha três negativos reais nativos. Três!" O Exp. 3 tem 38 negativas reais
(37 recortes + 1 nativa). O problema não é ter 3; é que metade tem gêmeo no treino.

**(g) A AUDITORIA_PIPELINE.md repete descrições do texto em vez de ler o código.** Ela lista como "OK" o "class
balancing ... em todos os modelos" (o XGBoost não tem; train_model.py:123-132), diz "importância apenas via MDI
(Gini)" (o XGB é gain e o CatBoost é PVC), e repete o corte "<120 pontos" da janela (o código usa <40). O C3 dela (a
tripla obj/data/observador vinda por dois caminhos) é especulativo; o vazamento real e verificável é o dos irmãos, que
ela não viu. O C2 (o z-score apagando o dip) quase não morde na prática: remove_outliers só roda na etapa de recorte.
Se um dip curto some, a curva é pulada ("Nenhuma ocultação detectada") e não vira um negativo falso. O efeito real é a
assimetria de pré-processamento entre as classes (meu E12).

**(h) Pequeno ajuste com Sagan (A7):** o McNemar "concluir equivalência" não é virtude; não significativo ≠
equivalente, e com b+c ≤ 6 o teste exato dá p = 1 (meu E20). Concordo com você, porém, que não proclamar vencedor é a
atitude certa, e Simons mostrou o porquê: o vencedor muda com a semente (XGB 4/10, CB 3, RF 2, LR 1) e com a versão da
biblioteca.

### R2.3 O que vocês viram e eu não (e se aceito)
- **Simons, E1: os rótulos de experimento e as contagens estão errados no próprio artefato.** Conferi
  feature_names.pkl: o Exp. 4 tem **13** features (não 14), o Exp. 5 tem **12** (não 13), e o Exp. 6 tem 12 MAS mantém
  Savgol_Min (o apêndice diz "sem Savgol_Min"); o conjunto de 14 nunca foi rodado; resultado6.1 ("65/35") é cópia
  byte a byte de resultado5 (mesmo md5 de training_results.csv). ACEITO, e é mais grave que as minhas contagens de
  texto.
- **Simons, E12: no Exp. 6 a importância perdida pelo kmeans vai para Savgol_MIN, não para Savgol_std.** Isso
  contradiz capitulo5.tex:270 e apendice_experimentos.tex:123. ACEITO. A "lição" (importância ≠ insubstituibilidade)
  continua verdadeira, mas o mecanismo físico narrado ("dispersão dos dois patamares") é o da feature errada.
- **Simons, E14:** a tabela 65/35 ≠ a figura 65/35, e o Exp. 3 (80/20) não tem output arquivado; os resultados vêm de
  dois ambientes de software. ACEITO (reprodutibilidade).
- **Simons, linha "menores", sobre o Savgol_Max:** a tese diz que o máximo suavizado é "próximo de 1,0 em quase todas
  as curvas" (capitulo5.tex:113). Conferi: há positivas com Savgol_Max = **2453**, 115/802 com máximo suavizado > 1,5
  e 40 com fluxo mínimo < −0,5. ACEITO, e acrescento a leitura física: um fluxo normalizado de 2453, ou de −0,5, não é
  a estrela; é a normalização ou a fotometria quebrada (baseline perto de zero, fundo mal subtraído). ~14% das
  positivas têm problema de dado, e ninguém olhou. É o mesmo padrão de antes: o número absurdo estava lá, esperando
  alguém perguntar "isso faz sentido físico?".
- **Simons:** o Chiron tem 0 pontos no banco (capitulo4.tex:43 o anuncia como fonte); as datas do banco estão
  truncadas ao mês; o FPR real a τ=0,5 é de 4–9% em 10 sementes com split agrupado; os limiares que o critério
  declarado de "≥ 99,5%" de fato daria são RF 0,33, XGB 0,12 e CB 0,29. ACEITO tudo.
- **Sagan, E2:** o critério "sensibilidade mínima garantida ≥ 99,5%" não é aplicado na própria tabela (XGB e CB em
  98,75% com 2 FN), e com 160 positivas "garantida" é indefensável (IC95% de 100% de recall: 97,7–100%). ACEITO; eu
  não tinha visto.
- **Sagan, E9:** o solver é lbfgs (quase-Newton), não "gradiente descendente" como diz capitulo3.tex:123. ACEITO.
- **Sagan, E12:** "XGBoost e CatBoost mantêm F1 ≥ 0,990" (capitulo5.tex:574), mas o CatBoost do Exp. 6 tem 0,9874.
  ACEITO.
- **Sagan, E20:** "encontrar padrões desconhecidos" (capitulo3.tex:27) para um classificador supervisionado que
  procura um padrão CONHECIDO. ACEITO; é uma contradição conceitual boa.
- **Sagan, E23/E24:** a banca e o CDU ainda como modelo (teseon.tex:69, 72-75), o TODO no apêndice C, a falta de URL
  do repositório, e "filtro z (visível-vermelho)" (capitulo5.tex:520), quando a banda z, ~0,9 µm, é infravermelho
  próximo. ACEITO. O erro do z é física e eu deixei passar.
- **Sagan, 2b:** capitulo5.tex:525 explica a queda de p̂ com o "mínimo do Savitzky-Golay", mas o modelo do Exp. 2
  usado em Quaoar NÃO tem Savgol_Min. ACEITO. Somado ao meu E14 (a janela N/40 cresce com a janela temporal e apaga um
  dip de 0,5 s), a explicação "estrutural" do texto cita uma feature que o modelo nem usa.
- **Sagan, 2b:** o histograma do kmeans mostra positivas quase só com distância > 0,2, então o Q2R (~5% de
  profundidade) está fora da distribuição de treino. ACEITO; é a mesma conclusão do meu E1/E12, vista de outro ângulo.
- **Sagan, a narrativa** (anéis de Urano 1977, Chariklo 2014, Haumea 2017; a conclusão não volta aos TNOs): aceito
  como crítica de comunicação. Não é a minha área, mas concordo: as histórias de "sinal sutil achado por ocultação"
  são justamente o argumento físico da tese.

### R2.4 Os achados mudam a CONCLUSÃO ou só a força?
Separo as três conclusões, porque a natureza não se importa com o nosso resumo.
1. **"Classificar curvas com ocultação bem definida contra curvas sem evento funciona."** Só muda a FORÇA. Com split
   agrupado e 10 sementes (Simons), o F1 fica em ~0,98 ± 0,005, a AUC contra negativas reais em ≈0,999 e o FPR real
   em 4–9% a τ = 0,5. Os ensembles batem a régua de uma feature por um fator de 3 a 10 em erros. A "precisão de 100%"
   e o "0,99" saem; a conclusão fica.
2. **"A ferramenta recupera eventos sutis (anéis) com um ajuste de limiar, sem falsos alarmes."** MUDA A CONCLUSÃO. O
   limiar foi escolhido a posteriori em 6 janelas, e o mesmo τ = 0,03 marca 10–18% das negativas reais do próprio
   teste. Passa de "demonstrado" para "ilustrado, não validado". É a afirmação que o resumo vende como valor
   científico.
3. **"Comparável a CNN e a inspeção manual; robusto em baixo S/N."** MUDA A CONCLUSÃO: não testado. O "teste de baixo
   S/N" mediu ocultações profundas em curvas de treino.
Resumindo: o motor funciona; a promessa que justifica o motor (achar o que o olho perdeu) ainda não foi posta à prova.

**Frase honesta para o resumo (proposta):**
"Em curvas com ocultação bem definida, os classificadores separam eventos de não eventos com AUC ≈ 0,99–1,00
(F1 ≈ 0,98 entre partições; taxa de falsos positivos em negativas reais de 4–9%), superando um limiar sobre uma única
feature (F1 ≈ 0,90–0,95). Na curva de Quaoar, os anéis finos recebem probabilidades baixas (0,04–0,46), mas maiores
que as de duas janelas de controle; um limiar reduzido, escolhido a posteriori (τ = 0,03), os sinalizaria, porém esse
mesmo limiar marca 10–18% das negativas reais do conjunto de teste. A recuperação de eventos sutis é, portanto, uma
possibilidade promissora que exige validação sistemática (varredura por janela deslizante e injeção de anéis
sintéticos em curvas reais), e não um resultado demonstrado."

### R2.5 Nota revisada: 6,0 / 10 (era 6,5)
Sobe: o sinal contra negativas reais é genuíno, o ML supera os baselines triviais e o Exp. 3 é reprodutível bit a bit.
Concedo isso, e corrijo o meu E1.
Desce, por coisas que eu não tinha visto ou que se confirmaram:
- a afirmação central do resumo sobre eventos sutis "sem falsos alarmes" é refutada pelos arquivos de predição da
  própria tese (τ = 0,03: 10–18% de FP em negativas reais);
- os rótulos e contagens de experimento estão errados no artefato (Simons E1), e a tabela ≠ a figura 65/35;
- ~14% das positivas têm fluxo normalizado fisicamente impossível (máximo até 2453), e ninguém olhou;
- o vazamento entre irmãos foi confirmado em todos os splits.
Fico em 6,0, no mesmo lugar que vocês dois, mas por caminho próprio. Tudo é corrigível com texto e uma reanálise leve:
split agrupado, τ por CV, varredura cega em Quaoar, injeção e recuperação, e baseline trivial na tabela. Feito isso, a
nota sobe sozinha para 7,5–8.

---------------------------------------------------------------------
## Rodada 3 — Correções a partir da carta da banca (Dra. F. L. Rommel)
---------------------------------------------------------------------
Entregue em SP\correcoes_feynman.md: Geral f, j, m; Cap. 2 bb–nn; Cap. 4 1–19; referências; extras.
Respostas factuais tiradas do código e do banco:
- 923 prévias do VizieR baixadas; 912 inseridas no banco; 931 observações no total (928 positivas, 3 negativas).
- Chiron tem 0 pontos.
- Não existe checagem de alinhamento temporal no código: 19 curvas estão em dias e 2 têm o tempo fora de ordem.
- Os rótulos do VizieR são "positive" por padrão (vêm da pasta), não dos curadores.
- O simulador usa x = V_S(t − t₀) com uma faixa 1-D, isto é, só corda central.
- A janela de suavização corta em 40 pontos, não em 120.
Discordâncias com a banca: 1:1 "só para TNOs" (bb); V_S sem o movimento orbital da Terra (cc); "uma corda = perfil"
(cc.i); o acrônimo SORA já está aberto (jj.iv); vermelho = "dados" (mm); remover "ruído de fótons" (17a);
"representativo" (19); "posição ao longo da corda" não é erro (9).

---

# MEMÓRIA — Revisor "Sagan" (comunicação, narrativa, detector de baloney)

Dissertação: "Pipeline para Detecção Automatizada de Ocultações Estelares em Curvas de Luz com Técnicas de ML" (Thiago Laidler, ON).
Rodada 1 concluída em 2026-10-01. Base: ROOT\writing_latex\Tese\*.tex (todos lidos na íntegra).
NÃO li: critica.pdf, critica_sagan_feynman.md, AUDITORIA_PIPELINE.md (independência preservada).
Material de apoio consultado: roteiro_falado.md (início), roteiro_defesa.md (títulos e trechos: S1, S6, S32).
Figuras abertas (12): ModelosSORA, regressao_linear_ex1, quaoar_test, quaoar_recorte_tau_ajustado,
exp5/feature_importance_{xgboost,logistic_regression,catboost,random_forest}, exp3/feature_importance_xgboost,
exp2/feature_importance_xgboost, resultado3/histograma_kmeans_por_classe, learning_curves_xgb_catboost,
diagrama_1, OccUmbriel_outputExemplo2, LimbFitCircle.

Mapa das pastas de figuras (interno, confuso, mas consistente): pngs/exp1=Exp1, exp2=Exp4, exp3=Exp5, exp4=Exp6,
exp5=Exp2, exp7=variante 65/35 do Exp3. Labels LaTeX seguem a numeração antiga (sec:resultados_exp5 = Exp 2, etc.).

Contas que conferi (Python/à mão):
- Fresnel 40 UA, 500 nm -> 1,22 km (OK). Condorcet 25 árvores p=0,65 -> 0,940 (OK). Gini do exemplo (OK).
- Exemplo do gradiente da Reg. Logística: gradiente correto = -0,125 (texto diz -0,15); J após 1 passo = 0,678 (ou 0,675 c/ theta=0,15); texto diz 0,685. ERRO.
- Tabelas 5.x batem com contagens inteiras: teste misto = 160 positivas / 179 negativas (339). Exp3 = 160/38.
- Desvio-padrão de meia-gaussiana = 0,603 sigma (relevante para Occ_baseline_std).
- Real elegível = 802+186+3 = 991; treino real 80/20 = 793, 65/35 = 644 -> -18,8% do real / -10,0% do total (não "15%").

---------------------------------------------------------------------------------------------------
## 1. ACERTOS PRINCIPAIS

A1. Termos traduzidos/definidos na primeira ocorrência, como promete a introdução: "aprendizado de máquina (Machine Learning, ML)"
    e definição operacional de ML (introducao.tex:16); "fluxo de trabalho em etapas (pipeline)", "características numéricas (features)"
    (introducao.tex:26); "verdade de campo (ground truth)" (capitulo3.tex:38); sobreajuste/subajuste (capitulo3.tex:393).
A2. Exemplos numéricos que ensinam: Fresnel 1,2 km (capitulo2.tex:86-90, correto); redução de Gini (capitulo3.tex:201-215, correto);
    paradoxo da acurácia (capitulo3.tex:352); Condorcet 65% -> 94% (capitulo3.tex:237, correto).
A3. Honestidade sobre as fragilidades: ausência de estudo de concordância de rótulos (capitulo4.tex:85); curvas defeituosas descartadas
    e proveniência "local" (capitulo4.tex:49); só 38 negativas reais no teste (capitulo5.tex:326); n pequeno em Quaoar (capitulo5.tex:540);
    lista de limitações (capitulo6.tex:52-60).
A4. O Experimento 3 (teste só com curvas reais, sintéticas só no treino) é a pergunta certa a fazer (capitulo5.tex:301).
A5. A lição da ablação — "importância de feature não é sinônimo de insubstituibilidade" — é cientificamente correta e bem explicada
    (capitulo5.tex:270; apendice_experimentos.tex:105-123). As figuras de importância confirmam a redistribuição (Savgol_Min 0,58 no Exp4 ->
    kmeans 0,69 no Exp5 -> Savgol_std 0,57 no Exp2).
A6. Teste contra o próprio interesse: "A janela curta não é a causa" (capitulo5.tex:525) — hipótese testada, explicação mecanística
    (features globais diluem o dip) e ligação direta com trabalho futuro (capitulo6.tex:77).
A7. Humildade estatística: CV 5-fold estratificada com agrupamento por curva (capitulo5.tex:654) e McNemar concluindo equivalência
    dos modelos (capitulo5.tex:709), em vez de proclamar um "vencedor".
A8. Custo assimétrico FN/FP explicado com analogia acessível (triagem médica) e dois modos operacionais (capitulo5.tex:336-343, 434-441).
A9. Esclarecimento de escala quadros vs. curvas, que evita confusão do leitor (capitulo4.tex:45).
A10. Curvas de aprendizado por iteração bem lidas e a figura bate com o texto (capitulo5.tex:727; gaps 0,0215 / 0,0125 conferidos).

---------------------------------------------------------------------------------------------------
## 2. ERROS PRINCIPAIS (ordenados por severidade; [V] = verificado; [AV] = a verificar)

E1. [V] ALTA — ML/estatística + baloney. Estudo de caso de Quaoar: limiar escolhido depois de ver os dados e troca de modelo.
    capitulo5.tex:471 "A escolha do CatBoost-Exp.~2 é deliberada"; :515 "Baixando o limiar para $\tau = 0{,}03$ ... sem que o controle
    ($6\times10^{-4}$) ou o ruído ($5\times10^{-4}$) cruzem"; :527 "A análise de recortes destaca o XGBoost porque suas probabilidades são mais polarizadas".
    Por quê: (i) tau=0,03 foi posto "entre as duas escalas" já conhecendo os rótulos das 6 janelas; (ii) as janelas foram desenhadas onde
    os anéis já eram conhecidos (dados cedidos pelo autor de Quaoar2023, :458) — não é uma revisita às cegas; (iii) o modelo declarado
    (CatBoost) dá 0,029 ao controle e 0,058 ao Q2R (tabela :501-503): razão ~2x, e o controle fica a 0,001 do limiar; o "~86x"/"duas
    ordens de grandeza" (resumo teseon.tex:136; capitulo6.tex:43) vale só para o XGBoost, escolhido porque o número fica mais bonito.
    "Sensibilidade sobe de 50% para 100%" (:515) com n=4 eventos e 2 controles. O teste honesto seria uma janela deslizante sobre a curva
    inteira, reportando o posto dos anéis entre todas as janelas e os falsos alarmes com tau=0,03.
E2. [V] ALTA — ML/estatística. Ajuste de limiar feito no próprio conjunto de teste e critério declarado não aplicado.
    capitulo5.tex:387 "Para cada modelo, foram calculadas as métricas em função do limiar"; :412 "Regressão Logística com $\tau = 0{,}16$ atinge sensibilidade de 100\% ... ponto operacional ideal".
    Por quê: escolher tau no teste e reportar o desempenho nesse mesmo teste é otimista (não há conjunto de validação). Além disso, o
    critério adotado é "sensibilidade mínima garantida (ex.: >= 99,5%)" (:373, :382), mas XGBoost (tau=0,30) e CatBoost (tau=0,37) ficam
    em 98,75% com 2 FN (tabela :405-407). "Garantida" não se sustenta com 160 positivas.
E3. [V] ALTA — consistência numérica/ML (vazamento). As positivas que originaram recortes deveriam ser excluídas, mas as 802 estão todas no dataset.
    capitulo4.tex:115 "a curva positiva original é excluída do conjunto de positivos usados no treino"; :121 "positivas do banco (excluindo as usadas para recorte)"
    vs capitulo5.tex:206 "802 curvas positivas ... a partir delas, foram obtidos 186 negativos por recorte" e tabela :216 "Curvas positivas do banco ... 802".
    Por quê: ou a exclusão não foi feita (o que contradiz o Cap. 4 e permite que a mesma observação apareça como positiva no treino e como
    negativa no teste), ou as contagens estão erradas. O split principal (capitulo5.tex:226, "estratificada por curva") não diz se agrupa
    a mãe com os recortes; só a CV diz agrupar (:654).
E4. [AV, mas forte] ALTA — ML (atalho/confundimento). Possível atalho por comprimento/cadência e por origem das curvas.
    Todas as sintéticas são negativas (capitulo5.tex:15); os recortes são mais curtos que as curvas completas; várias features crescem com N
    ou dependem da cadência (chi2 são somas, capitulo4.tex:209-215; p-valores, :179; Occ_duration_s, :203). Nas figuras do Exp2, Occ_duration_s
    é a feature nº 1 na RL (|beta|~5) e no CatBoost (~24) (pngs/exp5). Por quê: o modelo pode estar aprendendo "comprimento/origem" em vez de
    "ocultação"; o F1~0,99 pede esse controle (por ex., recortes de mesmo comprimento, features normalizadas por N, teste de permutação).
E5. [V] ALTA — baloney/consistência. A hipótese é declarada "corroborada" sem nenhum termo de comparação.
    introducao.tex:32 "desempenho superior ou comparável ao de abordagens manuais ou baseadas em redes convolucionais"; capitulo6.tex:23 "é \textbf{corroborada}".
    Por quê: não há baseline CNN/ODNet nem inspeção manual no mesmo conjunto (grep confirma: Cap. 5 não menciona ODNet). Também
    desaparece o "superior" entre a introdução e a conclusão. Trata-se de uma afirmação extraordinária sem evidência.
E6. [V] ALTA — consistência numérica. Faixas de F1 contraditórias.
    capitulo5.tex:735 "F1-score entre 0,974 e 0,994 no teste misto ... e entre 0,975 e 0,982 no teste exclusivamente em curvas reais (Experimento~3)".
    Tabelas: o teste misto vai de 0,9841 a 0,9937 (tab. comparacao_f1); o Exp3 vai de 0,9778 a 0,9906 (capitulo5.tex:316-319). O resumo e o
    Cap. 6 dizem 0,978–0,994 (teseon.tex:136; capitulo6.tex:6). São números antigos (parecem da variante 65/35) que sobraram no texto.
E7. [V] MÉDIA-ALTA — consistência. "Queda de ≈2 pp" na variante 65/35 vs. "0,7 pp" no apêndice.
    capitulo5.tex:326 e :576 "queda de $\approx$2 pontos percentuais"; apendice_experimentos.tex:157 "recua de 0,9906 para 0,9838 (queda de apenas $\approx$0,7 ponto percentual)".
    Também "15% menos dados de treino" (apendice_experimentos.tex:139, :157) está errado: são -10% do treino total ou -19% do treino real.
    E chamar 80% vs 65% de "curva de aprendizado saturada em duas dimensões" (capitulo6.tex:37) é exagero: são 2 pontos, com conjuntos de teste diferentes.
E8. [V] MÉDIA-ALTA — consistência. Exp2 ≠ "ablação combinada": os conjuntos de features não batem.
    capitulo5.tex:21/:275 "11 features (sem Feature_Savgol_Min e sem kmeans_centroid_dist)"; apendice_experimentos.tex:77 o Exp6 já está "sem
    kmeans ... (sem Feature_Savgol_Min)" com 12. Pela contagem (Exp4 = 14, inclui Occ_n_frames_below_baseline; apendice_experimentos.tex:13),
    o Exp2 difere do Exp6 apenas pela remoção NÃO DOCUMENTADA de Occ_n_frames. A "Tabela do conjunto final, 13 features" (capitulo5.tex:119-131)
    inclui Savgol_Min e não inclui n_frames, enquanto o "Exp5 13 features" é outro conjunto. Cap.3:45 diz "14 ou 28 features"; Cap.6:33, "13–14";
    o operacional é 11. Além disso, a descrição do Exp4 em capitulo5.tex:268 omite duas remoções (28-12=16 ≠ 14).
E9. [V] MÉDIA — consistência ML. A Regressão Logística é descrita de três formas incompatíveis.
    capitulo4.tex:252 "regularização \(\ell_2\) (Ridge) ou \(\ell_1\) (Lasso); ... (\(C\) ou \(\alpha\)) escolhido via validação cruzada" e capitulo3.tex:169
    "utiliza-se Ridge ou Lasso" vs apendice_hiperparametros.tex:11-13,50 (l2, C=1,0 padrão, lbfgs, "sem ... validação cruzada").
    O solver lbfgs (quase-Newton) contradiz "A Regressão Logística é ajustada por gradiente descendente" (capitulo3.tex:123, :292).
E10. [V] MÉDIA — consistência/ML. Ponderação de classes.
    capitulo5.tex:228 "Utilizou-se ponderação das classes nos quatro algoritmos" vs apendice_hiperparametros.tex:36 "sem scale_pos_weight ...
    o desbalanceamento é tratado indiretamente pelo algoritmo" — o XGBoost não faz isso por padrão. Além disso, o dataset é quase
    balanceado (802/891), o que contradiz capitulo4.tex:266 "em que os dados são desbalanceados (muitas curvas sem ocultação)".
E11. [V/AV] MÉDIA — ML. A importância das features é descrita de forma contraditória e, em parte, errada.
    capitulo3.tex:224 e capitulo4.tex:258: RF/XGB/CatBoost usam "queda média na impureza (Gini)" vs capitulo5.tex:157 (XGB = "weight") e :163 (CatBoost).
    capitulo5.tex:163 descreve PredictionValuesChange como "mudança ... quando os valores de $x_j$ são permutados aleatoriamente" — está errado
    (PVC sai da estrutura das árvores; a variante baseada em perda é LossFunctionChange) e contradiz capitulo3.tex:266. [AV] Em xgboost 2.0.3,
    XGBClassifier.feature_importances_ usa "gain" por padrão para árvores, não "weight". A tabela :193 dá a escala XGB "0 a ≈0,15", mas as figuras
    mostram 0,57–0,69; "63% no XGBoost" (:749) não aparece em nenhuma figura (Exp5 ≈0,69); "consistentemente a mais importante" (:749) é falso no Exp4 (Savgol_Min 0,58).
E12. [V] MÉDIA — consistência. capitulo5.tex:574 "Nos Experimentos 6 e 2 ... XGBoost e CatBoost mantêm F1 $\geq 0{,}990$" — o CatBoost do Exp6 tem 0,9874 (apendice_experimentos.tex:89).
E13. [V] MÉDIA — narrativa contraditória. A generalização para dados reais é afirmada e negada.
    capitulo5.tex:326 "O Experimento~3 reforça que a pipeline é adequada para triagem em dados observacionais reais"; resumo "generalização para dados
    exclusivamente reais" vs capitulo6.tex:52 "a capacidade de generalização para um cenário puramente observacional não foi validada".
    Com 38 negativas reais (quase todas recortes das próprias positivas), especificidade 37/38 tem IC95% ~[0,86; 1,00]. Além disso, capitulo5.tex:534
    "treinado em curvas predominantemente sintéticas" está errado (41% do total; 0% das positivas), e "três bandas ... dois telescópios" não aparece nos resultados (só uma curva é analisada).
E14. [V] MÉDIA — ML/baloney. Avaliação em dados de treino apresentada como evidência, e introduzida só na conclusão.
    capitulo6.tex:18 "as 67 curvas do banco com $\mathrm{Occ\_SNR\_dip} < 3$ ... todas foram corretamente classificadas ... Embora essas curvas tenham
    participado do treinamento". Por quê: acertar o que já viu no treino não indica nada sobre baixo SNR; resultado novo não deveria aparecer pela primeira vez na conclusão.
E15. [V] MÉDIA — física. Escala de Fresnel com distância e direção erradas.
    capitulo2.tex:77 "\(D\) é a distância entre o observador e o corpo ocultante (ou, em convenções equivalentes, a distância estrela--corpo)" — não é
    equivalente: a estrela está, para todos os efeitos, no infinito; D é a distância observador–corpo. capitulo2.tex:90 "resolução espacial efetiva
    na direção perpendicular à corda" — a difração limita a resolução AO LONGO da corda (radial, nos tempos de imersão/emersão); na perpendicular, quem limita é o espaçamento entre cordas.
E16. [V] MÉDIA — física/legenda. A legenda do modelo do SORA descreve a figura de forma errada.
    capitulo2.tex:82 "difração de Fresnel (azul), ... e, resultante da combinação dessas componentes, o modelo geométrico (verde) ... dados observados (pontos vermelhos)".
    Na figura (pngs/ModelosSORA.png), o preto é Fresnel, o azul é o tamanho angular da estrela, o verde é o poço geométrico ANTES das convoluções e o
    vermelho é a resposta instrumental (o modelo integrado), não dados observados.
E17. [V] MÉDIA — física. Profundidade da queda e terminologia.
    capitulo2.tex:75 "durante o intervalo de tempo em que o trânsito ocorre" (o termo certo é ocultação; trânsito é outra coisa) e "em ocultações centrais
    ou próximas do centro, a queda pode ser total". Para estrela quase pontual, qualquer corda dentro da sombra dá queda total da estrela; o fluxo
    residual vem do brilho do próprio ocultante (a curva de Umbriel na Fig. 2.2d cai para ~0,25, não para 0), e não da posição da corda.
E18. [V] MÉDIA — consistência numérica (didática). capitulo3.tex:150 "$\partial J / \partial \theta_1 = ... = -0{,}15$" — o certo é -0,125; e "O custo cai
    para $J \approx 0{,}685$" — o certo é 0,678 (0,675 se theta=0,15). Num exemplo feito para ensinar, a conta precisa fechar.
E19. [V] MÉDIA — baloney/citações. Citações que não sustentam a frase.
    introducao.tex:14 "sua versatilidade vai de asteroides próximos a TNOs extremamente distantes \citep{Fraser2024}" (Fraser 2024 é um survey shift-and-stack
    da New Horizons, não trata de ocultação); "Ocultações são ainda empregadas há décadas no estudo de atmosferas planetárias \citep{Zhu2022}" (Zhu 2022 trata de
    sondagem da atmosfera TERRESTRE por constelação de satélites); física de ocultação citada no paper do ODNet (Cazeneuve2023). introducao.tex:24 Deisenroth (livro de matemática)
    citado como prova de que "já são usados para filtrar candidatos". capitulo3.tex:17 Gryak 2018 não trata de "conjecturar teoremas depois demonstrados". capitulo3.tex:373 Saito 2015 não
    defende beta=2. Faltam as referências primárias de RF (Breiman 2001), XGBoost (Chen & Guestrin 2016) e CatBoost (Prokhorenkova et al. 2018), todos citados via Géron ou sem citação.
E20. [V] MÉDIA — escrita/coerência conceitual. capitulo3.tex:27 "o ML atua sobretudo na função de \textbf{encontrar padrões desconhecidos}" — um
    classificador supervisionado treinado com ocultações rotuladas procura um padrão CONHECIDO. Contradiz a própria formulação (capitulo3.tex:38).
E21. [V] MÉDIA — física/método. A janela de suavização é descontínua e o texto critica o mesmo recurso que usa.
    capitulo4.tex:149 "utiliza-se \(N/40\) para séries longas (ex.: \(N > 120\) pontos) e \(N/3\) para séries mais curtas" — em N=119 a janela é 39 pontos; em N=121, 3 pontos.
    Janelas de N/3 apagam eventos curtos, exatamente a crítica que introducao.tex:24 faz aos "métodos que dispensam ML, por exemplo, janelas de suavização".
    [AV] capitulo4.tex:95: o corte por z-score |z|>3 pode remover os próprios pontos de uma ocultação curta e profunda; o texto não diz quando foi aplicado.
E22. [V] MÉDIA — formatação LaTeX. capitulo5.tex:121-131: tabela "solta" (\begin{tabular} com \label, fora de table e sem \caption). O \ref{tab:features_final}
    (:119) aponta para o contador errado e a tabela não entra na Lista de Tabelas.
E23. [V] MÉDIA — formatação/ABNT. Pendências de versão final: membros da banca ainda como modelo (teseon.tex:72-75 "Nome Sobrenome / Instituicao");
    apendice_ambiente.tex:26 "A data de geração do ambiente ... deve ser registrada pelo autor ao finalizar a dissertação" (um TODO no texto final);
    apendice_ambiente.tex:11 "Python: 3.x"; capitulo6.tex:31 "disponível para reprodução" sem URL ou DOI do repositório em lugar nenhum.
E24. [V/AV] MÉDIA — formatação/ética de figura. capitulo5.tex:477-478: a Fig. de Quaoar (pngs/quaoar_test.png: rótulos em inglês, insets com ajustes em vermelho)
    parece reproduzida de Pereira et al. 2023 sem "Fonte:", e o texto (:473) a apresenta como "a curva analisada após o pré-processamento". [AV] confirmar origem.
    Também: capitulo5.tex:520 "filtro $z$ (visível-vermelho)" — a banda z (~0,9 µm) é infravermelho próximo.
E25. [V] BAIXA-MÉDIA — consistência/escrita. Detalhes que corroem a confiança do leitor:
    capitulo4.tex:43 "Chiron, observada em 2023" (a ref. é a ocultação de 15/12/2022, teseon.tex:226); capitulo2.tex:65 PRAIA = "Package for the Reduction..." vs teseon.tex:222 "Platform for Reduction...";
    capitulo5.tex:682 (b = "A erra e B acerta") vs legenda :693 (b = "apenas A acerta"), e com b+c ≤ 6 caberia o McNemar exato que a própria ref. (Smith & Ruxton) recomenda;
    apendice_experimentos.tex:217 "O Capítulo~5 discute a importância ... com base na figura do Experimento~1" (é o Exp2); capitulo6.tex:71 o "real holdout" treinaria
    "apenas com curvas sintéticas e negativos por recorte" — ou seja, sem nenhuma positiva, o que é impossível; introducao.tex:11 "distâncias de 15 a 100~UA" exclui Centauros
    internos (Júpiter = 5 UA) e TNOs distantes.

---------------------------------------------------------------------------------------------------
## 2b. ACHADOS SECUNDÁRIOS (para o debate e para propostas de correção)

- Narrativa (Sagan, central): a introdução abre com formação e dinâmica (Morbidelli, Nice; introducao.tex:3-9), mas a tese não trata de dinâmica;
  a motivação para Centauros/TNOs cabe numa frase sem citação ("por preservarem características primitivas", :11). Ficam de fora as melhores histórias, que são
  justamente de "sinal sutil achado por ocultação": anéis de Urano (1977), Chariklo (2014, citado só para a figura), Haumea (2017) e o anel de Quaoar FORA do limite
  de Roche (Morgado2023, citado só de passagem em capitulo5.tex:449). A conclusão nunca volta à ciência dos TNOs: a história começa no Sistema Solar e termina
  na ablação do K-means. O roteiro oral tem um gancho muito melhor que o texto: "Quando a estrela apaga de vez, qualquer um vê. O problema são as curvas duvidosas"
  e "não é um juiz, é uma fila de prioridade para os olhos humanos". Vale levar isso para a Introdução e o Cap. 6.
- Falta mostrar onde o modelo erra: existem figuras de FN (pngs/resultado3/RF_curva_FN_*.png, LR_curva_FN_*.png) e o slide S32 ("Onde o modelo erra"),
  mas a tese não traz análise de erros.
- O histograma do kmeans (pngs/resultado3) mostra positivas quase só com distância > 0,2 (eventos profundos). Os eventos sutis (Q2R, ~5%) estão FORA da
  distribuição de treino, o que prevê o fracasso em tau=0,5 e reforça a limitação (capitulo6.tex:60). O argumento "objetivo de maior valor = sinais sutis"
  (introducao.tex:22) não foi treinado.
- Occ_baseline_std = desvio-padrão só dos pontos acima da mediana (capitulo4.tex:193): subestima o ruído (fator ~0,60), o que infla o SNR_dip em ~1,66x;
  isso afeta a leitura de "SNR<3" (capitulo6.tex:18). "Continuum" (capitulo4.tex:91) é jargão de espectroscopia mal aplicado; a citação de Morettin sobre resíduos ali é enchimento.
- capitulo5.tex:525 diz que o modelo usa "mínimo do Savitzky-Golay", mas o modelo do Exp2 usado em Quaoar NÃO tem Savgol_Min.
- capitulo5.tex:753 "AUC-ROC $\geq 0{,}998$ garante que a precisão se mantenha aceitável" — o Exp3 tem 0,9965, e AUC não garante precisão (RF com tau=0,01 tem 0,79).
  A precisão também depende da prevalência: os ~47% de positivas do teste são artificiais.
- capitulo5.tex:675 e :711 estão escritos como molde condicional ("Se o desvio padrão ... for pequeno"; "Se o McNemar indicar ...") depois dos resultados — cara de rascunho.
- Ecos/repetições: "importância ≠ insubstituibilidade" aparece 5 vezes (capitulo5.tex:270, :749; capitulo6.tex:13, :35; apendice_experimentos.tex:123); a anedota da revisita
  de Quaoar, 5 vezes (introducao.tex:22; capitulo2.tex:116; capitulo5.tex:339, :486; Cap. 6); "simplificar a pipeline eliminando o passo de K-Means" quase literal 3 vezes.
- Parágrafos longos demais: capitulo2.tex:77 (~400 palavras; repete "exposições longas ... mascarar detalhes da difração" duas vezes), capitulo3.tex:220,
  introducao.tex:24, capitulo4.tex:85 e :121.
- Termos em inglês sem padrão: "dataset" em itálico 7x e sem itálico 7x; "baseline" 17/13; "overfitting" 5/5; "feature" em negrito (capitulo3.tex:19);
  'threshold' entre aspas simples (capitulo3.tex:47); "a pipeline" vs "o pipeline" (capitulo5.tex:749; capitulo6.tex:35; apendice_ambiente.tex:7);
  aspas ASCII " em capitulo3.tex (17x; com babel brazil, " é ativo) e mistura "...'' (capitulo3.tex:45).
- Legendas: várias discutem em vez de descrever (capitulo3.tex:90, :380; capitulo5.tex:419); a capitulo3.tex:90 diz "Nosso conjunto de dados" para uma figura de
  Levada2026; a capitulo2.tex:107 não explica as linhas verdes tracejadas (cordas negativas — ótima chance de ligar com "negativas são úteis") e tem "incerteza vermelho";
  a figura da pipeline (pngs/diagrama_1.png) é UML genérica em inglês ("Is that Positive?", Feature1/2/3) e não informa nada; a figura de recortes tem legenda sem acentos e mistura PT/EN.
  Figuras de fonte fraca (Medium, cienciaenegocios, ResearchGate em vez do artigo original); Gauss/Laplace e manual_2 sem fonte.
- Bibliografia: chave Tsiganis2009 → GOMES 2009 sem periódico; Simulator com URL errada (página de TDM da Springer, teseon.tex:232); "[1]" solto (teseon.tex:205);
  Carleo "(Review paper excerpts)"; AssafinPRAIA e Shewchuk2024 nunca citados; estilos misturados (título entre aspas vs. em itálico); fora de ordem alfabética (ABNT 6023).
- Palavras-chave: "Aprendizado de Máquina" e "Machine Learning" são a mesma coisa; "Big Data" para 1693 curvas soa exagerado (teseon.tex:85-90). O resumo usa "Os resultados
  demonstram" duas vezes e põe a justificativa do custo FN/FP depois da afirmação que ela justifica.
- Gramática/tipografia: capitulo3.tex:94 "varios", "proximos"; :111 "continuará continua"; :75 "a solução ... podem ser acompanhadas" e \citep onde caberia \citet; :105 "será adaptado";
  capitulo4.tex:101 "suas classificação"; capitulo2.tex:116 "nos interessam também que ... descrito em \citep"; capitulo5.tex:488 "micrococultação"; capitulo2.tex:57, o parêntese
  "(extinção atmosférica, variações de transparência)" ficou depois de "curta duração do evento", longe de "efeitos sistemáticos", a que se refere.
- Labels com acento (capitulo4.tex:37 sec:aquisição; :99 sec:construção_dataset) [AV de compilação]; seção de considerações do Cap. 4 comentada (capitulo4.tex:273),
  deixando o fecho pendurado em "Fluxo de treinamento".
- [AV] capitulo5.tex:465: "removidos por um clip físico no intervalo [-2, 5]" — clip satura em vez de remover (99,999 vira 5, um pico espúrio). Confirmar no código.
- [AV] introducao.tex:22: "identificados apenas após uma revisita ... pelo próprio autor da análise \citep{Quaoar2023}" — o Q1R é de Morgado2023; confirmar a história da revisita.

---------------------------------------------------------------------------------------------------
## 3. QUALIDADE DA ESCRITA (parágrafo)

O português é claro e a vocação didática é real: os termos em inglês costumam ser traduzidos na primeira ocorrência, há exemplos numéricos que ensinam
e analogias (triagem médica, júri de Condorcet) que um leitor de física acompanha. Mas o texto ainda tem cara de versão
intermediária. Há números antigos que não batem com as tabelas, frases condicionais escritas como molde depois dos resultados, TODOs e campos de modelo
na versão final, parágrafos de 300–400 palavras, refrões repetidos (Quaoar e "importância ≠ insubstituibilidade") e um uso
irregular de itálico, aspas e gênero ("o/a pipeline"). Várias legendas interpretam em vez de descrever, e uma descreve a figura de forma errada (SORA).
O problema maior é narrativo: a história abre na formação do Sistema Solar, promete "sinais sutis" como objetivo de maior valor, treina num conjunto
dominado por quedas profundas e fecha na ablação do K-means, sem voltar aos TNOs. O roteiro oral da defesa conta essa história melhor que a tese.

---------------------------------------------------------------------------------------------------
## 4. NOTA: 6,0 / 10

Justificativa: a engenharia é sólida, a didática é boa e há honestidade sobre os limites, mas as afirmações centrais (Quaoar "duas ordens de grandeza",
hipótese "corroborada", generalização ao real) vão além da evidência: limiar escolhido no teste ou depois de ver os dados, possível vazamento ou atalho, sem baseline.
Somam-se muitas inconsistências numéricas e textuais verificáveis, que uma revisão cuidadosa corrigiria sem novos experimentos.

---------------------------------------------------------------------------------------------------
## 5. NOTAS PARA AS PRÓXIMAS RODADAS

Posições para o debate (Feynman / Simons):
- Com Feynman: convergimos em "não se enganar" (epígrafe da tese, teseon.tex:123!). Ironia a explorar: a epígrafe de Feynman e um tau escolhido depois de ver os dados.
  Ele deve atacar a física (Fresnel, legenda do SORA, profundidade) e o exemplo da RL; eu posso ceder a ele a física fina e manter comunicação e baloney.
- Com Simons: ele deve atacar vazamento, atalhos, validação e limiar no teste (E2-E4) e a base rate. Concordo; meu acréscimo é que o leitor não especialista
  sai do resumo acreditando numa capacidade (revisita de eventos sutis) que não foi testada às cegas.
- Onde posso ser contestado: E4 é [AV] (sem acesso ao código nesta rodada); E11, a parte do "gain" do XGBoost, é [AV]; E24, a origem da figura, é [AV].
Correções baratas a propor (sem novos experimentos): uniformizar números (E6-E8, E12), alinhar descrição da RL/pesos/importâncias (E9-E11), corrigir física
(E15-E17), refazer a conta (E18), trocar citações (E19), tabela com \caption (E22), preencher banca/TODOs/URL (E23), dar crédito à figura (E24), reescrever o
estudo de Quaoar como "ilustração com tau a posteriori" e reportar CatBoost e XGBoost lado a lado (E1), e reescrever a conclusão sobre a hipótese (E5).
Correções que pedem rodar algo: janela deslizante cega em Quaoar; tau escolhido em validação ou CV; split agrupado por observação; controle de comprimento das features.

---------------------------------------------------------------------------------------------------
## Rodada 2 — Debate

(Li memoria_feynman.md e memoria_simons.md na íntegra. Consultei agora critica_sagan_feynman.md e AUDITORIA_PIPELINE.md como evidência,
não como âncora. Continuo sem ler critica.pdf e evitei o critica.txt do scratchpad, que é derivado dele. Verificação própria nesta rodada:
contei as barras das figuras de importância — pngs/exp2 (Exp 4) tem 13 features, sem n_frames; pngs/exp3 (Exp 5) tem 12; pngs/exp4 (Exp 6)
tem 12 COM Feature_Savgol_Min = 0,64 e sem kmeans — e reli capitulo5.tex:525 ("Q2R2 caiu de 0,081 para 0,029").)

Caro Richard, caro Jim: vocês desceram ao código e às saídas; eu fiquei na página impressa. A combinação é boa, porque um leitor da banca
lê a página, mas a página tem de ser verdadeira em relação ao código. Vamos às contas.

### R2.1 Concordâncias (confirmo)

- Feynman E2 / Simons E2 — vazamento entre recortes-irmãos. Confirmo pelo texto: capitulo5.tex:654 afirma "todos os segmentos recortados
  de uma mesma curva ficam na mesma dobra", e vocês dois mostram que antes/depois têm curve_name distintos. Uma afirmação metodológica falsa
  custa mais credibilidade do que o vazamento custa em F1.
- Feynman E3 / Simons E5 — limiar escolhido no teste (o meu E2). Concordo também com o refinamento de Simons: pelo critério declarado
  (>=99,5%), os limiares seriam RF 0,33, XGB 0,12 e CB 0,29, com 3 FP e 0 FN cada; o "destaque" da RegLog (capitulo5.tex:412) é artefato da escolha.
  Agravante de comunicação: a AUDITORIA de abril (AUDITORIA_PIPELINE.md:242, C10) já apontava isso, e o texto final continua chamando
  o ponto de "ideal".
- Feynman E4 / Simons E3-E4 — Quaoar (o meu E1). Concordamos os três: CatBoost dá 2x contra o controle, o XGBoost foi escolhido depois de ver os
  números e tau=0,03 é a posteriori.
- Feynman E7 / Simons E6 — hipótese "corroborada" sem nenhum termo de comparação (o meu E5).
- Feynman E8-E11 / Simons E23 — física do Cap. 2: profundidade, Fresnel (D e direção) e legenda do SORA (os meus E15-E17). Três leituras
  independentes chegaram aos mesmos quatro erros, o que os torna obrigatórios.
- Feynman E21 / Simons E24 — o exemplo da logística (-0,125; J~0,678), o meu E18.
- Feynman E15 / Simons E11 — o default do XGBoost é "gain" (eles conferiram no código-fonte e na saída). Meu [AV] vira [V].
- Simons E7 / Feynman E1 — métricas sem incerteza; a ordem dos modelos muda com a semente e com a versão da biblioteca. Isso esvazia o
  "Por que XGBoost ... coerente com a leve vantagem do XGBoost no Exp. 3" (capitulo5.tex:527).
- Simons E21 / Feynman E19 — o "real holdout" sem positivas (o meu E25) e a contradição Exp. 3 x Limitações (o meu E13).

### R2.2 Discordâncias e nuances (com evidência)

(a) Recuo meu, Richard e Jim: o meu E3 da Rodada 1 ("as 802 incluem as mães dos recortes") ESTÁ ERRADO. Vocês verificaram que as 125 mães
    foram excluídas (build_dataset.py:204-208; o banco tinha 927/928 positivas). O erro é só de redação: capitulo5.tex:15 "o banco dispunha de 802"
    e :206 "a partir delas". Rebaixo de ALTA para MÉDIA (consistência textual). Fica a lição: confiei no texto, e o texto mentia sobre si mesmo.
(b) Meu E8 também estava errado no mecanismo: inferi que o Exp 2 removia n_frames sem dizer. Jim mostrou, e eu confirmei pelas barras, que
    n_frames NUNCA entrou: o Exp 4 tem 13 (não 14), o Exp 5 tem 12 (não 13) e o Exp 6 MANTÉM Savgol_Min (apendice_experimentos.tex:77 diz o
    contrário). O diagnóstico ("os rótulos dos experimentos estão errados") continua de pé, e o erro é maior do que eu supunha.
(c) 18/38 (Feynman) x 21/38 (Simons): não é contradição. Richard mediu no split do Exp 3 (só reais, 198 no teste: 18 de 61 pares separados);
    Jim, nos splits mistos 80/20 (38 recortes no teste). Para o texto: "cerca de metade (18–21 de 38, conforme o split) das negativas reais de
    teste tem o recorte-irmão no treino". Acrescento o achado de Richard, que é tão relevante quanto: 39/160 positivas de teste têm cordas do
    MESMO EVENTO no treino. O grupo certo é o evento, não só a curva-mãe.
(d) Nuance com Richard (E1, "números bons demais"): concordo que o teste mede o problema fácil, mas não diria que o 0,99 é "inflado" no
    sentido de falso. Jim mostrou AUC ~0,999 contra negativas REAIS e um ganho claro sobre baselines de 1–2 features (F1 0,93–0,95 -> 0,99);
    a sessão anterior achou o mesmo (critica_sagan_feynman.md:72-92: Occ_depth sozinho, F1 0,905 misto / 0,948 real). A frase correta é:
    "o número é verdadeiro e responde a uma pergunta mais fácil do que a que a Introdução faz".
(e) Nuance com Jim ("o vazamento de irmãos provavelmente infla pouco"): concordo quanto à magnitude, mas não quanto à prioridade. Para o leitor,
    capitulo5.tex:654 é uma frase falsa sobre o método, e frase falsa sobre método é o tipo de coisa que faz uma banca desconfiar de todo o resto.
(f) Discordo da "Sagan" da sessão anterior (critica_sagan_feynman.md:231, nota 8,5, "validação externa, adversarial ... padrão-ouro") e da réplica
    acolhida em :195-199 ("recuperados sem nenhum falso positivo"). Uma única janela de ruído escolhida a olho não é um teste adversarial; é um
    exemplo. As contas de Jim refutam o "sem falsos alarmes": em tau=0,03 há 4/39 FP em negativas reais no teste do Exp 2 (10%) e 1 FN
    remanescente; 6/38 (16%) no Exp 3; 15–17% em 10 sementes. E a própria tese mostra a fragilidade: ao ampliar a janela, Q2R2 cai para 0,029
    (capitulo5.tex:525), abaixo do tau=0,03 que o "recupera" (:515). O veredito depende de onde se corta a janela.
(g) Discordo da AUDITORIA em dois itens "OK": "Class balancing aplicado consistentemente em todos os modelos" (AUDITORIA_PIPELINE.md:327) é falso para
    o XGBoost (apendice_hiperparametros.tex:36); e "Split ... no nível de curva — OK" (:315) deixou passar exatamente o vazamento entre irmãos. O vetor
    C3 que a AUDITORIA imaginou (mesma observação duplicada em duas fontes) era mais exótico do que o real.
(h) Nuance com Richard (E14): a janela de suavização que cresce com N é uma explicação concorrente, e talvez melhor, para a queda de p ao
    ampliar a janela. A tese diz "hipótese ... refutada" e "a explicação é estrutural" (capitulo5.tex:525). O texto deveria apresentar as duas
    explicações como candidatas e não declarar o caso encerrado com dois pontos.

#### Como o texto deve assumir isso sem destruir a contribuição real

Regra de comunicação: o erro deve ser dito pelo autor, na primeira pessoa metodológica e com número, antes que a banca o encontre. Uma
correção feita às claras demonstra rigor.
1. Vazamento entre irmãos. Um parágrafo curto no Cap. 4/5: "Na revisão do código, verificou-se que os recortes antes/depois de uma mesma curva
   receberam identificadores distintos; no split adotado, 18–21 das 38 negativas reais de teste têm o irmão no treino, e 39 das 160 positivas
   têm cordas do mesmo evento no treino. Isso tende a otimizar a especificidade em negativas reais." Se houver tempo, refazer agrupando por
   evento e mostrar as duas linhas lado a lado. Se não houver, assumir como limitação quantificada e apagar a frase falsa de capitulo5.tex:654.
2. Contagem de features. UMA tabela-mestra (experimento | features removidas | nº real | pasta de saída) como única fonte de verdade, com a
   numeração em ordem lógica: 28 -> 13 -> 12 (sem Savgol_Min) -> 12 (sem kmeans) -> 11 -> só reais -> 65/35. Ao renumerar, as tabelas e figuras atuais continuam válidas.
3. "Importância ≠ insubstituibilidade" SOBREVIVE e FICA MAIS BONITA com os números corretos. A importância migra em cadeia: no Exp 4 (13)
   lidera Savgol_Min (0,58); sem Savgol_Min (Exp 5), kmeans sobe para 0,69; sem kmeans (Exp 6), Savgol_Min volta a 0,64; sem os dois (Exp 2),
   Savgol_std assume 0,57. O F1 não se mexe. A imagem que fica para o leitor: a importância comporta-se como água, ocupa o recipiente que estiver disponível. Isso exige
   corrigir capitulo5.tex:270 e apendice_experimentos.tex:123 ("sobretudo Feature_Savgol_std", falso no Exp 6) e substituí-los pela cadeia, que vale como figura própria.
4. Quaoar continua sendo o coração da tese, como ILUSTRAÇÃO, não como validação. O que permanece verdadeiro: (i) o corpo e o anel Q1R são detectados no
   limiar padrão, numa curva externa ao treino; (ii) nos dois modelos, Q2R fica acima da janela de ruído vizinha; (iii) o diagnóstico "features
   globais diluem eventos curtos" aponta para a janela deslizante, que é a contribuição conceitual mais fértil do trabalho. Sai o que é
   insustentável: "duas ordens de grandeza" sem dizer o modelo, "sem falsos alarmes", "validando", "demonstrou". E entra uma frase que transforma
   a fraqueza em informação operacional: recuperar anéis finos com tau=0,03 tem um preço, revisar cerca de 1 em cada 6–10 negativas reais.
   Para uma fila de prioridade, esse preço pode valer a pena, e dizer isso é honesto E útil.
5. O baseline de uma feature (F1 ~0,90–0,95) tem de entrar no Cap. 5. É a melhor defesa do trabalho: mostra que o ML se paga (5–10x menos
   erros) e, ao mesmo tempo, que a maior parte da tarefa é "tem um buraco fundo?". As duas metades da verdade, lado a lado.

### R2.3 O que vocês viram e eu não vi (e aceito)

De Feynman (aceito tudo, com [AV] onde eu não li o código):
- Negativas sintéticas com ruído ~3x menor (Occ_baseline_std 0,021 x 0,058/0,104), e uma única feature (Savgol_Min) com AUC 0,99.
- "depth ~0 sem ocultação" é falso (mediana 0,10–0,31 nas negativas), e o "SNR" de ruído puro dá ~6,5. Eu só tinha visto o fator 0,60 do sigma.
- A região "manual" é automática (fluxo < 0,78); quedas rasas acima de 0,78 entram como NEGATIVAS. Isso é, para mim, o achado narrativo mais
  grave: a tese promete sinais sutis (introducao.tex:22) e, por construção, ensina o modelo a chamá-los de negativos. Aceito.
- Remoção de outliers aplicada só aos recortes (pré-processamento dependente da classe). Aceito; Simons confirma.
- As "67 curvas SNR<3" são ocultações PROFUNDAS em que a mediana quebra, não eventos fracos (capitulo6.tex:18). Isso é mais forte que a minha crítica (in-sample).
- Occ_duration_s em DIAS para o Grupo do Rio/Umbriel (capitulo4.tex:67, "uniformização de unidades"), e Occ_duration_s é a feature nº 1 da RL e do
  CatBoost. Isso dá substância ao meu E4 (atalho): era suspeita, agora é um mecanismo concreto.
- O texto da janela de suavização difere do código (N<40, não N>120). O simulador já gera anéis, então um teste de injeção e recuperação
  (completeza x profundidade) seria o experimento natural, e é a melhor sugestão de trabalho futuro da mesa.
- O central flash em corda central com atmosfera e a projeção oblíqua da sombra no solo: aceito como física fina.
De Simons:
- O mapa experimento<->pasta<->nº real de features. resultado6.1 é cópia de resultado5; o Exp 3 80/20 não tem saída arquivada; a tabela 65/35 ≠
  a figura (exp7). Aceito: no capítulo de reprodutibilidade, isso pesa mais que qualquer vírgula.
- Em tau=0,03, FP de 10–17% em negativas reais, e Q2R2 ampliado cai abaixo de 0,03. Eu tinha a linha 525 na mão e não liguei os dois números. Aceito, com humildade.
- dropna -> 1692 amostras e imputer inócuo; Chiron com 0 pontos; datas truncadas ao mês; Savgol_Max "de baixa variância" com máximo de 2453
  (o que indica falhas de normalização em algumas positivas); n_frames x duration com Pearson de 0,43 (não "proporcional"); a média móvel listada
  como feature, mas que não é calculada; "Aur\'elin"; o README cita DAMIT/ALCDEF. Aceito tudo; nenhum item contradiz o que eu li.
- O vencedor muda com a semente (XGB 4/10, CB 3, RF 2, LR 1): aceito. Para a comunicação, isso significa abandonar o "modelo campeão" e falar em
  "quatro modelos estatisticamente equivalentes", como o próprio McNemar já sugeria.

### R2.4 A frase honesta do resumo e o tom do Cap. 6

Versão A (só com o que já está na tese, sem rodar nada), substituindo teseon.tex:136, de "Como validação em dados reais..." até "...ainda não identificados":
  "Como ilustração exploratória, aplicou-se a ferramenta a uma curva da ocultação por (50000) Quaoar externa ao treino: o corpo principal
  e o anel Q1R são detectados no limiar padrão, enquanto os cruzamentos do anel fino Q2R recebem probabilidades baixas (4–8% no XGBoost),
  ainda que superiores às de uma janela de ruído vizinha; um limiar reduzido, escolhido a posteriori, os recupera, mas a taxa de falsos alarmes
  desse regime ainda precisa ser medida. Sinais sutis permanecem, assim, o principal desafio em aberto."
Versão B (se o autor incorporar as reanálises de Simons e Feynman):
  "...um limiar reduzido (tau = 0,03), escolhido a posteriori, os recupera ao custo de sinalizar cerca de 10–16% das curvas negativas reais
  para revisão humana — um preço compatível com uma fila de prioridade, não com um classificador autônomo."
E, para os números gerais, também no resumo:
  "No teste misto, os quatro classificadores, estatisticamente equivalentes entre si, atingem F1 de 0,98–0,99 (contra 0,90–0,95 de um limiar único na
  profundidade da queda); o conjunto é dominado por ocultações profundas, e a taxa de falsos alarmes em negativas reais é maior que no teste misto."

Tom do Cap. 6 (o que eu pediria ao autor):
- Abrir pela espinha do roteiro oral, que é melhor que o texto: "O que se construiu não é um juiz; é uma fila de prioridade para os olhos humanos."
- Três camadas explícitas, cada uma com seus verbos. DEMONSTRADO ("mostrou-se"): pipeline reprodutível; o ML supera a régua de uma feature; a importância
  migra entre proxies colineares. ILUSTRADO ("ilustra", "sugere"): Quaoar. EM ABERTO ("não foi testado"): sinais sutis, negativas reais difíceis,
  comparação com CNN/ODNet e inspeção humana, vazamento por evento.
- A hipótese deixa de ser "corroborada" e passa a "não testada nesta forma; o que se mostrou foi desempenho alto num regime de ocultações profundas, com interpretabilidade".
- Deixar as limitações contaminarem as conclusões: nada de "garante", "valida", "demonstrou que recupera anéis".
- Fechar o círculo científico. A Introdução promete Centauros, TNOs e anéis; o Cap. 6 deveria terminar lembrando que o anel de Quaoar além do limite
  de Roche (Morgado2023) só foi visto porque alguém olhou de novo, e que esta ferramenta é um passo — ainda curto — para que o próximo não durma no arquivo.
  É mais modesto e mais memorável.

### R2.5 Nota revisada: 6,0 / 10 (mantida)

Justificativa: dois achados meus caem (a exclusão das mães funciona; o mecanismo do n_frames estava errado) e a contribuição real fica mais
sólida do que eu supunha (ML > régua; AUC ~0,999 contra negativas reais; a cadeia de migração da importância). Mas o que Feynman e Simons
acrescentaram atinge justamente a manchete do resumo: tau=0,03 dá 10–17% de falsos alarmes, o Q2R ampliado cai abaixo do limiar, os sinais sutis
são rotulados como negativos por construção, os rótulos e contagens dos experimentos estão errados e há saídas não arquivadas. Os dois
movimentos se compensam. Rejeito o 8,5 da sessão anterior, que se apoiou num "sem falsos positivos" refutado pelos próprios dados. Com reescrita
honesta (frase do resumo, tabela-mestra, cadeia de importância, baseline, física do Cap. 2), sem novos experimentos, o documento sobe a ~7,5;
com split por evento e uma varredura de Quaoar por janela deslizante, a ~8.

---------------------------------------------------------------------------------------------------
## Rodada 3 — Correções a partir da carta da banca (Dra. F. L. Rommel)
Saída: SP\correcoes_sagan.md — 26 blocos (Geral a, b, c, d, e, g, h, k, l, n, o, p; Cap. 1 q, r, s, t.i, t.ii, u, v, w, x.i–iii, y, z, aa),
9 novas \bibitem (8 com metadados verificados por WebSearch; ressalvas pontuais anotadas em cada uma) e 8 Extras.
Pontos-chave: a causa das aspas é o atalho " do babel brazil (25 pares em capitulo3.tex + epígrafe); \raggedbottom para o vão
(book twoside → \flushbottom); indentfirst; 28 trocas "sintéticas"→"simuladas"; 7 trocas S/N→SNR; 13 citações com parêntese duplo ou \citep textual.
Conflitos com R1/R2 registrados nos blocos: Saito2015 (capitulo3.tex:373), capitulo5.tex:534 e capitulo6.tex:52 (sobre as simuladas), Occ_SNR_dip, hipótese (aa) e
a crítica à suavização (x.ii) contra capitulo4.tex:149.
Scripts: SP\sagan_scan.py, SP\sagan_etc.py; saída bruta: SP\terms_out.txt.

---

# Memória do revisor "Simons" — Rodada 1 (revisão independente)

Dissertação: "Pipeline para Detecção Automatizada de Ocultações Estelares em Curvas de Luz com Técnicas de ML" (T. L. V. Cunha, ON).
Lente: rigor quantitativo (desenho experimental, vazamento, incerteza, sinal vs artefato, seleção no teste, consistência texto↔código↔outputs, reprodutibilidade).
Abreviações: T = writing_latex/Tese/ ; P = pipeline/ ; O = P/model_training/outputs/ ; SP = scratchpad.
Não li (por instrução): critica.pdf, critica_sagan_feynman.md, AUDITORIA_PIPELINE.md.

## 0. Fatos verificados (base para o debate)

### 0.1 Mapa experimento (tese) ↔ pasta de output ↔ pasta de figuras ↔ nº REAL de features
| Tese | Pasta O/ | Figuras T/pngs/ | nº features declarado | nº REAL (feature_names.pkl) |
|---|---|---|---|---|
| Exp 1 | resultado1_split0.8-0.2_all-features | exp1 | 28 | 28 |
| Exp 4 | resultado2_split0.8-0.2_less_features | exp2 | **14** | **13** (= Tabela "13 features finais", com Savgol_Min e kmeans) |
| Exp 5 | resultado3_..._noMin | exp3 | **13** | **12** (13 finais − Savgol_Min) |
| Exp 6 | resultado4_..._noKmeans | exp4 | 12 ("sem Savgol_Min" no apêndice) | 12 (13 finais − kmeans; **mantém** Savgol_Min) |
| Exp 2 | resultado5_..._noMin-noKmeans | exp5 | 11 | 11 |
| (nenhum) | resultado6.1_split0.65-0.35_... | exp6 | — | **cópia byte-a-byte de resultado5** (md5 idêntico; NÃO é 65/35) |
| Var. 65/35 do Exp 3 | resultado6.2_applyTestOnlyRealCurves | exp7 | 11 | 11 (mas métricas salvas ≠ tabela da tese) |
| Exp 3 (80/20 real) | **sem pasta** | **sem figura** | 11 | reproduzi exatamente em ambiente novo (ver 0.3) |
- O conjunto "14 features" (com Occ_n_frames_below_baseline) NUNCA foi rodado. Occ_n_frames nunca entrou em nenhum experimento reduzido.
- Rótulos LaTeX herdados da numeração antiga: sec:resultados_exp5 = Exp 2; tab:metricas_7 = Exp 3; comentário em P/model_training/train_model.py:97 ("Exp. 2 mostrou que derivadas...") = Exp 4 atual.

### 0.2 Dados e split (dataset_final.csv, DB SQLite)
- dataset_final.csv: 1693 linhas (802 db_positive, 702 synthetic, 186 artificial_negative, 3 db_negative). `load_dataset` faz `.dropna()` (train_model.py:175) → **1692 usadas** (cai 1 positiva: Hera_2005-04-01_BAllen, NaN em Occ_flux_min_over_baseline) → 801 pos / 891 neg; treino 1353, teste 339 (160 pos, 179 neg: 140 sintéticas + 38 recortes + 1 nativa). SimpleImputer é no-op.
- DB (P/data_warehouse/stellar_occultations.db): 931 observações, **928 positivas** (927 com pontos) e 3 negativas. 125 positivas-mãe foram excluídas por terem gerado os 186 recortes → 802. A tese diz "o banco dispunha de 802 positivas".
- Exclusão da positiva-mãe: VERIFICADA (0 das 125 mães presentes no dataset).
- MAS: recortes "_antes_artificial" e "_depois_artificial" da mesma mãe têm curve_name distintos; o split/CV agrupa por curve_name → em todos os splits mistos 80/20, **21 dos 38 recortes do teste têm o "irmão" no treino** (65/35 real: 26 de 65). Contradiz T/capitulo5.tex:654.
- Unidades de tempo: curvas de Umbriel (15 pos + 3 neg nativas) em **JD (dias)**, dt≈1,16e-5 d; VizieR em segundos → Occ_duration_s das 3 negativas nativas ≈1e-4 "s". Chiron: 1 observação, **0 pontos**.
- Datas no DB truncadas ao mês (todas terminam em "-01").
- Sintéticas: gerador chama `gerar_curvas_aleatorias(n_curvas=720, ..., seed=422)` (simulate_curve.py:845) mas o dataset tem 702 (a verificar). Os .dat sintéticos NÃO estão no repo (só PNG) e a curva de Quaoar também não → dataset e Quaoar não regeneráveis a partir do repo.
- Ruído: Occ_baseline_std mediano: sintética 0,021; recorte 0,058; positiva 0,104. AUC univariada sintética vs negativa-real: Savgol_std 0,941; kmeans 0,940; chi2_sw 0,922 → sintéticas são população distinguível (mais "limpas").
- Occ_chi2_constant é soma ∝ N (mediana: recorte 140; sintética 594; positiva 1220) → proxy de comprimento; AUC pos vs neg-real só com ela = 0,934.

### 0.3 Reexecuções (scripts em SP: check_outputs.py, repro_exp.py, seed_spread.py, baseline1f.py; ambiente local sklearn 1.9 / xgb 3.3 / catboost 1.2.10 ≠ Apêndice C)
- Exp 3 (80/20 teste real, 198 = 160+38): reproduz **exatamente** Tab. tab:metricas_7 (XGB 0,9848/0,9937/0,9875/0,9906/0,9984 etc.).
- Variante 65/35: reproduz **exatamente** a tabela do apêndice (XGB acc 0,9741, FP=2; RF P 0,9856 R 0,9751) — mas O/resultado6.2 e a figura T/pngs/exp7 (Fig. confusao_7) mostram XGB acc 0,971 (FP=3), RF TP 273/FP 3. Tabela ≠ figura.
- Exp 2 misto no ambiente novo: RF F1 0,9905 (tese 0,9874), XGB 0,9874 (tese 0,9906): o "melhor modelo" troca com a versão da biblioteca.
- 10 sementes, split agrupado pela curva-mãe: F1 médio misto ≈0,980–0,985 (σ≈0,005); FPR em negativas REAIS a τ=0,5: 4–9% (máx 17,5%); a τ=0,03: XGB 15–17%, CB ~24%, RF ~44%, LR ~42–49%. Vencedor por F1 varia com a semente (XGB 4/10, CB 3, RF 2, LR 1 no misto).
- No teste do Exp 2 (O/resultado5, XGB): τ=0,03 → 5 FP (4 dos 39 negativos reais = 10%) e ainda 1 FN (Lumen, p=0,0136). No Exp 3 (repro): XGB τ=0,03 → 6/38 FP (15,8%).
- AUC positivas vs negativas reais (Exp 2): ~0,999 → o sinal NÃO é só artefato sintético (ponto a favor).
- Baseline de 1 feature (LR balanceada, mesmo split): Savgol_std F1 0,926 (misto) / Max_Drawdown 0,945 (real); 2 features 0,96; ensembles 0,99 → ML agrega valor real, mas a tese não reporta nenhum baseline nulo.
- XGBoost `feature_importances_` salvo = **gain** (confere 0,566 de Savgol_std no Exp 2); por *weight* o topo seria Occ_duration_s (0,166).
- Importâncias Exp 6 (sem kmeans): absorvida por **Feature_Savgol_Min** (XGB 0,641; RF 0,277; CB 41,7), não por Savgol_std (0,157).
- "67 curvas SNR<3": 48 no treino, 10 no teste, 9 fora (mães dos recortes); mediana Feature_Savgol_Min = 0,058 e Amp 1,76 → são ocultações PROFUNDAS onde mediana/σ_baseline quebram (evento >50% dos pontos), não curvas de baixo SNR.
- Exemplo numérico da RegLog (cap.3): ∂J/∂θ1 = −0,125 (texto −0,15); J após passo = 0,676 (θ=0,15) ou 0,678 (θ=0,125); texto 0,685.
- Conferidos OK: Fresnel 40 UA/500 nm = 1,22 km; Condorcet 25×65% → 94,0%; exemplo de Gini; tabelas Exp 1, 2, 4, 5, 6, McNemar (Exp 4 = resultado2), CV (Exp 5 = resultado3) e tabela de limiar (resultado3) batem com os CSVs salvos.

## 1. ACERTOS principais
1. Exclusão da positiva-mãe ao gerar recortes — implementada e verificada (P/model_training/build_dataset.py:204-208, 459-461; T/capitulo4.tex:113-115).
2. Pré-processamento sem vazamento treino→teste: imputer e StandardScaler ajustados só no treino; scaler só para RegLog (train_model.py:224-249, 1249-1251; T/capitulo4.tex:127).
3. Desenho do Exp 3 (sintéticas apenas no treino, teste só real) é a pergunta certa e é reprodutível bit-a-bit (train_model.py:323-377; T/capitulo5.tex:296-322).
4. Tabelas dos Exp 1, 2, 4, 5, 6, McNemar e CV conferem com O/*/training_results.csv, mcnemar_results.csv, cross_validation_summary.csv (T/capitulo5.tex:240-249, 281-290, 663-672, 695-706; T/apendice_experimentos.tex:19-92).
5. Normalização por média dos dois quartis temporais mais altos e features Occ_* implementadas como descrito (P/model_training/astro_data_access.py:222-281; occ_features.py:326-393; T/capitulo4.tex:91, 185-222).
6. Ressalvas honestas: rótulos herdados sem concordância entre anotadores (T/capitulo4.tex:85), descarte de curvas defeituosas (T/capitulo4.tex:49), só 38 negativas reais (T/capitulo5.tex:326), n pequeno em Quaoar (T/capitulo5.tex:540).
7. Lição de ablação "importância ≠ insubstituibilidade" é metodologicamente valiosa (T/capitulo5.tex:270; T/capitulo5.tex:749).
8. Exemplos numéricos de física/estatística corretos: Fresnel (T/capitulo2.tex:86-89), Gini (T/capitulo3.tex:202-215), Condorcet (T/capitulo3.tex:237).
9. Sinal real: AUC positivas vs negativas reais ≈0,999 e ganho claro sobre baselines de 1–2 features (verificação própria, SP/baseline1f.py).
10. Hiperparâmetros do Apêndice B batem com o código (T/apendice_hiperparametros.tex:9-48 ↔ train_model.py:113-148), inclusive C=1, l2, lbfgs.

## 2. ERROS principais (arquivo:linha — citação — categoria — severidade — por quê)

E1. T/capitulo5.tex:268, T/apendice_experimentos.tex:13,45,77, T/capitulo5.tex:550-557,570,741, T/capitulo6.tex:11,33 — "O Experimento~4 (14 features)… Experimento~5 (13 features)" — consistência numérica — ALTA. feature_names.pkl: Exp 4 = 13, Exp 5 = 12; Exp 6 mantém Savgol_Min (apêndice:77 diz "sem Feature_Savgol_Min"). O conjunto de 14 nunca foi rodado; a lista de remoções do cap.5:268 (12 removidas → 16) nem bate com 14. Toda a narrativa de "redução progressiva" e a Tab. comparacao_f1 estão com rótulos errados; resultado6.1 ("65/35") é duplicata de resultado5.

E2. T/capitulo5.tex:654 — "todos os segmentos recortados de uma mesma curva ficam na mesma dobra" — ML/estatística (vazamento) — ALTA. Código agrupa por curve_name (train_model.py:279-320, 715-752); "antes"/"depois" têm nomes distintos → 21/38 recortes do teste têm o irmão (mesma estrela, noite, telescópio) no treino. Afirmação falsa; especificidade em negativas reais otimista.

E3. T/teseon.tex:136, T/capitulo5.tex:515, T/capitulo6.tex:43 — "um ajuste simples do limiar é suficiente para recuperar esses eventos sutis sem introduzir falsos alarmes" / "τ = 0,03" — ML/estatística — ALTA. τ escolhido a posteriori sobre as mesmas 6 janelas (2 controles). No próprio teste do Exp 2, XGB a τ=0,03 dá 4/39 FP em negativas reais (10%) e ainda 1 FN; no Exp 3, 6/38 (15,8%); em 10 sementes, 15–17%. Além disso a janela ampliada de Q2R₂ (p=0,029, cap.5:525) já cai abaixo de 0,03 → veredito instável.

E4. T/teseon.tex:136, T/capitulo5.tex:513,527, T/capitulo6.tex:43 — "cerca de duas ordens de grandeza superiores às atribuídas a trechos de ruído semelhantes" — ML/estatística — ALTA. Vale só para XGB (86×) e contra UMA janela de ruído de 10 s; para o CatBoost (modelo de referência do Exp 2) Q2R₁ = 0,058 vs ruído 0,005 (12×) e vs controle 0,029 (2×). Troca de modelo (XGB "mais polarizado") decidida olhando os mesmos dados = seleção no teste. Falta distribuição nula (muitas janelas de baseline de mesma duração).

E5. T/capitulo5.tex:373,382,387-412 — "adota-se o critério de sensibilidade mínima garantida (≥99,5%)" — ML/estatística — ALTA. (i) Limiares escolhidos no próprio conjunto de teste (train_model.py:801-839), sem validação; (ii) a tabela não aplica o critério: RF τ=0,45 (1 FN), XGB 0,30 e CB 0,37 (2 FN cada). Pelo critério declarado seriam RF 0,33, XGB 0,12, CB 0,29 (todos 3 FP/0 FN, threshold_analysis.csv de resultado3); o "destaque" da RegLog é artefato da escolha. Com 160 positivas, 100% de recall tem IC95% [97,7%, 100%] — "garantida" é indefensável. E a análise é feita no Exp 5, enquanto Quaoar usa Exp 2.

E6. T/capitulo6.tex:23, T/introducao.tex:32 — "hipótese… comparável a abordagens baseadas em redes convolucionais ou inspeção manual… é corroborada" — ML/lógica científica — ALTA. Nenhuma comparação com ODNet, CNN, inspeção manual ou sequer baseline trivial é apresentada. O script P/model_in_practice/quaoar_baseline_vs_ml.py existe mas não entra na tese. Hipótese não testada ≠ corroborada.

E7. T/capitulo5.tex:252,326,576,735-737; T/capitulo6.tex:41 — métricas pontuais sem incerteza ("precisão de 100%", "F1 = 0,9937 lidera") — ML/estatística — ALTA. Diferenças entre modelos = 1–3 curvas; McNemar não significativo; a ordem dos modelos muda com a semente e com a versão da biblioteca (Exp 2 em ambiente novo: RF 0,9905, XGB 0,9874). Precisão no teste misto é inflada por 140 sintéticas fáceis: FPR em negativas reais é 4–9% (média em 10 sementes). Faltam IC binomiais, FPR por fonte e prevalência realista.

E8. T/capitulo4.tex:119; T/capitulo6.tex:52 — "submetidas ao mesmo tipo de ruído e normalização das curvas reais" / "geradas com base em propriedades estatísticas de curvas reais" — física/ML (artefato) — ALTA. simulate_curve.py:735-748 sorteia parâmetros uniformes à mão (mag 11–14,5, t_exp 0,05–0,25 s); ruído branco, σ_baseline mediano 0,021 vs 0,058 (recortes) e 0,104 (positivas); sintéticas são separáveis das negativas reais (AUC até 0,94). Atalho "ruído baixo → negativo" é plausível.

E9. T/capitulo4.tex:115; P/model_training/build_dataset.py:69-124 — "identifica-se a região de ocultação de forma manual" — ML (pré-processamento condicional à classe) — MÉDIA-ALTA. A região é detectada automaticamente (fluxo < 0,78, primeiro/último ponto) com aceite manual, e a remoção de outliers z>3 é aplicada SÓ aos recortes (negativos), não às positivas nem às sintéticas → pré-processamento diferente por classe; recortes vêm só de mães com dip >22% e são curtos (chi2_constant ∝ N vira proxy de comprimento). Nada disso está no texto.

E10. T/capitulo6.tex:18 — "as 67 curvas do banco com Occ_SNR_dip < 3… todas corretamente classificadas" — ML/física — MÉDIA-ALTA. 48/67 estavam no treino (avaliação in-sample) e o corte SNR<3 seleciona ocultações profundas onde mediana e σ(f≥mediana) quebram (mediana Savgol_Min = 0,058), não curvas ruidosas. O teste não mede o que diz medir.

E11. T/capitulo5.tex:155-159,193,594 — "feature_importances_ retorna, por padrão, a métrica weight" — escrita/ML (texto ≠ código) — MÉDIA. O modelo salvo usa gain (0,566 para Savgol_std = gain; por weight seria 0,085). A escala típica de "0 a ≈0,15" (Tab. metodos_importancia) também está errada (0,57–0,69). E T/capitulo5.tex:163 descreve PredictionValuesChange como permutação (errado); T/capitulo3.tex:224 e T/capitulo4.tex:258 dizem "Gini para RF, XGBoost e CatBoost", contradizendo o cap.5 e o cap.3:266.

E12. T/capitulo5.tex:270; T/apendice_experimentos.tex:123 — "redistribuída… sobretudo Feature_Savgol_std" — consistência — MÉDIA. No Exp 6 (sem kmeans, com Savgol_Min) a importância vai para Feature_Savgol_Min (XGB 0,64; RF 0,28; CB 41,7). Savgol_std só domina no Exp 2, quando Savgol_Min também saiu. Também "63% no XGBoost" (cap.5:749) não bate com nenhuma pasta (Exp 5: 0,689; Exp 1: 0,236) — a verificar.

E13. T/capitulo5.tex:326,576 vs T/apendice_experimentos.tex:157 — "A queda de ≈2 pontos percentuais observada na variante 65/35" vs "queda de apenas ≈0,7 ponto percentual" — consistência — MÉDIA. Reforçado por T/capitulo5.tex:735 ("F1 entre 0,974 e 0,994 no teste misto… entre 0,975 e 0,982 no teste real"), resquício de quando o "Exp 3" era o run 65/35 (resultado6.2); as tabelas atuais dão misto 0,9841–0,9937 e real 0,9778–0,9906. T/capitulo5.tex:753 "AUC-ROC ≥ 0,998" contradiz Exp 3 (0,9965).

E14. T/apendice_experimentos.tex:143-155 vs :161,169 (T/pngs/exp7) — tabela 65/35 ≠ figura — reprodutibilidade — MÉDIA. A tabela (XGB acc 0,9741, FP 2) vem de uma reexecução não arquivada; a figura e O/resultado6.2 mostram acc 0,971 (FP 3) e RF 273/3. O Exp 3 principal não tem output nem figura salvos. Os resultados vêm de dois ambientes de software diferentes, e o Apêndice C lista só um ("Python 3.x"; "a data… deve ser registrada pelo autor", apendice_ambiente.tex:11,26); requirements_frozen.txt não é um freeze real.

E15. T/capitulo5.tex:15,206,216-221; T/teseon.tex:136 — "o banco dispunha de 802 curvas positivas e apenas 3 negativas… a partir delas, 186 negativos por recorte" — consistência — MÉDIA. O banco tem 927/928 positivas; 802 é o que sobra após excluir as 125 mães. "A partir delas" é falso (os recortes vêm de curvas que não estão entre as 802). Além disso o treino usa 1692 (801 positivas) por causa do dropna, e o cap.5:226 dá "aproximadamente 178–179/160–161" quando são exatamente 179/160.

E16. T/capitulo4.tex:236; T/capitulo5.tex:27 — "Valores faltantes (NaN) são preenchidos pela mediana… (SimpleImputer)" — texto ≠ código — BAIXA-MÉDIA. train_model.py:175 faz dropna antes do split; o imputer nunca atua.

E17. T/capitulo4.tex:149 — "utiliza-se N/40 para séries longas (ex.: N > 120 pontos) e N/3 para séries mais curtas" — texto ≠ código — BAIXA-MÉDIA. build_dataset.py:316-321 usa o corte N<40; para 40≤N<120 a janela é 3, e há descontinuidade (N=39 → 13; N=40 → 3). Também T/capitulo4.tex:152 e 228 dizem que máximo/mínimo da média móvel são features, mas com use_filter='savgol' (build_dataset.py:332-344) eles não são calculados.

E18. T/capitulo4.tex:67 e :43 — "uniformização de unidades quando necessário" / dados de Chiron — física/consistência — MÉDIA. Curvas de Umbriel em JD (dias) e VizieR em segundos → Occ_duration_s (feature nº1 da RegLog e do CatBoost no Exp 2) não está em segundos para 18 curvas, incluindo as 3 negativas nativas. Chiron: 1 observação com 0 pontos, ou seja, não contribui. Ref. Chiron2023 é de evento de dez/2022, não "observada em 2023".

E19. T/capitulo4.tex:252; T/capitulo3.tex:123,169 — "C escolhido via validação cruzada" / "ajuste realizado por gradiente descendente" / "utiliza-se Ridge ou Lasso" — texto ≠ código — MÉDIA-BAIXA. Código e Apêndice B: C=1 fixo, só l2, solver lbfgs (quasi-Newton). T/capitulo5.tex:228 "ponderação das classes nos quatro algoritmos" contradiz T/apendice_hiperparametros.tex:36 e train_model.py:123-132 (XGB sem scale_pos_weight).

E20. T/capitulo5.tex:17-25,275,116 — ordem e seleção dos experimentos — ML (seleção no teste) — MÉDIA-ALTA. Seis configurações avaliadas no MESMO teste de 339 curvas, e a "configuração enxuta… sem perda de desempenho" é escolhida pelo F1 de teste (jardim de caminhos bifurcados). As ablações removem 15 features de uma vez, então "remoção das derivadas não causou perda" (cap.5:116) não é identificável. Exp 2 (o mais reduzido) numerado antes dos intermediários 4–6 confunde o leitor.

E21. T/capitulo6.tex:71 — "Experimento real holdout: reservar todas as curvas reais… treinando apenas com curvas sintéticas e negativos por recorte" — lógica/ML — MÉDIA. Treino sem nenhuma positiva é impossível, e negativos por recorte SÃO curvas reais. Também T/capitulo6.tex:52 ("generalização… puramente observacional não foi validada") contradiz T/capitulo5.tex:326 ("Exp 3 reforça que a pipeline é adequada para triagem em dados observacionais reais").

E22. T/capitulo4.tex:193,207-222; occ_features.py:316-370 — "σ_baseline… ruído fotométrico" / "Chi² do modelo constante" — física/estatística — MÉDIA. σ(f≥mediana) é o desvio de meia distribuição (≈0,60σ para gaussiana) → SNR_dip inflado ~1,7×; o "χ²" usa MAD sem o fator 1,4826, nenhuma barra de erro fotométrica (o DB só guarda time, flux) e é uma soma ∝ N (não normalizada por graus de liberdade). Não é χ² no sentido estatístico.

E23. T/capitulo2.tex:90 e :77 — "Essa escala define a resolução espacial efetiva na direção perpendicular à corda" / "(ou, em convenções equivalentes, a distância estrela--corpo)" — física — MÉDIA/BAIXA. A difração limita a resolução AO LONGO da corda (direção radial ao limbo, ao longo do movimento da sombra); a resolução perpendicular vem do espaçamento entre cordas. D é a distância observador–corpo; a distância estrela–corpo não é equivalente (estrela no infinito).

E24. T/capitulo3.tex:150 — "∂J/∂θ1 = … = −0,15 … O custo cai para J ≈ 0,685" — consistência numérica — BAIXA-MÉDIA. O correto é −0,125; com θ1=0,15 dá J=0,676 (0,678 com θ1=0,125). As probabilidades são calculadas com o valor errado. Nota: as p das negativas também sobem (0,5→0,51), então "direção correta" vale só para a ordenação.

E25. T/capitulo5.tex:121-131 — `\begin{tabular}` + `\label{tab:features_final}` sem ambiente table nem \caption — formatação LaTeX — MÉDIA. \ref{tab:features_final} (cap.5:119) vai imprimir número de seção. Outros: banca e CDU placeholders (T/teseon.tex:69,72-75); "Aur\'elin" → Aurélien (teseon.tex:193); chave Tsiganis2009 aponta para Gomes 2009 sem periódico, para o Modelo de Nice (introducao.tex:9; teseon.tex:237); "[1]" solto (teseon.tex:205); URL errada no Simulator (teseon.tex:232); Carleo incompleto (teseon.tex:245); aspas retas "…" (teseon.tex:123, cap.3); labels com acentos (capitulo4.tex:37,99, a verificar na compilação); "14 ou 28 features" (capitulo3.tex:45); T/apendice_experimentos.tex:217 diz que o cap.5 usa a figura do Exp 1 (usa a do Exp 2).

Menores (baixa): McNemar com b/c invertidos entre texto e legenda (T/capitulo5.tex:682 vs 693; o código segue a legenda); a correção de continuidade dá χ²=0,5 com b=c (deveria ser 0; para b+c<25 o padrão é o teste binomial exato). Savgol_Max removida por "variância muito baixa" (T/capitulo5.tex:112-113), mas positivas têm máximo até 2453 e σ=86,6. n_frames vs duration "proporcional" (cap.5:109-110), mas Pearson é 0,43. P/README.md cita DAMIT/ALCDEF como fontes (contradiz a tese). A revisita do "próprio autor" na descoberta dos anéis (introducao.tex:22) está a verificar na fonte. Só a curva Red-z de Quaoar tem números; as outras duas bandas não (cap.5:534).

## 3. Qualidade da escrita
Português correto, didático e bem organizado. Os capítulos 3 e 4 explicam ML com clareza rara para o público de astronomia (exemplos numéricos, MAP bayesiano, viés–variância). Há, porém, muita redundância (métricas definidas em três capítulos; "importância ≠ insubstituibilidade" repetida 5×) e vestígios de renumeração dos experimentos (labels, pastas, contagens de features, faixas de F1 desatualizadas) que minam a confiança do leitor atento. Erros tipográficos pontuais ("continuará continua", "varios", "proximos", "nos interessam… que sejam"). O tom é por vezes mais assertivo do que os dados permitem ("demonstra", "garante", "corroborada", "sem falsos alarmes", "refutada"), sobretudo na seção de Quaoar e nas conclusões.

## 4. Nota: 6,0 / 10
Pipeline completa e funcional, com sinal real (AUC ≈0,999 contra negativas reais; Exp 3 reprodutível) e boas práticas básicas contra vazamento. Mas a nomenclatura e as contagens dos experimentos estão erradas, há vazamento entre recortes-irmãos contrariando o texto, limiares e configurações são escolhidos no teste e as afirmações de Quaoar e de "sem falsos alarmes" são refutadas pelos próprios dados. Tudo é corrigível (texto + reanálise leve).

## 5. Notas para as próximas rodadas (debate Feynman/Sagan; carta da banca)
- Posições que vou defender: (a) corrigir E1 (rótulos e contagens) é obrigatório e barato; (b) refazer split/CV agrupando por curva-mãe (StratifiedGroupKFold), com grupo = nome sem o sufixo _antes/_depois_artificial; (c) reportar FPR em negativas reais com IC (Clopper-Pearson) e métricas por fonte; (d) escolher τ por CV no treino e reportar no teste intocado; (e) para Quaoar: distribuição nula de p em N janelas de baseline com a mesma duração de Q2R, FPR a τ=0,03 e mesmo modelo do Exp 2 (ou declarar a troca); (f) reescrever o resumo sem "sem falsos alarmes" e "duas ordens de grandeza" genéricos; (g) baseline nulo (1 feature) e retirar "hipótese corroborada" ou reformular; (h) arquivar o Exp 3 80/20 e alinhar a figura e a tabela 65/35; registrar as versões reais.
- Concessões possíveis: o vazamento de irmãos provavelmente infla pouco (o FPR real já era 2–9%); sintéticas distintas não invalidam o Exp 3; AUC alta contra negativas reais é robusta.
- Correções rápidas de texto: E11, E13, E15–E19, E21, E23–E25.
- Scripts prontos em SP: check_outputs.py, repro_exp.py (reproduz Exp 2/65-35/Exp 3), seed_spread.py (10 sementes, grupo = curva-mãe), baseline1f.py.

## Rodada 2 — Debate

*(Simons, para Feynman e Sagan. Lidos: memoria_feynman.md, memoria_sagan.md, AUDITORIA_PIPELINE.md, critica_sagan_feynman.md. Não lidos: critica.pdf e critica.txt. Script novo: SP/reconcile_siblings.py.)*

Feynman, Sagan: concordamos nas três coisas que importam. O sinal existe, os números das tabelas são verdadeiros e as afirmações do resumo vão além deles. A minha contribuição é contar.

### 1. Concordâncias (confirmo com dados)
- **Feynman E2 / Sagan E3-split**: o split e a CV não agrupam pela curva-mãe. Confirmo (ver 2a para a reconciliação 21 × 18).
- **Feynman E3 / Sagan E2**: limiar escolhido no próprio teste, e o critério declarado não é aplicado. Confirmo pelo threshold_analysis.csv (resultado3). Pelo critério de recall ≥ 99,5%, os limiares seriam RF 0,33, XGB 0,12 e CB 0,29, todos com 3 FP e 0 FN. Os τ da tabela (0,45 / 0,30 / 0,37) deixam 1–2 FN.
- **Feynman E4 / Sagan E1**: Quaoar com τ e modelo escolhidos depois de ver os dados. Confirmo e acrescento o número que falta. No teste do Exp 2 (O/resultado5/predictions_xgboost.csv), τ=0,03 dá 4/39 FP em negativas reais e ainda 1 FN (Lumen, p=0,0136). No Exp 3, que reproduzi, dá 6/38 (15,8%). Em 10 sementes, 15–17% (XGB) e ~24% (CB).
- **Feynman E5, E6 / Sagan E14**: "SNR<3" é in-sample (48/67 no treino) e, na prática, seleciona ocultações profundas (mediana de Savgol_Min = 0,058). Três revisores chegaram ao mesmo número.
- **Feynman E7 / Sagan E5**: a hipótese é declarada "corroborada" sem nenhum termo de comparação. Concordo.
- **Feynman E12-E13, E14, E15-E19, E21-E22, E24 / Sagan E6-E11, E15, E18, E21-E23**: coincidem com os meus E9, E11, E13, E15-E19, E21-E25. Mesmos números: −0,125 e 0,678; 0,974–0,994; ≈2 pp × 0,7 pp; gain × weight; N<40 × N>120; dias × segundos; C fixo; XGB sem peso de classe.
- **Feynman E1**: negativas sintéticas com ~1/3 do ruído real. Confirmo: baseline_std mediano 0,021 × 0,058 × 0,104, e AUC sintética × negativa-real de até 0,94.

### 2. Discordâncias, correções e reconciliações

**2a. Recortes-irmãos: 21/38 (meu) × 18/38 (Feynman).** Os dois estão certos; são splits diferentes (SP/reconcile_siblings.py, após o dropna da tese):

| split | recortes no teste | negativas reais no teste | recortes com o irmão no treino |
|---|---|---|---|
| misto 80/20 (Exp 1, 2, 4, 5, 6) | 38 | 39 (= 38 + 1 nativa) | **21** |
| só-real 80/20 (Exp 3) | 37 | 38 (= 37 + 1 nativa) | **18** |
| só-real 65/35 | 65 | 66 | 26 |

- Há 125 mães: 61 deram par antes/depois e 64 deram um só recorte. O número de recortes com irmão no treino é igual ao número de pares separados.
- Correção fina para Feynman: são "18 dos 37 recortes", não "18 das 38 negativas" (a 38ª é a nativa de Umbriel).
- Positivas do teste com outra corda do mesmo evento (objeto + mês) no treino: **39/160 no Exp 3** (confirmo o número de Feynman, contando só positivas do treino) e 46/160 no misto.

**2b. CatBoost: 12× ou 2×?** Ambos são verdadeiros; mudam os denominadores. Q2R₁ = 0,058. Contra a janela de "ruído parecido" (−109 a −99 s, 10 s, p=0,005), a razão é **12×**. Contra o controle de baseline (−290 a −250 s, 40 s, p=0,029), é **2×**. No XGB, as razões correspondentes são 86× e 72×.
- Para uma afirmação de "sem falsos alarmes", o denominador relevante é o **máximo** sobre as janelas nulas. Isso dá 2× para o modelo de referência (CatBoost), que é o pior caso, e não "duas ordens de grandeza".
- Com 2 janelas nulas, esse máximo não é estimável.
- As janelas têm durações diferentes (10, 15, 25, 40, 60 s), e o próprio cap.5:525 mostra que p̂ cai quando a janela cresce. Duração é um confundidor, não um detalhe.

**2c. Sagan E3 ("as 802 positivas estão no dataset → a exclusão não foi feita"): REFUTADO pelo código e pelos dados.**
- build_dataset.py:204-208 marca a mãe, e :459-461 a pula.
- No DB há 928 observações positivas (927 com pontos).
- Nenhuma das 125 mães aparece no dataset_final.csv (0/125): 927 − 125 = 802.
- O vazamento de positiva-mãe não existe. O erro é de texto: cap.5:15 e :206 ("o banco dispunha de 802", "a partir delas").
- O vazamento real é outro: irmãos (2a) e cordas do mesmo evento.
- Sagan, retire também o A7 ("CV com agrupamento por curva"): a CV agrupa por curve_name (train_model.py:732-752), não pela mãe.

**2d. Sagan [AV] "clip satura 99,999 em 5": REFUTADO.** test_quaoar_recortes.py:109-110 (e test_quaoar.py:106) usa uma máscara `keep`, isto é, remove o ponto. A palavra "clip" no texto (cap.5:465) é imprecisa, mas o efeito descrito, remoção, está correto.

**2e. Sagan E4 (atalho por comprimento): passo de [AV] para parcialmente verificado.**
- Occ_chi2_constant é soma ∝ N: medianas 140 (recortes) × 594 (sintéticas) × 1220 (positivas).
- Só essa feature separa positivas de negativas reais com AUC 0,934.
- Não provei que o modelo *usa* o atalho; isso exige um controle de comprimento pareado.

**2f. Feynman: "Savgol_Min com um limiar dá F1 0,963 (in-sample)".**
- Fora da amostra, no mesmo split, 1 feature dá F1 0,93–0,95 (SP/baseline1f.py). O baseline da sessão anterior dá Occ_depth 0,905 (misto) e 0,948 (só-real). As três medidas são compatíveis.
- Ressalva: Savgol_Min não está no modelo operacional de 11 features.
- O ganho do ensemble (0,93 → 0,99, ~6× menos erros) é real e deve ir para a tese.

**2g. Contra a âncora da sessão anterior (critica_sagan_feynman.md, "Réplica do autor").** Ali se aceitou que "com τ=0,03 os dois Q2R são recuperados sem nenhum falso positivo" e as notas subiram para 8,0–8,5. Rejeito essa concessão por três motivos:
1. As janelas foram desenhadas sabendo onde estavam os anéis.
2. O "sem falso positivo" se apoia em 2 janelas.
3. O próprio modelo, no próprio teste, tem FPR de 10–16% em curvas negativas reais com τ=0,03.

Um teste adversarial de verdade é cego e tem um nulo com N grande. A subida de nota se baseou numa afirmação que os dados não sustentam.

**2h. AUDITORIA_PIPELINE.md (abril/2026).**
- Afirma "class balancing… em todos os modelos". É falso para o XGBoost (train_model.py:123-132).
- O C3 é hipotético (Umbriel duplicado entre fontes) e não encontra o vetor real (irmãos antes/depois e cordas do mesmo evento).
- A previsão "<0,5 pp" de efeito é plausível. No meu re-split agrupado por mãe em 10 sementes, o F1 médio misto fica em 0,980–0,985, contra o 0,99 do split único.

### 3. O que vocês viram e eu não vi (aceito)
- **Feynman E8 / Sagan E17**: a profundidade não depende de a corda ser central. O patamar vem da luz do ocultante (a Umbriel cai a ~0,2). Física correta; aceito.
- **Feynman E11 / Sagan E16**: a legenda do SORA (cap.2:82) descreve a figura errado. Verifiquei no PNG: preto = Fresnel, azul = diâmetro estelar, verde = poço geométrico de partida, vermelho = resposta instrumental (não são dados). Aceito; severidade média.
- **Feynman E14**: a janela de suavização acompanha N, não a física. Ao ampliar a janela de Quaoar, a janela SG passa de ~3 para ~11 pontos, o que pode apagar um dip de 0,5 s. Hipótese concorrente com a "diluição" do cap.5:525. Aceito como "a verificar": os dados de Quaoar não estão no repo, e no conjunto de 11 features só Savgol_std usa a série suavizada (é a nº 1 do XGB).
- **Feynman E12(c)**: quedas rasas acima de 0,78 entram nos negativos por construção. A pipeline é treinada para chamar de negativo exatamente o sinal sutil que promete achar. Aceito; é o argumento físico mais forte contra a narrativa de Quaoar.
- **Feynman E19**: a cintilação ∝ seeing no simulador está errada (a fórmula de Young depende de abertura, massa de ar e altitude). Também a oportunidade perdida de um teste de injeção e recuperação. Aceito.
- **Feynman E20**: McNemar "não significativo ≠ equivalente". Aceito (eu tinha só o aspecto técnico).
- **Cordas do mesmo evento (Feynman)**: 39/160. Aceito como segundo vetor de vazamento; agrupar por (objeto, data).
- **Sagan E12**: cap.5:574 diz "XGB e CatBoost ≥ 0,990 nos Exp 6 e 2", mas o CatBoost do Exp 6 tem 0,9874. Verificado; aceito.
- **Sagan, cap.5:525**: o texto cita "mínimo do Savitzky-Golay" como feature dominante, mas o modelo do Exp 2 não a tem. Aceito.
- **Sagan E19**: citações que não sustentam a frase (Fraser2024, Zhu2022, Deisenroth, Gryak, Saito) e falta de referências primárias (Breiman 2001; Chen & Guestrin 2016; Prokhorenkova et al. 2018). Aceito.
- **Sagan E20, E24, e a falta de análise de erros**: "encontrar padrões desconhecidos" × aprendizado supervisionado; banda z é infravermelho próximo; figura de Quaoar possivelmente sem fonte (a verificar); figuras de FN existem (pngs/resultado3) mas não são analisadas. Aceito.
- **Sagan sobre "15% menos treino"**: são −10% do treino total e −19% do treino real. Eu tinha anotado; concordo.

### 4. Os achados mudam a CONCLUSÃO ou só a força?
Mudam a conclusão em dois pontos e a força nos demais.
- **Fica de pé**, com força menor: "features clássicas + ensembles separam ocultações bem definidas de negativas, inclusive reais". As evidências:
  - AUC positivas × negativas reais ≈ 0,999;
  - o Exp 3 se reproduz bit-a-bit;
  - o ganho sobre a régua de 1 feature é real.

  O número honesto é F1 ≈ 0,98 ± 0,005 (10 sementes, grupo = mãe), com FPR em negativas reais de 4–9% (IC largo) a τ=0,5, e não "0,99 com precisão 1,000".
- **Muda 1, a capacidade de revisita**: "um ajuste simples do limiar recupera eventos sutis sem falsos alarmes". Isso não está demonstrado: com τ=0,03, a FPR em curvas negativas reais é de 10–16%; n=1 curva; janelas não cegas; e o treino rotula sinais rasos como negativos. O que se pode afirmar é "ilustração a posteriori em uma curva; o ranking anel > ruído existe no XGB e é fraco no CatBoost".
- **Muda 2, a hipótese**: de "corroborada" para "não testada" contra CNN ou inspeção manual. Só foi testada contra baselines de 1–2 features, e esse resultado deve entrar na tese.

**Três números que precisam mudar obrigatoriamente:**
1. **Contagem de features**: Exp 4 "14" → **13** e Exp 5 "13" → **12** (cap.5:268, :550-557, :570, :741; apêndice:10-13, 42-49; cap.6:11, 33), com a descrição correta do Exp 6 (sem kmeans, **com** Savgol_Min).
2. **Faixas de F1 e a queda da variante 65/35**: cap.5:735 "0,974–0,994 / 0,975–0,982" → **0,984–0,994 (misto) / 0,978–0,991 (Exp 3)**; e cap.5:326, :576 "≈2 pp" → **≈0,7 pp**.
3. **Resumo, cap.5:513-515 e cap.6:43**: "duas ordens de grandeza … sem falsos alarmes" → razões **por modelo e por denominador** (CatBoost: 12× contra o ruído, 2× contra o controle; XGB: 86× e 72×), mais a **FPR em negativas reais com τ=0,03 (6/38 = 16% no Exp 3)**.

Quase obrigatório: "o banco dispunha de 802 positivas" → **927** (802 após excluir 125 mães), e 1693 → **1692** amostras usadas.

### 5. Nota revisada: **6,0 / 10** (mantida)
- **Para baixo**: o vazamento por evento (39/160 positivas, Feynman), os erros de física do Cap. 2 (profundidade, Fresnel, legenda do SORA) e a construção dos recortes que rotula sinais rasos como negativos.
- **Para cima**:
  - o Exp 3 e a variante 65/35 reproduzem exatamente;
  - as tabelas batem com os CSVs;
  - a exclusão da mãe funciona (o E3 de Sagan cai);
  - o ganho do ML sobre a régua é real.
- O saldo fica em 6,0. Recuso as notas de 8,0–8,5 da sessão anterior, que se apoiam na concessão "τ=0,03 sem falso positivo", contradita pelos dados do próprio modelo.
- Subo para ~7,5 se a tese:
  1. refizer split e CV agrupando por mãe e por evento;
  2. escolher τ por CV;
  3. reportar a FPR em negativas reais com IC;
  4. fizer uma varredura cega de janelas em Quaoar;
  5. corrigir os itens obrigatórios acima.
