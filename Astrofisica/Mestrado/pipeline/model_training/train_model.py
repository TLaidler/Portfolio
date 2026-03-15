#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pipeline de Treinamento de Modelos para Detecção de Ocultações Estelares

Este script implementa um pipeline completo de Machine Learning para:
1. Carregar dataset construído por build_dataset.py
2. Separar dados em treino/teste (com opção de seleção manual de curvas de teste)
3. Treinar modelos: Random Forest, XGBoost, CatBoost
4. Avaliar desempenho com métricas e gráficos
5. Persistir modelos treinados

Uso:
    python train_model.py

Autor: Pipeline gerado para mestrado em Astrofísica
"""

import os
import random
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, 
    precision_score, 
    recall_score, 
    f1_score, 
    roc_auc_score, 
    confusion_matrix, 
    roc_curve,
    classification_report
)

from xgboost import XGBClassifier
from catboost import CatBoostClassifier

# Importa módulo de construção do dataset
import build_dataset as bd

# Suprime warnings desnecessários
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Seeds para reprodutibilidade (fixados no início)
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)
random.seed(RANDOM_STATE)
SIZE_CROPPING = 250

# =============================================================================
# CONFIGURAÇÕES E HIPERPARÂMETROS
# =============================================================================

# Diretório para salvar modelos e resultados
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'outputs')

# Proporção do conjunto de teste (quando usar split automático)
TEST_SIZE = 0.2

# Colunas que NÃO são features (metadados)
METADATA_COLS = ['curve_name', 'source', 'occ']

# Coluna alvo (target)
TARGET_COL = 'occ'

# Coluna identificadora
ID_COL = 'curve_name'

# -----------------------------------------------------------------------------
# HIPERPARÂMETROS DOS MODELOS (baseline - ajustar conforme necessário)
# -----------------------------------------------------------------------------

RF_PARAMS = {
    'n_estimators': 100,
    'max_depth': 10,
    'min_samples_split': 5,
    'min_samples_leaf': 2,
    'random_state': RANDOM_STATE,
    'n_jobs': -1,
    'class_weight': 'balanced'  # Útil para datasets desbalanceados
}

XGB_PARAMS = {
    'n_estimators': 100,
    'max_depth': 6,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': RANDOM_STATE,
    'use_label_encoder': False,
    'eval_metric': 'logloss'
}

CAT_PARAMS = {
    'iterations': 100,
    'depth': 6,
    'learning_rate': 0.1,
    'random_state': RANDOM_STATE,
    'verbose': False,
    'auto_class_weights': 'Balanced'
}

LR_PARAMS = {
    'max_iter': 1000,
    'random_state': RANDOM_STATE,
    'class_weight': 'balanced',
    'n_jobs': -1
}


# =============================================================================
# FUNÇÕES DE CARREGAMENTO DE DADOS
# =============================================================================

def load_dataset(from_csv=None, skip_cropping=False, use_filter='savgol'):
    """
    Carrega o dataset para treinamento.
    
    Pode carregar de duas formas:
    1. Via build_dataset.py (gera dataset do zero)
    2. De um arquivo CSV existente
    
    Args:
        from_csv (str, optional): Caminho para CSV existente. 
                                   Se None, usa build_dataset.
        skip_cropping (bool): Se True, pula recorte interativo ao usar build_dataset.
        use_filter (str, optional): 'savgol', 'mv_avg' ou None. Usado apenas ao construir
                                    dataset do zero. Ignorado se from_csv for fornecido.
    
    Returns:
        pd.DataFrame: Dataset carregado
    """
    if from_csv and os.path.exists(from_csv):
        print(f"  Carregando dataset de: {from_csv}")
        df = pd.read_csv(from_csv).dropna() #pd.read_csv(from_csv, sep=';').dropna() 
        #removendo features - teste
        df = df.drop(columns=['Feature_Amp', 'kmeans_centroid_dist','Feature_Flux_std', 'Feature_Savgol_Max','Feature_Savgol_Min', 'Deriv_Min', 'Deriv_Max', 'Deriv_Mean', 'Deriv_Std', 'Deriv_Skew', 'Deriv_Kurtosis', 'SecondDeriv_Min', 'SecondDeriv_Max', 'SecondDeriv_Std', 'IOTA_flux_min', 'IOTA_flux_min_over_baseline'])
    else:
        # Carrega via build_dataset (pode demorar se precisar construir do zero)
        print("  Construindo dataset via build_dataset.py...")
        df = bd.build_dataset(
            sample_size_for_cropping=SIZE_CROPPING,
            skip_cropping=skip_cropping,
            use_filter=use_filter
        )
    
    return df


def prepare_features_target(df):
    """
    Separa features (X) e target (y) do DataFrame.
    
    IMPORTANTE: Esta função garante que o target NÃO é usado como feature,
    evitando data leakage. NaNs são preservados; usar apply_imputation após o split.
    
    Args:
        df (pd.DataFrame): Dataset completo
    
    Returns:
        tuple: (X, y, feature_names) onde:
            - X: DataFrame com features
            - y: Series com target
            - feature_names: Lista com nomes das features
    """
    # Identifica colunas de features (tudo que não é metadado)
    feature_cols = [col for col in df.columns if col not in METADATA_COLS]
    
    # Extrai features e target (NaNs preservados para imputação pós-split)
    X = df[feature_cols].copy()
    y = df[TARGET_COL].copy()
    
    print(f"\n  Features ({len(feature_cols)}):")
    for i, col in enumerate(feature_cols, 1):
        print(f"    {i:2d}. {col}")
    
    print(f"\n  Target: '{TARGET_COL}' (0=negativa, 1=positiva)")
    print(f"  Distribuição: {dict(y.value_counts())}")
    
    return X, y, feature_cols


def apply_imputation(X_train, X_test, strategy='median'):
    """
    Imputa valores faltantes (NaN) usando mediana do conjunto de treino.
    
    Fit é feito apenas em X_train para evitar data leakage.
    
    Args:
        X_train (pd.DataFrame): Features de treino
        X_test (pd.DataFrame): Features de teste
        strategy (str): Estratégia do SimpleImputer ('median', 'mean', etc.)
    
    Returns:
        tuple: (X_train_imputed, X_test_imputed, imputer)
    """
    imputer = SimpleImputer(strategy=strategy)
    X_train_imp = pd.DataFrame(
        imputer.fit_transform(X_train),
        columns=X_train.columns,
        index=X_train.index
    )
    X_test_imp = pd.DataFrame(
        imputer.transform(X_test),
        columns=X_test.columns,
        index=X_test.index
    )
    return X_train_imp, X_test_imp, imputer


# =============================================================================
# FUNÇÕES DE SPLIT TREINO/TESTE
# =============================================================================

def split_data(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE):
    """
    Divide dados em treino e teste usando split automático estratificado (por linha).
    
    Args:
        X (pd.DataFrame): Features
        y (pd.Series): Target
        test_size (float): Proporção do conjunto de teste (0 a 1)
        random_state (int): Seed para reprodutibilidade
    
    Returns:
        tuple: (X_train, X_test, y_train, y_test)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=test_size, 
        random_state=random_state,
        stratify=y  # Mantém proporção das classes
    )
    
    return X_train, X_test, y_train, y_test


def split_by_curve(df, test_size=TEST_SIZE, random_state=RANDOM_STATE):
    """
    Divide dados em treino e teste por curva/evento (uma curva inteira vai para
    treino ou teste, nunca ambos). Evita data leakage entre curvas.
    
    Args:
        df (pd.DataFrame): Dataset completo com colunas curve_name, occ e features
        test_size (float): Proporção de curvas para teste (0 a 1)
        random_state (int): Seed para reprodutibilidade
    
    Returns:
        tuple: (X_train, X_test, y_train, y_test, df_train, df_test)
    """
    feature_cols = [c for c in df.columns if c not in METADATA_COLS]
    curve_info = df[[ID_COL, TARGET_COL]].drop_duplicates()
    curves = curve_info[ID_COL].values
    y_curves = curve_info[TARGET_COL].values

    try:
        curves_train, curves_test, _, _ = train_test_split(
            curves, y_curves,
            test_size=test_size,
            random_state=random_state,
            stratify=y_curves
        )
    except ValueError:
        # Pode falhar se apenas 1 amostra por classe; fallback sem stratify
        curves_train, curves_test = train_test_split(
            curves, test_size=test_size, random_state=random_state
        )

    mask_test = df[ID_COL].isin(curves_test)
    df_test = df[mask_test].copy()
    df_train = df[~mask_test].copy()

    X_train = df_train[feature_cols]
    X_test = df_test[feature_cols]
    y_train = df_train[TARGET_COL]
    y_test = df_test[TARGET_COL]

    return X_train, X_test, y_train, y_test, df_train, df_test


def split_real_holdout(df, test_size=TEST_SIZE, random_state=RANDOM_STATE):
    """
    Divide dados de forma que o conjunto de teste contenha apenas curvas reais
    (db_positive, db_negative). Treino = synthetic + artificial + curvas reais
    não usadas em teste. Útil para validar generalização em dados reais.
    
    Requer coluna 'source' no DataFrame.
    
    Args:
        df (pd.DataFrame): Dataset completo
        test_size (float): Proporção de curvas reais para teste
        random_state (int): Seed para reprodutibilidade
    
    Returns:
        tuple: (X_train, X_test, y_train, y_test, df_train, df_test)
    """
    if 'source' not in df.columns:
        raise ValueError("split_real_holdout requer coluna 'source' no dataset.")

    real_sources = ['db_positive', 'db_negative']
    feature_cols = [c for c in df.columns if c not in METADATA_COLS]

    df_real = df[df['source'].isin(real_sources)]
    df_non_real = df[~df['source'].isin(real_sources)]

    curve_info = df_real[[ID_COL, TARGET_COL]].drop_duplicates()
    curves = curve_info[ID_COL].values
    y_curves = curve_info[TARGET_COL].values

    try:
        curves_train, curves_test, _, _ = train_test_split(
            curves, y_curves,
            test_size=test_size,
            random_state=random_state,
            stratify=y_curves
        )
    except ValueError:
        curves_train, curves_test = train_test_split(
            curves, test_size=test_size, random_state=random_state
        )

    df_test = df_real[df_real[ID_COL].isin(curves_test)].copy()
    df_train_real = df_real[df_real[ID_COL].isin(curves_train)].copy()
    df_train = pd.concat([df_non_real, df_train_real], ignore_index=True)

    X_train = df_train[feature_cols]
    X_test = df_test[feature_cols]
    y_train = df_train[TARGET_COL]
    y_test = df_test[TARGET_COL]

    return X_train, X_test, y_train, y_test, df_train, df_test


def split_with_manual_test(df, test_curve_names):
    """
    Divide dados forçando curvas específicas no conjunto de teste.
    
    Esta função permite ao usuário definir exatamente quais curvas
    serão usadas para teste, útil para:
    - Testar em curvas específicas de interesse
    - Validação com dados que você conhece bem
    - Reproduzir experimentos anteriores
    
    Args:
        df (pd.DataFrame): Dataset completo
        test_curve_names (list): Lista de nomes/IDs das curvas de teste
            Exemplo: ["curve_001", "Chiron_2020-01-01_Observer1", ...]
    
    Returns:
        tuple: (X_train, X_test, y_train, y_test, df_train, df_test)
            Retorna também os DataFrames originais para referência
    
    Raises:
        ValueError: Se nenhuma curva da lista for encontrada no dataset
    """
    # Verifica quais curvas existem no dataset
    existing_curves = set(df[ID_COL].values)
    requested_curves = set(test_curve_names)
    found_curves = existing_curves.intersection(requested_curves)
    not_found = requested_curves - found_curves
    
    if not found_curves:
        raise ValueError(
            f"Nenhuma das curvas especificadas foi encontrada no dataset.\n"
            f"Curvas solicitadas: {test_curve_names}\n"
            f"Curvas disponíveis: {list(existing_curves)[:10]}..."
        )
    
    if not_found:
        print(f"\n  [AVISO] Curvas não encontradas: {list(not_found)}")
    
    # Separa em teste (curvas especificadas) e treino (restante)
    mask_test = df[ID_COL].isin(found_curves)
    df_test = df[mask_test].copy()
    df_train = df[~mask_test].copy()
    
    # Prepara features e target (NaNs preservados para imputação)
    feature_cols = [col for col in df.columns if col not in METADATA_COLS]
    
    X_train = df_train[feature_cols]
    X_test = df_test[feature_cols]
    y_train = df_train[TARGET_COL]
    y_test = df_test[TARGET_COL]
    
    print(f"\n  Curvas forçadas no teste: {list(found_curves)}")
    
    return X_train, X_test, y_train, y_test, df_train, df_test


# =============================================================================
# FUNÇÕES DE TREINAMENTO
# =============================================================================

def train_random_forest(X_train, y_train, params=None):
    """
    Treina modelo Random Forest.
    
    Args:
        X_train: Features de treino
        y_train: Target de treino
        params (dict, optional): Hiperparâmetros. Se None, usa RF_PARAMS.
    
    Returns:
        RandomForestClassifier: Modelo treinado
    """
    if params is None:
        params = RF_PARAMS.copy()
    
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)
    
    return model


def train_xgboost(X_train, y_train, params=None):
    """
    Treina modelo XGBoost.
    
    Args:
        X_train: Features de treino
        y_train: Target de treino
        params (dict, optional): Hiperparâmetros. Se None, usa XGB_PARAMS.
    
    Returns:
        XGBClassifier: Modelo treinado
    """
    if params is None:
        params = XGB_PARAMS.copy()
    
    model = XGBClassifier(**params)
    model.fit(X_train, y_train)
    
    return model


def train_catboost(X_train, y_train, params=None):
    """
    Treina modelo CatBoost.
    
    Args:
        X_train: Features de treino
        y_train: Target de treino
        params (dict, optional): Hiperparâmetros. Se None, usa CAT_PARAMS.
    
    Returns:
        CatBoostClassifier: Modelo treinado
    """
    if params is None:
        params = CAT_PARAMS.copy()
    
    model = CatBoostClassifier(**params)
    model.fit(X_train, y_train)
    
    return model


def train_logistic_regression(X_train_scaled, y_train, params=None):
    """
    Treina modelo de Regressão Logística em features já escaladas.
    
    Args:
        X_train_scaled: Features de treino escaladas (StandardScaler)
        y_train: Target de treino
        params (dict, optional): Hiperparâmetros. Se None, usa LR_PARAMS.
    
    Returns:
        LogisticRegression: Modelo treinado
    """
    if params is None:
        params = LR_PARAMS.copy()
    
    model = LogisticRegression(**params)
    model.fit(X_train_scaled, y_train)
    
    return model


# =============================================================================
# FUNÇÕES DE AVALIAÇÃO
# =============================================================================

def evaluate_model(model, X_test, y_test, model_name="Modelo"):
    """
    Avalia modelo e retorna métricas.
    
    Args:
        model: Modelo treinado (deve ter métodos predict e predict_proba)
        X_test: Features de teste
        y_test: Target de teste
        model_name (str): Nome do modelo para exibição
    
    Returns:
        dict: Dicionário com todas as métricas
    """
    # Predições
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # Calcula métricas
    metrics = {
        'model': model_name,
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y_test, y_proba),
        'confusion_matrix': confusion_matrix(y_test, y_pred),
        'y_pred': y_pred,
        'y_proba': y_proba
    }
    
    return metrics


def print_metrics(metrics):
    """
    Exibe métricas de forma formatada no terminal.
    
    Args:
        metrics (dict): Dicionário com métricas (retornado por evaluate_model)
    """
    print(f"\n{'─' * 40}")
    print(f"  {metrics['model'].upper()}")
    print(f"{'─' * 40}")
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f}")
    print(f"  F1-Score:  {metrics['f1_score']:.4f}")
    print(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")
    print(f"\n  Matriz de Confusão:")
    cm = metrics['confusion_matrix']
    print(f"    TN={cm[0,0]:3d}  FP={cm[0,1]:3d}")
    print(f"    FN={cm[1,0]:3d}  TP={cm[1,1]:3d}")


# =============================================================================
# FUNÇÕES DE VISUALIZAÇÃO
# =============================================================================

def plot_roc_curves(all_metrics, y_test, save_path=None):
    """
    Plota curvas ROC de todos os modelos em um único gráfico.
    
    Args:
        all_metrics (list): Lista de dicionários de métricas
        y_test: Target de teste (para calcular curva)
        save_path (str, optional): Caminho para salvar figura
    """
    plt.figure(figsize=(8, 6))
    
    colors = ['#2ecc71', '#3498db', '#e74c3c', '#9b59b6', '#1abc9c']
    
    for metrics, color in zip(all_metrics, colors):
        fpr, tpr, _ = roc_curve(y_test, metrics['y_proba'])
        auc = metrics['roc_auc']
        label = f"{metrics['model']} (AUC = {auc:.3f})"
        plt.plot(fpr, tpr, color=color, lw=2, label=label)
    
    # Linha de referência (classificador aleatório)
    plt.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.5, label='Random (AUC = 0.500)')
    
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Taxa de Falso Positivo (FPR)', fontsize=12)
    plt.ylabel('Taxa de Verdadeiro Positivo (TPR)', fontsize=12)
    plt.title('Curvas ROC - Comparação de Modelos', fontsize=14)
    plt.legend(loc='lower right', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  -> Gráfico ROC salvo em: {save_path}")
    
    plt.show()


def plot_confusion_matrices(all_metrics, save_path=None):
    """
    Plota matrizes de confusão de todos os modelos.
    
    Args:
        all_metrics (list): Lista de dicionários de métricas
        save_path (str, optional): Caminho para salvar figura
    """
    n_models = len(all_metrics)
    fig, axes = plt.subplots(1, n_models, figsize=(5 * n_models, 4))
    
    if n_models == 1:
        axes = [axes]
    
    for ax, metrics in zip(axes, all_metrics):
        cm = metrics['confusion_matrix']
        
        sns.heatmap(
            cm, 
            annot=True, 
            fmt='d', 
            cmap='Blues',
            xticklabels=['Negativa', 'Positiva'],
            yticklabels=['Negativa', 'Positiva'],
            ax=ax,
            cbar=False
        )
        ax.set_xlabel('Predito', fontsize=11)
        ax.set_ylabel('Real', fontsize=11)
        ax.set_title(f"{metrics['model']}\n(Acc: {metrics['accuracy']:.3f})", fontsize=12)
    
    plt.suptitle('Matrizes de Confusão', fontsize=14, y=1.02)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  -> Matrizes de confusão salvas em: {save_path}")
    
    plt.show()


def plot_feature_importance(model, feature_names, model_name, top_n=15, save_path=None):
    """
    Plota importância das features para um modelo.
    
    Suporta modelos com feature_importances_ (RF, XGBoost, CatBoost) ou
    coef_ (LogisticRegression).
    
    Args:
        model: Modelo treinado
        feature_names (list): Lista com nomes das features
        model_name (str): Nome do modelo
        top_n (int): Número de features a exibir
        save_path (str, optional): Caminho para salvar figura
    """
    if hasattr(model, 'feature_importances_'):
        importance = model.feature_importances_
    elif hasattr(model, 'coef_'):
        importance = np.abs(model.coef_).flatten()
    else:
        print(f"  [AVISO] Modelo {model_name} não suporta feature importance")
        return

    indices = np.argsort(importance)[::-1][:top_n]
    
    plt.figure(figsize=(10, 6))
    plt.title(f'Feature Importance - {model_name}', fontsize=14)
    plt.barh(
        range(len(indices)), 
        importance[indices][::-1],
        color='steelblue',
        edgecolor='black'
    )
    plt.yticks(range(len(indices)), [feature_names[i] for i in indices][::-1])
    plt.xlabel('Importância', fontsize=12)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  -> Feature importance salvo em: {save_path}")
    
    plt.show()


# =============================================================================
# FUNÇÕES DE PERSISTÊNCIA
# =============================================================================

def save_model(model, model_name, output_dir=OUTPUT_DIR):
    """
    Salva modelo treinado em disco.
    
    Args:
        model: Modelo treinado
        model_name (str): Nome do modelo (usado no nome do arquivo)
        output_dir (str): Diretório de saída
    
    Returns:
        str: Caminho do arquivo salvo
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Define extensão apropriada
    if isinstance(model, CatBoostClassifier):
        filename = f"{model_name.lower().replace(' ', '_')}_model.cbm"
        filepath = os.path.join(output_dir, filename)
        model.save_model(filepath)
    else:
        filename = f"{model_name.lower().replace(' ', '_')}_model.pkl"
        filepath = os.path.join(output_dir, filename)
        joblib.dump(model, filepath)
    
    return filepath


def save_results_summary(all_metrics, output_dir=OUTPUT_DIR):
    """
    Salva resumo dos resultados em CSV.
    
    Args:
        all_metrics (list): Lista de dicionários de métricas
        output_dir (str): Diretório de saída
    
    Returns:
        str: Caminho do arquivo salvo
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Cria DataFrame com métricas
    summary = []
    for metrics in all_metrics:
        summary.append({
            'model': metrics['model'],
            'accuracy': metrics['accuracy'],
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'f1_score': metrics['f1_score'],
            'roc_auc': metrics['roc_auc']
        })
    
    df_summary = pd.DataFrame(summary)
    filepath = os.path.join(output_dir, 'training_results.csv')
    df_summary.to_csv(filepath, index=False)
    
    return filepath


def save_classification_reports(all_metrics, y_test, output_dir=OUTPUT_DIR):
    """Salva classification report de cada modelo em arquivos de texto."""
    os.makedirs(output_dir, exist_ok=True)
    for metrics in all_metrics:
        name = metrics['model'].lower().replace(' ', '_')
        report = classification_report(
            y_test,
            metrics['y_pred'],
            target_names=['Negativa', 'Positiva'],
            digits=4
        )
        path = os.path.join(output_dir, f'classification_report_{name}.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"Modelo: {metrics['model']}\n\n{report}")
        print(f"  -> Report salvo: {path}")


def save_predictions(all_metrics, df_test, y_test, output_dir=OUTPUT_DIR):
    """Salva predições (y_true, y_pred, y_proba) por modelo em CSV."""
    os.makedirs(output_dir, exist_ok=True)
    for metrics in all_metrics:
        name = metrics['model'].lower().replace(' ', '_')
        pred_df = pd.DataFrame({
            'curve_name': df_test[ID_COL].values if ID_COL in df_test.columns else range(len(y_test)),
            'y_true': y_test.values,
            'y_pred': metrics['y_pred'],
            'y_proba': metrics['y_proba']
        })
        path = os.path.join(output_dir, f'predictions_{name}.csv')
        pred_df.to_csv(path, index=False)
        print(f"  -> Predições salvas: {path}")


def save_split_info(df_train, df_test, output_dir=OUTPUT_DIR):
    """Salva lista de curvas em treino e teste para reprodutibilidade."""
    os.makedirs(output_dir, exist_ok=True)
    train_curves = df_train[ID_COL].drop_duplicates().tolist()
    test_curves = df_test[ID_COL].drop_duplicates().tolist()
    with open(os.path.join(output_dir, 'split_train_curves.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(train_curves))
    with open(os.path.join(output_dir, 'split_test_curves.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(test_curves))
    print(f"  -> Split salvo: split_train_curves.txt, split_test_curves.txt")


# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================

def run_pipeline(
    csv_path=None,
    test_curve_names=None,
    test_size=TEST_SIZE,
    skip_cropping=False,
    use_filter='savgol',
    test_on_real_only=False,
    show_plots=True,
    save_plots=True
):
    """
    Executa o pipeline completo de treinamento.
    
    Args:
        csv_path (str, optional): Caminho para CSV do dataset. 
                                   Se None, usa build_dataset.
        test_curve_names (list, optional): Lista de curvas para forçar no teste.
                                            Se None, usa split por curva ou real holdout.
        test_size (float): Proporção do teste
        skip_cropping (bool): Pular recorte interativo no build_dataset
        use_filter (str): 'savgol', 'mv_avg' ou None. Usado ao construir dataset.
        test_on_real_only (bool): Se True, teste apenas em curvas reais (db_positive/db_negative)
        show_plots (bool): Exibir gráficos
        save_plots (bool): Salvar gráficos em disco
    
    Returns:
        dict: Dicionário com modelos treinados e métricas
    """
    print("\n" + "=" * 60)
    print("  PIPELINE DE TREINAMENTO DE MODELOS")
    print("=" * 60)
    
    # -------------------------------------------------------------------------
    # ETAPA 1: Carregar Dataset
    # -------------------------------------------------------------------------
    print("\n[1/6] Carregando dataset...")
    
    df = load_dataset(
        from_csv=csv_path,
        skip_cropping=skip_cropping,
        use_filter=use_filter
    )
    print(f"\n  -> {len(df)} amostras carregadas")
    
    # -------------------------------------------------------------------------
    # ETAPA 2: Preparar Features e Target
    # -------------------------------------------------------------------------
    print("\n[2/6] Preparando features e target...")
    
    X, y, feature_names = prepare_features_target(df)
    
    # -------------------------------------------------------------------------
    # ETAPA 3: Split Treino/Teste
    # -------------------------------------------------------------------------
    print("\n[3/6] Separando treino/teste...")
    
    if test_curve_names:
        print("  Modo: SELEÇÃO MANUAL de curvas de teste")
        X_train, X_test, y_train, y_test, df_train, df_test = split_with_manual_test(
            df, test_curve_names
        )
    elif test_on_real_only:
        print(f"  Modo: REAL HOLDOUT (teste em curvas reais, test_size={test_size})")
        X_train, X_test, y_train, y_test, df_train, df_test = split_real_holdout(
            df, test_size=test_size
        )
    else:
        print(f"  Modo: SPLIT POR CURVA (test_size={test_size})")
        X_train, X_test, y_train, y_test, df_train, df_test = split_by_curve(
            df, test_size=test_size
        )
    
    # -------------------------------------------------------------------------
    # ETAPA 3b: Imputação de NaN
    # -------------------------------------------------------------------------
    print("\n  Imputando valores faltantes (mediana do treino)...")
    X_train, X_test, imputer = apply_imputation(X_train, X_test)
    
    print(f"\n  Treino: {len(X_train)} amostras")
    print(f"    - Positivas: {sum(y_train == 1)}")
    print(f"    - Negativas: {sum(y_train == 0)}")
    print(f"\n  Teste: {len(X_test)} amostras")
    print(f"    - Positivas: {sum(y_test == 1)}")
    print(f"    - Negativas: {sum(y_test == 0)}")
    
    # -------------------------------------------------------------------------
    # ETAPA 4: Treinar e Avaliar Modelos
    # -------------------------------------------------------------------------
    print("\n[4/6] Treinando e avaliando modelos...")
    
    all_metrics = []
    models = {}
    
    # --- Random Forest ---
    print("\n  Treinando Random Forest...")
    rf_model = train_random_forest(X_train, y_train)
    rf_metrics = evaluate_model(rf_model, X_test, y_test, "Random Forest")
    all_metrics.append(rf_metrics)
    models['random_forest'] = rf_model
    print_metrics(rf_metrics)
    
    # --- XGBoost ---
    print("\n  Treinando XGBoost...")
    xgb_model = train_xgboost(X_train, y_train)
    xgb_metrics = evaluate_model(xgb_model, X_test, y_test, "XGBoost")
    all_metrics.append(xgb_metrics)
    models['xgboost'] = xgb_model
    print_metrics(xgb_metrics)
    
    # --- CatBoost ---
    print("\n  Treinando CatBoost...")
    cat_model = train_catboost(X_train, y_train)
    cat_metrics = evaluate_model(cat_model, X_test, y_test, "CatBoost")
    all_metrics.append(cat_metrics)
    models['catboost'] = cat_model
    print_metrics(cat_metrics)
    
    # --- Regressão Logística (requer features escaladas) ---
    print("\n  Treinando Regressão Logística...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    lr_model = train_logistic_regression(X_train_scaled, y_train)
    lr_metrics = evaluate_model(lr_model, X_test_scaled, y_test, "Logistic Regression")
    all_metrics.append(lr_metrics)
    models['logistic_regression'] = lr_model
    models['scaler'] = scaler
    print_metrics(lr_metrics)
    
    # -------------------------------------------------------------------------
    # ETAPA 5: Persistência
    # -------------------------------------------------------------------------
    print("\n[5/6] Salvando modelos...")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for name, model in models.items():
        if name == 'scaler':
            path = os.path.join(OUTPUT_DIR, 'scaler_model.pkl')
            joblib.dump(model, path)
        else:
            path = save_model(model, name)
        print(f"  -> Salvo: {path}")
    
    # Salva imputer para uso em inferência
    joblib.dump(imputer, os.path.join(OUTPUT_DIR, 'imputer_model.pkl'))
    
    summary_path = save_results_summary(all_metrics)
    print(f"  -> Resultados: {summary_path}")
    
    # Salva relatórios, predições e split
    save_classification_reports(all_metrics, y_test)
    save_predictions(all_metrics, df_test, y_test)
    save_split_info(df_train, df_test)
    
    # -------------------------------------------------------------------------
    # ETAPA 6: Visualizações (sempre salva quando save_plots=True)
    # -------------------------------------------------------------------------
    print("\n[6/6] Gerando e salvando visualizações...")
    
    roc_path = os.path.join(OUTPUT_DIR, 'roc_curves.png') if save_plots else None
    cm_path = os.path.join(OUTPUT_DIR, 'confusion_matrices.png') if save_plots else None
    
    if show_plots or save_plots:
        plot_roc_curves(all_metrics, y_test, save_path=roc_path)
        plot_confusion_matrices(all_metrics, save_path=cm_path)
        # Feature importance para todos os modelos que suportam
        for model, name in [
            (rf_model, "Random Forest"),
            (xgb_model, "XGBoost"),
            (cat_model, "CatBoost"),
            (lr_model, "Logistic Regression"),
        ]:
            fi_path = os.path.join(
                OUTPUT_DIR,
                f"feature_importance_{name.lower().replace(' ', '_')}.png"
            ) if save_plots else None
            plot_feature_importance(model, feature_names, name, save_path=fi_path)
    
    # -------------------------------------------------------------------------
    # Resumo Final
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  PIPELINE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
    print(f"\n  Modelos treinados: {len([k for k in models if k != 'scaler'])}")
    print(f"  Arquivos salvos em: {OUTPUT_DIR}/")
    
    best = max(all_metrics, key=lambda x: x['f1_score'])
    print(f"\n  Melhor modelo (F1-Score): {best['model']} ({best['f1_score']:.4f})")
    
    return {
        'models': models,
        'metrics': all_metrics,
        'feature_names': feature_names,
        'imputer': imputer,
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test
    }


# =============================================================================
# EXECUÇÃO DIRETA
# =============================================================================

if __name__ == "__main__":
    # -------------------------------------------------------------------------
    # CONFIGURAÇÃO DE EXECUÇÃO
    # -------------------------------------------------------------------------
    
    CSV_PATH = os.path.join(OUTPUT_DIR, 'dataset_final.csv')
    TEST_CURVES = None  # Para forçar curvas no teste: ["curve_1", "curve_2", ...]
    
    # test_on_real_only=False (padrão): split por curva em todo o dataset
    # test_on_real_only=True: teste APENAS em curvas reais (db_positive/db_negative)
    #   Use apenas quando quiser validar generalização em dados reais.
    TEST_ON_REAL_ONLY = False
    
    # -------------------------------------------------------------------------
    # EXECUÇÃO DO PIPELINE
    # -------------------------------------------------------------------------
    
    results = run_pipeline(
        csv_path=CSV_PATH if os.path.exists(CSV_PATH) else None,
        test_curve_names=TEST_CURVES,
        test_size=TEST_SIZE,
        skip_cropping=False,
        use_filter='savgol',
        test_on_real_only=TEST_ON_REAL_ONLY,
        show_plots=True,
        save_plots=True
    )

    print(results)
