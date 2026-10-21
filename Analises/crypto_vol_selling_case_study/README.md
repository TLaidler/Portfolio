# Venda sistemática de volatilidade em cripto — um case study de processo

> **TL;DR (English).** Research case study of a systematic short-volatility program on crypto options. What this document sells is the **process**, not the rule: hypotheses, acceptance bars and NO-GO criteria pre-registered in dated documents *before* each run; a trial registry (`K`) kept across 24 research campaigns and used to deflate the Sharpe; leakage blocked **by construction** rather than by argument; and the single largest improvement of the whole programme found not in the signal but in an **execution parameter nobody had ever swept**. Three of the most interesting entries are failures — including one where I found a 21-percentage-point error in my own risk model, always in the unsafe direction. The entry rule, the tenor, the hedge trigger, the sizing and the live performance are deliberately omitted: the strategy runs with real capital at the firm where it was developed.

---

## 1. O papel econômico, antes de qualquer fórmula

O ponto de partida não foi "que sinal prevê o preço?". Foi uma pergunta de função: **quem vende volatilidade está subscrevendo seguro.**

Recebe-se prêmio hoje e assume-se a obrigação de pagar se o movimento vier. É a mesma estrutura econômica de uma seguradora de automóveis — recebe mensalidade de muitos, paga sinistro a poucos, e vive da diferença. O prêmio existe porque a maioria dos participantes é estruturalmente *compradora* de proteção, e essa demanda desequilibrada faz a volatilidade implícita negociar acima da que de fato se realiza.

Isso reposiciona a pesquisa inteira. A pergunta deixa de ser *"para onde vai o preço?"* — que eu não sei responder, e medi que não sei — e passa a ser **"o prêmio desta semana paga bem o risco desta semana?"**. É uma pergunta de adequação de preço, não de previsão.

Duas consequências metodológicas que valem mais que a tese:

- **Sinistralidade (`sinistro ÷ prêmio`) é a métrica natural**, não o P&L. O P&L mistura as duas pernas e não se decompõe; a razão separa frequência de severidade e deixa ver qual das duas o filtro está atacando.
- **Seguro quebra por concentração, não por falta de prêmio.** O risco relevante não é a média — é quantas apólices do mesmo ramo você tem abertas ao mesmo tempo.

## 2. O protocolo veio antes dos resultados

Regras do laboratório, em documentos datados **antes** de cada rodada (`docs/preregistro_*.md`, 16 deles):

| Item | Regra |
|---|---|
| Pré-registro | Hipótese, barras numéricas e **o desfecho NO-GO declarado por escrito antes de rodar** |
| Registro de tentativas | Toda rodada entra na contagem `K`, inclusive as que falharam — a contagem alimenta a deflação do Sharpe |
| Correção de múltiplos testes | **Deflated Sharpe Ratio** (Bailey & López de Prado) sobre a família auditada, com assimetria e curtose dos retornos |
| Overfitting | **PBO por CSCV**, com o estimador calibrado em ruído puro (deve dar ~0,5) e em sinal plantado (deve dar <0,1) **antes** de tocar o dado real |
| Tamanho efetivo | Toda inferência reporta `N_ef` corrigido por autocorrelação, nunca o `n` nominal — janelas sobrepostas inflam o `n` por um fator grande |
| Causalidade | Verificada **por construção**, não por argumento — ver §4 |
| Anti-garimpo | Quando a grade tinha um máximo melhor que o parâmetro adotado, **o máximo não foi adotado** e a diferença ficou registrada |

> A última linha é a que mais custa e a que mais vale. Um parâmetro vizinho entregava métrica superior; foi mantido o valor original, porque escolher o argmax da grade *é* o garimpo que o Deflated Sharpe existe para punir.

## 3. O cemitério faz parte do resultado

A família auditada tem **184 configurações em 24 campanhas**. A maioria morreu. As mortes mais informativas:

| Campanha | O que testava | Veredito |
|---|---|---|
| Previsão da magnitude do movimento | Modelo com atributos de superfície para prever o erro da implícita, 1.036 observações | **NO-GO declarado antes de rodar.** R² fora da amostra negativo — perde dos dois baselines triviais |
| Regras de saída antecipada | Nove critérios para desmontar antes do vencimento | **Todas perderam** para carregar até o fim |
| Controle de risco por grega de segunda ordem | Gestão dinâmica em vez de estática | NO-GO |
| Estruturas travadas | Limitar a cauda comprando proteção mais longe | Reprovada sob a hipótese de margem pessimista — ver §5 |
| Réplica em outro mercado | Mesma lógica fora de cripto | Reprovada: o mecanismo que funciona num mercado **não é o mesmo** no outro, e a tabela que mostra isso está no relatório |

O item mais útil da tabela é o primeiro: **ele estabelece que o programa tem um *edge* e não um *alfa*.** Sabe-se escolher *quando* subscrever; não se sabe *quanto* vai render. O prêmio quem define é o mercado. Essa distinção aparece em todos os documentos derivados, e é ela que impede o backtest de virar promessa.

## 4. Vazamento barrado por construção

O teste de causalidade não é um argumento sobre o código — é um aparelho:

> Substitui-se **todo o futuro da série** por 10⁶ e exige-se que o resultado seja **bit a bit idêntico**. Se mudar, vazou.

Roda a cada execução. A vantagem sobre revisar o código é que ele não depende de eu estar atento: um `assert` não cansa, não tem pressa e não se convence de que "dessa vez está certo".

O mesmo princípio aparece no estimador de overfitting (calibrado em resposta conhecida antes de medir o desconhecido) e nos auto-testes `demo()` embutidos em cada módulo.

## 5. Os três achados que mais valeram — e dois são erros meus

**1. O maior ganho da pesquisa estava num parâmetro de execução, não no sinal.**

O preço médio do book (*mid*) não é o que se recebe: quem vende recebe o lado de compra. A taxa de preenchimento passivo foi medida como **função da janela de postagem**, em dezenas de milhares de negócios reais:

| janela da ordem no book | taxa de preenchimento | custo esperado |
|---|---|---|
| valor que estava em produção | 0,339 | 4,81% do crédito |
| intermediária | 0,541 | 2,83% |
| maior janela testada | **0,627** | **2,11%** |

O parâmetro estava fixado no código desde o começo e **nunca tinha sido varrido** — era lido como propriedade do mercado quando era propriedade da nossa impaciência. Corrigi-lo elevou o edge líquido em **71%**, mais do que qualquer refinamento de sinal produziu em cinco campanhas.

O custo na janela original era **maior que o edge líquido do programa**. Um backtest que supõe "recebo o mid" apaga esse custo e inverte o sinal da estratégia no papel.

**2. Achei um erro de 21 pontos percentuais no meu próprio modelo de risco, sempre na direção insegura.**

A rotina que estimava o preço de liquidação tratava a margem de manutenção como se ficasse parada no valor de hoje. Ela não fica: quando o preço anda contra, a perna que entra no dinheiro passa a contar na marcação, e **a exigência sobe enquanto o patrimônio cai**. Os dois lados andam contra ao mesmo tempo.

| carteira | conta estática (errada) | conta correta | erro |
|---|---|---|---|
| menor | +22,6% | +12,5% | 10 pp |
| intermediária | +43,1% | +22,2% | **21 pp** |
| maior | +65,3% | +32,6% | 33 pp |

O erro **cresce com o tamanho da carteira e nunca erra a favor da prudência**. Uma tela que erra assim é pior que uma tela sem o número. Corrigido, com `assert` de regressão que trava a volta.

**3. A compensação de margem entre pernas nunca foi medida — e isso limita o desenho.**

Saber se a corretora reconhece uma estrutura travada muda o capital exigido por mais de uma ordem de grandeza, e é o que decide se dá para limitar a cauda. O teste que resolveria isso são duas leituras de API com uma ordem entre elas. **Ele está escrito e nunca foi executado** — e fica declarado como dívida em vez de sumir.

## 6. O que a validação disse, com a ressalva na frente

| Ataque | Resultado |
|---|---|
| Filtro aleatório de mesma frequência (3.000 sorteios) | Percentil 97,3 — **passa** |
| **Deflated Sharpe contra a família auditada** | **Passa a barra de 0,95 por margem de oito tentativas** |
| PBO por CSCV | 0,22 — aceitável |
| Estabilidade em janelas móveis de um ano | Nenhuma negativa |
| Sensibilidade a custo de execução | Sobrevive a 3× o custo medido |

**A leitura registrada é deliberadamente modesta.** O Deflated Sharpe passa, mas passa por pouco: bastariam oito configurações a mais na contagem para encostar na barra. E a fronteira da família — quais das minhas próprias campanhas "contam" — é um **julgamento declarado, não uma regra objetiva**. Um resultado cujo veredito depende dessa fronteira não é um teste; é um argumento com uma distribuição normal pendurada nele.

Isso não se resolve com mais análise. Resolve-se com **dado que a busca nunca viu**, e a única coisa que produz esse dado é o calendário.

## 7. Limitações conhecidas (autodeclaradas)

1. **A cauda não tem teto.** O hedge remove a parte direcional, mas não um salto que atravesse a faixa entre dois rebalanços. Um gap de fim de semana não tem mitigação dentro do desenho atual.
2. **Não há diversificação real entre os dois ativos.** Eles correm juntos com ρ ≈ +0,6 e perdem nas mesmas semanas — o livro vale cerca de **1,5 aposta efetiva**, não duas, e o Sharpe é calculado como se fossem duas.
3. **Um único regime, uma única contraparte.** A amostra cobre pouco mais de quatro anos e um só regime de cripto. Opções, futuros e caixa ficam na mesma corretora: risco de crédito, de saque e regulatório, todos concentrados no mesmo lugar.
4. **Desenho e avaliação no mesmo dado.** Reservar o último ano e dividir as metades reduz o problema; não o elimina. O remédio é tempo.
5. **Capacidade baixa.** O teto chega cedo e é a limitação mais séria do programa — mais do que qualquer risco de mercado. O número medido e a faixa estimada ficam de fora deste documento (§8).
6. **Governança da contagem de `K` imperfeita.** Cinco runners ainda não declaram quantas células testaram. A direção do erro é conhecida — subestimar `K` **infla** o Deflated Sharpe, que é a direção errada para errar — e isso está registrado em vez de corrigido no número.

## 8. O que não está aqui — e por quê

A estratégia foi desenvolvida na gestora onde trabalho, **com dados e infraestrutura da casa, e roda com capital real**. Portanto ficam de fora, deliberadamente:

- a regra de entrada e o que ela mede;
- o prazo das estruturas e a escolha de strike;
- o gatilho e a mecânica do hedge;
- a fração de dimensionamento;
- **o desempenho realizado e a capacidade estimada** — ambos são informação de negócio da gestora, não minha.

Este documento existe para mostrar **como** o resultado foi construído, atacado e auditado — não para distribuir a receita, e não para publicar números que não são meus. Todos os métodos citados estão na literatura aberta: Bailey & López de Prado (2014) para PSR/DSR; López de Prado, *Advances in Financial Machine Learning*, para PBO/CSCV e validação purgada; a literatura de *variance risk premium* para a tese econômica.

Se você está avaliando este trabalho para uma vaga e quer profundidade, o artefato certo para discutir sob NDA não é o backtest: é **um documento de pré-registro com o desfecho declarado antes de rodar**. Ele prova o método inteiro e não vaza nada.

---

*Stack: Python (pandas/NumPy/matplotlib), dados de cadeia de opções e de book, biblioteca própria de precificação e de margem de corretora. Sistema completo além da pesquisa: coleta, backtest, painel de decisão para operação manual e robô de execução, com auto-teste embutido em cada módulo.*

*Projetos irmãos neste repositório: [case study de estratégia sistemática em ações BR](../c9_equity_strategy_case_study) — mesmo protocolo de pré-registro, aplicado a um mercado em que os dados são públicos e por isso o documento pode mostrar os números; [replicação da metodologia AFML em cripto](../regime_detection_study), onde o pipeline rejeitou a própria estratégia.*
