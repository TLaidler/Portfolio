##Revisao rapidinha
def convertor():
	n=int(input("Digite um numero."))
	b=int(input("Escolha a base o qual converter.\n(1) Binaria.\n(2) Octal.\n(3) Hexadecimal\n"))
	if (b==1):
		print("O numero {} em forma binaria eh {} \n".format(n,bin(n)[2:])) ##Recortando para nao aparecer as letras iniciais (b pra binario, x pra hexa...)
	elif (b==2):
		print("O numero {} em forma octal eh {} \n".format(n,oct(n)[2:]))
	elif (b==3):
		print("O numero {} em forma hexadecimal eh {} \n".format(n,hex(n)[2:]))
	else:
		print ("Opcao invalida.\n")
#cores
## \033[m  base das cores
##  \033[      m
##  \033[style,text,corfundo  m
## ex: \033[0;33;44m
# codigo stilo 0 = basicao
#codigo texto 33 basicao
# cor de fundo 44 = azul
##  style = 0 (none), 1 (bold) , 4(underline), 7(negative - inverte as cores de fundo e da letra)
## text = 30 (branco), 31(vermelho),32(verde),33(amarelo),34(azul),35(roxo),36(azul claro),37(cinza)
## back = 40(branco),41,42,43,44,45,46,47(cinza) --> mesma ordem de cor do text
##################Revisao over##########################

##mundo3-manuais de comando#############
c = ('\033[m',       # 0 = sem cores
 '\033[0;30;41m',    # 1 = vermelho
 '\033[0;30;42m',    # 2 = verde
 '\033[0;30;43m',    # 3 = amarelo
 '\033[0;30;40m'     # 4 = branco
 )


def ajuda(com):
	titulo('Acessando o manual do comando',2)
	print(c[4],end='')         ##end ==> uma forma de printar o ultimo caractere sem pular a linha
	help(com)

def titulo(msg,cor=0):
	tam=len(msg)
	print(c[cor],end='')
	print('~'*tam)
	print(msg)
	print('~'*tam)
	print(c[0],end='')


comando=''
while True:
	titulo('SISTEMA DE AJUDA',3)
	comando=str(input("Funcao ou Biblioteca > "))
	if comando.upper()=='FIM':
		break
	elif comando.upper()=='VTNC':
		print("Vai tomar no cu, escreve direito.\n Rode o programa mais uma vez, e ve se roda direito.")
		break
	else:
		ajuda(comando)
titulo ('FINALIZANDO PROGRAMA DE AJUDA',1)
