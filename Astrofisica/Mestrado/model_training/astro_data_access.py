#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para formatação e manipulação de dados de curvas de luz
de ocultações estelares armazenadas no banco de dados SQLite.

Este módulo fornece funções para:
1. Listar objetos celestes disponíveis
2. Obter datas de observação para um objeto específico
3. Procurar curvas de luz com base em critérios
4. Extrair e formatar dados de curvas de luz específicas
"""

import os
import sqlite3
import re
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import random

# Caminho para o banco de dados
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                     'data_warehouse', 'stellar_occultations.db')

def connect_to_database():
    """Estabelece conexão com o banco de dados SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def get_available_objects():
    """
    Retorna uma lista de todos os objetos celestes disponíveis no banco de dados.
    
    Returns:
        list: Lista de nomes de objetos celestes.
    """
    conn = connect_to_database()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT object_name FROM observations ORDER BY object_name")
        objects = [row[0] for row in cursor.fetchall()]
        return objects
    except sqlite3.Error as e:
        print(f"Erro ao recuperar objetos: {e}")
        return []
    finally:
        conn.close()

def get_observation_dates(object_name):
    """
    Retorna todas as datas de observação disponíveis para um objeto específico.
    
    Args:
        object_name (str): Nome do objeto celeste.
        
    Returns:
        list: Lista de datas de observação no formato YYYY-MM-DD.
    """
    conn = connect_to_database()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT observation_date 
            FROM observations 
            WHERE object_name = ? 
            ORDER BY observation_date
        """, (object_name,))
        
        dates = [row[0] for row in cursor.fetchall()]
        return dates
    except sqlite3.Error as e:
        print(f"Erro ao recuperar datas para {object_name}: {e}")
        return []
    finally:
        conn.close()

def extract_observer_name(additional_metadata):
    """
    Extrai o nome do observador do campo additional_metadata.
    
    Args:
        additional_metadata (str): String contendo metadados adicionais.
        
    Returns:
        str: Nome do observador ou None se não encontrado.
    """
    if not additional_metadata:
        return None
    
    # Procura padrão "observer: NomeDoObservador"
    match = re.search(r'observer:\s*([^,]+)', additional_metadata)
    if match:
        return match.group(1).strip()
    return None

def search_light_curves(object_name, date):
    """
    Retorna uma lista de observadores que possuem curvas de luz para um objeto e data específicos.
    
    Args:
        object_name (str): Nome do objeto celeste.
        date (str): Data da observação no formato YYYY-MM-DD.
        
    Returns:
        list: Lista de dicionários com informações de cada observação.
    """
    conn = connect_to_database()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, additional_metadata 
            FROM observations 
            WHERE object_name = ? AND observation_date = ?
            ORDER BY id
        """, (object_name, date))
        
        results = []
        for row in cursor.fetchall():
            observation_id = row[0]
            additional_metadata = row[1]
            
            # Extrai informações adicionais
            observer_name = extract_observer_name(additional_metadata)
            is_positive = "positive" in additional_metadata.lower()
            
            # Conta quantos pontos de dados tem a curva de luz
            cursor.execute("""
                SELECT COUNT(*) FROM light_curves 
                WHERE observation_id = ?
            """, (observation_id,))
            
            point_count = cursor.fetchone()[0]
            
            results.append({
                "observation_id": observation_id,
                "observer_name": observer_name,
                "is_positive": is_positive,
                "point_count": point_count
            })
            
        return results
    except sqlite3.Error as e:
        print(f"Erro ao pesquisar curvas de luz para {object_name} em {date}: {e}")
        return []
    finally:
        conn.close()

def get_single_light_curve(object_name, date, observer):
    """
    Retorna dados de uma curva de luz específica.
    
    Args:
        object_name (str): Nome do objeto celeste.
        date (str): Data da observação no formato YYYY-MM-DD.
        observer (str): Nome do observador.
        
    Returns:
        dict: Dicionário contendo listas de tempo e fluxo.
    """
    conn = connect_to_database()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Encontra a observação específica
        cursor.execute("""
            SELECT id FROM observations 
            WHERE object_name = ? AND observation_date = ? AND additional_metadata LIKE ?
        """, (object_name, date, f"%observer: {observer}%"))
        
        result = cursor.fetchone()
        if not result:
            print(f"Nenhuma observação encontrada para {observer} de {object_name} em {date}")
            return None
        
        observation_id = result[0]
        
        # Obtém os dados da curva de luz
        cursor.execute("""
            SELECT time, flux FROM light_curves 
            WHERE observation_id = ? 
            ORDER BY time
        """, (observation_id,))
        
        data = cursor.fetchall()
        if not data:
            print(f"Nenhum dado de curva de luz encontrado para esta observação")
            return None
        
        # Converte para dicionário com listas
        times = [row[0] for row in data]
        fluxes = [row[1] for row in data]
        
        return {
            "time": times,
            "flux": fluxes
        }
    
    except sqlite3.Error as e:
        print(f"Erro ao recuperar curva de luz: {e}")
        return None
    finally:
        conn.close()

def normalize_flux(flux_values):
    """
    Normaliza valores de fluxo pela média.
    
    Args:
        flux_values (list): Lista de valores de fluxo.
        
    Returns:
        list: Lista de valores de fluxo normalizados.
    """
    if not flux_values:
        return []
    
    # Calcula a média dos valores
    mean_flux = sum(flux_values) / len(flux_values)
    
    if mean_flux > 0:
        # Normaliza pela média
        return [flux / mean_flux for flux in flux_values]
    else:
        # Se a média for zero ou negativa, retorna os valores originais
        return flux_values[:]

def fetch_light_curves_from_observation(n_curves, object_name, date):
    """
    Função principal para formatação de dados de curvas de luz.
    
    Args:
        n_curves (int): Número de curvas de luz a serem recuperadas.
        object_name (str): Nome do objeto celeste.
        date (str): Data da observação no formato YYYY-MM-DD.
        
    Returns:
        list: Lista de dicionários contendo as curvas de luz formatadas.
        list: Lista com nomes dos observadores correspondentes.
    """
    # Verifica se o objeto existe
    available_objects = get_available_objects()
    if object_name not in available_objects:
        print(f"Objeto '{object_name}' não encontrado. Objetos disponíveis: {available_objects}")
        return [], []
    
    # Verifica se a data existe para esse objeto
    available_dates = get_observation_dates(object_name)
    if date not in available_dates:
        print(f"Data '{date}' não disponível para '{object_name}'. Datas disponíveis: {available_dates}")
        return [], []
    
    # Obtém informações sobre as curvas de luz disponíveis
    light_curves_info = search_light_curves(object_name, date)
    
    if not light_curves_info:
        print(f"Nenhuma curva de luz encontrada para {object_name} em {date}")
        return [], []
    
    # Ordena por nome do observador em ordem alfabética
    light_curves_info.sort(key=lambda info: info.get("observer_name", "") or "")
    
    # Limita ao número solicitado
    light_curves_info = light_curves_info[:n_curves]
    
    # Extrai os dados para cada curva de luz
    curves = []
    observers = []
    
    for info in light_curves_info:
        observer_name = info.get("observer_name")
        if not observer_name:
            continue
            
        data = get_single_light_curve(object_name, date, observer_name)
        if data is not None and data.get("time") and data.get("flux"):
            curves.append(data)
            observers.append(observer_name)
    
    return curves, observers

def fetch_and_normalize_light_curves_from_observation(n_curves, object_name, date):
    """
    Função principal para formatação de dados de curvas de luz.
    
    Args:
        n_curves (int): Número de curvas de luz a serem recuperadas.
        object_name (str): Nome do objeto celeste.
        date (str): Data da observação no formato YYYY-MM-DD.
        
    Returns:
        list: Lista de dicionários contendo as curvas de luz formatadas.
        list: Lista com nomes dos observadores correspondentes.
    """
    # Verifica se o objeto existe
    available_objects = get_available_objects()
    if object_name not in available_objects:
        print(f"Objeto '{object_name}' não encontrado. Objetos disponíveis: {available_objects}")
        return [], []
    
    # Verifica se a data existe para esse objeto
    available_dates = get_observation_dates(object_name)
    if date not in available_dates:
        print(f"Data '{date}' não disponível para '{object_name}'. Datas disponíveis: {available_dates}")
        return [], []
    
    # Obtém informações sobre as curvas de luz disponíveis
    light_curves_info = search_light_curves(object_name, date)
    
    if not light_curves_info:
        print(f"Nenhuma curva de luz encontrada para {object_name} em {date}")
        return [], []
    
    # Ordena por nome do observador em ordem alfabética
    light_curves_info.sort(key=lambda info: info.get("observer_name", "") or "")
    
    # Limita ao número solicitado
    light_curves_info = light_curves_info[:n_curves]
    
    # Extrai os dados para cada curva de luz
    curves = []
    observers = []
    
    for info in light_curves_info:
        observer_name = info.get("observer_name")
        if not observer_name:
            continue
            
        data = get_single_light_curve(object_name, date, observer_name)
        if data is not None and data.get("time") and data.get("flux"):
            # Normaliza os fluxos
            normalized_flux = normalize_flux(data["flux"])
            
            # Adiciona os fluxos normalizados ao dicionário
            data["flux_normalized"] = normalized_flux
            
            curves.append(data)
            observers.append(observer_name)
    
    return curves, observers

def save_data_to_csv(curves, observers, object_name, date):
    """
    Salva os dados das curvas de luz em arquivos CSV.
    
    Args:
        curves (list): Lista de dicionários contendo dados das curvas de luz.
        observers (list): Lista com nomes dos observadores correspondentes.
        object_name (str): Nome do objeto celeste.
        date (str): Data da observação.
    """
    if not curves:
        print("Nenhuma curva para salvar")
        return
    
    # Cria diretório de saída se não existir
    output_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    for curve, observer in zip(curves, observers):
        output_file = os.path.join(
            output_dir, 
            f"{object_name}_{date.replace('-', '')}_{observer}.csv"
        )
        
        with open(output_file, 'w') as f:
            # Escreve cabeçalho
            f.write("time,flux,flux_normalized\n")
            
            # Escreve dados
            for i in range(len(curve["time"])):
                time = curve["time"][i]
                flux = curve["flux"][i]
                flux_norm = curve["flux_normalized"][i]
                f.write(f"{time},{flux},{flux_norm}\n")
        
        print(f"Dados salvos em {output_file}")

def get_all_light_curves_from_object(object_name):
    """
    Busca todas as curvas de luz de um objeto específico.
    
    Args:
        object_name (str): Nome do objeto celeste.
    
    Returns:
        List[Tuple[curve, object_name, date, observer]]
    """
    all_curves = []
    objects = [object_name]
    dates = get_observation_dates(object_name)
    for date in dates:
        curves, observers = fetch_light_curves_from_observation(None, object_name, date)
        for curve, observer in zip(curves, observers):
            all_curves.append((curve, object_name, date, observer))
    return all_curves

def get_sampled_light_curves(limit=None):
    """
    Busca uma amostra aleatória de curvas de luz do banco de dados.
    Se limit for fornecido, retorna até 'limit' curvas aleatórias (de vários objetos).
    
    Args:
        limit (int, opcional): Número máximo de curvas a buscar.
    
    Returns:
        List[Tuple[curve, object_name, date, observer]]
    """
    all_curve_refs = []
    objects = get_available_objects()
    for obj in objects:
        dates = get_observation_dates(obj)
        for date in dates:
            curves, observers = fetch_light_curves_from_observation(1, obj, date)
            for curve, observer in zip(curves, observers):
                all_curve_refs.append((curve, obj, date, observer))
    if limit and limit < len(all_curve_refs):
        sampled_refs = random.sample(all_curve_refs, limit)
    else:
        sampled_refs = all_curve_refs
    return sampled_refs

def get_sampled_light_curves_by_type(_type='positive', limit=None):
    """
    Busca uma amostra aleatória de curvas de luz do banco de dados.
    Se limit for fornecido, retorna até 'limit' curvas aleatórias (de vários objetos).
    
    Args:
        limit (int, opcional): Número máximo de curvas a buscar.
    
    Returns:
        List[Tuple[curve, object_name, date, observer]]
    """
    all_curve_refs = []
    objects = get_available_objects()
    for obj in objects:
        dates = get_observation_dates(obj)
        for date in dates:
            curves, observers = fetch_light_curves_from_observation(1, obj, date)
            for curve, observer in zip(curves, observers):
                all_curve_refs.append((curve, obj, date, observer))
    if limit and limit < len(all_curve_refs):
        sampled_refs = random.sample(all_curve_refs, limit)
    else:
        sampled_refs = all_curve_refs
    return sampled_refs

def plot_raw_curves(curves, pause=False):
    """
    Plota uma lista de curvas de luz, uma por vez.
    Args:
        curves: lista de tuplas (curve, obj, date, observer)
        pause: se True, pausa entre os plots
    """
    for i, (curve, obj, date, observer) in enumerate(curves):
        plt.figure(figsize=(10, 5))
        plt.plot(curve['time'], curve['flux'], marker='o', linestyle='-', markersize=2)
        plt.title(f"Curve {i+1}: {obj} - {date} - {observer}")
        plt.xlabel("Time")
        plt.ylabel("Flux")
        plt.grid(True)
        plt.show()
        if pause:
            input("Press Enter to see the next curve...")

def plot_normalized_curves(curves, pause=False):
    """
    Plota uma lista de curvas de luz, uma por vez.
    Args:
        curves: lista de tuplas (curve, obj, date, observer)
        pause: se True, pausa entre os plots
    """
    for i, (curve, obj, date, observer) in enumerate(curves):
        plt.figure(figsize=(10, 5))
        plt.plot(curve['time'], curve['flux_normalized'], marker='o', linestyle='-', markersize=2)
        plt.title(f"Curve {i+1}: {obj} - {date} - {observer}")
        plt.xlabel("Time")
        plt.ylabel("Normalized Flux")
        plt.grid(True)
        plt.show()
        if pause:
            input("Press Enter to see the next curve...")

def remove_outliers(time, flux, z_thresh=3):
    """
    Remove outliers do fluxo usando z-score.
    """
    flux = np.array(flux)
    time = np.array(time)
    mean = np.mean(flux)
    std = np.std(flux)
    if std == 0:
        return time, flux  # Nenhum outlier possível
    z = (flux - mean) / std
    mask = np.abs(z) < z_thresh
    return time[mask], flux[mask]

def get_first_or_last_n_curves(n, first=True):
    """
    Busca as primeiras ou últimas n curvas do banco de dados.
    Args:
        n (int): Número de curvas a buscar.
        first (bool): Se True, retorna as primeiras n; se False, retorna as últimas n.
    Returns:
        List[dict]: Lista de curvas (cada curva é um dicionário com 'time' e 'flux').
    """
    all_curve_refs = []
    objects = get_available_objects()
    for obj in objects:
        dates = get_observation_dates(obj)
        for date in dates:
            curves, observers = fetch_light_curves_from_observation(1, obj, date)
            for curve, observer in zip(curves, observers):
                all_curve_refs.append(curve)
    if first:
        return all_curve_refs[:n]
    else:
        return all_curve_refs[-n:]

def get_all_curves():
    """
    Busca todas as curvas do banco de dados.
    Returns:
        List[dict]: Lista de curvas (cada curva é um dicionário com 'time' e 'flux').
    """
    all_curves = []
    objects = get_available_objects()
    for obj in objects:
        dates = get_observation_dates(obj)
        for date in dates:
            curves, observers = fetch_light_curves_from_observation(1, obj, date)
            for curve in curves:
                all_curves.append(curve)
    return all_curves



def get_light_curves_by_type(_type='positive', normalized=False, limit=None):
    """
    Busca todas as curvas de luz onde additional_metadata contém is_positive: True/False.

    Args:
        _type (str|bool): 'positive'/'negative' ou True/False.
        normalized (bool): Se True, adiciona 'flux_normalized' em cada curva.
        limit (int|None): Se informado, limita a quantidade de curvas retornadas.

    Returns:
        List[Tuple[curve, object_name, date, observer]]:
            Onde 'curve' é um dicionário com 'time', 'flux' (e opcionalmente 'flux_normalized').
    """
    # Normaliza o alvo para bool
    if isinstance(_type, bool):
        want_positive = _type
    else:
        key = (_type or '').strip().lower()
        if key in ('positive', 'pos', 'true', '1'):
            want_positive = True
        elif key in ('negative', 'neg', 'false', '0'):
            want_positive = False
        else:
            raise ValueError("type deve ser 'positive'/'negative' ou True/False.")

    conn = connect_to_database()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        if want_positive:
            cursor.execute("""
                SELECT id, object_name, observation_date, additional_metadata
                FROM observations
                WHERE additional_metadata IS NOT NULL
                AND LOWER(additional_metadata) LIKE '%is_positive: True%'
                ORDER BY object_name, observation_date, id
            """)
        else:
            cursor.execute("""
                SELECT id, object_name, observation_date, additional_metadata
                FROM observations
                WHERE additional_metadata IS NOT NULL
                AND LOWER(additional_metadata) LIKE '%is_positive: False%'
                ORDER BY object_name, observation_date, id
            """)
        rows = cursor.fetchall()
        results = []

        for obs_id, obj, date, add_meta in rows:
            flag = extract_is_positive(add_meta)
            if flag is None or flag != want_positive:
                continue

            cursor.execute("""
                SELECT time, flux
                FROM light_curves
                WHERE observation_id = ?
                ORDER BY time
            """, (obs_id,))
            data = cursor.fetchall()
            if not data:
                continue

            times = [r[0] for r in data]
            fluxes = [r[1] for r in data]
            curve = {"time": times, "flux": fluxes}
            if normalized:
                curve["flux_normalized"] = normalize_flux(fluxes)

            observer = extract_observer_name(add_meta)
            results.append((curve, obj, date, observer))

            if limit is not None and len(results) >= limit:
                break

        return results

    except sqlite3.Error as e:
        print(f"Erro ao recuperar curvas por tipo '{_type}': {e}")
        return []
    finally:
        conn.close()

def extract_is_positive(additional_metadata):
    """
    Extrai o valor booleano de is_positive do campo additional_metadata.
    Aceita variações como True/False/1/0 (case-insensitive) e ':' ou '='.
    Returns:
        bool | None
    """
    if not additional_metadata:
        return None
    m = re.search(r'is_positive\s*[:=]\s*(true|false|1|0)', additional_metadata, re.IGNORECASE)
    if not m:
        return None
    v = m.group(1).lower()
    return v in ('true', '1')

