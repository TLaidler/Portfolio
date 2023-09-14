class Gatos:
    """
    Uma classe simples de exemplo
    """
    
    def __init__(self):
        """
        Essa funcao ira rodar automaticamente assim 
        que voce instanciar um objeto
        """
        self.contador = 0
        
    def __str__(self):
        return 'Voce tem {} gatos'.format(self.contador)

    def add(self, n):
        """
        Funcao que adiciona um numero de gatos
        """
        from astropy.time import Time
        self.contador += n
        self.last_update = Time.now()