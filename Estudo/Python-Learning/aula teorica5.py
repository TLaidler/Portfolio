def tuplaum(a,b):
    return a / b , a%b
def tupladois(a,b):
    return b-a
def questao1(a):
   f=str.strip(a)
   lista=str.split(f)
   return len(lista)
def questao2(frase,word,i,j):
    ant=frase[0:i]
    inter=frase[i:j+1]
    pos=frase[j+1:]
    inter=str.repalce(inter,word,"")
    return ant+inter+pos


def matheus(a,b,c):
    d=a+b+c
    return d
#Refazer questões 1,2 e 3
def req1(str1):
    S=str(str1)
    A=S.split()
    B=len(A)
    return B
def req2(frase,palavra,pos1,pos2):
    W=frase[0:pos1]
    Q=frase[pos1:pos2+1]
    F=frase[pos2+1:]
    Q=str.replace(Q,palavra," ")
    return W+Q+F

#Teoria5
def teoria1(din,preco):
    quant=din/preco
    troco=din%preco
    return preco-troco
def teoria2(tupe):
    return tupe[0]==tupe[-1]
def teoria3(tup):
    b=len(tup)
    if b==3:
        return tup[::-1]
    else:
        return "Pode-se apenas ter 3 elementos"
def teoria4(list1,list2):
    L1=list(list1)
    L2=list(list2)
    return L1+L2
def teoria5(n):
    if n%2==0:
        return range(2,n+1,2)
    #para que conte o n caso ele seja par
    else:
        return range(2,n,2)






def prat1(frase):
    a=frase.split()
    b=len(a)
    return b

#Lista 6
def quest8(lista):
    L=list(lista)
    return max(L)

def quest9(notas):
    L=list(notas)
    a=len(L)
    b=sum(L)/a
    return b






































































