#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Baseline trivial (limiar de UMA feature) vs. ML, NOS MESMOS recortes de Quaoar.

Pergunta que este script responde:
    O XGBoost separa o anel fino REAL (Q2R_1) do trecho de RUIDO parecido
    (~86x de razao de probabilidade) porque combina features de forma nao
    trivial --- ou uma unica feature de profundidade (Occ_depth,
    Max_Drawdown, Feature_Savgol_Min) ja reproduziria essa separacao,
    sendo o resultado "apenas fisica"?

Metodo:
    1. Le a curva real de Quaoar e recorta as mesmas 6 janelas de
       test_quaoar_recortes.py.
    2. Extrai as features de cada recorte com o MESMO pipeline
       (extract_features + compute_occ_features).
    3. Treina, no dataset_final.csv (split misto 80/20 por curva, seed 42):
         - XGBoost (11 features, config do Experimento 5); e
         - baselines de UMA feature (LogisticRegression class_weight=balanced).
    4. Para cada recorte imprime p_ML e p_baseline(cada feature) + o valor
       bruto da feature, com foco no par decisivo dois (anel real) vs
       tres (ruido).

Previsao falseavel:
    - Se Occ_depth(dois) >> Occ_depth(tres) e o baseline sozinho reproduzir a
      separacao -> "e fisica" (a regua basta).
    - Se as profundidades forem parecidas e SO o ML separar -> o ensemble
      ganha o proprio salario justamente no evento sutil.

REQUISITO DE DADO: a curva bruta 'Gemini-Alopeke_Red-z.dat' (cedida pelo
autor de Pereira et al. 2023) NAO esta versionada no repositorio. Coloque-a
em pipeline/model_in_practice/quaoar/ e rode:  python quaoar_baseline_vs_ml.py
"""

import os
import sys
import numpy as np
import pandas as pd

# --- caminhos ---------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
QUAOAR_DIR = os.path.join(SCRIPT_DIR, 'quaoar')
CURVE_FILE = 'Gemini-Alopeke_Red-z.dat'
MODEL_TRAINING_DIR = os.path.join(SCRIPT_DIR, '..', 'model_training')
DATASET_CSV = os.path.join(
    MODEL_TRAINING_DIR, 'outputs',
    'resultado6.2_applyTestOnlyRealCurves', 'dataset_final.csv')

TIME_COL, FLUX_COL = 4, 9          # colunas do .dat do PRAIA
RS = 42

# features candidatas ao baseline trivial (uma de cada vez)
BASELINE_FEATURES = ['Occ_depth', 'Max_Drawdown', 'Feature_Savgol_Min', 'Occ_SNR_dip']

# 11 features do Experimento 5 (exclui as 17 abaixo dos metadados)
META = ['curve_name', 'source', 'occ']
EXCLUDED = ['Feature_Amp', 'Feature_Flux_std', 'Feature_Savgol_Min',
            'kmeans_centroid_dist', 'Feature_Savgol_Max', 'Occ_flux_min',
            'Occ_flux_min_over_baseline', 'Occ_n_frames_below_baseline',
            'Deriv_Min', 'Deriv_Max', 'Deriv_Mean', 'Deriv_Std', 'Deriv_Skew',
            'Deriv_Kurtosis', 'SecondDeriv_Min', 'SecondDeriv_Max', 'SecondDeriv_Std']

XGB_PARAMS = dict(n_estimators=100, max_depth=6, learning_rate=0.1,
                  subsample=0.8, colsample_bytree=0.8, random_state=RS,
                  eval_metric='logloss')

# mesmas janelas de test_quaoar_recortes.py (segundos UTC do dia)
RECORTES = {
    'zero':   {'window': (23399, 23439), 'desc': 'baseline sem ocultacao (controle NEG)'},
    'um':     {'window': (23464, 23489), 'desc': 'Q1R continuous (OCC forte)'},
    'dois':   {'window': (23560, 23575), 'desc': 'Q2R_1 anel fino REAL'},
    'tres':   {'window': (23580, 23590), 'desc': 'Q2R_1 RUIDO parecido com occ'},
    'quatro': {'window': (23810, 23835), 'desc': 'Q2R_2 anel fino'},
    'cinco':  {'window': (23880, 23940), 'desc': 'Q1R dense (OCC forte)'},
}

# --- pipeline de features (mesmo do treino) ---------------------------------
sys.path.insert(0, MODEL_TRAINING_DIR)
from build_dataset import extract_features                 # noqa: E402
from occ_features import compute_occ_features, OCC_FEATURE_NAMES  # noqa: E402


def read_curve(filepath, flux_min=-2.0, flux_max=5.0):
    data = np.genfromtxt(filepath, usecols=[TIME_COL, FLUX_COL], dtype=float)
    data = data[np.isfinite(data).all(axis=1)]
    t, f = data[:, 0], data[:, 1]
    keep = (f >= flux_min) & (f <= flux_max)
    return t[keep], f[keep]


def cut_curve(t, f, a, b):
    m = (t >= a) & (t <= b)
    return t[m], f[m]


def features_from_window(t, f, name):
    d = {'time': t.tolist(), 'flux': f.tolist(), 'flux_normalized': f.tolist()}
    feats = extract_features(d, name, use_filter='savgol')
    if feats is None:
        return None
    occ = compute_occ_features(d)
    if occ is not None:
        feats.update(occ)
    else:
        for c in OCC_FEATURE_NAMES:
            feats[c] = np.nan
    return feats


def train_models():
    """Treina XGBoost (11 feat) e os baselines de 1 feature no split misto 80/20."""
    from sklearn.model_selection import train_test_split
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from xgboost import XGBClassifier

    df = pd.read_csv(DATASET_CSV).dropna()
    ci = df[['curve_name', 'occ']].drop_duplicates()
    _, c_te = train_test_split(ci['curve_name'].values, test_size=0.20,
                               random_state=RS, stratify=ci['occ'].values)
    tr = df[~df['curve_name'].isin(c_te)]
    ytr = tr['occ'].values

    fcols = [c for c in df.columns if c not in META and c not in EXCLUDED]
    imp = SimpleImputer(strategy='median')
    Xtr = imp.fit_transform(tr[fcols])
    xgb = XGBClassifier(**XGB_PARAMS).fit(Xtr, ytr)

    # baselines de uma feature (probabilidade calibrada por logistica)
    base = {}
    for feat in BASELINE_FEATURES:
        med = tr[feat].median()
        x = tr[[feat]].fillna(med).values
        lr = LogisticRegression(class_weight='balanced', max_iter=1000,
                                random_state=RS).fit(x, ytr)
        base[feat] = (lr, med)
    return dict(xgb=xgb, imputer=imp, fcols=fcols, base=base)


def main():
    print("=" * 84)
    print("  BASELINE TRIVIAL (1 feature) vs XGBoost  --  recortes de Quaoar")
    print("=" * 84)

    filepath = os.path.join(QUAOAR_DIR, CURVE_FILE)
    if not os.path.exists(filepath):
        print(f"\n[FALTA O DADO] Curva bruta nao encontrada:\n    {filepath}\n")
        print("A curva 'Gemini-Alopeke_Red-z.dat' (Pereira et al. 2023) nao esta")
        print("versionada no repositorio. Coloque-a em pipeline/model_in_practice/")
        print("quaoar/ e rode novamente. O script esta pronto e fara:")
        print("  ML (XGBoost 11 feat) vs baseline de 1 feature, por recorte,")
        print("  com foco no par 'dois' (anel real) vs 'tres' (ruido).")
        return 1

    print("\n[1] Treinando XGBoost (11 feat) e baselines de 1 feature (split 80/20)...")
    M = train_models()

    print("[2] Lendo a curva e extraindo features por recorte...")
    t_full, f_full = read_curve(filepath)
    rows = []
    for name, cfg in RECORTES.items():
        a, b = cfg['window']
        tc, fc = cut_curve(t_full, f_full, a, b)
        if len(tc) < 5:
            print(f"    recorte {name}: <5 pontos, pulado")
            continue
        feats = features_from_window(tc, fc, f'quaoar_{name}')
        if feats is None:
            print(f"    recorte {name}: extracao falhou, pulado")
            continue
        # ML
        X = pd.DataFrame([feats]).reindex(columns=M['fcols'])
        X = M['imputer'].transform(X)
        p_ml = float(M['xgb'].predict_proba(X)[0, 1])
        # baselines de 1 feature
        pbase = {}
        for feat, (lr, med) in M['base'].items():
            v = feats.get(feat, np.nan)
            v = med if (v is None or (isinstance(v, float) and np.isnan(v))) else v
            pbase[feat] = float(lr.predict_proba([[v]])[0, 1])
        rows.append((name, cfg['desc'], len(tc), feats.get('Occ_depth', np.nan),
                     p_ml, pbase))

    # --- tabela ---
    print("\n" + "=" * 84)
    hdr = (f"{'recorte':8}{'N':>5}{'Occ_depth':>11}{'p_XGB':>9}" +
           "".join(f"{'p['+f[:8]+']':>13}" for f in BASELINE_FEATURES))
    print(hdr); print("-" * len(hdr))
    for name, desc, n, depth, p_ml, pbase in rows:
        line = f"{name:8}{n:>5}{depth:>11.4f}{p_ml:>9.4f}"
        line += "".join(f"{pbase[f]:>13.4f}" for f in BASELINE_FEATURES)
        print(line)
    for name, desc, *_ in rows:
        print(f"   {name:8} = {desc}")

    # --- separacao anel real (dois) vs ruido (tres) ---
    d = {r[0]: r for r in rows}
    if 'dois' in d and 'tres' in d:
        print("\n" + "-" * 84)
        print("SEPARACAO anel real (dois) / ruido (tres) -- quanto MAIOR, melhor:")
        _, _, _, _, ml2, pb2 = d['dois']
        _, _, _, _, ml3, pb3 = d['tres']
        eps = 1e-9
        print(f"  XGBoost:            {ml2/ (ml3+eps):8.1f}x   ({ml2:.4f} / {ml3:.4f})")
        for f in BASELINE_FEATURES:
            print(f"  baseline[{f:18}]: {pb2[f]/(pb3[f]+eps):8.1f}x   "
                  f"({pb2[f]:.4f} / {pb3[f]:.4f})")
        print("\nLeitura: se algum baseline reproduzir a separacao do XGB, o merito")
        print("e da fisica (a regua basta). Se so o XGB separar, o ensemble agrega")
        print("valor justamente no evento sutil.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
