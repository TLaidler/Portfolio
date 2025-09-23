import yfinance as yf
import pandas as pd
import numpy as np
from bcb import sgs
from itertools import combinations
from scipy.stats import norm
import matplotlib.pyplot as plt

import datetime as dt
from dateutil.relativedelta import relativedelta
from bcb import currency, sgs
import pandas_datareader.data as web

# Classe para buscar dados do Banco Central do Brasil
class BancoCentral:
    def __init__(self):
        self.hoje = dt.datetime.now()
        self.start = dt.datetime(2009,1,1)

    def busca_juros(self, start='2009-01-01'):
        """
        Busca a taxa SELIC.
        """
        return sgs.get({'selic': 4390}, start=start)

    def busca_inflacao_ipca(self, start=dt.datetime(2009,1,1)):
        """
        Busca o índice IPCA.
        """
        return sgs.get({'ipca': 433}, start=start)
    
    def busca_inflacao_ipca_ultimos_tempos(self, anos=1):
        """
        Busca o índice IPCA.
        """
        ano_passado = self.hoje - relativedelta(years=anos)
        return sgs.get({'ipca': 433}, start=ano_passado)

    def busca_inflacao_igpm(self, start=dt.datetime(2010,1,1)):
        """
        Busca o índice IGPM.
        """
        return sgs.get({'igpm': 189}, start=start)

    def busca_inflacao_igpm_ultimos_tempos(self, anos=1):
        """
        Busca o índice IGPM.
        """
        ano_passado = self.hoje - relativedelta(years=anos)
        return sgs.get({'igpm': 189}, start=ano_passado)

    def busca_pib(self, start='2000-01-01'):
        """
        Busca o PIB do Brasil (em variação trimestral real).
        """
        return sgs.get({'pib': 22099}, start=start)
    
    def busca_cambio(self, moedas=['USD', 'EUR'], start='2000-01-01', end=None):
        """
        Busca o câmbio das moedas especificadas.
        """
        if not end:
            end = self.hoje.strftime('%Y-%m-%d')
        return currency.get(moedas, start=start, end=end, side='bid')

# Classe para buscar dados do FED
class FederalReserve:
    def __init__(self):
        self.start = dt.datetime(2010, 1, 1)
        self.end = dt.datetime.now()

    def busca_taxa_federal_funds(self):
        """
        Busca a taxa de juros dos Federal Funds (EFFR).
        """
        return web.DataReader('DFF', 'fred', self.start, self.end)
    
    def busca_inflacao(self):
        """
        Busca o CPI (Consumer Price Index) nos EUA.
        """
        return web.DataReader('CPIAUCSL', 'fred', self.start, self.end)

    def busca_pib(self):
        """
        Busca os dados de PIB dos EUA.
        """
        return web.DataReader('GDPC1', 'fred', self.start, self.end)


#Buscar todos os ativos:
def fetch_all_tickers():
    import os
    from selenium import webdriver
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from webdriver_manager.firefox import GeckoDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import pandas_datareader.data as pdr
    import time
    # Configuração do WebDriver
    driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))

    # URL inicial do site
    url = "https://maisretorno.com/lista-acoes"
    driver.get(url)
    time.sleep(5)  # Espera inicial para carregamento da página

    # Lista para armazenar os tickers
    tickers = []

    while True:
        # Captura os tickers na página atual
        elementos = driver.find_elements(By.XPATH, "//main//ul//li//a")
        tickers.extend([el.text for el in elementos if el.text])  # Adiciona os tickers encontrados

        try:
            # Aguarda o botão "Próxima Página" aparecer
            next_page = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//a[@aria-label='próxima página']"))
            )

            # Obtém a URL da próxima página
            next_page_url = next_page.get_attribute("href")

            if not next_page_url:
                print("Última página alcançada.")
                break  # Sai do loop

            # Acessa a próxima página diretamente
            driver.get(next_page_url)
            time.sleep(3)  # Espera carregar

        except Exception as e:
            print(f"Erro ao tentar acessar próxima página: {e}")
            break  # Sai do loop
    
    tickers = [item for item in tickers if not item.isdigit()]
    return tickers


# Função para obter dados históricos de um ativo

def obter_dados_ativo(ticker, inicio, fim):
    dados = yf.download(ticker, start=inicio, end=fim)
    return dados['Adj Close']


# Função para calcular a rentabilidade real

def calcular_rentabilidade_real(retornos, inflacao):
    rentabilidade_real = (1 + retornos).div(1 + inflacao, fill_value=0) - 1
    return rentabilidade_real

# Função para calcular o índice de Sharpe

def calcular_sharpe(retornos, rf=0.0):
    excesso_retorno = retornos - rf
    return excesso_retorno.mean() / excesso_retorno.std()

# Função para simular carteiras e calcular métricas

def simular_carteiras(ativos, tamanho_carteira, inicio, fim, rf=0.0):
    combinacoes = list(combinations(list(ativos.columns), tamanho_carteira))
    resultados = []
    cont = 1
    for carteira in combinacoes:
        dados_carteira = pd.DataFrame()
        for ativo in carteira:
            dados_carteira[ativo] = ativos[ativo].pct_change().dropna()
        retornos_carteira = dados_carteira.mean(axis=1)
        sharpe = calcular_sharpe(retornos_carteira, rf)
        resultados.append((carteira, retornos_carteira.mean(), sharpe))
        print(f"########## {(cont/len(combinacoes))*100} % ##########")
        cont = cont + 1
    return resultados

def anualizar_df_mensal(df):
    name = df.columns[0]
    df["fator"] = 1 + df[name] / 100
    df[f"{name}_anual"] = (
    df["fator"].rolling(window=12).apply(lambda x: x.prod(), raw=True) - 1) * 100
    df_anual = df[[f"{name}_anual"]]
    return df_anual

def calcular_spread(df1, df2):
    # 1. Garantir que os índices sejam datetime
    df1.index = pd.to_datetime(df1.index)
    df2.index = pd.to_datetime(df2.index)

    # 2. Juntar as duas séries pelo índice
    df = pd.concat([df1, df2], axis=1)

    # Renomear para evitar confusão
    df.columns = [f"{df1.columns[0]}", f"{df2.columns[0]}"]

    # 3. Calcular o spread (Selic - IPCA)
    df[f"spread_{df1.columns[0]}&{df2.columns[0]}"] = df[f"{df1.columns[0]}"] - df[f"{df2.columns[0]}"]

    return df[f"spread_{df1.columns[0]}&{df2.columns[0]}"]


def selecionar_top30(all_stocks_df):
    """
    Filtra e retorna as 30 ações mais 'seguras' com base nos critérios:
    1. Longevidade: só mantêm tickers com dados desde 2010.
    2. Retorno mínimo: só mantêm tickers com retorno (Close final / Close inicial - 1) >= 300%.
    3. Se restarem mais de 30 tickers, seleciona as 30 com maior volume médio.

    Parameters:
        all_stocks_df (pd.DataFrame): dataframe no formato MultiIndex (columns: ['Adj Close','Close','High','Low','Open','Volume']).

    Returns:
        pd.DataFrame: dataframe apenas com os 30 tickers finais, colunas = tickers, valores = 'Close'.
    """

    tickers_validos = []
    volumes = []

    # Percorre cada ticker do dataframe
    for ticker in all_stocks_df["Close"].columns:
        df_ticker = all_stocks_df.xs(ticker, axis=1, level=1)

        # 1) Verifica longevidade (dados desde 2010)
        if df_ticker.dropna().index.min() > pd.Timestamp("2010-01-20"):
            continue
        else:
            # 2) Calcula retorno acumulado desde 2010
            preco_inicio = df_ticker["Close"].loc["2010-01-01":].dropna().iloc[0]
            preco_final = df_ticker["Close"].iloc[-1]
            retorno = (preco_final / preco_inicio) - 1

            if retorno < 0.5:  
                continue
            else:
                # 3) Armazena volume médio
                vol_medio = df_ticker["Volume"].mean()
                tickers_validos.append(ticker)
                volumes.append(vol_medio)

    # Cria dataframe auxiliar
    df_filtrado = pd.DataFrame({"Ticker": tickers_validos, "VolumeMedio": volumes})

    # Se houver mais de 30, pega os top 30 com maior volume
    if len(df_filtrado) > 30:
        df_filtrado = df_filtrado.sort_values(by="VolumeMedio", ascending=False).head(30)

    tickers_final = df_filtrado["Ticker"].tolist()

    # Retorna apenas o 'Close' desses tickers
    closes = all_stocks_df["Close"][tickers_final]

    return closes



def AVISO_DIVIDENDOS():
    import yfinance as yf
    import matplotlib.pyplot as plt
    import pandas as pd

    # Baixar dados da PETR4 (ajustado automaticamente pelo Yahoo)
    ticker = yf.Ticker("PETR4.SA")
    data = ticker.history(start="2022-01-01", end="2025-01-01", auto_adjust=True)

    # Colunas relevantes
    df = data[["Close", "Dividends"]].copy()

    # Calcular Total Return (reinvestindo dividendos)
    shares = 1.0
    values = []

    for i in range(len(df)):
        price = df["Close"].iloc[i]
        div = df["Dividends"].iloc[i]
        
        # Se houve dividendo, compra mais ações com ele
        if div > 0:
            shares += div / price
        
        values.append(shares * price)

    df["Total Return"] = values

    # Normalizar para começar em 100
    df["Adj Close (Preço Ajustado)"] = df["Close"] / df["Close"].iloc[0] * 100
    df["Total Return (Reinvestido)"] = df["Total Return"] / df["Total Return"].iloc[0] * 100

    # Plotar comparação
    plt.figure(figsize=(10,5))
    plt.plot(df.index, df["Adj Close (Preço Ajustado)"], label="Preço Ajustado (TradingView style)")
    plt.plot(df.index, df["Total Return (Reinvestido)"], label="Total Return (Dividendos reinvestidos)", linestyle="--")
    plt.legend()
    plt.title("PETR4: Preço Ajustado vs Total Return")
    plt.ylabel("Base 100")
    plt.grid(True)
    plt.show()
    return "Cuidado!! Tem que considerar os dividendos reinvestidos!"


if __name__ == "__main__":
    # Parâmetros
    inicio = '2010-01-01'
    fim = '2025-09-20'
        # Instâncias
    bc = BancoCentral()
    fed = FederalReserve()

    print("Baixando dados da Selic e IPCA...")
    selic =  bc.busca_juros(start='2009-01-01')
    selic_anual = anualizar_df_mensal(selic).dropna()
    ipca = bc.busca_inflacao_ipca()
    ipca_anual = anualizar_df_mensal(ipca).dropna()
    igpm = bc.busca_inflacao_igpm()
    igpm_anual = anualizar_df_mensal(igpm).dropna()
    pib_br = bc.busca_pib()
    cambio = bc.busca_cambio()
    taxa_federal_EUA = fed.busca_taxa_federal_funds()
    cpi_EUA = fed.busca_inflacao()
    cpi_EUA["CPIAUCSL"] = cpi_EUA["CPIAUCSL"].pct_change(12) * 100
    pib_eua = fed.busca_pib()

    spread_selic_ipca = calcular_spread(selic_anual, ipca_anual).dropna()
    spread_interestUS_cpi = calcular_spread(taxa_federal_EUA, cpi_EUA).dropna() #O certo aqui seria dividir mensal/mensal e ir acumulando. Mas dessa forma já temos uma ótima aproximação.
    carry_trade_real = pd.DataFrame(calcular_spread(pd.DataFrame(spread_selic_ipca), pd.DataFrame(spread_interestUS_cpi)).dropna())
    carry_trade_real['nivel_juros'] = np.where(carry_trade_real > carry_trade_real.mean().values[0], 'alto', 'baixo')

    print("Baixando dados do Ibovespa e IFIX...")
    ibovespa = yf.download(["^BVSP"], dt.datetime(2010,1,1),dt.datetime.now())
    #ifix = obter_dados_ativo('IFIX.SA', inicio, fim)

    # Calcular rentabilidades
    retorno_ibovespa = ibovespa['Close'].pct_change().dropna()
    #retorno_ifix = ifix.pct_change().dropna()
    inflacao = ipca.pct_change().dropna()

    # Calcular rentabilidade real
    rentabilidade_real_ibovespa = calcular_spread(retorno_ibovespa, inflacao[['ipca']]).dropna().plot()
    #rentabilidade_real_ifix = calcular_rentabilidade_real(retorno_ifix, inflacao)
    #tickers = fetch_all_tickers() #TODO: descomentar caso não tenha arquivo .csv
    tickers_yf = list(pd.read_csv('tickers_yf.csv')['0'])#[t + ".SA" for t in tickers]
    # Analisar rentabilidade em períodos de juros altos e baixos
    #resultados_juros = selic.join(rentabilidade_real_ibovespa, how='inner').join(rentabilidade_real_ifix, how='inner', rsuffix='_ifix')
    #print("\nRentabilidade média corrigida pela inflação em períodos de juros altos e baixos:")
    #print(resultados_juros.groupby('nivel_juros').mean().iloc[:,1:])

    # Exemplo de lista de ativos do Ibovespa (ajuste conforme necessário)
    #ativos_ibovespa = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA', 'BBAS3.SA', 'B3SA3.SA', 'WEGE3.SA', 'RENT3.SA', 'LREN3.SA']
    all_stocks_BR = yf.download(tickers_yf, dt.datetime(2010,1,1),dt.datetime.now(),auto_adjust=True)

    all_stocks_BR = all_stocks_BR.dropna(axis=1, how="all")
    all_stocks_BR = all_stocks_BR.dropna(axis=0, how="all")
    top30_tickers = selecionar_top30(all_stocks_BR)
    #TODO: Agora falta selecionar as empresas que estão a mais tempo e possuem maior volume. Retornar outro 'tickers_list' e depois sim rodar a simulação.
    print("\nSimulando carteiras de 5 ativos do Ibovespa (2008-2024)...")
    resultados_carteiras = simular_carteiras(top30_tickers, 5, inicio, fim, rf=selic.pct_change().mean().values[0]) #TODO: Verificar, talvez não esteja acumulando a rentabilidade

    # Ordenar por rentabilidade e Sharpe
    melhores_rentabilidades = sorted(resultados_carteiras, key=lambda x: x[1], reverse=True)[:3]
    melhores_sharpe = sorted(resultados_carteiras, key=lambda x: x[2], reverse=True)[:3]

    print("\nTop 3 carteiras por rentabilidade:")
    for carteira in melhores_rentabilidades:
        print(f"Carteira: {carteira[0]}, Rentabilidade: {carteira[1]:.2%}, Sharpe: {carteira[2]:.2f}")

    print("\nTop 3 carteiras por índice de Sharpe:")
    for carteira in melhores_sharpe:
        print(f"Carteira: {carteira[0]}, Rentabilidade: {carteira[1]:.2%}, Sharpe: {carteira[2]:.2f}")
