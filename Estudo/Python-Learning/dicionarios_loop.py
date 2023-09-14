"""loops/lacos e dicionarios
"""

def main():

    dicio = {'a':3, 'b': 1, 'c': 'aulas', 'd': 40}

    #pelas chaves
    for key in dicio:
        print key
        
    print '\n' # pular linha
    #ou
    for key in dicio.keys():
        print key

    print '\n' # pular linha
    #pelos valores
    for value in dicio.values():
        print value

    print '\n' # pular linha
    #pelos items <chave-valor>
    for key, value in dicio.items():
        print key, value

    print '\n' # pular linha
    #ou
    for item in dicio.items():
        print item[0], item[1]

    print '\n' # pular linha
    

if __name__ == "__main__":
    main()
