"""Quantos jogos e que WR a Hutake precisa para Esmeralda 4 ate 31/01/2027."""
from datetime import date
HOJE, ALVO = date(2026,9,21), date(2027,1,31)
sem = (ALVO-HOJE).days/7
DIV_LP = 100          # ~100 LP por divisao
DIVS   = 9            # Prata 1 -> Esmeralda 4
print(f"janela: {(ALVO-HOJE).days} dias = {sem:.1f} semanas | alvo: {DIVS} divisoes = {DIVS*DIV_LP} LP liquidos\n")
print(f"{'WR':>5} {'fase1 +25/-15':>14} {'fase2 +20/-20':>14} {'jogos total':>12} {'jogos/semana':>13}")
for w in (0.50,0.52,0.55,0.57,0.60,0.63):
    n1 = 40*w-15      # MMR da Hutake ainda acima do rank: ganho assimetrico ate ~Ouro 3
    n2 = 40*w-20      # depois disso, ganho simetrico
    if n1<=0 or n2<=0:
        print(f"{w*100:4.0f}% {'nunca':>14} {'nunca':>14} {'-':>12} {'-':>13}"); continue
    g1, g2 = 300/n1, 600/n2
    tot = g1+g2
    print(f"{w*100:4.0f}% {g1:13.0f}j {g2:13.0f}j {tot:11.0f}j {tot/sem:12.1f}")
print("\nvolume atual do jogador: ~35 ranqueadas/semana (Hipparcos, 56 jogos em 11 dias)")
print("=> volume NAO e' o gargalo em nenhum cenario >=52%. O gargalo e' a taxa de vitoria.")
