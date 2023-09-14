class Pessoa:
    def __init__(self, nome, idade, comendo=False, falando=False):
        self.nome = nome
        self.idade = idade
        self.comendo = comendo
        self.falando = falando
        
    def comer(self, alimento):
        if self.comendo == True:
            print(f'{self.nome} nao pode comer agora...')
        else:
            self.alimento = alimento
            print(f'comendo {self.alimento}!')
            self.comendo = True
        
    def parar_comer(self):
        if self.comendo == False:
            print(f'{self.nome} vai morrer de fome...')
        else:
            self.comendo = False

class Complex:
    def __init__(self, r=0, i=0):
        self.real = r
        self.imag = i

    def get_data(self):
        print(f'{self.real}+{self.imag}j')
