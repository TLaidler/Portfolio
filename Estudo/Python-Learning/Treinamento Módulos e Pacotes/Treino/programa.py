import moeda
import math ##ou from math import something
def valor(m=0.00,real='R$'):
    m=round(m,2)                ##funcao para arredondar qlqr valor para até 2 casas decimais
    return (f"{real} {m}".replace('.',','))

n=float(input("Digite o preco do produto: R$ "))
print(f"O dobro de {valor(n)} é {valor(moeda.dobro(n))}")
print(f"A metade de {valor(n)} é {valor(moeda.metade(n))}")
print(f"Aumentando em 10%, {valor(n)} fica {valor(moeda.aumentar(n,10))}")
print(f"Reduzindo em 10%, {valor(n)} fica {valor(moeda.reduzir(n,10))}")
# ou print("O fatorial de " + str(n) + " é " + str(fat))
# ou print("O fatorial de {} é {}.\n".format(n,fat))