# Plano Esmeralda — Hutake#BR1

**Alvo:** Esmeralda 4 na conta Hutake#BR1 até 31/01/2027
**Ponto de partida:** Prata 1, 8 LP (elo_point 1532) — 21/09/2026
**Janela:** 132 dias = 18,9 semanas
**Probabilidade estimada com adesão total:** 35–45%

> Este plano foi derivado de 40 partidas ranqueadas coletadas das contas Hutake#BR1 e
> Hipparcos#BR1, da tier list do patch 16.18.1 (BR) e do histórico de LP das duas contas.
> Toda regra aqui existe porque um número a justifica. Os números estão junto.

---

## 1. Veredito honesto

Esmeralda até janeiro é **possível, mas está no limite**. O resultado ~75% provável é
Ouro 1 / Platina 4. O plano abaixo é desenhado para maximizar a chance de Esmeralda, não
para prometê-la.

O que puxa a probabilidade para baixo: depois da inserção do Esmeralda em 2023, o alvo
fica **1–2 divisões acima do pico histórico do jogador** (Ouro, em 2021). Não é voltar ao
que era — é superar, com 5 anos de ferrugem e menos de 1 mês de retorno.

O que puxa para cima: a inclinação de melhora já está medida. Nas 10 partidas mais
recentes contra as 10 anteriores (Hipparcos): OP score 4,16 → 5,27, participação em
abates 38% → 51%, mortes 6,3 → 5,0. Sem intervenção nenhuma.

### O tamanho do salto (distribuição do BR, 1.169.773 ranqueados — `rank_dist.py`)

| Marco | Percentil acumulado |
|---|---|
| Prata 2 (nível real estimado) | top 70% → **percentil ~30** |
| Prata 1 (rank exibido da Hutake) | top 65% → percentil ~35 |
| Lobbies que o matchmaking já entrega (Ouro 2–4) | percentil ~40–55 |
| Ouro 3 — **mediana do BR** | top 52% |
| Platina 4 | top 37% |
| **Esmeralda 4 — o alvo** | **top 18,10%** |

O plano pede passar por **~47% de toda a população ranqueada do BR** em 19 semanas. É o que
sustenta a estimativa de 35–45%, e não mais.

Nota de leitura: o rank exibido **subestima** o jogador — o matchmaking já o coloca em
lobbies de percentil 40–55 enquanto o LP marca percentil 35. É esse descasamento que a
fase 1 gasta primeiro.

---

## 2. A matemática que manda em tudo

Prata 1 → Esmeralda 4 são **9 divisões ≈ 900 LP líquidos**.

| WR sustentada | Jogos necessários | Jogos/semana |
|---|---|---|
| 50% | nunca | — |
| 52% | 802 | 42,5 |
| **55%** | **343** | **18,2** |
| **57%** | **253** | **13,4** |
| 60% | 183 | 9,7 |
| 63% | 145 | 7,7 |

*(Fase 1 assume ganho assimétrico +25/−15 até ~Ouro 3, porque o MMR da conta está acima
do rank exibido. Depois disso, +20/−20. Ver `plan_math.py`.)*

O jogador faz hoje ~35 ranqueadas por semana. **Volume não é o gargalo em nenhum cenário
acima de 52% — sobra o dobro do necessário. A taxa de vitória é o gargalo.**

A curva é brutalmente não-linear entre 52% e 57%: é a diferença entre inviável e
confortável. Por isso **cada elemento deste plano é julgado por uma única pergunta: isso
move a taxa de vitória?** Nada entra por parecer treino.

### Linha de base medida (Hutake, últimas 19 ranqueadas)

```
elo_point 1532  (S 1, 8 LP)
->  mortes <= jungler inimigo :  42%   meta >= 60%
->  vitorias                  :  42%   meta >= 55%
->  share de dano do time     : 11.4%  meta >= 18%
->  jogos na pool travada     :   0%   meta >= 90%
->  maior sessao do periodo   :   9    meta <=  3 jogos/dia
    mortes por jogo           :  5.9
```

Cinco de cinco métricas fora da meta. Isso é bom: significa que há muito ganho barato
disponível antes de precisar de qualquer melhora fina de habilidade.

---

## 3. Pool travada — calibrada ao patch 16.18.1

Dados reais da tier list do op.gg (BR), extraídos com `meta_pool.py`.

| Campeão | Ouro | Esmeralda | Ban | Leitura |
|---|---|---|---|---|
| **Trundle** | 52,4% (#24) | **55,0% (#16, tier 2)** | 0,5–0,9% | Melhora com o elo. Ninguém bane. Já foi pool dele em 2021. |
| **Warwick** | 52,9% (#6, tier 1) | 52,7% (#6, tier 2) | 1,9–5,1% | Estável nas duas faixas. Menor perfil de morte do arquétipo. |
| Sejuani | 53,1% | 53,0% (#11) | 0,3–0,5% | Estável, invisível ao ban. Dano baixo conflita com "carry". |
| Udyr | 52,0% | 51,9% (#9) | 1,4–2,8% | Power farm puro, simples, estável. |
| Shyvana | 53,7% (#5, tier 1) | **50,4% (#14)** | 4,2% | Ótima no Ouro, degrada no alvo. |
| Master Yi | 52,3% (tier 1) | 51,8% (tier 1) | **29,6 → 33,3%** | Banido em 1 de cada 3 jogos. |
| Rammus | 56,3% (#1) | 54,7% (#1) | 13,0% | Melhor do jogo, mas tanque puro — fora da filosofia. |
| **Jax** | **49,2% (#20, tier 3)** | **48,5% (#42, tier 4)** | 12–14% | Abaixo da média, e piora rumo ao alvo. |
| Hecarim | 46,7% | 46,4% | — | Armadilha. |
| Xin Zhao | 51,2% | **45,9%** | — | Desaba no alvo. |

### A pool

| Campeão | Fatia | Motivo |
|---|---|---|
| **Trundle** | **70%** | Único campeão com resultado pessoal comprovado (5V-2D; 83% quando não morre mais que o jungler inimigo). Único da lista que **melhora** rumo ao Esmeralda. Ban abaixo de 1% — nunca some do pick. |
| **Warwick** | **25%** | Escolhido por uma razão específica: o problema nº 1 é morrer, e Warwick tem o compromisso mais barato do arquétipo (E dá redução de dano no mergulho e medo na saída, Q cura, gank pré-6 é reversível). Estável 52,7–52,9%. |
| **Sejuani** | **5%** | Só contra composições sem engage. Opcional. |

> **Níveis de confiança diferentes — leia antes de travar a pool.**
> **Trundle é recomendação medida:** 7 partidas do próprio jogador (5V-2D, 83% em estado
> bom) + dado de patch. **Warwick é recomendação raciocinada:** o dado de patch é firme,
> mas o encaixe no perfil dele é inferência a partir do design do campeão — ele nunca
> jogou Warwick nesta amostra.
>
> **Teste de 10 jogos.** Jogue 10 Warwicks e rode o `scorecard.py`:
> - diferencial de mortes ≤ 0 em **≥60%** → confirmado, siga;
> - abaixo disso → a inferência estava errada. Troque por **Sejuani** (compromisso ainda
>   menor: R é skillshot de longe) e aceite atacar o share de dano só na fase 3.

### Escada de compromisso

O Warwick **não** é um Trundle equivalente — ele cobra aluguel na mesma moeda, em parcela
menor: **Trundle < Warwick << Jax**. Isso é de propósito. Um pool só de Trundle ensina a
nunca entrar na luta, o que trava o share de dano em 11% para sempre. A fase 2 existe para
treinar compromisso controlado, e o Warwick é o degrau calibrado para isso.

**Udyr** (52,0% / 51,9%, ban 1,4–2,8%) é o candidato da **fase 3**: power farm puro, dano
real, casa com a filosofia — mas o padrão de luta é andar em cima do alvo sem gap closer,
compromisso alto de outro tipo. Cedo demais na fase 2.

### Como ler a tabela acima

O `rank` e o `tier` do op.gg são compostos — misturam WR com pick rate e ban rate, então
penalizam campeão pouco jogado. No Esmeralda o Trundle tem WR **maior** que o Warwick
(55,0% vs 52,7%) e rank **pior** (#16 vs #6), só porque tem 1,00% de pick contra 4,20%.
**Para escolher pool, olhe WR e ban rate; ignore o rank.**

**Fora da pool ranqueada:** Jax, Master Yi, Shyvana, e todo o resto.

Evidência: na Hipparcos, **fora da pool = 2V-11D (15%)**; dentro da pool = 5V-2D (71%).

### Sobre o Jax

O Jax está de fato abaixo da média (49,2% no Ouro, 48,5% no Esmeralda) — um imposto de
**~1 ponto de WR**. Mas o desempenho pessoal nele é **36%**, um déficit de 13 pontos.
**O campeão explica cerca de 1/13 do buraco.**

O teste que prova isso — mesmo campeão, mesmo patch, só mudando o diferencial de mortes
contra o jungler inimigo:

| | Morreu ≤ que o jungler inimigo | Morreu mais |
|---|---|---|
| **Jax** | **5V-2D (71%)** | 1V-10D (9%) |
| Master Yi | 3V-1D (75%) | 0V-5D (0%) |
| Trundle | 5V-1D (83%) | 0V-1D (0%) |
| **Todos** | **13V-4D (76%)** | **1V-18D (5%)** |

Jax dá 71% de vitória quando o diferencial de mortes não é negativo. Um campeão fraco não
faz 71%. E o dano por minuto do jogador é **maior no Trundle (532) do que no Jax (442)** —
se fosse só potência de patch, o carry ainda daria mais dano que o utilitário.

**Conclusão:** o Jax não está fraco. Ele **cobra exatamente a habilidade que falta**
(entrar em luta e sobreviver). O Trundle deixa jogar o mesmo macro sem esse compromisso.
A troca está certa; o motivo não era o patch.

### Sobre a Shyvana

O instinto está bem calibrado para o Ouro (53,7%, tier 1, #5) e mal calibrado para o alvo
(50,4%, #14). Ela também repete o perfil de risco do Jax: o payoff é entrar de ult em
teamfight tardio — exatamente o buraco. **Deixar para depois do Esmeralda**, ou jogar na
conta laboratório.

---

## 4. As duas correções que são o plano inteiro

### 4a. Diferencial de mortes — a métrica número um

**Estado atual:** 42% dos jogos com diferencial ≤ 0. **Meta: 60%.**

O dado: morreu ≤ que o jungler inimigo → **76% de vitória**. Morreu mais → **5%**.
Isso classifica 36 de 39 partidas do conjunto.

> **Ressalva estatística:** morrer menos também é *consequência* de estar ganhando, não só
> causa. Por isso a métrica é o **diferencial contra o jungler inimigo** — mesma partida,
> mesma rota, mesmo tempo, mesmo elo — e não mortes absolutas. Isso reduz muito o
> problema, mas não o elimina. O que sobrevive limpo é a invariância entre campeões.

**Protocolo de etiquetagem — 10 minutos por jogo, numa planilha.**
Para cada morte, classifique em um dos cinco baldes:

1. Invadido / acampamento contestado sem visão
2. Gank sem prioridade de rota
3. Objetivo contestado em desvantagem numérica
4. Entrada errada em teamfight (entrou primeiro, ou sozinho)
5. Rotação / splitpush sem visão

Depois de 20 jogos há uma distribuição. **Ataque o maior balde e ignore os outros.**

### 4b. Share de dano — o buraco do teamfight

**Estado atual:** 11,4% (Hutake), 13,8% (Hipparcos). **Meta: ≥18%.**
Um jungler bruiser/carry deveria ficar em 20–25%.

O número revelador: nas **vitórias** o share cai para 11,3%; nas **derrotas** sobe para
15,2%. Ou seja — ele ganha farmando e não morrendo enquanto o time briga, e perde quando
precisa ser a fonte de dano. A filosofia declarada ("alto impacto, bruiser ou carry") e a
execução estão descoladas: 11% é perfil de tanque utilitário.

**Regra concreta no Trundle: pilar primeiro, entrar segundo.** O pilar é o que transforma
o Trundle em iniciador sem compromisso — é exatamente a mecânica que permite participar da
luta sem o risco que o Jax cobra.

---

## 5. Full clear cronometrado

**Dose a expectativa:** pelos dados, o clear é **~15% do buraco**. O ΔCS/min contra o
jungler inimigo é −0,9 no Jax e **+0,4 no Trundle** — no campeão certo ele já farma no
nível do oponente. Os outros 85% são morte e teamfight. Por isso o clear entra
time-boxed, não como peça central.

**Protocolo — 2× por semana, 10 minutos, Practice Tool:**

1. **Semana 1 — linha de base.** 5 clears completos por campeão. Registre a mediana de
   três números: tempo em que o 6º acampamento morre, **% de vida no fim**, nível alcançado.
2. **Semanas 2–4 — bater a si mesmo.** Meta: **−15 segundos** sobre a própria mediana,
   sem perder mais vida. Não persiga número de internet: o tempo certo depende de patch e
   campeão. Referência de sanidade apenas: um full clear limpo de 6 camps costuma fechar
   entre **3:15 e 3:30**; com escuteiro, entre **3:45 e 4:00**. Se está muito fora, o
   problema é kite. Se está dentro, pare de otimizar.
3. **Semanas 5+ — a parte que importa.** Mesmo tempo, mas com restrição: terminar com
   **≥70% de vida** e, ao acabar o clear, tomar a decisão certa em 3 segundos (gank /
   objetivo / invadir), lida a partir do estado das três rotas.

**O clear não é a habilidade. O que se faz às 3:30 é.** Um clear 10 segundos mais rápido
que termina numa decisão errada é pior que um clear lento que termina na certa.

---

## 6. Regras de sessão — o ganho mais barato do plano

**Dado medido:** jogos 1–2 do dia = **53% de vitória**. Jogo 3 em diante = **25%**.

- **Máximo 3 ranqueadas por dia.**
- **Duas derrotas seguidas encerram o dia.** Sem exceção, sem "só mais uma".
- **5 dias por semana** → 15 jogos/semana, exatamente a faixa que os cenários de 55–57%
  exigem.

Jogar menos aqui não é conservadorismo: **os jogos 3+ têm valor esperado negativo em LP.**

### Divisão de contas

| Conta | Papel |
|---|---|
| **Hutake** | Ranqueada séria. Pool travada. Regras de sessão. É onde está o MMR com 2,5 divisões de vantagem — **e ele vale mais hoje do que em qualquer data futura**. |
| **Hipparcos** | Laboratório. Jax como treino de controle, testes de Shyvana, campeão novo. Sem meta de elo. |

**Por que nesta ordem:** o elo_point da Hutake é 1532 contra 1391 da Hipparcos — 141
pontos ≈ **2,5 divisões de vantagem**, hoje. Quando a Hipparcos chegasse a Ouro 1 (~1812),
a Hutake estaria 280 pontos atrás; voltar para ela seria rebaixamento, não impulso. O
ativo é real, mas **decai a zero exatamente quando se planejava usá-lo**. Por isso é gasto
primeiro.

---

## 7. Calendário

| Fase | Semanas | Jogos | Alvo de elo | Métrica única em foco |
|---|---|---|---|---|
| **0 — Instalar** | 1–2 | ~30 | Prata 1 → Ouro 4 | Pool ≥90%, sessão ≤3/dia |
| **1 — Cobrar o MMR** | 3–5 | ~45 | Ouro 4 → Ouro 3 | Só não tiltar; o MMR faz o trabalho |
| **2 — Morte zero** | 6–10 | ~75 | Ouro 3 → Ouro 1 | Δmortes ≤ 0 em ≥60% |
| **3 — Teamfight** | 11–15 | ~75 | Ouro 1 → Platina 2 | Share de dano ≥18% |
| **4 — Consolidar** | 16–19 | ~60 | Platina 2 → **Esmeralda 4** | WR ≥55% nos últimos 30 |

~285 jogos em 19 semanas. A fase 1 é curta de propósito: o descasamento entre rank exibido
(Prata 1) e MMR (lobbies de Ouro 2–4) dá LP inflado, e esse ativo evapora conforme ele sobe.

**Uma métrica por fase.** Perseguir cinco ao mesmo tempo é como não perseguir nenhuma.

---

## 8. Ciclo semanal de controle

Toda segunda-feira, dois comandos:

```bash
python opgg_scraper.py "Hutake#BR1" --count 20 --out matches.json
python scorecard.py
```

Sai o painel com as 5 metas e o `elo_point` atual.

**Regras de decisão:**

- **Métrica da fase atual fora da meta por 2 semanas seguidas** → não avance de fase,
  repita a atual.
- **WR abaixo de 50% em 30 jogos** → o problema não é o plano, é adesão. Confira sessão e
  pool antes de mudar qualquer outra coisa.
- **Pool abaixo de 90%** → é a causa mais provável de qualquer coisa dando errado. Fora da
  pool o desempenho histórico é 15%.

**Revisão de VOD:** 1 derrota por semana, 30 minutos, olhando só as mortes e etiquetando
nos cinco baldes. **Não assista vitórias** — elas não ensinam nada que o placar já não diga.

---

## 9. Riscos que podem matar o plano

1. **Reset de split em janeiro.** Se houver reset de temporada antes de 31/01, o rank zera
   e é preciso reclassificar. **Confirme o calendário de splits de 2027 antes de começar.**
   Maior risco de impacto do plano — pode encurtar a janela real em semanas.
2. **A janela dos 52%.** A 52% o plano exige 42 jogos/semana e vira inviável. Os primeiros
   30 jogos dizem de que lado da linha ele está. Se a WR ficar em 50–52% depois da fase 1,
   a meta honesta passa a ser Platina, não Esmeralda.
3. **Erosão do MMR da Hutake.** A vantagem de 2,5 divisões financia a fase 1. Cada semana
   sem jogar nela é vantagem perdida — a conta está parada desde 14/09/2026.
4. **Esmeralda hoje ≈ Platina antiga.** O alvo está 1–2 divisões acima do pico histórico de
   2021. É o fator que mantém a probabilidade em 35–45% em vez de 70%.

---

## 10. Resumo em uma página

**Faça:**

- Só Trundle (70%), Warwick (25%), Sejuani (5%) na Hutake.
- Máximo 3 ranqueadas por dia; 2 derrotas seguidas = fim do dia; 5 dias por semana.
- 2× por semana, 10 min de full clear cronometrado contra a própria mediana.
- Etiquete cada morte em 5 baldes; ataque só o maior.
- Trundle: pilar primeiro, entrar segundo.
- Rode o `scorecard.py` toda segunda.

**Não faça:**

- Jax, Master Yi ou Shyvana em ranqueada — vão para a Hipparcos.
- Campeão novo em ranqueada (histórico: 0V-4D).
- Jogo 4 do dia.
- Guardar a Hutake "para depois". O MMR dela é um ativo que decai.

**Os cinco números que definem sucesso:**

| Métrica | Hoje | Meta |
|---|---|---|
| Diferencial de mortes ≤ 0 | 42% | **60%** |
| Taxa de vitória | 42% | **55%** |
| Share de dano do time | 11,4% | **18%** |
| Jogos na pool travada | 0% | **90%** |
| Maior sessão do dia | 9 | **3** |

---

## Anexo — ferramentas nesta pasta

| Arquivo | O que faz |
|---|---|
| `opgg_scraper.py` | Coleta histórico de partidas, LP e resumo de temporada do op.gg |
| `scorecard.py` | Painel semanal das 5 métricas com meta e status |
| `analyze.py` | Agregado completo: rota, campeão, culpa, tilt, tendência |
| `deepdive.py` | Controles de viés: linha de base, posição no time, duelo com o jungler inimigo |
| `meta_pool.py` | Tier list do patch por rota/elo/região (`--only trundle,jax,warwick`) |
| `plan_math.py` | Tabela de WR × jogos necessários para o alvo |
| `rank_dist.py` | Distribuição de elo por região com percentil acumulado (`--region br`) |
| `test_opgg_scraper.py` | Checagem do parser (rode depois de qualquer mudança no op.gg) |

O op.gg não tem API pública. O scraper usa o Next.js Server Action `getGames` que a própria
página chama, descobrindo o ID da action nos chunks JS — ele muda a cada deploy do op.gg,
então o scraper redescobre sozinho. Se algo quebrar, rode `python test_opgg_scraper.py`
primeiro.
