# Roteiro de ensaio — Defesa de Mestrado (45 min)

> Ensaie em voz alta, cronometrando por seção. O texto abaixo é fala sugerida, não
> decoreba: domine a *ideia* de cada slide e uma frase-ponte para o seguinte.
> Marcações: ⏱ tempo-alvo acumulado · ➡ frase de transição.

---

## A. Abertura (⏱ 0–2 min)

**1. Capa** — "Bom dia. Agradeço à banca pela presença. Vou apresentar a dissertação
'Pipeline para Detecção Automatizada de Ocultações Estelares em Curvas de Luz com
Técnicas de Machine Learning', orientada pelo Dr. Júlio Camargo."
➡ "Em 45 minutos quero convencê-los de três coisas — e este é o caminho."

**2. Roteiro** — Um período por item, sem ler a lista: "Primeiro o fenômeno; depois o
problema de escala que ele gera; como traduzi curvas em números; o que os modelos
alcançaram; e a prova de fogo numa curva real de Quaoar."

## B. Ocultações — o fenômeno (⏱ 2–9 min)

**3. [Divisor]** — meia frase: "Começando pela física."

**4. O que é uma ocultação** — "Um corpo pequeno do Sistema Solar passa na frente de uma
estrela; para quem está na sombra, a estrela 'pisca'. Este é o Centauro Chariklo com seus
anéis — e a curva de luz esquemática embaixo mostra o que registramos: quedas no fluxo."
*Apontar: corpo → queda central; anéis → quedas laterais.*

**5. A sombra varre a Terra** — "A sombra é quase uma cópia do corpo projetada no chão.
Observadores em posições diferentes cortam a sombra em instantes diferentes — aqui a
previsão para Umbriel em 2020, que o nosso grupo observou."

**6. Da câmera à curva** — "Cada estação grava vídeo; a fotometria diferencial transforma
os frames nesta série temporal. **Este objeto — a curva de luz — é o protagonista da
dissertação.**"
➡ "E por que tanto esforço por uma curva?"

**7. Ciência de precisão** — "Cada curva vira uma corda sobre o corpo. Com várias cordas,
desenhamos o limbo com precisão de quilômetros — de um objeto a bilhões de km. É a técnica
mais precisa depois de sondas in situ: mede tamanho, forma, anéis, atmosferas."
➡ "O sucesso da técnica criou o problema que motiva a tese."

## C. O problema e os dados (⏱ 9–17 min)

**8. O gargalo é humano** — "Gaia melhorou as efemérides; campanhas se multiplicaram;
cidadãos-cientistas observam. Resultado: milhares de curvas por ano — e a triagem ainda é
um par de olhos por curva. Pior: o olho cansado perde justamente o evento sutil."

**9. A proposta** — Percorrer o diagrama da esquerda para a direita em ~40 s: "curvas
entram num banco único, são normalizadas, viram vetores de características, e quatro
classificadores devolvem uma probabilidade de ocultação."

**10. De onde vêm os dados** — "Duas fontes: o catálogo público B/occ do VizieR e o banco
do Grupo do Rio. Tudo consolidado num SQLite com duas tabelas — a curva e seus metadados.
Engenharia de dados foi metade do trabalho do mestrado."

**11. O conjunto de dados rotulado** — "1693 curvas: 802 positivas reais. E as negativas? Quase
não existem em catálogo — ninguém arquiva 'a noite em que nada aconteceu'. Solução: 702
sintéticas com o simulador físico de Gomes-Ferrante & Braga-Ribas, 186 recortes de trechos
sem evento de curvas reais, 3 nativas — e daí treino e teste são sorteados (80/20)." *Falar a
limitação com naturalidade — ela volta no slide 32 (dificuldades).*

**12. Curva vira números (positivo)** — "Aqui o passo conceitual central: cada curva é
resumida em ~1 dúzia de números — profundidade da queda, SNR, duração, estatísticas. A
curva com ocultação... vira a linha destacada da tabela — valores reais do dataset: queda de
0,43, SNR 7." *Seguir a seta com a mão até a linha vermelha.*

**13. Curva vira números (negativo)** — "A curva sem evento, nas MESMAS colunas: queda 0,31,
SNR 4, metade da dispersão. O classificador não vê curvas — vê este contraste numérico."
➡ "E como uma máquina aprende esse contraste?"

## D. Machine Learning — sem caixa-preta (⏱ 17–24 min)

**14. [Divisor]** — "Prometo: nenhuma equação nos próximos cinco slides."

**15. Classificação supervisionada** — "Mostramos exemplos rotulados; o modelo ajusta seus
parâmetros para acertar o rótulo. A saída é uma probabilidade entre 0 e 1 — e decidimos
'positivo' acima de um limiar τ, por padrão 0,5. Guardem esse τ: ele volta como
protagonista."

**16. Árvores e florestas** — "Uma árvore de decisão faz perguntas simples — 'a queda é
mais funda que X?' — e sozinha erra. Uma floresta de centenas de árvores, cada uma vendo
um pedaço diferente dos dados, vota — e o comitê erra muito menos."

**17. Por que comitês funcionam** — "Erros independentes se cancelam na votação. Usei 4
modelos de famílias diferentes: Regressão Logística como referência linear, Random Forest,
XGBoost e CatBoost. Bônus das árvores: elas dizem quais características pesaram — é
interpretável."

**18. Avaliar sem se enganar** — "Regra de ouro: o teste usa curvas que o modelo nunca
viu. E validação cruzada em 5 dobras confirma que o resultado não depende de um sorteio
feliz. Reporto precisão, sensibilidade, F1 — a média harmônica das duas — e AUC."

**19. 28 → 11 features** — "Comecei com 28 características; análise de redundância
(correlação + ablação) mostrou que 11 bastam. Menos dimensões, mesma informação, mais
interpretabilidade."
➡ "Com dados e método na mesa: o que saiu?"

## E. Resultados (⏱ 24–33 min)

**20. [Divisor]** — "Três resultados principais e uma lição metodológica."

**21. A tabela** (~2 min) — "Seis experimentos variando features e composição do teste.
Leiam a coluna Melhor F1: de 0,982 no teste 100% real a 0,994. O ponto não é um número
alto — é a **estabilidade**: não depende de configuração. E comparem as linhas 1 e 2:
de 28 para 11 features, mesma performance — parcimônia validada. Exp. 3 é o mais
exigente — teste só com curvas reais — e ainda dá 0,982." *(Se citarem o 0,978 da tese:
é o mínimo entre TODOS os modelos, inclusive a Regressão Logística; a tabela mostra o
melhor por experimento.)*

**22. ROC/confusão** — "Visualmente: as ROC coladas no canto perfeito; na matriz de
confusão, erros contados nos dedos. McNemar diz que os 4 modelos são estatisticamente
equivalentes — a escolha entre eles vira critério prático."

**23. Só curvas reais** — "A pergunta que eu mesmo faria: 'não está aprendendo o
simulador?' Teste 100% real: F1 0,98. Caiu 1 ponto — sinal de que captura física, não
artefato."

**24. Importância ≠ insubstituibilidade** — "Lição metodológica que considero contribuição:
a feature do K-Means era a 'mais importante' das árvores. Removida... nada aconteceu.
Features colineares absorvem o papel. Importância alta não significa informação exclusiva."

**25. Onde erra** — "Honestidade: os falsos negativos são curvas assim — ruidosas, rasas.
Um humano também hesitaria. E isso motiva o próximo slide."

**26. O limiar τ** — "Perder um evento real custa muito mais que revisar um alarme falso.
Como a saída é probabilidade, basta baixar τ — sem retreinar — e a sensibilidade sobe a
99,4% no teste, ao custo de 5 alarmes extras em 179 negativas. É uma alavanca
operacional, calibrada por campanha."
➡ "Tudo isso em teste controlado. E no mundo real?"

## F. Quaoar — a prova de fogo (⏱ 33–39 min)

**27. [Divisor]** — "Uma curva que o modelo nunca viu, de um evento famoso: a ocultação
por Quaoar de 2022, dados cedidos pelo Chrystian Pereira — o evento dos dois anéis."

**28. Curva completa** — "Corpo central profundo, e estas estruturas rasas nos insets: os
anéis Q1R e Q2R. Curva inteira no modelo: p ≈ 0,99. Mas detectar o corpo é fácil —"

**29. Recortes** — "— o interessante é sondar por janelas. Anéis fortes: 0,96 a 0,999.
Agora as duas travessias do anel fino Q2R: 0,04 e 0,08. Reprovados no limiar padrão?" *Pausa. Deixar o
desconforto no ar.*

**30. O clímax** (~2 min) — "Olhem o vizinho: um trecho de ruído que imita uma
micro-ocultação recebe 0,0005. O anel real recebe 0,043 — **86 vezes mais**. A informação
está lá; o limiar padrão é que a esconde. τ = 0,03: as duas travessias do Q2R entram, e nem o ruído
nem o baseline cruzam a linha. Zero falsos alarmes. **Para revisitar curvas, o que importa
é a separação, não o valor absoluto.**"

**31. Janelas diluem** — "Testei a explicação alternativa — 'a janela era curta demais' —
e ela é falsa: ampliar a janela piora. Features globais diluem quedas curtas. Isso define
o próximo passo natural: janela deslizante com features locais."

## G. Fechamento (⏱ 39–42 min)

**32. Dificuldades** — Uma frase por par problema→solução. Terminar em: "a maior
fragilidade — 3 negativas reais nativas — está dita na tese com todas as letras."

**33. Conclusões** — "Três números para levar: F1 0,98–0,99 estável; sensibilidade de 99,4%
via τ, sem retreino; 86× de separação em dado externo. Uma ferramenta reproduzível de
triagem — pronta para reprocessar arquivos."

**34. Futuros** — "Janela deslizante e features locais; mais negativas reais; CNNs sobre a
série bruta; acoplamento às campanhas do grupo."

**35. Obrigado** — Agradecer nominalmente: orientador, Grupo do Rio, Braga-Ribas &
Gomes-Ferrante (simulador), Pereira (dados de Quaoar), banca, família. "Estou à disposição."

---

## Perguntas prováveis da banca (e a espinha da resposta)

1. **"Com 702 negativas sintéticas, o modelo não aprendeu o simulador?"**
   → Exp. 3: teste só com curvas reais, F1 0,982. E os recortes negativos são dados reais.
   Limitação reconhecida: negativas reais *difíceis* ainda são poucas (3 nativas).

2. **"Por que não uma CNN direto na curva (ODNet)?"**
   → Interpretabilidade (importância de features), volume moderado de dados, custo. CNN é
   trabalho futuro declarado; a pipeline atual é o baseline forte e auditável.

3. **"Esse F1 de 0,99 não é fácil demais? Um limiar simples não faria o mesmo?"**
   → (backup 37) Análise complementar: limiar numa única feature dá F1 0,90/0,95; o ML
   corta o erro restante ~10×. A física carrega muito — e o ML paga o próprio custo.

4. **"O τ=0,03 não é ajuste a posteriori para Quaoar?"**
   → O mecanismo (curva precisão-sensibilidade vs τ) está na tese antes do caso; 0,03 é o
   valor calibrado por campanha, validado também no conjunto de teste (recall 99,4%,
   +5 alarmes falsos em 179 negativas). Regra honesta: calibrar τ por campanha.

5. **"Os rótulos dos catálogos são confiáveis?"**
   → Ground truth = curadoria VizieR + análises publicadas do Grupo do Rio; sem reanálise
   independente — ressalva explícita na tese. Teste cego de Umbriel (backup 38): a única
   divergência era uma curva de rótulo discutível.

6. **"Por que 4 modelos se são equivalentes (McNemar)?"**
   → Robustez da conclusão: se famílias diferentes concordam, o sinal está nos dados, não
   no algoritmo. Operacionalmente recomendo XGBoost (probabilidades mais polarizadas).

7. **"Como isso entra numa campanha real?"**
   → Curvas pós-fotometria → banco → inferência em segundos por curva; modo triagem
   (τ baixo) prioriza o que o analista olha primeiro. Script de inferência pronto
   (`run_models.py`).

## Regras de ensaio

- 3 passadas completas: (1) lendo o roteiro, (2) só com os slides, (3) cronometrada
  com alguém assistindo.
- Se em 30 min você não chegou ao slide 21 (tabela), acione as válvulas: encurte o 7,
  pule o 25.
- Nunca ler o slide: o texto na tela é âncora do público, não seu.
- Água antes do slide 21 e do 30 (os dois de ~2 min).
