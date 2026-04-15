# Guia Completo: Pipeline Marcos Lopez de Prado para Criptoativos

> Baseado em *"Advances in Financial Machine Learning"* (AFML, 2018) e *"Machine Learning for Asset Managers"* (2020).

---

## Visao Geral do Pipeline

```
BTC 1-min OHLCV ──> Dollar Bars ──> Feature Engineering ──> Triple-Barrier Labels
                                                                     │
                    Fear & Greed ──────────────────────────> (merge) ─┘
                                                                     │
                                                                     v
                              Purged K-Fold CV  <──  Random Forest (primario)
                                                                     │
                                                                     v
                              Meta-Labeling (secundario: apostar ou nao?)
                                                                     │
                                                                     v
                              Avaliacao: MDA + PSR + Classification Report
                                                                     │
                                                                     v
                              5 plots diagnosticos em save_point_marcos/
```

---

## Etapa 1: Dollar Bars (Cap. 2 AFML)

### O Problema com Barras de Tempo

Barras de tempo (1 minuto, 1 hora, 1 dia) amostram em intervalos fixos de relogio.
Isso causa dois problemas:

1. **Sobre-amostragem** em periodos calmos: de madrugada, o BTC quase nao se move,
   mas geramos a mesma quantidade de barras que durante horarios de pico.
2. **Sub-amostragem** em periodos volateis: durante um crash, milhoes de dolares
   sao transacionados por minuto, mas so temos 1 barra por minuto.

### A Solucao: Dollar Bars

Dollar bars amostram quando o volume financeiro acumulado (preco x volume) atinge
um limiar fixo.  Cada barra representa a mesma "quantidade de informacao" medida
em dolares transacionados.

**Propriedade IID**: Lopez de Prado demonstra empiricamente (AFML, Teorema 2.1)
que os retornos de dollar bars se aproximam mais de uma distribuicao IID
(independente e identicamente distribuida) do que barras de tempo.  Isso e
fundamental porque a maioria dos modelos de ML assume IID.

### Calibracao do Threshold

```
threshold = mediana(dollar_volume_diario) / 50
```

Usando os primeiros 30 dias para calibrar (evita look-ahead bias), isso produz
~50 barras/dia, resultando em ~36.000 barras ao longo de 2 anos.

### Implementacao Vetorizada

Em vez de iterar ~1 milhao de linhas em Python puro, usamos:
1. `cumsum` sobre `typical_price * volume` (vetorizado)
2. `np.searchsorted` para encontrar as fronteiras das barras
3. `groupby` para agregar OHLCV

Complexidade: O(N) + O(K log N), onde K << N.

---

## Etapa 2: Feature Engineering (Cap. 5 e 18 AFML)

### 2.1 Diferenciacao Fracionaria (FFD) — Cap. 5

**O dilema**: precos em nivel sao nao-estacionarios (raiz unitaria), mas diferenciar
com d=1 (retornos) destroi toda a memoria da serie.  O modelo nao "lembra" de
suportes, resistencias, ou niveis historicos.

**A solucao**: diferenciar com d fracionario (0 < d < 1):

```
(1 - B)^d = SUM_{k=0}^{inf} w_k * B^k
```

onde B e o operador de backshift e os pesos seguem:
```
w_0 = 1
w_k = -w_{k-1} * (d - k + 1) / k
```

Com **d = 0.4**, o resultado:
- Passa no teste ADF de estacionaridade (p-value < 0.05)
- Mantem correlacao > 0.9 com os niveis originais

Isso permite que o modelo use informacao de niveis de preco (suportes/resistencias)
enquanto trabalha com uma serie estacionaria.

### 2.2 VPIN — Volume-Synchronized Probability of Informed Trading (Cap. 18)

VPIN mede a "toxicidade" do fluxo de ordens: quando traders informados dominam
o mercado, o VPIN sobe.

**Por que e essencial para crypto?**
- Detecta pressao de venda informada ANTES de um crash
- Historicamente, VPIN alto precedeu flash crashes em BTC e ETH
- Funciona como indicador antecedente de liquidacoes em cascata

**Algoritmo (Bulk Volume Classification)**:
1. Classificar volume como compra/venda sem dados de tick:
   `Z = (close - open) / std(close - open)`, `buy_pct = Phi(Z)`
2. Preencher buckets de volume fixo sequencialmente
3. `VPIN = media(|V_buy - V_sell| / V_bucket)` sobre ultimos N buckets

### 2.3 Lambda de Kyle (Cap. 18)

Medida de iliquidez baseada em Kyle (1985):
```
delta_p = lambda * signed_volume + epsilon
```

Lambda alto → cada unidade de volume move mais o preco → mercado iliquido.

**Importancia para crypto**:
- Em momentos de stress, lambda explode
- Indicador antecedente de slippage extremo
- Crucial para dimensionamento de posicao

**Implementacao**: regressao rolling de |delta_p| sobre |signed_volume| em janela de 20 barras.

### 2.4 Estimador de Roll (Cap. 18)

O spread bid-ask efetivo pode ser estimado a partir da autocovariancia dos retornos:
```
spread = 2 * sqrt(-cov(dp_t, dp_{t-1}))   quando cov < 0
       = 0                                  quando cov >= 0
```

O "bounce" entre bid e ask cria autocorrelacao negativa.  Quanto maior o spread,
mais negativa a covariancia.

### 2.5 Entropia Lempel-Ziv (Cap. 18)

Mede a complexidade/aleatoriedade da sequencia de retornos:
- **Entropia ALTA** → retornos imprevisiveis (mercado eficiente)
- **Entropia BAIXA** → padroes repetitivos → tendencia forte ou manipulacao

Binarizamos os retornos (1 se positivo, 0 se negativo) e aplicamos o algoritmo
LZ76 em janela rolling de 100 barras.

### 2.6 Fear & Greed Index

Feature macroeconomica exogena.  Usamos o valor do dia ANTERIOR para evitar
leakage (o indice e publicado ao final do dia).

**Utilidade a ser estudada**: correlacao com regimes de mercado, poder preditivo
marginal apos as features de microestrutura.

---

## Etapa 3: Triple-Barrier Method (Cap. 3 AFML)

### Por que nao usar retornos simples como rotulo?

`retorno > 0 → label = 1` ignora:
- A volatilidade do momento (um retorno de 1% em mercado calmo =/= 1% em crash)
- O risco da posicao (sem stop-loss implicito)
- O custo de oportunidade (sem barreira vertical)

### As Tres Barreiras

```
┌─────────────────────────────────────────────────┐
│  PROFIT-TAKE:  upper = close * (1 + pt * sigma) │  → label = +1
│  STOP-LOSS:    lower = close * (1 - sl * sigma) │  → label = -1
│  VERTICAL:     t + max_holding_bars              │  → label =  0
└─────────────────────────────────────────────────┘
```

As barreiras horizontais sao **dinamicas**: escalam com a volatilidade EWM.
Em mercados calmos as barreiras se estreitam; em crises se alargam.

### Parametros Default

- `pt_multiplier = 2.0`, `sl_multiplier = 2.0` (simetrico)
- `max_holding_bars = 50` (~1 dia de dollar bars)
- `volatility_lookback = 20` (EWM span)

### O Par (t0, t1)

Cada label carrega o intervalo [t0, t1] — entrada e toque da barreira.
Isso e **fundamental** para o Purged K-Fold: precisamos saber quais barras
futuras foram usadas para definir cada rotulo.

---

## Etapa 4: Meta-Labeling (Cap. 3.6 AFML)

### O Conceito Central

Em vez de um unico modelo:

**Estagio 1 (Modelo Primario)**: prediz direcao (+1 ou -1).
Tipicamente tem recall alto mas precision baixa (muitos falsos positivos).

**Estagio 2 (Meta-Modelo)**: recebe as mesmas features e decide:
"Devo confiar na predicao do modelo primario?"

```
meta_label = 1   se primary_pred == true_label   (correto)
meta_label = 0   se primary_pred != true_label   (incorreto)
```

**Resultado final**:
- Se meta_prob > 0.5 → manter a predicao primaria
- Se meta_prob <= 0.5 → nao apostar (label = 0)

### Por que funciona?

O meta-modelo aprende a FILTRAR os falsos positivos do modelo primario.
Exemplo: o primario diz "compra", mas o meta-modelo reconhece que nessa
combinacao de features o primario costuma errar → filtra o trade.

Resultado: melhoria significativa no F1-Score e Sharpe Ratio.

---

## Etapa 5: Purged K-Fold CV com Embargo (Cap. 7 AFML)

### O Problema do K-Fold Ingenuo

No K-Fold padrao, um rotulo no fold de teste pode ter sido determinado por
barras que estao no fold de treino (porque o triple-barrier olha para o futuro).
Isso gera leakage e superestima a performance.

### Solucao

1. **PURGE**: remove do treino qualquer amostra cujo span [t0, t1] se sobreponha
   com qualquer amostra do teste.

2. **EMBARGO**: remove do treino as primeiras N amostras APOS o fold de teste,
   prevenindo leakage de features com lag (rolling windows).

3. Folds sao **contiguos** (nao embaralhados) para respeitar a ordem temporal.

### Parametros

- `n_folds = 5`
- `purge_pct = 0.01` (1% das amostras, ~360 barras — cobre o max_holding de 50)
- `embargo_pct = 0.01`

---

## Etapa 6: Avaliacao

### MDA — Mean Decrease Accuracy (Cap. 8 AFML)

**Por que NAO usar Gini importance (MDI)?**
- MDI e viesado para features com alta cardinalidade
- Nao funciona out-of-sample
- Nao captura interacoes entre features correlacionadas

**MDA e mais confiavel porque**:
1. Mede no conjunto de TESTE (out-of-sample)
2. Permuta cada feature e mede a queda de accuracy
3. Features importantes causam grande queda; irrelevantes, nenhuma

### PSR — Probabilistic Sharpe Ratio (Cap. 14 AFML)

O Sharpe Ratio convencional ignora tamanho da amostra e distribuicao dos retornos.
O PSR corrige isso:

```
PSR = Phi[ (SR - SR*) * sqrt(T-1) / sqrt(1 - skew*SR + (kurt-1)/4 * SR^2) ]
```

- **PSR > 0.95** → performance estatisticamente significativa a 95%
- **PSR < 0.50** → nao podemos rejeitar que o SR e apenas ruido

---

## Features Essenciais para Criptoativos (Resumo)

| Feature | Descricao | Por que importa |
|---------|-----------|-----------------|
| **FFD Close (d=0.4)** | Preco fracionariamente diferenciado | Preserva memoria de suportes/resistencias, ao contrario de retornos log puros |
| **VPIN** | Probabilidade de informed trading | Detecta pressao de venda informada antes de crashes |
| **Kyle Lambda** | Impacto de preco por unidade de volume | Mede iliquidez; crucial para evitar slippage em BTC/ETH |
| **Roll Spread** | Spread efetivo estimado | Proxy de custos de transacao; sobe em crises |
| **LZ Entropy** | Complexidade do fluxo de ordens | Entropia baixa → tendencia forte; alta → mercado eficiente |
| **Fear & Greed** | Sentimento macro | Feature exogena; utilidade a ser validada pelo MDA |
| **Volatilidade 20** | EWM std dos retornos | Controle de regime; escala as barreiras |
| **Momentum 5/20** | Retornos de curto e medio prazo | Captura tendencia e mean-reversion |
| **Log Volume** | Volume em escala logaritmica | Proxy de atividade e interesse |

---

## Como Executar

```bash
cd regime_detection
pip install -r requirements.txt
python marcos.py
```

### Saida Esperada

1. Console: diagnosticos de cada etapa (shapes, ADF test, distribuicao de labels, CV folds, MDA ranking, PSR)
2. Diretorio `save_point_marcos/` com 5 PNGs:
   - `dollar_bars_sampling.png` — distribuicao de ticks e dollar volume por barra
   - `feature_importance_mda.png` — ranking MDA das features
   - `triple_barrier_labels.png` — preco com rotulos coloridos
   - `meta_label_filtering.png` — trades mantidos vs filtrados
   - `cumulative_returns.png` — retorno acumulado com PSR

---

## Configuracao Avancada

O `MarcosPipeline` aceita um dicionario `config` para override de qualquer parametro:

```python
pipeline = MarcosPipeline(
    data_dir="data",
    save_dir="save_point_marcos",
    config={
        "ffd_d": 0.35,           # menos diferenciacao (mais memoria)
        "pt_multiplier": 1.5,    # barreiras mais apertadas
        "sl_multiplier": 2.5,    # stop-loss mais largo
        "max_holding_bars": 30,  # ~0.6 dias
        "n_folds": 10,           # mais folds
        "bars_per_day": 100,     # mais dollar bars (menor threshold)
    }
)
```


### Melhorias

É sempre possível tornar o modelo mais sofisticado na tentativa de melhorar sua capacidade preditiva. Embora nem sempre isso ocorra, para que tenhamos mais chance de sucesso devemos focar nas informações que usaremos de input, trabalhando com novas features. Até agora trabalhamos com um conjunto de dados simples: OHLCV BTC/USDT da Binance e Fear and Greed da alternative. Agora devemos nos atentar a novas métricas.

- Features de Quebras Estruturais e Explosividade:
Para que o modelo aprenda a distinguir entre tendências sustentáveis e bolhas especulativas, você deve buscar:
SADF (Supremum Augmented Dickey-Fuller): Um teste recursivo que identifica comportamentos de bolha e o momento exato em que elas começam a "estourar"
.
Filtro CUSUM: Detecta mudanças na média de uma série (como volatilidade ou volume), sendo útil para identificar transições de regime de mercado
.
SMT (Sub- and Super-Martingale Tests): Permite detectar explosividade sem as restrições paramétricas dos testes ADF tradicionais

 - Amostragem Baseada em Informação: Além das barras de dólar, você pode extrair features de Barras de Desequilíbrio (Imbalance Bars) e Barras de Sequências (Runs Bars), escolhendo qual funciona melhor para seu objetivo.
.Desequilíbrio de Volume/Dólar (VIB/DIB): Estas barras são amostradas quando o desequilíbrio do fluxo de ordens diverge das expectativas iniciais, capturando a presença de traders informados
.Sequências de Ticks/Volume (TRB/VRB): Monitoram sequências persistentes de compras ou vendas (como varreduras no livro de ordens), que revelam quando grandes participantes estão fatiando ordens ou agredindo o mercado

- Microestrutura de Mercado Avançada
O histórico de bid-ask (via Tardis ou fontes similares, como observado fora das fontes) permite extrair mais do que o spread:
Lambdas de Amihud e Hasbrouck: Complementam o Lambda de Kyle, medindo o impacto do dólar transacionado no log-preço e o custo efetivo de execução
.Distribuição de Tamanho de Ordens: Monitorar a frequência de ordens com "tamanhos redondos" (ex: 1.0, 10, 50 BTC) pode ajudar a identificar a presença de traders humanos (GUI traders) versus algoritmos que randomizam tamanhos para se camuflar
.Taxas de Cancelamento e Substituição: Grandes volumes de cancelamentos podem indicar algoritmos predatórios, como quote stuffing ou liquidity squeezers, que tentam enganar outros participantes
.Assinatura de Algoritmos TWAP: Identificar execuções que ocorrem em intervalos de tempo fixos (ex: início de cada minuto) permite antecipar fluxos institucionais de grande escala

- Transformações de Memória (FFD)
Uma das contribuições mais importantes das fontes é a Diferenciação Fracionária (FFD)
. Em vez de usar retornos logarítmicos simples (que apagam a memória estatística), aplique FFD nos preços para obter uma série que seja estacionária, mas que ainda mantenha a correlação com os níveis originais (suportes e resistências)

- Dados de Opções e Derivados
Se você tiver acesso a dados de opções de BTC, pode extrair:
Divergência na Paridade Put-Call: Quando o preço implícito nas opções diverge do preço spot, isso geralmente indica uma assimetria de informação que o mercado de opções capturou primeiro
.Preço Implícito de Opções: Extrair toda a distribuição de resultados precificados pelo mercado, em vez de apenas o valor médio

- Informação Microestrutural (ϕ):
Você pode criar uma feature proprietária chamada Informação Microestrutural (ϕ). Ela é derivada da entropia cruzada (cross-entropy) de um modelo de market making simulado: quando a perda do modelo aumenta, significa que a complexidade do fluxo cresceu e a probabilidade de seleção adversa (traders informados explorando provedores de liquidez) é alta

- Dados Alternativos Adicionais
As fontes sugerem aglomerar dados "difíceis de processar", como:
Buscas no Google e Redes Sociais: Sentimentos extraídos de chats e Twitter
.
Fluxos de Transações On-chain: Embora não citados explicitamente como "on-chain" (termo cripto), as fontes mencionam o uso de metadados e registros de transações de agências
.

Ao fundir esses dados, use o Meta-labeling para que o modelo aprenda não apenas o lado da aposta, mas se as condições atuais (medidas por essas novas features) favorecem ou não a execução do sinal primário
. Além disso, valide os resultados usando Purged K-Fold Cross-Validation para evitar vazamento de dados (leakage) entre as observações sobrepostas.

Mais features uteis:

Yield curve slope (10Y - 2Y treasury): inversão prevê recessão → risk-off
DXY momentum (índice do dólar): dólar forte → cripto fraca historicamente
Funding rates de perpetuais: funding negativo persistente = smart money bearish
On-chain: MVRV Z-score: mede se BTC está sobrevalorizado vs. custo médio de aquisição


---

## Referencias

1. Lopez de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley.
2. Lopez de Prado, M. (2020). *Machine Learning for Asset Managers*. Cambridge.
3. Kyle, A. S. (1985). *Continuous Auctions and Insider Trading*. Econometrica.
4. Roll, R. (1984). *A Simple Implicit Measure of the Effective Bid-Ask Spread*. JoF.
5. Easley, D., Lopez de Prado, M., & O'Hara, M. (2012). *Flow Toxicity and Liquidity in a High-Frequency World*. RFS.
