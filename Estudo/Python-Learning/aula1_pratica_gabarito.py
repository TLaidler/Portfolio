
# Q1
def calc_areaRet (b, h):
    return b * h

# Q2
def calc_restDiv (x, y):
   return x/y, x % y

# Q3
def media_2_num(x, y):
   return (x+y)/2.0

# Q4
def calc_pondMedia1(k,p, wk, wp):
    # wk e wp sao os pesos e devem ser floats(decimais)
    return (k * wk) + (p * wp)


#Q5
def calc_conta(valor, num_pessoas):
    gorjeta = valor * 0.1
    total_por_pessoa = (valor + gorjeta)/num_pessoas

    return gorjeta, total_por_pessoa


#Q6
def calc_superfCubo(c):
    """A area da superficie de um objeto e a area combinada de todos os lados de sua superficie. 

       Todos os seis lados de um cubo sao congruentes, entao para encontrar a area da superficie de um cubo, 
       tudo o que voce tem de fazer e encontrar a area da superficie de um dos lados do mesmo (aresta**2) e, 
       depois, multiplicar por seis."""

    return c**2 * 6




