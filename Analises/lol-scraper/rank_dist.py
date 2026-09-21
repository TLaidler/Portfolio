"""Distribuicao de elo por regiao (op.gg /lol/statistics/tiers), com percentil acumulado.

Uso: python rank_dist.py --region br
"""
import argparse, json, re
import requests

BS = chr(92)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
ORDEM = ["CHALLENGER", "GRANDMASTER", "MASTER", "DIAMOND", "EMERALD", "PLATINUM",
         "GOLD", "SILVER", "BRONZE", "IRON"]


def dist(region="br"):
    u = requests.get(f"https://op.gg/lol/statistics/tiers?region={region}",
                     headers={"User-Agent": UA}, timeout=60).text.replace(BS + '"', '"')
    rows = []
    for m in re.finditer(
            r'"tier":"([A-Z]+)","division":(\d+),"player":(\d+),"playerPercent":"([\d.]+)"'
            r'.*?"cumulativePlayer":(\d+),"cumulativePlayerPercent":"([\d.]+)"', u):
        t, d, p, pp, cp, cpp = m.groups()
        rows.append({"tier": t, "div": int(d), "player": int(p), "pct": float(pp),
                     "cum_player": int(cp), "cum_pct": float(cpp)})
    # dedup mantendo a primeira ocorrencia de cada (tier, divisao)
    seen, out = set(), []
    for r in rows:
        k = (r["tier"], r["div"])
        if k not in seen:
            seen.add(k); out.append(r)
    return sorted(out, key=lambda r: (ORDEM.index(r["tier"]), r["div"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="br")
    a = ap.parse_args()
    rows = dist(a.region)
    total = max(r["cum_player"] for r in rows)
    print(f"Solo/Duo {a.region.upper()} | {total:,} jogadores ranqueados".replace(",", "."))
    print(f"{'divisao':14} {'jogadores':>10} {'% da pop':>9} {'top X% (acum)':>14}")
    por_tier = {}
    for r in rows:
        nome = f"{r['tier'].title()} {r['div']}" if r["tier"] not in ("MASTER", "GRANDMASTER", "CHALLENGER") else r["tier"].title()
        print(f"{nome:14} {r['player']:10,} {r['pct']:8.2f}% {r['cum_pct']:13.2f}%".replace(",", "."))
        por_tier.setdefault(r["tier"], []).append(r)
    print(f"\n{'tier':14} {'% da pop':>9} {'top X% (acum)':>14}")
    for t in ORDEM:
        if t not in por_tier: continue
        g = por_tier[t]
        print(f"{t.title():14} {sum(x['pct'] for x in g):8.2f}% {max(x['cum_pct'] for x in g):13.2f}%")


if __name__ == "__main__":
    main()
