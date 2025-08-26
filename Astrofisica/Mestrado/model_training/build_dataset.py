import os
import sqlite3
import re
from datetime import datetime

# Caminho para o banco de dados
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), 
                     'data_warehouse', 'stellar_occultations.db')

import astro_data_access as astro_data_access

def recortar_negativos(curva, margem=10, threshold=0.8, min_tamanho=20, z_thresh=3):
    """
    Recorta trechos negativos (sem ocultação) de uma curva positiva, com limpeza de outliers.
    """
    import numpy as np
    import pandas as pd

    time = np.array(curva[0].get('time'))
    flux = np.array(curva[0].get('flux', 'flux_normalized'))

    # Limpeza de outliers
    time, flux = astro_data_access.remove_outliers(time, flux, z_thresh=z_thresh)

    # Identifica pontos de ocultação
    ocultando = flux < threshold
    if not np.any(ocultando):
        # Não há ocultação, retorna a curva toda como negativa
        return [pd.DataFrame({'time': time, 'flux_normalized': flux})]

    # Encontra início e fim do evento
    indices = np.where(ocultando)[0]
    inicio = indices[0]
    fim = indices[-1]

    # Trecho antes da ocultação
    antes = slice(0, max(0, inicio - margem))
    # Trecho depois da ocultação
    depois = slice(min(len(time), fim + margem), len(time))

    negativos = []
    if (antes.stop - antes.start) >= min_tamanho:
        negativos.append(pd.DataFrame({'time': time[antes], 'flux_normalized': flux[antes]}))
    if (depois.stop - depois.start) >= min_tamanho:
        negativos.append(pd.DataFrame({'time': time[depois], 'flux_normalized': flux[depois]}))

    return negativos

## guardar dataset negativo:

all_negatives_from_db = astro_data_access.get_light_curves_by_type(_type='negative', normalized=True)

sampled_positives = astro_data_access.get_sampled_light_curves_by_type(_type='positive', limit=100, normalized=True)

negatives_from_sample = []

for curve in sampled_positives:
    sub_curves = recortar_negativos(curve, margem=len(curve[0]['time'])/4, threshold=0.6, min_tamanho=20, z_thresh=3)
    for curv in sub_curves:
        curv.plot(x='time', y='flux_normalized')
        resp = input("Guardar curva? (s/n)")
        if resp == 's':
            negatives_from_sample.extend(curv)