# Plano de Reescrita — Capítulo 5 (Resultados)

> **Gerado em:** 2026-03-17
> **Base:** Novos outputs do pipeline em `pipeline/model_training/outputs/`
> **Destino:** `writing_latex/Tese/capitulo5.tex`

---

## 1. Mapeamento: Novos Outputs → Experimentos do Capítulo

Os 7 diretórios de resultados do pipeline mapeiam-se aos experimentos do novo Capítulo 5 da seguinte forma:

| Experimento (novo) | Pasta do pipeline | Features | Split | Objetivo |
|---|---|---|---|---|
| **Exp. 1** | `resultado1_split0.8-0.2_all-features` | 28 (completo) | 80/20 | Linha de base |
| **Exp. 2** | `resultado2_split0.8-0.2_less_features` | 14 (reduzido) | 80/20 | Redução de features |
| **Exp. 3** | `resultado3_split0.8-0.2_less-features_noMin` | 13 (sem `Savgol_Min`) | 80/20 | Impacto de `Savgol_Min` |
| **Exp. 4** | `resultado4_split0.8-0.2_less-features_noKmeans` | 12 (sem `kmeans`) | 80/20 | Ablação do K-Means |
| **Exp. 5** | `resultado5_split0.8-0.2_less_features_noMin-noKmeans` | 11 (sem Min, sem kmeans) | 80/20 | Ablação combinada |
| **Exp. 6** | `resultado6.1_split0.65-0.35_less_feaures_noMin-noKmeans` | 11 | 65/35 | Sensibilidade ao split |
| **Exp. 7** | `resultado6.2_applyTestOnlyRealCurves` | 11 | 65/35 (teste só real) | Generalização para curvas reais |

---

## 2. Métricas Exatas (de `training_results.csv`)

### Exp. 1 — 28 features, 80/20

| Modelo | Acurácia | Precisão | Revocação | F1-score | AUC-ROC |
|---|---|---|---|---|---|
| Random Forest | 0,9941 | 1,0000 | 0,9875 | 0,9937 | 0,9997 |
| CatBoost | 0,9912 | 0,9937 | 0,9875 | 0,9906 | 0,9998 |
| Logistic Regression | 0,9882 | 1,0000 | 0,9750 | 0,9873 | 1,0000 |
| XGBoost | 0,9853 | 0,9814 | 0,9875 | 0,9844 | 0,9997 |

### Exp. 2 — 14 features, 80/20

| Modelo | Acurácia | Precisão | Revocação | F1-score | AUC-ROC |
|---|---|---|---|---|---|
| CatBoost | 0,9912 | 0,9937 | 0,9875 | 0,9906 | 0,9996 |
| Random Forest | 0,9882 | 0,9937 | 0,9813 | 0,9874 | 0,9997 |
| XGBoost | 0,9882 | 0,9875 | 0,9875 | 0,9875 | 0,9996 |
| Logistic Regression | 0,9882 | 1,0000 | 0,9750 | 0,9873 | 1,0000 |

### Exp. 3 — 13 features (sem Savgol_Min), 80/20

| Modelo | Acurácia | Precisão | Revocação | F1-score | AUC-ROC |
|---|---|---|---|---|---|
| Random Forest | 0,9912 | 1,0000 | 0,9813 | 0,9905 | 0,9998 |
| CatBoost | 0,9882 | 1,0000 | 0,9750 | 0,9873 | 0,9998 |
| Logistic Regression | 0,9882 | 1,0000 | 0,9750 | 0,9873 | 1,0000 |
| XGBoost | 0,9853 | 0,9874 | 0,9813 | 0,9843 | 0,9997 |

### Exp. 4 — 12 features (sem kmeans), 80/20

| Modelo | Acurácia | Precisão | Revocação | F1-score | AUC-ROC |
|---|---|---|---|---|---|
| Random Forest | 0,9912 | 0,9937 | 0,9875 | 0,9906 | 0,9998 |
| XGBoost | 0,9912 | 0,9937 | 0,9875 | 0,9906 | 0,9997 |
| CatBoost | 0,9882 | 0,9937 | 0,9813 | 0,9874 | 0,9997 |
| Logistic Regression | 0,9882 | 1,0000 | 0,9750 | 0,9873 | 1,0000 |

### Exp. 5 — 11 features (sem Min, sem kmeans), 80/20

| Modelo | Acurácia | Precisão | Revocação | F1-score | AUC-ROC |
|---|---|---|---|---|---|
| XGBoost | 0,9912 | 0,9937 | 0,9875 | 0,9906 | 0,9995 |
| CatBoost | 0,9912 | 1,0000 | 0,9813 | 0,9905 | 0,9997 |
| Random Forest | 0,9882 | 0,9937 | 0,9813 | 0,9874 | 0,9996 |
| Logistic Regression | 0,9853 | 1,0000 | 0,9688 | 0,9841 | 1,0000 |

### Exp. 6 — 11 features, 65/35

| Modelo | Acurácia | Precisão | Revocação | F1-score | AUC-ROC |
|---|---|---|---|---|---|
| XGBoost | 0,9912 | 0,9937 | 0,9875 | 0,9906 | 0,9995 |
| CatBoost | 0,9912 | 1,0000 | 0,9813 | 0,9905 | 0,9997 |
| Random Forest | 0,9882 | 0,9937 | 0,9813 | 0,9874 | 0,9996 |
| Logistic Regression | 0,9853 | 1,0000 | 0,9688 | 0,9841 | 1,0000 |

> ⚠️ **ALERTA:** Os valores de Exp. 5 e Exp. 6 são IDÊNTICOS nos CSVs. Isso pode indicar um bug no pipeline (o `training_results.csv` do resultado6.1 pode ter sido copiado do resultado5, ou os métricas foram calculadas sobre o mesmo conjunto). **Investigar antes de publicar.** Uma possibilidade é que o `training_results.csv` reporte métricas de treino (não de teste) em ambos. Comparar as `predictions_*.csv` e `confusion_matrices.png` para confirmar.

### Exp. 7 — Teste somente em curvas reais

| Modelo | Acurácia | Precisão | Revocação | F1-score | AUC-ROC |
|---|---|---|---|---|---|
| XGBoost | 0,9712 | 0,9892 | 0,9751 | 0,9821 | 0,9968 |
| Random Forest | 0,9683 | 0,9891 | 0,9715 | 0,9803 | 0,9950 |
| CatBoost | 0,9654 | 0,9891 | 0,9680 | 0,9784 | 0,9967 |
| Logistic Regression | 0,9597 | 0,9926 | 0,9573 | 0,9746 | 0,9959 |

---

## 3. Validação Cruzada (Exp. 3 — `cross_validation_summary.csv`)

| Modelo | Acurácia (μ ± σ) | Precisão (μ ± σ) | Revocação (μ ± σ) | F1 (μ ± σ) | AUC-ROC (μ ± σ) |
|---|---|---|---|---|---|
| CatBoost | 0,9876 ± 0,0067 | 0,9912 ± 0,0034 | 0,9825 ± 0,0148 | 0,9868 ± 0,0072 | 0,9993 ± 0,0005 |
| XGBoost | 0,9864 ± 0,0058 | 0,9888 ± 0,0090 | 0,9825 ± 0,0167 | 0,9856 ± 0,0062 | 0,9992 ± 0,0008 |
| Logistic Reg. | 0,9846 ± 0,0097 | 0,9911 ± 0,0057 | 0,9763 ± 0,0172 | 0,9836 ± 0,0104 | 0,9986 ± 0,0016 |
| Random Forest | 0,9840 ± 0,0068 | 0,9826 ± 0,0051 | 0,9838 ± 0,0129 | 0,9831 ± 0,0072 | 0,9992 ± 0,0007 |

---

## 4. Teste de McNemar (Exp. 2 — `mcnemar_results.csv`)

| Modelo A | Modelo B | b | c | χ² | p-valor | Significativo? |
|---|---|---|---|---|---|---|
| RF | XGBoost | 1 | 1 | 0,50 | 0,4795 | Não |
| RF | CatBoost | 1 | 2 | 0,00 | 1,0000 | Não |
| RF | Log. Reg. | 2 | 2 | 0,25 | 0,6171 | Não |
| XGBoost | CatBoost | 0 | 1 | 0,00 | 1,0000 | Não |
| XGBoost | Log. Reg. | 3 | 3 | 0,17 | 0,6831 | Não |
| CatBoost | Log. Reg. | 3 | 2 | 0,00 | 1,0000 | Não |

**Conclusão:** Nenhum par de modelos apresenta diferença estatisticamente significativa (α = 0,05).

---

## 5. Análise de Limiar (Exp. 3 — `threshold_analysis.csv`)

Pontos operacionais chave:

| Modelo | Limiar | Precisão | Revocação | F1 | F2 | FP | FN |
|---|---|---|---|---|---|---|---|
| **RF** (padrão) | 0,50 | 1,0000 | 0,9813 | 0,9905 | 0,9849 | 0 | 3 |
| **RF** (sensível) | 0,45 | 0,9938 | 0,9938 | 0,9938 | 0,9938 | 1 | 1 |
| **RF** (máx recall) | 0,01 | 0,7921 | 1,0000 | 0,8840 | 0,9501 | 42 | 0 |
| **LR** (ótimo) | 0,16 | 0,9938 | 1,0000 | 0,9969 | 0,9988 | 1 | 0 |
| **XGB** (ótimo) | 0,30 | 0,9875 | 0,9875 | 0,9875 | 0,9875 | 2 | 2 |
| **CB** (ótimo) | 0,37 | 0,9875 | 0,9875 | 0,9875 | 0,9875 | 2 | 2 |

**Destaque:** A Regressão Logística com τ = 0,16 atinge recall = 100% com apenas 1 FP — ponto operacional ideal para triagem.

---

## 6. Figuras a Copiar para `writing_latex/Tese/pngs/`

### Estrutura de subpastas a criar em `pngs/`:

```
pngs/
├── resultado1/        (já pode ter conteúdo antigo — NÃO apagar)
├── resultado2/        (NOVO)
├── resultado3/        (já existe — verificar se conteúdo é o antigo)
├── resultado4/        (já existe — pode ter conteúdo antigo)
├── resultado5/        (NOVO)
├── resultado6.1/      (NOVO)
└── resultado6.2/      (NOVO)
```

### Lista de cópias (pipeline → pngs):

| Origem (pipeline/model_training/outputs/) | Destino (writing_latex/Tese/pngs/) | Usado em |
|---|---|---|
| resultado1_.../confusion_matrices.png | resultado1/confusion_matrices.png | Exp. 1 |
| resultado1_.../roc_curves.png | resultado1/roc_curves.png | Exp. 1 |
| resultado1_.../feature_importance_*.png (4 arquivos) | resultado1/ | Exp. 1 |
| resultado1_.../precision_recall_curve.png | resultado1/precision_recall_curve.png | Threshold |
| resultado2_.../confusion_matrices.png | resultado2/confusion_matrices.png | Exp. 2 |
| resultado2_.../roc_curves.png | resultado2/roc_curves.png | Exp. 2 |
| resultado2_.../feature_importance_*.png (4) | resultado2/ | Exp. 2 |
| resultado2_.../precision_recall_curve.png | resultado2/precision_recall_curve.png | Threshold |
| resultado3_.../confusion_matrices.png | resultado3_new/confusion_matrices.png | Exp. 3 |
| resultado3_.../roc_curves.png | resultado3_new/roc_curves.png | Exp. 3 |
| resultado3_.../feature_importance_*.png (4) | resultado3_new/ | Exp. 3 |
| resultado3_.../precision_recall_curve.png | resultado3_new/precision_recall_curve.png | Threshold + CV |
| resultado3_.../metrics_vs_threshold_1.png | resultado3_new/metrics_vs_threshold_1.png | Threshold |
| resultado3_.../metrics_vs_threshold_2.png | resultado3_new/metrics_vs_threshold_2.png | Threshold |
| resultado4_.../confusion_matrices.png | resultado4_new/confusion_matrices.png | Exp. 4 |
| resultado4_.../roc_curves.png | resultado4_new/roc_curves.png | Exp. 4 |
| resultado4_.../feature_importance_*.png (4) | resultado4_new/ | Exp. 4 |
| resultado5_.../confusion_matrices.png | resultado5/confusion_matrices.png | Exp. 5 |
| resultado5_.../roc_curves.png | resultado5/roc_curves.png | Exp. 5 |
| resultado5_.../feature_importance_*.png (4) | resultado5/ | Exp. 5 |
| resultado6.1_.../confusion_matrices.png | resultado6.1/confusion_matrices.png | Exp. 6 |
| resultado6.1_.../roc_curves.png | resultado6.1/roc_curves.png | Exp. 6 |
| resultado6.2_.../confusion_matrices.png | resultado6.2/confusion_matrices.png | Exp. 7 |
| resultado6.2_.../roc_curves.png | resultado6.2/roc_curves.png | Exp. 7 |
| resultado6.2_.../feature_importance_*.png (4) | resultado6.2/ | Exp. 7 |
| resultado6.2_.../precision_recall_curve.png | resultado6.2/precision_recall_curve.png | Exp. 7 |

> **REGRA:** Nunca apagar nada da pasta `pngs/`. Usar subpastas com sufixo `_new` se houver conflito com figuras antigas.

**Total estimado:** ~50 arquivos PNG a copiar.

---

## 7. Estrutura Proposta do Novo Capítulo 5

```latex
% =============================================================================
% Capítulo 5 — Resultados
% =============================================================================

\section{Visão geral dos experimentos}
   - Resumo do problema (classificação binária)
   - 4 modelos: LR, RF, XGBoost, CatBoost
   - 7 experimentos (2 blocos + teste de generalização)
   - Métricas utilizadas

\section{Descrição das features e análise de redundância}
   \subsection{Conjunto completo de features}
      - Tabela com 28 features (MANTER tab:features_completo — idêntica ao cap. antigo)
   \subsection{Análise de redundância}
      - 7 pares redundantes identificados
      - Tabela com 13 features finais (tab:features_final)

\section{Importância das features: metodologia}
   \subsection{Random Forest — MDI}
   \subsection{XGBoost — Weight}
   \subsection{CatBoost — PredictionValuesChange}
   \subsection{Regressão Logística — coeficientes}
   \subsection{Comparação entre métodos}
      - Tabela comparativa (tab:metodos_importancia)

\section{Configuração experimental}
   - Dataset: 1693 amostras (802 pos, 891 neg)
   - Tabela de composição (tab:dataset_fonte)
   - Split estratificado, semente 42
   - Hiperparâmetros → Apêndice

\section{Resultados do Experimento 1}
   - Tabela de métricas (tab:metricas_1) — NOVOS VALORES
   - Figura: confusion_matrices (resultado1)
   - Análise: RF lidera em F1=0,994; LR com precisão 100%

\section{Resultados do Experimento 2}
   - Tabela (tab:metricas_2) — NOVOS VALORES
   - Figura: confusion_matrices (resultado2)
   - Análise: CatBoost lidera (F1=0,991); redução de features preserva desempenho

\section{Resultados do Experimento 3}
   - Tabela (tab:metricas_3) — NOVOS VALORES
   - Figura: confusion_matrices (resultado3_new)
   - Análise: RF sobe para F1=0,991; remoção de Savgol_Min sem degradação geral

\section{Estudo de ablação: impacto da feature kmeans_centroid_dist}
   \subsection{Resultados do Experimento 4 (sem kmeans)}
      - Tabela (tab:metricas_4) — RF e XGB ambos F1=0,991
      - Figura: confusion_matrices (resultado4_new)
   \subsection{Ablação combinada: Experimento 5 (sem Min e sem kmeans)}
      - Tabela (tab:metricas_5) — 11 features
   \subsection{Comparação e redistribuição de importância}
      - Tabela comparativa (com vs. sem kmeans)
      - Figuras de feature importance (Exp. 1, 4 e 5)

\section{Sensibilidade ao tamanho do conjunto de treino}
   \subsection{Experimento 6 (split 65/35)}
      - Tabela (tab:metricas_6)
      - ⚠️ NOTA: verificar se métricas são realmente distintas do Exp. 5
   \subsection{Curva de aprendizado implícita}
      - Tabela consolidada: melhor F1 vs. amostras de treino

\section{Teste de generalização: curvas exclusivamente reais}
   \subsection{Motivação}
      - 78% dos negativos são sintéticos → modelo vê distribuição artificial
      - Exp. 7 avalia exclusivamente em curvas reais
   \subsection{Resultados do Experimento 7}
      - Tabela (tab:metricas_7) — queda para ~97% acc, ~98% F1
      - Figura: confusion_matrices (resultado6.2)
   \subsection{Interpretação}
      - Queda de ~2 pp em F1 vs. teste misto
      - Ainda muito robusto (AUC > 0,995)
      - Indica que features capturam sinal real, não artefato sintético

\section{Validação cruzada estratificada}
   - Tabela (tab:cross_validation) — valores exatos do CV 5-fold
   - Desvios padrão pequenos (~0,006-0,010 em F1) → robustez confirmada
   \subsection{Teste de McNemar entre modelos}
      - Tabela (tab:mcnemar) — nenhum par significativo
      - Implicação: modelos são estatisticamente equivalentes

\section{Ajuste do limiar de decisão}
   \subsection{Motivação: assimetria de custo}
   \subsection{Método}
   \subsection{Resultados}
      - Tabela (tab:threshold_comparacao) — valores exatos
      - Figuras: precision_recall_curve, metrics_vs_threshold
      - Destaque: LR com τ=0,16 → recall=100%, apenas 1 FP
   \subsection{Implicações para uso operacional}
      - Modo balanceado vs. modo triagem

\section{Comparação entre os experimentos}
   - Tabela consolidada de F1-score (7 experimentos × 4 modelos)
   - 5 observações principais (atualizar com novos dados)
   - Figuras ROC de todos os experimentos

\section{Análise de importância das features}
   - Figuras 2×2 para Exp. 1, 2, 3, 4, 5, 7
   - Discussão das features mais relevantes
   - Histograma kmeans por classe (se disponível nos novos dados)

\section{Discussão dos resultados}
   \subsection{Desempenho e generalização}
      - F1 entre 0,984 e 0,994 (teste misto)
      - F1 entre 0,975 e 0,982 (teste real)
      - AUC-ROC > 0,995 em todos os cenários
   \subsection{Análise de redundância}
      - 28 → 11 features sem perda significativa
   \subsection{Interpretação da importância das features}
      - Concordância entre modelos
      - Colinearidade kmeans ↔ Savgol_std
   \subsection{Teste de generalização em dados reais}
      - Queda modesta mas reveladora
      - Implicações para datasets parcialmente sintéticos
   \subsection{Custo assimétrico e ajuste de limiar}
   \subsection{Limitações}
      1. Ground truth dos catálogos
      2. Métricas idênticas entre Exp. 5 e 6 (investigar)
      3. Único split por experimento (mitigado pelo CV)
      4. Generalização para outros catálogos não testada
      5. Dataset parcialmente sintético (78% dos negativos)
   \subsection{Recomendações para trabalhos futuros}
```

---

## 8. Diferenças-Chave entre o Capítulo Antigo e o Novo

### O que MUDA:

| Aspecto | Capítulo antigo | Capítulo novo |
|---|---|---|
| Nº de experimentos | 6 | 7 (adição do teste de generalização) |
| Valores nas tabelas | Antigos (resultado3/4/4.5) | Novos (resultado1-6.2) |
| Figuras de confusão | resultado3, resultado4, resultado4.5 | resultado1-6.2 |
| Figuras de ROC | 3 experimentos | 7 experimentos |
| Seção "Generalização" | Não existe | **NOVA** — resultado6.2 |
| Validação cruzada | Comentada (TODO) | **PREENCHIDA** com dados reais |
| Teste de McNemar | Comentado (TODO) | **PREENCHIDO** com dados reais |
| Threshold analysis | Comentada (TODO) | **PREENCHIDA** com dados reais |
| Curva de aprendizado | 3 pontos (40/60, 35/65, 80/20) | 2 pontos (65/35, 80/20) + gráficos |
| Exp. de split | Splits 35/65 e 40/60 | Split 65/35 |

### O que se MANTÉM (estrutura reutilizável):

- Seção de features e redundância (texto + tabelas)
- Seção de metodologia de importância de features
- Seção de configuração experimental (tabela de composição do dataset)
- Seção de ajuste de limiar (texto teórico)
- Estrutura geral das subseções de cada experimento

---

## 9. Pontos Críticos / Alertas

### 🔴 CRÍTICO: Métricas duplicadas (Exp. 5 = Exp. 6)

Os arquivos `training_results.csv` de `resultado5` e `resultado6.1` contêm **valores idênticos** em todas as métricas e para todos os modelos. Isso é fisicamente improvável com splits 80/20 vs 65/35 em conjuntos diferentes.

**Ação requerida antes de publicar:**
1. Comparar `predictions_*.csv` dos dois diretórios
2. Comparar as `confusion_matrices.png` visualmente
3. Comparar `split_train_curves.txt` e `split_test_curves.txt`
4. Se confirmado o bug, **re-executar** o pipeline para resultado6.1 com split correto
5. Se não for possível re-executar, **omitir** o Exp. 6 e reportar apenas Exp. 1-5 + Exp. 7

### 🟡 ATENÇÃO: Nomenclatura das pastas de figuras

As pastas antigas em `pngs/` usam nomes como `resultado3`, `resultado4`, `resultado4.5`. Os novos resultados usam nomes diferentes. Para evitar conflito:
- Criar subpastas novas (`resultado1_new`, `resultado2_new`, etc.) OU
- Renomear as referências LaTeX para apontar diretamente às pastas originais do pipeline

**Recomendação:** Usar subpastas com nomes descritivos curtos como `exp1`, `exp2`, ..., `exp7`.

### 🟡 ATENÇÃO: Figuras de feature importance inexistentes para resultado5 e resultado6.1

Verificar se `feature_importance_*.png` existem em todas as pastas. Se não, algumas figuras de importância serão omitidas para experimentos intermediários.

### 🟢 POSITIVO: Dados novos preenchem todos os TODOs

O capítulo antigo continha ~15 blocos `%% TODO` para:
- Tabelas de validação cruzada
- Tabelas de McNemar
- Tabelas de threshold
- Curvas precision-recall
- Figuras de métricas vs. threshold
- Matrizes de confusão dos Exp. 4-6

Todos esses podem agora ser preenchidos com dados reais.

---

## 10. Fluxo de Execução

### Passo 1: Investigar anomalia Exp. 5 vs. Exp. 6
```bash
# Comparar os CSVs
diff resultado5_.../training_results.csv resultado6.1_.../training_results.csv
diff resultado5_.../split_test_curves.txt resultado6.1_.../split_test_curves.txt
```

### Passo 2: Copiar figuras para `pngs/`
```bash
# Criar subpastas
mkdir -p pngs/exp1 pngs/exp2 pngs/exp3 pngs/exp4 pngs/exp5 pngs/exp6 pngs/exp7

# Copiar de cada resultado
cp resultado1_*/*.png pngs/exp1/
cp resultado2_*/*.png pngs/exp2/
cp resultado3_*/*.png pngs/exp3/
cp resultado4_*/*.png pngs/exp4/
cp resultado5_*/*.png pngs/exp5/
cp resultado6.1_*/*.png pngs/exp6/
cp resultado6.2_*/*.png pngs/exp7/
```

### Passo 3: Apagar conteúdo antigo do capitulo5.tex
- Remover todo o texto entre o header e o final
- Manter apenas o comentário de cabeçalho

### Passo 4: Escrever novo capítulo
- Seguir a estrutura da Seção 7 deste plano
- Preencher todas as tabelas com valores exatos da Seção 2
- Referenciar figuras com caminhos `pngs/expN/nome.png`

### Passo 5: Verificação
- [ ] Todas as figuras referenciadas existem em `pngs/`
- [ ] Nenhuma referência a experimentos antigos
- [ ] Todas as tabelas preenchidas (zero TODOs)
- [ ] Labels e refs consistentes com outros capítulos
- [ ] Terminologia alinhada com Capítulos 3 e 4

---

## 11. Terminologia a Manter (consistência com Cap. 3-4)

| Termo | Uso no capítulo |
|---|---|
| *pipeline* | Sempre em itálico |
| *features* | Sempre em itálico |
| *overfitting* | Traduzir como "sobreajuste" com original entre parênteses |
| *ground truth* | Usar "verdade de campo" ou manter em itálico |
| *ensemble* | Manter em inglês, sem itálico |
| *split* | Usar "divisão treino/teste" ou *split* em itálico |
| Modelos | "Regressão Logística", "Random Forest", "XGBoost", "CatBoost" |
| Métricas | "acurácia", "precisão", "revocação" (não "recall"), "F1-score", "AUC-ROC" |
| Dataset | "conjunto de dados" ou *dataset* em itálico |
| *baseline* | Em itálico, sem tradução |

---

## 12. Referências Cruzadas com Outros Capítulos

O novo Capítulo 5 deve referenciar:

| Referência | Onde aparece | Contexto |
|---|---|---|
| `Capítulo 3` | Descrição dos modelos | "conforme descrito no Capítulo 3" |
| `Capítulo 4` | Metodologia do pipeline | "a pipeline descrita no Capítulo 4" |
| `\ref{ap:hiperparametros}` | Config experimental | Hiperparâmetros dos modelos |
| `\cite{Simulator}` | Dataset sintético | Gomes-Ferrante & Braga-Ribas |
| `\cite{McNemar1947}` | Teste de McNemar | Referência do teste |
| `\cite{Saito2015}` | Curva PR | Referência de métricas |
| `\cite{geron2019maos}` | Overfitting, regularização | Géron 2019 |
| `Capítulo 6` | NÃO referenciar | Cap. 6 é Conclusões — não antecipar |

---

## 13. Estimativa de Volume

| Seção | Tabelas | Figuras | Páginas estimadas |
|---|---|---|---|
| Visão geral | 0 | 0 | 1 |
| Features e redundância | 2 | 0 | 2 |
| Importância: metodologia | 1 | 0 | 1.5 |
| Config experimental | 1 | 0 | 0.5 |
| Exp. 1-5 (5 seções) | 5 | 5 (confusão) | 5 |
| Ablação kmeans | 2 | 4 (importância) | 2 |
| Sensibilidade split | 2 | 0 | 1 |
| Generalização real | 1 | 1 | 1.5 |
| Validação cruzada + McNemar | 2 | 0 | 1.5 |
| Ajuste de limiar | 1 | 2 (PR, threshold) | 2 |
| Comparação geral | 1 | 3-7 (ROC) | 2 |
| Importância features | 0 | 6-12 (2×2) | 3-5 |
| Discussão | 0 | 0 | 3 |
| **Total** | **~18** | **~25-35** | **~26-30** |

---

## 14. Checklist Final

Antes de finalizar o Capítulo 5:

- [ ] Investigar anomalia Exp. 5 = Exp. 6
- [ ] Todas as figuras copiadas para `pngs/`
- [ ] Todas as tabelas preenchidas com valores dos CSVs
- [ ] Nenhum bloco `%% TODO` restante
- [ ] Nenhuma referência a `resultado3/`, `resultado4/`, `resultado4.5/` (pastas antigas)
- [ ] Todos os `\label{}` e `\ref{}` consistentes
- [ ] Seções de CV, McNemar e threshold descomentadas e preenchidas
- [ ] Capítulo lê-se de forma coerente com Cap. 3 e 4
- [ ] Tom acadêmico, sem exageros, limitações explícitas
- [ ] Compilação LaTeX sem warnings de figuras faltantes
