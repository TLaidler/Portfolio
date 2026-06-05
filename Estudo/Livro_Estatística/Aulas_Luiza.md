# Aulas Luiza — Preparação intensiva para a prova de Estatística

> **Formato:** 2 aulas de 30 min de conceitos + ~1 h de exercícios cada, totalizando ~2 h.
> **Filosofia (do material do Thiago):** tornar a estatística *intuitiva*. O professor cobra muito **V/F conceitual**, então a prioridade é entender o *porquê* de cada ideia, não decorar fórmula.
> **Legenda de cada exercício:**
> 🟢 **EXPLICAR EM AULA** (alto rendimento conceitual, vale o tempo)
> 🔵 **PASSAR DE TREINO** (gabarito abaixo, mecânico ou redundante — economiza tempo de aula)
>
> *As contas numéricas deste gabarito foram conferidas em Python (regressão, IC, teste de hipóteses).*

---

# 🎯 As 4 dualidades que organizam TUDO

Antes de qualquer aula, fixe na Luiza estas quatro tensões. Quase toda questão V/F do professor é uma delas disfarçada:

| Dualidade | Lado A | Lado B |
|---|---|---|
| **Acurácia × Precisão** | acerta o alvo (sem viés) | tiros agrupados (pouca variância) |
| **Parâmetro × Estimador** | verdade fixa da população (μ, σ²) | receita aleatória que chuta a verdade (X̄, S²) |
| **Probabilidade × Verossimilhança** | fixo o modelo, pergunto sobre os dados | fixo os dados, pergunto sobre o modelo |
| **Erro tipo I × tipo II** | rejeitar H0 verdadeira (α, falso +) | não rejeitar H0 falsa (β, falso −) |

> **Imagem-mãe (use o tempo todo):** o **alvo de dardos**. Viés = mira torta (sempre erra pro mesmo lado). Variância = mão trêmula (espalha os tiros). O erro total junta os dois: **EQM = Variância + Viés²**.

---

# 📘 AULA 1 — Fundamentos (30 min de conceito)

Ordem sugerida de explicação (cada bloco puxa o próximo):

### 1. Estatística descritiva: o meio e o espalhamento *(5 min)*
- **Média** = soma/N. Sensível a *outliers* (o amigo rico no bar infla a média do grupo).
- **Mediana** = ponto que divide a distribuição ao meio. *Não* é sensível a extremos.
  - Corte de imposto Bush: média >\$1000, mediana <\$100 → **a média engana**.
  - Remédio que cura 30%: mediana não move, mas a média sim → **a mediana engana**.
  - **Moral:** a escolha da medida do "meio" é onde mora a desonestidade estatística.
- **Variância** $\sigma^2 = \frac{1}{N}\sum (x_i-\bar x)^2$ → mede dispersão, mas na unidade *ao quadrado*.
- **Desvio padrão** $\sigma=\sqrt{\sigma^2}$ → dispersão na unidade original. (Avião vs. maratonistas: mesma média, dispersões diferentes.)

### 2. Precisão × Acurácia *(3 min — conceito-chave do professor)*
- **Precisão** = grau de exatidão/detalhe da medida ("siga 3,15 km a leste").
- **Acurácia** = consistência com a verdade (mas o posto era ao norte!).
- Precisão pode **mascarar** inacurácia (modelos de risco de 2008: precisos, premissas erradas).

### 3. Distribuição Normal *(2 min)*
- Simétrica, formato de sino, descrita 100% por **(μ, σ)**.
- Regra prática: ~68% em ±1σ, ~95% em ±2σ (mais exato, ±1,96σ).

### 4. Probabilidade × Verossimilhança *(5 min — pega muita gente)*
- **Probabilidade:** "a moeda é honesta (p=0,5); qual a chance de sair 7 caras?" → fixo o **modelo**, pergunto pelos **dados**.
- **Verossimilhança (likelihood):** "saíram 7 caras em 10; quão *plausível* é p=0,5? e p=0,7?" → fixo os **dados**, pergunto pelo **modelo**.
- A *likelihood* **não é probabilidade**: somada sobre todos os p, não dá 1.
- **MLE (máxima verossimilhança)** = achar o parâmetro que torna os dados observados o mais "esperáveis" possível.

### 5. Erro, Viés e EQM *(7 min — o coração da prova)*
- **Estimador** $\hat\theta$ = receita que pega a amostra e cospe um palpite. **É variável aleatória** (muda a amostra, muda o palpite).
- **Viés** = $E[\hat\theta]-\theta$ → erro *sistemático* (acurácia / mira torta). Não-viesado: $E[\hat\theta]=\theta$.
- **Variância** = quanto o palpite *balança* entre amostras (precisão / mão trêmula).
- **EQM** $= E[(\hat\theta-\theta)^2] = \text{Var}(\hat\theta) + [\text{Viés}(\hat\theta)]^2$.
- **Surpresa que humilha a intuição:** viés nem sempre é vilão. Às vezes vale aceitar um pouco de viés para cortar muita variância (é o *trade-off viés-variância*).
- **Por que n−1?** Dividir por $n$ subestima σ² (viesado), porque medimos desvios em torno de $\bar x$, que é o ponto que *minimiza* esses desvios. Corrigimos "gastando 1 grau de liberdade" → divide por $n-1$ (**correção de Bessel**).

### 6. Convergência: LGN, LFGN e TCL *(8 min — o professor adora)*
- **Lei dos Grandes Números (LGN):** a média de muitas observações se aproxima da média verdadeira. Motor quantitativo: $\text{Var}(\bar X_n)=\sigma^2/n \to 0$.
- **Erro padrão** $= \sigma/\sqrt{n}$: para reduzir o erro pela **metade**, precisa de **4×** mais dados (a tirania do √n).
- **Três modos de convergência** (do mais fraco ao mais forte):
  - **em distribuição** ($\xrightarrow{d}$): só o *formato* (a CDF) converge. Nada se afirma sobre valores individuais.
  - **em probabilidade** ($\xrightarrow{P}$): num instante distante escolhido *de antemão*, é quase certo estar perto do alvo (uma *foto*).
  - **quase certa** ($\xrightarrow{q.c.}$): a *trajetória inteira* assenta no alvo e não sai mais (o *filme*).
  - Hierarquia: $\xrightarrow{q.c.}\Rightarrow\xrightarrow{P}\Rightarrow\xrightarrow{d}$.
- **As três pontes (decore o pareamento!):**
  - Lei **Fraca** dos GN ⟷ convergência **em probabilidade**.
  - Lei **Forte** dos GN ⟷ convergência **quase certa**.
  - **TCL** ⟷ convergência **em distribuição**: $\sqrt{n}\,\frac{\bar X_n-\mu}{\sigma}\xrightarrow{d}\mathcal N(0,1)$, *qualquer que seja* a distribuição original (desde que **variância finita** — Cauchy não vale).

---

## 🧮 AULA 1 — Bateria de exercícios (gabarito)

### Bloco conceitual (Lista 1)

---

**🔵 Q2 — Por que George Box diz que "todos os modelos estão errados"?**

**Gabarito.** Porque todo modelo é uma *simplificação* da realidade: ele descarta informação de propósito para ser manejável e assume hipóteses (normalidade, independência, linearidade) que nunca valem perfeitamente. A frase completa é *"todos os modelos estão errados, mas alguns são úteis"* — o critério não é verdade, é **utilidade**. Liga-se direto ao material: *"qualquer simplificação convida ao abuso"* e aos modelos de risco de 2008 (precisos, mas com premissas erradas → catastróficos).

---

**🟢 Q6 — Diferença entre parâmetro, estimador e estimativa? Exemplo de estimador.**

**Gabarito.**
- **Parâmetro:** característica *fixa* (e geralmente desconhecida) da população. Ex.: μ, σ². **Não é aleatório.**
- **Estimador:** *regra/função* da amostra aleatória usada para chutar o parâmetro. **É variável aleatória** (muda com a amostra). Ex.: $\bar X=\frac1n\sum X_i$ é um estimador de μ.
- **Estimativa:** o *número concreto* que o estimador produz para uma amostra específica. Ex.: $\bar x = 10,48$ ohms.

> Frase de cofrinho: **estimador é a receita (aleatória); estimativa é o prato pronto (um número).**

---

**🟢 Q10 — Estimação intervalar × pontual?**

**Gabarito.**
- **Pontual:** entrega um único número como melhor palpite ($\bar x=10,48$). Não diz nada sobre a confiança.
- **Intervalar:** entrega uma *faixa* de valores plausíveis + um nível de confiança (ex.: IC 90%). Carrega a **precisão** da estimativa (largura) e embute o teste de hipóteses. *"Três coisas pelo preço de uma."*

---

**🟢 Q11 — O que convergência *em probabilidade* e *quase-certa* têm em comum, mas a *em distribuição* difere?**

**Gabarito.** As duas primeiras falam sobre os **valores** das variáveis se aproximarem de um alvo (existe um limite que as próprias $X_n$ perseguem). A convergência **em distribuição** fala só do **formato** (a CDF $F_n\to F$): a silhueta da distribuição converge, mas *nada* se garante sobre os valores individuais. Por isso ela é a mais fraca da hierarquia.

---

**🟢 Q12 — Em convergência *em probabilidade*, o que ocorre com $(X_n)$ quando n cresce? Vale o mesmo para *em distribuição*?**

**Gabarito.** Em probabilidade: à medida que $n$ cresce, $P(|X_n-\text{alvo}|>\varepsilon)\to 0$ — as variáveis se **concentram** em torno do alvo (cada vez mais difícil estar longe). Em distribuição: o que se aproxima é a **CDF** $F_n(x)\to F(x)$ nos pontos de continuidade — estabiliza-se o *formato*, não os valores. Justificativa: a convergência em distribuição é estritamente mais fraca; o TCL é o exemplo — a *distribuição* de $\bar X_n$ vira Normal, mas é a forma que converge, não os valores a um ponto.

---

**🟢 Q13 / Q14 / Q15 — As três pontes**

**Gabarito (decore como par):**
- **Q13.** A Lei **Fraca** dos Grandes Números *é* a afirmação de convergência **em probabilidade** da média amostral: $\bar X_n \xrightarrow{P}\mu$.
- **Q14.** A Lei **Forte** dos Grandes Números *é* a convergência **quase certa**: $P(\lim_n \bar X_n=\mu)=1$. Por isso é "mais forte" — implica a fraca, não o contrário.
- **Q15.** O **TCL** *é* uma afirmação de convergência **em distribuição**: a média amostral padronizada $\to \mathcal N(0,1)$. É sobre o *formato* da distribuição de $\bar X_n$ virar Normal.

---

**🟢 Q16 — Relação entre erro, viés e erro quadrático médio.**

**Gabarito.**
$$\text{EQM}(\hat\theta)=E[(\hat\theta-\theta)^2]=\underbrace{\text{Var}(\hat\theta)}_{\text{tremor / precisão}}+\underbrace{[\text{Viés}(\hat\theta)]^2}_{\text{mira torta / acurácia}}$$
O erro total se decompõe em **variância** (espalhamento) + **viés ao quadrado** (erro sistemático). É a tradução matemática exata do alvo de dardos — a dualidade precisão × acurácia destilada numa equação.

---

**🔵 Q17 — Ilustre um estimador não-viesado e um viesado.**

**Gabarito.**
- **Não-viesado:** a média amostral $\bar X$ para μ ($E[\bar X]=\mu$); ou a variância amostral $s^2=\frac{1}{n-1}\sum(x_i-\bar x)^2$ ($E[s^2]=\sigma^2$).
- **Viesado:** $S_n^2=\frac1n\sum(x_i-\bar x)^2$ para σ², pois $E[S_n^2]=\frac{n-1}{n}\sigma^2<\sigma^2$ → **subestima sistematicamente**. No alvo de dardos: mira torta, sempre cai para o mesmo lado.

---

### Bloco prático (Listas 2 e 3)

---

**🟢 Q1 (Lista 2) — $\bar x$ e $\hat\sigma^2=\frac1n\sum(x_i-\bar x)^2$. Julgue V/F:**

**Gabarito:**
- **(a) Ambos não-viesados — FALSO.** $\bar x$ é não-viesado, mas $\hat\sigma^2$ (dividido por $n$) é viesado: $E[\hat\sigma^2]=\frac{n-1}{n}\sigma^2$.
- **(b) Ambos consistentes — VERDADEIRO.** Os dois convergem em probabilidade quando $n\to\infty$. Mesmo $\hat\sigma^2$ sendo viesado para $n$ finito, o viés $\frac{n-1}{n}\sigma^2\to\sigma^2$ e a variância $\to 0$ → consistente.
- **(c) Apenas $\bar x$ é consistente — FALSO** (os dois são).
- **(d) Apenas $\bar x$ é não-viesado — VERDADEIRO.**

> Lição embutida: **viés e consistência são coisas diferentes.** Um estimador pode ser viesado e ainda assim consistente.

---

**🟢 Q4 (Lista 3) — Mostre que $E(S^2)=\sigma^2$, com $S^2=\frac{1}{n-1}\sum(X_i-\bar X)^2$.**

**Gabarito (a demonstração que justifica o n−1):**

Truque: somar e subtrair μ dentro do quadrado.
$$\sum(X_i-\bar X)^2=\sum\big[(X_i-\mu)-(\bar X-\mu)\big]^2=\sum(X_i-\mu)^2-2(\bar X-\mu)\underbrace{\sum(X_i-\mu)}_{=\,n(\bar X-\mu)}+n(\bar X-\mu)^2$$
$$=\sum(X_i-\mu)^2-2n(\bar X-\mu)^2+n(\bar X-\mu)^2=\sum(X_i-\mu)^2-n(\bar X-\mu)^2.$$

Tomando esperança e usando $E[(X_i-\mu)^2]=\sigma^2$ e $E[(\bar X-\mu)^2]=\text{Var}(\bar X)=\sigma^2/n$:
$$E\Big[\sum(X_i-\bar X)^2\Big]=n\sigma^2-n\cdot\frac{\sigma^2}{n}=(n-1)\sigma^2.$$

Logo $E[S^2]=\frac{1}{n-1}(n-1)\sigma^2=\boxed{\sigma^2}.$ ∎

> É exatamente o motivo do $n-1$: o $-1$ compensa o grau de liberdade "gasto" ao estimar $\bar X$ a partir dos próprios dados.

---

**🟢 Q8 (Lista 2) — Quais itens são variável aleatória?**

**Gabarito.** Variável aleatória = depende da amostra *sorteada*. Parâmetros e quantidades fixas **não** são.

| Item | V.A.? | Por quê |
|---|---|---|
| (a) média da população | ❌ | parâmetro fixo (μ) |
| (b) tamanho N da população | ❌ | constante fixa |
| (c) tamanho n da amostra | ❌ | escolhido por nós, fixo |
| (d) **média da amostra** | ✅ | depende da amostra |
| (e) variância da média da amostra | ❌ | $\sigma^2/n$ é um número fixo |
| (f) **maior valor na amostra** | ✅ | é uma estatística, depende da amostra |
| (g) variância da população | ❌ | parâmetro fixo (σ²) |
| (h) **variância *estimada* da média da amostra** | ✅ | $s^2/n$ — depende dos dados |

> Pegadinha fina: (e) vs (h). A variância *verdadeira* de $\bar X$ ($\sigma^2/n$) é fixa; a variância *estimada* ($s^2/n$) é aleatória.

**Resposta: (d), (f) e (h).**

---

**🟢 Q1 (Lista 3) — Combinação $Z=aL_1+(1-a)L_2$. Para qual $a$ a variância de $Z$ é mínima?**

> ⚠️ O enunciado tem um deslize: o interessante (e o que o texto diz logo antes) é que **as precisões diferem**, ou seja $V(L_1)\neq V(L_2)$. Resolvo o caso geral; o caso $V(L_1)=V(L_2)$ cai como caso particular ($a=1/2$).

**Gabarito.** As medições são independentes, então:
$$\text{Var}(Z)=a^2\,V(L_1)+(1-a)^2\,V(L_2).$$
Minimizando (derivada em $a$ igual a zero):
$$\frac{d}{da}\text{Var}(Z)=2a\,V(L_1)-2(1-a)\,V(L_2)=0\ \Rightarrow\ a\,V(L_1)=(1-a)\,V(L_2)$$
$$\boxed{a^*=\frac{V(L_2)}{V(L_1)+V(L_2)}}$$

Interpretação linda (conecta com **precisão**): os pesos são **inversamente proporcionais às variâncias** — o aparelho mais *preciso* (menor variância) recebe mais peso. Se $V(L_1)=V(L_2)$, então $a^*=1/2$ (média simples). Isso é a **ponderação por inverso da variância**, a forma ótima de combinar medidas não-viesadas.

---

**🔵 Q5 (Lista 3) — Mínimos quadrados: solubilidade do NaNO₃ × temperatura.**
*(Passar de treino — é o "refazer em Python". Gabarito completo abaixo.)*

**Gabarito.** Fórmulas do MQO:
$$\beta_1=\frac{n\sum T Y-\sum T\sum Y}{n\sum T^2-(\sum T)^2},\qquad \beta_0=\bar Y-\beta_1\bar T.$$

Somatórios ($n=9$): $\sum T=234$, $\sum Y=811{,}3$, $\sum T^2=10144$, $\sum TY=24628{,}6$, $\bar T=26$, $\bar Y=90{,}144$.

$$\beta_1=\frac{9(24628{,}6)-234(811{,}3)}{9(10144)-234^2}=\frac{31813{,}2}{36540}=\boxed{0{,}8706}$$
$$\beta_0=90{,}144-0{,}8706(26)=\boxed{67{,}508}$$

**Reta ajustada:** $\hat Y = 67{,}51 + 0{,}871\,T$. Faz sentido físico: a $T=0$ a solubilidade prevista (~67,5) bate com o dado observado (66,7), e a solubilidade cresce ~0,87 parte por °C.

```python
import numpy as np
T = np.array([0,4,10,15,21,29,36,51,68], float)
Y = np.array([66.7,71,76.3,80.6,85.7,92.9,99.4,113.6,125.1], float)
b1, b0 = np.polyfit(T, Y, 1)
print(b1, b0)   # 0.87064  67.50779
```

---

**🔵 Q9 e Q10 (amostragem estratificada / Neyman) — passar de treino.**

> ⚠️ **Aviso honesto:** esses dois exercícios são de *teoria de amostragem* (alocação proporcional vs. Neyman) — assunto que **não está na sua síntese**, vem dos slides do professor. Gabarito com a teoria-padrão abaixo. Recomendo passar de treino e revisar o gabarito junto, sem gastar aula explicando do zero.

**Fatos-base (memorizar):**
- Alocação **proporcional:** $n_h\propto N_h$. Alocação de **Neyman (ótima):** $n_h\propto N_h\sigma_h$.
- Variância: **Neyman ≤ Proporcional ≤ Amostragem Simples** (todas com igualdade em casos particulares).
- Neyman exige conhecer a **variância de cada estrato** $\sigma_h$.

**Q9 — Julgue:**
- **(a)** Estratificada tem variância menor que a simples — **VERDADEIRO** (no geral ≤; estratos homogêneos por dentro reduzem a variância da estimativa).
- **(b)** Se as variâncias das duas alocações são iguais, as estimativas não dependem do método — **FALSO.** Variância do estimador igual ≠ estimativa igual; as estimativas são v.a. e dependem dos dados sorteados em cada esquema.
- **(c)** A média de uma amostra estratificada é viesada — **FALSO.** O estimador estratificado (ponderado por $W_h=N_h/N$) é **não-viesado**.
- **(d)** Para estimativa mais precisa, aumentar $n$ — **VERDADEIRO** (erro padrão $\propto 1/\sqrt n$).
- **(e)** Na amostragem simples, $E(\bar X)=\mu$ — **VERDADEIRO** (não-viesada).

**Q10 — Julgue:**
- **(a)** "Quanto mais variância *entre* as variâncias dos estratos, melhor Neyman; e se as variâncias são iguais, as estimativas da variância populacional são *necessariamente* iguais" — **FALSO** (afirmação composta). A 1ª parte é verdadeira (a vantagem de Neyman sobre proporcional cresce quando os $\sigma_h$ diferem muito); a 2ª é falsa (variâncias iguais ⇒ Neyman = proporcional *na alocação/variância do estimador*, mas as **estimativas** continuam aleatórias, não "necessariamente iguais"). Basta uma parte falsa → tudo falso.
- **(b)** Neyman exige conhecer as variâncias individuais de cada partição, sem exceção — **VERDADEIRO.**
- **(c)** Proporcional *sempre* dá variância menor que a simples — **FALSO.** É ≤, não "sempre menor": quando as médias dos estratos são todas iguais, proporcional = simples (sem ganho).
- **(d)** Quanto *menos* dispersa a média entre as partições, melhor a estimativa com pesos proporcionais — **FALSO.** É o contrário: o ganho da estratificação vem de estratos com médias *diferentes* (alta dispersão entre partições). Pouca dispersão entre estratos → pouco ganho sobre a simples.

---

# 📗 AULA 2 — Inferência (30 min de conceito)

### 1. Distribuição de Poisson *(6 min)*
- Responde: *"se eventos raros acontecem aleatoriamente a uma taxa média λ, quantos vejo num intervalo fixo?"*
- **Três ingredientes:** eventos discretos (conta 0,1,2…), independentes, taxa λ constante.
- Fórmula: $P(X=k)=\dfrac{\lambda^k e^{-\lambda}}{k!}$.
- **Assinatura única: média = variância = λ.** Se no mundo real variância ≫ média → *overdispersion* (algum ingrediente foi violado).
- Nasce como limite da **Binomial** quando $N\to\infty$, $p\to0$, com $Np=\lambda$ fixo ("lei dos eventos raros"). Coices de cavalo no exército prussiano, decaimento radioativo, fila de call center.

### 2. Máxima Verossimilhança *(4 min)*
- Retoma a dualidade probabilidade × verossimilhança.
- **MLE = o parâmetro que maximiza $L(\theta)$** = o que torna os dados observados os mais "esperáveis".
- Moeda, 7 caras em 10: $L(0{,}7)\approx0{,}267$ é máximo → p=0,7 é ~2,3× mais compatível com os dados que p=0,5.

### 3. Intervalo de Confiança *(6 min)*
- $IC_{95\%}(\mu)=\bar X\pm 1{,}96\,\dfrac{\sigma}{\sqrt n}$ (σ conhecido). O 1,96 = 95% da massa da Normal padrão.
- σ **desconhecido** e amostra pequena → troca Normal pela **t de Student** e σ por $s$.
- **CUIDADO INTERPRETATIVO (cai na prova!):** o certo é *"se eu repetisse o experimento muitas vezes, 95% dos intervalos conteriam o parâmetro"*. O **errado** (tentador): *"há 95% de chance do parâmetro estar neste intervalo"*. O parâmetro é fixo; o **intervalo** é que é aleatório.

### 4. Teste de Hipóteses e os dois erros *(10 min — o núcleo)*
- **H0** (hipótese nula) = premissa de partida (réu inocente). **H1** = o que geralmente queremos provar.
- **α (nível de significância):** quanto aceitamos errar rejeitando H0 quando ela era verdadeira. Fixado *antes* (evita *p-hacking*).
- **CUIDADO (o erro mais comum em estatística aplicada):** $\alpha=P(\text{dados extremos}\mid H_0)$, **NÃO** $P(H_0\mid\text{dados})$. **p-valor NÃO é a probabilidade de H0 ser verdadeira.**

| | **H0 verdadeira** | **H0 falsa** |
|---|---|---|
| **Rejeito H0** | Erro tipo I (α) — falso + | Acerto |
| **Não rejeito H0** | Acerto | Erro tipo II (β) — falso − |

- **Poder do teste** $=1-\beta$ = probabilidade de detectar um efeito que existe. Cresce com $n$.
- **"Falhei em rejeitar H0" ≠ "provei H0".** Pode ser só falta de poder (amostra pequena, ruído alto).

---

## 🧮 AULA 2 — Bateria de exercícios (gabarito)

### Intervalos de confiança (Lista 4)

---

**🔵 Q1 — n=10, $\bar X=10{,}48$, $\hat\sigma=1{,}36$, confiança 90%.** *(passar de treino — s já vem pronto)*

**Gabarito.** σ é *estimado* e n é pequeno → **t de Student**, $df=n-1=9$.
$$IC_{90\%}=\bar X\pm t_{0{,}95;\,9}\cdot\frac{s}{\sqrt n}=10{,}48\pm 1{,}833\cdot\frac{1{,}36}{\sqrt{10}}=10{,}48\pm 1{,}833\cdot 0{,}4301=10{,}48\pm 0{,}788$$
$$\boxed{IC_{90\%}=(9{,}69;\ 11{,}27)}$$

> Se o professor mandar tratar σ como *conhecido* (usar z=1,645): $10{,}48\pm0{,}707=(9{,}77;\ 11{,}19)$. Com σ estimado, a t é a escolha rigorosa.

---

**🟢 Q2 — n=30, $\sum X_i=700{,}8$, $\sum X_i^2=16395{,}8$. IC 95% bilateral para μ.** *(explicar — é o mais completo: exige montar $s$ a partir dos somatórios)*

**Gabarito.**

1. Média: $\bar X=\dfrac{700{,}8}{30}=23{,}36$.
2. Variância amostral pela fórmula do "atalho":
$$s^2=\frac{\sum X_i^2-(\sum X_i)^2/n}{n-1}=\frac{16395{,}8-\frac{700{,}8^2}{30}}{29}=\frac{16395{,}8-16370{,}688}{29}=\frac{25{,}112}{29}=0{,}8659$$
$$s=0{,}9306,\qquad \frac{s}{\sqrt n}=\frac{0{,}9306}{\sqrt{30}}=0{,}1699.$$
3. $df=29$, $t_{0{,}975;\,29}=2{,}045$:
$$IC_{95\%}=23{,}36\pm 2{,}045\cdot 0{,}1699=23{,}36\pm 0{,}347$$
$$\boxed{IC_{95\%}=(23{,}01;\ 23{,}71)}$$

> Com z=1,96 daria $(23{,}03;\ 23{,}69)$ — quase igual, pois $n=30$ já é "grande". Lidere com a t por rigor.

---

### Teste de hipóteses (Lista 5) — exemplo completo

**🟢 EXPLICAR — é o coração da Aula 2.**

**Cenário:** $\sigma^2=400$ (logo $\sigma=20$) **conhecida**, $n=25$. Testar $H_0:\mu=100$ contra $H_1:\mu=105$. Estatística = média amostral, com $\bar X\sim N\big(\mu,\sigma^2/n\big)$, então o desvio padrão de $\bar X$ é $\dfrac{\sigma}{\sqrt n}=\dfrac{20}{5}=4$.

**(a) Erro tipo I com valor crítico arbitrário $t=103{,}36$:**
$$P(\text{erro I})=P(\bar X>103{,}36\mid\mu=100)=P\!\left(Z>\frac{103{,}36-100}{4}\right)=P(Z>0{,}84)\approx\boxed{20\%}$$

**(b) Erro tipo II (com o mesmo $t=103{,}36$):**
$$P(\text{erro II})=P(\bar X<103{,}36\mid\mu=105)=P\!\left(Z<\frac{103{,}36-105}{4}\right)=P(Z<-0{,}41)\approx\boxed{34\%}$$

**(c) Qual $t$ faz o erro tipo I valer exatamente 5%?** (α=0,05 fixado *a priori*)
$$0{,}05=P(\bar X>t\mid\mu=100)=P\!\left(Z>\frac{t-100}{4}\right)\ \Rightarrow\ \frac{t-100}{4}=1{,}645\ \Rightarrow\ \boxed{t\approx106{,}58}$$
(Com a aproximação $z=1{,}64$ da tabela: $t=106{,}56$.)

**Decisão:** se $\bar X>106{,}58$, **rejeito H0** ao nível 5%; caso contrário, não rejeito.

**Bônus para fixar o trade-off α↔β:** ao apertar α (de 20% → 5%), o valor crítico subiu (103,36 → 106,58) e o **erro tipo II aumentou**. Nesse $t$, o poder fica $1-\beta=P(\bar X>106{,}58\mid\mu=105)=P(Z>0{,}39)\approx 35\%$ (β≈65%). **Reduzir um erro encarece o outro** — só dá para baixar os dois juntos aumentando $n$ (que estreita a distribuição de $\bar X$).

---

# 🗺️ Arquitetura sugerida das 2 horas

| Tempo | Bloco | Conteúdo |
|---|---|---|
| 0–10 min | Abertura | As **4 dualidades** + alvo de dardos. Tudo será pendurado aqui. |
| 10–30 min | Conceito A1 | Descritiva → precisão×acurácia → Normal → likelihood → viés/EQM → convergência |
| 30–75 min | Exercícios A1 | 🟢 L1: Q6, Q11+Q12, Q13–15, Q16 · 🟢 L2: Q1, Q8 · 🟢 L3: Q4, Q1 |
| 75–80 min | Respiro/treino | Entregar 🔵 Q2, Q17 (L1), Q5, Q9, Q10 com gabarito |
| 80–100 min | Conceito A2 | Poisson → MLE → IC → teste de hipóteses + erros I/II/poder |
| 100–120 min | Exercícios A2 | 🟢 L4 Q2 · 🟢 L5 exemplo completo (erros I/II) · entregar 🔵 L4 Q1 de treino |

**Princípio do recorte:** os 🟢 escolhidos cobrem *cada* conceito ao menos uma vez (estimador, viés, consistência, EQM, convergência nos 3 modos, v.a. vs. parâmetro, MQO, IC, erros I/II). Os 🔵 são repetições mecânicas ou assunto de slide — viram treino com gabarito, sem custar aula.

**Três frases para a Luiza sair repetindo (são "pegadinhas" garantidas do professor):**
1. *"p-valor NÃO é a probabilidade de H0 ser verdadeira."*
2. *"Falhar em rejeitar H0 não é provar H0."*
3. *"No IC, o parâmetro é fixo; quem é aleatório é o intervalo."*
