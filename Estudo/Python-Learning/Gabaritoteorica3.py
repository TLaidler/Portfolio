import math

#Funcao Calculo do preco de mercadoria
def calculaPreco(cod, val):
    # cod = codigo da mercadoria
    # val = valor da mercadoria
    if cod == "00":
    	return val - (val * 0.1)
    else:
        return val

#Funcao Encontra o maior numero dentre dois numeros distintos
def encontra_o_maior(num1, num2):
    # Os numeros (num1 e num2) sao, por definicao, distintos
    if num1 > num2:
        return num1
    else:
        return num2

#Funcao Encontra o maior numero dentre dois numeros 
def encontra_o_maior2(num1, num2):
# Os numeros (num1 e num2) podem ser iguais
    if num1 > num2:
        return num1
    elif num2 > num1:
        return num2
    else:
        return "Os numeros sao iguais"

def main():

    cod_produto1 = "02"
    valor_produto1 = 200.0
    cod_produto2 = "00"
    valor_produto2 = 100.0
    numero_A = 30
    numero_B = 40
    numero_C = 30
    
    print "Preco da mercadoria de codigo ", cod_produto1, " e valor bruto ", valor_produto1, "= ",  calculaPreco(cod_produto1, valor_produto1), "\n"
    print "Preco da mercadoria de codigo ", cod_produto2, " e valor bruto ", valor_produto2, " = ",  calculaPreco(cod_produto2, valor_produto2), "\n"
    print "\n"
    print "O maior numero entre os numeros ", numero_A, "e", numero_B, "->", encontra_o_maior(numero_A, numero_B), "\n" 
    print "O maior numero entre os numeros ", numero_C, "e", numero_B, "->", encontra_o_maior2(numero_C, numero_B), "\n"
    print "O maior numero entre os numeros ", numero_A, "e", numero_C, "->", encontra_o_maior2(numero_A, numero_C), "\n"


