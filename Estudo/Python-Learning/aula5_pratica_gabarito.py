# coding: utf-8

''' 1) Faça uma função que dada uma frase, retorne o número de palavras da frase.
	Considere que a frase pode ter espaços no início e no final.'''
									# str -> int
def n_palavras(frase):
    return len(str.split(frase))


'''2) Faça uma função que dada uma frase, uma palavra, e duas posições, retorna a
	frase excluindo-se as ocorrências desta palavra entre estas duas posições, inclusive.'''
									# str, str, int, int -> str
def exclusao_ltda(frase, palavra, i, f):
    intervalo=frase[i:f+1]
    intervalo_alt=str.replace(intervalo, " "+palavra+" "," ")

    return frase[:i]+intervalo_alt+frase[f+1:]


'''3) Faça uma função que dada uma frase, substitua todos os espaças em branco por '#',
	só que sem usar a função replace.'''
									# str -> str
def substituir_espacos(frase):
    palavras = str.split(frase)
    cola = "#"
	
    return str.join(cola,palavras)


'''4) Escreva uma função que tenha dois parâmetros, uma string e um caractere, e retorne
	apenas o trecho da string situado entre a primeira ocorrência do caractere até o final
	da string. Por exemplo, se a entrada for 'abcabc' e 'a', a saída deve ser 'bcabc'.'''
									# str, str -> str
def trecho_final(string, caractere):
    posicao = str.find(string,caractere)
	
    if posicao==-1:
        return "O caractere '"+caractere+"' nao estah na string fornecida!"
    else:
        posicao+=1
        return string[posicao:]


'''5) Faça uma função que dadas duas listas L1 e L2 de tamanho 3, gera uma lista L3 que é formada
	intercalando os elementos de L1 e L2. Exemplo: L1 = [1, 3, 5] e L2 = [2, 4, 6] gera L3 = [1, 2, 3, 4, 5, 6].'''
									# list, list -> list
def intercalar(L1,L2):
    if len(L1)==3 and len(L2)==3:
        return [L1[0],L2[0],L1[1],L2[1],L1[2],L2[2]]
    else:
        return "As listas devem ter 3 elementos!"






