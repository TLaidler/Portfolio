#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de Inferência — Detecção de Ocultações Estelares

Carrega os modelos treinados pela pipeline e aplica a curvas de luz
observacionais (ex.: dados do Quaoar), gerando predições de ocultação.

Uso:
    python run_models.py quaoar/
    python run_models.py quaoar/ --time_col 3 --flux_col 9
    python run_models.py quaoar/ --excluded_features IOTA_chi2_constant IOTA_chi2_square_well

Autor: Pipeline de mestrado em Astrofísica
"""

import argparse
import glob
import os
import sys
import warnings

import joblib
import numpy as np
import pandas as pd

# Adiciona model_training ao path para importar extract_features e iota_features
_MODEL_TRAINING_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'model_training')
sys.path.insert(0, _MODEL_TRAINING_DIR)

from build_dataset import extract_features
from iota_features import compute_iota_features, IOTA_FEATURE_NAMES

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Diretório padrão dos modelos treinados
DEFAULT_MODEL_DIR = os.path.join(_MODEL_TRAINING_DIR, 'outputs')


# =============================================================================
# PARSING DE ARGUMENTOS
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='Aplica modelos treinados de detecção de ocultações estelares a curvas de luz.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python run_models.py quaoar/
  python run_models.py quaoar/ --time_col 3 --flux_col 9
  python run_models.py quaoar/ --excluded_features IOTA_chi2_constant
  python run_models.py quaoar/CFHT_Wircam_Ks_cor-time.dat --output resultados.csv
        """
    )
    parser.add_argument(
        'input_path',
        help='Diretório com arquivos .dat ou caminho para um único arquivo .dat'
    )
    parser.add_argument(
        '--model_dir',
        default=DEFAULT_MODEL_DIR,
        help=f'Diretório com modelos treinados (default: {DEFAULT_MODEL_DIR})'
    )
    parser.add_argument(
        '--time_col', type=int, default=3,
        help='Índice da coluna de tempo em segundos nos arquivos .dat (0-indexed, default: 3)'
    )
    parser.add_argument(
        '--flux_col', type=int, default=9,
        help='Índice da coluna de fluxo normalizado nos arquivos .dat (0-indexed, default: 9)'
    )
    parser.add_argument(
        '--excluded_features', nargs='*', default=[],
        help='Features a excluir da predição (serão preenchidas com a mediana do treino)'
    )
    parser.add_argument(
        '--output', default='predictions.csv',
        help='Caminho do arquivo CSV de saída (default: predictions.csv)'
    )
    parser.add_argument(
        '--use_filter', default='savgol', choices=['savgol', 'mv_avg', None],
        help='Filtro para extração de features (default: savgol, deve coincidir com o treinamento)'
    )
    return parser.parse_args()


# =============================================================================
# CARREGAMENTO DE DADOS
# =============================================================================

def load_light_curve(filepath, time_col, flux_col):
    """
    Lê um arquivo .dat e retorna um dicionário de curva compatível com
    extract_features() e compute_iota_features().

    Args:
        filepath: Caminho para o arquivo .dat
        time_col: Índice da coluna de tempo (0-indexed)
        flux_col: Índice da coluna de fluxo normalizado (0-indexed)

    Returns:
        dict com chaves 'time', 'flux', 'flux_normalized'
    """
    try:
        data = np.genfromtxt(filepath, usecols=[time_col, flux_col], dtype=float)
    except (ValueError, IndexError) as e:
        print(f"  [ERRO] Falha ao ler {filepath}: {e}")
        return None

    # Remove linhas com NaN
    valid_mask = np.isfinite(data).all(axis=1)
    data = data[valid_mask]

    if len(data) < 5:
        print(f"  [AVISO] Arquivo {filepath} tem menos de 5 pontos válidos, pulando.")
        return None

    time_arr = data[:, 0]
    flux_arr = data[:, 1]

    return {
        'time': time_arr.tolist(),
        'flux': flux_arr.tolist(),
        'flux_normalized': flux_arr.tolist(),
    }


def find_dat_files(input_path):
    """Retorna lista de caminhos .dat a partir de um diretório ou arquivo único."""
    if os.path.isfile(input_path):
        return [input_path]
    elif os.path.isdir(input_path):
        files = sorted(glob.glob(os.path.join(input_path, '*.dat')))
        if not files:
            print(f"  [AVISO] Nenhum arquivo .dat encontrado em {input_path}")
        return files
    else:
        print(f"  [ERRO] Caminho não encontrado: {input_path}")
        return []


# =============================================================================
# CARREGAMENTO DE MODELOS
# =============================================================================

def load_models(model_dir):
    """
    Carrega todos os modelos treinados, imputer, scaler e feature_names.

    Args:
        model_dir: Diretório contendo os artefatos do treinamento

    Returns:
        tuple: (models_dict, imputer, scaler, feature_names)
    """
    models = {}

    # Random Forest
    rf_path = os.path.join(model_dir, 'random_forest_model.pkl')
    if os.path.exists(rf_path):
        models['Random Forest'] = joblib.load(rf_path)
        print(f"  -> Random Forest carregado: {rf_path}")

    # XGBoost
    xgb_path = os.path.join(model_dir, 'xgboost_model.pkl')
    if os.path.exists(xgb_path):
        models['XGBoost'] = joblib.load(xgb_path)
        print(f"  -> XGBoost carregado: {xgb_path}")

    # CatBoost
    cb_path = os.path.join(model_dir, 'catboost_model.cbm')
    if os.path.exists(cb_path):
        from catboost import CatBoostClassifier
        cb = CatBoostClassifier()
        cb.load_model(cb_path)
        models['CatBoost'] = cb
        print(f"  -> CatBoost carregado: {cb_path}")

    # Logistic Regression
    lr_path = os.path.join(model_dir, 'logistic_regression_model.pkl')
    if os.path.exists(lr_path):
        models['Logistic Regression'] = joblib.load(lr_path)
        print(f"  -> Logistic Regression carregado: {lr_path}")

    if not models:
        raise FileNotFoundError(f"Nenhum modelo encontrado em {model_dir}")

    # Imputer
    imputer_path = os.path.join(model_dir, 'imputer_model.pkl')
    imputer = joblib.load(imputer_path) if os.path.exists(imputer_path) else None

    # Scaler (para Logistic Regression)
    scaler_path = os.path.join(model_dir, 'scaler_model.pkl')
    scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None

    # Feature names (ordem das colunas no treinamento)
    fn_path = os.path.join(model_dir, 'feature_names.pkl')
    feature_names = joblib.load(fn_path) if os.path.exists(fn_path) else None

    return models, imputer, scaler, feature_names


# =============================================================================
# EXTRAÇÃO DE FEATURES
# =============================================================================

def extract_all_features(curve, curve_name, use_filter='savgol'):
    """
    Extrai features estatísticas + IOTA de uma curva de luz.

    Args:
        curve: dict com 'time', 'flux', 'flux_normalized'
        curve_name: Identificador da curva
        use_filter: 'savgol', 'mv_avg' ou None

    Returns:
        dict com todas as features, ou None se a curva for inválida
    """
    feats = extract_features(curve, curve_name, use_filter=use_filter)
    if feats is None:
        return None

    iota_feats = compute_iota_features(curve)
    if iota_feats is not None:
        feats.update(iota_feats)
    else:
        for col in IOTA_FEATURE_NAMES:
            feats[col] = np.nan

    return feats


# =============================================================================
# PREDIÇÃO
# =============================================================================

def predict_curves(models, imputer, scaler, feature_names, features_list, excluded_features):
    """
    Gera predições para todas as curvas usando todos os modelos.

    Args:
        models: dict de modelos treinados
        imputer: SimpleImputer do treinamento
        scaler: StandardScaler do treinamento (para Logistic Regression)
        feature_names: lista ordenada de nomes de features do treinamento
        features_list: lista de dicts (saída de extract_all_features)
        excluded_features: lista de features a neutralizar

    Returns:
        pd.DataFrame com predições e probabilidades por modelo
    """
    # Monta DataFrame com features na ordem do treinamento
    df = pd.DataFrame(features_list)
    curve_names = df['curve_name'].values

    # Seleciona apenas as features usadas no treinamento, na ordem correta
    if feature_names is not None:
        # Adiciona colunas ausentes com NaN
        for col in feature_names:
            if col not in df.columns:
                df[col] = np.nan
        X = df[feature_names].copy()
    else:
        # Fallback: usa todas as colunas exceto metadados
        meta = ['curve_name', 'source', 'occ']
        X = df.drop(columns=[c for c in meta if c in df.columns]).copy()

    # Neutraliza features excluídas (preenche com mediana do treino)
    if excluded_features and imputer is not None:
        for feat in excluded_features:
            if feat in X.columns:
                col_idx = list(X.columns).index(feat)
                if col_idx < len(imputer.statistics_):
                    median_val = imputer.statistics_[col_idx]
                    X[feat] = median_val
                    print(f"  -> Feature '{feat}' neutralizada (preenchida com mediana={median_val:.4f})")
                else:
                    print(f"  [AVISO] Feature '{feat}' não encontrada no imputer, ignorando.")
            else:
                print(f"  [AVISO] Feature '{feat}' não existe no conjunto de features, ignorando.")

    # Imputa NaN restantes
    if imputer is not None:
        X_imputed = pd.DataFrame(
            imputer.transform(X),
            columns=X.columns,
            index=X.index
        )
    else:
        X_imputed = X.fillna(0)

    # Gera predições para cada modelo
    results = pd.DataFrame({'curve_name': curve_names})

    for model_name, model in models.items():
        if model_name == 'Logistic Regression' and scaler is not None:
            X_input = scaler.transform(X_imputed)
        else:
            X_input = X_imputed

        y_pred = model.predict(X_input)
        y_proba = model.predict_proba(X_input)[:, 1]

        results[f'{model_name}_pred'] = y_pred
        results[f'{model_name}_proba'] = np.round(y_proba, 4)

    return results


# =============================================================================
# EXIBIÇÃO DE RESULTADOS
# =============================================================================

def print_results(results, models):
    """Exibe resultados de forma formatada no terminal."""
    print("\n" + "=" * 70)
    print("  RESULTADOS DA PREDIÇÃO")
    print("=" * 70)

    for _, row in results.iterrows():
        print(f"\n  Curva: {row['curve_name']}")
        print(f"  {'─' * 50}")

        for model_name in models.keys():
            pred = int(row[f'{model_name}_pred'])
            proba = row[f'{model_name}_proba']
            label = 'OCULTAÇÃO' if pred == 1 else 'Sem evento'
            marker = '***' if pred == 1 else '   '

            print(f"  {marker} {model_name:25s}  →  {label:15s}  (P={proba:.4f})")


# =============================================================================
# MAIN
# =============================================================================

def main():
    args = parse_args()

    print("\n" + "=" * 70)
    print("  PIPELINE DE INFERÊNCIA — DETECÇÃO DE OCULTAÇÕES ESTELARES")
    print("=" * 70)

    # --- 1. Carrega modelos ---
    print("\n[1/4] Carregando modelos treinados...")
    models, imputer, scaler, feature_names = load_models(args.model_dir)
    print(f"  -> {len(models)} modelo(s) carregado(s)")
    if feature_names:
        print(f"  -> {len(feature_names)} features esperadas pelo modelo")

    # --- 2. Descobre e lê arquivos ---
    print(f"\n[2/4] Lendo curvas de luz de: {args.input_path}")
    dat_files = find_dat_files(args.input_path)
    print(f"  -> {len(dat_files)} arquivo(s) .dat encontrado(s)")

    features_list = []
    for filepath in dat_files:
        filename = os.path.basename(filepath)
        curve_name = os.path.splitext(filename)[0]
        print(f"\n  Processando: {filename}")

        curve = load_light_curve(filepath, args.time_col, args.flux_col)
        if curve is None:
            continue

        print(f"    -> {len(curve['time'])} pontos lidos")

        feats = extract_all_features(curve, curve_name, use_filter=args.use_filter)
        if feats is None:
            print(f"    -> [AVISO] Extração de features falhou, pulando.")
            continue

        features_list.append(feats)
        print(f"    -> {len(feats) - 1} features extraídas")  # -1 para curve_name

    if not features_list:
        print("\n  [ERRO] Nenhuma curva processada com sucesso. Verifique os dados de entrada.")
        sys.exit(1)

    # --- 3. Gera predições ---
    print(f"\n[3/4] Gerando predições...")
    if args.excluded_features:
        print(f"  Features excluídas: {args.excluded_features}")

    results = predict_curves(
        models, imputer, scaler, feature_names,
        features_list, args.excluded_features
    )

    # --- 4. Salva e exibe resultados ---
    print(f"\n[4/4] Salvando resultados...")
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
    results.to_csv(output_path, index=False)
    print(f"  -> Resultados salvos em: {output_path}")

    print_results(results, models)

    print("\n" + "=" * 70)
    print("  INFERÊNCIA CONCLUÍDA COM SUCESSO!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
