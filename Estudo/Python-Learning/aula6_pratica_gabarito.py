# coding: utf-8

""" 1. Faça uma função que dada uma frase retorne uma outra frase que contenha as mesmas palavras da frase
de entrada na ordem inversa. """

def inverte(frase):
    L = str.split(frase, " ")
    list.reverse(L)
	
    return str.join(" ", L)


""" 2. Faça uma função que dada uma frase, reordene as palavras em ordem alfabética. Retorne a frase alterada. """

def ordena(frase):
    L=str.split(frase, " ")
    list.sort(L)
	
    return str.join(" ", L)

# 3. CANCELADA

""" 4. Faça uma função que receba uma frase, uma palavra e uma posição. Caso a palavra já exista na frase,
transforme-a para maiúscula e mostre a frase novamente. Caso a palavra não exista, insira a palavra na
frase na posição dada. Assuma que a primeira palavra está na posição 0. retorne a nova frase. """

def insere_palavra(frase, palavra, s):
    L=str.split(frase)
	
    if palavra in L:
        L[list.index(L,palavra)] = str.upper(palavra)
    else:
        list.insert(L, s, palavra)

    return str.join(" ", L)


def insere_palavra_versao2(frase, palavra, s):
    if palavra in frase:
        inicio = str.index(frase, palavra)
        final = inicio + len(palavra) - 1
        
        return frase[:inicio] + str.upper(palavra) + frase[final+1:]
    else:
        inicio = frase[:s]
        final = frase[s+1:]

        return inicio + palavra + final


def insere_palavra_versaoAlunos(frase, palavra, s):
	''' Esta versao foi brilhantemente desenvolvida em sala pelos alunos:

	    Eric Abreu e Camila Paredes	& Mayara Miranda e Paola Ferreira
            Professor Kleber apenas renomeou as variaveis e colocou o str.join
            diretamente no return.'''

	if palavra in frase:
		return str.replace(frase, palavra, str.upper(palavra))
	else:
		lista_string = str.split(frase)
		list.insert(lista_string, s, palavra)

		return str.join(" ", lista_string)



# 5. CANCELADA


""" 6. Faça uma função que dada uma lista ordenada L (crescente) de números inteiros e um número inteiro
n, inclua n na posição correta. """

def inserir_certo( L, n):
    list.append(L, n)
    list.sort(L) # lista ordenada de forma crescente
	
    return L


"""7. Faça uma função que dada uma lista ordenada L (decrescente) de números inteiros e um número inteiro
n, selecione a sublista formada por todos os elementos maiores que n."""

def sub_maior (L, n):
    M = inserir_certo(L,n) # invocando a funcao inserir_certo do exercicio anterior
    list.reverse(M)
	
    return M[:list.index(M,n)]


""" 8. Faça uma função que dada uma lista de números, retorna o maior elemento da lista."""

def maior(L):
    return max(L)


""" 9. Faça uma função que dada uma lista com as notas dos alunos de uma turma, retorne a média da turma
e uma lista com as notas que ficaram acima da média. """

def notas(L):
    media=sum(L)/(float(len(L))) 
    aprovados=sub_maior(L, media) # invocando a funcao sub_maior do exercicio 7
	
    return media, aprovados



