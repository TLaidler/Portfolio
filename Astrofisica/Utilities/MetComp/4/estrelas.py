import numpy as np
import time
import argparse

parser = argparse.ArgumentParser(description='Código que calcula a temperatura da estrela passada para o código')

parser.add_argument('-e', '--estrela', type=int, help='Número da estrela')
args = parser.parse_args()

comp, rad, erro = np.loadtxt(f'./estrelas/estrela_{args.estrela}.txt').T

h = 6.62607015e-34
c = 299792458
k = 1.380649e-23

with open('./tempos.txt', 'a+') as tempos:
    i = time.time()
    minchi = float('inf')
    temp = 0
    mint, maxt = 1000, 50000
    while True:
        ts = [round(i,0) for i in np.linspace(mint,maxt, 20)]
        chi = minchi
        for t in ts:
            e = np.sum(np.power((rad - (((2 * h * (c ** 2))/(comp ** 5)) * (1 / (np.exp(1) ** ((h * c) / (comp * k * t)) - 1)))) / erro, 2))
            if e < minchi:
                minchi, temp = e, t
        if minchi == chi or minchi < 1.0e-5:
            break
        mint = ts[list(ts).index(temp)-1]
        if mint == ts[-1]:
            mint = ts[0]
        maxt = ts[list(ts).index(temp)+1]
    f = time.time()
    linha = f'estrela: {args.estrela}, temperatura: {temp}, tempo: {f-i}\n'
    print(linha[:-2])
    tempos.write(linha)
