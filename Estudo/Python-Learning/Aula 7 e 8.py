#aula7

def ah():
    A=80000
    B=200000
    anos=0
    while A>=80000 and B>=200000:
        A=A +0.03*A
        B=B+ 0.015*B
        anos=anos+1
        if A==B:
            A<80000
            B<200000
            return anos


def aah(A,B,txA,txB):
    anos=0
    while A>0 and B>0:
        A=A+txA*A
        B=B+txB*B
        anos=anos+1
        if A==B:
            A<0
            B<0
            return anos

from random import randint

def aaah():
    dado1=randint(1,6)
    dado2=randint(1,6)
    vezes=0
    while dado1 != dado2:
        vezes=vezes+1
        dado1=randint(1,6)
        dado2=randint(1,6)
        if dado1==dado2:
         return vezes
        
