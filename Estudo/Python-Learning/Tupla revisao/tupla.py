palavras = ('programacao','nomes','legal','que bacana','yeaaah','astronomia')

for i in palavras:
    print(f"Na palavra {i} há as vogais", end=' ')
    for j in i:
        if j.lower() in ('aeiou'):
            print (f"{j}", end=',')
    print("\n")