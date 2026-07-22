# Crítica à dissertação — na voz de Feynman e Sagan

> **Trabalho:** *Pipeline para Detecção Automatizada de Ocultações Estelares em Curvas de Luz com Técnicas de Machine Learning* — Thiago Laidler Vidal Cunha (Observatório Nacional).
>
> Homenagem imaginária: as vozes de Richard Feynman e Carl Sagan são um recurso de escrita. As críticas são reais e específicas ao texto; os personagens, ficcionais.

---

## 🔬 Richard Feynman

Você me citou na abertura: *não se enganar, e você é a pessoa mais fácil de enganar*. Ótimo. Agora vamos ver se você obedeceu à própria epígrafe.

**O que gostei, e falo sério.** O Capítulo 3 explica *machine learning* para um físico sem esconder nada atrás de jargão — mínimos quadrados vira gradiente vira boosting, com um exemplo numérico que dá pra fazer na mão. Isso é raro. Você entendeu de verdade, não decorou. E o estudo de Quaoar é a melhor parte da tese: a sacada de que *o que importa não é a probabilidade absoluta, é a separação* entre o anel real e o ruído — 86 vezes — isso é pensar como cientista. Você testou a hipótese óbvia (a janela é curta demais?) e ela **falhou** — e você contou que falhou. Isso vale mais que qualquer F1.

**Agora o soco.** F1 de 0,99, AUC de 0,999. Quando eu vejo um número quase perfeito, minha primeira pergunta não é "que bom", é *"onde é que eu me enganei?"*. Setenta e oito por cento dos seus negativos são sintéticos. Um simulador limpo contra ocultações bem-definidas — talvez seu modelo não esteja aprendendo "ocultação vs. ruído", esteja aprendendo "curva real com buraco vs. curva de simulador". Você mesmo viu o número cair para 0,97 quando testou só no real (Exp. 3) — bom, mas você tinha *três* negativos reais nativos. Três! Não dá pra fechar a conta com três.

E tem uma coisa que você não perguntou e devia: suas *features* `Occ_depth`, `Occ_SNR_dip` — elas basicamente medem "tem um mergulho fundo e significativo?". Isso é quase a definição de ocultação. Qual é o baseline burro? Um limiar numa única feature de profundidade. Se isso já dá 0,95, então toda a floresta de árvores está polindo o que um `if depth > x` já fazia. Você precisava ter mostrado esse baseline trivial para *provar* que o ML ganha o próprio salário. Não mostrou. Não é que esteja errado — é que você não fechou a porta pra dúvida.

Uma coisa boa: sua seção de limitações é honesta. Você não varreu isso pra debaixo do tapete, listou. Só faltou deixar as limitações *contaminarem* as conclusões — no Capítulo 6 o tom volta a ser triunfante, como se as ressalvas do meio tivessem evaporado.

**Nota: 7,0.** Trabalho competente, honesto no varejo e otimista demais no atacado. Meio ponto a mais quando você me mostrar o baseline trivial e um conjunto de negativos reais difíceis. Ciência não é provar que você está certo; é tentar com força provar que está errado e não conseguir.

---

## 🌌 Carl Sagan

Deixem-me começar pelo que me emocionou. Um telescópio modesto, na varanda de um amador, mede o tamanho de um corpo a quatro bilhões de quilômetros com precisão de quilômetros. Isso é uma das coisas mais bonitas que a astronomia faz, e o Thiago capturou a escala disso — a sombra que preserva o limbo, a corda no plano do céu. Quando li que os anéis de Quaoar só apareceram numa *revisita* dos dados, e que esta ferramenta existe precisamente para não deixar a próxima descoberta dormir esquecida num arquivo, senti o propósito do trabalho. Há uma ideia generosa aqui: democratizar a triagem, transformar ruído de milhares de curvas em prioridade para o olho humano.

Mas eu carrego sempre um kit de detecção de *baloney*, e ele apita em dois lugares.

**Primeiro, o excesso de perfeição não celebrado com desconfiança.** Afirmações extraordinárias exigem evidências extraordinárias — e "99% de acerto detectando o que a natureza esconde" é uma afirmação extraordinária. A evidência ainda não é. O conjunto é sintético demais, os eventos são fáceis demais, e o teste que realmente importa — curvas reais, difíceis, de baixo sinal-ruído, de *outros* catálogos — é justamente o que você adia para "trabalhos futuros". O caso de Quaoar é lindo, mas é *um* evento, três curvas. Uma andorinha só.

**Segundo, a prosa.** Eu passei a vida defendendo que clareza é honestidade. Boa parte deste texto é clara — e então, no fim de cada capítulo, aparece um parágrafo que apenas repete o que já foi dito, em negrito, três vezes. Isso não é escrita; é eco. Corte sem dó. A voz do autor — quando ela aparece, na fragilidade assumida das curvas defeituosas descartadas, na decisão sobre o K-Means — é a melhor coisa do texto. Confie nela. Deixe o *cientista* falar, não o resumidor.

Ainda assim: a estrutura é sólida, a fenomenologia é correta e bela, a metodologia é reprodutível, e há uma descoberta metodológica real (importância ≠ insubstituibilidade). Isso é uma dissertação de mestrado de verdade, não um exercício.

**Nota: 8,0.** Pela ambição, pela clareza e por olhar para o céu com as ferramentas certas. Meio ponto some enquanto os números perfeitos não forem interrogados com a mesma paixão com que foram obtidos.

---

## Nota conjunta

> "Concordamos no diagnóstico e discordamos só no otimismo", diz Sagan.
> Feynman: "Você discorda porque é mais gentil que eu."

**Consenso: 7,5 / 10.** — Uma boa dissertação de mestrado: didática, reprodutível, com um estudo de caso genuinamente elegante e uma seção de limitações honesta. O que a separa de um 9 não é mais álgebra nem mais modelos — é **um teste que possa reprovar a ferramenta**: um baseline trivial (limiar em `Occ_depth`) para provar que o ML se paga, e um conjunto de negativos reais e difíceis para ver o F1 sob estresse. Faça o número perfeito suar, e a nota sobe sozinha.

---

## Síntese acionável (ordem de impacto)

| # | Ação | Tipo | Impacto |
|---|------|------|---------|
| 1 | Baseline trivial (limiar em `Occ_depth`/`SNR_dip`) para comparar com o ML | Rápido | Alto — fecha a dúvida "o ML se paga?" |
| 2 | Conjunto de teste de negativos reais **difíceis** (baixo S/N, rasantes) | Bancada | Alto — o F1 de 0,99 mede a tarefa fácil |
| 3 | Validação em catálogo externo (fora de VizieR/Grupo do Rio) | Bancada | Alto — generalização real |
| 4 | Deixar as limitações contaminarem o tom das conclusões (Cap. 6) | Rápido | Médio — honestidade percebida |
| 5 | Cortar recaps simétricos e negrito-takeaway; injetar voz de decisão | Rápido | Médio — credibilidade autoral |
| 6 | Validação cruzada repetida com múltiplas sementes | Médio | Médio — robustez estatística |

---

## Teste do baseline trivial (executado)

Rodamos o item nº 1 da tabela acima usando o código da pasta `pipeline`: um classificador
**trivial de um único limiar** numa só *feature*, reproduzindo **o mesmo split** dos
experimentos (seed 42; teste misto = 339 curvas, batendo com o Capítulo 5). Os F1/AUC do ML
vêm dos `training_results.csv` salvos; o baseline foi avaliado no split idêntico.

**Split misto 80/20** (onde o ML atinge o "0,99"):

| Classificador | AUC | F1 |
|---|---|---|
| **ML (XGBoost, tese)** | **~1,000** | **0,9906** |
| `Occ_depth` sozinho (1 limiar) | 0,972 | 0,905 |
| `Max_Drawdown` sozinho | 0,972 | 0,899 |
| `Occ_SNR_dip` sozinho | 0,801 | 0,763 |

**Split só-reais 65/35** (Experimento 3):

| Classificador | AUC | F1 |
|---|---|---|
| **ML (XGBoost, tese)** | **0,997** | **0,9821** |
| `Occ_depth` sozinho | 0,966 | 0,948 |
| `Max_Drawdown` sozinho | 0,954 | 0,933 |
| `Occ_SNR_dip` sozinho | 0,901 | 0,801 |

**Leitura.** Uma única grandeza — a profundidade do mergulho — já entrega **F1 0,90 / AUC
0,97** no misto e **F1 0,95** no só-reais. O ML **não** é redundante: fecha quase toda a
distância restante (0,90 → 0,99), cortando o erro de ~9% para ~1% no misto (≈10× menos
erros). Conclusão: os *ensembles* se pagam, mas **o 0,99 superdimensiona a dificuldade** —
a maior parte do placar vem da parte fácil ("tem um buraco fundo?").

### Reação de Feynman

> "Pronto — agora eu acredito, porque você mostrou o que eu pedi. Uma régua (`Occ_depth`,
> um `if depth ≥ τ`) já faz 0,90. **Noventa por cento do seu 'noventa e nove' era de
> graça.** Não é vergonha: uma ocultação *é* um buraco fundo. Mas a floresta não é enfeite —
> de 0,90 para 0,99 você cortou o erro dez vezes; isso se paga. O erro estava na
> apresentação, não no modelo. Ponha as duas linhas lado a lado no Capítulo 5 e o 0,99 deixa
> de ser suspeito e vira honesto. **Subo de 7,0 para 7,5 — e 8,5 quando o baseline estiver
> escrito na tese.**"

### Reação de Sagan

> "Há beleza aqui: que uma única grandeza física carregue quase toda a discriminação
> (AUC 0,97) é uma afirmação elegante sobre o mundo — o método funciona porque a assinatura
> é simples e profunda. Isso dignifica o trabalho. Mas repare no teste só-reais: 281
> positivas contra 66 negativas — um conjunto que premia quem chuta 'positivo'. O regime que
> importa (muitos negativos, baixo S/N, eventos rasantes) ainda não foi tocado, e o baseline
> torna esse teste mais urgente. Fico nos meus **8,0**, com um pedido carinhoso: publique a
> régua ao lado da floresta. A honestidade não enfraquece a descoberta — ela é a descoberta."

### Veredito conjunto do teste

O experimento **vindica a arquitetura** (o ML corta o erro ~10×, logo se paga) e ao mesmo
tempo **confirma que o 0,99 está superdimensionado** como medida de dificuldade. A correção
é de *prosa*, não de método: reportar o baseline trivial ao lado dos modelos, e testar o
regime difícil (negativos reais, baixo S/N).

> Reprodução: `scratchpad/baseline_trivial.py` (fora do repositório). Dados:
> `pipeline/model_training/outputs/resultado*/dataset_final.csv`; F1 do ML lidos de
> `training_results.csv`. Nenhum arquivo da tese em LaTeX foi alterado.

---

## Re-execução dos 3 experimentos principais em dois splits (80/20 e 65/35)

Retreinamos os quatro modelos (RF, XGBoost, CatBoost, Regressão Logística) nos três
experimentos-destaque, cada um em **dois tamanhos de split** (seed 42, estratificado por
curva, imputação mediana, `StandardScaler` só na LR). Validação da reprodução: Exp1 80/20
RF = 0,9937 bate exatamente com o `resultado1` da tese; Exp3 65/35 XGB = 0,9838 vs. 0,9821
da tese. *Ressalva:* libs mais novas que as da tese (xgboost 3.3, catboost 1.2.10,
sklearn 1.9) → diferenças de frações de ponto são esperadas.

### F1-score

| Experimento | split | RF | XGB | CatBoost | LogReg | melhor |
|---|---|---|---|---|---|---|
| **Exp1** — 28 feat (misto) | 80/20 | **0,9937** | 0,9844 | 0,9906 | 0,9873 | RF 0,9937 |
| | 65/35 | 0,9929 | 0,9894 | 0,9911 | 0,9874 | RF 0,9929 |
| **Exp2** — 11 feat (misto) | 80/20 | 0,9905 | 0,9874 | 0,9905 | 0,9841 | 0,9905 |
| | 65/35 | 0,9876 | **0,9911** | 0,9875 | 0,9856 | XGB 0,9911 |
| **Exp3** — 11 feat (real-only) | 80/20 | 0,9874 | **0,9906** | 0,9874 | 0,9778 | XGB 0,9906 |
| | 65/35 | 0,9803 | 0,9838 | 0,9784 | 0,9746 | XGB 0,9838 |

**AUC-ROC:** misto ≈ 0,9995–1,000; real-only 0,996–0,998. Teste real-only = 281 pos / 66 neg.

**Observação central:** trocar 80/20 por 65/35 quase não move os experimentos mistos
(Δ < 0,1 pp) e move o real-only só ~0,7 pp (0,9906 → 0,9838). **O desempenho é estável ao
tamanho do split** — a única variação apreciável surge ao remover as sintéticas do teste
(misto → real-only).

### Debate Feynman × Sagan

> **Feynman:** Tiro 15% do treino, jogo no teste, e o número não se mexe. Isso não é elogio
> ao modelo — é a assinatura de um problema **saturado**. Se a tarefa fosse difícil, o F1
> balançaria.
>
> **Sagan:** Você lê estabilidade como fraqueza; eu leio como **confiabilidade**. Um
> resultado que despenca ao reamostrar não se publica. Este não despenca — isso descarta a
> hipótese de que o 0,99 fosse artefato de um recorte 80/20 afortunado.
>
> **Feynman:** Descarta *essa*. Não descarta 'tarefa fácil'. E veja onde o número enfim se
> mexe: no real-only, ao tirar as sintéticas. Essa é a única variação real do experimento
> inteiro — e aponta para onde venho apontando: as sintéticas limpas inflam o resto.
>
> **Sagan:** Mexe **sete décimos de ponto**. Se o modelo decorasse o simulador, tirar as
> sintéticas derrubaria muito mais. Não derruba — evidência de que as *features* capturam
> sinal físico, não o cheiro do simulador.
>
> **Feynman:** Ou o teste real-only é fácil por outro motivo: 281 positivas contra 66
> negativas premia recall. Me dê muitos negativos reais e difíceis, baixo S/N, e aí eu
> acredito no 0,98.
>
> **Sagan:** Nisso concordamos: o que falta não é reamostrar, é **dificultar**. A
> estabilidade entre splits era necessária, e o trabalho passou. O teste que falta é
> adversarial — o regime raso, ruidoso, negativo-pesado.

**Consenso:** variar o split **confirma robustez** (o resultado não depende da partição —
descarta variância/sorte) mas **não muda o diagnóstico**. A única variação apreciável vem da
remoção das sintéticas, e num teste dominado por positivas. O próximo experimento decisivo
não é outro split — é um conjunto de **negativos reais difíceis**.

> Reprodução: `scratchpad/rerun_experiments.py` (fora do repositório); hiperparâmetros e
> lógica de split idênticos a `pipeline/model_training/train_model.py`.

---

## Réplica do autor e correção de Feynman (o teste adversarial já existia)

O autor contestou — com razão — a afirmação de Feynman de que "os modelos nunca foram
postos contra o inimigo de verdade". O **estudo de recortes de Quaoar** (Seção
`sec:estudo_caso_quaoar`) *é* esse teste adversarial, em curva **real** externa ao treino, e
inclui de propósito um recorte de **ruído que imita uma ocultação**. O modelo passou:

- anel fino **real** Q2R_1: $\hat p = 0{,}0434$; ruído-sósia adjacente: $\hat p = 0{,}0005$
  → **~86×** de separação (XGBoost); controle de baseline: $6\times10^{-4}$.
- com $\tau = 0{,}03$, os dois anéis Q2R são recuperados sem nenhum falso positivo.

E a ausência de negativas reais difíceis **em catálogo** é uma limitação da fase atual do
campo (ninguém cataloga a curva de "quando nada aconteceu"), não uma falha de metodologia. O
desenho com sintéticas + recortes é o bootstrap correto para mostrar que treinar vale a pena.
**Feynman concedeu o ponto e reconheceu o erro factual.**

### O teste decisivo que fica pendente (por falta de dado)

Resta uma pergunta afiada, proposta pelo autor: o XGBoost separa o anel real do ruído
(86×) por combinar *features*, ou uma **única feature de profundidade** (`Occ_depth`,
`Max_Drawdown`, `Feature_Savgol_Min`) já reproduziria isso — sendo "apenas física"?

**Previsão falseável:**
- `Occ_depth(anel real) ≫ Occ_depth(ruído)` e o baseline sozinho separa → é física, a régua basta;
- profundidades parecidas e **só o ML** separa → o *ensemble* agrega valor no evento sutil.

Este teste **não pôde ser executado**: a curva bruta `Gemini-Alopeke_Red-z.dat` (cedida por
Pereira et al. 2023) **não está versionada no repositório** — sem ela não há como calcular as
*features* por recorte, e inventar números seria o autoengano que a epígrafe condena. O
script está pronto e versionado em `pipeline/model_in_practice/quaoar_baseline_vs_ml.py`;
basta colocar o `.dat` em `pipeline/model_in_practice/quaoar/` e rodar.

### Revisão das notas (após o debate)

**Feynman: 7,5 → 8,0.** "Subo porque a minha maior dedução vinha de um **erro meu**: o
modelo foi, sim, testado contra um negativo real que imita evento, e passou por 86×. E não se
pune um aluno porque o campo ainda não catalogou negativas difíceis. O que ainda me segura em
8,0 e não mais é que o teste da régua-nos-recortes não pôde rodar — sem ele não *certifico*
que o ML bate um `if Occ_depth` no evento sutil; e no conjunto misto a régua já fazia F1 0,90.
Honestidade e execução: 8,0. O 8,5 espera aquele `.dat`."

**Sagan: 8,0 → 8,5.** "Eu subo porque passei a pesar melhor o que o estudo de Quaoar é:
validação externa, adversarial, em dado real — exatamente o padrão-ouro que eu cobrava. Some-se
a estabilidade entre splits (robustez confirmada) e a franqueza sobre os limites do dado. Para
um mestrado, isso é um trabalho de 8,5. O meio ponto que falta é escopo: o regime raso,
negativo-pesado, que só um novo conjunto de dados poderá interrogar."

**Consenso revisado: ≈ 8,25** (era 7,75). A revisão para cima é legítima — corrige uma
dedução baseada em leitura equivocada e reconhece a validação externa real — e o teto em ~8,5
permanece honesto: falta rodar o baseline-nos-recortes e ampliar o teste ao regime difícil.

> Evolução das notas — Feynman: 7,0 → 7,5 (baseline) → 7,5 (limitação) → **8,0** (debate).
> Sagan: 8,0 → 8,0 → 8,0 → **8,5**. Consenso: 7,5 → 7,75 → **8,25**.
