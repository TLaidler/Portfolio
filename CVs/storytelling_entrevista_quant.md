# Storytelling de entrevista — Thiago Laidler, candidato quant

> **Nota de autoria:** este documento é assinado por "Helena Vasconcellos", especialista sênior em recrutamento quant para o mercado financeiro — uma persona ficcional, no mesmo espírito das homenagens de Feynman, Sagan e Simons que o motivaram. A persona é recurso de escrita; os fatos, histórias e números vêm todos do portfólio e do CV reais.

---

## Nota da recrutadora

Vinte anos colocando físicos em mesas de fundo me ensinaram uma coisa: o candidato-cientista quase sempre conta a história errada. Ele pede desculpas pela academia ("eu sei que não tenho experiência de mercado...") quando deveria cobrá-la como prêmio. O Thiago tem o problema inverso do candidato médio — o material dele é *melhor* do que a forma como ele o apresenta. Três avaliadores exigentes leram o portfólio inteiro e convergiram no mesmo diagnóstico, e é ele que deve virar a espinha dorsal de qualquer entrevista:

**Thiago não é um astrônomo que virou quant. É um detector de sinais fracos em ruído que trocou de dataset.**

Tudo neste documento deriva dessa tese. Regra da casa: **nenhuma frase de clichê** — "proativo", "trabalho em equipe", "apaixonado por dados" estão proibidos. Cada afirmação abaixo aponta para um artefato real, citável na entrevista com link do GitHub ([github.com/TLaidler](https://github.com/TLaidler)). Entrevistador quant confia em evidência, não em adjetivo.

---

## 1. Elevator pitch (30 segundos)

**Português:**

> "Eu passei a graduação e o mestrado resolvendo um problema: detectar quedas de brilho minúsculas, raras e valiosas — ocultações estelares — enterradas em ruído, onde um falso positivo custa caro. Publiquei no *Monthly Notices of the Royal Astronomical Society* medindo Umbriel com precisão de quilômetros e construí um pipeline de ML pra automatizar essa triagem. Aí percebi que o mercado financeiro é exatamente o mesmo problema com outro dataset — sinal fraco, ruído dominante, autoengano como maior risco. Hoje sou Analista Quantitativo na Transfero, cuidando de risco, backtests e infraestrutura de dados de fundos com giro de cerca de US$ 1 bilhão ao ano. O que eu trago não é só Python e estatística: é o hábito, treinado em astronomia, de tentar derrubar o próprio resultado antes que o mercado derrube."

**English:**

> "I spent my undergrad and master's solving one problem: detecting tiny, rare, valuable drops in starlight — stellar occultations — buried in noise, where a false positive is expensive. I co-authored a paper in *Monthly Notices of the Royal Astronomical Society* measuring the moon Umbriel to kilometer precision, and built an ML pipeline to automate that triage. Then I realized financial markets are the same problem with a different dataset — weak signal, dominant noise, self-deception as the main risk. Today I'm a Quantitative Analyst at Transfero, covering risk, backtesting and data infrastructure for funds with roughly US$ 1 billion in annual volume. What I bring isn't just Python and statistics: it's the astronomy-trained habit of trying to kill my own result before the market does."

---

## 2. A narrativa de 2 minutos ("me fale sobre você")

A estrutura é um arco em três atos. Decore os atos, não o texto — a entrevista boa é conversa, não recital.

**Ato 1 — O problema que me formou (astronomia como treino, não como passado).**

> "Eu me formei em Astronomia na UFRJ e fiz mestrado no Observatório Nacional. Desde a iniciação científica trabalho com ocultações estelares: uma estrela pisca por segundos quando um corpo do Sistema Solar passa na frente, e nesse piscar dá pra medir um objeto a bilhões de quilômetros com precisão de quilômetros. Fui coautor do artigo sobre Umbriel no MNRAS. No mestrado, construí um pipeline de machine learning para achar esses eventos automaticamente em milhares de curvas de luz — os anéis de Quaoar, por exemplo, foram descobertos numa *revisita* de dados antigos; descoberta dormindo em arquivo é exatamente o que a ferramenta evita."

**Ato 2 — A ponte (por que mercado, e por que não foi um salto).**

> "No meio do mestrado entrei na Transfero como estagiário de Middle Office — comecei pelo encanamento de propósito: conciliação de caixa, NAV, contato com administrador e custodiante. Automatizei essas rotinas com Python e SQL e em pouco mais de um ano virei Analista Quantitativo Pleno. Hoje faço análise de risco e performance de fundos multimercado quant, backtests de estratégias e pipelines de dados em Azure — um deles acelerou a conciliação de NAV em mais de 60%. Tirei o CEA da ANBIMA no caminho. A transição fez sentido porque o problema técnico é o mesmo da astronomia: separar sinal de ruído quando o ruído é quase tudo e o incentivo pra se enganar é enorme."

**Ato 3 — O diferencial (o método como caráter).**

> "O que eu acho que me diferencia é o que eu faço quando um resultado parece bom. Meu reflexo, treinado na física, é perguntar 'onde eu me enganei?' antes de comemorar. Eu audito meu próprio trabalho por iniciativa — na tese, escrevi uma auditoria com dez achados críticos contra a minha própria pipeline antes de qualquer revisor. Em finanças, construí um pipeline de backtest que seguiu López de Prado à risca — purged cross-validation, embargo, Deflated Sharpe — e o resultado foi nulo. Eu documentei o nulo com orgulho, porque um sistema que diz 'não' de forma confiável é o que protege capital. É esse padrão que eu quero trazer pra cá."

---

## 3. Banco de histórias (formato STAR)

Cinco histórias, cada uma respondendo a famílias de perguntas clássicas. Treine cada uma em ~90 segundos falados.

### História 1 — Quaoar e a separação de 86× *(“conte um resultado do qual se orgulha”)*

- **Situação:** O pipeline da tese atingia F1 de 0,99 em teste — número que, sozinho, não convence ninguém sério.
- **Tarefa:** Provar que o modelo funcionava em dado real, adversarial, fora do treino.
- **Ação:** Apliquei o modelo à curva real de Quaoar (dados Gemini/Alopeke de Pereira et al. 2023), incluindo de propósito um recorte de **ruído que imita uma ocultação**.
- **Resultado:** O modelo separou o anel real do ruído-sósia por um fator de ~86× na probabilidade — recuperando os dois anéis sem nenhum falso positivo. A lição que eu conto: *o que importa não é a probabilidade absoluta, é a separação entre o sinal e o impostor.*

### História 2 — O null result celebrado *(“conte um fracasso” / “como você evita overfitting?”)*

- **Situação:** Construí por conta própria um pipeline completo de pesquisa de estratégias no padrão *Advances in Financial Machine Learning*: triple-barrier labeling, purged CV com embargo, CPCV, Deflated Sharpe corrigido pelo número de tentativas, block-bootstrap como modelo nulo.
- **Tarefa:** Encontrar alfa — ou provar que não havia.
- **Ação:** Rodei o protocolo inteiro sem afrouxar nenhuma salvaguarda quando os números vieram feios.
- **Resultado:** Sharpe dentro de um erro-padrão de zero, dentro e fora da amostra. Registrei como resultado negativo publicável. A frase que resume: **"a virtude do pipeline não é achar alfa; é ser patologicamente conservador — quando ele diz 'não', é 'não' de verdade."** Noventa por cento da pesquisa quant honesta dá nisso; o valor está em saber *com certeza*.

### História 3 — A auditoria contra mim mesmo *(“como você revisa seu trabalho?” / “qual seu maior defeito?”)*

- **Situação:** Tese pronta, métricas excelentes, ninguém cobrando nada.
- **Tarefa:** Nenhuma — e é esse o ponto.
- **Ação:** Escrevi uma auditoria formal da minha própria pipeline com **dez achados críticos**, com arquivo e linha: risco de vazamento de metadados entre treino e teste, dependência de uma única semente aleatória, conjunto de teste consultado mais de uma vez. Depois, executei o teste que faltava — um baseline trivial de um único limiar — e descobri que ~90% do meu F1 de 0,99 vinha "de graça" da parte fácil do problema; o ML se pagava no resto (cortava o erro ~10×), mas o número cheio superdimensionava a dificuldade.
- **Resultado:** Correções incorporadas antes da defesa. Sobre defeito: a versão honesta é que meu tom público tende ao otimismo enquanto meu rigor privado é brutal — estou treinando deixar o auditor assinar o documento oficial.

### História 4 — O placebo no experimento *(“me dê um exemplo de ceticismo estatístico”)*

- **Situação:** Num estudo de detecção de regimes de mercado, um modelo com acurácia de ~51% exibia Sharpe médio suspeito de +0,13 em CPCV.
- **Tarefa:** Explicar o número bom demais em vez de aceitá-lo.
- **Ação:** Testei cada feature contra **dois modelos nulos** (random walk e retornos embaralhados), classifiquei tudo em genuíno/marginal/artefato — e plantei uma **feature de controle** no experimento, um placebo para fiscalizar o próprio fiscal. Encontrei um falso positivo do Probabilistic Sharpe Ratio.
- **Resultado:** O sinal aparente morreu; o protocolo sobreviveu e virou padrão dos meus estudos. Uma feature pode ser *real* (diferente do acaso) e ainda assim *inútil* (pequena demais para importar) — distinção que separa pesquisa de curve-fitting.

### História 5 — O NAV 60% mais rápido *(“que valor de negócio você já gerou?”)*

- **Situação:** Conciliação diária de posições, caixa e NAV da Transfero dependia de rotinas manuais lentas, em fundos com volume anual próximo de US$ 1 bilhão.
- **Tarefa:** Reduzir tempo, erro operacional e dependência de gente apertando botão.
- **Ação:** Projetei e implantei pipelines ETL em Azure (Functions, CosmosDB, SQL, Python) integrando administradores, corretoras e custodiantes.
- **Resultado:** Conciliação de NAV **mais de 60% mais rápida**, menos trabalho manual, mais auditabilidade — e foi essa entrega, começada como estagiário de Middle Office, que me levou a Analista Quantitativo Pleno em ~15 meses. Moral da história para o entrevistador: eu não desprezo o encanamento; alfa nenhum sobrevive a operação ruim.

---

## 4. Perguntas-armadilha e como respondê-las

**"Por que você deixou a astronomia?"**
Nunca responder com desculpa ou nostalgia. Resposta: *"Eu não deixei o método — mudei o dataset. O problema técnico da minha carreira sempre foi o mesmo: sinal fraco, raro e valioso dentro de ruído dominante, com custo alto de falso positivo. Ocultação estelar e alfa de mercado são o mesmo problema. E o mercado tem uma vantagem: o experimento responde todo dia."*

**"Você nunca trabalhou em banco grande / fundo tradicional."**
Não se defender — reenquadrar: *"É verdade, e foi escolha. Na Transfero eu vi o fundo inteiro por dentro — do custodiante ao backtest — em vez de uma célula de uma mesa. Sei o que acontece com uma estratégia depois que ela sai do notebook do pesquisador: conciliação, NAV, liquidez, regulação. Pesquisador que conhece a operação escreve backtest mais honesto."*

**"Seus modelos se abstêm demais / são conservadores demais. Isso escala?"**
(A crítica do Simons — vai aparecer, de uma forma ou de outra.) Conceder e virar: *"Crítica justa. Um modelo que diz 'não sei' em 91% dos casos está certo em cada caso e insuficiente como sistema — retorno é edge vezes frequência. A resposta não é afrouxar o cético, é multiplicar as apostas: muitos sinais fracos e independentes, somados. Provar que um sinal sozinho não basta foi o passo um; industrializar a soma de sinais é exatamente o trabalho que eu quero fazer aqui — e é trabalho de equipe, não de pesquisador solitário."*

**"Sharpe acima de 10 no seu CV — não é bom demais pra ser verdade?"**
Jamais se ofender; essa pergunta é um presente. *"Se eu visse esse número num backtest, eu mesmo desconfiaria — meu primeiro reflexo diante de número perfeito é 'onde me enganei?'. No caso, são fundos exclusivos com estratégias específicas em cripto, num regime de mercado particular, e eu sou parte da equipe que monitora, não o autor da mágica. Número extraordinário exige ceticismo extraordinário — inclusive no meu próprio CV."* (Quem responde assim demonstra o rigor que a pergunta testava.)

**"Qual seu maior defeito?"**
Usar a resposta da História 3 — verdadeira, específica, documentada: otimismo no tom público vs. rigor no privado; e organização de repositório que historicamente não acompanhou o rigor estatístico (commits pobres, versões manuais) — com o que já mudou a respeito. Defeito real + correção em andamento vale dez "sou perfeccionista".

---

## 5. O que NUNCA dizer

1. **Número triunfante sem o ceticismo junto.** Nunca citar "F1 de 0,99" ou "Sharpe 10" sem a segunda frase que interroga o número. A regra: *todo resultado entra na conversa já acompanhado do seu teste de estresse.* Dito sozinho, o número perfeito depõe contra você.
2. **Prolixidade.** O padrão identificado na tese — repetir a conclusão três vezes, em negrito — mata uma entrevista. Responder e **parar de falar**. Silêncio depois de uma boa resposta é o entrevistador pensando, não um vazio a preencher.
3. **Pedir desculpas pela academia.** "Eu sei que sou muito acadêmico, mas..." — proibido. A formação científica é o produto, não o defeito de fábrica.
4. **Esconder limitação até ser perguntado.** A assinatura do Thiago — nos melhores artefatos do portfólio — é *liderar* com a limitação ("três negativos reais são poucos; eis o que fiz a respeito"). Em entrevista, quem apresenta a fraqueza primeiro controla a narrativa dela.
5. **Clichês de RH.** "Proativo", "hands-on", "apaixonado por dados", "fora da caixa". Cada um desses tem uma história concreta do portfólio que o substitui. Conte a história.

---

## 6. Fechamento da entrevista

Quando vier o "você tem alguma pergunta?", fazer **esta**, que sinaliza cultura de pesquisa madura:

> "Como vocês tratam resultado negativo aqui? Quando um pesquisador passa dois meses numa hipótese e o protocolo diz 'não há sinal' — isso é documentado e valorizado, ou é dois meses perdidos? Pergunto porque a qualidade dos 'nãos' de uma equipe é o que eu aprendi a usar como termômetro do rigor dos 'sins'."

E, se houver espaço para uma frase final, é esta — a síntese das três homenagens:

> "O que eu ofereço é o hábito que a astronomia me deu e que o mercado paga caro para ter: **tentar com força provar que estou errado — e não conseguir.**"

---

*Documento preparado a partir do portfólio público ([github.com/TLaidler](https://github.com/TLaidler)), do CV (artigo MNRAS sobre Umbriel; Transfero Asset Management, Middle Office jan/2024 → Analista Quantitativo Pleno abr/2025; CEA-ANBIMA) e das avaliações ficcionais de Feynman, Sagan e Simons registradas neste repositório.*
