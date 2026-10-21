# Comentários Lillian (pesquisadora de IA e machine learning com formação em física):

- Escrita muito informal pra uma dissertação
- senti falta de mais interpretação da regressão logística
- Em geral a fonte das figuras estava muito pequena, é necessário refaze-las com letras maiores
- T-student de cada quartil? Não faz muito sentido -> comparação de médias...

Figura 2.2 (d) -> recortar parte da legenda fora (manual-> exige o usuário fazer)

- Citar Grupo do Rio sem contextualizar o que é
- figura 2.3 chamou difração de Fresnel de azul quando está de preto.
figura 2.4 -> explicitar que imagens são retiradas do artigo assafin et al, 2023

Capitulo 3 -> falta de padronização com uso de " aspas (algumas aspas são diferentes) e travessões 
-> "taxonomia" é uma palavra que não cola bem aqui, trocar por "classificação"
- > exemplos de ML supervisionado/não supervisionado -> não citou nenhum exemplo da astronomia.

- "Os parâmetros são estimados pelo método dos mínimos quadrados, que contitui o primeiro exemplo de algoritmo de otimização..." mudar "são" para "podem ser". 
- "O modelo prediz ... com X a matriz d dados..." -> X na fórmula do y não está em bold/itálico 
- "... por uma função sigmoide e utiliza o custo de entropia cruzada, para o qual não existe solução fechada..." substitua fechada por analítica
- "O que podemos ver é a reta de regressão pode sofrer..." -> "é que ..."
- A minimização de J(theta) não define a variável m antes. Não faz sentido. 
- Verificar exemplos numéricos de iteração
- termos em inglês devem fcar em itálico (como overfitting, underfitting e etc)

Capitulo 4 
(para o usuário apenas) -> senti falta de ver algumas curvas do dataset aqui
- formulas de estatística de fluxo como média/DP precisam estar com ^ 

Capitulo 5
GRAVE: "...cujo desempenho foi medido eclusivamente no conjunto de teste..." -> não se deve comparar no teste
"Experimento 3: 11 features, porém com teste somente em curvas reais..." -> os outros dois poderiam ser avaliados nesse teste também. 
"os pares identificados são apresentados a seguir." -> devia ver o gráfico de correlação entre features -> inclusive há uma tabela que pode ser retirada e substituída pelo gráfico de dispersão corr -> ficaria mais limpo e tão informativo quanto. 
- discordo que o experimento 3 seja um experimento separado por si só -> é uma vertente do segundo experimento -> reflita sobre a renomeação e reclassificação desses experimentos-> reorganize no projeto
- há citação do endereço da pipeline e pastas com script, mas não há no apêndice o link para o repositório público no GitHub ( https://github.com/TLaidler/pipeline_occ_ml)
- deixar explicito que a curva de quaoar foi retirado de Pereira et al, 2023 na legenda (invés de apenas cita-lo)
- "aqui está o ponto sutil" -> muito informal
- "A janela não é a causa." -> de que?  
- "-ou seja, ampliar a janela tornou o veredito negativo ainda mais forte." ??
- fonte dos gráficos de feature importance estão muito pequenos -> sugiro escolher os 5 mais importantes e aumentar a fonte, já que quer mostrar 4 gráficos em uma janela de figura. 
- "validação cruzada estratificada" -> devida ter sido feito desde o início
- "O procesimento é simples." -> muito informal. 
- Diminua ao jargões e informalidade. Seja direto ao ponto.
- teste de mcnemar entre modelos -> distribuição X2 com grau 1 de liberdade sob a hipótese nula -> não cola se b+c for muito pequeno, que é o caso.
