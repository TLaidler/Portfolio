import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
import pymp
import time
import multiprocessing as mp
from numba import jit, njit 
import scipy.stats as stats
from scipy.stats import norm
from scipy.stats import poisson

sigma = 8/(np.sqrt(8*np.log(2))) #Usando FWHM = 8pixel
x0=0
y0=0

def BrilhoZero(soma=0,flux=6000):
    """
    Docstring: Função printa a soma das exponenciais relativas ao fluxo de uma estrela artificial
    com meia altura (FWHM) de 8 pixels e fluxo total de 6000 elétrons/pixel cujo fundo de céu seja 100 elétrons/pixel.
    Retorna o Brilho_zero da gaussiana.
    """
## Calculando o brilho gaussiano levando em conta as diferentes aberturas possíveis
    for x in range(0,99):
        for y in range(0,99):
            soma = soma + np.exp((-x**2-y**2)/(2*(sigma**2)))
    return flux/soma
    

def gaussiana(x, x0, y, y0,B0): 
    return B0 * norm.pdf(x,x0,sigma)*norm.pdf(y,y0,sigma)


def CriarImg(B0=BrilhoZero()):
    """
    Docstring: Cria o céu teórico com 100 eletrons por pixel numa matriz 100x100 e depois coloca a Estrela Artifical no centro.
    Retorna a matriz imagem da estrela artificial. Recomendado usar plt.matshow() para visualizar.
    """
    ceu = np.ones((100,100))*100
    for j in range(100):
        for i in range(100):
            ceu[i][j] = gaussiana(i,50,j,50,B0) 
    return ceu
