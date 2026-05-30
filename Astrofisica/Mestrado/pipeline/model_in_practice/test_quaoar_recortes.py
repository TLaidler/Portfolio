#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste do CatBoost em RECORTES da curva CFHT_Wircam_Ks (Quaoar).

Cada recorte e uma janela temporal distinta da curva (sem ocultacao,
aneis Q1R/Q2R, ruido parecido com ocultacao, etc.). O script:
  1. Carrega a curva inteira.
  2. Aplica o modelo a cada recorte isoladamente (corta -> features -> predicao).
  3. Plota a curva completa destacando cada janela na sua cor, com legenda
     anotando o resultado da predicao (rotulo + probabilidade).

Estilo linear top-down: cada secao numerada e um bom lugar para colocar
um breakpoint no VS Code.
"""

# =============================================================================
# 0) IMPORTS
# =============================================================================
import os
import sys
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import joblib
from catboost import CatBoostClassifier


# =============================================================================
# 1) CAMINHOS
# =============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
QUAOAR_DIR = os.path.join(SCRIPT_DIR, 'quaoar')

MODEL_DIR = os.path.join(
    SCRIPT_DIR, '..', 'model_training', 'outputs',
    'resultado5_split0.8-0.2_less_features_noMin-noKmeans'
)

CURVE_FILE = 'Gemini-Alopeke_Red-z.dat'

TIME_COL = 4   # segundos UTC do dia
FLUX_COL = 9   # fluxo normalizado

# Epoca de referencia da ocultacao (UTC). O plot mostrara o tempo em
# segundos relativos a este instante (negativo = antes, positivo = depois).
EVENT_REFERENCE = '2022-08-09 06:34:49.26'


# =============================================================================
# 2) DEFINICAO DOS RECORTES
# =============================================================================
# Cada recorte: (t_inicio, t_fim) em segundos UTC, descricao, e cor para o plot.
# A ordem do dict define a ordem de iteracao e da legenda.
RECORTES = {
    'zero':   {'window': (23200, 23350),
               'desc':   'sem ocultacao (esperado NEGATIVO)',
               'color':  'tab:gray'},
    'um':     {'window': (23400, 23550),
               'desc':   'Q1R - continuous part',
               'color':  'tab:orange'},
    'dois':   {'window': (23560, 23575),
               'desc':   'Q2R_1 - ocultacao real',
               'color':  'tab:green'},
    'tres':   {'window': (23580, 23590),
               'desc':   'Q2R_1 - ruido parecido com occ',
               'color':  'tab:red'},
    'quatro': {'window': (23810, 23835),
               'desc':   'Q2R_2 - pos grande ocultacao',
               'color':  'tab:purple'},
    'cinco':  {'window': (23880, 23940),
               'desc':   'Q1R - dense part (forte e rapida)',
               'color':  'tab:brown'},
}


# =============================================================================
# 3) IMPORTA O PIPELINE DE FEATURES
# =============================================================================
MODEL_TRAINING_DIR = os.path.join(SCRIPT_DIR, '..', 'model_training')
sys.path.insert(0, MODEL_TRAINING_DIR)

from build_dataset import extract_features
from occ_features import compute_occ_features, OCC_FEATURE_NAMES


# =============================================================================
# 4) FUNCOES AUXILIARES (mesma logica do test_quaoar.py)
# =============================================================================
def read_curve(filepath, time_col=TIME_COL, flux_col=FLUX_COL,
               flux_min=-2.0, flux_max=5.0):
    """Le um .dat do PRAIA e devolve (time_array, flux_array) limpos."""
    data = np.genfromtxt(filepath, usecols=[time_col, flux_col], dtype=float)
    data = data[np.isfinite(data).all(axis=1)]
    time_arr = data[:, 0]
    flux_arr = data[:, 1]
    keep = (flux_arr >= flux_min) & (flux_arr <= flux_max)
    return time_arr[keep], flux_arr[keep]


def cut_curve(time_arr, flux_arr, t_start, t_end):
    """Mantem apenas os pontos com t_start <= tempo <= t_end."""
    mask = (time_arr >= t_start) & (time_arr <= t_end)
    return time_arr[mask], flux_arr[mask]


def seconds_of_day(reference):
    """Devolve quantos segundos UTC do dia correspondem a uma string
    'YYYY-MM-DD HH:MM:SS[.ff]' (UTC).

    Equivalente em escalar a calcular o offset que `time_to_relative()` do
    test_quaoar.py aplica a uma coluna de DataFrame.
    """
    ref_dt = datetime.strptime(reference, '%Y-%m-%d %H:%M:%S.%f')
    return (
        ref_dt.hour * 3600
        + ref_dt.minute * 60
        + ref_dt.second
        + ref_dt.microsecond / 1e6
    )


def time_to_relative_array(time_arr, reference=EVENT_REFERENCE):
    """Converte um array de tempos (segundos UTC do dia) para segundos
    relativos a uma data/hora UTC de referencia. Versao em array da
    funcao `time_to_relative(df, ...)` definida no test_quaoar.py.
    """
    return np.asarray(time_arr) - seconds_of_day(reference)


def features_from_window(time_arr, flux_arr, name):
    """Extrai features estatisticas + observacionais de uma janela."""
    curve_dict = {
        'time': time_arr.tolist(),
        'flux': flux_arr.tolist(),
        'flux_normalized': flux_arr.tolist(),
    }
    feats = extract_features(curve_dict, name, use_filter='savgol')
    if feats is None:
        return None
    occ_feats = compute_occ_features(curve_dict)
    if occ_feats is not None:
        feats.update(occ_feats)
    else:
        for col in OCC_FEATURE_NAMES:
            feats[col] = np.nan
    return feats


def predict_one(feats, model, imputer, feature_names):
    """Roda o CatBoost em um unico dict de features. Devolve (pred, proba)."""
    df_one = pd.DataFrame([feats])
    for col in feature_names:
        if col not in df_one.columns:
            df_one[col] = np.nan
    X = df_one[feature_names].copy()
    if imputer is not None:
        X = pd.DataFrame(imputer.transform(X), columns=X.columns)
    else:
        X = X.fillna(X.median()).fillna(0)
    pred = int(model.predict(X).flatten()[0])
    proba = float(model.predict_proba(X)[0, 1])
    return pred, proba


# =============================================================================
# 5) CARREGA A CURVA INTEIRA
# =============================================================================
print("=" * 70)
print("  TESTE DO MODELO EM RECORTES DA CURVA CFHT_Wircam_Ks (Quaoar)")
print("=" * 70)

filepath = os.path.join(QUAOAR_DIR, CURVE_FILE)
time_full, flux_full = read_curve(filepath)
print(f"\n[1] Curva completa: {len(time_full)} pontos validos")
print(f"    intervalo: {time_full.min():.1f} .. {time_full.max():.1f} s UTC")


# =============================================================================
# 6) CARREGA O MODELO E ARTEFATOS
# =============================================================================
print("\n[2] Carregando CatBoost + artefatos...")

model = CatBoostClassifier()
model.load_model(os.path.join(MODEL_DIR, 'catboost_model.cbm'))

try:
    imputer = joblib.load(os.path.join(MODEL_DIR, 'imputer_model.pkl'))
    print("  -> Imputer carregado")
except Exception as e:
    imputer = None
    print(f"  [AVISO] Imputer incompativel ({type(e).__name__}). "
          "Fallback: mediana local.")

feature_names = joblib.load(os.path.join(MODEL_DIR, 'feature_names.pkl'))
print(f"  -> {len(feature_names)} features esperadas")


# =============================================================================
# 7) APLICA O MODELO A CADA RECORTE
# =============================================================================
print("\n[3] Processando cada recorte...")

resultados = {}  # {name: {window, desc, color, n_pts, pred, proba}}

for name, cfg in RECORTES.items():
    t_ini, t_fim = cfg['window']
    t_cut, f_cut = cut_curve(time_full, flux_full, t_ini, t_fim)

    print(f"\n  Recorte '{name}'  janela=({t_ini}, {t_fim})  pts={len(t_cut)}")
    print(f"     {cfg['desc']}")

    res = dict(cfg)
    res['n_pts'] = len(t_cut)

    if len(t_cut) < 5:
        print(f"     [AVISO] janela vazia ou com <5 pontos. Pulando predicao.")
        print(f"             (curva valida: {time_full.min():.1f} .. "
              f"{time_full.max():.1f} s UTC)")
        res['pred'] = None
        res['proba'] = None
        resultados[name] = res
        continue

    feats = features_from_window(t_cut, f_cut, f'CFHT_recorte_{name}')
    if feats is None:
        print("     [AVISO] extracao de features falhou. Pulando predicao.")
        res['pred'] = None
        res['proba'] = None
        resultados[name] = res
        continue

    pred, proba = predict_one(feats, model, imputer, feature_names)
    label = 'OCULTACAO' if pred == 1 else 'sem evento'
    print(f"     -> {label}  (P={proba:.4f})")

    res['pred'] = pred
    res['proba'] = proba
    resultados[name] = res


# =============================================================================
# 8) PLOT: CURVA INTEIRA COM RECORTES DESTACADOS
# =============================================================================
print("\n[4] Gerando figura...")

# Converte o tempo para "segundos relativos ao instante do evento" antes
# de plotar — o classificador ja terminou e nao depende de tempo absoluto.
ref_sec = seconds_of_day(EVENT_REFERENCE)
time_full_rel = time_to_relative_array(time_full)
print(f"  -> Eixo x convertido para s relativos a {EVENT_REFERENCE} UTC"
      f"  (offset = {ref_sec:.2f} s)")

fig, ax = plt.subplots(figsize=(14, 5))

# Curva inteira em cinza claro (referencia visual)
ax.plot(time_full_rel, flux_full, '.', markersize=1.0, color='lightgray', alpha=0.6)

# Cada recorte: faixa vertical colorida + pontos da janela em destaque.
# As janelas em UTC sao deslocadas pelo mesmo offset para alinhar ao eixo.
for name, res in resultados.items():
    t_ini, t_fim = res['window']
    color = res['color']

    mask = (time_full >= t_ini) & (time_full <= t_fim)
    if not mask.any():
        # janela fora da curva — nada a desenhar
        continue

    ax.axvspan(t_ini - ref_sec, t_fim - ref_sec, color=color, alpha=0.15)
    ax.plot(time_full_rel[mask], flux_full[mask], '.', markersize=2.5, color=color)

# Limita o eixo x ao intervalo dos dados (com pequena margem)
xpad = 0.02 * (time_full_rel.max() - time_full_rel.min())
ax.set_xlim(time_full_rel.min() - xpad, time_full_rel.max() + xpad)

# Baseline
ax.axhline(1.0, color='gray', linestyle='--', alpha=0.5)

# Legenda customizada: uma entrada por recorte com a predicao do modelo.
# Mostra a janela ja em segundos relativos ao evento para casar com o eixo.
legend_items = []
for name, res in resultados.items():
    if res['pred'] is None:
        verdict = 'sem dados'
    else:
        verdict = ('OCC' if res['pred'] == 1 else 'NEG') + f"  P={res['proba']:.3f}"
    t_ini_rel = res['window'][0] - ref_sec
    t_fim_rel = res['window'][1] - ref_sec
    label = (f"{name:6s} [{t_ini_rel:+.0f} .. {t_fim_rel:+.0f} s]  "
             f"{res['desc']}  ->  {verdict}")
    legend_items.append(Patch(facecolor=res['color'], alpha=0.5, label=label))

ax.legend(handles=legend_items, loc='lower left', fontsize=8,
          framealpha=0.9, title='Recortes e veredito do CatBoost')

ax.set_xlabel(f'Tempo relativo a {EVENT_REFERENCE} UTC (s)')
ax.set_ylabel('Fluxo normalizado')
ax.set_title(f'{CURVE_FILE}: recortes da curva e resultado do modelo CatBoost')
ax.grid(True, alpha=0.3)

plt.tight_layout()

out_path = os.path.join(SCRIPT_DIR, 'quaoar_recortes.png')
fig.savefig(out_path, dpi=150, bbox_inches='tight')
print(f"  -> Figura salva em: {out_path}")
plt.show()


# =============================================================================
# 9) RESUMO TABULAR
# =============================================================================
print("\n" + "=" * 70)
print("  RESUMO DOS RECORTES")
print("=" * 70)
print(f"{'Recorte':8s} {'Janela':18s} {'N':>5s} {'Veredito':12s} {'Proba':>8s}  Descricao")
print("-" * 95)
for name, res in resultados.items():
    win = f"{res['window'][0]}..{res['window'][1]}"
    if res['pred'] is None:
        veredito = '-'
        proba_str = '-'
    else:
        veredito = 'OCULTACAO' if res['pred'] == 1 else 'sem evento'
        proba_str = f"{res['proba']:.4f}"
    print(f"{name:8s} {win:18s} {res['n_pts']:>5d} {veredito:12s} {proba_str:>8s}  {res['desc']}")
print("=" * 70)
