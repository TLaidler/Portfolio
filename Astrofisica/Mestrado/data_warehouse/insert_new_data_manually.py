#Devido aos problemas com o "insert_new_data.py", foi necessário criar um script para inserir os dados manualmente 
#Esse script serve apenas para inserir os dados na DB utilizando as curvas de luz obtidas no drive do Grupo do Rio

import os
import sqlite3
import re
from datetime import datetime

def extract_metadata_from_path(filepath):
    """
    Extrai metadados do caminho do arquivo.
    
    Exemplo: data_warehouse/data/Umbriel-set20/positive/lc_AndrewScheck.dat
    - object_name: Umbriel
    - observation_date: 2020-09-01 (convertido de 'set20')
    - is_positive: True/False (baseado na pasta 'positive' ou 'negative')
    - observer_name: AndrewScheck
    """
    # Extrai o nome do observador do nome do arquivo
    filename = os.path.basename(filepath)
    observer_match = re.match(r'lc_([A-Za-z0-9]+)\.dat', filename)
    observer_name = observer_match.group(1) if observer_match else "Unknown"
    
    # Determina se é uma detecção positiva ou negativa
    is_positive = 'positive' in filepath.lower()
    
    # Extrai o nome do objeto e a data
    path_parts = filepath.split(os.sep)
    object_parts = None
    
    for part in path_parts:
        if '-' in part and not part.startswith('lc_'):
            object_parts = part.split('-')
            break
    
    if object_parts and len(object_parts) >= 2:
        object_name = object_parts[0]
        date_str = object_parts[1]
        
        # Converte string de data para objeto datetime
        # Assume formato 'mes(abreviado)ano(2 dígitos)'
        month_map = {
            'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        month_match = re.match(r'([a-z]{3})(\d{2})', date_str.lower())
        if month_match:
            month_str, year_str = month_match.groups()
            month = month_map.get(month_str, 1)  # Default para janeiro se não encontrar
            year = 2000 + int(year_str)  # Assume anos 2000
            observation_date = f"{year}-{month:02d}-01"  # Usa dia 1 como padrão
        else:
            # Se não conseguir extrair a data corretamente, usa um valor padrão
            observation_date = "2000-01-01"
    else:
        object_name = "Unknown"
        observation_date = "2000-01-01"
    
    return {
        "object_name": object_name,
        "observation_date": observation_date,
        "is_positive": is_positive,
        "observer_name": observer_name
    }

def read_light_curve_data(filepath):
    """
    Lê os dados da curva de luz de um arquivo .dat
    Retorna uma lista de tuplas (time, flux, error)
    """
    data = []
    with open(filepath, 'r') as file:
        for line in file:
            # Ignora linhas vazias ou comentários
            if line.strip() and not line.strip().startswith('#'):
                parts = line.strip().split()
                if len(parts) >= 2:
                    time = float(parts[0])
                    flux = float(parts[1])
                    # Se houver um terceiro valor, é considerado como erro
                    error = float(parts[2]) if len(parts) > 2 else 0.0
                    data.append((time, flux, error))
    return data

def check_observation_exists(cursor, object_name, observation_date, observer_name, is_positive):
    """Verifica se a observação já existe no banco de dados"""
    additional_metadata = f"observer: {observer_name}, is_positive: {is_positive}"
    
    cursor.execute('''
        SELECT id FROM observations 
        WHERE object_name = ? AND observation_date = ? AND additional_metadata = ?
    ''', (object_name, observation_date, additional_metadata))
    
    result = cursor.fetchone()
    if result:
        return result[0]  # Retorna o ID se encontrar
    return None

def insert_observation(cursor, object_name, observation_date, observer_name, is_positive):
    """Insere uma nova observação e retorna seu ID"""
    additional_metadata = f"observer: {observer_name}, is_positive: {is_positive}"
    source_portal = "Manual Import"
    
    cursor.execute('''
        INSERT INTO observations (object_name, observation_date, source_portal, additional_metadata)
        VALUES (?, ?, ?, ?)
    ''', (object_name, observation_date, source_portal, additional_metadata))
    
    return cursor.lastrowid

def insert_light_curve_data(cursor, observation_id, light_curve_data):
    """Insere os pontos da curva de luz no banco de dados"""
    for time, flux, _ in light_curve_data:  # Ignoramos o valor de erro por enquanto
        cursor.execute('''
            INSERT INTO light_curves (observation_id, time, flux)
            VALUES (?, ?, ?)
        ''', (observation_id, time, flux))

def process_files():
    """Processa todos os arquivos .dat e insere no banco de dados"""
    db_path = os.path.join(os.path.dirname(__file__), 'stellar_occultations.db')
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    # Verifica se o banco de dados existe
    if not os.path.exists(db_path):
        print(f"Erro: Banco de dados não encontrado em {db_path}")
        print("Execute create_database.py primeiro.")
        return
    
    # Conecta ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Contadores para estatísticas
    stats = {
        "total_files": 0,
        "processed_files": 0,
        "existing_observations": 0,
        "new_observations": 0,
        "error_files": 0
    }
    
    # Percorre todas as pastas e arquivos
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.dat') and file.startswith('lc_'):
                stats["total_files"] += 1
                filepath = os.path.join(root, file)
                
                try:
                    # Extrai metadados do caminho do arquivo
                    metadata = extract_metadata_from_path(filepath)
                    object_name = metadata["object_name"]
                    observation_date = metadata["observation_date"]
                    is_positive = metadata["is_positive"]
                    observer_name = metadata["observer_name"]
                    
                    # Verifica se a observação já existe
                    observation_id = check_observation_exists(
                        cursor, object_name, observation_date, observer_name, is_positive
                    )
                    
                    if observation_id:
                        # Se a observação já existe, pula o arquivo
                        print(f"Observação já existe para {filepath}")
                        stats["existing_observations"] += 1
                        continue
                    
                    # Insere a nova observação
                    observation_id = insert_observation(
                        cursor, object_name, observation_date, observer_name, is_positive
                    )
                    
                    # Lê e insere os dados da curva de luz
                    light_curve_data = read_light_curve_data(filepath)
                    insert_light_curve_data(cursor, observation_id, light_curve_data)
                    
                    print(f"Processado: {filepath}")
                    stats["new_observations"] += 1
                    stats["processed_files"] += 1
                
                except Exception as e:
                    print(f"Erro ao processar {filepath}: {e}")
                    stats["error_files"] += 1
    
    # Commit das alterações e fecha a conexão
    conn.commit()
    conn.close()
    
    # Exibe estatísticas
    print("\nEstatísticas de processamento:")
    print(f"Total de arquivos encontrados: {stats['total_files']}")
    print(f"Arquivos processados com sucesso: {stats['processed_files']}")
    print(f"Observações novas inseridas: {stats['new_observations']}")
    print(f"Observações já existentes: {stats['existing_observations']}")
    print(f"Arquivos com erro: {stats['error_files']}")

if __name__ == "__main__":
    process_files()


