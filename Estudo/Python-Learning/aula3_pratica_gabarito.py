import math

#Q1
def absoluto(num):
    if num < 0:
        return num * -1
    else:
        return num

#Q1 - outra resolucao
def absoluto2(num):
    return abs(num)

#Q2
def inverteModulo(num):
    return num * -1

#Q3
def repetePalavra(palavra):
    return palavra * 3

# Q4
def funcao_figura(x):	
    if x >= 0 and x <= 2:
        return x
    elif x <= 3.5:
        return 2
    elif x <= 5:
        return 3
    elif x > 5:
        return  math.pow(x,2) - 10 * x + 28

#Q5
def min_max(a, b):
    if a > b:
        return 'minimo=' + str(b) + ' - maximo=' + str(a)
    elif b > a:
        return 'minimo=' + str(a) + ' - maximo=' + str(b)











	



