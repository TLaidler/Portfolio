#!/usr/bin/env python3
import argparse

parser = argparse.ArgumentParser(description = 'Calcular a área de um terreno')
#adicionar os argumentos ao script. A ordem deles importa! help = ajuda com o codigo pro user
parser.add_argument('-l','--largura', type = int, help = 'largura do terreno') 
parser.add_argument('-c','--comprimento', type = int, help = 'comprimento do terreno')
args = parser.parse_args() #Pego os dados digitados e armazeno na variavel args

def area(larg,comp):
  a = larg*comp
  return a

if __name__=='__main__':
  print("A área do terreno é de %s metros quadrados" %area(args.largura,args.comprimento))
