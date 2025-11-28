## Visão geral

Este script gera curvas de luz sintéticas de ocultações estelares “pós-fotometria”, combinando:
- Difração de Fresnel nas transições de imersão/emersão do corpo principal.
- Contribuições opcionais de anéis (opacidade parcial) e de um satélite (ocultação secundária).
- Efeitos atmosféricos (cintilação/seeing) e ruídos instrumentais.
- Conversões fotométricas (magnitude → fluxo; fluxo → fótons) e normalização do nível fora da ocultação para ≈ 1.

O objetivo é aproximar o que seria esperado observar para um corpo específico, dadas propriedades geométricas (diâmetro, distância, velocidade do evento) e condições observacionais (banda, tempo de exposição, seeing, etc.).


## Componentes principais

### 1) Fotometria e conversões
- Conversão magnitude → fluxo (escala relativa) usando a relação fotométrica padrão:

\[ F \propto 10^{-0{,}4\,m} \]

- Conversão fluxo → contagem de fótons (usando a energia do fóton \(E = h c / \lambda\)).

Essas rotinas são usadas para escalonar a taxa de fótons observados e, posteriormente, injetar ruídos (Poisson, leitura e cintilação).


### 2) Escala e difração de Fresnel
- A escala de Fresnel é dada por:

\[ F = \sqrt{\frac{\lambda\,D}{2}} \]

onde \( \lambda \) é o comprimento de onda efetivo e \( D \) a distância ao objeto. O código calcula esta escala e usa integrais de Fresnel (SciPy) para modelar o perfil difrativo de uma “faixa” opaca (imersão/emersão).

Trecho que calcula a escala de Fresnel (distância em km, comprimento de onda convertido para km):

```89:111:model_training/synthetic_curve/simulate_curveC&P.py
def calc_fresnel(distance, bandpass):
    """Calculates the Fresnel scale.

    Fresnel Scale = square root of half the multiplication of wavelength and
    object distance.
    """
    bandpass = bandpass*ang_km
    distance = distance*ua
    return np.sqrt(bandpass * distance / 2)
```

Modelo de “faixa” com dois knife-edges (imersão/emersão) usando as integrais de Fresnel de SciPy:

```138:156:model_training/synthetic_curve/simulate_curveC&P.py
import scipy.special as scsp
...
fresnel_scale = calc_fresnel(distance,bandpass)
x = X / fresnel_scale
x01 = X01 / fresnel_scale
x02 = X02 / fresnel_scale
x1 = x - x01
x2 = x - x02
s1, c1 = scsp.fresnel(x1)
s2, c2 = scsp.fresnel(x2)
cc = c1 - c2
ss = s1 - s2
r_ampli = - (cc + ss) * (opacity / 2.)
i_ampli = (cc - ss) * (opacity / 2.)
flux_fresnel = (1.0 + r_ampli) ** 2 + i_ampli ** 2
```

Comentários:
- A transmissão difrativa de uma borda é construída com as integrais de Fresnel \(C(u), S(u)\).
- Para uma “faixa” opaca (corpo), combinam-se duas bordas, gerando o padrão com franjas próximas às transições.


### 3) Turbulência atmosférica (seeing) e cintilação

O script escolhe um conjunto empírico de parâmetros atmosféricos a partir do seeing e deriva grandezas como \(r_0\) e variância de irradiância. A cintilação é modelada como ruído multiplicativo (lognormal), reduzida por tempos de exposição mais longos e abertura do telescópio.

Comentários:
- O modelo é heurístico/simplificado; serve para dar ordem de grandeza do efeito.
- A variância de irradiância depende de integrais de \(C_n^2\) (perfís verticais) e de fatores de “aperture averaging”.


### 4) Geometria da ocultação e linha do tempo
- Define-se o tempo de simulação e a coordenada ao longo da corda \(X(t) = v\,t\).
- Início/fim da ocultação principal são obtidos do diâmetro projetado e da velocidade do evento.
- Anéis e satélite são representados como faixas adicionais (opacidade parcial para anéis; opacidade total para satélite), com seus pares de bordas (imersão/emersão).

Combinação de curvas ópticas (corpo, anéis, satélite) por multiplicação das transmissões:

```870:876:model_training/synthetic_curve/simulate_curveC&P.py
Fres=bar_fresnel(Xs,X01,X02,1,distancia,band)
...
Fres_tot = (Fres*Fres_sat*Fres_an1*Fres_an2*Fres_an3*Fres_an4)
plt.plot(times,Fres_tot, 'o-',color='black',linewidth= 0.7,markersize=2.3)
```


### 5) Síntese observacional (ruído) e normalização pós-fotometria
- Em cada exposição, integra-se o fluxo esperado (considerando o estado geométrico e difração) e injeta-se ruído (Poisson, leitura, cintilação).
- A curva é normalizada para que o nível fora da ocultação fique ≈ 1 (pós-fotometria). Exemplo do procedimento de normalização usado no script atual:

```904:931:model_training/synthetic_curve/simulate_curveC&P.py
med=np.median(flua[0:40])
for i in range(len(flua)):
    flua[i]=flua[i]/med
...
Flua_fresn=[]
for j in range(len(Flua_fres)):
    Flua_fresn.append(Flua_fres[j]/med)
```

Comentários:
- No reprocessamento moderno, recomenda-se estimar o baseline com robustez (ex.: mediana global ou média dos dois melhores quartis fora da ocultação).


## Como usar para “pós-fotometria”
- Ajuste os parâmetros geométricos do corpo (diâmetro projetado, distância) e a velocidade do evento para o seu caso.
- Configure a banda/λ e o tempo de exposição (amostragem temporal) para aproximar o seu setup.
- Anéis: defina posições (início/fim) e opacidades; Satélite: offset e diâmetro.
- Seeing e diâmetro do telescópio controlam a força da cintilação e do ruído.
- Analise a curva final normalizada (fora da ocultação ~ 1) como faria com dados pós-fotometria reais.


## Limitações observadas
- Mistura de unidades e constantes em alguns trechos; vários prints/trechos experimentais.
- Há bugs pontuais (ex.: `==` no lugar de `=` em algumas atribuições; referência a `self.d_star` fora de classe).
- Uso de variáveis globais e loops não vetorizados (impacto em desempenho e clareza).
- Modelo atmosférico simplificado (heurístico) e normalização que pode ser tornada mais robusta.


## Recomendações
- Migrar para uma classe modular com parâmetros explícitos, docstrings e unidades consistentes.
- Usar um baseline robusto para normalização e vetorização para desempenho.
- Separar nitidamente: “ótica/física” (difração, geometria) vs “detector/atmosfera” (ruídos).


### Como o simulador funciona:

Ele tenta gerar curvas de luz sintéticas de ocultações estelares, combinando:
Difração de Fresnel nos instantes de imersão/emersão do corpo principal.
Contribuições opcionais de anéis (opacidade parcial) e de um satélite (ocultação secundária).
Efeitos atmosféricos (cintilação/seeing) e ruídos instrumentais.
Conversões fotométricas simples (magnitude → fluxo; fluxo → fótons).
Normalização “pós-fotometria” (trazendo o nível de fora da ocultação para ≈1).
Plots da curva resultante.
A ideia é aproximar o que você esperaria observar para um corpo específico, dados diâmetro, distância, velocidade do evento, anéis, etc.
Blocos principais do código
Fotometria e conversões
Fluxo_lambda(magnitude): aproxima o fluxo em função da magnitude da estrela.
fluxo_fotons(fluxo, lamb): converte fluxo em contagem de fótons.
Algumas variantes tentam injetar ruído lognormal na irradiância para simular cintilação.
Escala e difração de Fresnel
calc_fresnel(distance, bandpass): calcula a escala de Fresnel 
F
=
λ
D
/
2
F= 
λD/2
​
  para distância do corpo e comprimento de onda efetivo.
bar_fresnel(X, X01, X02, opacity, distance, bandpass): modelo de faixa (bar) com dois “knife-edges” (imersão/emersão) usando integrais de Fresnel de SciPy para gerar o perfil de difração:
simulate_curveC&P.pyLines 138-156
    import scipy.special as scsp    ...    s1, c1 = scsp.fresnel(x1)    s2, c2 = scsp.fresnel(x2)    cc = c1 - c2    ss = s1 - s2    r_ampli = - (cc + ss) * (opacity / 2.)    i_ampli = (cc - ss) * (opacity / 2.)    flux_fresnel = (1.0 + r_ampli) ** 2 + i_ampli ** 2
Turbulência atmosférica e seeing
A partir de um valor de seeing, escolhe um perfil empírico de turbulência (coeficientes A, B, C, D e escalas de altura) e obtém grandezas como r0, variância de fase e variância de irradiância. Isso determina a intensidade da cintilação (ruído multiplicativo).
Usa integrais e fatores de atenuação de abertura para estimar a variância da irradiância (modelo de Saha/Hardy/Tyson em versões simplificadas).
Ruídos instrumentais
Funções esboçadas para ruído térmico e de leitura; em outras rotinas o ruído é injetado via Poisson (contagem de fótons) e ruído lognormal (cintilação).
Geometria da ocultação e linha do tempo
Define o tempo de simulação, o vetor temporal times e a coordenada ao longo da corda Xs = v * t.
Determina início/fim da ocultação principal a partir do diâmetro do corpo e da velocidade.
Define segmentos para anéis (com opacidade parcial) e, se desejado, um satélite (offset e diâmetro), criando pares (X01, X02) para cada “faixa” que cruza a estrela.
Geração das curvas “ópticas” (sem ruído) e combinação
Calcula curvas de Fresnel para corpo principal, anéis e satélite; depois multiplica tudo para obter a transmissão total:
simulate_curveC&P.pyLines 870-879
Fres=bar_fresnel(Xs,X01,X02,1,distancia,band)...Fres_tot = (Fres*Fres_sat*Fres_an1*Fres_an2*Fres_an3*Fres_an4)plt.plot(times,Fres_tot, 'o-', ... )plt.title("Simulação com Difração de Fresnel")
Síntese de observação com ruído e normalização
Em um laço temporal, integra o fluxo observável em cada exposição, aplicando o “estado” geométrico (dentro/fora do corpo, anel, satélite) e ruídos.
Normaliza a curva para que a média/mediana fora da ocultação fique ≈1:
simulate_curveC&P.pyLines 904-931
med=np.median(flua[0:40])for i in range(len(flua)):    flua[i]=flua[i]/med...Flua_fresn=[]for j in range(len(Flua_fres)):    Flua_fresn.append(Flua_fres[j]/med)
Visualização
Plota e salva figuras (curvas de Fresnel individuais e a curva final normalizada).
Como os parâmetros controlam a curva
Corpo principal
diametro_corpo, distancia, vel (velocidade do evento) → definem começo/fim da ocultação e o espaçamento das franjas (via Fresnel).
Anéis
Conjuntos início/fim e opacidades → criam atenuações parciais adicionais (franjas mais suaves).
Satélite
Offset e diâmetro → gera uma pequena ocultação separada com sua própria difração.
Observação
tempexp (tempo de exposição) e banda band → definem amostragem e a escala de Fresnel.
diam_teles, readout_noise, temperatura → afetam contagem e ruído.
Seeing → controla a cintilação (ruído multiplicativo).
O que usar para “pós-fotometria”
A pipeline faz a normalização final (fora da ocultação ≈1), então o resultado imita uma curva “pós-fotometria”.
Para um corpo específico: ajuste diametro_corpo, distancia, vel, posição dos anéis/satélite e band. Ajuste tempexp para o seu cadence e seeing/diam_teles para o local/instrumento.
Limitações e cuidados
Há problemas de implementação:
Mistura de unidades e constantes; várias prints/experimentos deixados no código.
Trechos com bug de atribuição (== onde deveria ser =) e referência a self.d_star em contexto sem classe.
Uso extensivo de variáveis globais; funções redundantes e loop não vetorizado (lento).
Cientificamente, o cerne (difração de Fresnel × geometrias de faixas) está no caminho certo, mas:
A física da atmosfera está muito simplificada/heurística.
A normalização e a soma com ruído poderiam ser mais consistentes e vetorizadas.