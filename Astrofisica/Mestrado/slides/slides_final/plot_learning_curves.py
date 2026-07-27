# -*- coding: utf-8 -*-
"""
Curvas de aprendizado (logloss de treino vs teste por iteração de boosting) dos
modelos FINAIS da tese — XGBoost e CatBoost na configuração enxuta do
Experimento 2 (11 features), split misto 80/20 por curva, seed 42, mesmos
hiperparâmetros de pipeline/model_training/train_model.py.
Saída: learning_curve_xgboost.png, learning_curve_catboost.png (nesta pasta).
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from xgboost import XGBClassifier
from catboost import CatBoostClassifier

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CSV = (ROOT / 'pipeline' / 'model_training' / 'outputs' /
       'resultado6.2_applyTestOnlyRealCurves' / 'dataset_final.csv')

RS = 42
META = ['curve_name', 'source', 'occ']
EXCLUDED = ['Feature_Amp', 'Feature_Flux_std', 'Feature_Savgol_Min',
            'kmeans_centroid_dist', 'Feature_Savgol_Max', 'Occ_flux_min',
            'Occ_flux_min_over_baseline', 'Occ_n_frames_below_baseline',
            'Deriv_Min', 'Deriv_Max', 'Deriv_Mean', 'Deriv_Std', 'Deriv_Skew',
            'Deriv_Kurtosis', 'SecondDeriv_Min', 'SecondDeriv_Max', 'SecondDeriv_Std']

NAVY = '#1D2D54'
BLUE = '#4896DE'
RED = '#C41E3A'


def load_split():
    df = pd.read_csv(CSV).dropna()
    ci = df[[META[0], META[2]]].drop_duplicates()
    _, c_te = train_test_split(ci[META[0]].values, test_size=0.20,
                               random_state=RS, stratify=ci[META[2]].values)
    m = df[META[0]].isin(c_te)
    tr, te = df[~m], df[m]
    fcols = [c for c in df.columns if c not in META and c not in EXCLUDED]
    imp = SimpleImputer(strategy='median')
    Xtr = imp.fit_transform(tr[fcols])
    Xte = imp.transform(te[fcols])
    return Xtr, tr[META[2]].values, Xte, te[META[2]].values, fcols


def plot_curve(train_loss, test_loss, model_name, fname):
    fig, ax = plt.subplots(figsize=(8, 5))
    it = range(1, len(train_loss) + 1)
    ax.plot(it, train_loss, color=BLUE, lw=2.2, label='Treino (logloss)')
    ax.plot(it, test_loss, color=RED, lw=2.2, label='Teste (logloss)')
    gap = test_loss[-1] - train_loss[-1]
    ax.annotate(f'gap final = {gap:.4f}',
                xy=(len(train_loss), test_loss[-1]),
                xytext=(-130, 18), textcoords='offset points',
                fontsize=10, color=NAVY,
                arrowprops=dict(arrowstyle='-', color=NAVY, lw=0.8))
    ax.set_xlabel('Iterações de boosting')
    ax.set_ylabel('Logloss')
    ax.set_title(f'Curva de aprendizado — {model_name}\n'
                 '(Exp. 2: 11 features, split 80/20 por curva, seed 42)',
                 color=NAVY, fontsize=12)
    ax.grid(alpha=0.3)
    ax.legend(frameon=True)
    fig.tight_layout()
    out = HERE / fname
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f'salvo: {out.name}  (treino={train_loss[-1]:.4f}, '
          f'teste={test_loss[-1]:.4f}, gap={gap:.4f})')


def main():
    Xtr, ytr, Xte, yte, fcols = load_split()
    print(f'{len(fcols)} features · treino={len(ytr)} · teste={len(yte)}')

    xgb = XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1,
                        subsample=0.8, colsample_bytree=0.8, random_state=RS,
                        eval_metric='logloss')
    xgb.fit(Xtr, ytr, eval_set=[(Xtr, ytr), (Xte, yte)], verbose=False)
    ev = xgb.evals_result()
    plot_curve(ev['validation_0']['logloss'], ev['validation_1']['logloss'],
               'XGBoost', 'learning_curve_xgboost.png')

    cat = CatBoostClassifier(iterations=100, depth=6, learning_rate=0.1,
                             random_state=RS, verbose=False,
                             auto_class_weights='Balanced',
                             allow_writing_files=False)
    cat.fit(Xtr, ytr, eval_set=(Xte, yte))
    ev = cat.get_evals_result()
    plot_curve(ev['learn']['Logloss'], ev['validation']['Logloss'],
               'CatBoost', 'learning_curve_catboost.png')


if __name__ == '__main__':
    main()
