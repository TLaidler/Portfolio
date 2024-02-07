import asyncio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

c = np.arange(0.25, 100.25, 0.25)

class Estatistica_Drop:
    async def pelo_menos_1_sucesso(self, tentativas, fracasso):
        fracasso_total = fracasso**tentativas
        return (1 - fracasso_total) * 100

    async def qts_tentativas(self, fracasso, tentativas):
        l = [await self.pelo_menos_1_sucesso(i, fracasso) for i in range(tentativas)]
        return l

    async def tentativa_max(self, lista, n):
        for i in range(len(lista)):
            if lista[i] > n:
                return i
                break

    async def chance_sucesso(self, sucesso, jogadores):
        l = []
        tentativas = 1
        start = time.time()
        while len(l) < jogadores:
            if random.choice(c) <= (sucesso * 100):
                l.append(tentativas)
                tentativas = 1
            else:
                tentativas += 1
        end = time.time()
        print(f"Tempo de Simulacao Total (Assincrono): {end - start}")
        return l

    async def TeoremaCentralLimite(self, simulacao, n=100):
        nova_distribuicao = np.array([])
        start = time.time()

        for i in range(len(simulacao)):
            indices = np.random.randint(0, len(simulacao), n)
            nova_distribuicao = np.append(nova_distribuicao, simulacao[indices].mean())

        end = time.time()
        print(f"Tempo de Calculo Amostragem TCL (Sincrono): {end - start}")
        plt.hist(nova_distribuicao, color='gray', bins=50)
        plt.ylabel('PDF', fontsize=15)
        plt.xlabel('Valor', fontsize=15)
        plt.yticks(fontsize=15)
        plt.xticks(fontsize=15)
        plt.axvline(nova_distribuicao.mean(), color='r', ls='--', lw=2)
        plt.axvline(nova_distribuicao.mean() - nova_distribuicao.std(), color='k', ls='--', lw=2)
        plt.axvline(nova_distribuicao.mean() + nova_distribuicao.std(), color='k', ls='--', lw=2)
        plt.axvline(nova_distribuicao.mean() + 2 * nova_distribuicao.std(), color='m', ls='--', lw=2)
        plt.axvline(nova_distribuicao.mean() - 2 * nova_distribuicao.std(), color='m', ls='--', lw=2)
        plt.show()
        print(f"68% da populacao está dentro das {round(nova_distribuicao.mean()-1*nova_distribuicao.std(),2)}~{round(nova_distribuicao.mean()+1*nova_distribuicao.std(),2)} tentativas")
        print(f"95% da populacao está dentro das {round(nova_distribuicao.mean()-2*nova_distribuicao.std(),2)}~{round(nova_distribuicao.mean()+2*nova_distribuicao.std(),2)} tentativas")
        print(f"Média: {round(nova_distribuicao.mean(),2)}\nDesvio: {round(nova_distribuicao.std(),2)}")

async def main():
    simulacao_1_S = Estatistica_Drop()
    simulacao_1 = pd.Series(await simulacao_1_S.chance_sucesso(0.05, 100000))
    simulacao_1.describe()
    await simulacao_1_S.TeoremaCentralLimite(simulacao_1)

if __name__ == "__main__":
    asyncio.run(main())
