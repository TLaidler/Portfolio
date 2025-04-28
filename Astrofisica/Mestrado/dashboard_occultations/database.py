#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de acesso ao banco de dados de ocultações estelares.
Fornece funções para consultar e recuperar dados do banco SQLite.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import re

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

def get_all_objects():
    """
    Retorna uma lista de todos os objetos celestes disponíveis no banco de dados.
    
    Returns:
        list: Lista de nomes de objetos celestes.
    """
    conn = connect_to_database()
    if not conn:
        return []
    
    try:
        query = "SELECT DISTINCT object_name FROM observations ORDER BY object_name"
        df = pd.read_sql_query(query, conn)
        return df['object_name'].tolist()
    except sqlite3.Error as e:
        print(f"Erro ao recuperar objetos: {e}")
        return []
    finally:
        conn.close()

def get_object_summary():
    """
    Retorna um resumo dos objetos no banco de dados com contagens.
    
    Returns:
        pandas.DataFrame: DataFrame com nome do objeto, total de observações e datas distintas.
    """
    conn = connect_to_database()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT 
            object_name, 
            COUNT(*) as total_observations,
            COUNT(DISTINCT observation_date) as distinct_dates
        FROM 
            observations 
        GROUP BY 
            object_name
        ORDER BY 
            object_name
        """
        return pd.read_sql_query(query, conn)
    except sqlite3.Error as e:
        print(f"Erro ao recuperar resumo de objetos: {e}")
        return pd.DataFrame()
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
        query = """
            SELECT DISTINCT observation_date 
            FROM observations 
            WHERE object_name = ? 
            ORDER BY observation_date
        """
        df = pd.read_sql_query(query, conn, params=(object_name,))
        return df['observation_date'].tolist()
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
    return "Desconhecido"

def is_positive_observation(additional_metadata):
    """
    Verifica se a observação é positiva com base no campo additional_metadata.
    
    Args:
        additional_metadata (str): String contendo metadados adicionais.
        
    Returns:
        bool: True se a observação for positiva, False caso contrário.
    """
    if not additional_metadata:
        return False
    
    return "positive: True" in additional_metadata.lower() or "is_positive: true" in additional_metadata.lower()

def get_observers_for_date(object_name, date):
    """
    Retorna uma lista de observadores que possuem curvas de luz para um objeto e data específicos.
    
    Args:
        object_name (str): Nome do objeto celeste.
        date (str): Data da observação no formato YYYY-MM-DD.
        
    Returns:
        pandas.DataFrame: DataFrame com informações sobre cada observação.
    """
    conn = connect_to_database()
    if not conn:
        return pd.DataFrame()
    
    try:
        # Recupera as observações
        query = """
            SELECT id, additional_metadata 
            FROM observations 
            WHERE object_name = ? AND observation_date = ?
        """
        observations_df = pd.read_sql_query(query, conn, params=(object_name, date))
        
        # Adiciona colunas derivadas
        observations_df['observer_name'] = observations_df['additional_metadata'].apply(extract_observer_name)
        observations_df['is_positive'] = observations_df['additional_metadata'].apply(is_positive_observation)
        
        # Para cada observação, conta os pontos na curva de luz
        result_rows = []
        
        for _, row in observations_df.iterrows():
            observation_id = row['id']
            
            # Conta os pontos
            count_query = """
                SELECT COUNT(*) as point_count
                FROM light_curves
                WHERE observation_id = ?
            """
            count_df = pd.read_sql_query(count_query, conn, params=(observation_id,))
            point_count = count_df['point_count'].iloc[0]
            
            # Constrói a linha de resultado
            result_row = {
                'observation_id': observation_id,
                'observer_name': row['observer_name'],
                'is_positive': row['is_positive'],
                'point_count': point_count
            }
            result_rows.append(result_row)
        
        # Constrói o DataFrame de resultado
        result_df = pd.DataFrame(result_rows)
        
        # Ordena por nome do observador
        if not result_df.empty:
            result_df = result_df.sort_values('observer_name')
        
        return result_df
    
    except sqlite3.Error as e:
        print(f"Erro ao recuperar observadores para {object_name} em {date}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_light_curve_data(observation_id):
    """
    Retorna os dados da curva de luz para uma observação específica.
    
    Args:
        observation_id (int): ID da observação.
        
    Returns:
        pandas.DataFrame: DataFrame com os dados da curva de luz.
    """
    conn = connect_to_database()
    if not conn:
        return pd.DataFrame()
    
    try:
        # Recupera os dados da curva de luz
        query = """
            SELECT time, flux
            FROM light_curves
            WHERE observation_id = ?
            ORDER BY time
        """
        light_curve_df = pd.read_sql_query(query, conn, params=(observation_id,))
        
        # Normaliza o fluxo
        if not light_curve_df.empty:
            mean_flux = light_curve_df['flux'].mean()
            if mean_flux > 0:
                light_curve_df['flux_normalized'] = light_curve_df['flux'] / mean_flux
            else:
                light_curve_df['flux_normalized'] = light_curve_df['flux']
        
        return light_curve_df
    
    except sqlite3.Error as e:
        print(f"Erro ao recuperar curva de luz para observação {observation_id}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_observation_info(observation_id):
    """
    Retorna informações sobre uma observação específica.
    
    Args:
        observation_id (int): ID da observação.
        
    Returns:
        dict: Dicionário com informações sobre a observação.
    """
    conn = connect_to_database()
    if not conn:
        return {}
    
    try:
        query = """
            SELECT * 
            FROM observations
            WHERE id = ?
        """
        df = pd.read_sql_query(query, conn, params=(observation_id,))
        
        if df.empty:
            return {}
        
        row = df.iloc[0]
        
        result = {
            'id': row['id'],
            'object_name': row['object_name'],
            'observation_date': row['observation_date'],
            'source_portal': row['source_portal'],
            'additional_metadata': row['additional_metadata'],
            'observer_name': extract_observer_name(row['additional_metadata']),
            'is_positive': is_positive_observation(row['additional_metadata'])
        }
        
        return result
    
    except sqlite3.Error as e:
        print(f"Erro ao recuperar informações da observação {observation_id}: {e}")
        return {}
    finally:
        conn.close()

def get_comparative_light_curves(object_name, date, limit=None):
    """
    Retorna dados comparativos de todas as curvas de luz para um objeto e data específicos.
    
    Args:
        object_name (str): Nome do objeto celeste.
        date (str): Data da observação.
        limit (int, optional): Limita o número de curvas retornadas.
        
    Returns:
        dict: Dicionário com listas de curvas de luz e metadados.
    """
    # Obtém os observadores para a data
    observers_df = get_observers_for_date(object_name, date)
    
    if observers_df.empty:
        return {'curves': [], 'observers': [], 'metadata': []}
    
    # Limita o número de observadores se necessário
    if limit is not None and limit > 0:
        observers_df = observers_df.head(limit)
    
    curves = []
    metadata = []
    
    # Obtém os dados para cada observador
    for _, row in observers_df.iterrows():
        observation_id = row['observation_id']
        
        # Obtém a curva de luz
        curve_df = get_light_curve_data(observation_id)
        
        if not curve_df.empty:
            curves.append(curve_df)
            
            # Obtém metadados adicionais
            info = get_observation_info(observation_id)
            metadata.append(info)
    
    # Extrai os nomes dos observadores
    observers = [info['observer_name'] for info in metadata]
    
    return {
        'curves': curves,
        'observers': observers,
        'metadata': metadata
    }

def get_database_statistics():
    """
    Retorna estatísticas gerais sobre o banco de dados.
    
    Returns:
        dict: Dicionário com estatísticas do banco de dados.
    """
    conn = connect_to_database()
    if not conn:
        return {}
    
    try:
        # Total de objetos
        objects_query = "SELECT COUNT(DISTINCT object_name) as total_objects FROM observations"
        objects_df = pd.read_sql_query(objects_query, conn)
        total_objects = objects_df['total_objects'].iloc[0]
        
        # Total de observações
        observations_query = "SELECT COUNT(*) as total_observations FROM observations"
        observations_df = pd.read_sql_query(observations_query, conn)
        total_observations = observations_df['total_observations'].iloc[0]
        
        # Total de pontos de dados
        points_query = "SELECT COUNT(*) as total_points FROM light_curves"
        points_df = pd.read_sql_query(points_query, conn)
        total_points = points_df['total_points'].iloc[0]
        
        # Observações por objeto
        per_object_query = """
            SELECT 
                object_name, 
                COUNT(*) as observations_count 
            FROM 
                observations 
            GROUP BY 
                object_name
        """
        per_object_df = pd.read_sql_query(per_object_query, conn)
        
        # Dados por observador
        observer_query = """
            SELECT 
                additional_metadata
            FROM 
                observations
        """
        observer_df = pd.read_sql_query(observer_query, conn)
        observer_df['observer_name'] = observer_df['additional_metadata'].apply(extract_observer_name)
        
        observer_counts = observer_df['observer_name'].value_counts().to_dict()
        
        return {
            'total_objects': total_objects,
            'total_observations': total_observations,
            'total_points': total_points,
            'observations_per_object': per_object_df.to_dict('records'),
            'observer_counts': observer_counts
        }
        
    except sqlite3.Error as e:
        print(f"Erro ao recuperar estatísticas do banco de dados: {e}")
        return {}
    finally:
        conn.close()

if __name__ == "__main__":
    # Teste rápido das funções
    print("Objetos disponíveis:", get_all_objects())
    print("\nResumo de objetos:")
    print(get_object_summary())
    
    if get_all_objects():
        obj = get_all_objects()[0]
        print(f"\nDatas para {obj}:", get_observation_dates(obj))
        
        dates = get_observation_dates(obj)
        if dates:
            date = dates[0]
            print(f"\nObservadores para {obj} em {date}:")
            print(get_observers_for_date(obj, date))
            
            # Estatísticas gerais
            print("\nEstatísticas do banco de dados:")
            stats = get_database_statistics()
            print(f"Total de objetos: {stats.get('total_objects', 0)}")
            print(f"Total de observações: {stats.get('total_observations', 0)}")
            print(f"Total de pontos de dados: {stats.get('total_points', 0)}") 