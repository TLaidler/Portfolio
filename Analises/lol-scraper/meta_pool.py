"""Tier list de campeoes do op.gg por rota/elo/regiao, para calibrar a pool ao patch.

Uso: python meta_pool.py --lane jungle --tier gold --region br
     python meta_pool.py --lane jungle --tier gold --only trundle,jax,shyvana,warwick
"""
import argparse, json, re, sys
import requests

BS = chr(92)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def tier_list(lane="jungle", tier="gold", region="br"):
    """A lista vem server-rendered no payload RSC da pagina de campeoes."""
    html = requests.get(f"https://op.gg/lol/champions?position={lane}&tier={tier}&region={region}",
                        headers={"User-Agent": UA}, timeout=60).text
    u = html.replace(BS + '"', '"')
    patch = (re.search(r'/lol/([\d.]+)/champion/', u) or [None, None])[1]
    rows = []
    for m in re.finditer(
            r'"key":"([a-z0-9]+)","name":"([^"]+)".*?"positionWinRate":([\d.]+),'
            r'"positionPickRate":([\d.]+),"positionBanRate":([\d.]+),'
            r'"positionRoleRate":([\d.]+),"positionTierData":\{"tier":(\d+),"rank":(\d+)', u):
        k, n, wr, pr, br_, rr, t, rk = m.groups()
        rows.append({"key": k, "name": n, "wr": float(wr), "pick": float(pr),
                     "ban": float(br_), "role_rate": float(rr), "tier": int(t), "rank": int(rk)})
    # a mesma pagina repete campeoes; fica o de menor rank (a entrada da lista principal)
    best = {}
    for r in rows:
        if r["key"] not in best or r["rank"] < best[r["key"]]["rank"]:
            best[r["key"]] = r
    return patch, sorted(best.values(), key=lambda r: r["rank"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lane", default="jungle")
    ap.add_argument("--tier", default="gold", help="iron|bronze|silver|gold|platinum|emerald|diamond|master|all")
    ap.add_argument("--region", default="br")
    ap.add_argument("--only", help="lista de keys separadas por virgula")
    ap.add_argument("--top", type=int, default=25)
    a = ap.parse_args()

    patch, rows = tier_list(a.lane, a.tier, a.region)
    if not rows:
        sys.exit("nada extraido - o layout do op.gg deve ter mudado")
    keep = set(a.only.lower().split(",")) if a.only else None
    print(f"{a.lane.upper()} | {a.tier} | {a.region.upper()} | patch {patch} | {len(rows)} campeoes")
    print(f"{'#':>3} {'campeao':14} {'WR':>6} {'pick':>6} {'ban':>6} {'tier':>4}")
    for r in rows:
        if keep is not None and r["key"] not in keep:
            continue
        if keep is None and r["rank"] > a.top:
            continue
        print(f"{r['rank']:3} {r['name'][:14]:14} {r['wr']:5.1f}% {r['pick']:5.2f}% {r['ban']:5.2f}% {r['tier']:4}")


if __name__ == "__main__":
    main()
