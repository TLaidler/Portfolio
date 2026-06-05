# Exercícios — Lista de preparação (Luiza)

> Apenas os enunciados. Gabaritos em `Aulas_Luiza.md`.

---

## Lista 1 — Conceituais

**2.** Por que George Box diz que todos os modelos estão errados?

**6.** Qual a diferença entre parâmetro, estimador e estimativa? Dê um exemplo de estimador.

**10.** Qual a diferença entre estimação intervalar e estimação pontual?

**11.** O que a convergência em probabilidade e a convergência quase-certa possuem em comum, mas a convergência em distribuição difere?

**12.** Quanto à convergência em probabilidade, o que ocorre à medida que $n$ cresce na sequência $(X_n)$ de variáveis aleatórias? O mesmo vale para a convergência em distribuição? Justifique.

**13.** Qual a relação entre a lei fraca dos grandes números e a convergência em probabilidade?

**14.** Qual a relação entre a lei forte dos grandes números e a convergência quase-certa?

**15.** Qual a relação entre o teorema do limite central e convergência em distribuição?

**16.** Descreva a relação entre erro, viés e erro quadrado médio.

**17.** Ilustre um estimador não-viesado e um estimador viesado.

---

## Lista 2 — Práticas

**1.** Considere uma amostra aleatória de $n$ variáveis $x_1, x_2, \ldots, x_n$, normalmente distribuídas com média $\mu$ e variância $\sigma^2$. Sejam $\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i$ e $\hat{\sigma}^2 = \frac{1}{n}\sum_{i=1}^{n}(x_i - \bar{x})^2$. Julgue verdadeiro ou falso:
- (a) $\bar{x}$ e $\hat{\sigma}^2$ são não viesados.
- (b) $\bar{x}$ e $\hat{\sigma}^2$ são consistentes.
- (c) Apenas $\bar{x}$ é consistente.
- (d) Apenas $\bar{x}$ é não viesado.

**8.** Qual/Quais dos seguintes itens é classificado como variável aleatória?
- (a) A média da população;
- (b) O tamanho da população, $N$;
- (c) O tamanho da amostra, $n$;
- (d) A média da amostra;
- (e) A variância da média da amostra;
- (f) O maior valor na amostra;
- (g) A variância da população;
- (h) A variância estimada da média da amostra.

**9.** Julgue as seguintes afirmativas:
- (a) Estimativas da média populacional que usam amostras obtidas por amostragem estratificada possuem variância menor do que aquelas obtidas por amostragem simples.
- (b) Se as variâncias de duas alocações são iguais, as estimativas da variância populacional não dependem do método de alocação.
- (c) A média de uma amostra estratificada é viesada.
- (d) Para ter uma estimativa mais precisa, deve-se aumentar o tamanho da amostra.
- (e) Com amostragem aleatória simples, $E(\bar{X}) = \mu$.

**10.** Julgue verdadeiro ou falso:
- (a) Comparando a alocação de peso ótima e a alocação proporcional, quanto mais variância há entre as variâncias, melhor o método de alocação de Neyman. Além disso, se as variâncias são iguais, as estimativas da variância populacional são necessariamente iguais.
- (b) No método de alocação de Neyman, é preciso saber as variâncias individuais de cada partição da população, sem exceção.
- (c) A amostragem com alocação de peso proporcional sempre fornece uma estimativa da média com menor variância do que com amostragem simples.
- (d) Quanto menos dispersa for a média entre as partições da população, melhor será a estimativa usando pesos proporcionais.

---

## Lista 3 — Práticas

**1.** Suponha que um objeto seja mensurado independentemente com dois diferentes dispositivos de mensuração. Sejam $L_1$ e $L_2$ os comprimentos medidos pelo primeiro e segundo dispositivos, respectivamente. Se ambos os dispositivos estiverem calibrados corretamente, poderemos admitir que $E(L_1) = E(L_2) = L$, o comprimento verdadeiro. No entanto, a precisão dos dispositivos não é necessariamente a mesma — avaliando a precisão em termos da variância, $V(L_1) \neq V(L_2)$. Se empregarmos a combinação linear $Z = aL_1 + (1-a)L_2$ para nossa estimativa de $L$, teremos imediatamente que $E(Z) = L$, isto é, $Z$ será uma estimativa não-tendenciosa de $L$. Para qual valor escolhido de $a$, $0 < a < 1$, a variância de $Z$ será mínima?

**4.** Seja uma amostra aleatória simples $X_1, \ldots, X_n$ extraída de uma variável aleatória $X$, com expectância $\mu$ e variância $\sigma^2$. Façamos $S^2 = \frac{1}{n-1}\sum_{i=1}^{n}(X_i - \bar{X})^2$, onde $\bar{X}$ é a média amostral. Mostre que $E(S^2) = \sigma^2$.

**5.** Os dados da tabela abaixo relacionam a solubilidade do nitrato de sódio (NaNO₃) com a temperatura da água (°C). Na temperatura indicada, as $Y$ partes de NaNO₃ se dissolvem em 100 partes de água. Empregando o método dos mínimos quadrados, estime os coeficientes linear e angular, $\beta_0$ e $\beta_1$.

| $T$ (°C) | 0 | 4 | 10 | 15 | 21 | 29 | 36 | 51 | 68 |
|---|---|---|---|---|---|---|---|---|---|
| $Y$ | 66,7 | 71 | 76,3 | 80,6 | 85,7 | 92,9 | 99,4 | 113,6 | 125,1 |

---

## Lista 4 — Intervalos de confiança

**1.** Dez mensurações são feitas para a resistência de um certo tipo de fio, fornecendo os valores $X_1, \ldots, X_{10}$. Suponhamos que $\bar{X} = 10{,}48$ ohms e $\hat{\sigma} = \sqrt{\frac{1}{9}\sum_{i=1}^{10}(X_i - \bar{X})^2} = 1{,}36$ ohms. Suponhamos que $X$ tenha distribuição $N(\mu, \sigma^2)$ e que desejemos obter um intervalo de confiança para $\mu$, com coeficiente de confiança $0{,}90$. Qual o intervalo de confiança?

**2.** Suponha que $X$ tenha distribuição $N(\mu, \sigma^2)$. Uma amostra de tamanho 30, digamos $X_1, \ldots, X_{30}$, fornece os seguintes valores: $\sum_{i=1}^{30} X_i = 700{,}8$ e $\sum_{i=1}^{30} X_i^2 = 16395{,}8$. Determine um intervalo de confiança de $95\%$ (bilateral) para $\mu$.

---

## Lista 5 — Teste de hipóteses

**1.** Considere uma amostra $\{X_i\}_{i=1}^{n}$ retirada de uma população normalmente distribuída. Assuma que a variância é conhecida e igual a 400, e que o tamanho da amostra seja 25. Queremos testar a hipótese de que a média é igual a 100 ($H_0$) contra a hipótese de que a média é igual a 105 ($H_1$). Para distinguir entre as duas distribuições usaremos a média amostral, lembrando que $\bar{X} \sim N\!\left(\mu, \frac{\sigma^2}{n}\right)$.

- (a) Para um valor crítico arbitrário $t = 103{,}36$, calcule a probabilidade do **erro tipo I**.
- (b) Para o mesmo valor crítico, calcule a probabilidade do **erro tipo II**.
- (c) Qual é o valor crítico $t$ para que a probabilidade do erro tipo I seja igual a $5\%$ (nível de significância $\alpha = 0{,}05$ escolhido *a priori*)? Enuncie a regra de decisão.
