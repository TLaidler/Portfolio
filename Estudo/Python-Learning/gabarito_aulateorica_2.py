import math

# NOTA: eh possivel existir solucoes diferentes das deste gabarito

'''
EXERCICIOS - SLIDE 30
	GABARITO
'''
#cilindro reto

#Funcao Calculo da Base
def calculaBase(r, pi = 3.14):
    # r = raio
    return pi * r**2

#Funcao Calculo da Base usando a funcao PI do modulo math (math.pi)
def calculaBase(r):
    # r = raio
    # Usando as funcoes PI(funcao constante que retorna o do numero pi) e POW (funcao que calcula potencias)
    # pow recebe dois parametros:o primeiro representa o numero a ser elevado, o segundo representa a potencia
    # round eh uma funcao propria do Python, nao precisando ser importada em nenhum modulo para ser usada. 
    # round(x,2) arredonda o numero 'x' para duas casas decimais

    return round(math.pi, 2) * math.pow(r, 2) 

#Funcao Calculo da Lateral
def calculaLateral(r, h):
    # h = altura, r = raio
    return 2 * round(math.pi, 2) * r * h

#Funcao Calculo da Area Total
def calculaAreaTotal(r, h):
    return 2 * calculaBase(r) + calculaLateral(r, h)

#-------------------------------------------------------------------#

'''
EXERCICIOS - SLIDE 31
	GABARITO
'''
#Funcao Calculo da Gorjeta
def gorjeta(valor, taxa):
    return valor * (taxa /100.0)

#Funcao Calculo da Conta
def conta_total(valor, taxa=10):
    gorjeta_ = gorjeta(valor, taxa)
    
    return valor + gorjeta_

#-------------------------------------------------------------------#

'''
EXERCICIOS - SLIDE 40
	GABARITO
'''
#Funcao Area do Circulo Utilizando math.pi

def area_circulo(r):
    return round(math.pi, 2) * math.pow(r, 2)

#Funcao Arranjo
def arranjo(n, k):
    return math.factorial(n) / math.factorial(n - k)

#Funcao Combinacao
def combinacao(n, k):
    arranj = arranjo(n, k)
    return int(1.0/math.factorial(k) * arranj)

#-------------------------------------------------------------------#

'''
TESTANTO AS FUNCOES ACIMA NO BLOCO PRINCIPAL DO PROGRAMA (FUNCAO MAIN)

        (CHINES)
Invoque (chame) a funcao MAIN no IDLE e ela fara as chamadas a todas as demais funcoes
'''

def main():
    raio = 3
    altura = 4
    print 'cilindro reto -> raio =', raio, '& altura =', altura
    base = calculaBase(raio)
    lateral = calculaLateral(raio, altura)
    area_total = calculaAreaTotal(raio, altura)
    print 'base =', base, '- lateral =', lateral, '- area total =', area_total, '\n'

    total = conta_total(123.50)
    print 'conta = 123.50', '- conta total =', total
    total = conta_total(-230.00)
    print 'conta = -230.00', '- conta total =', total, '\n'

    raio = 6
    area = area_circulo(raio)
    print '\n', 'area do circulo de raio', raio, ' = ', area,  '\n'
 
    resultado1 = arranjo(4, 2)
    resultado2 = combinacao(4, 2)
    print 'arranjo e combinatoria: N = 4 & K = 2'
    print 'res. arranjo =', resultado1, '- res. combinacao =', resultado2

	
#-------------------------------------------------------------------#
