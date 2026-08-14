# Roteiro de Defesa — 47 slides, 45 minutos

> **Método:** TOPT em cada slide — **T**ópico (o assunto, na primeira frase) · **O**rientação
> (o contexto, o porquê) · **P**onto (a mensagem central) · **T**ransição (a ponte para o
> próximo).
>
> **Regra única de ouro:** você tem ~54 s por slide. A banca lê mais rápido do que você
> fala. Portanto **nunca leia o slide** — o slide mostra, você explica *por que aquilo está
> ali*. Tudo que já está escrito na tela está listado no fim como "cortar da fala".

---

## A ESPINHA — decore estas duas frases

Toda a palestra pende de um enigma. Diga-o no slide 1, antes do roteiro:

> **"Quando a estrela apaga de vez, qualquer um vê. O problema são as curvas duvidosas — e é
> justamente nelas que estão as coisas interessantes, como anéis. A pergunta desta
> dissertação é: uma máquina consegue apontar o dedo num sinal em que dois astrônomos
> experientes discordariam?"**

E a reformulação que salva metade dos seus resultados — diga no slide 9, repita no 33, pague no 37:

> **"O que eu construí não é um juiz. É uma fila de prioridade para os olhos humanos."**

Sem essa frase plantada no começo, o slide 37 soa como desculpa. Com ela, soa como clímax.
Um juiz que dá 0,04 num anel real *errou*; uma fila que põe aquele trecho 86 vezes acima do
ruído *acertou o que importa*.

**Última frase falada da defesa = a espinha outra vez.** Fecha o círculo e fica no ar durante
as perguntas.

## Orçamento de tempo (anote no slide impresso)

| Bloco | Slides | Minutos |
|---|---|---|
| Abertura | 1–2 | 1,5 |
| Ocultações | 3–7 | 5 |
| Problema e dados | 8–15 | 7 |
| Machine Learning | 16–26 | 9 |
| Resultados | 27–33 | 8 |
| Quaoar (o pico) | 34–38 | 8 |
| Fecho | 39–42 | 3,5 |
| **Total** | | **42** (+3 de folga) |

**Se chegar ao slide 27 com 5 min de atraso:** comprima 19, 22, 25 e 31 para uma frase cada.
**Nunca corte 32, 36 nem 37.**

---

# BLOCO A — Abertura (1–2) · 1,5 min

> **Feynman:** abra com o enigma, não com definição. O índice é promessa, não leitura.

### S1 · Capa — 45 s
- **T:** "Bom dia. Agradeço à banca pela presença. Apresento a dissertação *Pipeline para Detecção Automatizada de Ocultações Estelares em Curvas de Luz com Técnicas de Machine Learning*, orientada pelo Dr. Júlio Camargo."
- **O:** *(sem contexto histórico — vá direto ao enigma)*
- **P:** **a espinha, literalmente** (ver acima).
- **T:** "Cinco partes. A quarta é onde eu apanhei de verdade, e é a que eu quero que vocês guardem."

### S2 · Roteiro — 15 s
- **T:** *(aponte, não leia)* "Fenômeno, dados, método, resultados, e a prova de fogo."
- **P:** "Tudo converge para a última parte."
- **T:** "Começando pela física."

---

# BLOCO B — Ocultações estelares (3–7) · 5 min

> **Feynman:** é **uma cadeia contínua**, não cinco slides. Estrela → corpo → sombra → seu
> telescópio → um segundo de queda → uma corda → o contorno. Conte como uma história só.
> **Imagem física:** *um poste de luz distante e um lápis passando na frente; sua pupila mede
> quanto tempo ficou escuro, e disso você tira a espessura do lápis.*
> **Frase que fica:** "Cada telescópio mede uma corda; várias cordas desenham um corpo que
> nenhum telescópio consegue resolver."

### S3 · [Divisor] — 10 s
- **T:** "Primeiro: o que é o dado com que eu trabalho, e de onde ele vem."

### S4 · O que é uma ocultação — 50 s
- **T:** "Uma ocultação estelar é isto: um corpo pequeno do Sistema Solar cruza a linha de visada de uma estrela."
- **O:** ⚠️ **corrija a legenda ao falar** — não diga "pisca": "A estrela **desaparece por alguns segundos**. Não é um tremular — é um desligamento com começo e fim medíveis. E é a **duração** desse desligamento que vira medida de tamanho."
- **P:** ⚠️ **ressalva obrigatória sobre a arte:** "Esta é uma ilustração. Nós nunca vemos isto — não resolvemos o corpo. Só vemos o brilho da estrela caindo." *(Sem essa frase, o leigo sai achando que ocultação produz imagem.)*
- **T:** "E como essa queda chega até nós? Pela sombra."

### S5 · A sombra varre a Terra — 40 s
- **T:** "A sombra da estrela projetada pelo corpo varre a superfície da Terra."
- **O:** ⚠️ **complete a legenda** (ela fala só de "instante", e isso deixa o slide 7 sem fundamento): "Cada sítio atravessa uma **corda** diferente da sombra. Muda o instante — e, mais importante, muda a **duração**: quem passa perto do centro vê um desaparecimento longo; quem passa pela borda, um curto."
- **P:** "É essa diferença de duração que desenha o corpo. Por isso precisamos de muitas estações." *(Se couber, um número: "a sombra varre o solo a cerca de 18 km/s — é por isso que tudo dura segundos.")*
- **T:** ✚ **uma frase sobre predição** (omissão que a banca notaria; Camargo é astrômetra): "Nada disso acontece sem prever onde a sombra vai passar — o Gaia levou o erro da posição estelar ao sub-miliarcsegundo, e o erro dominante passou a ser a efeméride do corpo. Sem essa etapa não há campanha, não há curva, e não há o que triar."

### S6 · Da câmera à curva de luz — 40 s
- **T:** "Na estação, o que se grava é uma sequência de imagens."
- **O:** "A fotometria diferencial mede o fluxo da estrela quadro a quadro, contra estrelas de referência, e o resultado é esta série temporal."
- **P:** "**Este objeto — a curva de luz — é o protagonista da dissertação.** Tudo que vem depois opera sobre ela."
- **T:** "E por que tanto esforço por uma curva?"

### S7 · Por que vale a pena — 60 s ⏸ **DESACELERE**
- **T:** "Porque cada detecção vira uma corda, e cordas medem o corpo."
- **O:** ⚠️ **qualifique "precisão de km"** (slide mais vulnerável do bloco): "Três ou mais cordas ajustam o **limbo projetado** do corpo — não a forma tridimensional, que exigiria vários eventos em geometrias diferentes."
- **P:** "A precisão chega a poucos quilômetros, e o que a limita é físico e instrumental: a difração de Fresnel, cerca de **1 km** nessas distâncias; o tamanho aparente da estrela; e sobretudo o **tempo de integração** — a 18 km/s, cada 0,1 s de exposição vira 2 km no chão." *(Essa versão te fortalece: estabelece que a resolução é dominada pela amostragem temporal, que é exatamente a motivação da janela deslizante no slide 38.)*
- **P₂:** "Para tamanho e forma de corpos pequenos e distantes, é a técnica de maior resolução espacial disponível do solo. Só perde para uma visita de sonda — e, para asteroides próximos, para radar." ⚠️ *(não diga "a mais precisa depois de sondas in situ", sem qualificar)*
- **T:** "O sucesso da técnica criou o problema que motivou esta dissertação."

---

# BLOCO C — O problema e os dados (8–15) · 7 min

> **Feynman:** o gargalo tem de ser uma **cena humana**, não uma estatística. E os slides
> 14–15 são o *soco* do bloco, não ilustração.
> **Frase que fica:** "O gargalo não é o telescópio, é a atenção humana."

### S8 · O gargalo é humano — 60 s ⏸ **DESACELERE**
- **T:** "O volume cresceu, e a triagem continua sendo inspeção visual, curva por curva."
- **O:** "Milhares de curvas em arquivo e em campanhas novas — e no fim da fila sempre alguém olhando, à uma da manhã, na milésima curva." ⚠️ *(evite soar como crítica ao grupo: diga "funciona bem, mas não escala", não "um par de olhos só")*
- **P:** **leia em voz alta a única citação da palestra** — "*algumas curvas são de difícil interpretação*" — e emende: "Essa frase é a semente desta dissertação. O problema não são as ocultações óbvias; são essas."
- **T:** "Então o que eu construí?"

### S9 · A proposta: pipeline de triagem — 40 s
- **T:** "Uma pipeline em cinco etapas."
- **O:** *(percorra o diagrama sem detalhar caixa por caixa)* "Entra curva, sai um número entre 0 e 1."
- **P:** **a reformulação da espinha:** "E quero fixar desde já o que isso é: **não é um juiz, é uma fila de prioridade para os olhos humanos.**"
- **T:** "Cada caixa vem nos próximos slides. Começando pela primeira: os dados."

### S10 · De onde vêm os dados — 30 s
- **T:** "Duas fontes: o catálogo público B/occ do VizieR e o banco do Grupo do Rio."
- **O:** "Tudo consolidado num SQLite único, curvas e metadados."
- **P:** "Engenharia de dados foi metade do trabalho do mestrado — e é o que torna tudo reproduzível."
- **T:** "Com os dados na mão, veio a primeira dificuldade séria."

### S11 · O conjunto de dados rotulado — 60 s ⏸ **HONESTIDADE VOLUNTÁRIA**
- **T:** "1693 curvas rotuladas: 802 positivas reais."
- **O:** ⚠️ **antecipe a pergunta mais perigosa da defesa** — "Preciso ser honesto sobre um número: das 891 negativas, **702 são sintéticas**. Negativas reais rotuladas praticamente não existem em base pública — o banco tinha **três**. Essa é a fraqueza mais séria deste trabalho, e é exatamente por isso que o slide 30 existe: eu refiz o teste só com curvas reais."
- **P:** ✚ **transforme a limitação em achado** (nuance que o especialista destacou): "E vale dizer que isso não é um acaso do meu banco: é sintoma de que a comunidade não cataloga negativas. Mas uma corda negativa **é ciência** — restringe o limbo, diagnostica erro de efeméride, e é indispensável para limites sobre anéis e satélites. Recomendo, como produto desta dissertação, que passem a ser arquivadas."
- **T:** "Bom — e como é que uma curva entra num modelo?"

### S12–13 · Formando o dataset — 60 s **AS DUAS JUNTAS, RÁPIDO**
- **T:** "Cada curva é reduzida a um vetor de números."
- **O:** ⚠️ **não recite os 28 nomes.** Comprima: "Não são 28 características, são **três perguntas** medidas de 28 maneiras: **um — tem um degrau? dois — o degrau é maior que o barulho? três — ele sobrevive quando eu aliso a curva?**"
- **P:** "Do Savitzky-Golay basta o efeito: alisei a curva e refiz as mesmas contas. Se o degrau sobrevive, ele é real."
- **T:** "Vou mostrar isso em duas curvas concretas."

### S14 · A curva vira números: positivo — 40 s ⏸ **PAUSA DE 5 s**
- **T:** "Curva com ocultação, e a linha dela na tabela."
- **O:** *(aponte a linha destacada; **cale a boca por cinco segundos** deixando a banca comparar)*
- **P:** "Profundidade 0,43, SNR 7,0."
- **T:** "Agora a mesma tabela, outra curva."

### S15 · A curva vira números: negativo — 40 s
- **T:** "Curva sem evento, mesmas colunas."
- **O:** "Profundidade 0,31, SNR 4,4."
- **P:** **o soco:** "Isso é **perto**. Se uma coluna sozinha resolvesse, eu não precisaria de nada do que vem a seguir. O classificador não vê curvas — vê este contraste, em onze dimensões ao mesmo tempo."
- **T:** "E como uma máquina aprende um contraste desses?"

---

# BLOCO D — Machine Learning (16–26) · 9 min

> **Feynman:** ensine a árvore **fazendo uma**, em voz alta, com os números que a banca acabou
> de ver no slide 14. E não deixe o slide 19 virar taxonomia — nome de coisa não é a coisa.
> **Frase que fica:** "Quatro modelos, duas ideias: um comitê que vota e um aluno que refaz só
> as questões que errou."

### S16 · [Divisor] — 10 s
- **T:** "Prometo: nenhuma equação nos próximos dez slides."

### S17 · Classificação supervisionada — 40 s ⏸ **DESACELERE**
- **T:** "Aprendizado supervisionado: mostro exemplos rotulados, o modelo ajusta seus parâmetros."
- **O:** "A saída **não é um sim ou não** — é uma **probabilidade** entre 0 e 1."
- **P:** "A decisão vem depois, comparando essa probabilidade com um limiar τ, por padrão 0,5. **Guardem esse τ: ele volta como protagonista duas vezes.**" *(Trinta segundos bem gastos aqui salvam os slides 33 e 37.)*
- **T:** "O bloco de construção de três dos meus quatro modelos é a árvore de decisão."

### S18 · Árvores de decisão — 45 s
- **T:** "Uma árvore de decisão é o jogo das vinte perguntas."
- **O:** **faça uma, com os números do slide 14:** "SNR maior que 5? Sim. Profundidade maior que 0,35? Sim. Folha: ocultação."
- **P:** "Cada resposta corta o espaço em dois, até a folha decidir. E eu posso **ler a sequência inteira e discordar dela** — é daí que vem a interpretabilidade que eu reivindico."
- **T:** "Uma árvore sozinha, porém, é frágil."

### S19 · Genealogia das famílias — 20 s **RÁPIDO**
- **T:** "Esta é a genealogia dos modelos baseados em árvore."
- **P:** ⚠️ **não recite a taxonomia:** "Está aqui só para dizer que meus quatro modelos não são quatro ideias — são **duas**: votar junto e corrigir o próprio erro. Mais uma reta de referência que eu deixei de fora do bolo de propósito."
- **T:** "A primeira ideia: votar junto."

### S20 · Floresta aleatória — 45 s
- **T:** "Random Forest: um comitê de árvores."
- **O:** **analogia:** "É chamar cem pessoas para chutar o peso de um boi, cada uma olhando de um ângulo diferente, e tirar a média — os erros se cancelam."
- **P:** "Mas só funciona se elas **errarem em casos diferentes**. É por isso que cada árvore vê uma amostra sorteada dos dados e só um subconjunto das características: a aleatoriedade é o que descorrelaciona as árvores e reduz a variância."
- **T:** "A segunda ideia é o oposto: em vez de paralelo, em sequência."

### S21 · Gradient Boosting — 45 s
- **T:** "Boosting treina as árvores em sequência."
- **O:** **analogia:** "É um aluno só, que toda noite refaz exatamente as questões que errou no dia anterior."
- **P:** "Cada nova árvore é ajustada aos **erros** do conjunto acumulado. Bagging ataca a variância; boosting ataca o viés. São duas respostas diferentes ao mesmo dilema."
- **T:** "E por que comitês funcionam, afinal?"

### S22 · Por que comitês funcionam — 30 s **RÁPIDO**
- **T:** "Porque erros independentes se cancelam na votação — é o Teorema do Júri de Condorcet."
- **P:** "Os quatro modelos: Regressão Logística como referência linear, Random Forest, XGBoost e CatBoost. As árvores dão de brinde a importância de cada característica."
- **T:** "Antes dos resultados, preciso dizer como evitei me enganar."

### S23 · Avaliar sem se enganar — 35 s
- **T:** "Regra de ouro: o teste usa curvas que o modelo nunca viu."
- **O:** ⚠️ *(não explique o que é validação cruzada — diga o que ela te disse)* "Cinco dobras, com desvio pequeno."
- **P:** "O número não depende de qual pedaço dos dados eu escondi."
- **T:** "E as métricas."

### S24–25 · Métricas de performance — 40 s **AS DUAS JUNTAS, RÁPIDO**
- **T:** "Matriz de confusão e as métricas derivadas dela."
- **O:** ⚠️ **não defina precisão, sensibilidade, F1 nem AUC** — a banca sabe. "Reporto as quatro."
- **P:** "Duas decidem: **F1**, que equilibra os dois tipos de erro, e **AUC-ROC**, que mede a **ordenação** independentemente do limiar. Guardem a segunda — é ela que sustenta o final da apresentação."
- **T:** "Com método e métrica definidos, uma última decisão de projeto."

### S26 · Das 28 às 11 features — 35 s
- **T:** "Comecei com 28 características e terminei com 11."
- **O:** "Análise de redundância: correlação e ablação."
- **P:** **venda como evidência, não como faxina:** "Onze bastam, e isso é um sinal de que o modelo encontrou **estrutura**, não decorou ruído."
- **T:** "Agora, o que saiu."

---

# BLOCO E — Resultados (27–33) · 8 min

> **Feynman:** anuncie o padrão **antes** da tabela e **desarme a própria tabela**. Você tem um
> clímax melhor esperando dois blocos à frente — não gaste sua energia dramática aqui.
> **Frase que fica:** "Os quatro modelos são indistinguíveis — o mérito está nas
> características, não no classificador."

### S27 · [Divisor] — 10 s
- **T:** "Seis experimentos, e uma conclusão que me incomodou."

### S28 · Tabela dos seis experimentos — 90 s
- **T:** "Seis experimentos, variando características e composição do teste."
- **O:** ⚠️ **não leia célula por célula:** "Leiam a coluna do melhor F1: de 0,98 a 0,99 em todas as configurações."
- **P:** **desarme:** "O ponto não é o número alto, é a **estabilidade** — o resultado não depende do modelo nem da configuração. Isso é ótimo e é incômodo: significa que o mérito está nas características e nos dados, não no algoritmo da moda." E emende: "**Essa tabela não é o resultado da dissertação. É a checagem de que nada está quebrado. O resultado está no bloco do Quaoar.**"
- **P₂:** ⚠️ **se perguntarem sobre o Exp. 3** (a tabela do slide traz 0,9821, da variante 65/35): "Na versão final da dissertação eu igualei o split do Experimento 3 aos demais: em 80/20 o F1 é **0,9906**, e a variante 65/35, com 0,9838, ficou no apêndice como ablação do tamanho do treino."
- **T:** "Visualmente, o que isso significa."

### S29 · Separação das classes — 40 s
- **T:** "Curvas ROC e matriz de confusão do Experimento 2."
- **O:** "As ROC colam no canto ideal; os erros se contam nos dedos."
- **P:** "E o teste de McNemar diz que os quatro modelos são **estatisticamente equivalentes** — então eu escolho pelo mais simples de operar, não pelo 'melhor'."
- **T:** "Mas a pergunta que eu mesmo faria é outra."

### S30 · Só curvas reais — 45 s
- **T:** "'Você não está aprendendo o simulador?'"
- **O:** "Refiz o teste excluindo as sintéticas: avaliação 100% em curvas reais."
- **P:** "F1 em torno de 0,98 — cai cerca de um ponto. É o que se espera se o modelo aprendeu **física**, não o ruído do simulador."
- **T:** "Duas descobertas laterais valem um slide cada."

### S31 · Importância não é insubstituibilidade — 35 s **RÁPIDO**
- **T:** "A característica que as árvores apontam como mais importante é dispensável."
- **O:** "Removi a do K-Means: o F1 não caiu. Características colineares absorvem o papel."
- **P:** ⚠️ **honestidade:** "**Não leiam esse ranking como física.** Importância mede quem a árvore perguntou primeiro, não quem é indispensável."
- **T:** "E onde o modelo erra?"

### S32 · Onde o modelo erra — 45 s ⏸ **DESACELERE — momento de credibilidade**
- **T:** "Estes são falsos negativos."
- **O:** "Ruído alto, quedas rasas."
- **P:** *(aponte uma curva)* "**Eu mesmo hesitaria nessa.** Os erros do modelo estão onde os humanos também discordam — e isso motiva o slide seguinte."
- **T:** "Porque se o erro é hesitação, a hesitação é ajustável."

### S33 · O limiar τ — 50 s
- **T:** "Aqui o τ volta."
- **O:** **analogia:** "τ não é uma verdade da natureza, é a **altura da rede na quadra**. Em 0,5 eu digo 'só me avise quando tiver certeza'. Em 0,03: 'me avise em qualquer suspeita, eu tenho tempo de olhar'."
- **P:** "Baixando τ, a sensibilidade vai a **99,4%** no teste, ao custo de 5 alarmes extras em 179 negativas. E isso é **pós-processamento**: nada de retreinar. Quem escolhe a altura da rede é quem vai olhar as curvas — um alarme falso custa trinta segundos de um humano; um anel perdido custa uma descoberta."
- **T:** "Tudo isso, porém, é teste controlado. E no mundo real?"

---

# BLOCO F — Quaoar (34–38) · 8 min · **O PICO**

> **Feynman:** troque de registro — pare de reportar, comece a narrar. **Monte a aposta antes
> de mostrar o resultado.** E nunca diga "detectou o anel fraco": diga "não detectou pelo
> limiar; **ordenou** corretamente".

### S34 · [Divisor] — 30 s
- **T:** "Uma curva que o modelo nunca viu."
- **O:** "Ocultação por Quaoar, agosto de 2022. Dados cedidos pelo Chrystian Pereira e colaboradores — não entraram em treino nem em teste, não passaram por mim."
- **P:** **a aposta:** "O Quaoar tem dois anéis, um denso e um tênue. Eu vou pedir a um modelo que **nunca viu um anel na vida** que ache os dois."
- **T:** "Primeiro, a curva inteira."

### S35 · A curva completa — 45 s
- **T:** "Corpo principal, mais dois anéis."
- **O:** ⚠️ **use os descritores corretos** (não "o fino"): "O **Q1R, externo e denso**, a 4057 km do centro, descoberto por **Morgado e colaboradores em 2023** — e o **Q2R, interno e tênue**, a 2520 km, com cerca de 10 km de largura, descoberto por Pereira e colaboradores nesta ocultação."
- **P:** ⚠️ **ressalva obrigatória, senão a banca a faz:** "A curva inteira recebe p ≈ 0,99 — mas isso é **dominado pela queda do corpo principal**. Não é evidência de detecção de anel. Para isso, é preciso olhar em pedaços."
- **T:** "Então vamos sondar por recortes."

### S36 · Caçando estruturas por recortes — 60 s ⏸ **DESACELERE**
- **T:** "Seis janelas, cada uma sobre uma assinatura física distinta."
- **O:** ⚠️ **CORRIJA A LEGENDA AO FALAR** — o slide diz "anéis fortes" no plural, mas **existe um** anel denso, com **duas travessias**: "As duas travessias do **Q1R** passam com folga — 0,96 e 0,999. E passam por motivos físicos **diferentes**: numa delas o anel é largo e raso, com muitos pontos amostrados; na outra é o núcleo estreito e profundo."
- **P:** "Já as duas travessias do **Q2R** reprovam: 0,04 e 0,08. **Isso é um erro, e eu não vou chamar de outra coisa.**" ⏸ **PAUSA REAL. Deixe doer.**
- **T:** *(baixo, sem pressa)* "Mas olhem o vizinho."

### S37 · O sinal fraco ainda é sinal — 90 s ⏸ **O CLÍMAX**
- **T:** "Adjacente ao Q2R há um trecho de ruído que imita uma micro-ocultação. Ele recebe 0,0005. O anel real recebe 0,043."
- **O:** **analogia:** "A pergunta certa não é 'o alarme apitou?', é '**o ponteiro pulou?**'. É um detector de metais que não apitou, mas cujo ponteiro deu um salto de quase duas ordens de grandeza exatamente onde estava a moeda. O valor absoluto depende de onde **eu** pus o alarme; **o salto não depende de nada meu.**"
- **P:** **o pagamento da espinha:** "Pelo critério padrão o modelo disse 'não'. E mesmo dizendo 'não', ele colocou exatamente o trecho do anel fraco **86 vezes** acima de tudo o mais nessa curva. Ele hesitou, como um humano hesitaria — **mas hesitou no lugar certo.** Baixando τ para 0,03, as duas travessias do Q2R entram, e nem o controle nem o ruído cruzam a linha."
- **P₂:** ⚠️ **três ressalvas que você deve dizer antes que perguntem:**
  1. "Faço questão de dizer o que 86× **não é**: não é significância de detecção, não é SNR. É **separação relativa de escore** — e é o que basta para ordenar candidatos numa fila."
  2. "E τ = 0,03 foi ajustado **nesta curva**, para demonstrar a separação. Não é um limiar validado às cegas. O resultado defensável é o **ordenamento**, não o valor do limiar."
  3. "É **uma** curva, **um** objeto. É uma anedota bem comportada, não estatística."
- **T:** "E a curva do Quaoar me ensinou uma última coisa."

### S38 · Janelas maiores diluem — 45 s
- **T:** "Testei a explicação alternativa: 'a janela era curta demais'."
- **O:** "É falsa. Ao ampliar a janela, a probabilidade **cai** ainda mais."
- **P:** "A causa é estrutural: minhas características são **estatísticas globais** da janela. Uma queda de meio segundo diluída em dezenas de segundos de linha de base limpa vira um detalhe estatisticamente desprezível. A 18 km/s, o corpo dura um minuto e um anel de 10 km dura meio segundo — duas ordens de grandeza. A fronteira de detecção é a **razão** entre a duração do evento e a da janela."
- **T:** "E isso define exatamente o próximo passo do trabalho."

---

# BLOCO G — Fecho (39–42) · 3,5 min

> **Feynman:** o slide 39 é onde você soa cientista. Um par por respiração, sem elaborar.
> Nada de material novo no 40 — só os três números.

### S39 · Dificuldades e soluções — 50 s
- **T:** "Quatro dificuldades, quatro decisões."
- **O:** *(um par por respiração, sem elaborar)* "Dados dispersos → banco unificado. Três negativas reais → simulador físico mais recortes de curvas reais. Redundância → 28 para 11. Eventos curtos e rasos → τ ajustável por campanha."
- **P:** "A maior fragilidade — as três negativas nativas — está dita na dissertação com todas as letras."
- **T:** "Em três números, então."

### S40 · Conclusões — 50 s
- **T:** "F1 de 0,98 a 0,99, estável em seis experimentos e quatro modelos."
- **O:** "Sensibilidade de 99,4% com o τ ajustado, sem retreinar."
- **P:** "E 86× de separação entre anel real e ruído, em dado externo ao treino. Uma ferramenta reproduzível de triagem e priorização — pronta para revisitar arquivos de curvas."
- **T:** "O que fica para depois."

### S41 · Trabalhos futuros — 45 s
- **T:** "Quatro direções."
- **O:** ⚠️ **amarre ao seu próprio dado:** "A janela deslizante com características locais **não é uma ideia bonita que eu tive — é o que o slide 38 me obrigou a concluir.**"
- **P:** "Ampliar as negativas reais; redes convolucionais sobre a série bruta; e triagem em tempo quase-real nas campanhas do grupo." ⚠️ **honestidade:** "A rede convolucional é o caminho óbvio e eu **não** fiz. Não é preguiça, é amostra: com 1693 curvas eu não teria com que treinar."
- **T:** "Encerro agradecendo."

### S42 · Obrigado — 30 s
- **T:** *(olho nas pessoas, nominalmente)* "Dr. Júlio Camargo, pela orientação; o Grupo do Rio; Wellington Gomes-Ferrante e Felipe Braga-Ribas pelo simulador; Chrystian Pereira pelos dados de Quaoar; a banca; minha família."
- **P:** **a espinha, uma última vez:** "Se esta ferramenta serve para alguma coisa, é para que a próxima curva duvidosa não passe batido. Obrigado — estou à disposição."

---

# BACKUPS (43–47) — só sob demanda

| Slide | Quando usar | Frase de entrada |
|---|---|---|
| **44** Baseline trivial | "Precisava de ML?" | "Uma régua já vai longe — um limiar numa única característica dá F1 0,90. A física é forte. O ML corta o erro restante em cerca de **dez vezes**. É análise complementar, posterior à dissertação." |
| **45** Sobreajuste | "0,99 não é overfit?" | "Cinco indícios independentes. O mais forte: **a Regressão Logística também acerta, e ela tem doze parâmetros — não há como decorar 1353 curvas com doze parâmetros.** Logo o mérito está nas características." ⚠️ **NÃO** use as 67 curvas de baixo SNR como argumento: elas participaram do treino. |
| **46** Teste cego Umbriel | "Testou às cegas?" | "18 curvas, uma divergência. **Não vou dizer que o modelo acertou** — vou dizer que ali dois olhos humanos discordariam. Que é exatamente o problema que motivou esta dissertação." *(fecha o círculo com a espinha — melhor cartão da sua mão)* |
| **47** Recortes de Quaoar | Detalhe do 36–37 | "Janela a janela, com as probabilidades do XGBoost." |

---

# ⚠️ CORREÇÕES DE FÍSICA — a fazer NA FALA (os slides não mudam)

Validado por especialista em ocultações. Ordem de gravidade:

| # | Slide | O slide diz | **Diga isto** |
|---|---|---|---|
| 1 | **36** | "anéis fortes" (plural) | **"as duas travessias do anel Q1R"** — existe **um** anel denso. Erro factual que um especialista vê em cinco segundos. |
| 2 | **7** | "precisão de km", "forma" | Qualifique: Fresnel ~1 km + diâmetro estelar + **tempo de integração** (0,1 s = 2 km a 18 km/s). E **"limbo projetado"**, não forma 3D. |
| 3 | **37** | "86×" | Declare que é **razão de escore**, não significância/SNR; e que **τ=0,03 foi escolhido nesta curva** (a posteriori). |
| 4 | **35** | "Q2R (o fino)" | **"Q2R, interno e tênue"** (2520 km) vs **"Q1R, externo e denso"** (4057 km). E **cite Morgado et al. 2023** pela descoberta do Q1R. |
| 5 | **35** | "p ≈ 0,99" | Acrescente: **"dominado pela queda do corpo principal — não é detecção de anel."** |
| 6 | **5** | "instante diferente" | Acrescente **duração/corda** e a velocidade da sombra (~18 km/s). |
| 7 | **4** | "a luz pisca" | **"desaparece por alguns segundos"** + **"esta é uma ilustração; não resolvemos o corpo."** |
| 8 | fala | "mais precisa depois de sondas in situ" | Qualifique: **do solo**, para corpos pequenos e distantes; radar vence para asteroides próximos. |
| 9 | ✚ **novo** | — | Uma frase sobre **Gaia/efemérides** (S5) e uma sobre o **valor científico das negativas** (S11). |

## Verificar antes da defesa

- [ ] **Modelo de ruído do simulador** (Gomes-Ferrante & Braga-Ribas): é branco/Poisson ou inclui ruído **correlacionado** (cintilação, transparência)? Se for só branco, **diga isso como limitação** — é muito melhor que ser pego. Pergunta provável.
- [ ] **Qual canal é a sua curva de Quaoar.** A tese diz Gemini-'Alopeke **Red-z** — nesse canal há ingresso **e** egresso de Q2R, então "as duas travessias" está correto. (No canal r' haveria só o egresso.)
- [ ] **Crédito da ilustração de Chariklo** ("L. Maquet") — muitas circulam como ESO/L. Calçada. Se for Chariklo com anéis, citar **Braga-Ribas et al. 2014** é cortesia bem-vista (descoberta do Grupo do Rio).
- [ ] **Typo no slide 8:** "Alguma curvas" → "Algumas curvas" *(1 min, se mudar de ideia sobre editar)*.
- [ ] Existe **corrigendum** de Pereira et al. 2023 (A&A 2024): profundidades ópticas subestimadas por fator 2. **Você não cita τ nos slides** — então não há ação, mas saiba disso se o assunto surgir.

## Perguntas prováveis — resposta em uma respiração

1. **"Precisão de km com exposições de segundos?"** → Resolução = √(Fresnel² + diâmetro estelar² + (V·t_exp)²). O termo de exposição domina: 0,1 s = 2 km, 2 s = 35 km. Para o classificador o que importa não é km, é **quantos pontos caem dentro da queda** — e é por isso que evento curto mal amostrado é o regime de falha.
2. **"No regime de difração a curva tem franjas — suas features de profundidade valem?"** → Não plenamente, e é limite conhecido. Minhas features medem algo próximo de **opacidade integrada**, não a assinatura de franjas. É estruturalmente por isso que o Q2R pontua baixo. Correção certa: features locais em janela deslizante, ou CNN sobre a série bruta.
3. **"702 negativas sintéticas — não aprendeu o simulador?"** → Exp. 3 (100% real) cai ~1 ponto, e Quaoar é externo. A versão forte da pergunta é sobre **ruído correlacionado**: os 186 recortes de curvas reais mitigam parcialmente porque carregam ruído real. *(Ver checklist acima.)*
4. **"Por que XGBoost se o McNemar diz que são equivalentes?"** → Justamente por isso: sendo equivalentes, escolho por critérios operacionais — menor perda de teste, liderança no teste só-real, e **probabilidades mais polarizadas**, que tornam o ajuste de τ mais robusto. É a alavanca da pipeline.
5. **"O evento de 2025 com possível novo satélite de Quaoar — seu método pegaria?"** → É exatamente o caso de uso: evento isolado, curto, longe da queda principal. Com janela deslizante e τ baixo, entra na fila. Mas **candidato, não descoberta** — confirmação exige múltiplos sítios independentes.

---

# O que CORTAR da fala (o slide já diz)

- Ler o **roteiro** (S2) e os cinco itens em voz alta.
- **Recitar nomes de features** (S12–13): "t-Student por quartil, Kolmogorov-Smirnov, Savitzky-Golay" em série. Três perguntas, não 28 nomes.
- **Definir** precisão, sensibilidade, F1, AUC, matriz de confusão (S24–25).
- **Explicar o que é** validação cruzada (S23) — diga o que ela te disse.
- **A taxonomia** do S19.
- **Narrar o pipeline caixa por caixa** (S9) — você detalha tudo nos 15 slides seguintes.
- **O que é o VizieR / o esquema do SQLite** (S10).
- **Células da tabela** do S28 — diga a faixa e o padrão.
- **Predição/efemérides no S5** além da frase única.
- **Muletas:** "como vocês podem ver", "vou falar rapidamente sobre", desculpas pela figura, e qualquer ressalva **nova** no S40.

# Regras de ensaio

1. Três passadas: (1) lendo este roteiro, (2) só com os slides, (3) cronometrada, com alguém assistindo.
2. **Marco de controle:** ao entrar no slide 27, você deve estar em ~21 min. Se estiver em 26+, comprima 19, 22, 25 e 31.
3. **Decore só três coisas:** a espinha (S1), o pagamento (S37) e as três ressalvas do S37.
4. Silêncio é instrumento: 5 s nos slides 14–15, e uma pausa real depois de "isso é um erro" no S36.
5. Água antes do S28 e do S37.
