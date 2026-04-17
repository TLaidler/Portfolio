# Pipeline de Marcos Lopez de Prado

> Voce sabe funcoes, graficos, media, desvio padrao e probabilidade.
> Isso e tudo que precisa para entender cada etapa.

---

## O que estamos tentando fazer?

O preco do Bitcoin muda a cada segundo. Queremos construir um programa de computador
que olhe para os dados e responda: **"o preco vai subir, cair, ou ficar parado?"**

Parece simples, mas tem armadilhas escondidas em cada canto. O Lopez de Prado, um
matematico que gerencia bilhoes de dolares, criou um passo-a-passo para evitar essas
armadilhas. Vamos entender cada uma.

---

## Etapa 1: Dollar Bars — Quando amostrar os dados?

### O problema

Os dados do Bitcoin vem de minuto em minuto. As 3 da manha, quase ninguem esta
negociando — mas recebemos a mesma quantidade de dados que ao meio-dia, quando
milhares de pessoas estao comprando e vendendo.

Imagine que voce esta gravando o som de uma rua. Se voce grava 1 segundo a cada
minuto, de madrugada voce grava silencio (inutil) e no horario de pico voce perde
a maioria das conversas (informacao perdida).

### A solucao

Em vez de amostrar a cada 1 minuto (intervalo fixo de tempo), amostramos a cada
X dolares negociados. Quando muita gente esta negociando, geramos mais amostras.
Quando esta calmo, menos.

```
Barra normal:     1 amostra a cada 1 minuto  (fixo no tempo)
Dollar bar:       1 amostra a cada $400 milhoes negociados  (fixo no "movimento")
```

### Por que funciona?

Cada amostra agora representa a mesma "quantidade de atividade". Isso faz com que
os dados se comportem de forma mais previsivel — como se cada amostra fosse
independente das outras. Na estatistica, isso se chama IID (independente e
identicamente distribuido), e e o que a maioria dos modelos matematicos precisa
para funcionar.

### Na pratica

Com o Bitcoin, isso gera ~50 amostras por dia (em vez de 1.440 amostras de 1 minuto).
Em dias agitados, as amostras ficam mais juntas no tempo; em dias calmos, mais
espalhadas.

---

## Etapa 2: Diferenciacao Fracionaria — Lembrar sem baguncar

### O problema

O preco do Bitcoin em 2024 era ~$70.000 e em 2025 talvez ~$90.000. Essa serie de
precos e o que os estatisticos chamam de "nao-estacionaria" — a media muda ao longo
do tempo. Isso bagunca todos os calculos estatisticos.

A solucao classica e calcular a **variacao** de um periodo para outro:

```
variacao = preco_hoje - preco_ontem
```

Isso resolve a nao-estacionaridade, mas cria outro problema: a variacao "esquece"
tudo.  O programa nao sabe se o Bitcoin esta em $30.000 ou $100.000 — so ve que
subiu $500. Ele perde a nocao de "niveis importantes" (tipo uma regiao de preco
onde o BTC costuma parar de cair).

### A solucao: diferenciacao "pela metade"

Em vez de subtrair o preco de ontem por completo (diferenca de ordem 1), subtraimos
"parcialmente" (diferenca de ordem 0.4):

```
Ordem 0:    preco original  →  lembra tudo, mas nao-estacionario
Ordem 0.4:  meio-termo      →  lembra bastante E e estacionario
Ordem 1:    variacao pura   →  estacionario, mas esqueceu tudo
```

Na pratica, e uma media ponderada do preco atual com os precos passados, onde os
pesos decaem lentamente. O resultado:
- Ainda sobe e desce com o preco (mantem ~90% de correlacao com o original)
- Mas nao tem mais aquele "drift" de longo prazo que bagunca a estatistica

### Como sabemos que funcionou?

Rodamos o teste ADF (Augmented Dickey-Fuller). E um teste estatistico que responde:
"essa serie tem tendencia crescente/decrescente embutida?"

- Se p-value < 0.05: nao tem tendencia → estacionaria → OK!
- Se p-value > 0.05: tem tendencia → nao-estacionaria → precisa diferenciar mais

No nosso caso: p-value = 0.000000. Estacionaria com folga.

---

## Etapa 3: Features — O que o modelo vai olhar?

Features sao as "pistas" que damos ao modelo para ele decidir. Em vez de jogar o
preco bruto, calculamos indicadores que resumem o que esta acontecendo no mercado.

### 3.1 VPIN — Alguem sabe algo que eu nao sei?

Imagine um jogo de cartas onde alguns jogadores viram as cartas antes dos outros.
Esses jogadores vao comprar ou vender agressivamente, criando um **desequilibrio**
entre ordens de compra e venda.

VPIN mede esse desequilibrio:

```
VPIN = media( |volume_compra - volume_venda| / volume_total )
```

- VPIN alto: alguem esta comprando (ou vendendo) muito mais que o normal → perigo
- VPIN baixo: equilibrio entre compras e vendas → mercado "saudavel"

### 3.2 Kyle Lambda — Quanto custa mover o preco?

Se voce compra 1 Bitcoin e o preco sobe $100, o lambda e 100.
Se voce compra 1 Bitcoin e o preco sobe $10, o lambda e 10.

```
lambda = variacao_preco / volume_negociado
```

Lambda alto = mercado "travado" (pouca liquidez, dificil negociar sem mover o preco).
Lambda baixo = mercado "liquido" (facil negociar sem impactar o preco).

Isso e calculado por regressao linear numa janela de 20 amostras.

### 3.3 Roll Spread — Qual o custo escondido?

Quando voce compra Bitcoin, paga um preco (ask). Quando vende, recebe outro (bid).
A diferenca entre eles e o "spread" — um custo invisivel em cada operacao.

Roll descobriu que esse spread pode ser estimado a partir de uma propriedade
estatistica: a **covariancia** entre variacoes consecutivas de preco.

```
Se Cov(dp_t, dp_{t-1}) < 0:    spread = 2 * raiz(-Cov)
Se Cov >= 0:                     spread = 0
```

Por que funciona: o preco "quica" entre bid e ask, criando uma correlacao negativa
(subiu → corrigiu → subiu → corrigiu). Quanto maior o spread, mais forte esse quique.

### 3.4 Entropia de Lempel-Ziv — O mercado e previsivel?

Transformamos os retornos em uma sequencia de 0s e 1s:
- Subiu → 1
- Caiu → 0

Exemplo: `1 1 1 0 0 0 1 1 1 0 0 0` (padrao repetitivo, facil de prever)
Exemplo: `1 0 1 1 0 0 1 0 1 0 1 1` (aleatorio, dificil de prever)

O algoritmo de Lempel-Ziv conta quantos "blocos novos" aparecem na sequencia.
Poucos blocos novos = padrao repetitivo = **entropia baixa** = mercado previsivel.
Muitos blocos novos = aleatorio = **entropia alta** = mercado dificil.

### 3.5 Fear & Greed — O humor do mercado

Um indice de 0 a 100 que resume o "sentimento" dos investidores:
- 0-25: medo extremo (todo mundo com medo de perder dinheiro)
- 75-100: ganancia extrema (todo mundo acha que vai ficar rico)

Usamos o valor do dia ANTERIOR para evitar "espiar o futuro" (o indice so e
publicado no final do dia).

### 3.6 Retornos e Volatilidade

- **ret_5**: quanto o preco mudou nas ultimas 5 amostras (tendencia de curto prazo)
- **ret_20**: quanto mudou nas ultimas 20 amostras (tendencia de medio prazo)
- **volatility_20**: desvio padrao dos retornos nas ultimas 20 amostras
  (quanto o preco esta "balancando")
- **log_volume**: logaritmo do volume (quanta atividade esta acontecendo)

---

## Etapa 4: Triple Barrier — Como definir "subiu", "caiu" ou "nada"?

### O problema com a abordagem ingenua

A forma mais simples de rotular seria: "se o preco subiu nas proximas 50 amostras,
label = +1". Mas isso ignora que subir 1% num dia calmo e muito diferente de subir
1% num dia caotico.

### A solucao: tres "cercas"

Para cada amostra, colocamos tres limites:

```
        ┌─── Cerca de cima (profit): preco_entrada * (1 + 2 * volatilidade)
        │
  Preco ┤
        │
        └─── Cerca de baixo (loss):  preco_entrada * (1 - 2 * volatilidade)

  E um cronometro: 50 amostras para frente (cerca de tempo)
```

Andamos para frente no tempo e vemos o que acontece primeiro:

- Se o preco SOBE e bate na cerca de cima → **label = +1** (deu lucro)
- Se o preco DESCE e bate na cerca de baixo → **label = -1** (deu prejuizo)
- Se o cronometro acaba sem bater nenhuma cerca → **label = 0** (indefinido)

### Por que as cercas escalam com a volatilidade?

Em dias calmos (volatilidade baixa), as cercas ficam mais apertadas — um movimento
de 1% ja e significativo. Em dias caoticos (volatilidade alta), as cercas se
alargam — precisamos de um movimento maior para considerar "significativo".

Isso e como ajustar a sensibilidade de um instrumento de medicao: se o ruido de
fundo e alto, voce precisa de um sinal mais forte para considerar uma deteccao.

---

## Etapa 5: Purged K-Fold — Validacao cruzada honesta

### O que e validacao cruzada?

Para saber se um modelo e bom, voce nao pode testa-lo nos mesmos dados que usou
para treinar (seria como estudar a prova sabendo as respostas).

K-Fold divide os dados em K pedacos. Treina em K-1 e testa no restante. Repete K
vezes, cada vez testando num pedaco diferente.

### O problema com series temporais

Na etapa anterior (Triple Barrier), para definir o rotulo de cada amostra, olhamos
para as **proximas 50 amostras**. Isso significa que o rotulo da amostra #100
depende dos precos das amostras #101 a #150.

Se a amostra #100 esta no conjunto de teste e as amostras #101-#150 estao no treino,
o modelo de treino "sabe" parcialmente a resposta do teste. Isso e **vazamento de
informacao** (leakage) e faz o modelo parecer melhor do que realmente e.

### A solucao: purging + embargo

1. **Purge** (limpeza): para cada amostra de teste, removemos do treino qualquer
   amostra cujo intervalo [entrada, saida] se sobreponha com algum intervalo do
   teste.

2. **Embargo**: removemos do treino as primeiras amostras logo APOS o conjunto de
   teste (para evitar vazamento de features que usam medias moveis).

3. Os pedacos (folds) sao **sequenciais** no tempo (nao embaralhados).

```
Tempo: ─────────────────────────────────────────────────────────────
        [  Treino  ][PURGE][  Teste  ][EMBARGO][  Treino  ]
```

---

## Etapa 6: Meta-Labeling — Filtro de alarmes falsos

### A analogia

Imagine um detector de fumaca:
- **Modelo primario** (detector sensivel): dispara para qualquer fumacinha.
  Pega todos os incendios reais, mas tambem dispara para torrada queimada,
  vapor do chuveiro, etc. (muitos alarmes falsos)

- **Meta-modelo** (filtro inteligente): olha para o contexto (hora do dia,
  temperatura, umidade) e decide: "esse alarme e real ou falso?"

### Como funciona

1. **Modelo primario**: treinamos um Random Forest para prever direcao (+1 ou -1).
   Ele acerta bastante, mas tambem erra bastante.

2. **Meta-labels**: para cada previsao do modelo primario no treino, marcamos:
   - 1 se ele acertou
   - 0 se ele errou

3. **Meta-modelo**: treinamos outro Random Forest para prever "o modelo primario
   vai acertar neste caso?". Ele aprende em quais situacoes o primario e confiavel.

4. **Resultado final**:
   - Se o meta-modelo diz "confiar" (probabilidade > 50%): usamos a previsao primaria
   - Se diz "nao confiar": nao fazemos nada (label = 0, ficar de fora)

O resultado e que erramos MENOS — filtramos os casos onde o primario costuma errar.

---

## Etapa 7: Avaliacao — Os resultados sao de verdade?

### MDA (importancia das features)

Para saber qual feature e mais importante:

1. Medimos a accuracy do modelo no teste: ex. 68%
2. Embaralhamos aleatoriamente uma feature (ex: VPIN) — destruindo sua informacao
3. Medimos de novo: ex. 65%
4. A queda (68% - 65% = 3%) e a importancia daquela feature

Se embaralhar uma feature e a accuracy nao muda, aquela feature era inutil.
Se cai muito, era essencial.

### PSR (o resultado e sorte ou habilidade?)

O Sharpe Ratio mede retorno/risco: `SR = media(retornos) / desvio_padrao(retornos)`.
Um SR positivo parece bom, mas pode ser sorte com poucos dados.

O PSR responde: **"qual a probabilidade de que esse Sharpe Ratio positivo NAO seja
sorte?"**

```
PSR = probabilidade de que o SR real seja maior que zero
```

- PSR > 0.95: 95% de chance de ser habilidade, nao sorte → **significativo**
- PSR < 0.50: cara ou coroa → provavelmente sorte

O PSR e mais rigoroso que o SR simples porque leva em conta:
- Quantas amostras temos (mais amostras = mais confianca)
- Se os retornos sao simetricos ou enviesados (assimetria)
- Se tem caudas pesadas (eventos extremos)

---

## Resumo: por que cada etapa existe

| Etapa | Problema que resolve | Consequencia se pular |
|-------|---------------------|-----------------------|
| Dollar Bars | Dados com "tempo morto" e sub-amostragem | Modelo treina em ruido, testes estatisticos invalidos |
| FFD (d=0.4) | Serie nao-estacionaria vs perda de memoria | Ou o modelo nao funciona (nao-estacionario) ou perde informacao crucial (retornos puros) |
| Features (VPIN, Kyle, etc) | Modelo precisa de "pistas" boas | Com pistas ruins, o modelo nao aprende nada |
| Triple Barrier | Labels ingenuas ignoram volatilidade e risco | Modelo aprende a classificar algo sem significado economico |
| Purged K-Fold | Validacao cruzada padrao vaza informacao | Voce ACHA que o modelo e bom, mas em producao ele falha |
| Meta-Labeling | Modelo primario tem muitos alarmes falsos | Voce opera em sinais ruins e perde dinheiro |
| MDA + PSR | Resultados podem ser artefatos estatisticos | Voce implementa um modelo que so funciona no passado |

Cada etapa e uma barreira contra o **autoengano**. O objetivo nao e ter o modelo
mais sofisticado — e ter o modelo mais **honesto**.



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
