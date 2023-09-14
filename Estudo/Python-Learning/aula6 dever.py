#Lista 6 - Por Thiago Laidler#
def aquecimento(frase):
    frase=str(frase)
    s=frase.split()
    f="-".join(s)
    return f

def questao1(frase):
    frase=str(frase)
    s=frase.split()
    c=s[::-1]
    d=" ".join(c)
    return d
def questao2(frase):
    frase=str(frase)
    L=frase.split()
    list.sort(L)
    e=" ".join(L)
    return e

def questao4(frase,palavra,posicao):
    frase=str(frase)
    palavra=str(palavra)
    L=frase.split()
    if palavra in L:
        L[list.index(L,palavra)] = str.upper(palavra)
    else:
        list.insert(L, posicao, palavra)
        G=" ".join(L)
        return G
        
