# Gabaritos comentados — *Síntese Estatística*

Soluções detalhadas para as três provas. Onde possível, indico **o que** se busca testar com a questão, **o que** o aluno deve mostrar para receber a pontuação total, e armadilhas pedagógicas comuns.

---

## Gabarito — P1

### Q1. Média, mediana e moda *(2,0 pts)*

**Dados ordenados:** `4, 5, 5, 6, 6, 6, 7, 7, 8, 9, 10` (n = 11).

**(a)**
- Soma = $4+5+5+6+6+6+7+7+8+9+10 = 73$
- **Média** $= 73/11 \approx 6{,}64$
- **Mediana** = elemento na posição $\lceil 11/2 \rceil = 6$ = **6**
- **Moda** = 6 (aparece 3 vezes)

**(b)** Adicionando 0, $n = 12$:
- Nova soma = 73. **Média** $= 73/12 \approx 6{,}08$ (caiu $\approx 0{,}56$)
- Lista reordenada: `0, 4, 5, 5, 6, 6, 6, 7, 7, 8, 9, 10`. **Mediana** = $(6+6)/2 = $ **6** (inalterada)
- **Moda** = 6 (inalterada)

**(c)** No cenário original, todas as três estatísticas dão valores próximos (~6,5–7). No cenário com o outlier, a **média** absorveu o impacto desproporcionalmente. Recomenda-se reportar a **mediana** quando há outliers, ou ambas (média e mediana) explicitamente — a divergência entre elas é informação útil sobre assimetria/outliers.

> **O que se testa:** sensibilidade da média a outliers e robustez da mediana. Aluno que apenas calcule (a) sem responder (c) corretamente perde pontos.

---

### Q2. Precisão vs acurácia *(1,5 pts)*

- **Termômetro A**: leituras ~22°C, real = 20°C. Viés sistemático de +2°C. Variabilidade baixa (~0,1°C). $\Rightarrow$ **Preciso, mas não acurado.**
- **Termômetro B**: leituras 17, 23, 19, 24, 17. Média = $(17+23+19+24+17)/5 = 20$°C (acertando o valor real). Variabilidade alta (~3°C). $\Rightarrow$ **Acurado em média, mas não preciso.**

**Para a expedição:** depende do uso. Se for possível tomar várias leituras e calcular a média, **B** converge para o valor real (pelo TCL!). **A** sistematicamente erra por 2°C — a menos que o viés seja conhecido e corrigido, qualquer número de leituras dá o mesmo resultado errado. Em geral, prefere-se um instrumento corrigível por calibração (A) ou um cuja média seja correta (B) — desde que seja possível repetir as medições.

> **O que se testa:** distinção conceitual entre viés (acurácia) e variabilidade (precisão), e capacidade de aplicar essa distinção a uma decisão prática.

---

### Q3. Contagem e probabilidade *(2,0 pts)*

**(a)** $C(30, 4) = \dfrac{30!}{4!\,26!} = \dfrac{30 \cdot 29 \cdot 28 \cdot 27}{24} = \dfrac{657\,720}{24} = \mathbf{27\,405}$

**(b)** Fixando Maria, escolher 3 entre os 29 restantes: $C(29, 3) = \dfrac{29 \cdot 28 \cdot 27}{6} = \mathbf{3\,654}$

**(c)** $P(\text{Maria sorteada}) = \dfrac{C(29,3)}{C(30,4)} = \dfrac{3654}{27405} = \dfrac{4}{30} \approx \mathbf{13{,}3\%}$

> *Atalho:* há 4 vagas distribuídas uniformemente entre 30 alunos $\Rightarrow$ $4/30$ para cada um. Essa é a chave conceitual.

**(d)** "Nenhum do grupo de Maria entre os 4" = escolher os 4 entre os 24 alunos de fora do grupo:
$$P = \dfrac{C(24,4)}{C(30,4)} = \dfrac{10\,626}{27\,405} \approx \mathbf{38{,}8\%}$$

---

### Q4. Bayes — diagnóstico *(2,5 pts)*

**Dados:**
- $P(C) = 0{,}01$, $P(\overline{C}) = 0{,}99$
- $P(+ \mid C) = 0{,}90$ (sensibilidade)
- $P(+ \mid \overline{C}) = 0{,}08$ (falso positivo)

**(a)** Pelo Teorema de Bayes:
$$P(+) = P(+|C)P(C) + P(+|\overline{C})P(\overline{C}) = 0{,}9 \cdot 0{,}01 + 0{,}08 \cdot 0{,}99 = 0{,}009 + 0{,}0792 = 0{,}0882$$

$$P(C \mid +) = \dfrac{P(+|C) P(C)}{P(+)} = \dfrac{0{,}009}{0{,}0882} \approx \mathbf{10{,}2\%}$$

**(b)** A doença é **rara** (1%): em uma população de 10.000 mulheres, apenas 100 têm câncer (das quais ~90 positivam) e 9.900 não têm (das quais 8%, ou ~792, também positivam!). Os 792 falsos positivos dominam os 90 verdadeiros positivos. Por isso, mesmo um teste "muito sensível" produz mais ruído do que sinal quando a prevalência é baixa.

**(c)** **Cenário 1: sensibilidade $\uparrow$ para 99%, FP mantido em 8%:**
$$P(C \mid +) = \dfrac{0{,}99 \cdot 0{,}01}{0{,}99 \cdot 0{,}01 + 0{,}08 \cdot 0{,}99} = \dfrac{0{,}0099}{0{,}0891} \approx 11{,}1\%$$

Mudança pequena (+0,9 pp).

**Cenário 2: sensibilidade mantida em 90%, FP $\downarrow$ para 1%:**
$$P(C \mid +) = \dfrac{0{,}9 \cdot 0{,}01}{0{,}9 \cdot 0{,}01 + 0{,}01 \cdot 0{,}99} = \dfrac{0{,}009}{0{,}0189} \approx 47{,}6\%$$

Mudança enorme (+37 pp).

> **Conclusão:** reduzir falsos positivos tem impacto desproporcionalmente maior do que aumentar sensibilidade, pois a base de negativos domina quando a doença é rara. Essa é uma lição central em rastreamento populacional (e em sistemas de detecção em geral — incluindo fraude e churn).

---

### Q5. Independência e falácia do apostador *(2,0 pts)*

**(a)** Eventos independentes, regra do produto:
$$P(\text{3 seis}) = \left(\dfrac{1}{6}\right)^3 = \dfrac{1}{216} \approx \mathbf{0{,}46\%}$$

**(b)** O argumento é a **falácia do apostador**. Cada giro da roleta é independente — a bolinha não tem memória das 5 jogadas anteriores. $P(\text{preto}) = 18/38 \approx 47{,}4\%$ continua o mesmo na 6ª jogada. *Pior ainda:* se houver alguma assimetria física na roleta que produziu vermelho 5 vezes, o cenário mais provável é que ela esteja viesada *para o vermelho*, não que esteja "compensando" agora.

**(c)** **Não.** O cálculo $10^{-10}$ supõe independência entre as falhas dos dois motores. Em aviões, falhas frequentemente compartilham causa-raiz: aves no caminho (que entram simultaneamente em ambos os motores), contaminação do combustível, fadiga estrutural correlacionada, falhas de manutenção sistêmicas. Dado que um motor falhou por uma dessas causas, o segundo tem probabilidade muito maior que $10^{-5}$. A redundância vale, mas o ganho real é menor que o produto sugere.

> **O que se testa:** o aluno reconhece quando **assumir independência é erro** (avião) e quando **negar independência é erro** (gambler's fallacy). São os dois lados da mesma moeda conceitual.

---

## Gabarito — P2

### Q1. Bernoulli e Binomial *(2,0 pts)*

**(a)** Bernoulli com $p = 0{,}05$:
- $E[X] = p = \mathbf{0{,}05}$
- $\text{Var}(X) = p(1-p) = 0{,}05 \cdot 0{,}95 = \mathbf{0{,}0475}$
- $DP(X) = \sqrt{0{,}0475} \approx \mathbf{0{,}218}$

**(b)** $X \sim \text{Binomial}(100, 0{,}05)$. Média $= np = \mathbf{5}$; variância $= np(1-p) = \mathbf{4{,}75}$.

**(c)**
- $P(X = 0) = (0{,}95)^{100} \approx \mathbf{0{,}592\%}$
- $P(X \leq 2) = \binom{100}{0}(0{,}05)^0(0{,}95)^{100} + \binom{100}{1}(0{,}05)^1(0{,}95)^{99} + \binom{100}{2}(0{,}05)^2(0{,}95)^{98}$

$$\approx 0{,}00592 + 0{,}0312 + 0{,}0812 \approx \mathbf{11{,}8\%}$$

> *Atalho aceitável:* aproximar pela Poisson com $\lambda = np = 5$: $P(X=0) = e^{-5} \approx 0{,}0067$, $P(X \leq 2) = e^{-5}(1 + 5 + 12{,}5) \approx 12{,}5\%$. Ambas as aproximações são válidas; o aluno deve justificar a escolha.

---

### Q2. Poisson e overdispersion *(2,5 pts)*

**(a) Os três ingredientes:**
1. **Discretos** ✓ — chamadas são unidades inteiras.
2. **Independência** — **dúbio**. Ligações são geralmente independentes entre clientes, mas eventos disparadores (apagão regional, problema em um produto viral) geram correlação súbita.
3. **Taxa constante** — **provavelmente falso em escala diária**. Volume varia por hora do dia, dia da semana, sazonalidade. Para janelas curtas e fora de horários de pico, é razoável.

Conclusão: Poisson é uma **aproximação útil** num intervalo localizado, não uma descrição literal exata.

**(b)** Com $\lambda = 3$:
$$P(X = 5) = \dfrac{3^5 \cdot e^{-3}}{5!} = \dfrac{243 \cdot 0{,}0498}{120} \approx \mathbf{10{,}1\%}$$

Para $P(X > 5)$, calculamos $P(X \leq 5)$ primeiro:
$$P(X \leq 5) = e^{-3}\left(1 + 3 + \dfrac{9}{2} + \dfrac{27}{6} + \dfrac{81}{24} + \dfrac{243}{120}\right) \approx 0{,}916$$

Logo, $P(X > 5) \approx 1 - 0{,}916 = \mathbf{8{,}4\%}$.

**(c)** Variância (7,5) >> Média (3): **overdispersion**. Indica que pelo menos uma das hipóteses de Poisson é violada (provavelmente independência — talvez existam *bursts* de chamadas correlacionadas). Modelo apropriado: **binomial negativa**, que permite $\text{Var} > \text{Média}$ ao adicionar um parâmetro de dispersão extra. Em finanças/seguros, modelos compostos (Poisson misturada com Gamma) são alternativas.

---

### Q3. Teorema Central do Limite *(2,0 pts)*

**(a)** Pelo TCL, para $n = 100$:
$$\bar X \sim \mathcal{N}\left(\mu, \dfrac{\sigma^2}{n}\right) = \mathcal{N}\left(4, \dfrac{16}{100}\right) = \mathcal{N}(4, 0{,}16)$$

Logo $DP(\bar X) = \sqrt{0{,}16} = \mathbf{0{,}4}$ minutos.

**(b)** Padronizando:
$$P(\bar X > 5) = P\!\left(Z > \dfrac{5 - 4}{0{,}4}\right) = P(Z > 2{,}5) \approx \mathbf{0{,}62\%}$$

> *Reflexão:* mesmo a distribuição original sendo exponencial (assimétrica), a média amostral é tratada como Normal — esse é o "milagre" do TCL.

**(c)** **Não vale.** A distribuição de Cauchy tem **variância infinita** (a integral $\int x^2 f(x) dx$ diverge). A hipótese de variância finita é **necessária** no enunciado do TCL clássico. Para Cauchy, a média amostral $\bar X_n$ tem a *mesma* distribuição de Cauchy da variável original — não converge para Normal por mais que $n$ cresça. Esse é um caso patológico que ilustra que o TCL não é "universal" — depende de condições que precisam ser verificadas.

---

### Q4. Interpretação do p-valor *(2,0 pts)*

| Afirmação | Veredito | Justificativa |
|---|---|---|
| (a) "Há 3% de prob. de $H_0$ ser verdadeira." | **Incorreta** | P-valor é $P(\text{dados}\mid H_0)$, não $P(H_0 \mid \text{dados})$. Para o segundo, precisaria prior bayesiano. |
| (b) "Há 97% de chance de $H_1$ estar correta." | **Incorreta** | Mesma confusão direcional. $1 - p$ não é a probabilidade da alternativa. |
| (c) "Se $H_0$ for verdadeira, prob. de observar resultado tão extremo é 3%." | **Correta** | Esta é a definição formal de p-valor. |
| (d) "Como $p < 0{,}05$, rejeitamos $H_0$ ao nível $\alpha = 5\%$." | **Correta** | Procedimento padrão de Neyman-Pearson. |
| (e) "O efeito detectado é importante e relevante para a prática." | **Incorreta** | P-valor mede compatibilidade estatística com $H_0$, não magnitude do efeito. Com amostra muito grande, efeitos triviais geram $p$ baixíssimo. **Significância estatística ≠ relevância prática.** |

> **O que se testa:** essa questão é o coração pedagógico da prova. Aluno que erra (a) e (b) precisa revisar todo o capítulo de testes de hipótese — é o erro mais comum em estatística aplicada e o que motivou a ASA Statement de 2016.

---

### Q5. Intervalo de Confiança *(1,5 pts)*

**(a)** $IC_{95\%}(\mu) = \bar X \pm 1{,}96 \cdot \dfrac{\sigma}{\sqrt{n}} = 100 \pm 1{,}96 \cdot \dfrac{12}{\sqrt{36}} = 100 \pm 1{,}96 \cdot 2 = 100 \pm 3{,}92$

$$\boxed{[96{,}08;\ 103{,}92]}$$

**(b) Incorreta.** O parâmetro $\mu$ é fixo (embora desconhecido); o intervalo é a quantidade aleatória. A interpretação **correta** é:

> "Se repetíssemos esse procedimento muitas vezes, **95% dos intervalos construídos dessa forma** conteriam o $\mu$ verdadeiro."

A interpretação errada ("95% de chance de $\mu$ estar aqui") só seria válida em estatística **bayesiana**, com prior explícito — e nesse caso o objeto se chamaria *intervalo de credibilidade*.

**(c)** Com $n = 144$:
$$IC = 100 \pm 1{,}96 \cdot \dfrac{12}{12} = 100 \pm 1{,}96 = [98{,}04;\ 101{,}96]$$

A largura caiu pela metade (porque o desvio padrão da média escala com $1/\sqrt{n}$, e $\sqrt{144}/\sqrt{36} = 2$).

**Trade-off:** amostras maiores são mais caras (tempo, dinheiro, recursos, fadiga dos respondentes). Cada bit adicional de precisão exige proporcionalmente mais dados — para metade da largura, 4× mais amostras. Decisão prática: até onde vale a pena pagar pelo refinamento.

---

## Gabarito — P3

### Q1. Independência vs correlação *(2,0 pts)*

**Dado:** $X \sim \mathcal{N}(0,1)$ e $Y = X^2$.

**(a)** $\text{Cov}(X, Y) = E[XY] - E[X]E[Y]$

- $E[XY] = E[X \cdot X^2] = E[X^3] = 0$ (terceiro momento de uma distribuição simétrica em torno de zero).
- $E[X] = 0$, $E[Y] = E[X^2] = \text{Var}(X) + (E[X])^2 = 1$.

Logo $\text{Cov}(X, Y) = 0 - 0 \cdot 1 = \mathbf{0}$.

**(b)** Como $\text{Cov}(X, Y) = 0$, a correlação de Pearson também é $\boldsymbol{0}$ (ela é a covariância normalizada pelos desvios padrão; numerador zero $\Rightarrow$ correlação zero).

**(c)** **Não são independentes.** $Y$ é uma função *determinística* de $X$ — se conhecemos $X$, sabemos $Y$ exatamente. Isso é o oposto extremo de independência. Equivalentemente: $f_{X,Y}(x, y) \neq f_X(x) \cdot f_Y(y)$ (a densidade conjunta concentra-se na curva $y = x^2$, não cobre o plano).

> Correlação de Pearson zero significa apenas que não há relação **linear**. Pode haver relação não-linear forte (parabólica, periódica etc.).

**(d) Lição prática:** **nunca conclua independência a partir de correlação zero**. Sempre olhe o **gráfico de dispersão** antes de tirar conclusões. Coeficientes como Spearman e Kendall capturam relações monotônicas (mais geral que linear), mas mesmo eles falham com relações simétricas. Ferramentas robustas para detectar dependência geral incluem testes de independência baseados em informação mútua ou *distance correlation*.

---

### Q2. Regressão MQO *(2,0 pts)*

**(a)** $\bar x = 3$, $\bar y = 7$.

$$\sum (x_i - \bar x)(y_i - \bar y) = (-2)(-4) + (-1)(-2) + (0)(0) + (1)(2) + (2)(4) = 8+2+0+2+8 = 20$$

$$\sum (x_i - \bar x)^2 = 4+1+0+1+4 = 10$$

$$\hat a = \dfrac{20}{10} = \mathbf{2}, \quad \hat b = \bar y - \hat a \bar x = 7 - 6 = \mathbf{1}$$

$$\boxed{\hat y = 2x + 1}$$

**(b)** Resíduos: $y_i - \hat y_i$ para $i = 1, \ldots, 5$:
- $\hat y$ previsto = $3, 5, 7, 9, 11$, idêntico aos valores observados.
- Todos os resíduos são **zero**. Logo $S(\hat\theta) = \mathbf{0}$.

> *Comentário:* ajuste perfeito. Em dados reais isso quase nunca acontece — há sempre ruído de medição, variabilidade não-modelada etc. Esse exercício didático mostra que MQO **recupera exatamente** a relação verdadeira quando ela existe e está livre de ruído.

**(c) Razões para usar quadrado em vez de valor absoluto:**

- **Matemática:** o quadrado é **diferenciável em zero**; valor absoluto não é. Isso permite resolver a otimização analiticamente (derivar, igualar a zero, encontrar fórmula fechada para $\hat\theta$). Com valor absoluto, a solução exige programação linear ou métodos iterativos.
- **Estatística:** sob a hipótese de erros Normais, **minimizar a soma dos quadrados é equivalente à máxima verossimilhança** (MLE). Adicionalmente, MQO é BLUE (*Best Linear Unbiased Estimator*) pelos teoremas de Gauss-Markov. Minimização em valor absoluto leva à *mediana condicional* (regressão quantílica) — útil, mas com propriedades diferentes.

**(d) Dois pressupostos de Gauss-Markov (qualquer dois dos abaixo):**

- **Linearidade**: se viola, ajuste linear é viesado por construção (estamos forçando uma reta em uma relação curva).
- **Exogeneidade** ($E[\epsilon \mid X] = 0$): se viola (variável omitida correlacionada com $X$, ou causalidade reversa), $\hat\theta$ é **viesado** — não converge para o valor verdadeiro mesmo com $n \to \infty$.
- **Homocedasticidade**: se viola (variância dos resíduos cresce com $X$), $\hat\theta$ continua **não-viesado**, mas seus **erros-padrão** ficam errados — então IC e p-valores são incorretos.
- **Independência dos resíduos**: se viola (autocorrelação em séries temporais), erros-padrão também ficam errados, e inferência falha.

---

### Q3. Qui-quadrado *(2,0 pts)*

**(a)** Sob $H_0$ (dado honesto): cada face com probabilidade $1/6$ em 120 jogadas $\Rightarrow$ frequência esperada $E_i = 120/6 = \mathbf{20}$ para todas as faces.

**(b)** $\chi^2 = \sum \dfrac{(O_i - E_i)^2}{E_i}$:

| Face | $O_i$ | $E_i$ | $(O_i - E_i)^2 / E_i$ |
|---|---|---|---|
| 1 | 15 | 20 | $25/20 = 1{,}25$ |
| 2 | 22 | 20 | $4/20 = 0{,}20$ |
| 3 | 18 | 20 | $4/20 = 0{,}20$ |
| 4 | 20 | 20 | $0$ |
| 5 | 19 | 20 | $1/20 = 0{,}05$ |
| 6 | 26 | 20 | $36/20 = 1{,}80$ |

$$\chi^2 = 1{,}25 + 0{,}20 + 0{,}20 + 0 + 0{,}05 + 1{,}80 = \mathbf{3{,}50}$$

**(c)** $\chi^2_{\text{obs}} = 3{,}50 < 11{,}07 = \chi^2_{\text{crítico}}$. **Falhamos em rejeitar $H_0$** ao nível $\alpha = 5\%$.

**Redação cuidadosa:** os dados são **compatíveis** com a hipótese de dado honesto. Não estamos *provando* que o dado é honesto — apenas que, com essas 120 jogadas, não conseguimos descartar essa hipótese. A face 6 saiu mais frequentemente (26 vs 20 esperado), mas o desvio não é grande o suficiente para ser atribuído a algo além do acaso.

**(d)** Com proporções mantidas em 12.000 jogadas, todas as frequências escalam por 10:

| Face | $O_i$ | $E_i$ | $(O_i - E_i)^2 / E_i$ |
|---|---|---|---|
| 1 | 1.500 | 2.000 | $250\,000/2000 = 125$ |
| 2 | 2.200 | 2.000 | $40\,000/2000 = 20$ |
| 3 | 1.800 | 2.000 | $40\,000/2000 = 20$ |
| 4 | 2.000 | 2.000 | $0$ |
| 5 | 1.900 | 2.000 | $10\,000/2000 = 5$ |
| 6 | 2.600 | 2.000 | $360\,000/2000 = 180$ |

$$\chi^2 = 125 + 20 + 20 + 0 + 5 + 180 = \mathbf{350}$$

(Note: exatamente 10× o anterior — não coincidência, segue da definição da estatística.)

Agora $\chi^2 = 350 \gg 11{,}07$. **Rejeitamos $H_0$.** Mesmas proporções, mas com amostra maior o **poder do teste** aumentou e conseguimos detectar o desvio.

> **Lição pedagógica:** "*falha em rejeitar*" depende do tamanho da amostra. Em 120 jogadas, o teste tinha poder baixo demais para detectar um dado ligeiramente viciado. Em 12.000, sim. **Ausência de evidência não é evidência de ausência** — pode ser ausência de poder estatístico.

---

### Q4. Verossimilhança e MLE *(2,0 pts)*

**(a)** $L(p \mid \text{6 caras em 8}) = \binom{8}{6} p^6 (1-p)^2 = 28\,p^6 (1-p)^2$

**(b)** Maximizar via log-verossimilhança (mais fácil de derivar):
$$\ell(p) = \log L(p) = \log 28 + 6 \log p + 2 \log(1-p)$$

$$\dfrac{d\ell}{dp} = \dfrac{6}{p} - \dfrac{2}{1-p} = 0$$

$$6(1-p) = 2p \implies 6 - 6p = 2p \implies 8p = 6 \implies \hat p_{MLE} = \dfrac{6}{8} = \mathbf{0{,}75}$$

> *Intuição:* o MLE é exatamente a proporção observada — o que faz todo sentido (é o estimador que "explica perfeitamente" o que observamos).

**(c)**
- $L(0{,}5) = 28 \cdot (0{,}5)^6 \cdot (0{,}5)^2 = 28 \cdot (0{,}5)^8 = 28 / 256 \approx \mathbf{0{,}1094}$
- $L(0{,}75) = 28 \cdot (0{,}75)^6 \cdot (0{,}25)^2 = 28 \cdot 0{,}1780 \cdot 0{,}0625 \approx \mathbf{0{,}3115}$

**Razão:** $0{,}3115 / 0{,}1094 \approx \mathbf{2{,}85}$.

Os dados são cerca de **2,85× mais compatíveis com $p = 0{,}75$ do que com $p = 0{,}5$**. Note que isso é uma razão de verossimilhança, **não** uma razão de probabilidades — ambos $0{,}1094$ e $0{,}3115$ são números sem interpretação probabilística absoluta.

**(d) Não é probabilidade.** A integral é:

$$\int_0^1 L(p)\, dp = 28 \int_0^1 p^6 (1-p)^2 \, dp = 28 \cdot B(7, 3) = 28 \cdot \dfrac{6!\,2!}{9!} = 28 \cdot \dfrac{1440}{362\,880} = \dfrac{28}{252} = \dfrac{1}{9} \approx 0{,}111$$

**Não dá 1.**

**Razão filosófica:** $L$ é função de $p$ (parâmetro), não de $x$ (dados). Probabilidades integram a 1 sobre o espaço de **eventos**; verossimilhança não tem essa propriedade sobre o espaço de **parâmetros**. Ela é uma medida de *compatibilidade relativa* — só faz sentido comparar valores entre si, não interpretá-los como probabilidades absolutas.

---

### Q5. Monte Carlo *(2,0 pts)*

**(a)** **Pseudocódigo:**

```
N = 1.000.000  // número de amostras
soma = 0
para i = 1 até N:
    x = uniforme(0, 1)        // sorteia x uniformemente em [0,1]
    soma = soma + exp(-x²)    // acumula f(x)
Î = soma / N                   // estimativa
```

**Justificativa:** $\int_0^1 f(x)\, dx = E_{X \sim U(0,1)}[f(X)]$. A esperança é estimada pela média amostral. Aqui $f(x) = e^{-x^2}$.

**(b)** Pelo TCL, o erro da média amostral decai como $\boldsymbol{O(1/\sqrt N)}$. Para reduzir o erro pela metade, precisa-se de **4× mais amostras** — convergência lenta. O ponto crucial é que essa taxa **não depende da dimensão** do problema.

**(c) Métodos determinísticos** (trapezoidal, Simpson, quadraturas) têm erro decaindo como $O(N^{-k/d})$ onde $d$ é a dimensão e $k$ depende do método. Isso é a **maldição da dimensionalidade**: em alta dimensão, métodos determinísticos exigem $N$ exponencial. Monte Carlo, com erro $1/\sqrt N$ **independente de $d$**, vence em integrais multidimensionais (typicamente $d > 4$ ou 5 já é território MC).

**(d) Em finanças:**
- **VaR** exige avaliar a distribuição de retornos de uma carteira com $K$ ativos em $T$ horizontes futuros — efetivamente uma integral em $K \times T$ dimensões. Para qualquer carteira realista, $K \times T$ é alto. MC é praticamente a única opção.
- **Matriz de Cholesky** ($\Sigma = L L^\top$): para gerar amostras correlacionadas obedecendo a uma matriz de covariância $\Sigma$, parte-se de vetor i.i.d. $Z \sim \mathcal{N}(0, I)$ e aplica-se a transformação $X = \mu + L Z$. O resultado tem $\text{Cov}(X) = L L^\top = \Sigma$. Sem Cholesky, sortearíamos retornos independentes — e isso ignoraria a estrutura de correlação entre ativos, que é exatamente o que determina o risco agregado da carteira.

---

## Critérios gerais de correção

- **Cálculos com pequenos erros aritméticos**: descontar parcial, mas valorizar o procedimento correto.
- **Confusão entre $P(A|B)$ e $P(B|A)$** (Bayes, p-valor): erro grave, pesa bastante.
- **"95% de certeza"**, **"95% de probabilidade de $\mu$ estar no IC"**: erro conceitual recorrente; deve ser penalizado mesmo se o cálculo numérico está correto.
- **Aluno que demonstra raciocínio crítico em questões conceituais** (P2 Q4, P3 Q1) deve ser pontuado generosamente — esse é o tipo de pensamento que o material quer cultivar.
