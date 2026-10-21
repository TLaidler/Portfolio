#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reanálise pós-banca (out/2026): seleção de configuração e de limiar por validação cruzada,
com o conjunto de teste reservado e usado uma única vez.

Protocolo
---------
1. Conjunto: dataset_final.csv (1693 curvas; a única com NaN é descartada -> 1692).
   Correção de unidade: Occ_duration_s das curvas do Grupo do Rio (tempo em dias julianos)
   e dos recortes delas é convertida para segundos (x 86400). É a única feature que usa o tempo.
2. Grupos: todas as curvas de um mesmo evento (objeto + mês; as datas do banco têm resolução mensal) —
   cordas de observadores diferentes e recortes "antes"/"depois" de uma mesma curva (a curva-mãe não entra
   no conjunto) — ficam sempre do mesmo lado de qualquer partição. Curvas simuladas formam grupos individuais.
3. Teste reservado: 1/5 dos grupos (StratifiedGroupKFold, semente 42). Usado só no passo 7.
4. Desenvolvimento (4/5 restantes): validação cruzada estratificada e agrupada, 5 dobras x 5 repetições,
   para cada configuração de features x modelo, mais um baseline de um único limiar em Occ_depth.
5. Escolha da configuração: regra de um desvio padrão — a configuração mais simples cujo F1 médio
   (melhor modelo) fica a menos de um desvio padrão do melhor resultado.
6. Escolha do limiar: nas predições fora da dobra (repetição 0) do desenvolvimento.
7. Avaliação final: modelos retreinados em todo o desenvolvimento, avaliados uma vez no teste
   (misto e restrito a curvas reais); McNemar exato entre os modelos da configuração escolhida e de cada
   modelo contra o baseline.
8. Robustez da escolha: a mesma regra de 1 DP repetida com outras sementes da validação cruzada (2000-2004).
Hiperparâmetros: os mesmos do Apêndice B da dissertação.

Uso:  python reanalise_banca.py
Saídas: outputs/reanalise_banca/ (JSON, CSV, modelos/ com os modelos finais da configuração escolhida)
        e ../../writing_latex/Tese/pngs/reanalise/ (figuras).
O Apêndice A da dissertação é gerado a partir dessas saídas por gerar_apendice_a.py.
"""
import json
import os
import re

import joblib
import sqlite3
import sys
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
from scipy.stats import binomtest, beta
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, fbeta_score,
                             roc_auc_score, roc_curve, precision_recall_curve, confusion_matrix)
from xgboost import XGBClassifier
from catboost import CatBoostClassifier

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "outputs", "resultado1_split0.8-0.2_all-features", "dataset_final.csv")
DB = os.path.join(HERE, "..", "data_warehouse", "stellar_occultations.db")
OUT = os.path.join(HERE, "outputs", "reanalise_banca")
FIG = os.path.join(HERE, "..", "..", "writing_latex", "Tese", "pngs", "reanalise")
os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

SEED = 42
N_FOLDS, N_REPS = 5, 5
plt.rcParams.update({"font.size": 15, "axes.titlesize": 16, "axes.labelsize": 15, "xtick.labelsize": 13,
                     "ytick.labelsize": 13, "legend.fontsize": 12, "figure.dpi": 100, "savefig.dpi": 200,
                     "savefig.bbox": "tight"})

# ----------------------------------------------------------------------------- configurações
F13 = ["Feature_Savgol_Min", "Feature_Savgol_std", "Max_Drawdown", "MinLogP_KS", "MinLogP_Ttest", "Occ_SNR_dip",
       "Occ_baseline_std", "Occ_chi2_constant", "Occ_chi2_ratio", "Occ_chi2_square_well", "Occ_depth",
       "Occ_duration_s", "kmeans_centroid_dist"]
CONFIGS = {  # nome -> features (ordem: do mais completo ao mais simples)
    "1": None,  # preenchido com as 28
    "1.1": F13,
    "1.2a": [f for f in F13 if f != "Feature_Savgol_Min"],
    "1.2b": [f for f in F13 if f != "kmeans_centroid_dist"],
    "2": [f for f in F13 if f not in ("Feature_Savgol_Min", "kmeans_centroid_dist")],
}
SUPLEMENTAR = {"2 sem testes de quartis": [f for f in CONFIGS["2"] if f not in ("MinLogP_Ttest", "MinLogP_KS")],
               "1.2b sem testes de quartis": [f for f in CONFIGS["1.2b"] if f not in ("MinLogP_Ttest", "MinLogP_KS")],
               "1.2b sem teste t": [f for f in CONFIGS["1.2b"] if f != "MinLogP_Ttest"]}
MODELOS = ["Regressão Logística", "Random Forest", "XGBoost", "CatBoost"]


def make_model(name, seed):
    if name == "Regressão Logística":
        return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                             LogisticRegression(penalty="l2", C=1.0, solver="lbfgs", max_iter=1000,
                                                class_weight="balanced", random_state=seed))
    if name == "Random Forest":
        return make_pipeline(SimpleImputer(strategy="median"),
                             RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_split=5,
                                                    min_samples_leaf=2, class_weight="balanced",
                                                    random_state=seed, n_jobs=-1))
    if name == "XGBoost":
        return make_pipeline(SimpleImputer(strategy="median"),
                             XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, subsample=0.8,
                                           colsample_bytree=0.8, random_state=seed, eval_metric="logloss",
                                           verbosity=0, n_jobs=-1))
    if name == "CatBoost":
        return make_pipeline(SimpleImputer(strategy="median"),
                             CatBoostClassifier(iterations=100, depth=6, learning_rate=0.1,
                                                auto_class_weights="Balanced", random_seed=seed, verbose=0,
                                                allow_writing_files=False))
    if name == "Baseline (limiar em Occ_depth)":
        return DecisionTreeClassifier(max_depth=1, class_weight="balanced", random_state=seed)
    raise ValueError(name)


def metrics(y, p, tau=0.5, real_neg_mask=None):
    yhat = (p >= tau).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, yhat, labels=[0, 1]).ravel()
    out = dict(acc=accuracy_score(y, yhat), prec=precision_score(y, yhat, zero_division=0),
               rec=recall_score(y, yhat), f1=f1_score(y, yhat), f2=fbeta_score(y, yhat, beta=2),
               auc=roc_auc_score(y, p) if len(np.unique(y)) == 2 else np.nan,
               tp=int(tp), tn=int(tn), fp=int(fp), fn=int(fn))
    if real_neg_mask is not None and real_neg_mask.any():
        out["fpr_real"] = float(np.mean(yhat[real_neg_mask] == 1))
        out["n_real_neg"] = int(real_neg_mask.sum())
    return out


def clopper_pearson(k, n, a=0.05):
    return (0.0 if k == 0 else float(beta.ppf(a / 2, k, n - k + 1)),
            1.0 if k == n else float(beta.ppf(1 - a / 2, k + 1, n - k)))


def mcnemar(ok_a, ok_b):
    b, c = int(np.sum(~ok_a & ok_b)), int(np.sum(ok_a & ~ok_b))
    return b, c, (binomtest(min(b, c), b + c, 0.5).pvalue if b + c > 0 else 1.0)


VIRG = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",").replace("-", "−"))


def virgula(*axes):  # vírgula decimal nos eixos numéricos
    for ax in axes:
        ax.xaxis.set_major_formatter(VIRG); ax.yaxis.set_major_formatter(VIRG)


# ----------------------------------------------------------------------------- dados
df = pd.read_csv(DATA)
n_total = len(df)
df = df.dropna().reset_index(drop=True)
FEATS28 = [c for c in df.columns if c not in ("curve_name", "source", "occ")]
CONFIGS["1"] = FEATS28
y = df["occ"].astype(int).values
is_real_neg = df["source"].isin(["artificial_negative", "db_negative"]).values
is_real = (df["source"] != "synthetic").values

# --- correção de unidade de tempo (dias -> segundos)
con = sqlite3.connect(DB)
obs = pd.read_sql("SELECT id, object_name, observation_date, additional_metadata FROM observations", con)
obs["observer"] = obs["additional_metadata"].str.extract(r"observer:\s*([^,]+)")[0].str.strip()
obs["key"] = obs["object_name"].astype(str) + "_" + obs["observation_date"].astype(str).str[:10] + "_" + obs["observer"].astype(str)
dt = pd.read_sql("SELECT observation_id, time FROM light_curves", con)
dt = dt.groupby("observation_id")["time"].apply(lambda t: np.median(np.diff(np.sort(t.values))) if len(t) > 2 else np.nan)
obs = obs.merge(dt.rename("dt"), left_on="id", right_index=True, how="left")
jd_keys = set(obs.loc[obs["dt"] < 1e-3, "key"])  # cadência < 1 ms => tempo em dias
parent = df["curve_name"].str.replace(r"_(antes|depois)_artificial$", "", regex=True)
jd_rows = parent.isin(jd_keys).values
df.loc[jd_rows, "Occ_duration_s"] *= 86400.0

# --- grupos por evento (objeto + data; na prática objeto + mês, pois todas as datas do banco têm dia 01);
#     simuladas são grupos individuais
event = parent.str.extract(r"^(.*?_\d{4}-\d{2}-\d{2})")[0]
groups = np.where(df["source"] == "synthetic", df["curve_name"], event.fillna(df["curve_name"])).astype(str)

# ----------------------------------------------------------------------------- teste reservado
outer = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
dev_idx, test_idx = next(outer.split(df, y, groups))
assert not set(groups[dev_idx]) & set(groups[test_idx])
D, T = df.iloc[dev_idx].reset_index(drop=True), df.iloc[test_idx].reset_index(drop=True)
yD, yT = y[dev_idx], y[test_idx]
gD = groups[dev_idx]
rnD, rnT, realT = is_real_neg[dev_idx], is_real_neg[test_idx], is_real[test_idx]
summary = {"n_csv": n_total, "n_usadas": len(df), "n_jd_corrigidas": int(jd_rows.sum()),
           "n_grupos": int(len(set(groups))), "dev": {"n": len(D), "pos": int(yD.sum()), "neg": int((1 - yD).sum())},
           "teste": {"n": len(T), "pos": int(yT.sum()), "neg": int((1 - yT).sum()),
                     "neg_reais": int(rnT.sum()), "neg_simuladas": int(((1 - yT) & ~realT).sum()),
                     "reais": int(realT.sum())}}
print(json.dumps(summary, ensure_ascii=False, indent=1))

# ----------------------------------------------------------------------------- CV no desenvolvimento
def run_cv(cfgs, seeds, baseline_cfg=None):
    rows, oof = [], {}
    for cfg, cols in cfgs.items():
        models = MODELOS + (["Baseline (limiar em Occ_depth)"] if cfg == baseline_cfg else [])
        for mname in models:
            cols_m = ["Occ_depth"] if mname.startswith("Baseline") else cols
            for rep, seed in enumerate(seeds):
                cv = StratifiedGroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
                p_oof = np.zeros(len(D))
                for k, (tr, va) in enumerate(cv.split(D, yD, gD)):
                    m = make_model(mname, seed)
                    m.fit(D.iloc[tr][cols_m], yD[tr])
                    p = m.predict_proba(D.iloc[va][cols_m])[:, 1]
                    p_oof[va] = p
                    r = metrics(yD[va], p, 0.5, rnD[va]); r.update(config=cfg, modelo=mname, rep=rep, dobra=k)
                    rows.append(r)
                if rep == 0:
                    oof[(cfg, mname)] = p_oof
        print("CV feito:", cfg, seeds[0])
    return pd.DataFrame(rows), oof


def one_sd_rule(agg):
    best = agg[agg.config.isin(CONFIGS)].sort_values("f1", ascending=False).iloc[0]
    limit = best.f1 - best.f1_sd
    order_simple = sorted(CONFIGS, key=lambda c: len(CONFIGS[c]))  # menos features primeiro
    return best, limit, next(c for c in order_simple if agg[(agg.config == c)].f1.max() >= limit)


all_cfgs = {**CONFIGS, **SUPLEMENTAR}
cvdf, oof = run_cv(all_cfgs, list(range(N_REPS)), baseline_cfg="2")
cvdf.to_csv(os.path.join(OUT, "cv_dobras.csv"), index=False)
agg = cvdf.groupby(["config", "modelo"]).agg(
    f1=("f1", "mean"), f1_sd=("f1", "std"), auc=("auc", "mean"), auc_sd=("auc", "std"),
    prec=("prec", "mean"), prec_sd=("prec", "std"), rec=("rec", "mean"), rec_sd=("rec", "std"),
    acc=("acc", "mean"), acc_sd=("acc", "std"), fpr_real=("fpr_real", "mean"), fpr_real_sd=("fpr_real", "std")).reset_index()
agg.to_csv(os.path.join(OUT, "cv_resumo.csv"), index=False)

# --- escolha da configuração (regra de um desvio padrão)
best, limit, chosen = one_sd_rule(agg)
summary["selecao"] = {"melhor_config": best.config, "melhor_modelo": best.modelo, "f1_melhor": best.f1,
                      "f1_sd_melhor": best.f1_sd, "limite_1sd": limit, "config_escolhida": chosen,
                      "melhor_f1_por_config": agg[agg.config.isin(CONFIGS)].groupby("config").f1.max().to_dict(),
                      "n_features_por_config": {c: len(v) for c, v in all_cfgs.items()}}
print("Configuração escolhida:", chosen, summary["selecao"])

# --- diferença pareada por dobra entre a configuração escolhida e a 2 (mesmas dobras, mesmo modelo)
par = {}
for mname in MODELOS:
    a = cvdf[(cvdf.config == chosen) & (cvdf.modelo == mname)].sort_values(["rep", "dobra"]).f1.values
    b = cvdf[(cvdf.config == "2") & (cvdf.modelo == mname)].sort_values(["rep", "dobra"]).f1.values
    d = a - b
    par[mname] = {"media": float(d.mean()), "dp": float(d.std(ddof=1)), "a_favor": int((d > 1e-12).sum()),
                  "contra": int((d < -1e-12).sum()), "empates": int((np.abs(d) <= 1e-12).sum())}
summary["diferenca_pareada_escolhida_menos_2"] = par

# --- robustez: mesma regra com outras sementes da validação cruzada
cv_alt, _ = run_cv(CONFIGS, [2000 + i for i in range(N_REPS)])
agg_alt = cv_alt.groupby(["config", "modelo"]).agg(f1=("f1", "mean"), f1_sd=("f1", "std")).reset_index()
agg_alt.to_csv(os.path.join(OUT, "cv_resumo_sementes_alternativas.csv"), index=False)
b_alt, l_alt, c_alt = one_sd_rule(agg_alt)
summary["robustez_sementes"] = {"sementes": "2000-2004", "melhor_config": b_alt.config, "melhor_modelo": b_alt.modelo,
                                "f1_melhor": b_alt.f1, "f1_sd_melhor": b_alt.f1_sd, "limite_1sd": l_alt,
                                "config_escolhida": c_alt,
                                "melhor_f1_por_config": agg_alt.groupby("config").f1.max().to_dict()}
print("Robustez:", summary["robustez_sementes"])

# ----------------------------------------------------------------------------- limiar (OOF, rep 0)
grid = np.round(np.arange(0.01, 1.0, 0.01), 2)
thr = {}
for mname in MODELOS:
    p = oof[(chosen, mname)]
    rec = np.array([recall_score(yD, p >= t) for t in grid])
    f2 = np.array([fbeta_score(yD, p >= t, beta=2) for t in grid])
    ok = grid[rec >= 0.995]
    thr[mname] = {"tau_sens": float(ok.max()) if ok.size else 0.01, "tau_f2": float(grid[f2.argmax()]),
                  "fpr_real_oof_tau003": float(np.mean(p[rnD] >= 0.03)),
                  "fpr_real_oof_tau05": float(np.mean(p[rnD] >= 0.5))}
summary["limiares"] = thr

# ----------------------------------------------------------------------------- avaliação final (teste, uma vez)
final_rows, final_pred, final_models, imp_cfg = [], {}, {}, {}
for cfg, cols in CONFIGS.items():
    models = MODELOS + (["Baseline (limiar em Occ_depth)"] if cfg == chosen else [])
    for mname in models:
        cols_m = ["Occ_depth"] if mname.startswith("Baseline") else cols
        m = make_model(mname, SEED)
        m.fit(D[cols_m], yD)
        p = m.predict_proba(T[cols_m])[:, 1]
        final_pred[(cfg, mname)] = p
        if cfg == chosen:
            final_models[mname] = m
        if mname in ("Random Forest", "XGBoost", "CatBoost"):  # importâncias de todas as configurações (normalizadas)
            v = np.asarray(m[-1].feature_importances_, float)
            imp_cfg.setdefault(cfg, {})[mname] = dict(zip(cols_m, (v / v.sum()).tolist()))
        for escopo, mask in [("misto", np.ones(len(T), bool)), ("só reais", realT)]:
            r = metrics(yT[mask], p[mask], 0.5, rnT[mask]); r.update(config=cfg, modelo=mname, teste=escopo, tau=0.5)
            final_rows.append(r)
        if cfg == chosen and mname in thr:
            for nome_t in ("tau_sens", "tau_f2"):
                t = thr[mname][nome_t]
                r = metrics(yT, p, t, rnT); r.update(config=cfg, modelo=mname, teste="misto", tau=t, criterio=nome_t)
                final_rows.append(r)
final = pd.DataFrame(final_rows)
final.to_csv(os.path.join(OUT, "teste_final.csv"), index=False)
pd.DataFrame({"curve_name": T.curve_name, "source": T.source, "occ": yT,
              **{m: final_pred[(chosen, m)] for m in MODELOS}}).to_csv(os.path.join(OUT, "predicoes_teste.csv"), index=False)
# modelos finais da configuração escolhida (pipelines completos, com imputer), para uso em curvas novas (ex.: Quaoar)
os.makedirs(os.path.join(OUT, "modelos"), exist_ok=True)
joblib.dump({"features": CONFIGS[chosen], "modelos": final_models}, os.path.join(OUT, "modelos", f"modelos_config_{chosen}.joblib"))

# --- McNemar exato (teste misto, configuração escolhida, tau = 0,5)
mc = []
BASE = "Baseline (limiar em Occ_depth)"
acerto = {m: (final_pred[(chosen, m)] >= .5).astype(int) == yT for m in MODELOS + [BASE]}
pares = [(a, b_) for i, a in enumerate(MODELOS) for b_ in MODELOS[i + 1:]] + [(BASE, m) for m in MODELOS]
for a, b_ in pares:
    b, c, pval = mcnemar(acerto[a], acerto[b_])
    mc.append(dict(A=a, B=b_, b_A_erra_B_acerta=b, c_A_acerta_B_erra=c, p_exato=pval))
pd.DataFrame(mc).to_csv(os.path.join(OUT, "mcnemar_exato.csv"), index=False)

# --- falsos positivos em negativas reais, agregados fora da amostra (OOF rep. 0 do desenvolvimento + teste)
fpa = {}
for mname in MODELOS + [BASE]:
    p_dev = oof[("2", BASE)] if mname == BASE else oof[(chosen, mname)]
    k_dev, n_dev = int((p_dev[rnD] >= .5).sum()), int(rnD.sum())
    k_te, n_te = int((final_pred[(chosen, mname)][rnT] >= .5).sum()), int(rnT.sum())
    k, n = k_dev + k_te, n_dev + n_te
    fpa[mname] = {"k_dev": k_dev, "n_dev": n_dev, "k_teste": k_te, "n_teste": n_te, "k": k, "n": n,
                  "taxa": k / n, "ic95": clopper_pearson(k, n), "ic95_teste": clopper_pearson(k_te, n_te)}
summary["fp_negativas_reais_agregado"] = fpa
summary["teste_cordas_negativas"] = T[T.source == "db_negative"].curve_name.tolist()
summary["dev_cordas_negativas"] = int((D.source == "db_negative").sum())

# --- curvas de baixo SNR_dip (< 3): avaliação fora da amostra (OOF no desenvolvimento + teste)
low = df["Occ_SNR_dip"].lt(3) & (df["occ"] == 1)
low_D, low_T = low.values[dev_idx], low.values[test_idx]
lowres = {}
for mname in MODELOS:
    hits = np.r_[oof[(chosen, mname)][low_D] >= .5, final_pred[(chosen, mname)][low_T] >= .5]
    lowres[mname] = {"n": int(hits.size), "detectadas": int(hits.sum())}
pos = df["occ"] == 1
summary["baixo_snr"] = {"n_no_conjunto": int(low.sum()), "mediana_Savgol_Min": float(df.loc[low, "Feature_Savgol_Min"].median()),
                        "mediana_Savgol_Min_positivas": float(df.loc[pos, "Feature_Savgol_Min"].median()),
                        "mediana_baseline_std": float(df.loc[low, "Occ_baseline_std"].median()),
                        "mediana_baseline_std_positivas": float(df.loc[pos, "Occ_baseline_std"].median()),
                        "mediana_SNR_dip_negativas": float(df.loc[~pos, "Occ_SNR_dip"].median()),
                        "por_modelo": lowres}

# --- qualidade do fluxo normalizado nas positivas do banco (valores fisicamente implausíveis)
pdb = df[df.source == "db_positive"]
summary["qualidade_fluxo_positivas"] = {"n": len(pdb), "savgol_max_gt_1.5": int((pdb.Feature_Savgol_Max > 1.5).sum()),
                                        "flux_min_lt_-0.5": int((pdb.Occ_flux_min < -0.5).sum()),
                                        "uniao": int(((pdb.Feature_Savgol_Max > 1.5) | (pdb.Occ_flux_min < -0.5)).sum())}

# ----------------------------------------------------------------------------- ablação do tamanho do treino (Exp. 2.2)
fr_rows = []
cols = CONFIGS[chosen]
for frac in (0.25, 0.5, 0.75, 1.0):
    for rep in range(3):
        cv = StratifiedGroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=100 + rep)
        rng = np.random.default_rng(rep)
        for tr, va in cv.split(D, yD, gD):
            gtr = np.unique(gD[tr])
            keep_g = set(rng.choice(gtr, size=max(2, int(round(frac * gtr.size))), replace=False))
            tr2 = tr[np.isin(gD[tr], list(keep_g))]
            if len(np.unique(yD[tr2])) < 2:
                continue
            for mname in MODELOS:
                m = make_model(mname, rep); m.fit(D.iloc[tr2][cols], yD[tr2])
                p = m.predict_proba(D.iloc[va][cols])[:, 1]
                fr_rows.append(dict(frac=frac, modelo=mname, n_treino=len(tr2), f1=f1_score(yD[va], p >= .5),
                                    auc=roc_auc_score(yD[va], p)))
frdf = pd.DataFrame(fr_rows)
frdf.to_csv(os.path.join(OUT, "ablacao_tamanho_treino.csv"), index=False)
fr_agg = frdf.groupby(["frac", "modelo"]).agg(f1=("f1", "mean"), f1_sd=("f1", "std"), n_treino=("n_treino", "mean")).reset_index()
fr_agg.to_csv(os.path.join(OUT, "ablacao_tamanho_treino_resumo.csv"), index=False)

# ----------------------------------------------------------------------------- importâncias e coeficientes
imp = {}
lr = final_models["Regressão Logística"][-1]
imp["Regressão Logística"] = dict(zip(cols, np.abs(lr.coef_[0])))
imp["Random Forest"] = dict(zip(cols, final_models["Random Forest"][-1].feature_importances_))
g = final_models["XGBoost"][-1].get_booster().get_score(importance_type="gain")
gain = np.array([g.get(f"f{i}", 0.0) for i in range(len(cols))]); gain = gain / gain.sum()
imp["XGBoost"] = dict(zip(cols, gain))
imp["CatBoost"] = dict(zip(cols, final_models["CatBoost"][-1].get_feature_importance()))
coef = pd.DataFrame({"feature": cols, "theta": lr.coef_[0], "odds_ratio_por_1dp": np.exp(lr.coef_[0])}).sort_values("theta")
coef.to_csv(os.path.join(OUT, "coeficientes_regressao_logistica.csv"), index=False)
summary["intercepto_rl"] = float(lr.intercept_[0])
summary["importancias"] = {m: {k: float(v) for k, v in d.items()} for m, d in imp.items()}
summary["importancias_por_config"] = imp_cfg  # feature_importances_ nativo (XGB: gain), normalizado para somar 1

# ----------------------------------------------------------------------------- figuras
POS, NEG = "Positiva (1)", "Negativa (0)"
CORES = {"Regressão Logística": "#4C72B0", "Random Forest": "#55A868", "XGBoost": "#C44E52", "CatBoost": "#8172B2"}

# matrizes de confusão (teste, configuração escolhida)
fig, axs = plt.subplots(2, 2, figsize=(8, 7.5))
for ax, mname in zip(axs.ravel(), MODELOS):
    cm = confusion_matrix(yT, final_pred[(chosen, mname)] >= .5, labels=[0, 1])
    ax.imshow(cm, cmap="Blues")
    for (i, j), v in np.ndenumerate(cm):
        ax.text(j, i, str(v), ha="center", va="center", fontsize=20, color="white" if v > cm.max() / 2 else "black")
    ax.set_xticks([0, 1], [NEG, POS]); ax.set_yticks([0, 1], [NEG, POS], rotation=90, va="center")
    ax.set_xlabel("Classe predita"); ax.set_ylabel("Classe verdadeira"); ax.set_title(mname)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "matrizes_confusao_teste.png")); plt.close(fig)

# ROC (teste)
fig, ax = plt.subplots(figsize=(7.5, 6.5))
for mname in MODELOS:
    fpr, tpr, _ = roc_curve(yT, final_pred[(chosen, mname)])
    ax.plot(fpr, tpr, lw=2, color=CORES[mname], label=f"{mname} (AUC = {roc_auc_score(yT, final_pred[(chosen, mname)]):.4f})".replace(".", ","))
ax.plot([0, 1], [0, 1], "k--", lw=1, label="Classificador aleatório")
ax.set_xlabel("Taxa de falsos positivos"); ax.set_ylabel("Taxa de verdadeiros positivos")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2, fontsize=11); ax.grid(alpha=.3)
axin = inset_axes(ax, width="50%", height="45%", loc="center right", borderpad=1.5)
for mname in MODELOS:
    fpr, tpr, _ = roc_curve(yT, final_pred[(chosen, mname)])
    axin.plot(fpr, tpr, lw=2, color=CORES[mname])
axin.set_xlim(0, 0.1); axin.set_ylim(0.9, 1.0); axin.grid(alpha=.3); axin.tick_params(labelsize=11)
virgula(ax, axin)
fig.savefig(os.path.join(FIG, "roc_teste.png")); plt.close(fig)

# precisão-sensibilidade (OOF do desenvolvimento) com ampliação
fig, ax = plt.subplots(figsize=(7.5, 6))
for mname in MODELOS:
    pr, rc, _ = precision_recall_curve(yD, oof[(chosen, mname)])
    ax.plot(rc, pr, lw=2, color=CORES[mname], label=mname)
ax.set_xlabel("Sensibilidade"); ax.set_ylabel("Precisão"); ax.set_ylim(0.45, 1.02); ax.grid(alpha=.3)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2)
axin = inset_axes(ax, width="50%", height="45%", loc="center", borderpad=1)
for mname in MODELOS:
    pr, rc, _ = precision_recall_curve(yD, oof[(chosen, mname)])
    axin.plot(rc, pr, lw=2, color=CORES[mname])
axin.set_xlim(0.95, 1.0); axin.set_ylim(0.95, 1.0); axin.grid(alpha=.3); axin.tick_params(labelsize=11)
mark_inset(ax, axin, loc1=1, loc2=4, fc="none", ec="0.5")
virgula(ax, axin)
fig.savefig(os.path.join(FIG, "precisao_sensibilidade_oof.png")); plt.close(fig)

# métricas em função do limiar (OOF), quatro modelos
fig, axs = plt.subplots(2, 2, figsize=(8.5, 7.5), sharex=True, sharey=True)
for ax, mname in zip(axs.ravel(), MODELOS):
    p = oof[(chosen, mname)]
    ax.plot(grid, [precision_score(yD, p >= t, zero_division=0) for t in grid], lw=2, label="Precisão")
    ax.plot(grid, [recall_score(yD, p >= t) for t in grid], lw=2, label="Sensibilidade")
    ax.plot(grid, [f1_score(yD, p >= t) for t in grid], lw=2, label="F1")
    ax.plot(grid, [fbeta_score(yD, p >= t, beta=2) for t in grid], lw=2, ls="--", label="F$_2$")
    ax.axvline(thr[mname]["tau_sens"], color="k", ls=":", lw=1.5, label="$\\tau$ (sens. $\\geq$ 99,5%)")
    ax.set_title(mname); ax.set_ylim(0.6, 1.01); ax.grid(alpha=.3)
    virgula(ax)
for ax in axs[1]: ax.set_xlabel("Limiar de decisão $\\tau$")
for ax in axs[:, 0]: ax.set_ylabel("Métrica")
axs[0, 0].legend(loc="lower center", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "metricas_vs_limiar_oof.png")); plt.close(fig)

# importância (5 maiores por modelo); rótulos = identificadores sem os prefixos Feature_ e Occ_
TIT = {"Regressão Logística": "Regressão Logística ($|\\theta_j|$)", "Random Forest": "Random Forest (MDI)",
       "XGBoost": "XGBoost (gain)", "CatBoost": "CatBoost (PredictionValuesChange)"}
curto = lambda c: c.replace("Feature_", "").replace("Occ_", "")
fig, axs = plt.subplots(2, 2, figsize=(9.5, 7.5))
for ax, mname in zip(axs.ravel(), MODELOS):
    s = pd.Series(imp[mname]).sort_values().tail(5)
    ax.barh([curto(k) for k in s.index], s.values, color=CORES[mname])
    ax.set_title(TIT[mname], fontsize=13); ax.grid(axis="x", alpha=.3); ax.set_xlabel("Importância")
    ax.xaxis.set_major_formatter(VIRG)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "importancia_top5.png")); plt.close(fig)

# correlação de Spearman entre as 28 features (triângulo inferior)
corr = df[FEATS28].corr(method="spearman")
fig, ax = plt.subplots(figsize=(8.5, 7.5))
im = ax.imshow(np.where(np.tril(np.ones_like(corr.values, bool)), corr.values, np.nan), cmap="RdBu_r", vmin=-1, vmax=1)
lab = [curto(c) for c in FEATS28]
ax.set_xticks(range(len(lab)), lab, rotation=90, fontsize=10); ax.set_yticks(range(len(lab)), lab, fontsize=10)
for s_ in ax.spines.values(): s_.set_visible(False)
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Correlação de Spearman")
cbar.ax.yaxis.set_major_formatter(VIRG)
fig.savefig(os.path.join(FIG, "correlacao_features.png")); plt.close(fig)
pairs = [(a, b, corr.loc[a, b]) for i, a in enumerate(FEATS28) for b in FEATS28[i + 1:] if abs(corr.loc[a, b]) >= 0.9]
summary["pares_corr_ge_0.9"] = sorted([(a, b, round(float(v), 3)) for a, b, v in pairs], key=lambda x: -abs(x[2]))

# histograma da distância entre centróides (K-means) por classe
fig, ax = plt.subplots(figsize=(8, 5))
v = df["kmeans_centroid_dist"]; lo, hi = v.quantile(.01), v.quantile(.99)
bins = np.linspace(lo, hi, 50)
ax.hist(v[(df.occ == 0) & ~is_real], bins=bins, alpha=.55, label="Negativas simuladas", color="#4C72B0")
ax.hist(v[(df.occ == 0) & is_real], bins=bins, alpha=.75, label="Negativas reais", color="#DD8452")
ax.hist(v[df.occ == 1], bins=bins, alpha=.55, label="Positivas", color="#C44E52")
ax.set_xlabel("Distância entre os centroides do K-means"); ax.set_ylabel("Número de curvas")
ax.legend(); ax.grid(alpha=.3); virgula(ax)
fig.savefig(os.path.join(FIG, "histograma_kmeans.png")); plt.close(fig)

# curvas de aprendizado do boosting (treino x validação), dobra 0 da repetição 0
cv = StratifiedGroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=0)
tr, va = next(cv.split(D, yD, gD))
xgb = XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
                    random_state=SEED, eval_metric="logloss", verbosity=0)
xgb.fit(D.iloc[tr][cols], yD[tr], eval_set=[(D.iloc[tr][cols], yD[tr]), (D.iloc[va][cols], yD[va])], verbose=False)
ev = xgb.evals_result()
cb = CatBoostClassifier(iterations=100, depth=6, learning_rate=0.1, auto_class_weights="Balanced", random_seed=SEED,
                        verbose=0, allow_writing_files=False)
cb.fit(D.iloc[tr][cols], yD[tr], eval_set=(D.iloc[va][cols], yD[va]), use_best_model=False)
evc = cb.get_evals_result()
lc = {"xgb_treino": ev["validation_0"]["logloss"][-1], "xgb_valid": ev["validation_1"]["logloss"][-1],
      "cb_treino": evc["learn"]["Logloss"][-1], "cb_valid": evc["validation"]["Logloss"][-1],
      "xgb_iter_min_valid": int(np.argmin(ev["validation_1"]["logloss"])) + 1,
      "cb_iter_min_valid": int(np.argmin(evc["validation"]["Logloss"])) + 1}
summary["curvas_aprendizado"] = lc
fig, axs = plt.subplots(1, 2, figsize=(9, 4))
axs[0].plot(ev["validation_0"]["logloss"], lw=2, label="Treino"); axs[0].plot(ev["validation_1"]["logloss"], lw=2, label="Validação")
axs[1].plot(evc["learn"]["Logloss"], lw=2, label="Treino"); axs[1].plot(evc["validation"]["Logloss"], lw=2, label="Validação")
for ax, t in zip(axs, ["(a) XGBoost", "(b) CatBoost"]):
    ax.set_title(t); ax.set_xlabel("Iteração de boosting"); ax.set_ylabel("Perda logarítmica"); ax.legend(); ax.grid(alpha=.3)
    virgula(ax)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "curvas_aprendizado_boosting.png")); plt.close(fig)

# curva de aprendizado por tamanho do treino (Análise 2.2); deslocamento horizontal só para separar as barras
fig, ax = plt.subplots(figsize=(8, 5.5))
for i, mname in enumerate(MODELOS):
    s = fr_agg[fr_agg.modelo == mname]
    ax.errorbar(s.n_treino + 12 * (i - 1.5), s.f1, yerr=s.f1_sd, marker="o", lw=2, capsize=4, color=CORES[mname], label=mname)
ax.set_xlabel("Número de curvas no treino"); ax.set_ylabel("F1 (validação)"); ax.legend(); ax.grid(alpha=.3)
virgula(ax)
fig.savefig(os.path.join(FIG, "ablacao_tamanho_treino.png")); plt.close(fig)

# exemplos de curvas do conjunto (banco de dados + simulador)
def norm_quartis(f):
    seg = np.array_split(f, 4); means = sorted(np.mean(s) for s in seg)
    return f / np.mean(means[-2:])


lcurves = pd.read_sql("SELECT observation_id, time, flux FROM light_curves", con)
pos_db = df[(df.source == "db_positive") & ~jd_rows]
cand = pos_db.merge(obs[["key", "id"]], left_on="curve_name", right_on="key")
npts = lcurves.groupby("observation_id").size()
cand = cand[cand["id"].map(npts).between(150, 1500)]
ex_deep = cand.sort_values("Occ_SNR_dip", ascending=False).iloc[len(cand) // 10]
ex_shallow = cand[(cand.Occ_depth.between(0.25, 0.5))].sort_values("Occ_SNR_dip").iloc[len(cand[(cand.Occ_depth.between(0.25, 0.5))]) // 4]
neg_key = df[df.source == "db_negative"].curve_name.iloc[0]
neg_id = obs.loc[obs.key == neg_key, "id"].iloc[0]
sys.path.insert(0, os.path.join(HERE, "synthetic_curve"))
from simulate_curve import SyntheticLightCurveSimulator
sim = SyntheticLightCurveSimulator(mag_star=13.0, distance_km=2.5e9, diameter_km=0.0, velocity_kms=20.0,
                                   exposure_time_s=0.1, wavelength_nm=650.0, seeing_arcsec=1.2, rings=[],
                                   satellites=[], total_duration_s=40.0, random_seed=7)
sdf = sim.simulate()
tcol = next(c for c in sdf.columns if c.lower().startswith("time") or c.lower() in ("t", "t_s"))
fcol = next(c for c in sdf.columns if "norm" in c.lower())
MESES = ["jan.", "fev.", "mar.", "abr.", "maio", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."]


def rotulo(nome):  # "Objeto_AAAA-MM-01_Observador" -> "Objeto, mês/AAAA, Observador" (o dia 01 do banco é artificial)
    m = re.match(r"^(.*?)_(\d{4})-(\d{2})-\d{2}_(.*)$", nome)
    obsv = "observador não identificado" if m.group(4) == "Unknown" else m.group(4)
    return f"{m.group(1)}, {MESES[int(m.group(3)) - 1]}/{m.group(2)}, {obsv}"


fig, axs = plt.subplots(2, 2, figsize=(9.5, 7.5))
paineis = [(ex_deep, "(a) Positiva com queda profunda"), (ex_shallow, "(b) Positiva com queda parcial e ruído alto")]
for ax, (row, tit) in zip(axs.ravel()[:2], paineis):
    c = lcurves[lcurves.observation_id == row["id"]].sort_values("time")
    ax.plot(c.time - c.time.iloc[0], norm_quartis(c.flux.values), lw=.8, color="k")
    ax.set_title(f"{tit}\n{rotulo(row.curve_name)}", fontsize=12)
c = lcurves[lcurves.observation_id == neg_id].sort_values("time")
axs[1, 0].plot((c.time - c.time.iloc[0]) * 86400, norm_quartis(c.flux.values), lw=.8, color="k")  # neg_key é de Umbriel (tempo em JD)
axs[1, 0].set_title(f"(c) Negativa real (corda negativa)\n{rotulo(neg_key)}", fontsize=12)
axs[1, 1].plot(sdf[tcol] - sdf[tcol].iloc[0], sdf[fcol], lw=.8, color="k")
axs[1, 1].set_title("(d) Negativa simulada\n(exemplo gerado com o simulador)", fontsize=12)
for ax in axs.ravel():
    ax.set_xlabel("Tempo desde o início (s)"); ax.set_ylabel("Fluxo normalizado"); ax.grid(alpha=.3); virgula(ax)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "exemplos_curvas.png")); plt.close(fig)
summary["exemplos"] = {"profunda": ex_deep.curve_name, "parcial": ex_shallow.curve_name, "negativa": neg_key}

# ----------------------------------------------------------------------------- resumo
summary["teste_config_escolhida"] = final[(final.config == chosen) & (final.tau == 0.5)].to_dict("records")
summary["mcnemar"] = mc
with open(os.path.join(OUT, "resumo.json"), "w", encoding="utf-8") as fh:
    json.dump(summary, fh, ensure_ascii=False, indent=1, default=float)
print(json.dumps({k: summary[k] for k in ("selecao", "limiares", "baixo_snr", "curvas_aprendizado")}, ensure_ascii=False, indent=1, default=float))
print("ok")
