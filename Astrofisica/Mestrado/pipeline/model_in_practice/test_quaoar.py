#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste do modelo CatBoost em curvas peculiares de Quaoar/Chiron.

As curvas em ./quaoar/ nao estao na base de treino — elas apresentam
uma ocultacao principal profunda e dips menores (possiveis aneis/jatos).
Objetivo: verificar se o modelo captura a ocultacao principal.

Script escrito em estilo linear top-down, para facilitar debug por
breakpoints no VS Code (clique na margem esquerda de cada linha).
"""

# =============================================================================
# 0) IMPORTS
# =============================================================================
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib
from catboost import CatBoostClassifier


# =============================================================================
# 1) CAMINHOS (edite aqui se precisar apontar para outro modelo)
# =============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

QUAOAR_DIR = os.path.join(SCRIPT_DIR, 'quaoar')

# Diretorio do treinamento que contem imputer, scaler, feature_names e o modelo
MODEL_DIR = os.path.join(
    SCRIPT_DIR, '..', 'model_training', 'outputs',
    'resultado5_split0.8-0.2_less_features_noMin-noKmeans'
)

# Nomes dos tres arquivos de curva
CURVE_FILES = [
    'CFHT_Wircam_Ks_cor-time.dat',
    'Gemini-Alopeke_Blue-r.dat',
    'Gemini-Alopeke_Red-z.dat',
]

# Indices das colunas (0-indexed) no arquivo .dat do PRAIA.
# Layout: col 0 = num linha, col 1 = flag, col 2 = exptime, col 3 = JD,
# col 4 = segundos UTC do dia, ..., col 9 = fluxo normalizado.
TIME_COL = 4   # tempo em segundos UTC do dia
FLUX_COL = 9   # fluxo normalizado (valores proximos a 1.0)


# =============================================================================
# 2) IMPORTA O PIPELINE DE FEATURES DO MODEL_TRAINING
# =============================================================================
# Adiciona model_training ao path para reusar extract_features e compute_occ_features
MODEL_TRAINING_DIR = os.path.join(SCRIPT_DIR, '..', 'model_training')
sys.path.insert(0, MODEL_TRAINING_DIR)

from build_dataset import extract_features
from occ_features import compute_occ_features, OCC_FEATURE_NAMES


# =============================================================================
# 3) FUNCAO SIMPLES PARA LER UMA CURVA .DAT
# =============================================================================
def read_curve(filepath, time_col=TIME_COL, flux_col=FLUX_COL,
               flux_min=-2.0, flux_max=5.0):
    """Le um arquivo .dat do PRAIA e devolve (time_array, flux_array).

    Remove linhas NaN e pontos com fluxo fora de [flux_min, flux_max]
    (valores como 99.999 sao flags de qualidade ruim do PRAIA, NAO sinal).
    O intervalo e largo o suficiente para preservar ocultacoes profundas
    (fluxo ~ 0) sem descartar o dip real.
    """
    data = np.genfromtxt(filepath, usecols=[time_col, flux_col], dtype=float)

    # 1) Remove NaN
    valid = np.isfinite(data).all(axis=1)
    data = data[valid]

    time_arr = data[:, 0]
    flux_arr = data[:, 1]

    # 2) Remove valores fisicamente impossiveis / flags
    keep = (flux_arr >= flux_min) & (flux_arr <= flux_max)
    time_arr = time_arr[keep]
    flux_arr = flux_arr[keep]

    return time_arr, flux_arr


# =============================================================================
# 4) LER AS TRES CURVAS DE QUAOAR
# =============================================================================
print("=" * 70)
print("  TESTE DO MODELO EM CURVAS PECULIARES DE QUAOAR")
print("=" * 70)

print("\n[1] Lendo curvas de luz...")

curves = {}  # dicionario: {nome_curva: (time, flux)}

for filename in CURVE_FILES:
    filepath = os.path.join(QUAOAR_DIR, filename)
    curve_name = os.path.splitext(filename)[0]

    time_arr, flux_arr = read_curve(filepath)
    curves[curve_name] = (time_arr, flux_arr)

    print(f"  - {curve_name}: {len(time_arr)} pontos")


# =============================================================================
# 5) PLOTAR AS CURVAS PARA INSPECAO VISUAL
# =============================================================================
print("\n[2] Plotando curvas...")

fig, axes = plt.subplots(len(curves), 1, figsize=(12, 9), sharex=False)

for ax, (curve_name, (time_arr, flux_arr)) in zip(axes, curves.items()):
    ax.plot(time_arr, flux_arr, '.', markersize=1.5, color='tab:blue')
    ax.axhline(1.0, color='gray', linestyle='--', alpha=0.5, label='baseline (1.0)')
    ax.set_title(curve_name)
    ax.set_xlabel('Tempo (s UTC)')
    ax.set_ylabel('Fluxo normalizado')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right', fontsize=8)

plt.tight_layout()

# Salva a figura e exibe na tela
plot_path = os.path.join(SCRIPT_DIR, 'quaoar_curves.png')
fig.savefig(plot_path, dpi=150, bbox_inches='tight')
print(f"  -> Figura salva em: {plot_path}")
plt.show()


# =============================================================================
# 6) CARREGAR O MODELO CATBOOST E OS ARTEFATOS DE PRE-PROCESSAMENTO
# =============================================================================
print("\n[3] Carregando modelo CatBoost e artefatos...")

# 6.1) CatBoost
catboost_path = os.path.join(MODEL_DIR, 'catboost_model.cbm')
model = CatBoostClassifier()
model.load_model(catboost_path)
print(f"  -> Modelo: {catboost_path}")

# 6.2) Imputer — preenche NaN com a mediana aprendida no treino.
# Se o pickle for incompativel com a versao atual do scikit-learn,
# usamos a mediana das features extraidas como fallback.
imputer_path = os.path.join(MODEL_DIR, 'imputer_model.pkl')
try:
    imputer = joblib.load(imputer_path)
    print(f"  -> Imputer: {imputer_path}")
except Exception as e:
    imputer = None
    print(f"  [AVISO] Imputer salvo incompativel ({type(e).__name__}).")
    print(f"          Fallback: mediana das features locais.")

# 6.3) Feature names — ordem exata das colunas esperadas pelo modelo
feature_names_path = os.path.join(MODEL_DIR, 'feature_names.pkl')
feature_names = joblib.load(feature_names_path)
print(f"  -> {len(feature_names)} features esperadas")


# =============================================================================
# 7) EXTRAIR FEATURES DE CADA CURVA (mesma pipeline do treinamento)
# =============================================================================
print("\n[4] Extraindo features...")

features_list = []

for curve_name, (time_arr, flux_arr) in curves.items():
    # Monta o dict no formato que o pipeline espera
    curve_dict = {
        'time': time_arr.tolist(),
        'flux': flux_arr.tolist(),
        'flux_normalized': flux_arr.tolist(),
    }

    # Features estatisticas (Amp, Savgol, Drawdown, quartis, etc.)
    feats = extract_features(curve_dict, curve_name, use_filter='savgol')

    # Features observacionais (depth, SNR_dip, duration, chi2, ...)
    occ_feats = compute_occ_features(curve_dict)
    if occ_feats is not None:
        feats.update(occ_feats)
    else:
        for col in OCC_FEATURE_NAMES:
            feats[col] = np.nan

    features_list.append(feats)
    print(f"  - {curve_name}: {len(feats) - 1} features")


# =============================================================================
# 8) MONTAR A MATRIZ X NA ORDEM ESPERADA PELO MODELO
# =============================================================================
print("\n[5] Preparando matriz de entrada...")

df = pd.DataFrame(features_list)

# Adiciona colunas ausentes (features excluidas no treino) como NaN
for col in feature_names:
    if col not in df.columns:
        df[col] = np.nan

# Seleciona e reordena exatamente como o treino
X = df[feature_names].copy()

# Imputa NaN. Usa imputer do treino quando disponivel; senao mediana local.
if imputer is not None:
    X_imputed = pd.DataFrame(
        imputer.transform(X),
        columns=X.columns,
        index=X.index,
    )
else:
    X_imputed = X.fillna(X.median()).fillna(0)

print(f"  -> X shape: {X_imputed.shape}")


# =============================================================================
# 9) PREDICAO
# =============================================================================
print("\n[6] Rodando predicao...")

y_pred = model.predict(X_imputed).flatten()
y_proba = model.predict_proba(X_imputed)[:, 1]


# =============================================================================
# 10) EXIBIR RESULTADOS
# =============================================================================
print("\n" + "=" * 70)
print("  RESULTADO — DETECCAO DE OCULTACAO (CatBoost)")
print("=" * 70)

curve_names = list(curves.keys())
for i, curve_name in enumerate(curve_names):
    pred = int(y_pred[i])
    proba = float(y_proba[i])
    label = 'OCULTACAO DETECTADA' if pred == 1 else 'SEM EVENTO'
    marker = '***' if pred == 1 else '   '
    print(f"  {marker} {curve_name:40s}  ->  {label:25s}  (P={proba:.4f})")

# Tambem mostra algumas metricas observacionais para contexto
print("\n" + "-" * 70)
print("  Features observacionais principais:")
print("-" * 70)
for i, curve_name in enumerate(curve_names):
    feats = features_list[i]
    depth = feats.get('Occ_depth', np.nan)
    snr = feats.get('Occ_SNR_dip', np.nan)
    dur = feats.get('Occ_duration_s', np.nan)
    print(f"  {curve_name}")
    print(f"      depth={depth:.4f}   SNR_dip={snr:.2f}   duration={dur:.2f}s")

print("\n" + "=" * 70)
print("  FIM")
print("=" * 70)
