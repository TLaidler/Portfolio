#Prototipo#

def RPG():
    nome=input("Qual nome de seu personagem? ")
    raca=input("Qual sua raca entre humano, orc ou elfo?: ")
    raca=str.lower(raca)
    if raca=="orc":
        introd="Bem-vindo, caro orc "+ nome+". Gostariamos de saber qual sera a sua classe preferida? Tenha em mente que nao eh necessario se apegar as armas de sua classe de origem (mas elas terao dano maximo se forem)."
        print (introd)
        classe=input("Qual sua classe?: ")
        return "Boa escola caro, " + classe
    elif raca=="elfo":
        introd="Bem vindo majestade "+nome+", As florestas elficas precisam de sua ajuda mas primeiro voce precisa especificar sua classe de batalha! Tenha em mente que podes usar armas de diferentes classes mas seu dano sera total apenas em sua classe de origem."
        print (introd)
        classe=raw_input("Qual sua classe?: ")
        return "Otima escolha majestade... ou melhor dizendo, " + classe
    elif raca=="humano":
        introd="Bem vindo "+nome+" camarada! Precisamos de sua ajuda nos campos de batalha ao norte de Nahteru. Os orcs estao nos massacrando e os elfos nao parecem tao amistosos quanto antigamente... enfim, escolha sua classe para irmos logo a batalha! Tenha em mente que podes usar armas de diferentes classes mas seu dano sera total apenas em sua classe de origem!"
        print (introd)
        classe=raw_input("Qual sua classe?: ")
        return "Otima escolha "+ classe+ "! Agora junte-se a nos. Treine um pouco para nao morrer rapido demais... HAHAHA"
    else:
        return "Esta raca nao existe. Por favor escolha uma raca valida."
  
#############################################################

import cmd
import textwrap
import sys
import os
import time
import random

screen_width=100

def cls():  #call clear
	os.system('cls' if os.name=='nt' else 'clear')

##Player Setup##
class player:
    def __init__(self):
        self.name=''
        self.hp=0
        self.mp=0
        self.status_effects=[]
        self.location="start"
myPlayer=player()
 


######Tela inicial#########
def title_screen_selections():
    option=input("> ")
    if option.lower()==('jogar'):
        start_game()
    elif option.lower()==('ajuda'):
        help_menu()
    elif option.lower()==('sair'):
        sys.exit()
    while option.lower() not in ['jogar', 'ajuda' , 'sair']:
        print ("Por favor escolha uma opcao válida!")
        option=input("> ")
        if option.lower()==('Jogar'):
            start_game()
        elif option.lower()==('Ajuda'):
            help_menu()
        elif option.lower()==('Sair'):
            sys.exit()
        
       
def main():  #title_screen
    print ("#############################")
    print ("Bem-vindo à Dragons Fury!!")
    print ("#############################")
    print ("             ~Jogar~             ")
    print ("             ~Ajuda~             ")
    print ("             ~Sair~             ")
    title_screen_selections()

def help_menu():
    print ("###############")
    print ("     -Faca suas escolhas digitando-as!")
    print ("     -Este game tem uma historia propria dependendo de qual raca foi escolhida ")
    print ("      voce pode escolher o modo em que as historias irao terminar!")
    print ("O jogo eh apenas um pequeno projeto de um iniciante em programacao entao nao serao historias muito longas.")
    print ("Suas escolhas nao impactarao necessariamente o final das historias mas haverao situacoes diferentes com que voce ira enfrentar no meio do caminho (estas sim dependentes de suas escolhas)")
    print ("      -O sistema de batalha funciona como um RPG de mesa onde usa-se dados(ou seja, numeros aleatorios) somando-as com o status de seu personagem.")
    print("       -Podes escolher a classe que quiser mas se não existir dentro do jogo seu item inicial sera apenas equipamentos basicos: adaga inicial e armadura de couro.")
    print ("     -As classes existentes são: Guerreiro, Espadachim, Gladiador, Barbaro, Paladino, Arqueiro, Cacador, Ninja, Samurai, Lutador, Monge, Curandeiro, Mago, Bruxo, Feiticeiro, Mago, Druida, Xama, Sentinela, Guardiao")
    print (" Digite -DESCRICAO,EXAMINACAO, UP,DOWN, LEFT, RIGHT para interagir c o mapa")
    print ("      -Boa sorte e divirta-se!")
    print ("###############")
    title_screen_selections()

#Funcionalidades do game
def start_game():
     nome=input("Qual nome de seu personagem? ")
     raca=input("Qual sua raca entre humano, orc ou elfo?: ")
     raca=str.lower(raca)
     if raca=="orc":
         introd="Bem-vindo, caro orc "+ nome+". Gostariamos de saber qual sera a sua classe preferida? Tenha em mente que nao eh necessario se apegar as armas de sua classe de origem (mas elas terao dano maximo se forem)."
         print (introd)
         classe=input("Qual sua classe?: ")
         print ("Boa escola caro, " + classe)
         classe_armainicial(classe)         
     elif raca=="elfo":
         introd="Bem vindo majestade "+nome+", As florestas elficas precisam de sua ajuda mas primeiro voce precisa especificar sua classe de batalha! Tenha em mente que podes usar armas de diferentes classes mas seu dano sera total apenas em sua classe de origem."
         print (introd)
         classe=input("Qual sua classe?: ")
         print ("Otima escolha majestade... ou melhor dizendo, " + classe)
         classe_armainicial(classe)
     elif raca=="humano":
         introd="Bem vindo "+nome+" camarada! Precisamos de sua ajuda nos campos de batalha ao norte de Nahteru. Os orcs estao nos massacrando e os elfos nao parecem tao amistosos quanto antigamente... enfim, escolha sua classe para irmos logo a batalha! Tenha em mente que podes usar armas de diferentes classes mas seu dano sera total apenas em sua classe de origem!"
         print (introd)
         classe=input("Qual sua classe?: ")
         print ("Otima escolha "+ classe+ "! Agora junte-se a nos. Treine um pouco para nao morrer rapido demais... HAHAHA")
         classe_armainicial(classe)
     while raca not in ['orc', 'humano' , 'elfo']:
         print ("Por favor escolha uma opcao válida!")
         raca=input("Qual sua raca entre humano, orc ou elfo?: ")
         raca=str.lower(raca)
         if raca=="orc":
             introd="Bem-vindo, caro orc "+ nome+". Gostariamos de saber qual sera a sua classe preferida? Tenha em mente que nao eh necessario se apegar as armas de sua classe de origem (mas elas terao dano maximo se forem)."
             print (introd)
             classe=input("Qual sua classe?: ")
             print ("Boa escolha caro, " + classe)
             classe_armainicial(classe)
         elif raca=="elfo":
             introd="Bem vindo majestade "+nome+", As florestas elficas precisam de sua ajuda mas primeiro voce precisa especificar sua classe de batalha! Tenha em mente que podes usar armas de diferentes classes mas seu dano sera total apenas em sua classe de origem."
             print (introd)
             classe=input("Qual sua classe?: ")
             print ("Otima escolha majestade... ou melhor dizendo, " + classe)
             classe_armainicial(classe)
         elif raca=="humano":
             introd="Bem vindo "+nome+" camarada! Precisamos de sua ajuda nos campos de batalha ao norte de Nahteru. Os orcs estao nos massacrando e os elfos nao parecem tao amistosos quanto antigamente... enfim, escolha sua classe para irmos logo a batalha! Tenha em mente que podes usar armas de diferentes classes mas seu dano sera total apenas em sua classe de origem!"
             print (introd)
             classe=input("Qual sua classe?: ")
             print ("Otima escolha "+ classe+ "! Agora junte-se a nos. Treine um pouco para nao morrer rapido demais... HAHAHA")
             classe_armainicial(classe)
     print_location()   




def classe_armainicial(classe):
    if str.lower(classe) in ['guerreiro','espadachin','espadachim','gladiador','barbaro','paladino']:
        print ("Agora, ja que es "+classe+" voce vai receber inicialmente uma armadura media e uma -espada de ferro inicial!")
    elif str.lower(classe) in ['arqueiro','atirador','cacador']:
        print ("Agora, ja que es "+classe+" voce vai receber inicialmente uma armadura leve e um -arco simples inicial!")
    elif str.lower(classe) in ['ninja','samurai']:
        print ("Agora, ja que es "+classe+" voce vai receber inicialmente uma armadura media e uma -katana de ferro inicial!")
    elif str.lower(classe) in ['lutador','monje','monge']:
        print  ("Agora, ja que es "+classe+" voce vai receber inicialmente uma armadura media e uma -Luva de ferro pontiagudo inicial!")
    elif str.lower(classe) in ['curandeiro','mago','bruxo','healer','feiticeira','feiticeiro','maga','bruxa']:
        print ("Agora, ja que es "+classe+" voce vai receber inicialmente um chapéu leve de feitico e um -Cajado magico inicial!")
    elif str.lower(classe)in['druida','xama','sentinela','guardiao']:
        print ("Agora, ja que es "+classe+" voce vai receber inicialmente uma armadura media e um -machadinho de ferro inicial!")
    else:
        print ("Agora, ja que es "+classe+" voce vai receber inicialmente uma armadura de couro e uma -adaga inicial!")
    
    
###########Mapa##########
        #player starts at b2

ZONENAME=' '
DESCRICAO = 'descricao'
EXAMINACAO = 'examinar'
SOLVED=False
UP='up','norte','north','cima','norte'
DOWN='down','south','baixo','sul'
LEFT='left','west','esquerda','oeste'
RIGHT='right','east','direita','leste'

solved_places={'a1':False,'a2':False,'a3':False,'a4':False,
                     'b1':False,'b2':False,'b3':False,'b4':False,
                     'c1':False,'c2':False,'c3':False,'c4':False}
zonemap={
    'a1':{
        ZONENAME: "Zona de treinamento",
        DESCRICAO== 'Onde podes aprender como funciona o sistema de batalha e conseguir missoes extras'
        EXAMINACAO == 'Todos parecem muito focados em melhorar...'
        SOLVED=False
        UP=''
        DOWN='b1'
        LEFT=''
        RIGHT='a2'
        }
    'a2':{
        ZONENAME: "Rua 120-t",
        DESCRICAO = 'liga Zona de treinamento ao Quartel'
        EXAMINACAO = 'a rua parece a mesma de sempre'
        SOLVED=False
        UP=''
        DOWN='b2'
        LEFT='a1'
        RIGHT='a3'
        }
    'a3':{
        ZONENAME: "Quartel",
        DESCRICAO = 'Aqui onde o general do batalhao se encontra na maioria das vezes. Importantes missoes sao dadas aqui'
        EXAMINACAO = 'Aqui anda bem movimento...como sempre'
        SOLVED=False
        UP=''
        DOWN='b3'
        LEFT='a2'
        RIGHT='a4'
        }
    'a4':{
        ZONENAME: "Floresta",
        DESCRICAO = 'Uma floresta normal ao lado do quartel'
        EXAMINACAO = 'As arvores estao lindas essa epoca do ano...'
        SOLVED=False
        UP=''
        DOWN='b4'
        LEFT='a3'
        RIGHT=''
        }
    'b1':{
        ZONENAME: "",
        DESCRICAO = 'descricao'
        EXAMINACAO = 'examinar'
        SOLVED=False
        UP='a1'
        DOWN='c1'
        LEFT=''
        RIGHT='b2'
        }
    'b2':{
        ZONENAME: 'Casa',
        DESCRICAO = 'Aqui eh onde voce mora...por enquanto,'
        EXAMINACAO = 'Sua casa parece a mesma coisa de sempre'
        SOLVED=False
        UP='a2'
        DOWN='c2'
        LEFT='b1'
        RIGHT='b3'
        }
    'b3':{
        ZONENAME: "Vizinho",
        DESCRICAO = 'Nao conheco muito os vizinhos... mas parecem pessoas legais'
        EXAMINACAO = 'Examinar a casa dos outros eh meio...esquesito'
        SOLVED=False
        UP='a3'
        DOWN='c3'
        LEFT='b2'
        RIGHT='b4'
        }
    'b4':{
        ZONENAME: "Floresta",
        DESCRICAO = 'Uma floresta normal ao lado do quartel'
        EXAMINACAO = 'As arvores estao lindas essa epoca do ano...'
        SOLVED=False
        UP='a4'
        DOWN='c4'
        LEFT='b3'
        RIGHT=''
        }
    'c1':{
        ZONENAME: "Saida da cidade principal",
        DESCRICAO = 'Ao examinar aqui voce concorda em sair do local. Deseja mesmo sair?'
        EXAMINACAO = 'Saindo'
        SOLVED=False
        UP='b1'
        DOWN=''
        LEFT=''
        RIGHT='c2'
        }
    'c2':{
        ZONENAME: "Portoes da cidade",
        DESCRICAO = 'Aqui eh a entrada da cidade principal'
        EXAMINACAO = 'Os portoes sempre abertos. Parece mesmo perigoso...'
        SOLVED=False
        UP='b2'
        DOWN=''
        LEFT='c1'
        RIGHT='c3'
        }
    'c3':{
        ZONENAME: "Rua principal",
        DESCRICAO = 'O coracao da cidade'
        EXAMINACAO = 'Seu vizinho fica logo a cima, mais em cima ha o Quartel. A esquerda fica os portoes e mais a esquerda a saida da cidade. Esquerda e pra cima voce chega em casa. Duas esquerdas e duas cima voce chega na zona de treinamento!'
        SOLVED=False
        UP='b3'
        DOWN=''
        LEFT='c2'
        RIGHT='c4'
        }
    'c4':{
        ZONENAME: "Trilha para a floresta",
        DESCRICAO = 'A floresta esta logo a cima!'
        EXAMINACAO = 'Lugar bem calmo'
        SOLVED=False
        UP='b4'
        DOWN=''
        LEFT='c3'
        RIGHT=''
        }
    }
         



####Interatividade do Game########
def print_location():
    print ('\n'+('#'*(4+len(myPlayer.location))))
    print ('#' + myPlayer.location.upper()+'#')
    print ('#'+zonemap[myPlayer.location][DESCRICAO]+'#')
    print ('\n'+('#'*(4+len(myPlayer.location))))

def prompt():
    print ("\n"+"=======================")
    print ("Digite o que gostaria de fazer")
    action=input("> ")
    acceptable_actions=['mover','ir','viajar','inspecionar','interagir','descricao','olhar']
    while action.lower() not in acceptable_actions:
        print ("Acao desconhecida, tente novamente.\n")
        action=input("> ")
    if action.lower() == 'sair':
        sys.exit()
    elif action.lower() in ['mover','ir','viajar']:
        player_move(action.lower())
    elif action.lower() in ['inspecionar','interagir','descricao','olhar']:
        player_examine(action.lower())


def player_move(myAction):
    ask="Onde voce gostaria de ir? \n"
    dest=input(ask)
    if dest in ['up','norte','north','cima','norte']:
        destination=zonemap[myPlayer,location][UP]
        movement_handler(destination)
    elif dest in ['left','west','esquerda','oeste']:
        destination=zonemap[myPlayer.location][LEFT]
        movement_handler(destination)
    elif dest in ['down','south','baixo','sul']:
        destination=zonemap[myPlayer.location][DOWN]
        movement_handler(destination)
    elif dest in ['right','east','direita','leste']:
        destination=zonemap[myPlayer.location][RIGHT]
        movement_handler(destination)
    

def movement_handler(destination):
    print ("\n"+ "Voce se moveu para "+ destination)
    myPlayer.location=destination
    print_location()

def player_examine(action):
    if zonemap[myPlayer.location][SOLVED]==True:
        print ("Voce ja sabe tudo sobre aqui.")
    else:
        print ("Voce ainda pode fazer coisas por aqui.")

if __name__ == '__main__':
    main()
    
    

    

    


    
    










