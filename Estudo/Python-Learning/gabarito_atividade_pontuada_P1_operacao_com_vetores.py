#!/usr/bin/env python
#-*- conding: utf8 -*

import math

# 0.3 pt
def produtoInterno(vetor_a, vetor_b): 
    ''' O produto interno entre dois vetores u=(a,b) e v=(c,d) eh dado por:
	<u,v> = <(a,b),(c,d)> = a * c + b * d . '''
    a_coordenadas = vetor_a[1]
    b_coordenadas = vetor_b[1]  
      
    produtoInterno = int(a_coordenadas[0]) * int(b_coordenadas[0]) + int(a_coordenadas[1]) * int(b_coordenadas[1]) + int(a_coordenadas[2]) * int(b_coordenadas[2])

    return produtoInterno 

# 0.3 pt
def norma(vetor): 
    ''' A norma de um vetor w=(a,b) eh dada por:
        |a| = raizquadrada(a^2 + b^2)'''
    coordenadas = vetor[1]
    norma = math.sqrt(math.pow(int(coordenadas[0]),2) + math.pow(int(coordenadas[1]),2) + math.pow(int(coordenadas[2]),2))

    return round(norma, 2)

# 0.1 pt
def angulo(produto_interno, norma_a, norma_b): 
    ''' O angulo entre dois vetores eh dado por:
        angulo = produto interno / (norma do vetor 1 * norma do vetor 2)'''
    return round(produto_interno / (norma_a * norma_b), 2)

# 0.3 pt
def criaVetor(cont, coordenadas): 
    vetor = ("Vetor_" + str(cont), coordenadas.split('.'))
    cont += 1

    return cont, vetor


def main(): 
    print '\n'
    #Criando "tres vetores"
    contador = 1
    contador, vet1 = criaVetor(contador, '2.3.1')
    contador, vet2 = criaVetor(contador, '5.2.2')
    contador, vet3 = criaVetor(contador, '1.5.0')

    #Imprimindo os vetores"
    print vet1, '\n', vet2, '\n', vet3, '\n'

    #Calculando norma dos vetores
    norma_1 = norma(vet1)
    print "Norma do Vetor 1 =", norma_1
    norma_2 = norma(vet2)
    print "Norma do Vetor 2 =", norma_2
    norma_3 = norma(vet3)
    print "Norma do Vetor 3 =", norma_3
    print '\n'

    #Calculando produto interno entre os vetores
    prod_1_2 = produtoInterno(vet1, vet2)
    print "Produto Interno entre os Vetores 1 e 2 =", prod_1_2
    prod_1_3 = produtoInterno(vet1, vet3)
    print "Produto Interno entre os Vetores 1 e 3 =", prod_1_3
    prod_2_3 = produtoInterno(vet2, vet3)
    print "Produto Interno entre os Vetores 2 e 3 =", prod_2_3
    print '\n'

  
    #Calculando angulo entre os vetores
    ang_1_2 = angulo(prod_1_2, norma_1, norma_2)
    print "Angulo entre os Vetores 1 e 2 =", ang_1_2
    ang_1_3 = angulo(prod_1_3, norma_1, norma_3)
    print "Angulo entre os Vetores 1 e 3 =", ang_1_3
    ang_2_3 = angulo(prod_2_3, norma_2, norma_3)
    print "Angulo entre os Vetores 2 e 3 =", ang_2_3
    print '\n'

    

if __name__ == '__main__':
    main()


