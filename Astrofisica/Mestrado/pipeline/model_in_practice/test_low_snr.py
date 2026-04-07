#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Teste de Desempenho em Curvas de Baixo SNR

Carrega TODAS as curvas do banco de dados, extrai features, filtra por
Occ_SNR_dip < threshold e avalia os modelos treinados apenas nessas curvas
difíceis. O objetivo é medir o desempenho real da pipeline em condições
onde a triagem automática é de fato necessária.

Uso:
    python test_low_snr.py
    python test_low_snr.py --snr_threshold 5.0
    python test_low_snr.py --snr_threshold 2.0 --output low_snr_results.csv

Autor: Pipeline de mestrado em Astrofísica
"""

import argparse
import os
import sys
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

# Adiciona model_training ao path (mesmo padrão do run_models.py)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_MODEL_TRAINING_DIR = os.path.join(_SCRIPT_DIR, '..', 'model_training')
sys.path.insert(0, _MODEL_TRAINING_DIR)

from build_dataset import extract_features
from occ_features import compute_occ_features, OCC_FEATURE_NAMES
import astro_data_access as ada

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Diretório padrão dos modelos treinados (resultado5 — 11 features, sem Min, sem Kmeans)
DEFAULT_MODEL_DIR = os.path.join(
    _MODEL_TRAINING_DIR, 'outputs',
    'resultado5_split0.8-0.2_less_features_noMin-noKmeans'
)

# Features excluídas — mesma lista do train_model.py
EXCLUDED_FEATURES = [
    'Feature_Amp',
    'Feature_Flux_std',
    'Feature_Savgol_Min',
    'kmeans_centroid_dist',
    'Feature_Savgol_Max',
    'Occ_flux_min',
    'Occ_flux_min_over_baseline',
    'Occ_n_frames_below_baseline',
    'Deriv_Min', 'Deriv_Max', 'Deriv_Mean', 'Deriv_Std',
    'Deriv_Skew', 'Deriv_Kurtosis',
    'SecondDeriv_Min', 'SecondDeriv_Max', 'SecondDeriv_Std',
]

METADATA_COLS = ['curve_name', 'source', 'occ']


# =============================================================================
# ARGUMENTOS
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='Testa modelos treinados em curvas de baixo SNR do banco de dados.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--snr_threshold', type=float, default=3.0,
        help='Limiar de Occ_SNR_dip para filtrar curvas difíceis (default: 3.0)'
    )
    parser.add_argument(
        '--model_dir', default=DEFAULT_MODEL_DIR,
        help=f'Diretório com modelos treinados (default: resultado5)'
    )
    parser.add_argument(
        '--output', default='low_snr_predictions.csv',
        help='Caminho do CSV de saída (default: low_snr_predictions.csv)'
    )
    parser.add_argument(
        '--use_filter', default='savgol', choices=['savgol', 'mv_avg'],
        help='Filtro para extração de features (default: savgol)'
    )
    return parser.parse_args()


# =============================================================================
# CARREGAMENTO DE MODELOS (reutiliza padrão do run_models.py)
# =============================================================================

def load_models(model_dir):
    """Carrega modelos, imputer, scaler e feature_names."""
    models = {}

    rf_path = os.path.join(model_dir, 'random_forest_model.pkl')
    if os.path.exists(rf_path):
        models['Random Forest'] = joblib.load(rf_path)

    xgb_path = os.path.join(model_dir, 'xgboost_model.pkl')
    if os.path.exists(xgb_path):
        models['XGBoost'] = joblib.load(xgb_path)

    cb_path = os.path.join(model_dir, 'catboost_model.cbm')
    if os.path.exists(cb_path):
        from catboost import CatBoostClassifier
        cb = CatBoostClassifier()
        cb.load_model(cb_path)
        models['CatBoost'] = cb

    lr_path = os.path.join(model_dir, 'logistic_regression_model.pkl')
    if os.path.exists(lr_path):
        models['Logistic Regression'] = joblib.load(lr_path)

    if not models:
        raise FileNotFoundError(f"Nenhum modelo encontrado em {model_dir}")

    imputer_path = os.path.join(model_dir, 'imputer_model.pkl')
    imputer = joblib.load(imputer_path) if os.path.exists(imputer_path) else None

    scaler_path = os.path.join(model_dir, 'scaler_model.pkl')
    scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None

    fn_path = os.path.join(model_dir, 'feature_names.pkl')
    feature_names = joblib.load(fn_path) if os.path.exists(fn_path) else None

    return models, imputer, scaler, feature_names


# =============================================================================
# EXTRAÇÃO DE FEATURES DE CURVAS DO BD
# =============================================================================

def extract_all_features(curve, curve_name, use_filter='savgol'):
    """Extrai features estatísticas + observacionais de uma curva."""
    feats = extract_features(curve, curve_name, use_filter=use_filter)
    if feats is None:
        return None

    occ_feats = compute_occ_features(curve)
    if occ_feats is not None:
        feats.update(occ_feats)
    else:
        for col in OCC_FEATURE_NAMES:
            feats[col] = np.nan

    return feats


def load_all_curves_from_db(use_filter='savgol'):
    """
    Carrega todas as curvas do BD, extrai features e retorna DataFrame
    com features, rótulo (occ) e Occ_SNR_dip para filtragem.
    """
    all_features = []

    for label, occ_value in [('positive', 1), ('negative', 0)]:
        curves = ada.get_light_curves_by_type(label, normalized=True)
        print(f"  -> {len(curves)} curvas {label}s carregadas do BD")

        for curve_data, obj_name, date, observer in curves:
            curve_name = f"{obj_name}_{date}_{observer}"

            feats = extract_all_features(curve_data, curve_name, use_filter=use_filter)
            if feats is None:
                continue

            feats['occ'] = occ_value
            feats['source'] = f'db_{label}'
            all_features.append(feats)

    df = pd.DataFrame(all_features)
    print(f"  -> {len(df)} curvas com features extraídas com sucesso")
    return df


# =============================================================================
# AVALIAÇÃO
# =============================================================================

def evaluate_model(model_name, y_true, y_pred, y_proba):
    """Calcula e imprime métricas de um modelo."""
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    try:
        auc = roc_auc_score(y_true, y_proba)
    except ValueError:
        auc = float('nan')

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

    print(f"\n  {'-' * 55}")
    print(f"  {model_name}")
    print(f"  {'-' * 55}")
    print(f"  Acuracia:       {acc:.4f}")
    print(f"  Precisao:       {prec:.4f}")
    print(f"  Sensibilidade:  {rec:.4f}")
    print(f"  F1-score:       {f1:.4f}")
    print(f"  AUC-ROC:        {auc:.4f}" if not np.isnan(auc) else "  AUC-ROC:        N/A (apenas 1 classe)")
    print(f"\n  Matriz de confusao:")
    print(f"                  Pred=0   Pred=1")
    print(f"    Real=0  (TN)  {cm[0, 0]:5d}    {cm[0, 1]:5d}  (FP)")
    print(f"    Real=1  (FN)  {cm[1, 0]:5d}    {cm[1, 1]:5d}  (TP)")

    return {'model': model_name, 'accuracy': acc, 'precision': prec,
            'recall': rec, 'f1': f1, 'auc_roc': auc}


# =============================================================================
# MAIN
# =============================================================================

def main():
    args = parse_args()

    print("\n" + "=" * 70)
    print("  TESTE DE DESEMPENHO EM CURVAS DE BAIXO SNR")
    print(f"  Limiar: Occ_SNR_dip < {args.snr_threshold}")
    print("=" * 70)

    # --- 1. Carrega modelos ---
    print("\n[1/5] Carregando modelos treinados...")
    models, imputer, scaler, feature_names = load_models(args.model_dir)
    print(f"  -> {len(models)} modelo(s): {', '.join(models.keys())}")

    # --- 2. Carrega todas as curvas do BD ---
    print("\n[2/5] Carregando curvas do banco de dados e extraindo features...")
    df = load_all_curves_from_db(use_filter=args.use_filter)

    if 'Occ_SNR_dip' not in df.columns:
        print("  [ERRO] Coluna Occ_SNR_dip não encontrada. Verifique occ_features.py.")
        sys.exit(1)

    # --- 3. Filtra por SNR ---
    print(f"\n[3/5] Filtrando curvas com Occ_SNR_dip < {args.snr_threshold}...")
    df_low_snr = df[df['Occ_SNR_dip'] < args.snr_threshold].copy()

    n_pos = (df_low_snr['occ'] == 1).sum()
    n_neg = (df_low_snr['occ'] == 0).sum()
    print(f"  -> {len(df_low_snr)} curvas passaram o filtro")
    print(f"     {n_pos} positivas (com ocultação)")
    print(f"     {n_neg} negativas (sem ocultação)")

    if len(df_low_snr) == 0:
        print("\n  [AVISO] Nenhuma curva com SNR abaixo do limiar. Tente aumentar --snr_threshold.")
        sys.exit(0)

    if n_pos == 0 or n_neg == 0:
        print(f"\n  [AVISO] Apenas uma classe presente. Métricas de classificação serão limitadas.")

    # Distribuição do SNR nas curvas filtradas
    snr_vals = df_low_snr['Occ_SNR_dip']
    print(f"\n  Distribuição do SNR nas curvas filtradas:")
    print(f"    min={snr_vals.min():.2f}  mediana={snr_vals.median():.2f}  max={snr_vals.max():.2f}")

    # --- 4. Prepara features e prediz ---
    print(f"\n[4/5] Preparando features e gerando predições...")
    y_true = df_low_snr['occ'].values
    curve_names = df_low_snr['curve_name'].values

    # Seleciona features na ordem do treinamento
    if feature_names is not None:
        for col in feature_names:
            if col not in df_low_snr.columns:
                df_low_snr[col] = np.nan
        X = df_low_snr[feature_names].copy()
    else:
        feature_cols = [c for c in df_low_snr.columns
                        if c not in METADATA_COLS and c not in EXCLUDED_FEATURES]
        X = df_low_snr[feature_cols].copy()

    # Imputa NaN (fallback para mediana local se o imputer salvo for incompatível)
    try:
        if imputer is not None:
            X_imputed = pd.DataFrame(imputer.transform(X), columns=X.columns, index=X.index)
        else:
            X_imputed = X.fillna(X.median())
    except AttributeError:
        print("  [AVISO] Imputer salvo incompatível com versão atual do scikit-learn.")
        print("          Usando mediana das features carregadas como fallback.")
        X_imputed = X.fillna(X.median()).fillna(0)

    # --- 5. Avalia cada modelo ---
    print(f"\n[5/5] Avaliação dos modelos (apenas curvas com SNR < {args.snr_threshold}):")

    results_rows = []
    predictions = pd.DataFrame({'curve_name': curve_names, 'occ_true': y_true,
                                'Occ_SNR_dip': df_low_snr['Occ_SNR_dip'].values})

    metrics_summary = []

    for model_name, model in models.items():
        if model_name == 'Logistic Regression' and scaler is not None:
            X_input = scaler.transform(X_imputed)
        else:
            X_input = X_imputed

        y_pred = model.predict(X_input)
        y_proba = model.predict_proba(X_input)[:, 1]

        metrics = evaluate_model(model_name, y_true, y_pred, y_proba)
        metrics_summary.append(metrics)

        predictions[f'{model_name}_pred'] = y_pred
        predictions[f'{model_name}_proba'] = np.round(y_proba, 4)

    # --- Salva resultados ---
    output_path = os.path.join(_SCRIPT_DIR, args.output)
    predictions.to_csv(output_path, index=False)
    print(f"\n  Predições salvas em: {output_path}")

    # --- Tabela resumo ---
    print("\n" + "=" * 70)
    print("  RESUMO COMPARATIVO")
    print("=" * 70)
    metrics_df = pd.DataFrame(metrics_summary)
    print(f"\n  Curvas testadas: {len(df_low_snr)} (SNR < {args.snr_threshold})")
    print(f"  Positivas: {n_pos}  |  Negativas: {n_neg}\n")
    print(metrics_df.to_string(index=False, float_format='{:.4f}'.format))

    print("\n" + "=" * 70)
    print("  TESTE CONCLUÍDO")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
