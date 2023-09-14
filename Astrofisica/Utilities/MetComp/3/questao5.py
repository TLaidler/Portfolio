#!/usr/bin/env python3
import argparse
import astropy
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz

parser = argparse.ArgumentParser(description = 'Receber as coordenadas de um observador. Altitude, Latitude, Longitude')

parser.add_argument('-lat', '--latitude', type = float, help = 'Latitude do observador')
parser.add_argument('-long','--longitude',type = float, help = 'Longitude do observador' )
parser.add_argument('-alt','--altitude',type = float, help = 'Altitude do observador')
parser.add_argument('-obg','--objeto',type = str, help = 'Nome do objeto')
args = parser.parse_args()

obj = SkyCoord.from_name(args.objeto)
coord = EarthLocation(lat=args.latitude*u.deg,lon=args.longitude*u.deg, height=args.altitude*u.n)
tempo = Time.now()
obj_agora = obj.transform_to(AltAz(location=coord, obstime=agora)) #agora = tempo?

print ("Localização dos Observadores: " + str(args.latitude)+','+str(args.longitude)+','+str(args.altitude)+'\n'+'Nome do Objeto: '+str(args.objeto)+'\n'+'Coordenadas:\n'+'Altazimutais: '+str(obj_agora.az)+','+str(obj_agora.alt)+'\n'+'Equatoriais: '+str(obj.ra)+','+str(obj.dec)
)
