#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pipeline de Utilização do Dataset para Treinamento de Modelos de Detecção de Ocultações Estelares

Este script implementa um pipeline completo para:
1. Carregar dataset final
2. Treinar modelos de detecção de ocultações estelares
3. Avaliar o desempenho dos modelos

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


