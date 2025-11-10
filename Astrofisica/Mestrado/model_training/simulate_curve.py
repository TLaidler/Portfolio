import numpy as np
import pandas as pd
import matplotlib.pylab as pl
import matplotlib.pyplot as plt
import random 
import time
import scipy.integrate as integrate
import pandas as pd 

### Simulador de Curva de Luz ###

ua = 149597870
ang_km = 1*10**-13
ano = 365*24*3600
mu0 = 1.256637061 * 10 ** -6 #N A**-2
ep0 = 8.854187817 * 10 **(-12) #C**2 N**-1 m**-2
c = 1/(mu0*ep0)**(1/2)
Cn2 = 1 

def calculo_magnitude(magnitude_absoluta, distancia): #em UA
    magnitude_aparente = magnitude_absoluta + 5*np.log10(distancia*(distancia-1))
    return(magnitude_aparente)

def Fluxo_lambda(magnitude):
    Fuxo=(10**(2.5*np.log10(3.44*(10**-12)))+(magnitude))**(1/2.5) #usando equação 20.9 kepler
    Fluxo = (3.69*10**-9)*(10**(magnitude))**(-1/2.5)
    return (Fluxo) #W/m2
# F V=0 3.44 * 10 ** - 8 J /m**2 s**-1 um**-1 === 1000 fotons cm**-2 s**-2 um**-1
#FLuxo 
print(Fluxo_lambda(0)) #W/m²

def Flux_lambda_ruido(magnitude):
    Fluxo=Fluxo_lambda(magnitude)
    tempo = 1
    area = 1
    cn15=integrate.quad(Cn2,0,np.inf)
    ir_saha=19.2*(600*10**-9)**(-7/6)*cn15[1]
    E0 = 3.6*10**-9 #W/m²
    E = (E0*10**(-0.4*magnitude))/tempo/area #W/cm²
    return(np.exp((np.log(E)+np.random.normal(0,ir_saha**(1/2)/area)*tempo)))

def fluxo_fotons(fluxo, lamb):
    h = 6.626196*10**-34 #m2kg/s
    c = 2.997924562*10**8 #m/s
    angstrons_m = 10**(-10) #
    fotons=fluxo*(lamb*angstrons_m)/(h*c)
    return(fotons)
print(fluxo_fotons(Fluxo_lambda(0),5500)/10**4)
print(10**6)
#fotons /m²/s

def diametro_angular(diametro, distancia): #unidades
    diametro_ang=(np.arctan(diametro/(distancia*ua)))*(360/(2*np.pi))*3600*1000
    return(diametro_ang) #segundo de arco

def Escala_placa(pixel, bin, dist_focal): #unidades
    escala_placa = 206265*pixel*bin/(1000*dist_focal)
    return escala_placa #segundo de arco/pixel

def tamanho_angular_corpo(diametro_angular,Escala_placa):
    tamanho = diametro_angular/Escala_placa
    return tamanho

#Exemplo:
ep = Escala_placa(5.86,1,100)
da = diametro_angular(6400,40)
print(tamanho_angular_corpo(da,ep))
#Incerteza de um photon-counting device que segue Estatistica de Poisson é sqrt(N), sendo N o número de fotons contados ToMeasuretheSky p.239

def soma_magnitude(mag1, mag2):
    magnitude_total = -2.5*np.log10(10**(-0.4*mag1)+10**(-0.4*mag2))
    return(magnitude_total)
    #https://www.astro.keele.ac.uk/jkt/pubs/JKTeq-fluxsum.pdf

print(soma_magnitude(21,20))

def fresnel_scale(lamb,dist):
    lamb = lamb*(10**-10)*micrometer_km
    dlamb = lamb*0.001
    dist = dist*ua
    fresnel_scale_1 = calc_fresnel(dist, lamb-dlamb/2.0)
    fresnel_scale_2 = calc_fresnel(dist, lamb+dlamb/2.0)
    fresnel_scale = (fresnel_scale_1 + fresnel_scale_2)/2.0
    return fresnel_scale



# https://www.youtube.com/watch?v=Bi2JWAHhBNg
def calc_fresnel(distance, bandpass):
    """Calculates the Fresnel scale.

    Fresnel Scale = square root of half the multiplication of wavelength and
    object distance.

    Parameters
    ----------
    distance : `int`, `float` array
        Distances, in km.

    bandpass : `int`, `float`, array
        Wavelength, in km.

    Returns
    -------
    fresnel_scale : `float`, array
        Fresnel scale, in km.
    """
    bandpass = bandpass*ang_km
    distance = distance*ua
    return np.sqrt(bandpass * distance / 2)


def bar_fresnel(X, X01, X02, opacity,distance,bandpass):
    """Returns the modelled light curve considering fresnel diffraction.

    Parameters
    ----------
    X : array
        Array with time values converted in km using the event velocity.

    X01 : `int`, `float`
        Immersion time converted in km using the event velocity.

    X02 `int`, `float`
        Emersion time converted in km using the event velocity.

    fresnel_scale : `int`, `float`
        Fresnel scale, in km.

    opacity : `int`, `float`
        Opacity. Opaque = 1.0, transparent = 0.0.

    Returns
    -------
    flux_fresnel : array
        The light curve with fresnel diffraction.
    """
    import scipy.special as scsp

    # Converting from km to units of fresnel scale
    fresnel_scale = calc_fresnel(distance,bandpass)
    x = X / fresnel_scale
    x01 = X01 / fresnel_scale
    x02 = X02 / fresnel_scale
    # Fresnel diffraction parameters
    x1 = x - x01
    x2 = x - x02
    s1, c1 = scsp.fresnel(x1)
    s2, c2 = scsp.fresnel(x2)
    cc = c1 - c2
    ss = s1 - s2
    r_ampli = - (cc + ss) * (opacity / 2.)
    i_ampli = (cc - ss) * (opacity / 2.)
    # Determining the flux considering fresnel diffraction
    flux_fresnel = (1.0 + r_ampli) ** 2 + i_ampli ** 2
    return flux_fresnel

if self.d_star > 0:
# Computing fresnel diffraction for the case where the star size is not negligenciable
    resolucao = (self.d_star/2)/npt_star
    flux_star_1 = np.zeros(len(time_model))
    flux_star_2 = np.zeros(len(time_model))
            # Computing stellar diameter only near the immersion or emersion times
    star_diam = (np.absolute(x - x01) < 3*self.d_star) + (np.absolute(x - x02) < 3*self.d_star)
    p = np.arange(-npt_star, npt_star)*resolucao
    coeff = np.sqrt(np.absolute((self.d_star/2)**2 - p**2))
    for ii in np.where(star_diam == True)[0]:
        xx = x[ii] + p
        flux1 = bar_fresnel(xx, x01, x02, fresnel_scale_1, opacity)
        flux2 = bar_fresnel(xx, x01, x02, fresnel_scale_2, opacity)
        flux_star_1[ii] = np.sum(coeff*flux1)/coeff.sum()
        flux_star_2[ii] = np.sum(coeff*flux2)/coeff.sum()
        flux_star[ii] = (flux_star_1[ii] + flux_star_2[ii])/2.
flux_inst = np.zeros(len(time_obs))

def ka(band):
    k=2*np.pi/band
    return k

#band = 6000 *10**-9

#print(k)
#L=20000
#diam_teles=1.6

aaf = (1+1.07*(((k*(diam_teles/100))**2)/(4*L))**(7/6))**(-1)

#mag_star = 21
#mag_obj = 20
#queda = (mag_star-mag_obj) + 2.5 * (np.log10(10**((mag_star-mag_obj)/2.5)+1))
#ou
#queda2 = 2.5*(np.log10(10**(mag_obj-mag_star)/2.5)+1)
#print(queda)
#print(queda2)

#fluxo_estrela = 10**(mag_star/2.5)
#fluxo_obj = 10**(mag_obj/2.5)
#dif_mag1 = -2.5 * np.log10(fluxo_estrela/fluxo_obj) + 2.5 * np.log10((fluxo_estrela + fluxo_obj) / fluxo_obj)
#dif_mag2 = 2.5 * np.log10((fluxo_estrela + fluxo_obj) / fluxo_estrela)
#print(dif_mag1)
#print(dif_mag2)
	
#aux = (mag_star-mag_obj) * 0.4
#contraste
#contr = 1 / (10**(aux)+1)
#soma_mag = mag_star - (2.5*(np.log10(1/contr)))
#queda_mag = mag_obj - mag_star
#aux = (soma_mag - mag_obj) * 0.4
#botton_flux = 10**(aux)
#print(soma_mag)
#print(queda_mag)
#print(aux)
#print(botton_flux)

#def Fluxo_de_fotons_Observado:
#    Fluxo_observado=*integral*fluxo_fotons*transmissao_atmosferica*eficiencia_telescopio*eficiencia_instrumento*eficiencia_filtro*eficiencia_detector*dlambda
#    Fluxo_deFotons_observado=Area_telescopio*tempo_integracao*Fluxo_observado

#numero de bits da câmera, limita o numero máximo de contagem que a ccd pode obter ...
#ADU = 2^numero de bits-1
#Ganho X eletrons por ADU resultando na capacidade total de pixels da ccd

#ARRUMAR para latitude
def posicao_corda(diametro_objeto, latitude):
    corda_corpo = diametro_objeto*np.cos(latitude)
    inicio = -corda_corpo/2
    fim = corda_corpo/2
    return(corda_corpo)


#ti = 0.1
#k = 2*np.pi/(5500*10**-10)
#L = 1
#area_teles = area_telescopio/10000
#f = Fluxo_lambda(0)
#var_log_amplitude = 0.124* (k/10) ** (7/6) * (L) ** (11/6) * Cn2 #tyson 2.31 
#aaf = (1+1.07*((k*(4*(area_teles)/(np.pi)))/(4*L))**(7/6))**(-1)
#var_irradi = aaf * (np.exp(4 * (var_log_amplitude))-1) #2.33
#ira = (np.random.normal(0,var_irradi**(1/2)))
#print("Fluxo")
#print(f)
#print("var_log")
#print(var_log_amplitude**(1/2))
#print("var ampli 10")
#print(np.log10(var_log_amplitude))
#print("var ampli e")
#print(np.log(var_log_amplitude))
#print("var_irradi")
#print(var_irradi)
#print("Ira")
#print(ira)
#ir = f+(ira)
#print("ir")
#print(ir)
#n_fotons = fluxo_fotons(ir,5500)*area_teles
#print("n_fotons")
#print(n_fotons)
#print("fotons")
#print(fluxo_fotons(f,5500)*area_teles)
#print((4*10**6)*10**(0/2.5)*10**4)
#print(fluxo_fotons(f,6500)*area_teles)

def Cnh2(h):
    Cn2 = A * np.exp(-h/Ha) + B * np.exp(-h/Hb) + C * (h**(10)) * np.exp(-h/Hc) + D *np.exp((-(h-Hd)**2)/2*d*d)
    cn2=Cn2
    return cn2
def Cn22(h):
    Cn2 = A * np.exp(-h/Ha) + B * np.exp(-h/Hb) + C * (h**(10)) * np.exp(-h/Hc) + D *np.exp((-(h-Hd)**2)/2*d*d)
    cn2=Cn2*h**(5/6)
    return cn2
def Cn22h(h):
    Cn2h = A * np.exp(-h/Ha) + B * np.exp(-h/Hb) + C * (h**(10)) * np.exp(-h/Hc) + D *np.exp((-(h-Hd)**2)/2*d*d)
    cn2h = Cn2h*h**(5/3)
    return cn2h

#print(var_log_amplitude)
##var_log = integrate.quad(Cn22,0,20000)
#intensity = 19.2*banda**(-7/6)
#print(var_log[0]*intensity)

############ FASE OK
#f = Fluxo_lambda(18)
#banda = 5000
#area_telescopio = np.pi*30**2 #CM²
#ti = 1
#g=fluxo_fotons(f,banda)*area_telescopio
#maxim=0

def erro_fase(f,var_fase):
    factor = 1
    #n_fotons = fluxo_fotons(f,banda)*area_telescopio*ti
    if f > 20000:
        factor= f / 20000
        f = 20000
        #print("Por questão de tempo coomputacional será realizada uma aproximação no número de fótons")
    x = f/2
    if f < 1:
        factor = 2
        f = 1
    desv_pad_fase = var_fase**(1/2)
    total = 0
    

    maxim = np.arange(0,x,factor)
   # print(maxim)
    if maxim ==[0]:
        return 0
    for i in (maxim):
        j1 = (np.sin(np.random.normal(0, desv_pad_fase)))
        j2 = (np.sin(np.random.normal(0, desv_pad_fase)))
        if j1+j2 > 0.5 or j1+j2 <-0.5:
            total += 2
        else:
            total = total

    return total*factor
#erro_fase(g,5000)    
#print(int(sum(arranjo)))
#print(int(np.random.normal(n_fotons, var_fase**(1/2))))
#for i in arranjo:
#    if arranjo[i] + arranjo [i+1] > 0.5 or arranjo[i] + arranjo[i+1] < -0.5:
#        total = total+2
#    i = i+2
#print(total*factor)


def contagem_fluxo(tempo_atual, mag_obj, mag_star, area_telescopio
, tempo_exposicao, banda, inicio, fim):
   # mag_star = mag_star #combinar com mag obj
    
   #
    ti = tempo_exposicao/100
    t = 0
    fluxo_total = 0
    while t < tempo_exposicao:
        #verifica posição objeto
        posicao = tempo_atual
        if posicao >= inicio and posicao <= fim:
            magnitude = mag_obj
           # print("dentro if 1")
        else:
            magnitude = soma_magnitude(mag_star,mag_obj)
           # print("dentro else 1")
        f = Fluxo_lambda(magnitude)
       # print(f)
        #var_log_amplitude = 0.307* k ** (7/6) * L ** (11/6) * Cn2 #tyson 2.31 
        #aaf = (1+1.07*(k*(area_telescopio/(4*np.pi))/(4*L))**(7/6))**(-1)
        #var_irradi = aaf * (np.exp(4 * (var_log_amplitude))-1) #2.33
        #ira = (np.random.normal(0,var_irradi**(1/2)))*ti
        #ir = f+abs(ira)
        n_fotons = fluxo_fotons(f,banda)*area_telescopio*ti 
       # print(n_fotons)
      #  photons = np.random.poisson(ruido_termico(270,n_fotons,ti))
        #arranjo = list()
        #for i in ((np.arange(0,n_fotons,1))):
        #    arranjo.append(1)
        #p=0
        #for i in arranjo:
        #    fase = (np.random.normal(0, var_fase**(1/2)))
        #    j = ((i/i+np.sin(fase)))    
        #    arranjo[p] = j
        #    p+=1
        f = Flux_lambda_ruido(magnitude,area_telescopio)
        #print(f)
        #f = Fluxo_lambda(magnitude)
        fluxo_total=f
        #fluxo_total += np.random.normal(fluxo_fotons(f,banda),var_irradi**(1/2))*area_telescopio*ti #+ fluxo_fotons(f, banda)*ti#*area_telescopio
        #fluxo_total = fluxo_total#/2 
        
        if fluxo_total < 0:
            fluxo_total = 0 #abs(fluxo_total)
        fluxo_total = fluxo_fotons(fluxo_total,banda)
        t += ti
        tempo_atual += ti
    return(fluxo_total)

        #fluxo_total += n_fotons #+ int(sum(arranjo))*ti  #fluxo_fotons(f, banda)*area_telescopio*ti
        #t += ti
        #tempo_atual += ti
       #
       #  print(fluxo_total)
    #### INSERIR O NUMERO DE FÓTONS E O TEMPO EM UMA TABELA
    #return(int(fluxo_total))

def contagem_fluxo_anel(tempo_atual, mag_obj, mag_star, area_telescopio
, tempo_exposicao, banda, inicio, fim, prof_otica, inicio_anel1, fim_anel1
,inicio_anel2, fim_anel2):
   # mag_star = mag_star #combinar com mag obj
    
   #
    ti = tempo_exposicao/20
    t = 0
    fluxo_total = 0
    while t < tempo_exposicao:
        #verifica posição objeto
        posicao = tempo_atual
        if posicao >= inicio and posicao <= fim:
            magnitude = mag_obj
        elif posicao >= inicio_anel1 and posicao <= fim_anel1:
            magnitude = soma_magnitude((mag_star+mag_star * prof_otica), mag_obj) 
        elif posicao >= inicio_anel2 and posicao <= fim_anel2:
            magnitude = soma_magnitude(mag_obj, (mag_star+mag_star*prof_otica))
        else:
            magnitude = soma_magnitude(mag_star,mag_obj)
        f = Fluxo_lambda(magnitude)
        fluxo_total += fluxo_fotons(f, banda)*area_telescopio*ti
        t += ti
        tempo_atual += ti
    return(fluxo_total)

def contagem_fluxo_anel_satelite(tempo_atual, mag_obj, mag_star,mag_sat, area_telescopio
, tempo_exposicao, banda, inicio, fim, prof_otica, inicio_anel1, fim_anel1
,inicio_anel2, fim_anel2,inicio_sat,fim_sat):
   # mag_star = mag_star #combinar com mag obj
    mag_anel = mag_star-2.5*np.log(np.exp(-prof_otica))
   #
    ti = tempo_exposicao/100
    t = 0
    fluxo_total = 0
    while t < tempo_exposicao:
        #verifica posição objeto
        posicao = tempo_atual
        if posicao >= inicio and posicao <= fim:
            magnitude = soma_magnitude(mag_obj,mag_sat)
        elif posicao >= inicio_anel1 and posicao <= fim_anel1:
            magnitude1 = soma_magnitude(mag_sat,mag_obj)
            magnitude = soma_magnitude((mag_anel), magnitude1) 
        elif posicao >= inicio_anel2 and posicao <= fim_anel2:
            magnitude1 = soma_magnitude(mag_sat,mag_obj)
            magnitude = soma_magnitude(magnitude1, mag_anel)
        elif posicao >= inicio_sat and posicao <= fim_sat:
            magnitude = soma_magnitude(mag_sat, mag_obj) 
        else:
            magnitude1 = soma_magnitude(mag_star,mag_obj)
            magnitude = soma_magnitude(magnitude1,mag_sat)
        f = Flux_lambda_ruido(magnitude)
        #f = Fluxo_lambda(magnitude)
        fluxo_total=f
         #+ fluxo_fotons(f, banda)*ti
        #fluxo_total = fluxo_total#/2 
        
        if fluxo_total < 0:
            fluxo_total = 0 #abs(fluxo_total)
        fluxo_total == fluxo_fotons(fluxo_total,banda)*ti*area_telescopio
        #fluxo_total += fluxo_total*np.random.normal(fluxo_total,var_irradi**(1/2))
        t += ti
        tempo_atual += ti
    return(fluxo_total)

def contagem_fluxo_satelite(tempo_atual, mag_obj, mag_star, mag_sat, area_telescopio
, tempo_exposicao, banda, inicio, fim, inicio_sat, fim_sat):
   # mag_star = mag_star #combinar com mag obj
    
   #
    ti = tempo_exposicao/20
    t = 0
    fluxo_total = 0
    while t < tempo_exposicao:
        #verifica posição objeto
        posicao = tempo_atual
        if posicao >= inicio and posicao <= fim:
            magnitude = soma_magnitude(mag_sat, mag_obj)
        elif posicao >= inicio_sat and posicao <= fim_sat:
            magnitude = soma_magnitude(mag_sat, mag_obj) 
        else:
            magnitude1 = soma_magnitude(mag_star,mag_obj)
            magnitude = soma_magnitude(mag_sat,magnitude1)
        f = Fluxo_lambda(magnitude)
        fluxo_total += fluxo_fotons(f, banda)*ti*area_telescopio
        t += ti
        tempo_atual += ti
    return(fluxo_total)

def contagem_fluxo_ceu(tempo_atual, area_telescopio, tempo_exposicao, banda, inicio, fim):
   # mag_star = mag_star #combinar com mag obj
    ti = tempo_exposicao/20
    t = 0
    fluxo_total = 0
    while t < tempo_exposicao:
        #verifica posição objeto
        if banda < 4050 and banda >= 2000: #3700
            magnitude = 23.2
        if banda >= 4050 and banda < 4950: #4400
            magnitude = 23.4
        if banda >= 4950 and banda < 5950: #5500
            magnitude = 22.7
        if banda >= 5950 and banda < 7200: #6400 
            magnitude = 22.2
        if banda >= 7200 and banda < 10000: #8000
            magnitude = 22.2
        if banda >= 10000 and banda < 14000: #12000
            magnitude = 20.7
        if banda >= 14000 and banda < 19000: #16000
            magnitude = 20.9
        if banda >= 19000 and banda < 25000: #22000
            magnitude = 21.3
        f = Fluxo_lambda(magnitude)
        fluxo_total += fluxo_fotons(f, banda)*area_telescopio*ti
        t += ti
        tempo_atual += ti
    return(fluxo_total)

#S/N
def signalNoise():
    N = 1#numero de fótons coletados
    npix = 1 #numero de pixels levados em consideração para o S/N 
    Ns = 1 #Número de fótons por pixel do fundo de céu
    Nd = 1 #Número de eletrons de dark current 
    Nr = 1 #Número de eletrons por pixel resultante do ruido de leitura
    return N

#cintilação

def cintilacao(velocidade_vento_chao, altitude, tempo):
   
    result,error = integrate.quad(vel_vento, 5000, 20000, args=(altitude, velocidade_vento_chao))
    
    w=1/15*result
    A=np.exp(random.gauss(altitude, tempo))
    print("O resultado de A é " + str(A))
    cintila = A*(2.2*10**(-53)*(altitude**10)*(w/27)**2*np.exp(-altitude/1000)+1*10**-16*np.exp(-altitude/1500))
    return cintila
####

####seeing 17_08
#tabela 3.1 hardy para referencia dos números
seeing = 2.5#(1.22*500*10**-9)/0.05
h = 4213 
L_prop = 20000 #m
dist_raios = 10 # distancia entre dois raios paralelos que passam pela atmosfera e geram uma diferença de fase deltafi
L=20000
if seeing >= 1.88:
    seeing = 2.5
    print("O valor do seeing utilizado será de {:.2f} para se adaptar ao modelo de turbulência" .format(seeing))
    A = 17 * 10 ** -15
    Ha = 100
    B = 27 * 10 ** -17
    Hb = 1500
    C = 3.59 * 10 ** -53 
    Hc = 1000
    D = 0
    Hd = 0
    r0 = 0.05
elif seeing < 1.88 and seeing >= 1.205:
    seeing = 1.26
    print("O valor do seeing utilizado será de {:.2f} para se adaptar ao modelo de turbulência" .format(seeing))
    A = 4.5 * 10 ** -15
    Ha = 100
    B = 9 * 10 ** -17
    Hb = 1500
    C = 2 * 10 ** -53 
    Hc = 1000
    D = 0
    Hd = 0
    r0 = 0.1
elif seeing < 1.205 and seeing >= 0.995:
    seeing = 1.15
    print("O valor do seeing utilizado será de {:.2f} para se adaptar ao modelo de turbulência" .format(seeing))
    A = 0
    Ha = 1
    B = 27 * 10 ** -17
    Hb = 1500
    C = 5.94 * 10 ** -53 
    Hc = 1000
    D = 0
    Hd = 0
    r0 = 0.11
elif seeing < 0.995 and seeing >= 0.685:
    seeing = 0.84
    print("O valor do seeing utilizado será de {:.2f} para se adaptar ao modelo de turbulência" .format(seeing))
    A = 2 * 10 ** -15
    Ha = 100
    B = 7 * 10 ** -17
    Hb = 1500
    C = 1.54 * 10 ** -53 
    Hc = 1000
    D = 0
    Hd = 0
    r0 = 0.15
elif seeing < 0.685 and seeing >= 0.445:
    seeing = 0.53
    print("O valor do seeing utilizado será de {:.2f} para se adaptar ao modelo de turbulência" .format(seeing))
    A = 0
    Ha = 1
    B = 1 * 10 ** -17
    Hb = 3000
    C = 1.63 * 10 ** -53 
    Hc = 1000
    D = 1
    Hd = 6500
    r0 = 0.24
elif seeing < 0.445:
    seeing = 0.36
    print("O valor do seeing utilizado será de {:.2f} para se adaptar ao modelo de turbulência" .format(seeing))
    A = 0
    Ha = 1
    B = 1 * 10 ** -17
    Hb = 3000
    C = 1.63 * 10 ** -53 
    Hc = 1000
    D = 0
    Hd = 0
    r0 = 0.34
else:
    print("erro")

#k = 2 * np.pi / (0.55 * 10 **-6)

#deltafi = k*d*deltaN(d) #deltaN é a variação no indice de refração
d = ((np.pi**2)/(np.pi*np.pi*Cn2*L))**(3/5) # espessura da camada de ar responsável pelos efeitos
print(d)
Cn2 = A * np.exp(-h/Ha) + B * np.exp(-h/Hb) + C * (h**(10)) * np.exp(-h/Hc) + D *np.exp((-(h-Hd)**2)/2*dist_raios*dist_raios)
cn10 = integrate.quad(Cnh2,-np.inf,np.inf)
cn11=integrate.quad(Cn22,0,np.inf)
cn12=integrate.quad(Cn22h,-np.inf,np.inf)
#L=(cn12[0]/cn10[0])**(3/5)*100 #5.137 saha
print(Cn2)
print(L)

print(cn11[0])
print(cn10)
print(cn12)
#valido para l0<dist_raios<L0
k=ka(band)
D0 = 1.46 * k ** 2 * Cn2 * L * dist_raios **(5/3)
print(D0)
s2 = seeing *180*60*60/np.pi
print(seeing)
print(s2)

# contar fotons em área equivalente ao telescopio, aplicar a variancia de fase em cada fóton e com base 
#nisso fazer dois fótons interagirem e assim incluir o ruído

#diam_teles = 1.6 #m
#k = 2 * np.pi/ (600*10**-9) #/m

var_fase = 0.134 * (diam_teles/r0) ** (5/3) #2.62 tyson
#var_log_amplitude = 0.124* (k ** (7/6)) * (L_prop ** (11/6) )* Cn2 #2.31 tyson

# a is an aperture-averaging factor
a = (1 + 1.07 * ((k * (diam_teles**2))/(4 * L_prop))**(7/6))**-1
#print(a)

#print(var_fase)
#print("log_amp " + str(var_log_amplitude))

cn15=integrate.quad(Cn22,0,np.inf)
ir_saha=((19.2*band*(10**-9))**(-7/6))*cn15[0]
#print("variancia log intensidade " + str(ir_saha**(1/2))) #Saha 5.139

var_irradi = a * (np.exp(4 * (ir_saha))-1)
print(var_fase)

#print(cn15)


hp=6.62*10**-34 #m²kg/s
#mag_star = 14.83
#print(np.random.normal(0,var_fase**(1/2))) #DIVIDIR POR PI E VERIFICAR SE OCORRE INTERFERENCIA DESTRUTIVA OU CONSTRUTIVA
#print(np.random.normal(0,var_log_amplitude**(1/2)))
#tempexp = 0.44 #s
#compri_onda = 600*10**-9 #m
print(band)
print(tempexp)
ampli = (2*hp/(((band*10**-9)**2) * ep0 * tempexp))**(1/2)
print("a amplitudo vale " + str(ampli))
print(ir_saha)
amp = np.random.normal(np.log(ampli),ir_saha**(1/2))#var_log_amplitude**(1/2))
print(amp)
print(np.exp(amp))

print("A amplitude ficou: "+ str(np.exp(amp)))
#intesit = ((c*ep0*(np.exp(ampli))**2)/2)/10000/tempo
intesity = ((c*ep0*(np.exp(amp))**2)/2)/tempexp/10000 #W/cm²
E0 = 3.6*10**-9 #W/m²
E = (E0*10**(-0.4*mag_star))/tempexp/(np.pi*(diam_teles/2)**2) #W/cm²
#E2=(hp*c/compri_onda)/tempo/(np.pi*(diam_teles/2)**2) #W/cm²
print("A irradiancia é: " + str (E))
#print("A irradiancia 2 é: " + str (E2))
#print("o valor da intensidade é de " + str(intesit))
print("o valor da intensidade variada é de " + str(intesity))
ira = np.random.normal(0,(var_irradi**(1/2))/np.pi*(diam_teles/2)**2)
print("o valor da variancia da irradiancia e " + str (ira*tempexp))
irad = np.random.normal(0,(var_irradi**(1/2))/np.pi*(diam_teles/2)**2)
print("o valor da variancia da irradiancia e " + str (irad*tempexp))

print(np.exp((np.log(E)+np.random.normal(0,ir_saha**(1/2)/np.pi*(diam_teles/2)**2)*tempexp)))

def ruido_termico(Temperatura, numero_pixel, tempo_exp):
    Eg = 1.1557 - (7.021 * 10 **(-4)*Temperatura**2/(1108+Temperatura))
    Tx = 5.86*(10**9)*(Temperatura**(2/8))*np.exp(-(Eg)/(2*(1.23*10**-4)*Temperatura)) # k = 1.23*10**-4 obtido em testes para seguir a relação da literatura
    sig_dark = (Tx*numero_pixel*tempo_exp)**(1/2)
    return sig_dark
print(np.random.poisson(ruido_termico(300,10,4)))

def ruido_leitura(ruido):
    rui_leit=np.random.normal(0,ruido)
    return rui_leit
print(ruido_leitura(2.5))

#Definindo Dados:
flua = []
vel = 30 #[30,31,32]
tmini = 0
temp = tmini
tmaxi = 4000
mag_star = 19 #magnitudes_estrelas = [12,19,21]
mag_obj = 20 #[19 20 25]
distancia = 300 #[240, 300, 520]
magi_sat = -1.25 #Triton -1.25 Miranda 3.49
mag_sat = calculo_magnitude(magi_sat, distancia)
#mag_sat = 25.1
diametro_sat = 2700 #Triton 2700 Miranda 500
distancia_sat = 60000 #Triton 60000 Miranda 250000
diametro_estrela = 1.33 #[0.98, 7.84]
diam_teles = 500 # cm
foco = 1.8 #F
ep = 0.7 #arcsec?
#ep = Escala_placa(13,1,16000)
bina = 1
gain = 0.8
readout_noise = 2.5
temperatura = 215

area_telescopio = np.pi*(diam_teles)**2 #cm²
tempexp = 0.01 #[300, 100, 50, 10, 1]
band = 6200 #[5000, 5500, 6000, 6500, 7000]
diametro_corpo = 19548 #km [18432, 19548, 20665]
centro_ocultacao =  2000 #Triton 2800 miranda 50
inicio = centro_ocultacao - diametro_corpo/vel/2
fim = centro_ocultacao + diametro_corpo/vel/2
cyc = tempexp+0.001#tempexp + 0.01
times = np.arange(tmini, tmaxi, cyc)
Xs = np.arange(tmini*vel,tmaxi*vel,cyc*vel)
X01 = inicio*vel
X02 = fim*vel
#https://arxiv.org/ftp/arxiv/papers/1805/1805.08963.pdf#:~:text=Uranus%20rings%20are%20dense%2C%20made,range%20between%200.1%20and%201.
#https://arxiv.org/pdf/1906.11728.pdf
prof_otica = 0.1 #10-4 a 0.1 (netuno) (0.003 Lassell ring), 0.1 a 1 Urano  [0.0001, 0.003, 0.1, 0.5, 1]
diametro_anel = 51000 #[40900, 53200, 51000, 42000, 37800]
espessura_anel = 10 #[2000, 100, 20, 2, 3500]
inicio_anel1 = centro_ocultacao - diametro_anel/vel/2 - espessura_anel/vel/2
fim_anel1 = centro_ocultacao - diametro_anel/vel/2 + espessura_anel/vel/2
#inicio_anel2 = centro_ocultacao + diametro_anel/vel/2 - espessura_anel/vel/2
#fim_anel2 = centro_ocultacao + diametro_anel/vel/2 + espessura_anel/vel/2
X01_an = inicio_anel1*vel
X02_an = fim_anel1*vel
#X03_an = inicio_anel2*vel
#X04_an = fim_anel2*vel
inicio_sat = centro_ocultacao - distancia_sat/vel/2 - diametro_sat/vel/2
fim_sat = centro_ocultacao - distancia_sat/vel/2 + diametro_sat/vel/2
X01_sat = inicio_sat*vel
X02_sat = fim_sat*vel
print(inicio_sat)
print(fim_sat)
print(inicio_anel1)
print(fim_anel1)
print(inicio)
print(fim)

#prof_otica = 
#print(prof_otica)
#prof_otica = -np.log(1-prof_otica)
#print(prof_otica)
#print(soma_magnitude(mag_obj, (mag_star+mag_star*prof_otica)))
#print(mag_obj)
#print(mag_star)
#print(soma_magnitude(mag_star,mag_obj))
prof_otica2 = 0.1 #10-4 a 0.1 (netuno) (0.003 Lassell ring), 0.1 a 1 Urano  [0.0001, 0.003, 0.1, 0.5, 1]
diametro_anel2 = 51000
espessura_anel2 =20
inicio_anel2 = centro_ocultacao + diametro_anel2/vel/2 - espessura_anel2/vel/2
fim_anel2 = centro_ocultacao + diametro_anel2/vel/2 + espessura_anel2/vel/2

prof_otica3 = 0.0000026
diametro_anel3 = 799000.8
espessura_anel3 = 76.4
inicio_anel3 = centro_ocultacao - diametro_anel3/vel/2 - espessura_anel3/vel/2
fim_anel3 = centro_ocultacao - diametro_anel3/vel/2 + espessura_anel3/vel/2

prof_otica4 = 0.0000353
diametro_anel4 = 824600.22
espessura_anel4 = 5.3
inicio_anel4 = centro_ocultacao + diametro_anel4/vel/2 - espessura_anel4/vel/2
fim_anel4 = centro_ocultacao + diametro_anel4/vel/2 + espessura_anel4/vel/2

X03_an = inicio_anel2*vel
X04_an = fim_anel2*vel
X05_an = inicio_anel3*vel
X06_an = fim_anel3*vel
X07_an = inicio_anel4*vel
X08_an = fim_anel4*vel

def contagem_fluxo_anel2(tempo_atual, mag_obj, mag_star, area_telescopio
, tempo_exposicao, banda, inicio, fim, prof_otica,prof_otica2, prof_otica3,prof_otica4, inicio_anel1, fim_anel1
,inicio_anel2, fim_anel2,inicio_anel3, fim_anel3
,inicio_anel4, fim_anel4):
   # mag_star = mag_star #combinar com mag obj
    mag_anel = mag_star-2.5*np.log(np.exp(-prof_otica))
    mag_anel2 = mag_star-2.5*np.log(np.exp(-prof_otica2))
    mag_anel3 = mag_star-2.5*np.log(np.exp(-prof_otica3))
    mag_anel4 = mag_star-2.5*np.log(np.exp(-prof_otica4))
   #
    ti = tempo_exposicao/100
    t = 0
    fluxo_total = 0
    while t < tempo_exposicao:
        #verifica posição objeto
        posicao = tempo_atual
        if posicao >= inicio and posicao <= fim:
            magnitude = mag_obj
        elif posicao >= inicio_anel1 and posicao <= fim_anel1:
            magnitude1 = mag_obj

            magnitude = soma_magnitude((mag_anel), magnitude1) 
        elif posicao >= inicio_anel2 and posicao <= fim_anel2:
            magnitude1 = mag_obj
            magnitude = soma_magnitude((mag_anel2), magnitude1) 
        elif posicao >= inicio_anel3 and posicao <= fim_anel3:
            magnitude1 = mag_obj
            magnitude = soma_magnitude((mag_anel3), magnitude1)  
        elif posicao >= inicio_anel4 and posicao <= fim_anel4:
            magnitude1 = mag_obj
            magnitude = soma_magnitude((mag_anel4), magnitude1) 
        else:
            magnitude = soma_magnitude(mag_star,mag_obj)
            
        f = Flux_lambda_ruido(magnitude)
        #f = Fluxo_lambda(magnitude)
        fluxo_total=f
         #+ fluxo_fotons(f, banda)*ti
        #fluxo_total = fluxo_total#/2 
        
        if fluxo_total < 0:
            fluxo_total = 0 #abs(fluxo_total)
        fluxo_total == fluxo_fotons(fluxo_total,banda)*ti*area_telescopio
        fluxo_total += fluxo_total*np.random.normal(fluxo_total,var_irradi**(1/2))*5
        t += ti
        tempo_atual += ti
    return(fluxo_total)

calc_fresnel(distancia,band)

Fres_sat=bar_fresnel(Xs,X01_sat,X02_sat,1,distancia,band)

plt.plot(times,Fres_sat, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo ")
plt.xlabel('Tempo [segundos]')

Fres_an1=bar_fresnel(Xs,X01_an,X02_an,prof_otica,distancia,band)
plt.plot(times,Fres_an1, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo ")
plt.xlabel('Tempo [segundos]')

Fres_an2=bar_fresnel(Xs,X03_an,X04_an,prof_otica2,distancia,band)
plt.plot(times,Fres_an2, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo ")
plt.xlabel('Tempo [segundos]')

Fres_an3=bar_fresnel(Xs,X05_an,X06_an,prof_otica3,distancia,band)
plt.plot(times,Fres_an1, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo ")
plt.xlabel('Tempo [segundos]')

Fres_an4=bar_fresnel(Xs,X07_an,X08_an,prof_otica4,distancia,band)
plt.plot(times,Fres_an1, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo ")
plt.xlabel('Tempo [segundos]')

Fres=bar_fresnel(Xs,X01,X02,1,distancia,band)
plt.plot(times,Fres, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo ")
plt.xlabel('Tempo [segundos]')

Fres_tot = (Fres*Fres_sat*Fres_an1*Fres_an2*Fres_an3*Fres_an4)
plt.plot(times,Fres_tot, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo ")
plt.xlabel('Tempo [segundos]')
plt.title("Simulação com Difração de Fresnel")

tempo_a =  tmini
#if fluxo_instante > 20000:
#        print("Por questão de tempo computacional foi realizada uma aproximação no número de fótons")
while tempo_a < tmaxi:
    fluxo_instante = contagem_fluxo_anel2(tempo_a,mag_obj,mag_star, area_telescopio, 
                                                  tempexp, band, inicio, fim, prof_otica, prof_otica2, prof_otica3, prof_otica4, inicio_anel1, 
                                                  fim_anel1, inicio_anel2, fim_anel2, inicio_anel3, fim_anel3, inicio_anel4, fim_anel4)
    #ceu = random.gauss(1,0.03)*contagem_fluxo_ceu(tempo_a, area_telescopio, tempexp,band, inicio, fim) 
    #print(fluxo_instante)
    ####ARRUMAR NO RUIDO TERMICO QUE É COM NUMERO DE PIXEL NÃO COM O FLUXO
    fluxo_instant = fluxo_instante#+(np.random.normal(0,ruido_termico(temperatura,fluxo_instante,tempexp)))#np.random.normal(fluxo_instante, 0.3)#var_fase**(1/2))#ceu+random.gauss(1, 0.03)*fluxo_instante
   # print(fluxo_instante)
    fluxo_instant = fluxo_instante #+ erro_fase(fluxo_instante,var_fase)
    #fluxo_instant = abs(fluxo_instant)
    flua.append(fluxo_instant)
    tempo_a += cyc
print (flua)

plt.plot(times,flua, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo Normalizado")
plt.xlabel('Tempo [segundos]')
plt.title("Simulação P9")

##########NORMALIZAÇÃO
i=0
med=np.median(flua[0:40])
for i in range(len(flua)):
    flua[i]=flua[i]/med
    i=i+1


Flua_fres=[i for i in range(len(flua))]

i=0
while i < len(flua):
    if flua[i] == 1:
        Flua_fres[i]=flua[i]*Fres_tot[i]
    else:
        Flua_fres[i]=(flua[i]+Fres_tot[i])/2
    i+=1
print(flua)
print(Flua_fres)

##########NORMALIZAÇÃO
j=0
med=(np.median(Flua_fres))
Flua_fresn=[]
for j in range(len(Flua_fres)):
    Flua_fresn.append(Flua_fres[j]/med)
    j=j+1

plt.plot(times,Flua_fres, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo Normalizado")
plt.xlabel('Tempo [segundos]')
plt.title("Simulação com Difração de Fresnel")#"{:.1f}s_{:.1f}ms_{:.0f}Mm_{:.0f}UA_{:.0f}_{:.0f}_{:.0f}_{:.1f}m_{:.0f}".format(
        #tempexp,vel,diametro_corpo/1000, distancia, diametro_estrela, mag_star,band, diam_teles/1000,mag_obj))
#plt.savefig("teste")
    #"mSt{:.0f}_{:.1f}s_{:.0f}Mm_Rg_{:.2f}_{:.0f}km_sa_Mir_T_{:.1f}m".format(
    #mag_star,tempexp,diametro_corpo/1000, prof_otica, espessura_anel, diam_teles/1000))
#
# plt.savefig("imags/_{:.1f}s_{:.1f}ms_{:.0f}Mm_{:.0f}UA_{:.0f}_{:.0f}_{:.0f}_{:.1f}m_{:.0f}_sat{:.0f}_{:.0f}_anel_{:.0f}_{:.0f}_{:.4f}.png".format
#    (tempexp, vel, diametro_corpo/1000, distancia, diametro_estrela, mag_star, band, (diam_teles/1000), mag_obj, diametro_sat, distancia_sat, diametro_anel, espessura_anel,prof_otica),dpi = 300)    
                                                     
                                
    #"magStar{:.1f}_{:.1f}s_{:.0f}Mm_Ring_{:.2f}_{:.0f}km_sat_Miranda_Tel_{:.1f}m.png".format(
    #mag_star,tempexp,diametro_corpo/1000, prof_otica, espessura_anel, diam_teles/1000)
    #        ,dpi = 300)                

plt.figure(figsize=(20,6))
plt.plot(times,Flua_fresn, 'o-',color='black',linewidth= 0.7,markersize=1)
plt.ylabel("Fluxo Normalizado")
plt.xlabel('Tempo [segundos]')
plt.title("Simulação P9 seeing 2.5")#"{:.1f}s_{:.1f}ms_{:.0f}Mm_{:.0f}UA_{:.0f}_{:.0f}_{:.0f}_{:.1f}m_{:.0f}".format(
        #tempexp,vel,diametro_corpo/1000, distancia, diametro_estrela, mag_star,band, diam_teles/1000,mag_obj))
#plt.savefig("teste")
    #"mSt{:.0f}_{:.1f}s_{:.0f}Mm_Rg_{:.2f}_{:.0f}km_sa_Mir_T_{:.1f}m".format(
    #mag_star,tempexp,diametro_corpo/1000, prof_otica, espessura_anel, diam_teles/1000))
#
plt.savefig("imags/2.5_0.01.png" ) 
                                                     
    #"magStar{:.1f}_{:.1f}s_{:.0f}Mm_Ring_{:.2f}_{:.0f}km_sat_Miranda_Tel_{:.1f}m.png".format(
    #mag_star,tempexp,diametro_corpo/1000, prof_otica, espessura_anel, diam_teles/1000)
    #        ,dpi = 300)                



