#Pacote
#Author:
#Last update: Never

r'''
Docstrings: Descrição do pacote

Funções:
Checar_tempo
Passar_tempo
Maior_Tupla
'''

import numpy as np
from astropy.time import Time

def Checar_tempo():
	"""
	Docstring da função. Essa função escreve
	o tempo no momento em que foi rodada.
	"""
	print(Time.now().iso)

def Passar_tempo(loop=10000):
	"""
	Docstring da função. Essa função faz um loop
	qualquer e escreve o tempo que demorou
	"""
	t0=Time.now()
	for i in range(loop):
		a=1
	t1=Time.now()
	print('Passou {:0.3f} segundos'.format((t1-t0).sec))