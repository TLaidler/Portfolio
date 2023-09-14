import math
##Como tratar erros e exceçoes. Utilizar comando
#  try: (comandos errados) 
#  except: (oq ocorre se falhar) 
#  else: (caso nao de problema) 
#  finally: (ocorre independentemente doq ocorra)


def funcaoseila():
  a=int(input("Digite um numero: "))
  b=int(input("Digite outro numero: "))
  print (f"O resultado é {a/b}\n")

#nesse caso, uma exceção seria o usuario digitar b=0; ou digitar os numeros por extenso: 'oito'

try:
    n=int(input("Digite um numero: "))
    m=int(input("Digite outro: "))
    r=n/m                              ##tentei colocar n/m direto no print, mas o try nao acha o erro até que se calcule n/m.
except:       
    print("Houve um erro :/\n\n tente novamente\n\n")
else:
    print(f"O resultado é {round(r,2)}")
finally:
    print ("Obrigado por utilizar meu programa :)\n")

## No caso do except: 
## Podemos criar vários except diferentes para nos retornar alguma mensagem diferente dependendo do erro que ocorra. No caso, poderiamos ter uma msg que nos diga que divisão por 0 não existe e outra mensagem explicando que não aceita-se numeros por extenso.
# except (TypeError,ValueError):
#   print("!!!!Tivemos um problema com os tipos de dados digitados!!!!")
# except (ZeroDivisionError):
#   print ("Não se divide por zero animal!")
# except (KeyboardInterruption):
#   print("o usuario nao quis revelar os dados...")

# except Exception as erro:          Mostrando pro usuario qual erro.
#     print(f"O erro encontrado foi {erro.__cause__}")