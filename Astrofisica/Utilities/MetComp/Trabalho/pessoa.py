class Pessoa:
	def __init__(self, nome, cpf, idade):
		self.nome = nome
		self.cpf = cpf
		self.idade = idade
	def falar(self,dialogo):
		print('\n>'+self.nome+' diz: '+ dialogo)
	def despedir(self):
		print(f'{self.nome} diz:\n Tchaul...\n\n')

