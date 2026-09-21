"""Controles para o vies do op_score: o op.gg pontua o time perdedor para baixo,
entao 'posicao no lobby (1-10)' mede resultado do time, nao desempenho individual.

Controles usados aqui: linha de base de quem perde, posicao dentro do PROPRIO time
(1-5) e duelo direto com o jungler inimigo da mesma partida.

Uso: python deepdive.py [matches.json]
"""
import json, statistics as stat, sys
from collections import Counter, defaultdict

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "matches.json", encoding="utf-8"))
cs = lambda s: (s.get("minion_kill") or 0) + (s.get("neutral_minion_kill") or 0)


def avg(xs, nd=2):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return round(stat.mean(xs), nd) if xs else None

lose_ranks, win_ranks = [], []
for acc,b in d.items():
    for g in b["SOLORANKED"]["raw"]:
        if g.get("game_result") not in ("WIN","LOSE"): continue
        for p in g["team_blue"]+g["team_red"]:
            r=p["stats"].get("op_score_rank")
            if not isinstance(r,int) or r==0: continue
            (win_ranks if p["stats"].get("result")=="WIN" else lose_ranks).append(r)
print("### LINHA DE BASE: posicao no lobby (1-10) de TODOS os jogadores das 39 partidas")
print(f"  quem GANHOU: posicao media {avg(win_ranks)}  distrib {dict(sorted(Counter(win_ranks).items()))}")
print(f"  quem PERDEU: posicao media {avg(lose_ranks)}  distrib {dict(sorted(Counter(lose_ranks).items()))}")
bot4=sum(1 for r in lose_ranks if r>=7)
print(f"  quem perdeu e ficou bottom-4 do lobby: {bot4}/{len(lose_ranks)} ({round(100*bot4/len(lose_ranks))}%)  <- a linha de base")
top3=sum(1 for r in lose_ranks if r<=3)
print(f"  quem perdeu e ficou top-3 do lobby:    {top3}/{len(lose_ranks)} ({round(100*top3/len(lose_ranks))}%)  <- raro para QUALQUER um")
print()
print("### COMPARADO A LINHA DE BASE")
for acc,b in d.items():
    rs=[]
    for g in b["SOLORANKED"]["raw"]:
        if g.get("game_result")!="LOSE": continue
        side=g.get("summoner_team"); mine=g["team_blue"] if side=="BLUE" else g["team_red"]
        me=next((p for p in mine if p["participant_id"]==g["participant_id"]),None)
        if me and isinstance(me["stats"].get("op_score_rank"),int) and me["stats"]["op_score_rank"]:
            rs.append(me["stats"]["op_score_rank"])
    bot=sum(1 for r in rs if r>=7)
    print(f"  {acc:16} derrotas n={len(rs)} posicao media {avg(rs)} (base {avg(lose_ranks)}) | "
          f"bottom-4 {round(100*bot/len(rs))}% (base {round(100*bot4/len(lose_ranks))}%)")

games=[]
for acc,b in d.items():
    for g in b["SOLORANKED"]["raw"]:
        if g.get("game_result") not in ("WIN","LOSE"): continue
        side=g.get("summoner_team")
        mine=g["team_blue"] if side=="BLUE" else g["team_red"]
        theirs=g["team_red"] if side=="BLUE" else g["team_blue"]
        me=next((p for p in mine if p["participant_id"]==g["participant_id"]), None)
        if not me: continue
        games.append({"acc":acc,"g":g,"me":me,"mine":mine,"theirs":theirs})

# --- 1. quanto o resultado do time infla/desinfla o op_score
wins=[p for x in games for p in x["mine"]+x["theirs"] if (p["stats"].get("result") or "")=="WIN"]
loss=[p for x in games for p in x["mine"]+x["theirs"] if (p["stats"].get("result") or "")=="LOSE"]
print("### 1. VIES DO OP SCORE (todos os 10 jogadores de 39 partidas)")
print(f"  op_score medio do time VENCEDOR: {avg([p['stats'].get('op_score') for p in wins])}  (n={len(wins)})")
print(f"  op_score medio do time PERDEDOR: {avg([p['stats'].get('op_score') for p in loss])}  (n={len(loss)})")
print(f"  lane_score  vencedor: {avg([p['stats'].get('lane_score') for p in wins])} | perdedor: {avg([p['stats'].get('lane_score') for p in loss])}")
print("  -> se a diferenca e' grande, 'rank no lobby' mede resultado do time, nao individuo\n")

# --- 2. o controle correto: posicao dentro do proprio time
print("### 2. POSICAO DENTRO DO PROPRIO TIME (1 = melhor dos 5)")
for acc in d:
    for res in ("LOSE","WIN"):
        sel=[x for x in games if x["acc"]==acc and x["g"]["game_result"]==res]
        ranks=[]
        for x in sel:
            order=sorted(x["mine"], key=lambda p: -(p["stats"].get("op_score") or 0))
            ranks.append(1+[p["participant_id"] for p in order].index(x["me"]["participant_id"]))
        c=Counter(ranks)
        top2=sum(v for k,v in c.items() if k<=2)
        print(f"  {acc:16} {res:5} n={len(sel):2} media {avg(ranks)} | distrib {dict(sorted(c.items()))} "
              f"| top-2 do time em {top2}/{len(sel)} ({round(100*top2/max(len(sel),1))}%)")
print()

# --- 3. duelo direto com o jungler inimigo (controle simetrico)
print("### 3. VS JUNGLER INIMIGO (mesma rota, lados opostos, mesmo jogo)")
for acc in d:
    for res in ("LOSE","WIN"):
        rows=[]
        for x in [y for y in games if y["acc"]==acc and y["g"]["game_result"]==res]:
            if x["me"].get("position")!="JUNGLE": continue
            opp=next((p for p in x["theirs"] if p.get("position")=="JUNGLE"), None)
            if not opp: continue
            ms,os_=x["me"]["stats"],opp["stats"]
            cs=lambda s: (s.get("minion_kill") or 0)+(s.get("neutral_minion_kill") or 0)
            rows.append({"op":(ms.get("op_score") or 0)-(os_.get("op_score") or 0),
                         "cs":cs(ms)-cs(os_),
                         "gold":(ms.get("gold_earned") or 0)-(os_.get("gold_earned") or 0),
                         "dmg":(ms.get("total_damage_dealt_to_champions") or 0)-(os_.get("total_damage_dealt_to_champions") or 0),
                         "d":(ms.get("death") or 0)-(os_.get("death") or 0),
                         "won_duel":(ms.get("op_score") or 0)>(os_.get("op_score") or 0)})
        if rows:
            print(f"  {acc:16} {res:5} n={len(rows):2} | delta op {avg([r['op'] for r in rows]):+} "
                  f"| cs {avg([r['cs'] for r in rows]):+} | ouro {avg([r['gold'] for r in rows]):+} "
                  f"| dano {avg([r['dmg'] for r in rows]):+} | mortes {avg([r['d'] for r in rows]):+} "
                  f"| ganhou o duelo {sum(r['won_duel'] for r in rows)}/{len(rows)}")
print()

# --- 4. participacao no proprio time (share), imune ao resultado
print("### 4. SHARE DENTRO DO TIME (dano e ouro; 20% = media exata)")
for acc in d:
    for res in ("LOSE","WIN"):
        sel=[x for x in games if x["acc"]==acc and x["g"]["game_result"]==res]
        dsh,gsh=[],[]
        for x in sel:
            td=sum(p["stats"].get("total_damage_dealt_to_champions") or 0 for p in x["mine"])
            tg=sum(p["stats"].get("gold_earned") or 0 for p in x["mine"])
            if td: dsh.append(100*(x["me"]["stats"].get("total_damage_dealt_to_champions") or 0)/td)
            if tg: gsh.append(100*(x["me"]["stats"].get("gold_earned") or 0)/tg)
        print(f"  {acc:16} {res:5} n={len(sel):2} | dano {avg(dsh)}% | ouro {avg(gsh)}%")

cs=lambda s:(s.get("minion_kill") or 0)+(s.get("neutral_minion_kill") or 0)

by=defaultdict(list)
for acc,b in d.items():
    for g in b["SOLORANKED"]["raw"]:
        if g.get("game_result") not in ("WIN","LOSE"): continue
        side=g["summoner_team"]
        mine=g["team_blue"] if side=="BLUE" else g["team_red"]
        theirs=g["team_red"] if side=="BLUE" else g["team_blue"]
        me=next((p for p in mine if p["participant_id"]==g["participant_id"]),None)
        if not me or me.get("position")!="JUNGLE": continue
        opp=next((p for p in theirs if p.get("position")=="JUNGLE"),None)
        if not opp: continue
        mn=g["game_length"]/60
        by[g["champion"]["name"]].append({
            "res":g["game_result"], "opp":opp["champion"]["name"],
            "dcs":(cs(me["stats"])-cs(opp["stats"]))/mn,
            "dgold":(me["stats"].get("gold_earned",0)-opp["stats"].get("gold_earned",0))/mn,
            "ddmg":(me["stats"].get("total_damage_dealt_to_champions",0)-opp["stats"].get("total_damage_dealt_to_champions",0))/mn,
            "dd":me["stats"].get("death",0)-opp["stats"].get("death",0),
            "dop":(me["stats"].get("op_score") or 0)-(opp["stats"].get("op_score") or 0),
            "mydmg":me["stats"].get("total_damage_dealt_to_champions",0)/mn})

print("### SEU CAMPEAO vs O JUNGLER INIMIGO, por minuto (mesma partida = controle perfeito)")
print(f"{'campeao':12} {'n':>2} {'V-D':>5} {'dCS/min':>8} {'dOuro/min':>10} {'dDano/min':>10} {'dMortes':>8} {'dOP':>6} {'seuDano/min':>12}")
for ch,rows in sorted(by.items(), key=lambda kv:-len(kv[1])):
    w=sum(r["res"]=="WIN" for r in rows)
    print(f"{ch:12} {len(rows):2} {str(w)+'-'+str(len(rows)-w):>5} "
          f"{avg([r['dcs'] for r in rows]):>8} {avg([r['dgold'] for r in rows]):>10} "
          f"{avg([r['ddmg'] for r in rows]):>10} {avg([r['dd'] for r in rows]):>8} "
          f"{avg([r['dop'] for r in rows]):>6} {avg([r['mydmg'] for r in rows]):>12}")
print("\n### JAX: partida a partida (contra quem, e por quanto)")
for r in sorted(by.get("Jax",[]), key=lambda r:r["dop"]):
    print(f"  vs {r['opp']:12} {r['res']:5} dCS/min {r['dcs']:+6.1f} dOuro/min {r['dgold']:+7.1f} "
          f"dDano/min {r['ddmg']:+8.1f} dMortes {r['dd']:+3} dOP {r['dop']:+5.1f}")
