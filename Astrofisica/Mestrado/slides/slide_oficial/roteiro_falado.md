# Roteiro falado — Defesa de Mestrado

> **Como usar:** este é o texto a ser dito. Não decore palavra por palavra — leia em voz
> alta três vezes e depois fale com as suas palavras, mantendo as **frases em negrito**, que
> são as que precisam sair exatamente assim.
>
> **Calibragem:** ~125 palavras por minuto (ritmo acadêmico, com pausas para apontar figuras).
> Total: **~43 minutos** até o slide 42. Os apêndices (43–47) ficam fora do tempo.
>
> **Companheiro:** o arquivo `roteiro_defesa.md` traz a tabela de correções de física, o
> checklist de verificação e as respostas às perguntas prováveis. Leia-o antes; este aqui é
> para levar ao púlpito.
>
> **Marcos de controle:** slide 8 → 2 min · slide 16 → 13 min · slide 27 → 22 min ·
> slide 34 → 30 min · slide 39 → 37 min · slide 42 → 43 min.

---

# BLOCO A — Abertura · 1,5 min

## Slide 1 — Capa · 60 s

Bom dia. Agradeço à banca pela presença e pela leitura do trabalho. Meu nome é Thiago
Laidler, e apresento a dissertação *Pipeline para Detecção Automatizada de Ocultações
Estelares em Curvas de Luz com Técnicas de Machine Learning*, desenvolvida no Observatório
Nacional sob orientação do Dr. Júlio Camargo.

Quero começar pelo problema que motivou tudo isto, porque ele não é o problema óbvio.
**Quando a estrela apaga de vez, qualquer um vê. O problema são as curvas duvidosas — e é
justamente nelas que estão as coisas mais interessantes, como anéis e atmosferas tênues. A
pergunta desta dissertação é: uma máquina consegue apontar o dedo num sinal em que dois
astrônomos experientes discordariam?**

## Slide 2 — Roteiro · 20 s

*(aponte, não leia)* O caminho é este: o fenômeno e o dado; o problema de escala; os modelos;
os resultados; e a prova de fogo numa curva real. **A última parte é onde eu apanhei de
verdade, e é a que eu gostaria que vocês guardassem.**

---

# BLOCO B — Ocultações estelares · 5,5 min

## Slide 3 — Divisor · 15 s

Começando pela física do fenômeno, para ficarmos de acordo sobre o que exatamente é o dado
que a pipeline recebe na entrada.

## Slide 4 — O que é uma ocultação · 70 s

Uma ocultação estelar acontece quando um corpo do Sistema Solar — um asteroide, um Centauro,
um objeto transnetuniano — cruza a linha de visada entre nós e uma estrela distante.

Uma observação sobre a linguagem: costuma-se dizer que a estrela "pisca", mas essa palavra
atrapalha, porque cintilação é exatamente o que confundimos com evento. **O que acontece é
que a estrela desaparece por alguns segundos. Não é um tremular: é um desligamento com
começo e fim medíveis — e é a duração desse desligamento que se converte em medida de
tamanho.**

E uma ressalva sobre esta figura, que é uma representação artística do Centauro Chariklo com
seu sistema de anéis: **nós nunca vemos isto.** Não resolvemos o corpo, não há imagem. O que
temos é uma única grandeza medida ao longo do tempo — o brilho da estrela caindo e voltando.

Como essa queda chega até nós? Pela sombra.

## Slide 5 — A sombra varre a Terra · 75 s

Como a estrela está a anos-luz e o corpo a horas-luz, os raios chegam essencialmente
paralelos. Isso tem uma consequência bonita: **a sombra projetada no chão é a silhueta do
corpo em escala um para um** — ela preserva o limbo, sem ampliação nem redução.

Aqui está o mapa de predição da ocultação por Umbriel, em 2020, que o nosso grupo observou.
Cada estação atravessa uma **corda** diferente da sombra. Muda o instante do evento — e,
mais importante, **muda a duração**: quem passa perto do centro registra um desaparecimento
longo; quem passa pela borda, um curto. É essa diferença de duração entre estações que
desenha o corpo. É por isso que uma campanha precisa de muitos observadores, e não de um
telescópio grande. A sombra varre o solo a cerca de dezoito quilômetros por segundo — é essa
velocidade que faz tudo durar segundos, e ela reaparece no fim da apresentação.

E nada disso funciona sem prever *onde* a sombra vai passar. **Com a astrometria do Gaia, o
erro da posição estelar caiu para o sub-miliarcsegundo, e o erro dominante passou a ser a
efeméride do corpo.** Sem essa etapa não há campanha, não há curva, e não há o que triar.

## Slide 6 — Da câmera à curva de luz · 60 s

Na estação, o que se grava é uma sequência de imagens. A redução usa **fotometria
diferencial**: mede-se o fluxo da estrela alvo quadro a quadro, em relação a estrelas de
referência no mesmo campo, o que cancela boa parte dos efeitos sistemáticos — variação de
transparência, extinção atmosférica. No nosso grupo isso é feito com o PRAIA, e a análise
posterior com o SORA.

À direita está o produto final: a **curva de luz**, a série temporal do fluxo normalizado, com
a queda da ocultação evidente.

**Este objeto — a curva de luz — é o protagonista da dissertação.** Tudo o que vem daqui para
frente opera sobre ele. E eu parto de curvas **já reduzidas**: a minha contribuição começa
depois da fotometria.

E por que tanto esforço por uma curva?

## Slide 7 — Por que vale a pena · 105 s ⏸ *desacelere*

Porque cada detecção positiva se converte em uma corda sobre o corpo, e cordas medem.

À esquerda, as cordas de uma campanha; à direita, o ajuste do limbo. Com três ou mais cordas
bem distribuídas, ajusta-se uma elipse e obtêm-se tamanho e achatamento. E preciso ser
cuidadoso com a palavra "forma": **o que se obtém é o limbo projetado no plano do céu naquele
instante** — forma tridimensional e orientação do polo exigem vários eventos em geometrias
diferentes.

Sobre a precisão, que é o número que impressiona: chega-se a poucos quilômetros, mas vale
dizer o que a limita, porque isso volta no fim. São três escalas somadas em quadratura. A
**difração de Fresnel** nas bordas, que a essas distâncias vale cerca de um quilômetro — um
vírgula dois, para um transnetuniano a quarenta unidades astronômicas no visível. O **diâmetro
aparente da estrela**. E o **tempo de integração**, que quase sempre domina: **a dezoito
quilômetros por segundo, cada décimo de segundo de exposição vira dois quilômetros no chão.**
Com exposições de um ou dois segundos, comuns em campanhas amadoras, são dezenas de
quilômetros.

Feita a ressalva: para corpos pequenos e distantes, esta é a técnica de maior resolução
espacial disponível do solo — supera imageamento direto e radiometria térmica por ordens de
grandeza. Só perde para a visita de uma sonda e, para asteroides próximos, para o radar.

**Cada telescópio mede uma corda; várias cordas desenham um corpo que nenhum telescópio
consegue resolver.** É por isso que vale o esforço. E é o sucesso dessa técnica que criou o
problema desta dissertação.

---

# BLOCO C — O problema e os dados · 8 min

## Slide 8 — O gargalo é humano · 85 s ⏸ *desacelere*

O avanço das predições e a multiplicação das redes de observação, incluindo ciência cidadã,
aumentaram muito o volume de dados. Há milhares de curvas de luz acumuladas em arquivos e em
campanhas novas. Mas a triagem continua sendo o que sempre foi: inspeção visual, curva por
curva. E isso funciona bem — não estou dizendo que se faz mal. Estou dizendo que **não
escala**, e que o custo cai sobre a atenção de alguém, à uma da manhã, na milésima curva.

Mas há uma segunda parte do problema, que é a que me interessa. *(aponte a frase no slide, e
leia em voz alta)* "Algumas curvas são de difícil interpretação."

**Essa frase é a semente desta dissertação.** O problema não são as ocultações óbvias, com
queda de cem por cento e patamar bem definido — essas qualquer ferramenta acha, e qualquer
analista acha. O problema são as curvas em que o sinal é raso, o ruído é alto, e duas pessoas
competentes olhando a mesma curva chegam a conclusões diferentes. É nessas que moram os
anéis, as atmosferas tênues e as estruturas secundárias.

O exemplo emblemático está na literatura: os anéis de Quaoar foram identificados apenas
depois de uma **revisita** cuidadosa aos dados. Estavam lá desde o início, e passaram
batido na primeira análise.

## Slide 9 — A proposta: uma pipeline de triagem · 60 s

O que eu construí é uma pipeline em cinco etapas. As curvas entram num banco de dados
relacional; passam por normalização do fluxo; são convertidas num **vetor de características**;
esse vetor alimenta quatro classificadores; e a saída é uma probabilidade de haver ocultação.
Em uma frase: **entra curva, sai um número entre zero e um.**

E quero fixar desde já o que essa ferramenta é, porque isso muda o significado de metade dos
meus resultados. **O que eu construí não é um juiz. É uma fila de prioridade para os olhos
humanos.** A pipeline não substitui o analista; ela decide o que ele olha primeiro. Guardem
essa distinção — ela vai ser decisiva no fim.

Cada uma dessas caixas vem nos próximos slides. Começo pela primeira.

## Slide 10 — De onde vêm os dados · 45 s

As curvas reais vêm de duas origens. A maior parte do catálogo público **B/occ/asteroid do
VizieR**, que é um agregador de campanhas independentes — vários corpos, vários observadores,
vários telescópios, várias datas. E uma parte do banco do **Grupo do Rio**, referente a
campanhas já analisadas na literatura: as ocultações por Umbriel e por Chiron.

Tudo isso foi consolidado num banco SQLite único, com duas tabelas — uma de observações, com
os metadados, e uma com os pontos de tempo e fluxo de cada curva. Parece um detalhe de
engenharia, mas foi **metade do trabalho do mestrado**, e é o que torna todo o resto
reproduzível.

Com os dados organizados, veio a primeira dificuldade séria.

## Slide 11 — O conjunto de dados rotulado · 90 s ⏸ *honestidade voluntária*

O conjunto final tem **1693 curvas de luz rotuladas**, das quais 802 são positivas reais, com
ocultação confirmada.

E aqui eu preciso ser honesto sobre um número, porque ele é a fraqueza mais séria deste
trabalho. Das 891 negativas, **702 são sintéticas** — geradas por um simulador físico, cedido
pelo Wellington Gomes-Ferrante e pelo Felipe Braga-Ribas. Outras 186 são **negativos por
recorte**: trechos reais, sem evento, extraídos de curvas positivas, antes da imersão e
depois da emersão. E apenas **três** são detecções negativas nativas — observações reais em
que, de fato, não houve ocultação.

Três. E isso não é um acaso do meu banco: é sintoma de que a comunidade não arquiva
negativas. Ninguém guarda a curva da noite em que nada aconteceu.

Só que **uma corda negativa é ciência.** Ela restringe o limbo pelo lado de fora, diagnostica
erro de efeméride, e é indispensável para estabelecer limites superiores sobre anéis e
satélites. Então, além de ser uma limitação metodológica minha, eu diria que é uma
recomendação que sai deste trabalho: **vale a pena catalogar as negativas.**

Voltarei a essa limitação no slide de resultados, porque foi ela que motivou o experimento
mais importante que eu fiz.

## Slides 12 e 13 — Formando o dataset · 90 s *(os dois juntos)*

Os modelos que eu uso não recebem a série temporal bruta. Eles recebem um vetor de números.
Então a etapa central de todo o trabalho é esta: **engenharia de características** — como
resumir uma curva de luz inteira em uma dúzia de grandezas que preservem o que importa.

E há uma razão honesta para essa escolha: **com 1693 curvas eu não tenho amostra para deixar
a máquina inventar as próprias características.** Uma rede convolucional aprenderia
representações direto da série bruta, mas precisaria de muito mais dados. Então eu escolhi as
grandezas que um astrônomo olharia.

*(aponte as listas, sem recitar os nomes)* São vinte e oito grandezas, mas na verdade são
**três perguntas medidas de vinte e oito maneiras**. Primeira: **tem um degrau?** —
profundidade em relação ao baseline, amplitude, *max drawdown*. Segunda: **o degrau é maior que
o barulho?** — razão sinal-ruído da queda, desvio padrão fora do evento, e testes estatísticos
entre quartis da curva, com t de Welch e Kolmogorov-Smirnov, que perguntam se um trecho tem
distribuição diferente dos outros. Terceira: **o degrau sobrevive quando eu aliso a curva?** —
aqui entra o filtro de Savitzky-Golay: eu suavizo a série e refaço as mesmas contas. Se o
degrau continua lá, é real; se desaparece, era ruído de alta frequência.

Vou mostrar isso em duas curvas concretas, porque é mais claro que qualquer lista.

## Slide 14 — A curva vira números: exemplo positivo · 45 s ⏸ *pausa de 5 s*

Esta é uma curva positiva da campanha de Umbriel, da estação do Andrew Scheck. A queda está
ali, visível. À direita, a linha correspondente na tabela de características — os valores
reais do meu conjunto de dados.

*(silêncio de cinco segundos, deixando a banca comparar)*

Profundidade zero vírgula quarenta e três. Razão sinal-ruído da queda, sete.

Agora a mesma tabela, para outra curva da mesma campanha.

## Slide 15 — A curva vira números: exemplo negativo · 60 s

Esta é uma curva sem evento, da estação do Norman Carlson. Mesmas colunas: profundidade zero
vírgula trinta e um, razão sinal-ruído quatro vírgula quatro.

**Repare que isso é perto.** Zero vírgula quarenta e três contra zero vírgula trinta e um.
Sete contra quatro vírgula quatro. Não é uma separação óbvia, não é uma ordem de grandeza. **Se
uma coluna sozinha resolvesse o problema, eu não precisaria de nada do que vem a seguir** — eu
usaria um limiar na profundidade e iria para casa.

E é exatamente isso que o classificador faz de diferente: ele não olha uma coluna, olha as
onze ao mesmo tempo, e aprende a fronteira nesse espaço. O modelo não vê curvas de luz — ele
vê este contraste numérico.

E como uma máquina aprende um contraste desses?

---

# BLOCO D — Machine Learning · 9,5 min

## Slide 16 — Divisor · 15 s

Este é o bloco em que eu explico os modelos. Prometo não escrever uma equação — a formalização
completa está no Capítulo 3 da dissertação.

## Slide 17 — Classificação supervisionada · 65 s ⏸ *desacelere*

O problema está formulado como **classificação binária supervisionada**. Supervisionada porque
cada exemplo do treino tem um rótulo conhecido — a chamada verdade de campo, que no meu caso
vem da curadoria dos catálogos e das análises publicadas. O modelo ajusta os próprios
parâmetros para acertar esses rótulos, e a esperança é que **generalize**: que erre pouco em
curvas que nunca viu.

Um ponto que parece técnico e é central para o final desta apresentação: **a saída do modelo
não é um sim ou um não.** É uma **probabilidade**, um número entre zero e um. A decisão binária
vem depois, comparando essa probabilidade com um **limiar de decisão**, que eu chamo de τ, e
que por convenção vale zero vírgula cinco.

**Guardem esse τ.** Ele parece uma escolha inocente, mas é arbitrário, e eu vou mostrar duas
vezes que mexer nele muda tudo.

Três dos meus quatro modelos são construídos a partir do mesmo bloco elementar: a árvore de
decisão.

## Slide 18 — Árvores de decisão · 70 s

Uma árvore de decisão funciona como o jogo das vinte perguntas: em cada nó ela pergunta o
valor de **uma** característica, comparado com um limiar.

Vou fazer uma, com os números que vocês acabaram de ver. A razão sinal-ruído da queda é maior
que cinco? Sim. A profundidade é maior que zero vírgula trinta e cinco? Sim. Folha:
**ocultação**. Para a curva negativa, o mesmo caminho levaria à outra folha.

Cada resposta restringe a região do espaço de características, que acaba particionado em
regiões retangulares, cada uma associada a uma classe. O critério de escolha das perguntas é a
redução de impureza — o coeficiente de Gini, no algoritmo CART.

E há uma consequência que eu reivindico como vantagem: **eu posso ler a sequência de perguntas
e discordar dela.** É a interpretabilidade que eu troquei pela potência de uma rede neural.

Uma árvore sozinha, porém, é instável, e sem restrições decora o treino.

## Slide 19 — Genealogia das famílias · 30 s *(rápido)*

Esta é a genealogia dos modelos baseados em árvore, e ela está aqui por um motivo só.
**Meus quatro modelos não são quatro ideias — são duas**: votar junto, e corrigir o próprio
erro. Bagging e boosting não são etapas de uma evolução: são dois ramos irmãos, duas respostas
diferentes ao dilema entre viés e variância. Mais a Regressão Logística, que é linear e que eu
deixei de fora dessa família de propósito, como referência.

A primeira ideia: votar junto.

## Slide 20 — Floresta aleatória · 75 s

Random Forest treina centenas de árvores e agrega por **votação majoritária**.

A intuição é a de um comitê: é como chamar cem pessoas para estimar o peso de um boi, cada uma
olhando de um ângulo diferente, e tirar a média. Os erros individuais, se forem independentes,
se cancelam.

E aqui está a parte que costuma ficar implícita: **isso só funciona se as árvores errarem em
casos diferentes.** Se eu treinasse centenas de árvores nos mesmos dados, com o mesmo
algoritmo, elas sairiam praticamente idênticas, votariam igual, e a votação não ganharia nada.

A floresta compra essa diversidade com **aleatoriedade em dois níveis**: cada árvore é treinada
em uma amostra sorteada com reposição — o *bootstrap* — e, em cada divisão, considera apenas um
subconjunto sorteado das características. É essa **descorrelação** entre as árvores que reduz a
**variância** do conjunto. O viés individual permanece baixo, e a instabilidade some.

A segunda ideia é quase o oposto: em vez de paralelo, sequência.

## Slide 21 — Gradient Boosting · 75 s

No boosting, as árvores são treinadas **uma após a outra**, e cada nova árvore é ajustada para
corrigir os erros do conjunto acumulado — formalmente, ela é ajustada ao gradiente negativo da
função de perda.

A imagem que eu uso é a de um aluno só, que toda noite refaz exatamente as questões que errou
no dia anterior. Ele não pede opinião a mais ninguém; ele itera sobre os próprios erros.

A consequência é que boosting ataca o **viés**, enquanto bagging ataca a **variância** — alvos
diferentes no mesmo dilema. E como cada árvore é rasa e a contribuição de cada uma é controlada
por uma taxa de aprendizado, o conjunto se aproxima da solução aos poucos.

Os dois modelos de boosting que eu uso são o **XGBoost**, que acrescenta regularização
explícita e usa expansão de segunda ordem da perda, e o **CatBoost**, que muda a ordem de
cálculo dos resíduos para combater vazamento e usa árvores simétricas. **Irmãos, não gerações.**

## Slide 22 — Por que comitês funcionam · 50 s *(rápido)*

O princípio que sustenta os dois esquemas é o mesmo, e o Teorema do Júri de Condorcet o
enuncia bem: se cada votante acerta com probabilidade um pouco acima de cinquenta por cento, a
decisão da maioria melhora com o número de votantes — desde que os erros não sejam idênticos.
Nesta figura, árvores com acurácia individual em torno de sessenta e cinco por cento produzem
uma floresta perto de noventa e quatro.

Os quatro modelos que eu comparo, então, são: Regressão Logística como referência linear,
Random Forest pelo lado do bagging, e XGBoost e CatBoost pelo lado do boosting. E as árvores
me dão de brinde a **importância das variáveis**, que eu vou usar mais adiante.

Antes de mostrar resultado, preciso dizer como evitei me enganar.

## Slide 23 — Avaliar sem se enganar · 55 s

A regra de ouro é que **o teste usa curvas que o modelo nunca viu**. Isso parece óbvio, mas na
minha pipeline exigiu cuidado: a divisão treino/teste é feita **por curva**, nunca por linha, e
quando eu recortei negativos de uma curva positiva, essa curva positiva foi **removida** do
treino — senão a mesma observação apareceria nas duas classes, e eu estaria vazando informação
para dentro do teste.

Além da divisão única, eu uso **validação cruzada estratificada em cinco dobras**: o conjunto é
dividido em cinco partes, e em cada rodada uma parte diferente serve de validação. As dobras
preservam a proporção entre as classes e respeitam o agrupamento por curva.

E o que ela me disse é o que importa: os desvios padrão entre dobras são pequenos, da ordem de
seis a dez milésimos em F1. **O resultado não depende de qual pedaço dos dados eu escondi.**

## Slides 24 e 25 — Métricas de performance · 65 s *(os dois juntos)*

As métricas partem todas da **matriz de confusão** — verdadeiros e falsos positivos,
verdadeiros e falsos negativos. Não vou defini-las uma a uma; estão no Capítulo 3.

Vou dizer apenas quais decidem, e por quê. Reporto acurácia, precisão e sensibilidade, mas as
duas que carregam o argumento são o **F1-score**, que é a média harmônica entre precisão e
sensibilidade e portanto pune os dois tipos de erro, e a **AUC-ROC**.

A AUC merece uma frase, porque ela é a chave do final. A curva ROC percorre todos os limiares
possíveis: cada ponto dela é um valor de τ. A área sob essa curva tem uma interpretação exata —
**é a probabilidade de o modelo dar uma pontuação mais alta a uma curva positiva sorteada ao
acaso do que a uma negativa sorteada ao acaso**. Ou seja: **a AUC mede ordenação, não
classificação.** Guardem isso; eu vou cobrar essa ideia no bloco do Quaoar.

## Slide 26 — Das 28 às 11 features · 60 s

Uma última decisão de projeto antes dos resultados. Comecei com vinte e oito características e
terminei com onze.

O critério foi uma **análise de redundância**: pares conceitualmente equivalentes ou altamente
correlacionados. A amplitude e a profundidade do dip, por exemplo, medem praticamente a mesma
coisa em curvas normalizadas — mantive a profundidade, que tem motivação física direta. E as
nove características derivadas do gradiente saíram sem prejuízo.

O resultado dessa poda é mais do que faxina: **onze características bastam para reproduzir o
desempenho de vinte e oito. Isso é indício de que o modelo encontrou estrutura, e não decorou
ruído** — um modelo que dependesse de correlações espúrias precisaria de todas elas.

Agora, o que saiu.

---

# BLOCO E — Resultados · 8 min

## Slide 27 — Divisor · 15 s

Seis experimentos, e uma conclusão que, confesso, me incomodou.

## Slide 28 — Seis experimentos · 110 s

Os seis experimentos variam duas coisas: o conjunto de características e a composição do
conjunto de teste. O primeiro é a linha de base, com as vinte e oito. O segundo, a configuração
enxuta com onze, que é a referência operacional do trabalho. O terceiro testa apenas em curvas
reais. Os demais são reduções intermediárias e a ablação da característica do K-means.

*(aponte a coluna, sem ler célula por célula)* A coluna que interessa é a do melhor F1: de zero
vírgula noventa e oito a zero vírgula noventa e nove, em todas as configurações, com AUC-ROC
sempre acima de zero vírgula noventa e nove e meio.

E aqui eu preciso desarmar a minha própria tabela. **O ponto não é o número ser alto — é ele
ser estável.** O desempenho não depende do modelo, nem de quantas características eu uso, nem
da partição. Isso é ótimo em robustez e incômodo em mérito: **significa que o crédito é das
características e dos dados, não do algoritmo da moda.**

Quero ser explícito sobre uma coisa: **esta tabela não é o resultado da dissertação. Ela é a
checagem de que nada está quebrado.** O resultado está no bloco do Quaoar, daqui a alguns
slides.

## Slide 29 — Separação das classes · 60 s

Visualmente, é isto. À esquerda as curvas ROC dos quatro modelos no Experimento 2, colando no
canto superior esquerdo, que é o canto ideal. À direita as matrizes de confusão: os erros se
contam nos dedos — um, dois, três curvas em trezentas e trinta e nove.

Apliquei também o **teste de McNemar** entre todos os pares de modelos, que é o teste
apropriado para comparar dois classificadores no mesmo conjunto de teste. Nenhum par apresenta
diferença estatisticamente significativa. Ou seja: **estatisticamente, os quatro são o mesmo
modelo.** E isso é libertador, porque me permite escolher por critérios secundários —
interpretabilidade, velocidade, e um que vai aparecer no Quaoar.

Mas a pergunta que eu mesmo faria a esta altura é outra.

## Slide 30 — E se o teste tiver só curvas reais? · 70 s

A pergunta é: "setenta e oito por cento das suas negativas são sintéticas; você não está
apenas aprendendo o simulador?"

É uma objeção legítima, e a resposta tinha que ser experimental. Então eu refiz o experimento
excluindo as curvas sintéticas do conjunto de teste. As sintéticas continuam no treino — o
modelo vê o simulador enquanto aprende — mas a **avaliação é cem por cento em curvas reais**.

O F1 fica em torno de zero vírgula noventa e oito. Cai cerca de um ponto, e a AUC permanece
acima de zero vírgula noventa e nove e meio.

Cair um ponto é exatamente o que se espera se o modelo aprendeu a **física** do fenômeno.
Se ele tivesse decorado a estatística de ruído do simulador, remover as sintéticas do teste
derrubaria o desempenho de forma muito mais violenta. Não derruba.

Duas descobertas laterais valem um slide cada.

## Slide 31 — Importância não é insubstituibilidade · 55 s

A primeira é metodológica, e eu considero uma contribuição do trabalho.

A característica derivada do K-means — a distância entre os dois centróides do fluxo suavizado
— aparecia consistentemente como a **mais importante** nos modelos de árvore, chegando a
concentrar mais de metade da importância no XGBoost. E a análise exploratória confirma: ela é,
por si só, discriminativa.

Só que eu a removi, e **o F1 não caiu.** A capacidade preditiva foi simplesmente redistribuída
para uma característica colinear — o desvio padrão do fluxo suavizado, que captura o mesmo
fenômeno físico, a coexistência de dois patamares dentro e fora da queda.

A lição, e eu diria isso a qualquer pessoa que use importância de variáveis: **não leiam esse
ranking como física.** Importância mede qual pergunta a árvore fez primeiro, não qual
informação é indispensável.

E onde o modelo erra?

## Slide 32 — Onde o modelo erra · 65 s ⏸ *desacelere*

Estes são falsos negativos — curvas positivas que o modelo classificou como negativas.

Olhem o que elas têm em comum: ruído alto, queda rasa, poucos pontos dentro do evento. **Eu
mesmo hesitaria nessa da esquerda.** Se vocês me mostrassem essa curva sem o rótulo, eu não
apostaria com convicção.

E isso não é uma desculpa — é um diagnóstico com consequência. **Os erros do modelo estão
concentrados exatamente onde os analistas humanos também discordam.** Ou seja: o modelo não
está falhando de forma aleatória nem em casos fáceis; ele está hesitando onde há motivo para
hesitar.

Se o erro é hesitação, e não incompetência, então ele é **ajustável**. E é isso que o próximo
slide faz.

## Slide 33 — O limiar τ · 85 s

Aqui o τ volta, como eu tinha prometido.

Em triagem, os dois erros não custam a mesma coisa. **Perder uma ocultação genuína pode
significar perder uma descoberta; revisar um alarme falso custa trinta segundos de um
analista.** O limiar padrão de zero vírgula cinco embute exatamente a hipótese contrária — que
os dois erros pesam igual.

A analogia é a da **altura da rede na quadra**. Em zero vírgula cinco eu digo ao modelo: "só me
avise quando tiver certeza". Baixando o τ: "me avise em qualquer suspeita, eu tenho tempo de
olhar".

E o custo, medido no conjunto de teste: a **sensibilidade sobe para noventa e nove vírgula
quatro por cento**, ao preço de cinco alarmes falsos adicionais em cento e setenta e nove
negativas. Cinco. E isso é **pós-processamento puro** — não retreina nada, é uma linha de
código depois do modelo pronto. Quem escolhe a altura da rede é a equipe que vai olhar as
curvas.

Tudo isso, porém, é teste controlado, com a minha própria partição dos meus próprios dados. A
pergunta que fica é: e no mundo real?

---

# BLOCO F — Quaoar · 7 min · **o pico**

## Slide 34 — Divisor · 45 s

Para responder isso, eu precisava de uma curva que o modelo nunca tivesse visto, e que também
não tivesse passado por mim.

Esta é a ocultação estelar por Quaoar, objeto transnetuniano, observada em agosto de 2022. Os
dados foram gentilmente cedidos pelo Chrystian Pereira, autor principal da análise publicada
em 2023. Esta curva **não está no banco SQLite**, não entrou em treino nem em teste, não foi
usada em nenhuma etapa de ajuste. É de outra campanha, outro instrumento, outro corpo.

E o evento é especialmente interessante, porque além da queda profunda do corpo principal ele
tem assinaturas de **dois anéis**. Então a aposta é a seguinte: **eu vou pedir a um modelo que
nunca viu um anel na vida que ache os dois.**

## Slide 35 — A curva completa · 70 s

Esta é a curva, do canal vermelho do instrumento 'Alopeke, no Gemini Norte.

No centro, a queda profunda do corpo principal: quarenta e oito segundos, profundidade
próxima de cem por cento. E nos recortes ampliados, as estruturas rasas: o **Q1R**, o anel
externo e denso, a quatro mil e cinquenta e sete quilômetros do centro, descoberto por Morgado
e colaboradores em 2023; e o **Q2R**, o anel interno e tênue, a dois mil quinhentos e vinte
quilômetros, com cerca de dez quilômetros de largura, descoberto por Pereira e colaboradores
justamente nesta ocultação. Os dois estão fora do limite de Roche clássico, o que é o que torna
esse sistema notável.

Aplicando o modelo à curva inteira, a probabilidade é de zero vírgula noventa e nove. Mas eu
preciso ser franco sobre o que esse número significa: **ele é dominado pela queda do corpo
principal.** Detectar o corpo é a parte fácil, e não é evidência nenhuma de detecção de anel.

Para isso, é preciso olhar a curva em pedaços.

## Slide 36 — Caçando estruturas por recortes · 85 s ⏸ *desacelere*

Então eu defini seis janelas temporais, cada uma sobre uma assinatura física distinta: um
trecho de linha de base sem evento, como controle negativo; as travessias do anel Q1R; as
travessias do anel Q2R; e um trecho de ruído que, visualmente, se parece com uma
micro-ocultação. Para cada janela eu recortei a curva, extraí as mesmas onze características, e
apliquei o mesmo modelo.

As **duas travessias do anel Q1R** passam com folga: zero vírgula noventa e seis e zero vírgula
nove nove nove. E vale notar que elas passam por motivos físicos **diferentes**: em uma delas o
anel é largo e raso, e o que salva a detecção é a quantidade de pontos amostrados dentro da
estrutura; na outra é o núcleo estreito e profundo, e o que salva é a amplitude da queda.

Já as duas travessias do **Q2R**, o anel tênue, recebem zero vírgula zero quatro e zero vírgula
zero oito. Ou seja: no limiar padrão, o modelo diz que **não há evento** ali.

**Isso é um erro, e eu não vou chamar de outra coisa.**

*(pausa real — deixe o desconforto se instalar)*

## Slide 37 — O sinal fraco ainda é sinal · 120 s ⏸ **o clímax**

Mas olhem o vizinho.

Adjacente à travessia do Q2R há aquele trecho de ruído que se parece com uma micro-ocultação,
de duração comparável. Ele recebe **zero vírgula zero zero zero cinco**. E o anel real recebe
**zero vírgula zero quatro três**.

*(deixe o contraste no ar por um segundo)*

A pergunta certa, então, não é "o alarme apitou?". A pergunta certa é: **"o ponteiro pulou?"**
É como um detector de metais que não apitou, mas cujo ponteiro deu um salto de quase duas
ordens de grandeza exatamente onde estava a moeda. E aqui está o ponto que eu considero o
resultado desta dissertação: **o valor absoluto depende de onde eu pus o alarme; o salto não
depende de nada meu.**

**Pelo critério padrão, o modelo disse "não". E mesmo dizendo "não", ele colocou exatamente o
trecho do anel verdadeiro oitenta e seis vezes acima de tudo o mais nessa curva. Ele hesitou,
como um humano hesitaria — mas hesitou no lugar certo.** E é para isso que serve uma fila de
prioridade, não um juiz.

Na prática, isso significa que basta baixar o τ para zero vírgula zero três — um valor entre as
duas escalas de probabilidade — e as duas travessias do Q2R passam a ser classificadas
corretamente, sem que o controle de linha de base nem o trecho de ruído cruzem o novo limiar.
A sensibilidade sobre os quatro eventos físicos da curva sobe de cinquenta para cem por cento.

E agora as três ressalvas, que eu prefiro dizer antes de me perguntarem. Primeira: **oitenta e
seis vezes não é uma significância de detecção, e não é uma razão sinal-ruído.** É separação
relativa de pontuação de um classificador — e é o que basta para ordenar candidatos numa fila.
Segunda: **o valor de τ igual a zero vírgula zero três foi ajustado nesta curva**, para
demonstrar a separação; não é um limiar validado às cegas, e o resultado defensável aqui é o
ordenamento, não o número. Terceira: **é uma curva, um objeto.** É uma anedota bem comportada,
não estatística.

E a curva do Quaoar me ensinou uma última coisa, que mudou a agenda do trabalho.

## Slide 38 — Janelas maiores diluem · 75 s

A explicação mais natural para o Q2R pontuar baixo seria trivial: a janela é curta demais,
poucos pontos, extração instável. Eu testei essa hipótese, e ela é **falsa**.

Ao ampliar as janelas do Q2R por um fator de aproximadamente três, a probabilidade atribuída ao
anel real **caiu** — de zero vírgula zero quatro três para zero vírgula zero três cinco.
Ampliar a janela tornou o veredito negativo ainda mais forte.

A causa é estrutural, e é uma limitação do meu conjunto de características: elas são
**estatísticas globais da janela** — profundidade, desvio padrão, razão sinal-ruído, todas
calculadas sobre a janela inteira. Uma queda de meio segundo diluída em dezenas de segundos de
linha de base limpa vira um desvio desprezível, e o modelo responde, com mais confiança, que
ali é linha de base pura.

E os números do fenômeno mostram por que isso é grave: **a dezoito quilômetros por segundo, o
corpo principal dura quase um minuto, e um anel de dez quilômetros dura meio segundo.** Duas
ordens de grandeza. A fronteira de detecção não é o tamanho absoluto da janela — é a **razão**
entre a duração do evento e a da janela.

Isso define o próximo passo do trabalho de forma inescapável.

---

# BLOCO G — Fecho · 3,5 min

## Slide 39 — Dificuldades e como foram enfrentadas · 60 s

Antes de concluir, quatro dificuldades e as decisões que tomei diante delas.

Dados heterogêneos e dispersos, em formatos e convenções diferentes: consolidei tudo num banco
único. Escassez de negativas reais — apenas três nativas: preenchi com simulador físico e com
recortes de curvas reais, e assumo o custo dessa escolha. Redundância entre características:
análise sistemática, vinte e oito para onze. E eventos curtos e rasos, que o limiar padrão
perde: τ ajustável por campanha.

A maior fragilidade continua sendo a segunda, e ela está dita na dissertação com todas as
letras, no capítulo de limitações.

## Slide 40 — Conclusões · 60 s

Em três números.

**F1 entre zero vírgula noventa e oito e zero vírgula noventa e nove**, estável em seis
experimentos e quatro modelos de famílias distintas, incluindo teste exclusivamente em curvas
reais.

**Sensibilidade de noventa e nove vírgula quatro por cento** com o limiar ajustado, sem
retreinamento — a assimetria de custo entre perder um evento e revisar um alarme incorporada em
pós-processamento.

E **oitenta e seis vezes de separação** entre um anel verdadeiro e um trecho de ruído
semelhante, em dado externo ao treinamento.

O que eu entrego, no fim, é uma **ferramenta reproduzível de triagem e priorização** de curvas
de luz — pronta para revisitar arquivos em busca de eventos que passaram batido.

## Slide 41 — Trabalhos futuros · 60 s

Quatro direções, e quero destacar que a primeira não é uma ideia bonita que eu tive: **é o que
o slide anterior me obrigou a concluir.** Aplicar a pipeline por **janela deslizante**, com
largura compatível com a duração do evento alvo, e enriquecer o conjunto com **características
locais** — profundidade máxima de qualquer subjanela, simetria do perfil de ingresso e egresso,
ajuste a um poço retangular curto. Isso atacaria a raiz do problema do Q2R.

Segunda: ampliar as negativas reais nativas, o que depende de colaboração e de mudança de
prática na comunidade. Terceira: redes convolucionais sobre a série bruta — e aqui uma
honestidade: **a rede convolucional é o caminho óbvio, e eu não a fiz. Não é preguiça, é
amostra: com 1693 curvas eu não teria com que treinar.** Quarta: triagem em tempo quase-real
nas campanhas do grupo.

## Slide 42 — Obrigado · 35 s

Encerro agradecendo. Ao Dr. Júlio Camargo, pela orientação e pela confiança numa proposta
ambiciosa. Ao Grupo do Rio. Ao Wellington Gomes-Ferrante e ao Felipe Braga-Ribas, pelo
simulador. Ao Chrystian Pereira, pelos dados de Quaoar. À banca e à minha família.

**Se esta ferramenta serve para alguma coisa, é para que a próxima curva duvidosa não passe
batido.**

Obrigado. Estou à disposição para as perguntas.

---

# Controle de tempo

Texto medido: **5659 palavras** nos slides 1–42. O tempo depende do seu ritmo, e a diferença
não é pequena — meça na primeira passada cronometrada e use a coluna que corresponder a você.

| Marco | Slide | Ritmo calmo (125 pal/min) | Ritmo de defesa (135 pal/min) |
|---|---|---|---|
| Fim da abertura | 2 | 1,3 min | 1,2 min |
| Fim das ocultações | 7 | 7,5 min | 7 min |
| Fim do problema e dados | 15 | 16 min | 15 min |
| Fim do Machine Learning | 26 | 26,5 min | 24,5 min |
| Fim dos resultados | 33 | 33,5 min | 31 min |
| Fim do Quaoar | 38 | 42 min | 39 min |
| **Fim (slide 42)** | 42 | **45,5 min** | **42 min** |
| *(+ pausas marcadas)* | | ~46 min | ~43 min |

Na prática quase todo mundo acelera sob adrenaline: o cenário provável é a coluna da direita,
**~43 minutos**. Mas o roteiro está dimensionado no limite superior da faixa, então trate as
compressões abaixo como parte do plano, não como emergência.

**Marco decisivo:** se ao entrar no **slide 27** você passou de **27 minutos**, comprima —
19, 22, 25 e 31 a uma frase cada recupera cerca de 2 minutos, e o slide 7 pode perder o
parágrafo do orçamento de resolução (mais 40 segundos). **Nunca comprima 11, 32, 36, 37
nem 38** — são os slides de honestidade e o clímax.

**Se estiver adiantado:** desenvolva no slide 7 (as três escalas que limitam a precisão) e no
23 (os cuidados contra vazamento: divisão por curva, remoção da curva-mãe dos recortes) — são
os dois pontos onde profundidade extra rende crédito técnico com a banca.
