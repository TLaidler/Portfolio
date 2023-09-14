def matriz(M):
    L=[]
    for i in range(len(M)):
        for j in range(len(M[0])):
            if int(M[i][j])%2==0:
                L.append(M[i][j])
    print "Você tem "+str( len(L)) +" pares que são: ",str(L)
    print "A matriz analisada foi: "+str(M)
def main():
    M=input("Digite sua matriz: ")
    return matriz(M)

if __name__=="__main__":
    main()
    

#revisao matrizes slide:
def ma(M):
    s=[]
    for i in range(len(M)):
        s.append(sum(M[i]))
    print  max(s), M[s.index(max(s))]

    

        
        
            
        
    
