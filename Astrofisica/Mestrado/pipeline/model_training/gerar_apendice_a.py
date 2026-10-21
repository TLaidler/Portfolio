"""Gera writing_latex/Tese/apendice_experimentos.tex a partir das saídas de reanalise_banca.py.

Uso (depois de rodar reanalise_banca.py):  python gerar_apendice_a.py
"""
import json
import pandas as pd

import os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..") + "/"  # pasta Mestrado
O = ROOT + "pipeline/model_training/outputs/reanalise_banca/"
cv = pd.read_csv(O + "cv_resumo.csv")
cv_alt = pd.read_csv(O + "cv_resumo_sementes_alternativas.csv")
te = pd.read_csv(O + "teste_final.csv")
S = json.load(open(O + "resumo.json", encoding="utf-8"))
M = ["Regressão Logística", "Random Forest", "XGBoost", "CatBoost"]
BASE = "Baseline (limiar em Occ_depth)"
ABR = {"Regressão Logística": "Regressão Log.", "Random Forest": "Random Forest", "XGBoost": "XGBoost",
       "CatBoost": "CatBoost", BASE: "Limiar em \\texttt{Occ\\_depth}"}
CFG = ["1", "1.1", "1.2a", "1.2b", "2"]
SUP = ["1.2b sem teste t", "1.2b sem testes de quartis", "2 sem testes de quartis"]
NF = S["selecao"]["n_features_por_config"]


def n(x, d=4):
    return f"{x:.{d}f}".replace(".", "{,}")


def pm(m, s, d=4):
    return f"${n(m, d)} \\pm {n(s, d)}$"


def pct(x, d=1):
    return f"{100 * x:.{d}f}".replace(".", "{,}") + "\\,\\%"


L = []
A = L.append
A(r"""% =============================================================================
% Apêndice — Resultados experimentais complementares
% =============================================================================
% Gerado por pipeline/model_training/gerar_apendice_a.py a partir de outputs/reanalise_banca/; não editar à mão.
\chapter{Resultados experimentais complementares}
\label{ap:experimentos}

Este apêndice reúne os resultados da reanálise do Capítulo~5 que não foram incluídos no corpo do texto: a correspondência entre a numeração dos experimentos na versão apresentada à banca e a numeração atual, todas as métricas da validação cruzada, a verificação da regra de seleção com outras sementes, as estimativas agregadas de falsos positivos nas negativas reais e as métricas no conjunto de teste de todas as configurações. Os resultados da versão apresentada à banca, obtidos com uma única divisão treino/teste, foram substituídos por estes e não são reproduzidos aqui.

% -----------------------------------------------------------------------------
\section{Correspondência entre as versões}
\label{sec:correspondencia_experimentos}

A Tabela~\ref{tab:correspondencia} relaciona a numeração dos experimentos na versão apresentada à banca com a adotada nesta versão. O número de \textit{features} de cada configuração foi conferido nos modelos salvos de cada experimento (arquivo \texttt{feature\_names.pkl}).

\begin{table}[htbp]
\centering
\caption{Correspondência entre os experimentos da versão apresentada à banca e os desta versão.}
\label{tab:correspondencia}
\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{lllcl}
\hline
\textbf{Versão da banca} & \textbf{Esta versão} & \textbf{Conteúdo} & \textbf{\textit{Features}} & \textbf{Diretório antigo} \\
\hline
Exp.~1 & Exp.~1 & conjunto completo & 28 & \texttt{resultado1} \\
Exp.~4\textsuperscript{a} & Exp.~1.1 & sem as 15 redundantes & 13 & \texttt{resultado2} \\
Exp.~5\textsuperscript{a} & Exp.~1.2a & 1.1 sem \texttt{Feature\_Savgol\_Min} & 12 & \texttt{resultado3} \\
Exp.~6 & Exp.~1.2b & 1.1 sem \texttt{kmeans\_centroid\_dist} & 12 & \texttt{resultado4} \\
Exp.~2 & Exp.~2 & 1.1 sem as duas & 11 & \texttt{resultado5} \\
Exp.~3 & Análise~2.1 & teste só em curvas reais & 12\textsuperscript{b} & \texttt{resultado6.2} \\
Exp.~3 (65/35) & Análise~2.2 & tamanho do treino & 12\textsuperscript{b} & \texttt{resultado6.1} \\
\hline
\end{tabular}

\smallskip
\begin{minipage}{0.92\textwidth}
\textsuperscript{a}\,O texto da versão da banca atribuía 14 \textit{features} ao Exp.~4 e 13 ao Exp.~5; os modelos salvos têm 13 e 12.\\
\textsuperscript{b}\,Nesta versão, as Análises 2.1 e 2.2 usam a configuração escolhida (1.2b); na versão da banca, a de 11 \textit{features}.
\end{minipage}
\end{table}

% -----------------------------------------------------------------------------
\section{Métricas completas da validação cruzada}
\label{sec:cv_completa}

A Tabela~\ref{tab:cv_completa} apresenta todas as métricas da validação cruzada (5 dobras $\times$ 5 repetições, no conjunto de desenvolvimento, $\tau = 0{,}5$), inclusive as das três configurações suplementares avaliadas depois da escolha, que não participaram da regra de seleção.

\begin{table}[htbp]
\centering
\caption{Validação cruzada no conjunto de desenvolvimento: média $\pm$ desvio padrão sobre as 25 dobras. Entre parênteses, o número de \textit{features}. As três últimas configurações são suplementares (avaliadas depois da escolha).}
\label{tab:cv_completa}
\scriptsize
\setlength{\tabcolsep}{3pt}
\resizebox{\textwidth}{!}{%
\begin{tabular}{llccccc}
\hline
\textbf{Configuração} & \textbf{Modelo} & \textbf{Acurácia} & \textbf{Precisão} & \textbf{Sensibilidade} & \textbf{F1} & \textbf{AUC-ROC} \\
\hline""")
for c in CFG + SUP:
    for i, m in enumerate(M):
        r = cv[(cv.config == c) & (cv.modelo == m)].iloc[0]
        lab = f"\\multirow{{4}}{{*}}{{\\shortstack[l]{{{c.replace(' sem ', '\\\\ sem ')}\\\\({NF[c]})}}}}" if i == 0 else ""
        A(f"{lab} & {ABR[m]} & {pm(r.acc, r.acc_sd)} & {pm(r.prec, r.prec_sd)} & {pm(r.rec, r.rec_sd)} & {pm(r.f1, r.f1_sd)} & {pm(r.auc, r.auc_sd)} \\\\")
    A("\\hline")
r = cv[(cv.modelo == BASE)].iloc[0]
A(f"Referência (1) & {ABR[BASE]} & {pm(r.acc, r.acc_sd)} & {pm(r.prec, r.prec_sd)} & {pm(r.rec, r.rec_sd)} & {pm(r.f1, r.f1_sd)} & {pm(r.auc, r.auc_sd)} \\\\")
A(r"""\hline
\end{tabular}}
\end{table}

% -----------------------------------------------------------------------------
\section{Robustez da regra de seleção}
\label{sec:robustez_selecao}

A Tabela~\ref{tab:robustez_selecao} compara o melhor F1 médio de cada configuração na validação cruzada principal (sementes 0 a 4) e em uma repetição com outras cinco sementes (2000 a 2004), mantidos a partição de teste e os modelos. Na validação principal, a regra de um desvio padrão escolhe a configuração 1.2b; na repetição, a configuração~2 fica acima do limite, e a mesma regra a escolheria.

\begin{table}[htbp]
\centering
\caption{Melhor F1 médio de cada configuração (e modelo correspondente) na validação cruzada com dois conjuntos de sementes, e limite da regra de um desvio padrão.}
\label{tab:robustez_selecao}
\footnotesize
\begin{tabular}{lcccc}
\hline
 & \multicolumn{2}{c}{\textbf{Sementes 0--4}} & \multicolumn{2}{c}{\textbf{Sementes 2000--2004}} \\
\textbf{Configuração} & \textbf{Melhor F1} & \textbf{Modelo} & \textbf{Melhor F1} & \textbf{Modelo} \\
\hline""")
for c in CFG:
    a = cv[(cv.config == c) & cv.modelo.isin(M)].sort_values("f1").iloc[-1]
    b = cv_alt[(cv_alt.config == c) & cv_alt.modelo.isin(M)].sort_values("f1").iloc[-1]
    A(f"{c} ({NF[c]}) & {n(a.f1)} & {ABR[a.modelo]} & {n(b.f1)} & {ABR[b.modelo]} \\\\")
s0, s1 = S["selecao"], S["robustez_sementes"]
A("\\hline")
A(f"Limite (melhor $-$ 1 DP) & \\multicolumn{{2}}{{c}}{{{n(s0['limite_1sd'])}}} & \\multicolumn{{2}}{{c}}{{{n(s1['limite_1sd'])}}} \\\\")
A(f"Configuração escolhida & \\multicolumn{{2}}{{c}}{{{s0['config_escolhida']}}} & \\multicolumn{{2}}{{c}}{{{s1['config_escolhida']}}} \\\\")
A(r"""\hline
\end{tabular}
\end{table}

A Tabela~\ref{tab:diferenca_pareada} mostra, para cada modelo, a diferença de F1 entre as configurações 1.2b e~2 calculada dobra a dobra (mesmas partições da validação cruzada principal). Em todos os modelos, a configuração com \texttt{Feature\_Savgol\_Min} vence na maioria das dobras.

\begin{table}[htbp]
\centering
\caption{Diferença pareada de F1 entre as configurações 1.2b e~2 nas 25 dobras da validação cruzada (positiva quando a 1.2b é melhor).}
\label{tab:diferenca_pareada}
\footnotesize
\begin{tabular}{lcccc}
\hline
\textbf{Modelo} & \textbf{Diferença média $\pm$ DP} & \textbf{1.2b melhor} & \textbf{2 melhor} & \textbf{Empates} \\
\hline""")
for m in M:
    d = S["diferenca_pareada_escolhida_menos_2"][m]
    A(f"{ABR[m]} & {pm(d['media'], d['dp'])} & {d['a_favor']} & {d['contra']} & {d['empates']} \\\\")
A(r"""\hline
\end{tabular}
\end{table}

% -----------------------------------------------------------------------------
\section{Falsos positivos nas negativas reais}
\label{sec:fp_reais_agregado}

Como o conjunto de teste contém apenas 34 negativas reais, a Tabela~\ref{tab:fp_reais_agregado} soma as predições fora da amostra das negativas reais do desenvolvimento (predições fora da dobra da primeira repetição da validação cruzada) e do teste (modelos finais), na configuração 1.2b e no limiar $\tau = 0{,}5$. Os intervalos de confiança de 95\,\% são de Clopper--Pearson.

\begin{table}[htbp]
\centering
\caption{Negativas reais classificadas como positivas, fora da amostra (configuração 1.2b, $\tau = 0{,}5$).}
\label{tab:fp_reais_agregado}
\footnotesize
\begin{tabular}{lccccc}
\hline
\textbf{Modelo} & \textbf{Desenvolvimento} & \textbf{Teste} & \textbf{Total} & \textbf{Taxa} & \textbf{IC 95\,\%} \\
\hline""")
for m in M + [BASE]:
    f = S["fp_negativas_reais_agregado"][m]
    A(f"{ABR[m]} & {f['k_dev']}/{f['n_dev']} & {f['k_teste']}/{f['n_teste']} & {f['k']}/{f['n']} & ${pct(f['taxa'])}$ & ${pct(f['ic95'][0])}$ -- ${pct(f['ic95'][1])}$ \\\\")
A(r"""\hline
\end{tabular}
\end{table}

% -----------------------------------------------------------------------------
\section{Métricas no conjunto de teste de todas as configurações}
\label{sec:teste_todas}

A Tabela~\ref{tab:teste_todas} apresenta, apenas para registro, as métricas no conjunto de teste das cinco configurações, cada uma treinada em todo o conjunto de desenvolvimento. Essas métricas \textbf{não} foram usadas em nenhuma escolha. As diferenças entre configurações correspondem a poucas curvas e não coincidem com a ordem da validação cruzada (por exemplo, a configuração~2 aparece à frente no XGBoost), o que ilustra por que a comparação entre configurações deve ser feita por validação cruzada, e não em um único conjunto de teste.

\begin{table}[htbp]
\centering
\caption{Métricas no conjunto de teste ($\tau = 0{,}5$) de todas as configurações. ``Misto'': 341 curvas; ``Só reais'': 195 curvas. FP/FN no teste misto.}
\label{tab:teste_todas}
\footnotesize
\begin{tabular}{llccccc}
\hline
 & & \multicolumn{3}{c}{\textbf{Misto}} & \multicolumn{2}{c}{\textbf{Só reais}} \\
\textbf{Configuração} & \textbf{Modelo} & \textbf{F1} & \textbf{AUC-ROC} & \textbf{FP / FN} & \textbf{F1} & \textbf{AUC-ROC} \\
\hline""")
for c in CFG:
    for i, m in enumerate(M):
        a = te[(te.config == c) & (te.modelo == m) & (te.teste == "misto") & (te.tau == 0.5)].iloc[0]
        b = te[(te.config == c) & (te.modelo == m) & (te.teste == "só reais") & (te.tau == 0.5)].iloc[0]
        lab = f"\\multirow{{4}}{{*}}{{{c} ({NF[c]})}}" if i == 0 else ""
        A(f"{lab} & {ABR[m]} & {n(a.f1)} & {n(a.auc)} & {int(a.fp)} / {int(a.fn)} & {n(b.f1)} & {n(b.auc)} \\\\")
    A("\\hline")
A(r"""\end{tabular}
\end{table}
""")
open(ROOT + "writing_latex/Tese/apendice_experimentos.tex", "w", encoding="utf-8", newline="\n").write("\n".join(L))
print("ok", len(L))
