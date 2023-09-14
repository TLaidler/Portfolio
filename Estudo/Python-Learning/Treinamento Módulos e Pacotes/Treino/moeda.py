## Modulo de funcoes para manusearmos as moedas
def aumentar(preco,porcentagem):
    n=preco*(porcentagem*0.01)
    return preco+n

def metade(preco):
    return preco/2

def dobro(preco):
    return preco*2

def reduzir(preco,porcentagem):
    n=preco*(porcentagem*0.01)
    return preco-n

