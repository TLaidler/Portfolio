def nome():
	nome=raw_input("Digite seu nome para receber o numero de letras assim como sua primeira letra: ")
	nome2=nome.strip()
	nomesemesp=nome2.replace(" ","")
	inverter=nome2[::-1]
	return str(len(nomesemesp)) + " eh o numero de letras de teu nome e " + nome2[:1] + " eh a primeira letra!" + " Seu nome invertido eh: " + str(inverter) + ". As posicoes impares do nome dado sao: " + nome2[1::2]
