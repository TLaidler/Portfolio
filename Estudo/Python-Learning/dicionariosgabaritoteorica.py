"""Funcao que transforma lista de tuplas em dicionario -> tuplas com 2 elementos
   Para cada tupla, associar primeiro elemento ao segundo:
       primeiro elemento de cada tupla (item da lista) -> chave
       segundo elemento de cada tupla (item da lista) - > valor
"""
def criaDicionario(lista_tup):
    # lista_tup: lista onde cada elemento eh uma tupla de tamanho 2

    dicio = {} # criando dicionario vazio

    for tupla in lista_tup:
        dicio[tupla[0]] = tupla[1]    
 
    return dicio

def criaDicionario2(lista_tup):
    # lista_tup: lista onde cada elemento eh uma tupla de tamanho 2

    dicio = dict(lista_tup)

    return dicio

"""
   Funcao que transforma um dicionario em uma lista de tuplas onde as tuplas(elementos da lista) estarao ordenadas pelos primeiros elementos
"""
def cria_listaTuplas(dic):
    # dic : dicionario
    lista_tup = dic.items()
    list.sort(lista_tup)

    return lista_tup


def cria_listaTuplas2(dic):
    # dic : dicionario
    lista_tup = [] # criando lista vazia

    for k, v in dic.items():
        tup = (k, v)
        lista_tup.append(tup)
    
    list.sort(lista_tup)

    return lista_tup


