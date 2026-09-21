"""Agrega matches.json em metricas de rota, desempenho, culpa e tendencia.

Uso: python analyze.py [matches.json]
"""
import json, statistics as stat, sys
from collections import Counter, defaultdict

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "matches.json", encoding="utf-8"))


def avg(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]  # op.gg manda "$undefined" as vezes
    return round(stat.mean(xs), 2) if xs else None


print("#" * 78 + "\n# 1. RESUMO POR CONTA\n" + "#" * 78)
for acc, blob in d.items():
    print("=" * 78); print(acc, "| puuid:", blob["puuid"][:16] + "...")
    lp = blob.get("lp_history") or []
    if lp:
        print(f"LP history ({len(lp)} pts): {lp[0]['created_at'][:10]} {lp[0]['tier_info']['label']} "
              f"{lp[0]['tier_info']['lp']}LP elo={lp[0]['elo_point']}  ->  "
              f"{lp[-1]['created_at'][:10]} {lp[-1]['tier_info']['label']} "
              f"{lp[-1]['tier_info']['lp']}LP elo={lp[-1]['elo_point']}")
        print("  elo_point serie:", [x["elo_point"] for x in lp])
    for gt in ("total", "SOLORANKED"):
        f = blob[gt]["flat"]
        if not f: continue
        w = sum(x["result"] == "WIN" for x in f); l = sum(x["result"] == "LOSE" for x in f)
        print(f"\n--- {gt}: {len(f)} jogos | {w}W {l}L ({round(100*w/max(w+l,1))}% WR) | "
              f"{f[-1]['created_at'][:10]} .. {f[0]['created_at'][:10]}")
        print("  filas:", dict(Counter(x["queue"] for x in f)))
        print("  rotas:", dict(Counter(x["position"] for x in f)))
        print("  champs:", dict(Counter(x["champion"] for x in f).most_common()))
        print("  tier medio das partidas:", dict(Counter(x["avg_tier"] for x in f).most_common()))
        print(f"  KDA med {avg([x['kda'] for x in f])} | K {avg([x['kills'] for x in f])} "
              f"D {avg([x['deaths'] for x in f])} A {avg([x['assists'] for x in f])}")
        print(f"  KP% {avg([x['kp'] for x in f])} | CS/min {avg([x['cs_per_min'] for x in f])} | "
              f"dur med {avg([x['length_min'] for x in f])}min")
        print(f"  OP score {avg([x['op_score'] for x in f])} | rank no jogo {avg([x['op_score_rank'] for x in f])} "
              f"| lane_score {avg([x['lane_score'] for x in f])}")
        ws = [x for x in f if x["result"] == "WIN"]; ls = [x for x in f if x["result"] == "LOSE"]
        for lbl, g in (("VITORIAS", ws), ("DERROTAS", ls)):
            if g:
                print(f"  [{lbl}] n={len(g)} KDA {avg([x['kda'] for x in g])} D {avg([x['deaths'] for x in g])} "
                      f"CS/min {avg([x['cs_per_min'] for x in g])} KP {avg([x['kp'] for x in g])} "
                      f"OP {avg([x['op_score'] for x in g])} rank {avg([x['op_score_rank'] for x in g])} "
                      f"lane {avg([x['lane_score'] for x in g])} dur {avg([x['length_min'] for x in g])}")
        by = defaultdict(list)
        for x in f: by[(x["position"], x["champion"])].append(x)
        print("  por rota/champ:")
        for k, g in sorted(by.items(), key=lambda kv: -len(kv[1])):
            gw = sum(y["result"] == "WIN" for y in g)
            print(f"    {str(k):28} n={len(g):2} {gw}W{len(g)-gw}L  KDA {avg([y['kda'] for y in g])} "
                  f"D {avg([y['deaths'] for y in g])} OP {avg([y['op_score'] for y in g])} "
                  f"rank {avg([y['op_score_rank'] for y in g])} lane {avg([y['lane_score'] for y in g])}")
        print("  sequencia (recente->antiga):", "".join("W" if x["result"] == "WIN" else "L" for x in f))
        print("  keywords:", dict(Counter(x["keyword"] for x in f).most_common()))
        print("  op_score_rank distrib:", dict(sorted(Counter(x["op_score_rank"] for x in f).items())))
        print("  duracao x resultado: W", sorted(round(x["length_min"]) for x in ws),
              "| L", sorted(round(x["length_min"]) for x in ls))

print("\n" + "#" * 78 + "\n# 2. CULPA, TILT E RITMO\n" + "#" * 78)
for acc,b in d.items():
    f=[x for x in b["SOLORANKED"]["flat"] if x["result"] in ("WIN","LOSE")]
    W=[x for x in f if x["result"]=="WIN"]; L=[x for x in f if x["result"]=="LOSE"]
    print("="*72); print(acc, f"{len(W)}W {len(L)}L")
    print(f"  team kills: W {avg([x['team_kills'] for x in W])} | L {avg([x['team_kills'] for x in L])}")
    print(f"  kills+assists absolutos: W {avg([x['kills']+x['assists'] for x in W])} | L {avg([x['kills']+x['assists'] for x in L])}")
    print(f"  deaths/min: W {avg([x['deaths']/x['length_min'] for x in W])} | L {avg([x['deaths']/x['length_min'] for x in L])}")
    blame=[x for x in L if (x['op_score_rank'] or 0)>=7]; team=[x for x in L if 1<=(x['op_score_rank'] or 0)<=3]
    print(f"  derrotas em que foi bottom-4 do lobby: {len(blame)}/{len(L)} ({round(100*len(blame)/max(len(L),1))}%)")
    print(f"  derrotas em que foi top-3 do lobby:    {len(team)}/{len(L)} ({round(100*len(team)/max(len(L),1))}%)")
    car=[x for x in W if 1<=(x['op_score_rank'] or 0)<=3]
    print(f"  vitorias em que foi top-3 do lobby:    {len(car)}/{len(W)} ({round(100*len(car)/max(len(W),1))}%)")
    print(f"  lane_score: W {avg([x['lane_score'] for x in W])} | L {avg([x['lane_score'] for x in L])}")
    print(f"  jogos com >=8 mortes: {sum(1 for x in f if (x['deaths'] or 0)>=8)}/{len(f)} "
          f"(destes, derrotas: {sum(1 for x in f if (x['deaths'] or 0)>=8 and x['result']=='LOSE')})")
    print(f"  jogos com KP<40%: {sum(1 for x in f if (x['kp'] or 0)<40)}/{len(f)} "
          f"(derrotas: {sum(1 for x in f if (x['kp'] or 0)<40 and x['result']=='LOSE')})")
    print(f"  jogos com cs/min<5.5: {sum(1 for x in f if (x['cs_per_min'] or 0)<5.5)}/{len(f)}")
    # ritmo: jogos por dia
    days=Counter(x["created_at"][:10] for x in f)
    print("  jogos/dia:", dict(sorted(days.items())))
    print("  maior sessao num dia:", max(days.values()), "| dias ativos:", len(days))
    # dentro do dia: resultado por ordem da sessao
    for day,n in sorted(days.items()):
        seq="".join("W" if x["result"]=="WIN" else "L" for x in reversed([x for x in f if x["created_at"][:10]==day]))
        print(f"    {day} {seq}")

print("\n" + "#" * 78 + "\n# 3. FADIGA, CAMPEAO E TENDENCIA\n" + "#" * 78)
pool=[]
for acc,b in d.items():
    for x in b["SOLORANKED"]["flat"]:
        if x["result"] in ("WIN","LOSE"): x["acc"]=acc; pool.append(x)

print("### FADIGA: resultado por posicao do jogo dentro da sessao (dia), ambas as contas")
bydayacc=defaultdict(list)
for x in pool: bydayacc[(x["acc"],x["created_at"][:10])].append(x)
idx=defaultdict(list)
for k,g in bydayacc.items():
    for i,x in enumerate(sorted(g,key=lambda y:y["created_at"])): idx[min(i+1,6)].append(x)
for i in sorted(idx):
    g=idx[i]; w=sum(y["result"]=="WIN" for y in g)
    print(f"  jogo #{i}{'+' if i==6 else ''} da sessao: n={len(g):2} {w}W{len(g)-w}L "
          f"({round(100*w/len(g)):3}% WR) OP {avg([y['op_score'] for y in g])} "
          f"mortes {avg([y['deaths'] for y in g])} lane {avg([y['lane_score'] for y in g])}")

print("\n### CAMPEAO (pool das duas contas, ultimas 20 ranked de cada)")
bych=defaultdict(list)
for x in pool: bych[x["champion"]].append(x)
for ch,g in sorted(bych.items(),key=lambda kv:-len(kv[1])):
    w=sum(y["result"]=="WIN" for y in g)
    print(f"  {ch:12} n={len(g):2} {w}W{len(g)-w}L ({round(100*w/len(g)):3}%) OP {avg([y['op_score'] for y in g])} "
          f"rank {avg([y['op_score_rank'] for y in g])} mortes {avg([y['deaths'] for y in g])} "
          f"KP {avg([y['kp'] for y in g])} lane {avg([y['lane_score'] for y in g])}")

print("\n### TENDENCIA temporal (mais antigo -> mais novo), por conta")
for acc,b in d.items():
    f=[x for x in b["SOLORANKED"]["flat"] if x["result"] in ("WIN","LOSE")][::-1]
    h1,h2=f[:len(f)//2],f[len(f)//2:]
    print(f"  {acc}")
    for lbl,g in (("10 mais antigas",h1),("10 mais recentes",h2)):
        w=sum(y["result"]=="WIN" for y in g)
        print(f"    {lbl}: {w}W{len(g)-w}L OP {avg([y['op_score'] for y in g])} "
              f"mortes {avg([y['deaths'] for y in g])} KP {avg([y['kp'] for y in g])} "
              f"cs/min {avg([y['cs_per_min'] for y in g])} lane {avg([y['lane_score'] for y in g])}")
    print("    op_score serie:", [y["op_score"] for y in f])
