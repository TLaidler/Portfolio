"""Orcamento de horas: da para perseguir LoL e xadrez ao mesmo tempo ate 31/12/2026?

Nao e' pergunta de motivacao, e' de aritmetica. As duas metas competem pelo mesmo
recurso: horas de foco depois de um dia de 10h de trabalho.

Uso: python budget.py
"""
from datetime import date

HOJE, FIM = date(2026, 9, 21), date(2026, 12, 31)
SEM = (FIM - HOJE).days / 7

# --- LoL: 100 LP por divisao; fase 1 com MMR favoravel (+25/-15), depois (+20/-20)
MIN_PARTIDA_LOL = 35          # 29 min de media medidos + fila e selecao
ALVOS_LOL = {"Ouro 1": 4, "Platina 4": 5, "Platina 3": 6, "Platina 2": 7, "Esmeralda 4": 9}


def jogos_lol(divs, wr):
    n1, n2 = 40 * wr - 15, 40 * wr - 20
    if n1 <= 0 or n2 <= 0:
        return None
    d1 = min(divs, 3)                      # o MMR da Hutake cobre ~3 divisoes
    return d1 * 100 / n1 + max(0, divs - d1) * 100 / n2


print(f"janela ate 31/12/2026: {(FIM-HOJE).days} dias = {SEM:.1f} semanas\n")
print("### LoL — jogos e horas por semana, por alvo e taxa de vitoria")
print(f"{'alvo':13} " + " ".join(f"{int(w*100)}%WR".rjust(13) for w in (0.55, 0.57, 0.60)))
for alvo, divs in ALVOS_LOL.items():
    linha = f"{alvo:13} "
    for wr in (0.55, 0.57, 0.60):
        g = jogos_lol(divs, wr)
        h = g * MIN_PARTIDA_LOL / 60 / SEM
        linha += f"{g/SEM:5.1f}j {h:4.1f}h".rjust(14)
    print(linha)
print("  + 0,5h/semana de treino (full clear, revisao de VOD, placar)")

# --- custo marginal: no LoL cada divisao acima de Ouro 3 custa quase o mesmo
print("\n### LoL — custo MARGINAL de cada divisao (a 55% de WR)")
ant = 0
for alvo, divs in ALVOS_LOL.items():
    g = jogos_lol(divs, 0.55)
    print(f"  ate {alvo:13} {g:5.0f} jogos acumulados  (+{g-ant:4.0f} jogos = +{(g-ant)*MIN_PARTIDA_LOL/60:4.1f}h "
          f"vs o alvo anterior)")
    ant = g

# --- Xadrez
# As duas contas concordam: 956 em 10 min + 100 (delta medido de controle) = 1056 ~ 1051.
# Entao o 1051 NAO esta defasado, e nao existe atalho de "revalidar".
print("\n### Xadrez — de 1051 (30 min) para cada alvo")
ALVOS_X = [(1100, "tatica 15min x5 + 3 partidas/sem + revisao", 1.25 + 1.75 + 0.5, "75-80%"),
           (1200, "tatica 20min x5 + 3-4 partidas/sem + revisao", 1.7 + 2.0 + 1.0, "40-50%")]
for alvo, regime, h, p in ALVOS_X:
    print(f"  {alvo}  ({alvo-1051:+4} pts)  {h:4.1f}h/semana  {regime:44} P ~ {p}")
print("  Nota: o RD da hutakev e' 92, entao +50 cabe dentro do proprio erro da medida.")

# --- combinacoes
print("\n### COMBINACOES (LoL a 55% de WR)")
print(f"  {'':28} {'xadrez 1100':>13} {'xadrez 1200':>13}")
for alvo, divs in ALVOS_LOL.items():
    hl = jogos_lol(divs, 0.55) * MIN_PARTIDA_LOL / 60 / SEM + 0.5
    print(f"  LoL {alvo:13} {hl:4.1f}h  {hl+ALVOS_X[0][2]:12.1f}h {hl+ALVOS_X[1][2]:12.1f}h")

# --- orcamento diario
print("\n### Orcamento de horas do dia (estimativa)")
dia = [("sono", 7.5), ("trabalho", 10), ("academia + deslocamento", 1.5),
       ("afazeres domesticos", 1.0), ("refeicoes", 1.0)]
usado = sum(h for _, h in dia)
for n, h in dia:
    print(f"  {n:26} {h:4.1f}h")
print(f"  {'-'*26} ----")
print(f"  {'comprometido':26} {usado:4.1f}h")
print(f"  {'LIVRE (dia util)':26} {24-usado:4.1f}h  -> {(24-usado)*5:4.1f}h/semana em dias uteis")
print(f"  {'+ fim de semana (6h/dia)':26} {12.0:4.1f}h")
print(f"  {'TOTAL LIVRE':26} {(24-usado)*5+12:4.1f}h/semana  (tudo, sem descanso nem folga)")
