# Ensaio para a Defesa de Mestrado

**Pipeline para Detecao Automatizada de Ocultacoes Estelares em Curvas de Luz com Tecnicas de Machine Learning**

Thiago Laidler Vidal Cunha | Orientador: Dr. Julio Camargo | Observatorio Nacional - COPAA

*Transcricao do ensaio de apresentacao, baseada nas tecnicas de comunicacao de Feynman e Sagan.*

---

## ABERTURA (60 segundos)

*[Slide 1: titulo da dissertacao. Respire. Conte "1, 2" em silencio antes de comecar.]*

"Boa tarde. Antes de falar sobre machine learning, quero contar uma historia sobre sombras.

Quando uma nuvem passa na frente do Sol, ela projeta uma sombra no chao. Se voce estiver na sombra, o Sol escurece. Se estiver fora, nao.

*[Pausa de 2 segundos.]*

Agora imagine que, em vez do Sol, e uma estrela a bilhoes de quilometros. E em vez de uma nuvem, e um asteroide -- um objeto do tamanho de uma cidade -- passando na frente dela. A sombra desse asteroide viaja pela superficie da Terra a milhares de quilometros por hora. Se voce tem um telescopio no caminho certo, no momento certo, ve a estrela *apagar* por alguns segundos.

*[Pausa.]*

Isso e uma ocultacao estelar. E a curva que o telescopio registra -- brilho da estrela ao longo do tempo -- e uma curva de luz. E a partir dessa curva que extraimos o tamanho, a forma e ate os aneis de objetos que nunca visitamos.

O problema e que hoje geramos *milhares* dessas curvas por campanha. Alguem precisa olhar cada uma e dizer: 'esta tem ocultacao, esta nao'. Esta dissertacao construiu uma maquina que faz isso automaticamente."

---

## CAPITULO 2 -- O fenomeno (3-4 minutos)

*[Slide 2: Figura do Chariklo (fig:ilustracao_ocultacao)]*

"Essa e uma representacao artistica do Centauro Chariklo. Em 2014, uma ocultacao estelar revelou que ele tem *aneis* -- como Saturno, mas em um corpo de 250 km. A curva de luz embaixo mostra as quedas: uma para cada anel e uma para o corpo.

*[Pausa.]*

O ponto e: a curva de luz *contem* a fisica do objeto. Cada queda e informacao."

*[Slide 3: Painel Umbriel (fig:umbriel_painel)]*

"Para dar um exemplo concreto, vou usar um caso real em que participei: a ocultacao por Umbriel, satelite de Urano, em setembro de 2020.

*[Aponta para (a)]* Aqui esta o mapa de previsao -- a sombra de Umbriel cruzando a America do Norte.

*[Aponta para (b)]* O zoom mostra onde cada observador se posicionou -- sao telescopios espalhados pela costa leste dos EUA.

*[Aponta para (c)]* Cada telescopio produz centenas de imagens como estas. Sao quadros CCD -- a materia-prima dos dados. Neste caso, Urano e tao brilhante que foi preciso usar coronagrafia digital para enxergar Umbriel ao lado.

*[Aponta para (d)]* E o resultado da fotometria e esta curva de luz. O eixo vertical e o brilho normalizado; o horizontal e o tempo. A queda no meio e a ocultacao. O verde embaixo e o ruido de fundo.

*[Pausa de 2 segundos.]*

Essa curva e *facil*. A queda e profunda, o ruido e baixo. O desafio comeca quando a queda e rasa e o ruido e alto -- quando um humano olha e nao tem certeza."

*[Slide 4: Bardecker + Antiope (fig:curvas_cordas)]*

"Quando varios observadores registram a mesma ocultacao, cada um contribui com uma *corda* -- um corte na silhueta do corpo. Combinando varias cordas, reconstruimos o perfil. A direita, o asteroide binario Antiope -- cada traco diagonal e uma corda de um observador diferente."

*[Slide 5: Modelo SORA (fig:modelo_sora)]*

"Na pratica, a curva observada nao e um degrau perfeito. Ela e suavizada pela difracao de Fresnel, pelo tamanho da estrela, e pelo tempo de exposicao do detector. O SORA ajusta todas essas componentes simultaneamente para extrair os instantes exatos de entrada e saida da ocultacao.

A escala de Fresnel, para dar um numero: um objeto a 40 UA, no visivel, produz uma resolucao de 1,2 km. Quilometros de resolucao a bilhoes de quilometros de distancia -- melhor que qualquer telescopio terrestre por imageamento direto."

---

## CAPITULO 3 -- As ferramentas de ML (4-5 minutos)

*[Slide 6: O problema como classificacao]*

"Agora, o problema. Tenho uma curva de luz. Quero saber: tem ocultacao ou nao? Isso e um problema de *classificacao binaria*. Sim ou nao. Um ou zero.

*[Pausa.]*

A ideia e simples: eu pego cada curva, calculo alguns numeros que a descrevem -- quanto caiu o fluxo, quanto tempo durou a queda, qual o nivel de ruido -- e entrego esses numeros a um algoritmo que aprendeu, a partir de exemplos, a distinguir curvas com ocultacao de curvas sem.

E como ensinar alguem a reconhecer chuva pela janela: nao precisa saber meteorologia. So precisa de exemplos suficientes de 'chovendo' e 'nao chovendo', e de saber onde olhar."

*[Slide 7: Regressao Logistica -- a sigmoide]*

"O modelo mais simples e a Regressao Logistica. Ela faz uma soma ponderada das caracteristicas da curva e passa o resultado por uma funcao -- a sigmoide -- que comprime qualquer valor para o intervalo entre zero e um. Esse numero e interpretado como probabilidade.

Se a probabilidade e maior que 50%, o modelo diz 'ocultacao'. Senao, 'sem evento'.

*[Pausa.]*

Esse limiar de 50% e arbitrario. E essa e uma das coisas que exploramos: o que acontece se eu baixo o limiar para 30%? Detecto mais eventos, mas tambem mais falsos alarmes. E um *trade-off*, e a escolha depende do custo de cada erro."

*[Slide 8: Random Forest e Boosting]*

"Para ir alem da Regressao Logistica, usamos *ensembles* de arvores de decisao. Uma arvore sozinha e como um fluxograma: 'o minimo do fluxo e menor que 0,8? Se sim, va para a esquerda; se nao, para a direita.' Simples, mas instavel.

O Random Forest treina centenas de arvores, cada uma em uma amostra diferente dos dados, e decide por votacao majoritaria. E o Teorema do Juri de Condorcet: se cada 'jurado' acerta mais da metade das vezes, o grupo acerta quase sempre.

XGBoost e CatBoost sao variantes de *boosting*: cada arvore nova e treinada para corrigir os erros da anterior. Em vez de votar, elas se complementam."

*[Slide 9: Metricas]*

"Como sei se o modelo e bom? Nao basta acuracia. Se 90% das curvas nao tem ocultacao, um modelo que sempre diz 'nao' acerta 90% -- mas nao detecta *nenhum* evento.

Por isso usamos sensibilidade -- dos eventos reais, quantos o modelo encontrou -- e precisao -- dos que o modelo apontou como evento, quantos eram reais. O F1-score equilibra as duas."

---

## CAPITULO 4 -- A pipeline (3-4 minutos)

*[Slide 10: Diagrama da pipeline]*

"A pipeline tem cinco etapas. Vou descreve-las como uma linha de montagem.

*[Pausa.]*

**Etapa 1**: Coleto as curvas de luz do VizieR e do Grupo do Rio, e guardo tudo em um banco SQLite. **Etapa 2**: Normalizo o fluxo -- coloco todas as curvas na mesma escala. **Etapa 3**: Construo o dataset -- e aqui houve um desafio: eu tinha 802 curvas com ocultacao e apenas 3 sem. Para equilibrar, recortei trechos sem evento de curvas positivas e gerei curvas sinteticas. No total, 1693 amostras. **Etapa 4**: Extraio caracteristicas numericas de cada curva -- 28 inicialmente, reduzidas a 13 apos analise de redundancia. **Etapa 5**: Treino e avalio os quatro modelos."

*[Slide 11: Features]*

"As 13 caracteristicas finais capturam tres aspectos da curva: *quanto* caiu (profundidade, SNR), *por quanto tempo* (duracao do dip), e *quao diferente* o trecho da queda e do resto da curva (testes estatisticos entre quartis, razao chi-quadrado).

Uma feature que merece destaque e a distancia entre centroides do K-means: aplico um agrupamento com dois clusters ao fluxo. Se a curva tem dois niveis claros -- um alto e um baixo -- a distancia e grande. Se e so ruido, os dois clusters ficam juntos."

---

## CAPITULO 5 -- Resultados (4-5 minutos)

*[Slide 12: Tabela comparativa dos 7 experimentos]*

"Sete experimentos. Vou direto ao ponto.

*[Pausa de 2 segundos. Aponta para a tabela.]*

Com 28 features, F1 de 0,994. Com 13 features, F1 de 0,991. Com 11 features, F1 de 0,991. Ou seja: removemos metade das variaveis e o desempenho *nao caiu*.

*[Pausa.]*

AUC-ROC acima de 0,999 em todos os experimentos. Os modelos separam as classes quase perfeitamente."

*[Slide 13: Ablacao do K-means]*

"A feature do K-means aparecia como a mais importante nos graficos de importancia do Random Forest. Mas quando a removemos... nada aconteceu. F1 caiu menos de 0,3 ponto percentual.

*[Pausa.]*

Isso e um resultado importante por si so: *importancia de feature nao significa insubstituibilidade*. Outras variaveis correlacionadas compensaram a ausencia."

*[Slide 14: Experimento 7 -- generalizacao]*

"O teste mais honesto e o Experimento 7: treinamos com tudo, mas testamos *apenas* em curvas reais -- sem sinteticas no teste. F1 cai para 0,982. Ainda excelente, mas e a medida mais realista que temos."

*[Slide 15: Verificacao low-SNR]*

"Como verificacao complementar, separamos as 67 curvas do banco com SNR abaixo de 3 -- as mais ruidosas. Todos os modelos de arvore acertaram 67 de 67. A Logistica errou uma.

Esse teste tem limitacoes claras: essas curvas participaram do treino. Mas o resultado confirma que o modelo nao rejeita sistematicamente eventos dificeis."

---

## CAPITULO 6 -- Conclusoes (2-3 minutos)

*[Slide 16: Contribuicoes]*

"Cinco contribuicoes.

Primeiro: uma pipeline completa, reproduzivel, em Python. Do banco de dados ao modelo treinado.

Segundo: 13 features baseadas na fisica do problema, validadas experimentalmente.

Terceiro: a demonstracao de que importancia de feature nao e sinonimo de necessidade.

Quarto: evidencia de que o desempenho satura com 700 amostras de treino.

Quinto: um metodo de ajuste de limiar que permite operar em regime de alta sensibilidade sem retreinar."

*[Slide 17: Limitacoes e futuro]*

"As limitacoes sao claras. O dataset e parcialmente sintetico. Nao testamos em catalogos externos. Os hiperparametros nao foram otimizados. E a maioria das curvas no dataset e 'facil'.

*[Pausa.]*

O proximo passo natural e testar em curvas realmente dificeis -- SNR baixo, com negativos genuinos de baixo SNR no teste. E o passo ambicioso e a classificacao multi-classe: distinguir uma ocultacao por corpo solido de uma assinatura atmosferica, de um anel, de um padrao de Fresnel. Isso exigiria features novas e um dataset curado para cada categoria."

---

## ENCERRAMENTO (30 segundos)

"Esta dissertacao mostrou que e possivel automatizar a triagem de curvas de luz de ocultacoes estelares com modelos interpretaveis e desempenho superior a 99% em F1. O modelo nao substitui o astronomo -- ele diz *onde olhar primeiro*.

*[Pausa de 3 segundos.]*

Obrigado."

---

## SIMULACAO DE PERGUNTAS DA BANCA

### Pergunta 1 (provavel)

**"Voce mencionou que 702 das 891 negativas sao sinteticas. Isso nao compromete a validade dos resultados?"**

"Compromete parcialmente, e e importante ser honesto sobre isso. O Experimento 7 foi desenhado exatamente para medir esse efeito: quando testamos apenas em curvas reais, o F1 cai de 0,99 para 0,98. A queda e pequena, mas existe. O que nao sabemos e como o modelo se comportaria com centenas de negativas reais de diferentes catalogos e condicoes. Essa e a limitacao numero um do trabalho, e a primeira direcao de trabalho futuro: um experimento *real holdout* puro."

---

### Pergunta 2 (provavel)

**"Por que nao usar redes neurais convolucionais, como o ODNet?"**

"Tres razoes. Primeira: interpretabilidade. Com arvores de decisao, sei *quais features* levaram a decisao -- posso verificar se fazem sentido fisico. Com uma CNN, a decisao e opaca. Segunda: volume de dados. CNNs exigem milhares a milhoes de exemplos; eu tinha 802 positivas. Terceira: reprodutibilidade -- os classificadores que usei estao em bibliotecas estaveis e rodam em qualquer laptop. Dito isso, a arquitetura da pipeline permite incorporar uma CNN como quinto classificador no futuro, sem alterar o resto do fluxo."

---

### Pergunta 3 (dificil)

**"Seu modelo nao esta matando uma barata com uma bazuca? Bastaria olhar o fluxo minimo e a amplitude para classificar a maioria das curvas."**

*[Pausa de 2 segundos. Nao se apresse.]*

"Para a maioria das curvas, sim. Tres numeros resolveriam. E o F1 de 0,99 reflete em parte que o dataset e dominado por curvas 'faceis'. Mas a pipeline nao foi feita para as 95% faceis -- foi feita para as 5% que um humano olharia duas vezes. As features de comparacao entre quartis, o chi-quadrado do modelo square-well, e o SNR do dip existem para os casos marginais. Alem disso, o estudo de ablacao mostrou que mesmo removendo features aparentemente essenciais, o modelo se sustenta -- o que prova que as features remanescentes capturam redundancia suficiente para os casos dificeis. Reconheco a limitacao: nao temos negativas de baixo SNR no teste para provar isso numericamente. Mas a arquitetura esta pronta para esse teste."

---

### Pergunta 4 (sobre o K-means)

**"Se a feature do K-means e dispensavel, por que inclui-la no trabalho?"**

"Porque a dispensabilidade e o resultado, nao o pressuposto. Antes do estudo de ablacao, os graficos de importancia mostravam o K-means como a feature dominante no Random Forest. Um pesquisador que olhasse apenas os graficos de importancia concluiria que ela e essencial. A ablacao mostrou o contrario -- e essa e, na minha opiniao, uma das contribuicoes mais uteis do trabalho: importancia algoritmica nao significa necessidade. Isso tem implicacao pratica: simplifica a pipeline e alerta contra decisoes baseadas apenas em ranking de features."

---

### Pergunta 5 (sobre futuro)

**"A classificacao multi-classe que voce propoe -- corpo, atmosfera, anel, Fresnel -- e viavel com essa mesma abordagem de features classicas?"**

*[Pausa.]*

"Parcialmente. Para distinguir corpo solido de atmosfera, features como a simetria do perfil de ingresso e egresso e a presenca de refracao gradual provavelmente seriam discriminativas com modelos de arvore. Para aneis, a presenca de quedas secundarias e uma feature clara. Mas para padroes finos de Fresnel, acredito que seria necessario incorporar features baseadas em modelos fisicos -- ajuste a padroes de difracao, por exemplo -- ou talvez recorrer a CNNs que operem diretamente na serie temporal. A abordagem ideal provavelmente seria hibrida: features classicas para a triagem inicial e modelos mais sofisticados para a classificacao fina."

---

## NOTAS DE ORATORIA

### Tecnica Feynman aplicada

- Toda explicacao parte de uma analogia concreta antes da formalizacao (sombra da nuvem, chuva pela janela, linha de montagem, juri de Condorcet)
- Jargao tecnico e sempre definido na primeira ocorrencia ("sensibilidade -- dos eventos reais, quantos o modelo encontrou")
- Segunda versao de cada explicacao deve ser mais curta que a primeira

### Tecnica Sagan aplicada

- Estrutura em tres atos: por que importa (sombras, estrelas apagando) -> o problema (milhares de curvas, triagem manual inviavel) -> a solucao (pipeline automatizada)
- Escala e emocao: "quilometros de resolucao a bilhoes de quilometros de distancia"
- Pausas deliberadas antes de numeros importantes e apos afirmacoes fortes

### Pausas criticas

- Antes de comecar (conte "1, 2")
- Apos "Isso e uma ocultacao estelar"
- Antes de mostrar cada tabela de resultados
- Apos "nada aconteceu" (ablacao do K-means)
- Antes de "Obrigado" final (3 segundos)

### Tempo estimado

| Bloco | Duracao |
|-------|---------|
| Abertura | 1 min |
| Capitulo 2 | 3-4 min |
| Capitulo 3 | 4-5 min |
| Capitulo 4 | 3-4 min |
| Capitulo 5 | 4-5 min |
| Capitulo 6 + Encerramento | 2-3 min |
| **Total** | **~20-22 min** |

Dentro do padrao de 25 minutos de apresentacao + 20 minutos de perguntas.
