"""Compara as duas contas controlando o que o rating sozinho esconde.

O rating bruto nao e' comparavel entre as contas porque elas jogam controles de tempo
diferentes e enfrentaram campos diferentes. Aqui: acuracia por controle, trajetoria
desde a criacao e RD (confiabilidade da medida).

Uso: python compare.py [full.json]
"""
import json, statistics as stat, sys
from collections import Counter, defaultdict

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "full.json", encoding="utf-8"))


def avg(xs, nd=1):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return round(stat.mean(xs), nd) if xs else None


TC = {"600": "10 min", "900+10": "15|10", "1800": "30 min", "1800+10": "30|10",
      "300": "5 min", "180": "3 min", "60": "1 min", "120+1": "2|1", "300+5": "5|5"}
tcname = lambda c: TC.get(c, c)

print("#" * 74)
print("# 1. CONTROLE DE TEMPO — as contas nao jogam o mesmo jogo")
print("#" * 74)
for u, b in d.items():
    r = [g for g in b["jogos"] if g["modalidade"] == "rapid"]
    c = Counter(tcname(g["controle"]) for g in r)
    print(f"  {u:14} {len(r):3} rapid  {dict(c.most_common())}")

print()
print("#" * 74)
print("# 2. ACURACIA POR CONTROLE DE TEMPO (so partidas analisadas pelo chess.com)")
print("#" * 74)
por = defaultdict(lambda: defaultdict(list))
for u, b in d.items():
    for g in b["jogos"]:
        if g["acc_minha"] is not None and g["modalidade"] == "rapid":
            por[tcname(g["controle"])][u].append(g)
print(f"  {'controle':10} {'conta':14} {'n':>3} {'acuracia':>9} {'adversario':>11} {'delta':>7}")
for tc in sorted(por, key=lambda t: -sum(len(v) for v in por[t].values())):
    for u, gs in por[tc].items():
        a = avg([g["acc_minha"] for g in gs]); o = avg([g["acc_opp"] for g in gs])
        print(f"  {tc:10} {u:14} {len(gs):3} {a:8}% {o:10}% {round(a-o,1):+7}")

print()
print("#" * 74)
print("# 3. ACURACIA AGREGADA (todas as partidas rapid analisadas)")
print("#" * 74)
for u, b in d.items():
    gs = [g for g in b["jogos"] if g["acc_minha"] is not None and g["modalidade"] == "rapid"]
    if not gs:
        continue
    v = [g["acc_minha"] for g in gs if g["pontos"] == 1]
    p = [g["acc_minha"] for g in gs if g["pontos"] == 0]
    print(f"  {u:14} n={len(gs):3} geral {avg([g['acc_minha'] for g in gs])}% "
          f"| vitorias {avg(v)}% | derrotas {avg(p)}% "
          f"| adversarios {avg([g['acc_opp'] for g in gs])}%")

print()
print("#" * 74)
print("# 4. TRAJETORIA DE RATING desde a criacao da conta")
print("#" * 74)
for u, b in d.items():
    r = sorted([g for g in b["jogos"] if g["modalidade"] == "rapid"], key=lambda g: g["epoch"])
    if not r:
        continue
    st = b["stats"]["chess_rapid"]
    print(f"\n  {u}  (criada {b['criada_em'][:10]}, {len(r)} rapid coletadas)")
    print(f"    1a partida coletada: {r[0]['fim'][:10]}  rating {r[0]['meu_rating']}")
    print(f"    ultima             : {r[-1]['fim'][:10]}  rating {r[-1]['meu_rating']}")
    print(f"    atual {st['last']['rating']}  RD {st['last']['rd']}  pico {st['best']['rating']}")
    # blocos de 20 para ver a evolucao
    print(f"    {'bloco':16} {'n':>3} {'rating med':>11} {'score':>7} {'campo':>7}")
    for i in range(0, len(r), 20):
        bl = r[i:i + 20]
        if len(bl) < 5:
            continue
        s = sum(g["pontos"] for g in bl)
        print(f"    {bl[0]['fim'][:10]:16} {len(bl):3} {avg([g['meu_rating'] for g in bl]):10} "
              f"{100*s/len(bl):6.0f}% {avg([g['rating_opp'] for g in bl]):7}")

print()
print("#" * 74)
print("# 5. CONFIABILIDADE DA MEDIDA (RD do Glicko)")
print("#" * 74)
for u, b in d.items():
    st = b["stats"].get("chess_rapid")
    if not st:
        continue
    rd = st["last"]["rd"]
    print(f"  {u:14} rating {st['last']['rating']}  RD {rd:3}  "
          f"-> intervalo ~95%: {st['last']['rating']-2*rd} a {st['last']['rating']+2*rd}  "
          f"({st['record']['win']+st['record']['loss']+st['record']['draw']} partidas)")
