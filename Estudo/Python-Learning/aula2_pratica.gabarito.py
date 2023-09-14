import math

#Q1_a
def media_4num(x,y,w,z):
    med = (x+y+w+z)/4.0
 
    return med

#Q2_a (versao 1)
def hipotenusa(ca, co):
    hipo = math.sqrt(math.pow(ca,2) + math.pow(co,2)) 

    return hipo

#Q2_a (versao 2)
def hipotenusa_2(ca, co):
    hipo = math.hypot(ca,co)

    return hipo

#Q2_b
def distancia_2pontos(x1, y1, x2, y2):
    dist = math.sqrt((math.pow(x1-x2,2) + math.pow(y1-y2,2))

    return dist

#Q2_c
def perimetro_trianguloReto(ca, co):
    hipo = hipotenusa(ca,co)
    peri = hipo + ca, + co

    return peri


#Q3
def comprimentoCirc(raio):
    comp = 2 * math.pi * raio

    return comp

# Q4
def area_circular(raio, angulo=360):
    area_c = (angulo * math.pi * math.pow(raio,2)) / angulo

    return area_c	

# Q5_1
def calc_termosPA(a1, an, r):
    t = (an - a1)/r + 1

    return t

# Q5_2
def calc_somaPA(a1, an, r):
    n = calc_termosPA(a1, an, r)
    soma = ((a1 + an) * n)/2

    return soma	












	



