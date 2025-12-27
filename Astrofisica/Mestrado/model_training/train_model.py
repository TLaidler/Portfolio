#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pipeline de Construção do Dataset para Detecção de Ocultações Estelares

Este script implementa um pipeline completo para:
1. Buscar curvas de luz do banco de dados SQLite
2. Recortar segmentos negativos de curvas positivas (revisão manual)
3. Carregar curvas sintéticas
4. Extrair features e montar dataset final

Autor: Pipeline gerado para mestrado em Astrofísica
"""

import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from scipy.stats import skew, kurtosis, ttest_ind, ks_2samp
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Importa funções do módulo de acesso a dados
import astro_data_access as ada


# =============================================================================
# ETAPA 1: Buscar todas as curvas do banco de dados
# =============================================================================

def fetch_all_curves_from_db():
    """
    Busca todas as curvas de luz do banco de dados SQLite.
    
    Returns:
        tuple: (positives, negatives) onde cada um é uma lista de tuplas
               (curve, object_name, date, observer)
               curve é um dict com 'time', 'flux', 'flux_normalized'
    """
    print("=" * 60)
    print("ETAPA 1: Buscando curvas do banco de dados...")
    print("=" * 60)
    
    # Busca curvas positivas (com ocultação)
    print("\nBuscando curvas positivas...")
    positives = ada.get_light_curves_by_type('positive', normalized=True)
    print(f"  -> Encontradas {len(positives)} curvas positivas")
    
    # Busca curvas negativas (sem ocultação)
    print("\nBuscando curvas negativas...")
    negatives = ada.get_light_curves_by_type('negative', normalized=True)
    print(f"  -> Encontradas {len(negatives)} curvas negativas")
    
    return positives, negatives


# =============================================================================
# ETAPA 2: Recortar segmentos negativos de curvas positivas
# =============================================================================

def recortar_negativos_interativo(positives, threshold=0.78, min_tamanho=20, z_thresh=3):
    """
    Recorta segmentos negativos (sem ocultação) de curvas positivas,
    permitindo revisão manual de cada recorte.
    
    Args:
        positives: Lista de tuplas (curve, object_name, date, observer)
        threshold: Limiar de fluxo normalizado para detectar ocultação
        min_tamanho: Tamanho mínimo do segmento para ser considerado
        z_thresh: Threshold de z-score para remoção de outliers
    
    Returns:
        tuple: (artificial_negatives, excluded_positives)
               artificial_negatives: lista de tuplas (curve, obj, date, observer, segment_id)
               excluded_positives: set de IDs das curvas positivas usadas para recorte
    """
    print("\n" + "=" * 60)
    print("ETAPA 2: Recorte interativo de segmentos negativos")
    print("=" * 60)
    print("\nInstruções:")
    print("  - Para cada curva positiva, serão mostrados os segmentos fora da ocultação")
    print("  - Digite 's' para ACEITAR o segmento como negativo")
    print("  - Digite 'n' para REJEITAR o segmento")
    print("  - Digite 'q' para SAIR do processo de recorte")
    print("  - Digite 'skip' para PULAR esta curva sem recortar\n")
    
    artificial_negatives = []
    excluded_positives = set()
    
    for idx, (curve, obj, date, observer) in enumerate(positives):
        print(f"\n[{idx+1}/{len(positives)}] Processando: {obj} - {date} - {observer}")
        
        # Obtém dados
        time = np.array(curve.get('time', []))
        flux = np.array(curve.get('flux_normalized', curve.get('flux', [])))
        
        if len(time) == 0 or len(flux) == 0:
            print("  -> Curva vazia, pulando...")
            continue
        
        # Remove outliers
        time_clean, flux_clean = ada.remove_outliers(time, flux, z_thresh=z_thresh)
        
        if len(flux_clean) < min_tamanho * 2:
            print(f"  -> Poucos pontos ({len(flux_clean)}), pulando...")
            continue
        
        # Identifica região de ocultação
        ocultando = flux_clean < threshold
        
        if not np.any(ocultando):
            print("  -> Nenhuma ocultação detectada nesta curva, pulando...")
            continue
        
        inicio_occ = np.where(ocultando)[0][0]
        fim_occ = np.where(ocultando)[0][-1]
        
        # Define segmentos antes e depois da ocultação
        segments = []
        
        # Segmento antes da ocultação
        if inicio_occ >= min_tamanho:
            seg_time = time_clean[:inicio_occ]
            seg_flux = flux_clean[:inicio_occ]
            segments.append(('antes', seg_time, seg_flux))
        
        # Segmento depois da ocultação
        if len(time_clean) - fim_occ - 1 >= min_tamanho:
            seg_time = time_clean[fim_occ+1:]
            seg_flux = flux_clean[fim_occ+1:]
            segments.append(('depois', seg_time, seg_flux))
        
        if not segments:
            print("  -> Nenhum segmento válido encontrado")
            continue
        
        # Mostra a curva completa e os segmentos
        fig, axes = plt.subplots(1, len(segments) + 1, figsize=(5 * (len(segments) + 1), 4))
        #if len(segments) == 1:
        #    axes = [axes, axes]  # Ajusta para indexação
        
        # Plot da curva completa
        ax_full = axes[0] #if len(segments) > 0 else axes
        ax_full.plot(time_clean, flux_clean, 'b.-', markersize=2, linewidth=0.5)
        ax_full.axhline(y=threshold, color='r', linestyle='--', label=f'Threshold={threshold}')
        ax_full.axvspan(time_clean[inicio_occ], time_clean[fim_occ], alpha=0.3, color='red', label='Ocultação')
        ax_full.set_title(f'Curva Completa\n{obj} - {date}')
        ax_full.set_xlabel('Tempo')
        ax_full.set_ylabel('Fluxo Normalizado')
        ax_full.legend(fontsize=8)
        ax_full.grid(True, alpha=0.3)
        
        # Plot dos segmentos
        for i, (seg_name, seg_time, seg_flux) in enumerate(segments):
            ax = axes[i + 1] if len(segments) > 1 else axes[1]
            ax.plot(seg_time, seg_flux, 'g.-', markersize=3, linewidth=0.5)
            ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
            ax.set_title(f'Segmento {seg_name.upper()}\n({len(seg_time)} pontos)')
            ax.set_xlabel('Tempo')
            ax.set_ylabel('Fluxo Normalizado')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        # Revisão manual de cada segmento
        curve_used = False
        for seg_idx, (seg_name, seg_time, seg_flux) in enumerate(segments):
            resp = input(f"  Aceitar segmento '{seg_name}' ({len(seg_time)} pontos)? [s/n/q/skip]: ").strip().lower()
            
            if resp == 'q':
                print("\nProcesso de recorte interrompido pelo usuário.")
                plt.close('all')
                return artificial_negatives, excluded_positives
            
            if resp == 'skip':
                print("  -> Curva pulada")
                break
            
            if resp == 's':
                # Cria curva negativa artificial
                new_curve = {
                    'time': seg_time.tolist(),
                    'flux': seg_flux.tolist(),  # Já está normalizado
                    'flux_normalized': seg_flux.tolist()
                }
                curve_id = f"{obj}_{date}_{observer}_{seg_name}"
                artificial_negatives.append((new_curve, obj, date, observer, seg_name))
                curve_used = True
                print(f"  -> Segmento '{seg_name}' ACEITO como negativo artificial")
            else:
                print(f"  -> Segmento '{seg_name}' REJEITADO")
        
        plt.close('all')
        
        # Se algum segmento foi usado, marca a curva original para exclusão
        if curve_used:
            excluded_id = f"{obj}_{date}_{observer}"
            excluded_positives.add(excluded_id)
            print(f"  -> Curva original marcada para exclusão do dataset positivo")
    
    print(f"\n--- Resumo do Recorte ---")
    print(f"  Segmentos negativos criados: {len(artificial_negatives)}")
    print(f"  Curvas positivas a excluir: {len(excluded_positives)}")
    
    return artificial_negatives, excluded_positives


# =============================================================================
# ETAPA 3: Carregar curvas sintéticas
# =============================================================================

def load_synthetic_curves():
    """
    Carrega todas as curvas sintéticas do diretório synthetic_curve/output/.
    
    Returns:
        list: Lista de tuplas (curve, name) onde curve é um dict com 
              'time', 'flux', 'flux_normalized'
    """
    print("\n" + "=" * 60)
    print("ETAPA 3: Carregando curvas sintéticas...")
    print("=" * 60)
    
    synthetic_dir = os.path.join(os.path.dirname(__file__), 'synthetic_curve', 'output')
    dat_files = glob.glob(os.path.join(synthetic_dir, '*.dat'))
    
    print(f"\nDiretório: {synthetic_dir}")
    print(f"Arquivos encontrados: {len(dat_files)}")
    
    synthetic_curves = []
    
    for filepath in sorted(dat_files):
        filename = os.path.basename(filepath)
        
        try:
            # Lê o arquivo .dat (separado por espaço, com header)
            # Formato: time_s flux flux_norm
            data = []
            with open(filepath, 'r') as f:
                lines = f.readlines()
                
                # Pula o header
                for line in lines[1:]:
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        time_val = float(parts[0])
                        flux_val = float(parts[1])
                        flux_norm = float(parts[2])
                        data.append((time_val, flux_val, flux_norm))
            
            if data:
                times = [d[0] for d in data]
                fluxes = [d[1] for d in data]
                fluxes_norm = [d[2] for d in data]
                
                curve = {
                    'time': times,
                    'flux': fluxes,
                    'flux_normalized': fluxes_norm
                }
                
                # Nome sem extensão
                curve_name = os.path.splitext(filename)[0]
                synthetic_curves.append((curve, curve_name))
                
        except Exception as e:
            print(f"  Erro ao ler {filename}: {e}")
    
    print(f"  -> Carregadas {len(synthetic_curves)} curvas sintéticas")
    
    return synthetic_curves


# =============================================================================
# ETAPA 4: Extração de Features
# =============================================================================

def extract_features(curve, curve_name):
    """
    Extrai features de uma curva de luz para classificação.
    
    Metodologia baseada em lc_processing_pipeline.ipynb:
    - Janela adaptativa baseada no tamanho da curva
    - Derivadas calculadas sobre série suavizada (savgol)
    - Features de comparação entre quartis (testes estatísticos)
    
    Args:
        curve: dict com 'time', 'flux', 'flux_normalized'
        curve_name: Nome identificador da curva
    
    Returns:
        dict: Dicionário com todas as features extraídas
    """
    # Obtém o fluxo normalizado (preferencial) ou bruto
    flux = np.array(curve.get('flux_normalized', curve.get('flux', [])))
    time = np.array(curve.get('time', []))
    
    if len(flux) < 5:
        return None
    
    features = {'curve_name': curve_name}
    
    # ==========================================================================
    # JANELA ADAPTATIVA (seguindo metodologia do notebook)
    # ==========================================================================
    if len(flux) < 40:
        window = max(3, int(len(flux) / 3))
    else:
        window = max(3, int(len(flux) / 40))
    
    # Janela do savgol precisa ser ímpar
    if window % 2 == 0:
        window += 1
    
    # ==========================================================================
    # FEATURES BÁSICAS
    # ==========================================================================
    features['Feature_Amp'] = float(np.max(flux) - np.min(flux))
    features['Feature_Flux_std'] = float(np.std(flux))
    
    # ==========================================================================
    # MOVING AVERAGE FEATURES
    # ==========================================================================
    if window >= 1 and window <= len(flux):
        mv_avg = np.convolve(flux, np.ones(window)/window, mode='valid')
        features['Feature_mv_av_Max'] = float(np.max(mv_avg))
        features['Feature_mv_av_Min'] = float(np.min(mv_avg))
    else:
        features['Feature_mv_av_Max'] = float(np.max(flux))
        features['Feature_mv_av_Min'] = float(np.min(flux))
    
    # ==========================================================================
    # SAVITZKY-GOLAY FILTER FEATURES
    # ==========================================================================
    sg_filtered = flux.copy()  # Fallback
    try:
        if window >= 3 and window <= len(flux):
            sg_filtered = savgol_filter(flux, window_length=window, polyorder=2)
            features['Feature_Savgol_Max'] = float(np.max(sg_filtered))
            features['Feature_Savgol_Min'] = float(np.min(sg_filtered))
            features['Feature_Savgol_std'] = float(np.std(sg_filtered))
        else:
            features['Feature_Savgol_Max'] = float(np.max(flux))
            features['Feature_Savgol_Min'] = float(np.min(flux))
            features['Feature_Savgol_std'] = float(np.std(flux))
    except ValueError:
        # Fallback se savgol falhar
        sg_filtered = flux.copy()
        features['Feature_Savgol_Max'] = float(np.max(flux))
        features['Feature_Savgol_Min'] = float(np.min(flux))
        features['Feature_Savgol_std'] = float(np.std(flux))
    
    # ==========================================================================
    # MAX DRAWDOWN
    # ==========================================================================
    cummax = np.maximum.accumulate(flux)
    drawdown = flux - cummax
    features['Max_Drawdown'] = float(np.min(drawdown))
    
    # ==========================================================================
    # DERIVADAS (SOBRE O SAVGOL - metodologia do notebook)
    # ==========================================================================
    # Primeira derivada usando np.gradient (preserva tamanho do array)
    d_flux = np.gradient(sg_filtered)
    
    # Segunda derivada
    dd_flux = np.gradient(d_flux)
    
    # Features de primeira derivada
    features['Deriv_Min'] = float(np.min(d_flux))
    features['Deriv_Max'] = float(np.max(d_flux))
    features['Deriv_Mean'] = float(np.mean(d_flux))
    features['Deriv_Std'] = float(np.std(d_flux))
    features['Deriv_Skew'] = float(pd.Series(d_flux).skew()) if len(d_flux) > 2 else 0.0
    features['Deriv_Kurtosis'] = float(pd.Series(d_flux).kurtosis()) if len(d_flux) > 3 else 0.0
    
    # Features de segunda derivada
    features['SecondDeriv_Min'] = float(np.min(dd_flux))
    features['SecondDeriv_Max'] = float(np.max(dd_flux))
    features['SecondDeriv_Std'] = float(np.std(dd_flux))
    
    # ==========================================================================
    # FEATURES DE QUARTIS (testes estatísticos entre segmentos)
    # ==========================================================================
    # Remove NaN antes de dividir em quartis
    flux_clean = pd.Series(flux).dropna().values
    
    if len(flux_clean) >= 4:
        quartis = np.array_split(flux_clean, 4)
        
        # Combinações de pares de quartis para comparação
        comb = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        t_pvals = []
        ks_pvals = []
        
        for i, j in comb:
            if len(quartis[i]) > 1 and len(quartis[j]) > 1:
                try:
                    _, t_p = ttest_ind(quartis[i], quartis[j], equal_var=False)
                    _, ks_p = ks_2samp(quartis[i], quartis[j])
                except Exception:
                    t_p, ks_p = np.nan, np.nan
            else:
                t_p, ks_p = np.nan, np.nan
            
            t_pvals.append(t_p)
            ks_pvals.append(ks_p)
        
        # Remove NaN antes de calcular mínimos
        t_pvals_clean = [p for p in t_pvals if not np.isnan(p)]
        ks_pvals_clean = [p for p in ks_pvals if not np.isnan(p)]
        
        # Evita log(0)
        eps = 1e-300
        
        # Menor p-valor em escala log (mais discriminativo)
        if t_pvals_clean:
            features['MinLogP_Ttest'] = float(-np.log10(min(t_pvals_clean) + eps))
        else:
            features['MinLogP_Ttest'] = np.nan
        
        if ks_pvals_clean:
            features['MinLogP_KS'] = float(-np.log10(min(ks_pvals_clean) + eps))
        else:
            features['MinLogP_KS'] = np.nan
    else:
        features['MinLogP_Ttest'] = np.nan
        features['MinLogP_KS'] = np.nan
    
    return features


# =============================================================================
# K-MEANS FEATURE ENGINEERING
# =============================================================================

def add_kmeans_features(df, n_clusters=2, random_state=42):
    """
    Adiciona features baseadas em K-Means ao DataFrame.
    
    Esta função usa K-Means para criar features adicionais que capturam
    a posição de cada amostra no espaço de features em relação aos 
    centroides dos clusters.
    
    Features adicionadas:
    - kmeans_cluster: Label do cluster atribuído (0, 1, ..., n_clusters-1)
    - kmeans_dist_c0, kmeans_dist_c1, ...: Distância euclidiana a cada centroide
    
    Args:
        df: DataFrame com as features originais
        n_clusters: Número de clusters para K-Means (default: 3)
        random_state: Seed para reprodutibilidade
    
    Returns:
        tuple: (df_with_kmeans, kmeans_model, scaler)
    """
    print("\n--- Adicionando features de K-Means ---")
    
    # Seleciona apenas colunas numéricas de features (exclui metadados)
    feature_cols = [c for c in df.columns 
                    if c not in ['curve_name', 'source', 'occ']]
    
    print(f"  Features usadas para clustering: {len(feature_cols)}")
    
    # Preenche NaN com 0 e extrai matriz de features
    X = df[feature_cols].fillna(0).values
    
    # Normaliza antes do K-Means (essencial para K-Means funcionar corretamente)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Treina K-Means
    print(f"  Treinando K-Means com K={n_clusters}...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    kmeans.fit(X_scaled)
    
    # Adiciona label do cluster
    df = df.copy()  # Evita SettingWithCopyWarning
    df['kmeans_cluster'] = kmeans.labels_
    
    # Adiciona distância a cada centroide
    distances = kmeans.transform(X_scaled)  # Shape: (n_samples, n_clusters)
    for i in range(n_clusters):
        df[f'kmeans_dist_c{i}'] = distances[:, i]
    
    # Estatísticas dos clusters
    print(f"\n  Distribuição dos clusters:")
    for i in range(n_clusters):
        count = (df['kmeans_cluster'] == i).sum()
        pos_count = ((df['kmeans_cluster'] == i) & (df['occ'] == 1)).sum()
        neg_count = ((df['kmeans_cluster'] == i) & (df['occ'] == 0)).sum()
        print(f"    Cluster {i}: {count} amostras (pos={pos_count}, neg={neg_count})")
    
    print(f"\n  Features K-Means adicionadas: kmeans_cluster + {n_clusters} distâncias")
    
    return df, kmeans, scaler


# =============================================================================
# ETAPA 5: Construir e salvar dataset final
# =============================================================================

def build_and_save_dataset(positives, negatives_db, artificial_negatives, 
                           synthetic_curves, excluded_positives):
    """
    Constrói o dataset final unificando todas as fontes de dados.
    
    Args:
        positives: Curvas positivas do banco de dados
        negatives_db: Curvas negativas do banco de dados
        artificial_negatives: Segmentos negativos recortados de positivas
        synthetic_curves: Curvas sintéticas (negativas)
        excluded_positives: Set de IDs de positivas a excluir
    
    Returns:
        pd.DataFrame: Dataset final
    """
    print("\n" + "=" * 60)
    print("ETAPA 4: Extraindo features e construindo dataset...")
    print("=" * 60)
    
    all_features = []
    
    # --- Processa curvas positivas (excluindo as usadas para recorte) ---
    print("\nProcessando curvas positivas...")
    count_pos = 0
    for curve, obj, date, observer in positives:
        curve_id = f"{obj}_{date}_{observer}"
        
        # Pula se foi usada para criar negativo artificial
        if curve_id in excluded_positives:
            continue
        
        curve_name = f"{obj}_{date}_{observer}"
        feats = extract_features(curve, curve_name)
        
        if feats:
            feats['source'] = 'db_positive'
            feats['occ'] = 1
            all_features.append(feats)
            count_pos += 1
    
    print(f"  -> {count_pos} curvas positivas processadas")
    
    # --- Processa curvas negativas do banco ---
    print("\nProcessando curvas negativas do banco...")
    count_neg_db = 0
    for curve, obj, date, observer in negatives_db:
        curve_name = f"{obj}_{date}_{observer}"
        feats = extract_features(curve, curve_name)
        
        if feats:
            feats['source'] = 'db_negative'
            feats['occ'] = 0
            all_features.append(feats)
            count_neg_db += 1
    
    print(f"  -> {count_neg_db} curvas negativas do banco processadas")
    
    # --- Processa negativos artificiais ---
    print("\nProcessando negativos artificiais...")
    count_art = 0
    for curve, obj, date, observer, seg_name in artificial_negatives:
        curve_name = f"{obj}_{date}_{observer}_{seg_name}_artificial"
        feats = extract_features(curve, curve_name)
        
        if feats:
            feats['source'] = 'artificial_negative'
            feats['occ'] = 0
            all_features.append(feats)
            count_art += 1
    
    print(f"  -> {count_art} negativos artificiais processados")
    
    # --- Processa curvas sintéticas ---
    print("\nProcessando curvas sintéticas...")
    count_syn = 0
    for curve, name in synthetic_curves:
        curve_name = f"synthetic_{name}"
        feats = extract_features(curve, curve_name)
        
        if feats:
            feats['source'] = 'synthetic'
            feats['occ'] = 0  # Sintéticas são negativas
            all_features.append(feats)
            count_syn += 1
    
    print(f"  -> {count_syn} curvas sintéticas processadas")
    
    # --- Monta DataFrame ---
    print("\nMontando DataFrame final...")
    df = pd.DataFrame(all_features)
    
    # --- Adiciona features de K-Means ---
    #if len(df) >= 2:  # Precisa de pelo menos 3 amostras para K=3
    #    df, kmeans_model, scaler = add_kmeans_features(df, n_clusters=2)
    #else:
    #    print("\n[AVISO] Poucas amostras para K-Means, pulando...")
    #    kmeans_model, scaler = None, None
    
    # Reordena colunas (20 features originais + 4 K-Means + 3 metadados)
    cols_order = ['curve_name', 'source', 'occ',
                  # Features básicas (8)
                  'Feature_Amp', 'Feature_mv_av_Max', 'Feature_mv_av_Min', 
                  'Feature_Flux_std', 'Feature_Savgol_Max', 'Feature_Savgol_Min',
                  'Feature_Savgol_std', 'Max_Drawdown',
                  # Features de quartis (2)
                  'MinLogP_Ttest', 'MinLogP_KS',
                  # Features de derivadas (9)
                  'Deriv_Min', 'Deriv_Max', 'Deriv_Mean', 'Deriv_Std',
                  'Deriv_Skew', 'Deriv_Kurtosis',
                  'SecondDeriv_Min', 'SecondDeriv_Max', 'SecondDeriv_Std',
                  # Features de K-Means (4)
                  #'kmeans_cluster', 'kmeans_dist_c0', 'kmeans_dist_c1', 'kmeans_dist_c2']
                  ]
    
    # Usa apenas colunas que existem
    cols_final = [c for c in cols_order if c in df.columns]
    df = df[cols_final]
    
    # --- Salva o dataset ---
    output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, 'dataset_final.csv')
    df.to_csv(output_path, index=False)
    
    print(f"\n{'=' * 60}")
    print("DATASET FINAL CRIADO COM SUCESSO!")
    print(f"{'=' * 60}")
    print(f"\nArquivo: {output_path}")
    print(f"\nResumo:")
    print(f"  - Total de amostras: {len(df)}")
    print(f"  - Positivas (occ=1): {len(df[df['occ'] == 1])}")
    print(f"  - Negativas (occ=0): {len(df[df['occ'] == 0])}")
    print(f"\nDistribuição por fonte:")
    print(df['source'].value_counts().to_string())
    
    return df


# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================

def run_pipeline(sample_size_for_cropping=None, skip_cropping=False):
    """
    Executa o pipeline completo de construção do dataset.
    
    Args:
        sample_size_for_cropping: Número de curvas positivas a usar no recorte
                                  (None = usar todas)
        skip_cropping: Se True, pula a etapa de recorte interativo
    
    Returns:
        pd.DataFrame: Dataset final
    """
    print("\n" + "#" * 70)
    print("#" + " " * 20 + "PIPELINE DE CONSTRUÇÃO DO DATASET" + " " * 15 + "#")
    print("#" * 70)
    
    # Etapa 1: Buscar curvas do banco de dados
    positives, negatives_db = fetch_all_curves_from_db()
    
    # Etapa 2: Recorte interativo de segmentos negativos
    artificial_negatives = []
    excluded_positives = set()
    
    if not skip_cropping and len(positives) > 0:
        # Usa amostra se especificado
        if sample_size_for_cropping and sample_size_for_cropping < len(positives):
            import random
            sample = random.sample(positives, sample_size_for_cropping)
            print(f"\nUsando amostra de {sample_size_for_cropping} curvas para recorte...")
        else:
            sample = positives
        
        artificial_negatives, excluded_positives = recortar_negativos_interativo(sample)
    else:
        print("\n[INFO] Etapa de recorte interativo pulada.")
    
    # Etapa 3: Carregar curvas sintéticas
    synthetic_curves = load_synthetic_curves()
    
    # Etapa 4 & 5: Extrair features e construir dataset
    df = build_and_save_dataset(
        positives=positives,
        negatives_db=negatives_db,
        artificial_negatives=artificial_negatives,
        synthetic_curves=synthetic_curves,
        excluded_positives=excluded_positives
    )
    
    return df


# =============================================================================
# EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Pipeline de construção do dataset para detecção de ocultações estelares'
    )
    parser.add_argument(
        '--sample', '-s',
        type=int,
        default=50,
        help='Número de curvas positivas a usar no recorte interativo (default: todas)'
    )
    parser.add_argument(
        '--skip-cropping',
        action='store_true',
        help='Pular a etapa de recorte interativo'
    )
    
    args = parser.parse_args()
    
    # Executa o pipeline
    dataset = run_pipeline(
        sample_size_for_cropping=args.sample,
        skip_cropping=args.skip_cropping
    )
    
    print("\nPipeline concluído!")

