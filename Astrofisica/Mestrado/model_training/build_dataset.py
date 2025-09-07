import os
import sqlite3
import re
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# Caminho para o banco de dados
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), 
                     'data_warehouse', 'stellar_occultations.db')

import astro_data_access as astro_data_access

def recortar_negativos(curva, margem=10, threshold=0.8, min_tamanho=20, z_thresh=3):
    """
    Recorta trechos negativos (sem ocultação) de uma curva positiva, com limpeza de outliers.
    """
    import numpy as np

    time = np.array(curva[0].get('time'))
    flux = np.array(curva[0].get('flux', 'flux_normalized'))

    flux = astro_data_access.normalize_flux(flux)

    # Limpeza de outliers
    time, flux = astro_data_access.remove_outliers(time, flux, z_thresh=z_thresh)

    # Identifica pontos de ocultação
    ocultando = flux < threshold
    if not np.any(ocultando):
        # Não há ocultação, retorna a curva toda como negativa
        return [pd.DataFrame({'time': time, 'flux_normalized': flux})]

    inicio = np.where(ocultando)[0][0]
    fim = np.where(ocultando)[0][-1]

    if inicio - 0 >= min_tamanho:
        negative_curve1 = ({'time': time[:inicio], 'flux_normalized': flux[:inicio]}, curva[1], curva[2], curva[3])
    else:
        negative_curve1 = None
    if len(time) - fim >= min_tamanho:
        negative_curve2 = ({'time': time[fim:], 'flux_normalized': flux[fim:]}, curva[1], curva[2], curva[3])
    else:
        negative_curve2 = None

    return [negative_curve1, negative_curve2]

def separar_curvas_especiais(amostra):
    """
    Separa curvas especiais da amostra.

    Args:
        amostra (list): Amostra de curvas de luz.
    
    Returns:
        list: List contendo as curvas especiais 
        list: List contendo as curvas não especiais.
    """

    observacoes_especiais = [('Aphonsina', '2019-10-01', 'DeanHooper'),
                            ('Hygiea', '2020-12-01', 'Unknown'),
                            ('Athamantis', '2021-01-01', 'PNosworthy'),
                            ('Polyxo', '2019-05-01', 'ChristianWeber'),
                            ('Hygiea', '2017-02-01', 'MForbes'),
                            ('Psyche', '2020-11-01', 'DHerald')]
    curvas_especiais = []
    curvas_nao_especiais = []
    for curve in amostra:
        tuple_obs = (curve[1], curve[2], curve[3])
        if tuple_obs in observacoes_especiais:
            curvas_especiais.append(curve)
        else:
            curvas_nao_especiais.append(curve)
    return curvas_especiais, curvas_nao_especiais

def fetch_all_except(exeptions: list, limit: int):
    """
    Separa curvas especiais da amostra.

    Args:
        amostra (list): Amostra de curvas de luz.
    
    Returns:
        list: List  of tuples [(object, date, observer)] 
    """
    amostra = astro_data_access.get_first_or_last_n_curves(n = limit, first = True)
    #sampled_positives = astro_data_access.get_sampled_light_curves_by_type(_type='positive', limit=100, normalized=True)
    curvas_especiais = []
    curvas_nao_especiais = []
    for curve in amostra:
        tuple_obs = (curve[1], curve[2], curve[3])
        if tuple_obs in observacoes_especiais:
            curvas_especiais.append(curve)
        else:
            curvas_nao_especiais.append(curve)
    return curvas_especiais, curvas_nao_especiais

## guardar dataset negativo:
#all_negatives_from_db = astro_data_access.get_light_curves_by_type(_type='negative', normalized=True)
def create_and_save_artificially_negative_curves():
    limit = input("Digite o limite de curvas a serem analisadas: ")
    sampled_positives = astro_data_access.get_sampled_light_curves_by_type(_type='positive', limit=int(limit), normalized=True)

    specials_curves_from_sample, common_curves_from_sample = separar_curvas_especiais(sampled_positives)

    artificially_negatives_from_sample = []

    try:
        for curve in common_curves_from_sample:
            count = 1
            sub_curves = recortar_negativos(curve, margem=len(curve[0]['time'])/4, threshold=0.75, min_tamanho=4, z_thresh=3)
            for curv in sub_curves:
                if curv is not None:
                    df_curv = pd.DataFrame(curv[0])
                    df_curv.plot(x='time', y='flux_normalized')
                    plt.show()
                    resp = input("Guardar curva? (s/n)")
                    if resp == 's':
                        artificially_negatives_from_sample.append(curv)  # <-- append, não extend!
                        df_curv.to_csv(f'outputs/artific_neg_{curv[3]}_{curv[2]}_{curv[1]}_{count}.csv')
                        count = count + 1
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    return True




