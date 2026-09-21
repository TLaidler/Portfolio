"""Placar semanal: as 6 metricas do plano, com meta e status.

Uso: python opgg_scraper.py "Hutake#BR1" --count 20 --out matches.json && python scorecard.py
"""
import json, statistics as stat, sys
from collections import Counter, defaultdict

POOL = {"Trundle", "Warwick"}          # pool travada do plano
META = {"dmort": 60, "wr": 55, "dmg_share": 18, "sessao": 3, "pool": 90}

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "matches.json", encoding="utf-8"))
cs = lambda s: (s.get("minion_kill") or 0) + (s.get("neutral_minion_kill") or 0)
pct = lambda a, b: round(100 * a / b) if b else 0
ok = lambda v, m, maior=True: "OK " if (v >= m if maior else v <= m) else "-> "

for acc, b in d.items():
    games = []
    for g in b["SOLORANKED"]["raw"]:
        if g.get("game_result") not in ("WIN", "LOSE"):
            continue
        side = g["summoner_team"]
        mine = g["team_blue"] if side == "BLUE" else g["team_red"]
        theirs = g["team_red"] if side == "BLUE" else g["team_blue"]
        me = next((p for p in mine if p["participant_id"] == g["participant_id"]), None)
        if not me:
            continue
        opp = next((p for p in theirs if p.get("position") == "JUNGLE"), None)
        td = sum(p["stats"].get("total_damage_dealt_to_champions") or 0 for p in mine)
        games.append({
            "dia": g["created_at"][:10], "champ": g["champion"]["name"], "res": g["game_result"],
            "dmort": (me["stats"].get("death", 0) - opp["stats"].get("death", 0)) if opp else None,
            "share": 100 * (me["stats"].get("total_damage_dealt_to_champions") or 0) / td if td else None,
            "mortes": me["stats"].get("death", 0)})
    if not games:
        continue

    n = len(games)
    wr = pct(sum(g["res"] == "WIN" for g in games), n)
    dm = [g for g in games if g["dmort"] is not None]
    bom = pct(sum(g["dmort"] <= 0 for g in dm), len(dm))
    share = round(stat.mean([g["share"] for g in games if g["share"] is not None]), 1)
    poolpct = pct(sum(g["champ"] in POOL for g in games), n)
    dias = Counter(g["dia"] for g in games)
    maior = max(dias.values())
    lp = b.get("lp_history") or []

    print("=" * 66)
    print(f"{acc}  |  ultimas {n} ranqueadas  |  {games[-1]['dia']} a {games[0]['dia']}")
    if lp:
        print(f"  elo_point {lp[-1]['elo_point']}  ({lp[-1]['tier_info']['label']} {lp[-1]['tier_info']['lp']} LP)")
    print(f"  {ok(bom, META['dmort'])} mortes <= jungler inimigo : {bom:3}%   meta >= {META['dmort']}%")
    print(f"  {ok(wr, META['wr'])} vitorias                   : {wr:3}%   meta >= {META['wr']}%")
    print(f"  {ok(share, META['dmg_share'])} share de dano do time      : {share:5}% meta >= {META['dmg_share']}%")
    print(f"  {ok(poolpct, META['pool'])} jogos na pool travada      : {poolpct:3}%   meta >= {META['pool']}%")
    print(f"  {ok(maior, META['sessao'], False)} maior sessao do periodo    : {maior:3}    meta <= {META['sessao']} jogos/dia")
    print(f"      mortes por jogo            : {round(stat.mean([g['mortes'] for g in games]),1)}")
    print(f"      campeoes: {dict(Counter(g['champ'] for g in games).most_common())}")
    fora = [g for g in games if g["champ"] not in POOL]
    if fora:
        w = sum(g["res"] == "WIN" for g in fora)
        print(f"      fora da pool: {len(fora)} jogos, {w}V-{len(fora)-w}D")
