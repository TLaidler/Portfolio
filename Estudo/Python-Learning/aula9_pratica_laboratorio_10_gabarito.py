# coding: utf-8
from operator import itemgetter

''' 1. Responda: Dicionarios podem ser ordenados?'''
	# Não é possível ordenar um dicionario, mas podemos criar uma representação do mesmo com as chaves ordenadas.
	# No caso uma lista de tuplas

def ordena(dicionario):
	L=dict.keys(dicionario)
	L.sort()
	D=[]
	for i in L:
		D.append((i,dicionario[i]))
	return D
       
        # Imprimindo os dados do dicionario de forma ordenada
def print_ordenado(dicionario):
        for k,v in sorted(dicionario.items(), key=itemgetter(0)):
            print 'chave(',k,')-> valor:', v


''' 2. Escreva uma função que converte números inteiros entre 1 e 999 para algarismos romanos. Não converta
o número para uma string. Use os três dicionários abaixo: '''


def romanos(n):
	UNIDADES = { 0: '', 1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII', 8: 'VIII', 9: 'IX' }
	DEZENAS = { 0: '', 1: 'X', 2: 'XX', 3: 'XXX', 4: 'XL', 5: 'L', 6: 'LX', 7: 'LXX', 8: 'LXXX', 9:'XC' }
	CENTENAS = { 0: '', 1: 'C', 2: 'CC', 3: 'CCC', 4: 'CD', 5: 'D', 6: 'DC', 7: 'DCC', 8:'DCCC', 9:'CM' }

	u= n%10
	c= n/100
	d= n/10 - c*10
        num = CENTENAS[c] + DEZENAS[d] + UNIDADES[u]

        return num




















''' 3. Construa uma função que receba uma string e retorne um dicionário onde cada palavra dessa string seja
uma chave e tenha como valor o número de vezes que a palavra aparece.'''

def freq_palavras(string):
	Chaves=str.split(string)
	dicionario={}
	for i in Chaves:
		dicionario[i]=list.count(Chaves,i)
	return dicionario


''' 4. Sabe-se que uma molécula de RNA mensageiro é utilizada como base para sintetizar proteínas, no
processo denominado de tradução. Cada trinca de bases de RNA mensageiro está relacionado com um
aminoácido. Combinando vários aminoácidos, temos uma proteína. Com base na tabela (simplificada)
de trincas de RNA abaixo, crie uma função que receba uma string representando uma molécula de RNA
mensageiro válida, segundo essa tabela, e retorne a cadeia de aminoácidos que representam a proteína
correspondente:'''

def traducao_rnaM(molecula):
	trincas={'UUU': 'Phe','CUU': 'Leu','UUA': 'Leu','AAG': 'Lisina','UCU':'Ser','UAU':'Tyr','CAA':'Gln'}
	i=0
	L=[]
	while i<len(molecula):
		L.append(molecula[i:i+3])
		i+=3
        """
	Se quiser usar for, ao inves de while seria:

	for i in range(0, len(molecula), 3):
		L.append(molecula[i:i+3])

        """

	M=[]
	for j in L:
		M.append(trincas[j])
	return str.join("-",M)


''' 5. Escreva uma função que recebe uma lista de compras e um dicionário contendo o preço de cada produto
disponível em uma determinada loja, e retorna o valor total dos itens da lista que estejam disponíveis
nesta loja. '''

def compras(lista, supermercado = {'amaciante':4.99,'arroz':10.90,'biscoito':1.69,'cafe':6.98,'chocolate':3.79,'farinha':2.99}):
	conta=0
	for i in lista:
		conta += supermercado[i]
	return conta



