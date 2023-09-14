def m(tup):
    """
Retorna o maior valor da tupla e seu index
    """
    maior = 0
    ind = 0
    for i in range(len(tup)):
        while i<=len(tup):
            if tup[i] > maior:
                maior = tup[i]
                ind = i
            break
    return maior,ind