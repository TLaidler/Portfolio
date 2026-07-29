# Debate: Modelo de abertura USDBRL pré-mercado — Marcos López de Prado × Jim Simons

**Data:** 2026-07-27
**Contexto:** Sessão de desenho (design review) de um modelo para estimar o preço de abertura do USDBRL spot
(~9:00 BRT, proxy do fixing de um banco parceiro), para uso do trader pré-mercado (~8:50 BRT).
Base: inventário completo dos dados disponíveis (dez/2023 → ago/2024, histórico imutável).

**Checklist de armadilhas clássicas apresentado aos debatedores (o que o desenho deve excluir por construção):**
1. 🔴 Target contemporâneo às features: com o spot implícito do futuro em X e o spot do mesmo minuto em y,
   qualquer modelo "aprende" apenas a base futuro-spot (tautologia) e o erro vira reconciliação de preço.
2. 🔴 `shuffle=True` em splits de série temporal e CV embaralhada: o teste vira interpolação de vizinhos de 1 minuto.
3. 🔴 Imputação com estatísticas do dataset inteiro antes do split; janelas "futuras" que incluem o presente.
4. 🔴 Macro alinhado por data de referência (não publicação) → semanas de lookahead via ffill.
5. 🟠 Shifts fixos de timezone (não aware); flags de reunião ativas antes do anúncio; features pré-mercado
   sem um target de abertura explicitamente definido.

---

## RODADA 1

### Dr. Marcos López de Prado — posição inicial

#### 1. Os pecados capitais que este desenho precisa excluir

Este problema convida a um catálogo quase completo dos erros que documentei em *Advances in Financial Machine Learning*. Antes de propor qualquer coisa, deixo explícito o que invalidaria o estudo:

**Pecado 1 — Tautologia disfarçada de previsão (leakage contemporâneo).** Treinar `close_bloom(t)` com `dolar_cc(t)` em X não é um modelo: é uma calculadora de basis. Um MAE minúsculo nesse arranjo mede a qualidade da reconciliação futuro-spot via paridade coberta de juros — algo que já sabemos por arbitragem — e o desvio residual é ruído de microestrutura da base, não erro de previsão. **Métricas produzidas assim não têm valor probatório.**

**Pecado 2 — Destruição da estrutura temporal.** `shuffle=True` em séries com autocorrelação serial de ~0.99 em nível significa que cada ponto de teste tem vizinhos de 1 minuto no treino. Isto é o caso extremo do que exige *purging*: sem purge e embargo, o R² é uma medida de interpolação, não de generalização. Pior ainda seria rodar `cross_val_score` no dataset completo ou refitar o modelo final com dados de validação: isso elimina qualquer conjunto verdadeiramente out-of-sample e o backtest morre antes de nascer.

**Pecado 3 — Leakage por data de publicação.** CPI/PIB indexados por data de referência com ffill dariam ao modelo ~6 semanas de informação futura. Adiciono: DGS do FRED com defasagem de ~1 dia entra no cupom cambial — logo **o próprio `dolar_cc` histórico pode estar contaminado** se `us_rate(t)` usa o valor publicado em t+1. Isto precisa de auditoria vintage.

**Pecado 4 — Leakage de pré-processamento e de construção.** Imputação global com a média do dataset, janelas de "média futura" que incluem o presente, target algebricamente contido nas features, `sample_weight` derivado do target, shift fixo de −3h ignorando DST. Cada um sozinho invalida um estudo.

**Pecado 5 — Não formular o problema.** Construir features "pré-mercado" e usá-las para prever cada minuto do dia contemporaneamente é responder a uma pergunta que ninguém fez. O target de abertura precisa existir explicitamente antes de qualquer fit.

#### 2. Reformulação do problema

Aqui está o ponto central e vou ser direto: **isto não é um problema de previsão; é um problema de nowcast/basis-adjustment com correção residual.**

O 6L negocia 23h/dia. Às 8:50 BRT, o mercado já precificou toda a informação overnight. Por arbitragem coberta:

    spot_implícito(8:50) = dolar_cc(8:50) = (100/close_6L) / C_C

O fixing das 9:00 no banco parceiro difere disso por: (i) basis idiossincrática do fixing (spread do banco, fluxo de abertura), (ii) 10 minutos de drift. Portanto o target correto é o **resíduo**:

    y_d = open_bloom(d, 9:00) − dolar_cc(d, 8:50)

ou, em forma estacionária, y_d em retorno logarítmico: `log(open/dolar_cc_8:50)`. Nunca o nível. Prever nível com features em nível produz R²~1 espúrio por cointegração trivial.

Por que residual e não retorno close→open? Porque `dolar_cc(8:50)` já contém a informação overnight; o retorno close→open desperdiça o 6L, que é o ativo mais informativo disponível. O modelo de ML só precisa prever o que o mercado de futuros **não** precifica: a micro-basis do fixing. Se essa basis for ruído branco com média estável, a resposta honesta é "não há alfa de ML aqui; use dolar_cc + ajuste médio" — e isso também é um resultado válido.

#### 3. Dataset point-in-time

- **Uma linha por dia útil, snapshot congelado às 8:50 BRT** (timezone-aware, `America/Sao_Paulo`, nunca shift fixo). Aceito perder os 69k pontos intraday: eles são pseudo-réplicas com dependência serial massiva; o **tamanho amostral efetivo** do problema intraday, após corrigir autocorrelação, não é muito maior que os ~140 dias. Melhor 140 amostras honestas que 69k fraudulentas.
- Features às 8:50: dolar_cc(8:50); retorno overnight do 6L (17:58 d-1 → 8:50); realized vol overnight do 6L; DXY overnight; close_binan(8:49) e spread cripto (24/7 — proxy valioso de fluxo BRL overnight); EWZ **apenas close d-1**; CDS último tick disponível ≤8:50; VIX close d-1.
- Macro por **vintage**: cada valor entra na primeira data em que estava publicamente disponível às 8:50 BRT. Flags COPOM/FED separadas em "anúncio hoje ainda não ocorrido" vs "ocorreu ontem". PIB real: frequência trimestral em 7 meses de dados = 2-3 observações — **inútil como feature; rejeito a inclusão** salvo como dummy de dia de publicação.
- Imputação: apenas last-observation-carried-forward até 8:50 (isso É point-in-time); estatísticas de normalização calculadas exclusivamente no treino de cada fold.

#### 4. Validação

Com ~140 amostras, CPCV é luxo estatístico frágil; prescrevo **walk-forward expandindo com purge de 1 dia e embargo de 5 dias**, mínimo 60 dias de treino inicial, passo de 5 dias. Métricas: MAE em pontos de basis, e **teste de Diebold-Mariano contra dois benchmarks obrigatórios**: (b1) open = dolar_cc(8:50) [random walk informado]; (b2) open = dolar_cc(8:50) + média móvel 20d da basis. Se o modelo não bate b2 com significância, não existe. Reportar **Deflated Sharpe / PBO** sobre o número real de configurações testadas — incluindo toda tentativa descartada ao longo da pesquisa.

#### 5. Modelo

Com N≈140 e alvo de variância minúscula: **no máximo regressão linear regularizada (Lasso/ElasticNet) com ≤5 features**, coeficientes com bootstrap em blocos. Nenhuma floresta, nenhum boosting — a razão parâmetros/amostras não sustenta. Feature importance via MDA em walk-forward, nunca seleção de features sobre dados vazados. **Meta-labeling sim, invertido**: modelo primário = dolar_cc(8:50); modelo secundário binário prevê "hoje a basis será anormalmente grande?" (dias de COPOM/FED, stress de CDS) — dimensiona a confiança do trader, que é o uso real pré-mercado.

#### 6. Três desafios para Jim Simons

1. Jim, com 140 observações efetivas, você defenderia qualquer modelo não-linear — ou concorda que aqui a estatística clássica domina o ML?
2. Você aceitaria explorar o grid intraday 1min se o target for reformulado — e como você corrigiria o tamanho amostral efetivo dada a dependência serial da basis?
3. O spread Binance-Bloomberg 24/7 é o único preço de BRL "onshore-adjacente" overnight: sinal de fluxo ou ruído de stablecoin? Como você o testaria sem sobreajustar 7 meses de dados?

---

### Jim Simons — posição inicial

#### 1. Diagnóstico pragmático

Na Renaissance, um projeto assim morreria em cinco minutos se cometesse um único erro: **prever o presente**. Treinar o spot do minuto t com dolar_cc do minuto t não é previsão, é uma regressão da base futuro-spot contra ela mesma — o MAE sai minúsculo porque mede o custo de reconciliação entre duas cotações do mesmo ativo. Já vi dezenas de pesquisadores brilhantes chegarem com Sharpe 15 no backtest; a primeira pergunta é sempre "onde está o lookahead?". E shuffle no split de série temporal é o segundo prego no caixão: com autocorrelação de 1 minuto, shuffle garante que o teste contém vizinhos temporais do treino.

Dito isso — e isso é importante — **há coisas que valem ouro aqui**. O dolar_cc é exatamente o que eu chamaria de âncora arbitrage-free: o spot implícito no futuro CME via cupom cambial. Isso não é um sinal de ML, é matemática de não-arbitragem — qualquer seletor de features o apontaria como dominante justamente pela tautologia. Mas como **baseline**, é excelente. E o spread USDT/BRL Binance vs. Bloomberg é informação genuinamente interessante: é o único preço de BRL que negocia enquanto o Brasil dorme, e carrega fluxo real (remessas, cripto-arb, fuga de capital). Se há alfa nesse dataset, está aí e no comportamento overnight do 6L — não no XGBoost.

#### 2. O trade real

O trader às 8:50 não precisa de "um número". Ele já **tem** o número: dolar_cc às 8:50, calculado do 6L que negociou a noite inteira. Qualquer previsão de abertura que não bata esse benchmark é inútil por construção. O que ele precisa — e onde está o dinheiro — é a resposta a: **a abertura do fixing do banco parceiro vai desviar do implícito no futuro, em que direção, e o desvio é grande o suficiente para agir?** Ou seja: modele o **resíduo** `r = abertura_bloom(9:00) − dolar_cc(8:55)`. Esse resíduo é a soma de microestrutura do fixing, atraso de ajuste do spot on-shore e ruído. Se ele tem componente previsível, o trade é direcional e pequeno; se não tem, o modelo honesto diz "use o futuro" e isso também é uma resposta valiosa.

#### 3. Minha abordagem

Com **130-160 observações diárias** — porque o problema real é 1 previsão por dia, os 69k minutos são ilusão de amostra — a matemática é brutal: você suporta talvez 3 a 5 parâmetros efetivos. Nada de gradient boosting, nada de redes. Eu faria:

1. **Baseline zero**: previsão = dolar_cc(8:55). Meça o erro dele primeiro. Se σ desse erro for da ordem do spread bid-ask do fixing, pare — não há dinheiro.
2. **Estude o resíduo antes de modelá-lo**: autocorrelação, média por dia da semana, comportamento em dias de COPOM/FED/payroll, correlação com retorno overnight do DXY e do USDT/BRL. Uma semana de análise exploratória honesta vale mais que um mês de tuning.
3. **Regressão linear regularizada (ridge) com 4-6 sinais fracos**, todos computáveis às 8:55: retorno overnight do 6L, retorno overnight do USDT/BRL, mudança do spread binan-bloom desde o último close, retorno overnight do DXY, resíduo de ontem (mean-reversion do fixing), dummy de dia de reunião. Muitos sinais fracos, combinados linearmente — é assim que sempre funcionou para nós. Cada um explica 1-2%? Ótimo, é disso que se vive.
4. **Validação walk-forward pura**: treine em dias 1-90, preveja 91-120, expanda. Sem shuffle, nunca. Com 7 meses, você tem talvez 40-60 previsões out-of-sample genuínas. É pouco — então a barra estatística tem que ser explícita.
5. **Higiene de dados antes de tudo**: timezone-aware (um shift fixo de −3h erraria 1h durante o DST americano, exatamente na janela pré-mercado que importa), imputação só com dados passados, releases alinhados por data de publicação. Nós gastávamos mais tempo limpando dados do que modelando. Sempre.

#### 4. PIB e macro mensal

Sejamos honestos: em 7 meses há **2 releases de PIB**. Duas observações. Incluir isso num modelo é convidar o overfitting para jantar — o modelo aprenderá o que aconteceu naqueles dois dias específicos e chamará de "efeito PIB". Meu veredito: **não inclua como feature contínua**. No máximo, uma dummy "dia de release macro relevante" (agregando PIB, CPI, payroll, IPCA num único indicador de "dia de evento"), que pelo menos tem 15-20 ocorrências. O nível do PIB não prevê a abertura de amanhã; o que move a abertura é o que aconteceu entre 18h e 9h, e isso está no 6L, no DXY e na Binance.

#### 5. Critério de sucesso

Benchmark: `abertura = dolar_cc(8:55)`. O modelo só entra em produção se, **out-of-sample walk-forward**:
- MAE do modelo < MAE do benchmark com melhora ≥ 15-20%, e um teste Diebold-Mariano (ou bootstrap simples dos erros pareados) rejeitando igualdade — com 50 previsões, melhoras de 5% são ruído;
- **Acerto direcional do sinal do resíduo > 58-60%** quando |resíduo previsto| > limiar, com o limiar acima do custo de transação do trader. Direção condicionada é onde está o dinheiro, não o MAE;
- Estabilidade: a melhora aparece nas duas metades do período de teste, não concentrada em 3 dias.

#### 6. Três perguntas para López de Prado

1. Marcos, você vai propor purged k-fold com embargo, fractional differentiation e meta-labeling — mas com **50 previsões out-of-sample**, qual é o poder estatístico real de qualquer teste que você proponha? Sua maquinaria não é elegância sem denominador?
2. Triple-barrier e sample weights pressupõem que definimos "evento". Aqui o evento é fixo (9:00 BRT, todo dia). O que do seu arsenal sobrevive quando o problema é uma única previsão diária de horário fixo?
3. Você aceitaria colocar dinheiro num sinal com 7 meses de história que **não pode ser estendida**, sob qualquer framework de validação? Ou a resposta honesta é "colete mais dados ou opere o sinal em paper trading prospectivo" — e nesse caso, qual o tamanho mínimo de track record prospectivo que você exigiria?

---

## RODADA 2

### Dr. Marcos López de Prado — réplica e convergência

**Às três perguntas de Jim, diretamente.**

**1. Poder estatístico com ~50 previsões OOS.** Ele tem razão em apontar o denominador, e admito sem rodeios: com N≈50, um teste Diebold-Mariano só detecta melhoria de MAE da ordem de 25-30% com poder razoável; os 15-20% que ele propõe como sucesso ficam na zona cinzenta. O Deflated Sharpe Ratio não cria poder — ele apenas impede que a falta de poder seja mascarada por seleção. E é exatamente por isso que ele importa *mais* com N pequeno, não menos: com 50 observações, testar 20 configurações garante um "vencedor" espúrio. Minha concessão: DSR e PBO aqui não são ferramentas de descoberta, são freios. O arsenal vira disciplina de laboratório, não microscópio.

**2. O que sobrevive quando o evento é fixo?** Quase nada do triple-barrier — concedo. Barreiras e sample weights por unicidade pressupõem eventos sobrepostos e assíncronos; com um evento diário fixo às 9:00, as amostras já são (quase) não-sobrepostas por construção. O que sobrevive: (a) purge e embargo, porque o resíduo pode ter memória (features usam janelas de 5-20 dias — vazamento é real); (b) o *espírito* do meta-labeling, reformulado como Jim propôs: o modelo primário é o dolar_cc, e o secundário só responde "hoje o desvio será grande o suficiente para pagar o custo?" — isso é meta-labeling sem barreiras; (c) bootstrap em blocos para intervalos de confiança do MAE.

**3. Colocaria dinheiro?** Não. Sete meses inextensíveis não sustentam decisão de capital — a resposta honesta é paper trading prospectivo, e essa é a única forma de *aumentar* N de verdade: cada dia novo é uma observação genuinamente out-of-sample, sem risco de backtest overfitting. Protocolo: 60 dias úteis (~3 meses), previsão registrada às 8:55 com timestamp imutável, sizing zero. Só depois, capital simbólico (1-5% do ticket normal) por mais 60 dias.

**Refinamentos à abordagem dele.**

Primeiro, o *resíduo de ontem* como feature exige tratamento explícito de feriados assimétricos (feriado B3 sem feriado CME e vice-versa): nesses dias o resíduo de "ontem" mistura dois regimes de carrego. Proposta: dummy de feriado assimétrico + resíduo defasado zerado nesses dias. Segundo, sobre a interação embargo/passo: o walk-forward dele com passo curto e meu embargo de 5d se sobrepõem — com features de janela ≤5d, embargo de 2-3d basta e preserva observações preciosas. Terceiro, a dummy agregada dele ("dia de release macro relevante", 15-20 ocorrências) é *melhor* que minhas dummies separadas: com N=50, três dummies de 3-5 ocorrências cada é convite ao overfitting. Cedo esse ponto integralmente. Ridge vs ElasticNet: com 4-6 features pré-selecionadas por EDA, ridge dele basta; ElasticNet só se a lista passar de 8.

**O grid intraday: um uso legítimo.** Jim descarta os 69k minutos; eu resgato três usos que *não* são pseudo-réplicas porque não entram como amostras do modelo: (1) estimar σ da basis intraday para calibrar o limiar do meta-label (a vol realizada da última hora do 6L antes das 8:50 é uma feature legítima, computável em tempo real); (2) bootstrap em blocos da basis para o intervalo de confiança do baseline — responde "o erro do baseline é distinguível do bid-ask?" com dados que temos; (3) microestrutura da última hora do dia anterior (volume, range) como candidata única no EDA.

---

### Jim Simons — réplica e convergência

**1. Não-linearidade com 140 observações?** Não. Você tem razão, e nem é uma concessão dolorosa — na Renaissance nós usávamos modelos simples com dados enormes, nunca o contrário. Com 140 pontos, cada parâmetro extra custa graus de liberdade que não temos. Um gradient boosting aqui memorizaria os três ou quatro dias de COPOM e chamaria isso de "interação". Estatística clássica domina: regressão penalizada, testes formais, intervalos de confiança honestos. A única "não-linearidade" que aceito é a que você mesmo propôs pela porta dos fundos — o classificador binário de regime, que é um degrau, não uma curva. Fora isso, ElasticNet ou ridge com ≤5 features, e ponto final.

**2. O grid intraday de 1 minuto?** Aceito explorá-lo, mas com a correção que você exige. Os 69k minutos não são 69k observações — a basis tem autocorrelação fortíssima dentro do dia; o tamanho efetivo é n_eff ≈ n·(1−ρ)/(1+ρ), e com ρ intradiário perto de 0.99 voltamos aos mesmos ~140-200 pontos efetivos. Então o grid não serve para *treinar* — serve para *medir*: estimar a volatilidade da basis por hora do dia, verificar se a convergência dolar_cc→spot tem padrão de microestrutura (a basis às 8:50 já convergiu ou ainda está drenando?), e escolher empiricamente o horário do snapshot. Se descobrirmos que 8:55 tem basis sistematicamente menor que 8:50, isso vale mais que qualquer feature. Uso: diagnóstico e HAC/Newey-West nos erros; jamais inflar o n do modelo.

**3. Spread Binance-Bloomberg: fluxo ou ruído de peg?** Minha hipótese é que é uma mistura, e o teste é decomposável sem sobreajuste. O spread USDT/BRL−USDBRL contém (a) prêmio do peg USDT/USD, que é global e nada diz sobre o real, e (b) pressão local de fluxo BRL. Teste em três passos, todos fora do modelo: primeiro, subtraia o desvio do peg (USDT/USD de fonte independente) e veja se o spread *ajustado* Granger-precede o retorno overnight do 6L — uma regressão, um p-valor, zero tuning. Segundo, verifique o sinal: fluxo real deve ter correlação positiva com a basis do dia seguinte; ruído de peg, correlação zero. Terceiro, teste de estabilidade nas duas metades da amostra. Se sobreviver aos três, entra como uma feature; se não, morre antes de tocar o modelo. Sete meses não permitem mais que isso.

**Sobre o meta-labeling invertido.** Aqui cedo mais do que esperava: para o *trader*, seu classificador é operacionalmente superior à minha regressão. O trader às 8:50 não precisa de uma estimativa pontual de +3 bps com erro de ±8 bps — precisa saber se hoje é um dia em que dolar_cc é confiável ou não. Mas são complementares, não substitutos: a regressão do resíduo é o *teste científico* de que existe (ou não) sinal condicional; o classificador é o *produto*. Proponho: rodamos a regressão como pesquisa; se ela falhar no DM test, entregamos só dolar_cc + classificador de regime, e essa é uma resposta honesta e útil.

**Sobre a auditoria vintage do dolar_cc.** Você me pegou. Eu tratei a âncora como sagrada e não perguntei quando us_rate foi *publicado*. Se o FRED entrega t com defasagem t+1, toda a série histórica de dolar_cc está levemente deslocada — e como ela é simultaneamente âncora e componente do target, o erro contamina os dois lados. Entra no topo da minha lista de higiene: reconstruir dolar_cc com a taxa disponível em D-1 às 8:50, explicitamente, e comparar as duas séries. Se a diferença for < 1 bp, documentamos e seguimos; se não, refazemos tudo.

---

## CONSENSO FINAL (especificação do modelo)

1. **Target:** `y_d = log(open_bloom ~9:00) − log(dolar_cc no snapshot pré-mercado)`, snapshot único por dia,
   timezone `America/Sao_Paulo`; horário exato (8:50 vs 8:55) escolhido pelo diagnóstico intraday. Nunca nível.
2. **Dataset:** 1 linha/dia útil (~150-165 obs); grid intraday 1min só para diagnóstico, vol e erros HAC — nunca como amostra.
3. **Âncora auditada:** dolar_cc reconstruído com taxa US disponível em D-1 (defasagem de publicação explícita);
   comparação com a série ingênua documentada antes de qualquer modelagem.
4. **Baselines obrigatórios:** b1 = basis zero (open = dolar_cc); b2 = dolar_cc + média móvel 20d da basis.
   Nada é aprovado sem bater ambos.
5. **Features (≤6, todas observáveis às 8:50 em tempo real):** retorno overnight 6L; Δ DXY overnight;
   basis de D-1 (zerada + dummy em feriados assimétricos B3/CME); vol realizada da última hora do 6L pré-snapshot;
   dummy agregada "dia de evento macro" (COPOM/FED/CPI/IPCA/payroll/PIB, por data de PUBLICAÇÃO);
   retorno overnight USDT/BRL ajustado pelo peg — **somente se sobreviver ao teste de 3 passos + ablação**
   (ressalva do usuário: perfil de spread de 2024 ≠ atual; modelo default SEM USDT/BRL).
6. **PIB real / macro mensal:** rejeitados como features contínuas (2-3 releases em 8 meses); entram no dataset
   por data de publicação vintage como colunas informativas e dentro da dummy agregada de evento.
7. **Validação:** walk-forward expandindo — treino inicial 60d, passo 5d, purge 1d, embargo 2-3d;
   Diebold-Mariano contra b1 e b2; registro de TODAS as configurações testadas (limite ≤10) para PBO/DSR.
8. **Modelo:** baseline zero primeiro — se σ(erro b1) ≈ bid-ask do fixing, PARE (não há alfa; resposta honesta).
   Senão: ridge ≤6 features (pesquisa) + classificador logístico binário "basis anormal hoje?" (produto).
9. **Go/no-go:** MAE ≥15% melhor que b2 com DM p<0.10 E direcional >58% nos dias acionáveis E estabilidade
   nas duas metades do OOS. Se falhar → entregar dolar_cc + classificador de regime.
10. **Paper trading prospectivo:** previsão registrada com timestamp imutável às 8:50, mínimo 30-60 dias úteis,
    sizing zero; depois capital simbólico. Só então uso real.

*"O consenso é maior que a divergência: Jim me puxou para a parcimônia; espero tê-lo puxado para a disciplina
de registro. O modelo final é dele na forma e meu no protocolo."* — M.L.P.

*"Foi um bom debate. Você me tornou mais paranoico — e nesse negócio, paranoia é retorno."* — J.S.
