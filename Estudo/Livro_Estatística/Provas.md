# Provas — *Síntese Estatística*

Três provas baseadas no material **Síntese Estatística** (T. L. V. Cunha). Cada prova vale 10 pontos e tem duração estimada de 2 horas. As questões cobrem progressivamente os capítulos do material.

- **P1** — Estatística descritiva, probabilidade básica e Bayes (Caps. 1–3)
- **P2** — Distribuições, TCL e fundamentos de inferência (Cap. 4)
- **P3** — Correlação, regressão, χ², Monte Carlo e Verossimilhança (Caps. 5–6 + tópicos selecionados)

---

## P1 — Estatística descritiva, probabilidade básica e Bayes

### Q1. Média, mediana e sensibilidade a outliers *(2,0 pts)*

Uma turma de 11 alunos teve as seguintes notas em uma prova:

`4, 5, 5, 6, 6, 6, 7, 7, 8, 9, 10`

(a) Calcule média, mediana e moda.
(b) Suponha agora que um 12º aluno seja adicionado à amostra com nota 0. Como cada uma das três estatísticas muda?
(c) Se você precisasse reportar uma única estatística para descrever o "desempenho típico" da turma, qual escolheria nos dois cenários e por quê?

---

### Q2. Precisão vs acurácia *(1,5 pts)*

Dois termômetros foram testados em uma sala mantida a 20°C real:

- **Termômetro A**: leituras consecutivas de 22,1; 22,0; 21,9; 22,1; 22,0.
- **Termômetro B**: leituras consecutivas de 17; 23; 19; 24; 17.

Classifique cada termômetro em "preciso", "acurado", ambos ou nenhum. Justifique. Em seguida: se você só pode levar um deles para uma expedição, qual escolhe e por quê?

---

### Q3. Contagem e probabilidade *(2,0 pts)*

Uma turma de 30 alunos vai sortear 4 representantes (sem distinção de função).

(a) De quantas formas distintas o grupo de 4 pode ser formado?
(b) Se um aluno específico (Maria) precisa estar no grupo, de quantas formas o resto pode ser escolhido?
(c) Qual a probabilidade de Maria ser uma das sorteadas, no sorteio puramente aleatório?
(d) Qual a probabilidade de **nenhum** dos 4 representantes ser do mesmo grupo de amigos de Maria, sabendo que esse grupo tem 6 alunos (incluindo ela)?

---

### Q4. Bayes — diagnóstico de doença *(2,5 pts)*

Em uma população, 1% das mulheres acima de 40 anos têm câncer de mama. Um exame de mamografia:

- Detecta corretamente o câncer em **90% das mulheres que o têm** (sensibilidade).
- Dá positivo em **8% das mulheres que não o têm** (falso positivo).

Uma mulher selecionada aleatoriamente nessa população fez o exame e o resultado foi **positivo**.

(a) Qual a probabilidade dela realmente ter câncer?
(b) Explique em linguagem cotidiana por que a resposta é tão baixa, apesar do teste ser "90% sensível".
(c) Se a sensibilidade do teste subisse para 99% (mantendo o falso positivo em 8%), a probabilidade *a posteriori* mudaria muito? E se fosse o falso positivo que caísse de 8% para 1%? Qual das duas melhorias tem mais impacto?

---

### Q5. Independência e a falácia do apostador *(2,0 pts)*

(a) Você joga 3 dados honestos simultaneamente. Qual a probabilidade de tirar 3 seis?
(b) Numa roleta americana (18 vermelhos, 18 pretos, 2 verdes), a bolinha caiu no vermelho 5 vezes seguidas. Seu amigo diz: "*Aposte no preto agora, está na hora dele aparecer*". Avalie criticamente o argumento.
(c) Em contraste, suponha que um motor de avião tenha probabilidade $10^{-5}$ de falhar por voo. A companhia coloca dois motores independentes. O risco virou $10^{-10}$? Justifique.

---

## P2 — Distribuições, TCL e fundamentos de inferência

### Q1. Bernoulli e Binomial *(2,0 pts)*

Uma linha de produção rejeita peças com probabilidade $p = 0{,}05$ por defeito, de forma independente entre peças.

(a) Modele a inspeção de **uma única peça** como Bernoulli. Calcule $E[X]$, $\text{Var}(X)$ e $DP(X)$.
(b) Em um lote de **100 peças**, qual a distribuição do número de peças rejeitadas? Forneça média e variância.
(c) Qual a probabilidade de que **exatamente zero** peças sejam rejeitadas no lote? E **no máximo 2**?

---

### Q2. Poisson e overdispersion *(2,5 pts)*

Em um call center, recebe-se em média 3 chamadas por minuto.

(a) Liste os três ingredientes necessários para que o número de chamadas por minuto seja modelado por Poisson e avalie criticamente se cada um vale (de fato) para um call center real.
(b) Sob a hipótese de Poisson, qual a probabilidade de receber exatamente 5 chamadas em um minuto? E de receber **mais que 5**?
(c) Em uma medição real, observou-se que a variância empírica do número de chamadas por minuto foi 7,5, embora a média fosse 3. O que isso indica sobre o uso da Poisson? Que tipo de modelo seria mais apropriado?

---

### Q3. Teorema Central do Limite *(2,0 pts)*

O tempo de espera num caixa de banco segue uma distribuição **exponencial** (assimétrica, não-Normal) com média $\mu = 4$ min e desvio padrão $\sigma = 4$ min.

(a) Pelo TCL, qual é a distribuição **aproximada** da média amostral $\bar X$ se você amostrar 100 clientes? Forneça média e desvio padrão dessa distribuição.
(b) Qual a probabilidade aproximada de que essa média amostral seja **maior que 5 minutos**?
(c) O TCL valeria se a distribuição de espera fosse **Cauchy**? Justifique tecnicamente (não basta dizer "porque é Cauchy").

---

### Q4. Interpretação do p-valor *(2,0 pts)*

Em um teste $H_0: \mu = 50$ vs. $H_1: \mu \neq 50$, obteve-se um p-valor de **0,03**. Classifique cada afirmação abaixo como **correta** ou **incorreta**, justificando em uma frase:

(a) "Há 3% de probabilidade de $H_0$ ser verdadeira."
(b) "Há 97% de chance de que $H_1$ esteja correta."
(c) "Se $H_0$ for verdadeira, a probabilidade de observarmos um resultado tão extremo (ou mais extremo) é de 3%."
(d) "Como $p < 0{,}05$, rejeitamos $H_0$ ao nível $\alpha = 5\%$."
(e) "O efeito detectado é importante e relevante para a prática."

---

### Q5. Intervalo de Confiança *(1,5 pts)*

Uma amostra de $n = 36$ medições, de uma variável Normal com $\sigma = 12$ conhecido, deu $\bar X = 100$.

(a) Construa o intervalo de confiança de 95% para a média populacional $\mu$.
(b) Um colega afirma: "*há 95% de chance de que $\mu$ esteja nesse intervalo*". A afirmação está correta? Reformule-a se necessário.
(c) Se a amostra aumentasse para $n = 144$ (mantendo $\bar X = 100$ e $\sigma = 12$), como o IC mudaria? Qual o trade-off prático envolvido em escolher amostras maiores?

---

## P3 — Correlação, regressão, χ², Monte Carlo, MLE

### Q1. Independência vs correlação *(2,0 pts)*

Seja $X \sim \mathcal{N}(0, 1)$ e $Y = X^2$.

(a) Calcule $\text{Cov}(X, Y)$. (Dica: para qualquer distribuição simétrica em torno de zero, $E[X^3] = 0$.)
(b) Qual é a correlação de Pearson entre $X$ e $Y$?
(c) $X$ e $Y$ são independentes? Justifique com cuidado — distinga "correlação zero" de "independência".
(d) Que lição prática um analista deve tirar disso ao calcular o coeficiente de Pearson em dados reais?

---

### Q2. Regressão MQO *(2,0 pts)*

Os seguintes dados foram coletados:

| $x_i$ | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| $y_i$ | 3 | 5 | 7 | 9 | 11 |

(a) Ajuste uma reta $y = ax + b$ por mínimos quadrados ordinários. Mostre as contas de $a$ e $b$.
(b) Calcule a soma dos quadrados dos resíduos $S(\hat\theta)$. Comente o valor obtido.
(c) Por que MQO minimiza a soma dos resíduos **ao quadrado** e não a soma em **valor absoluto**? Cite duas razões — uma matemática, uma estatística.
(d) Liste **dois** pressupostos de Gauss-Markov e explique, em uma frase cada, o que aconteceria com a inferência se cada um fosse violado.

---

### Q3. Qui-quadrado *(2,0 pts)*

Um dado de 6 faces é jogado 120 vezes, com os seguintes resultados:

| Face | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Frequência observada | 15 | 22 | 18 | 20 | 19 | 26 |

(a) Sob a hipótese $H_0$ de que o dado é honesto, qual é a frequência esperada de cada face?
(b) Calcule a estatística $\chi^2$ para esses dados.
(c) Sabendo que o valor crítico para $\alpha = 5\%$ e 5 graus de liberdade é $11{,}07$, qual a sua conclusão? **Cuidado:** redija a conclusão evitando linguagens como "*95% de certeza*" ou "*provamos que H₀ é verdade*".
(d) Suponha que, em vez de 120 jogadas, fossem 12.000 (mantendo as proporções: 1.500, 2.200, 1.800, 2.000, 1.900, 2.600). Refaça o cálculo de $\chi^2$. O que muda na conclusão? Comente sobre poder do teste.

---

### Q4. Verossimilhança e MLE *(2,0 pts)*

Uma moeda foi jogada 8 vezes e deu **6 caras**.

(a) Escreva a função de verossimilhança $L(p \mid \text{dados})$, onde $p$ é a probabilidade de cara.
(b) Encontre o valor de $p$ que maximiza a verossimilhança (MLE). Use cálculo (dica: trabalhe com o **log** da verossimilhança).
(c) Avalie $L(0{,}5)$ e $L(0{,}75)$. Quão mais plausível é $p = 0{,}75$ vs $p = 0{,}5$, dado o que vimos?
(d) A verossimilhança é uma probabilidade? Em particular, $\int_0^1 L(p) \, dp = 1$? Por que sim ou por que não?

---

### Q5. Monte Carlo *(2,0 pts)*

Você quer estimar numericamente a integral

$$I = \int_0^1 e^{-x^2}\, dx$$

(que não tem antiderivada elementar) via Monte Carlo.

(a) Descreva, em pseudocódigo ou em prosa estruturada, um procedimento de Monte Carlo para estimar $I$.
(b) Como o erro da sua estimativa decai em função do número de amostras $N$? (Forneça a ordem de grandeza, não precisa demonstrar.)
(c) Em qual cenário Monte Carlo se torna **especialmente** vantajoso em relação a métodos determinísticos (Simpson, trapezoidal)? Justifique.
(d) Conecte: por que esse mesmo arcabouço se aplica diretamente ao cálculo de Value-at-Risk em finanças? Que papel a matriz de Cholesky desempenha nesse caso?

---

*Boa prova.*
