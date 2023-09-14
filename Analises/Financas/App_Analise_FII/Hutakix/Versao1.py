# Importando Bibliotecas
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
from tqdm import tqdm 
import time
import multiprocessing as mp
import random
import datetime
import yfinance as yf
import mplcyberpunk
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
import datetime
import pandas_datareader.data as pdr
from numpy import linalg as LA
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
import os
from pathlib import Path
yf.pdr_override()

#Funções utilizadas:
def encontrar_arquivo_download(nome_arquivo):
    # Encontra o caminho da pasta de download padrão
    if os.name == "nt":  # Windows
        pasta_download = Path(os.path.expanduser("~")) / "Downloads"
    elif os.name == "posix":  # Linux ou macOS
        pasta_download = Path(os.path.expanduser("~")) / "Downloads"
    else:
        raise OSError("Sistema operacional não suportado.")
    
    # Verifica se o arquivo está presente na pasta de download
    arquivo_procurado = pasta_download / nome_arquivo
    if arquivo_procurado.is_file():
        return str(arquivo_procurado)
    else:
        return None

def BolaDeNeve(data):
    '''Docstring:
        Função recebe Data Frame e retorna valores para calcularmos o Magic Number necessário para
        começar a 'bola de neve'. Ou seja, a quantidade de cotas e a quantidade de investimento necessario
        para que a rentabilidade pague +1 cota.    
    '''
    cotas=[]
    valores=[]
    for i in range(1,len(data)+1):
        preco = data.loc[i]['Preco']
        div_ult = data.loc[i]['Ultimo Dividendo']
        cotas_nec = round(preco/div_ult)
        valor_nec = cotas_nec*preco
        cotas.append(cotas_nec)
        valores.append(valor_nec)
    return cotas,valores


#Procurando dados Ibovespa e IFIX (no momento os dados de IFIX n podem ser baixados pelo yfinance)
codigos = ["^BVSP","IFIX.SA"] #Ibovespa e IFIX
data_final = pd.Timestamp.today()
data_inicial = data_final - pd.DateOffset(months=12) #dados do ultimo ano
dados_mercado = yf.download(codigos, data_inicial, data_final, ignore_tz=True)['Adj Close']

###Necessário outra API para puxar IFIX:
ALPHA_VANTAGE_KEY = "E5Q5PIRX35FQE5R5" #Codigo adquirido ao me registrar
ts = TimeSeries(key=ALPHA_VANTAGE_KEY,output_format='pandas')
ts.get_daily_adjusted("IFIX.SAO") #Versão gratuita
dados_ifix, meta = ts.get_daily_adjusted("IFIX.SAO",outputsize='full') #separando os dados necessarios

#Dados anuais (ifix):
ifix_anual = dados_ifix['5. adjusted close'].resample("Y").last() #pegando dados anuais do IFIX
media_anual = dados_ifix['5. adjusted close'].resample("Y").mean()
#calcular fechamento do dia, retorno no ano dos ativos
retorno_anual_ifix = ifix_anual.pct_change() #funcao que automatiza isso
retorno_anual_ifix = retorno_anual_ifix.dropna()

#Dados mensais (ifix):
ifix_mensal = dados_ifix['5. adjusted close'].resample("M").last() # Pegando dados mensais do IFIX
retorno_mensal_ifix = ifix_mensal.pct_change().dropna()

ifix =  dados_ifix['5. adjusted close'][:150]

ibov = dados_mercado['^BVSP'].sort_index(ascending = False)

#Dados anuais (IBOVESPA):
ibov_anual = ibov.resample("Y").last() #pegando dados anuais do IBOVESPA
media_anual = ibov.resample("Y").mean()
#calcular fechamento do dia, retorno no ano dos ativos
retorno_anual_ibov = ibov_anual.pct_change()
retorno_anual_ibov = retorno_anual_ibov.dropna()

#Dados mensais (IBOVESPA):
ibov_mensal = ibov.resample("M").last() #pegando dados anuais do IBOVESPA
media_mensal = ibov.resample("M").mean()
#calcular fechamento do dia, retorno no ano dos ativos
retorno_mensal_ibov = ibov_mensal.pct_change()
retorno_mensal_ibov = retorno_mensal_ibov.dropna()

#Guardando tudo em Data Frame:
df_ibov = pd.DataFrame(data=ibov)
df_ifix = pd.DataFrame(data=ifix)
df_ifix.rename(columns = {'5. adjusted close':'IFIX.SA'}, inplace=True)

#Save_plot:
plt.style.use('cyberpunk')
df_ifix.plot()
plt.savefig('IFIX.png', dpi = 300)
plt.show()

#Save_plot:
plt.style.use('cyberpunk')
df_ibov.plot()
plt.show()

###### Bot especialista em FIIs:
driver = webdriver.Firefox( service=FirefoxService(GeckoDriverManager().install())) #nosso bot que irá abrir o navegador e procurar os sites
url = "https://statusinvest.com.br/fundos-imobiliarios/busca-avancada"
driver.get(url)
time.sleep(5) #Python é mais rapido que o carregamento da tabela

#achar o botão BUSCAR
botao_buscar = driver.find_element("xpath",'''//*[@id="main-2"]/div[3]/div/div/div/button[2] ''')
driver.execute_script("arguments[0].click()",botao_buscar)

time.sleep(3)

#Clicar em download
botao_dwnl = driver.find_element("xpath",'''/html/body/main/div[4]/div/div[1]/div[2]/a''')
driver.execute_script("arguments[0].click()",botao_dwnl)

time.sleep(3) #esperar um tempinho para completar o download

# Verificando localização do arquivo
nome_do_arquivo = "statusinvest-busca-avancada.csv"
caminho_do_arquivo = encontrar_arquivo_download(nome_do_arquivo)

if caminho_do_arquivo:
    print(f"Arquivo encontrado: {caminho_do_arquivo}")
    tabela_dwnl = pd.read_csv(str(caminho_do_arquivo),
                 #error_bad_lines=False
                sep=';', comment='#', na_values=' ')
else:
    print("Arquivo não encontrado na pasta de download.")

## limpando tabela que o bot conseguiu através do download
tabela_dwnl.DY = tabela_dwnl.DY.str.replace(".","").str.replace(",",".").astype(float)
tabela_dwnl['P/VP'] = tabela_dwnl['P/VP'].str.replace(".","").str.replace(",",".").astype(float)
tabela_dwnl['PATRIMONIO'] = tabela_dwnl['PATRIMONIO'].str.replace(".","").str.replace(",",".").astype(float)
tabela_dwnl['ULTIMO DIVIDENDO'] = tabela_dwnl['ULTIMO DIVIDENDO'].str.replace(".","").str.replace(",",".").astype(float)
tabela_dwnl['PRECO'] = tabela_dwnl['PRECO'].str.replace(".","").str.replace(",",".").astype(float)

### Filtro ditado pelo usuário ###
minimo_DY = float(input("Digite o valor minimo DY para busca (recomendavel acima da inflação): "))
maximo_DY = float(input("Digite o valor maximo DY para busca (recomendavel a taxa selic): "))
valor_max = float(input("Digite o valor maximo de P/VP que deseja (recomendável 1.0): "))

Filtro_DY = tabela_dwnl[(tabela_dwnl.DY >= minimo_DY)*(tabela_dwnl.DY < maximo_DY)] # Aqueles com DY entre 6 e 10
Filtro = Filtro_DY[Filtro_DY['P/VP'] <= valor_max] #Aqueles com valor de cota menor ou igual ao valor patrimonial
Filtro = Filtro.sort_values(by=['PATRIMONIO'], ascending=False).dropna() 

#####Após o filtro, manipularemos os dados para fins de conveniencia:
#Renomeando colunas + selecionando as 15 cotas mais interessantes
df_2 = pd.DataFrame(data = Filtro[1:16].values,index = list(range(1,16)),columns = ['Ticker','Preco','Ultimo Dividendo','DY','VALOR PATRIMONIAL COTA','P/VP','LIQUIDEZ MEDIA DIARIA','PERCENTUAL EM CAIXA','Dividendos 3 anos','Valor CORA 3 anos','PATRIMONIO','COTISTAS','GESTAO','N COTAS'])
#Adicionando rentabilidade do ultimo mês como uma coluna nova
df_2['% ult mês'] = (df_2['Ultimo Dividendo']/df_2['Preco'])*100
#Adicionando o Magic Number como uma coluna nova
df_2['Cotas Necessarias'],df_2['Investimento Necessario (Real)'] = BolaDeNeve(df_2)
#Ordenando pelo menor valor necessário para alcançar o Magic Number
df_2 = df_2.sort_values(by=['Investimento Necessario (Real)'])

### Criando as duas seleções de escolha de ativos:
## 1° : Os 5 melhores magic numbers
MN_5_melhores = df_2[:5]
## 2°: Os 5 melhores rendimentos do ultimos mês
# Ordenando de acordo com a rentabilidade SEGUNDO O ULTIMO DIVIDENDO
df_2 = df_2.sort_values(by=['% ult mês'], ascending=False)
Rent_5_melhores = df_2[:5]

print("Testando uma carteira de fundos imobiliário com os ativos: "+str(MN_5_melhores['Ticker'].tolist())+" e "+str(Rent_5_melhores['Ticker'].tolist()))

#Criando planilha dos ativos escolhidos:
df_escolhas = pd.concat([MN_5_melhores, Rent_5_melhores], ignore_index=True).drop_duplicates()
df_escolhas.to_excel("carteira_ifix.xlsx") 

#Selecionando os Tickers dos nossos ativos:
escolhas = MN_5_melhores['Ticker'].tolist() + Rent_5_melhores['Ticker'].tolist()
escolhas = list(dict.fromkeys(escolhas))


##Buscar dados para simulações de Monte Carlo:
lista_acoes = escolhas #pegando os fundos que escolhemos
lista_acoes = [fii + ".SA" for fii in lista_acoes] #para conseguir puxar os dados da yfinance

data_final = pd.Timestamp.today()
data_inicial = data_final - pd.DateOffset(months=110) #pegar dados desde 2014

precos = yf.download(lista_acoes, start=data_inicial, end=data_final)['Adj Close']

#Informações sobre o retorno da nossa carteira no momento
retornos = precos.pct_change().dropna()
media_retornos = retornos.mean()
matriz_covariancia = retornos.cov()
pesos_carteira = np.full(len(lista_acoes), 1/len(lista_acoes))
numero_acoes = len(lista_acoes)

#### Simulações:
# Premissas montecarlo

numero_simulacoes = 1000
dias_projetados = 252*20 #252 dias uteis -> proximos 20 anos
capital_inicial = 1000 #o que vai ocorrer com 1000 reais?

#Retorno medio em forma de matriz

retorno_medio = retornos.mean(axis = 0).to_numpy()
matriz_retorno_medio = retorno_medio*np.ones(shape = (dias_projetados,numero_acoes))

#Nossa matriz L

L = LA.cholesky(matriz_covariancia)

retornos_carteira = np.zeros([dias_projetados, numero_simulacoes])
montante_final = np.zeros(numero_simulacoes)

for s in range(numero_simulacoes):
    
    Rpdf = np.random.normal(size = (dias_projetados, numero_acoes))
    retornos_sinteticos = matriz_retorno_medio + np.inner(Rpdf, L) #Unico parametro aleatorio é Rpdf
    
    retornos_carteira[:,s] = np.cumprod(np.inner(pesos_carteira, retornos_sinteticos) + 1) * capital_inicial
    montante_final[s] = retornos_carteira[-1,s]

plt.figure(figsize = [8,7])
plt.title("Projeção de 1000 reais rendendo na carteira top5 MagicNumber-FIIs")
plt.plot(retornos_carteira,linewidth = 1)
plt.ylabel('Dinheiro')
plt.xlabel('Dias')

#salvar a imagem
plt.savefig('proj.png', dpi = 300)

plt.show()

#Criando as estatísticas para a nossa análise de carteira

montante_99 = str(np.percentile(montante_final,1))
montante_95 = str(np.percentile(montante_final,5))
montante_mediano = str(np.percentile(montante_final, 50))
cenarios_com_lucro = str(round((len(montante_final[montante_final > 1000])/len(montante_final))*100,2))+"%"

print("Ao investir R$ 1000,00 na carteira " + str(lista_acoes), "o resultado esperado para as próximas duas décadas, seguindo o método Monte Carlo com 1.000 simulações: \n")
print("50% de chance do montante ser maior que R$"+str(montante_mediano))
print("95% de chance do montante ser maior que R$"+str(montante_95))
print("99% de chance do montante ser maior que R$"+str(montante_99))
print("Cenários com lucro: "+str(cenarios_com_lucro))

#### Envio de e-mail (gmail):

fromaddr = "hutakegames@gmail.com"
remetentes = ['thiago18@ov.ufrj.br']
toaddr = " , ".join(remetentes)
msg = MIMEMultipart()
msg['From'] = fromaddr
msg['To'] = toaddr
msg['Subject'] = "Relatorio Automático FIIs."
body = f''' 
    Prezado,
    
    Segue a análise dos melhores fundos imobiliários com respeito ao Magic Number (aqueles que necessitam menor investimento para pagarem as proprias cotas).
    
    As cotas escolhidas para a carteira foram {lista_acoes}. 
    Com essa carteira, a chance de ter lucro nos próximos 20 anos será de {cenarios_com_lucro}. 
    Com R$1.000,00 investidos, haverá 50% de chance do montante ser maior que {montante_mediano} e 95% de chance do montante ser maior que {montante_95}.
    
    O rendimento mensal do IFIX: {round(retorno_mensal_ifix[-1],2)}%.
    O rendimento anual do IFIX: {round(retorno_anual_ifix[-1],2)}%.
    
    O rendimento mensal do IBOVESPA: {round(retorno_mensal_ibov[-1],2)}%.
    O rendimento anual de IBOVESPA: {round(retorno_anual_ibov[-1],2)}%.
    
    Segue em anexo os gráficos que mostram as possíveis evoluções destes rendimentos seguindo o método Monte Carlo.
    
    Abraços!
    
    
    Robô Hutake, auxiliar de Thiago Laidler (astrofísico e cientista de dados).
    Prazer.
    '''
msg.attach(MIMEText(body, 'plain'))

filename = "proj.png"
attachment = open("proj.png", "rb")

filename2 = "IFIX.png"
attachment2 = open("IFIX.png", "rb")

filename3 = "carteira_ifix.xlsx"
attachment3 = open("carteira_ifix.xlsx", "rb")

p = MIMEBase('application', 'octet-stream')
p.set_payload((attachment).read())
encoders.encode_base64(p)
p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
msg.attach(p)
p2 = MIMEBase('application', 'octet-stream')
p2.set_payload((attachment2).read())
encoders.encode_base64(p2)
p2.add_header('Content-Disposition', "attachment2; filename= %s" % filename2)
msg.attach(p2)
p3 = MIMEBase('application', 'octet-stream')
p3.set_payload((attachment3).read())
encoders.encode_base64(p3)
p3.add_header('Content-Disposition', "attachment3; filename= %s" % filename3)
msg.attach(p3)

s = smtplib.SMTP('smtp.gmail.com', 587)
s.starttls()
s.login(fromaddr, "xtlgeuwofxfvdlfv")
text = msg.as_string()
s.sendmail(fromaddr, remetentes, text)

s.quit()
