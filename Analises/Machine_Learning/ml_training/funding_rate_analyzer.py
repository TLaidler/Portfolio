import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from typing import Optional

class FundingRateAnalyzer:
    def __init__(self):
        self.dfs = {}
        self.dist = {}

    @staticmethod
    def count_funding_events(start_str, end_str):
        """
        Conta quantos eventos de funding ocorrem entre duas datas.
        Eventos ocorrem de 4 em 4 horas: 00h, 04h, 08h, 12h, 16h, 20h.
        - Se start_str cair exatamente em um evento, não conta.
        - Se end_str cair exatamente em um evento, conta.
        """
        if type(start_str) == str:
            start = dt.datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
        elif type(start_str) == dt.datetime:
            start = start_str
        elif type(start_str) == dt.date:
            start = dt.datetime.combine(start_str, dt.time(0, 0, 0))
        elif type(start_str) == int:
            start = pd.to_datetime(start_str, unit='ms')
        elif type(start_str) == pd.Timestamp:
            start = start_str
        else:
            raise ValueError(f"Tipo de start_str inválido: {type(start_str)}")

        if type(end_str) == str:
            end = dt.datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S')
        elif type(end_str) == dt.datetime:
            end = end_str
        elif type(end_str) == dt.date:
            end = dt.datetime.combine(end_str, dt.time(0, 0, 0))
        elif type(end_str) == int:
            end = pd.to_datetime(end_str, unit='ms')
        elif type(end_str) == pd.Timestamp:
            end = end_str
        else:
            raise ValueError(f"Tipo de end_str inválido: {type(end_str)}")

        if end <= start:
            return 0

        count = 0
        horas_evento = [0, 8, 16]
        proximo_evento = start.replace(minute=0, second=0, microsecond=0)

        while proximo_evento <= start:
            h = proximo_evento.hour
            prox_hora = next((he for he in horas_evento if he > h), None)
            if prox_hora is None:
                proximo_evento = proximo_evento.replace(hour=0) + dt.timedelta(days=1)
            else:
                proximo_evento = proximo_evento.replace(hour=prox_hora)

        while proximo_evento <= end:
            count += 1
            proximo_evento += dt.timedelta(hours=8)

        return count - 1

    def read_funding_csv(self, filepath, symbol_suffix):
        """
        Lê e processa o CSV de funding rate da Binance para o formato padronizado.
        """
        df = pd.read_csv(filepath, sep=';')
        if 'Unnamed: 0' in df.columns:
            df.drop(columns=['Unnamed: 0'], inplace=True)

        df['fundingTime'] = pd.to_datetime(df['fundingTime'], unit='ms')
        df.set_index('fundingTime', inplace=True)

        df.rename(columns={
            'fundingRate': f'fundingRate_{symbol_suffix}',
            'markPrice': f'markPrice_{symbol_suffix}'
        }, inplace=True)

        df[f'funding_{symbol_suffix}'] = df[f'fundingRate_{symbol_suffix}'] * df[f'markPrice_{symbol_suffix}']

        self.dfs[symbol_suffix] = df
        return self.dfs[symbol_suffix]

    def filter_dfs_by_date(self, start_date, end_date):
        """
        Filtra o DataFrame pela data.
        """
        if type(start_date) == str:
            start_date = pd.to_datetime(start_date)
        if type(end_date) == str:
            end_date = pd.to_datetime(end_date)

        for symbol_suffix in self.dfs:
            self.dfs[symbol_suffix] = self.dfs[symbol_suffix][self.dfs[symbol_suffix].index >= start_date]
            self.dfs[symbol_suffix] = self.dfs[symbol_suffix][self.dfs[symbol_suffix].index <= end_date]

    def plot_funding_rate(self, symbol_suffix):
        """
        Plota o histórico do fundingRate.
        """
        col = f'fundingRate_{symbol_suffix}'
        if col not in self.dfs[symbol_suffix].columns:
            raise ValueError(f"Coluna {col} não encontrada no DataFrame.")
        
        plt.figure(figsize=(12, 6))
        plt.plot(self.dfs[symbol_suffix].index, self.dfs[symbol_suffix][col], label='Funding Rate')
        plt.axhline(0, color='red', linestyle='--', alpha=0.5)
        plt.title(f'Histórico de Funding Rate ({symbol_suffix.upper()})')
        plt.xlabel('Data')
        plt.ylabel('Funding Rate')
        plt.legend()
        plt.show()

    def plots_extras(self, symbol_suffix):
        """
        Plots extras: sugestão de gráfico com:
        - Funding rate
        - Mark price
        - Média móvel do funding
        - Distribuição do funding (histograma)
        """
        col_funding = f'fundingRate_{symbol_suffix}'
        col_price = f'markPrice_{symbol_suffix}'

        if col_funding not in self.dfs[symbol_suffix].columns or col_price not in self.dfs[symbol_suffix].columns:
            raise ValueError("Colunas necessárias não encontradas.")

        fig, ax1 = plt.subplots(figsize=(14, 7))

        ax1.set_xlabel('Data')
        ax1.set_ylabel('Mark Price', color='blue')
        ax1.plot(self.dfs[symbol_suffix].index, self.dfs[symbol_suffix][col_price], color='blue', alpha=0.6, label='Mark Price')
        ax1.tick_params(axis='y', labelcolor='blue')

        ax2 = ax1.twinx()
        ax2.set_ylabel('Funding Rate', color='orange')
        ax2.plot(self.dfs[symbol_suffix].index, self.dfs[symbol_suffix][col_funding], color='orange', alpha=0.6, label='Funding Rate')
        ax2.plot(self.dfs[symbol_suffix].index, self.dfs[symbol_suffix][col_funding].rolling(window=10).mean(), 
                 color='red', linestyle='--', label='Média Móvel (10 períodos)')
        ax2.tick_params(axis='y', labelcolor='orange')

        fig.tight_layout()
        plt.title(f'Preço e Funding Rate ({symbol_suffix.upper()})')
        plt.legend(loc='upper left')
        plt.show()

        # Histograma
        plt.figure(figsize=(10, 5))
        plt.hist(self.dfs[symbol_suffix][col_funding].dropna(), bins=300, color='orange', alpha=0.7)
        plt.axvline(0, color='red', linestyle='--')
        plt.axvline(self.dfs[symbol_suffix][col_funding].mean(), color='green', linestyle='--', label='Média')
        plt.title(f'Distribuição do Funding Rate ({symbol_suffix.upper()})')
        plt.xlabel('Funding Rate')
        plt.ylabel('Frequência')
        plt.legend()
        plt.show()

    def funding_percentile(self, n, p, symbol_suffix, plot=False):
        """
        Calcula o percentil 10 do rolling sum de n eventos de funding.
        """
        col = f'fundingRate_{symbol_suffix}'
        if col not in self.dfs[symbol_suffix].columns:
            raise ValueError(f"Coluna {col} não encontrada no DataFrame.")

        percentiles = []
        roll_sum = self.dfs[symbol_suffix][col].rolling(window=n).sum()
        for i in p:
            percentile = np.percentile(roll_sum.dropna(), i)
            percentiles.append(percentile)

        if plot:
            # Plot histogram of rolling sum
            plt.figure(figsize=(10, 5))
            plt.hist(roll_sum.dropna(), bins=300, color='blue', alpha=0.7)
            plt.axvline(roll_sum.mean(), color='green', linestyle='--', label='Média')
            for i in range(len(p)):
                plt.axvline(percentiles[i], linestyle='--', label=f'Percentil {p[i]}')
            plt.title(f'Distribuição da Soma Móvel de {n} Períodos do Funding Rate ({symbol_suffix.upper()})')
            plt.xlabel('Soma Móvel do Funding Rate')
            plt.ylabel('Frequência')
            plt.legend()
            plt.show()

        return percentiles
    
    def compare_funding_rates(self, symbol_suffix_1, symbol_suffix_2):
        """
        Compara os funding rates de dois símbolos.
        """
        col_1 = f'fundingRate_{symbol_suffix_1}'
        col_2 = f'fundingRate_{symbol_suffix_2}'
        
        if col_1 not in self.dfs[symbol_suffix_1].columns or col_2 not in self.dfs[symbol_suffix_2].columns:
            raise ValueError("Colunas necessárias não encontradas.")
        
        plt.figure(figsize=(12, 6))
        plt.plot(self.dfs[symbol_suffix_1].index, self.dfs[symbol_suffix_1][col_1], label=symbol_suffix_1.upper())
        plt.plot(self.dfs[symbol_suffix_2].index, self.dfs[symbol_suffix_2][col_2], label=symbol_suffix_2.upper())
        plt.title(f'Comparação de Funding Rates ({symbol_suffix_1.upper()} e {symbol_suffix_2.upper()})')
        plt.xlabel('Data')
        plt.ylabel('Funding Rate')
        plt.legend()
        plt.show()

    def create_funding_dist(self, symbol_suffix, n):
        self.dist[symbol_suffix] = self.dfs[symbol_suffix][f'funding_{symbol_suffix}'].rolling(window=n).sum().shift(-n+1)
        return self.dist[symbol_suffix]
    
    def funding_rate_diff_percentile(self, n, p, symbol_suffix_1, symbol_suffix_2, plot=False):
        """
        Calcula a diferença entre os percentis 10 do rolling sum de n eventos de funding de dois símbolos.
        """
        col_1 = f'fundingRate_{symbol_suffix_1}'
        col_2 = f'fundingRate_{symbol_suffix_2}'
        
        if col_1 not in self.dfs[symbol_suffix_1].columns or col_2 not in self.dfs[symbol_suffix_2].columns:
            raise ValueError("Colunas necessárias não encontradas.")
        
        roll_sum_1 = self.dfs[symbol_suffix_1][col_1].rolling(window=n).sum()
        roll_sum_2 = self.dfs[symbol_suffix_2][col_2].rolling(window=n).sum()
        diff = roll_sum_1 - roll_sum_2

        percentiles = []
        for i in p:
            percentile = np.percentile(diff.dropna(), i)
            percentiles.append(percentile)

        if plot:
            # Plot histogram of rolling sum
            plt.figure(figsize=(10, 5))
            plt.hist(diff.dropna(), bins=300, color='blue', alpha=0.7)
            plt.axvline(diff.mean(), color='green', linestyle='--', label='Média')
            for i in range(len(p)):
                plt.axvline(percentiles[i], linestyle='--', label=f'Percentil {p[i]}')
            plt.title(f'Distribuição da Diferença de Funding Rates ({symbol_suffix_1.upper()} - {symbol_suffix_2.upper()})')
            plt.xlabel('Diferença de Funding Rate')
            plt.ylabel('Frequência')
            plt.legend()
            plt.show()

        return diff, percentiles
    
    def calculate_risk(
        self,
        ohlcv: pd.DataFrame,
        coluna: str,
        janela: int,
        modelo: str = "std",
        alpha: float = 0.05,
        log_returns: bool = False,
        min_periods: Optional[int] = None,
    ) -> pd.Series:
        """
        Calcula uma medida de risco em janela móvel.

        Parâmetros
        - ohlcv: DataFrame com OHLCV (requer 'close' para VaR, 'high' e 'low' para Parkinson).
        - coluna: nome da coluna alvo (p/ 'std' e 'mdd').
        - janela: tamanho da janela (int).
        - modelo: 'std' | 'var' | 'parkinson' | 'mdd' (default: 'std').
        - alpha: nível de cauda para VaR histórico (default: 0.05 → VaR 95%).
        - log_returns: se True, usa log-retornos no VaR; caso contrário, retornos simples.
        - min_periods: mínimo de observações válidas na janela (default = janela).

        Retorna
        - pd.Series alinhada ao índice original com o valor do risco por barra.
          Convenções: medidas sempre não negativas (std, VaR, Parkinson, MDD).
        """
        if min_periods is None:
            min_periods = janela

        modelo = modelo.lower()

        if modelo == "std":
            if coluna not in ohlcv.columns:
                raise ValueError(f"Coluna '{coluna}' não encontrada no DataFrame.")
            return ohlcv[coluna].rolling(window=janela, min_periods=min_periods).std()

        elif modelo in {"var", "value_at_risk"}:
            if "close" not in ohlcv.columns:
                raise ValueError("Para VaR, a coluna 'close' é necessária em ohlcv.")
            serie_ret = (
                np.log(ohlcv["close"]).diff()
                if log_returns
                else ohlcv["close"].pct_change()
            )
            q_alpha = serie_ret.rolling(window=janela, min_periods=min_periods).quantile(alpha)
            # VaR histórico como perda positiva (magnitude no quantil de cauda)
            return (-q_alpha).clip(lower=0)

        elif modelo in {"parkinson", "pk"}:
            if not {"high", "low"}.issubset(ohlcv.columns):
                raise ValueError("Para Parkinson, as colunas 'high' e 'low' são necessárias.")
            hl_sq = np.log(ohlcv["high"] / ohlcv["low"]) ** 2
            fator = 1.0 / (4.0 * np.log(2.0))
            var_pk = fator * hl_sq.rolling(window=janela, min_periods=min_periods).mean()
            return np.sqrt(var_pk)

        elif modelo in {"mdd", "max_drawdown", "maximum_drawdown"}:
            if coluna not in ohlcv.columns:
                raise ValueError(f"Coluna '{coluna}' não encontrada no DataFrame.")

            def _mdd(arr: np.ndarray) -> float:
                arr = np.asarray(arr, dtype=float)
                if arr.size == 0 or np.all(np.isnan(arr)):
                    return np.nan
                x = arr[~np.isnan(arr)]
                if x.size == 0:
                    return np.nan
                cummax = np.maximum.accumulate(x)
                drawdown = x / cummax - 1.0
                return -np.min(drawdown)

            return ohlcv[coluna].rolling(window=janela, min_periods=min_periods).apply(_mdd, raw=True)

        else:
            raise ValueError("Modelo inválido. Use 'std', 'var', 'parkinson' ou 'mdd'.")
        
    

if __name__ == "__main__":
    analyzer = FundingRateAnalyzer()
    analyzer.read_funding_csv(f"eth_funding.csv", "eth")
    analyzer.read_funding_csv(f"sol_funding.csv", "sol")
    analyzer.read_funding_csv(f"btc_funding.csv", "btc")
    analyzer.filter_dfs_by_date("2023-01-01", "2025-08-01")
    # analyzer.plot_funding_rate("sol")
    # analyzer.plots_extras("sol")
    n = analyzer.count_funding_events((datetime.now() - timedelta(hours=3)).strftime(format="%Y-%m-%d %H:%M:%S"), "2025-09-26 17:00:00")
    n = 56
    print(analyzer.funding_percentile(n, [10, 90], "eth", plot=True))
    diff, percentiles = analyzer.funding_rate_diff_percentile(n, [10, 90], "eth", "btc", plot=True)
    print(percentiles)
    print(analyzer.funding_percentile(n, [10, 90], "eth", plot=True))
    print('ok')
