#!/usr/bin/env python3
import argparse
from astropy import units as u
from astropy.coordinates import SkyCoord
import numpy as np
from astropy.visualization import astropy_mpl_style
import matplotlib.pyplot as plt
from astropy.coordinates.tests.utils import randomly_sample_sphere
from astropy.coordinates import EarthLocation
from astropy.time import Time
from astropy.coordinates import AltAz

parser = argparse.ArgumentParser(description = 'Identificar objeto digitado em ICSR para AltAz')
#adicionar os argumentos ao script. A ordem deles importa! help = ajuda com o codigo pro user
parser.add_argument('la', type = str, help = 'latitude') 
parser.add_argument('long', type = str, help = 'longitude')
parser.add_argument('alt', type = float, help = 'altitude')
parser.add_argument('name' , type = str, help = 'nome')
args = parser.parse_args() #Pego os dados digitados e armazeno na variavel args

def local(la,long,alt,name):
  obs = EarthLocation(lat= la, lon= long, height=alt*u.m)  #Localização terrestre do observador
  obj = EarthLocation.of_site(name) #localização do objeto 
  Azi = AltAz(location=obj)     #Coordenada mudada, mas falta o tempo
  Equa = 
  return Azi,Equa

if __name__=='__main__':
  print("A localização: .2%f .2%f" %local(args.la,args.long,args.alt,args.name))
