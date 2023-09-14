class Produto:
    def __init__(self, nome, preco):
        self.nome = nome
        self.preco = preco

    def desconto(self, percent):
        self.preco = self.preco - (self.preco * (percent/100))
