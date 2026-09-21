"""Coleta partidas do chess.com pela API publica (sem auth, sem scraping de HTML).

    https://api.chess.com/pub/player/{user}          perfil
    https://api.chess.com/pub/player/{user}/stats    rating atual + RD por modalidade
    https://api.chess.com/pub/player/{user}/games/archives   lista de meses
    https://api.chess.com/pub/player/{user}/games/{ano}/{mes}

Uso: python chesscom_scraper.py hutaketrain hutakev --count 20 --out games.json
"""
import argparse, json, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
import requests

# a API do chess.com exige User-Agent identificavel; sem isso devolve 403
UA = "hutake-analysis/1.0 (chess strength analysis; contact via chess.com)"
API = "https://api.chess.com/pub"


def get(sess, url):
    r = sess.get(url, timeout=45)
    r.raise_for_status()
    return r.json()


def ts(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%d %H:%M")


def pgn_tag(pgn, tag):
    m = re.search(r'\[' + tag + r' "([^"]*)"\]', pgn or "")
    return m.group(1) if m else None


def accuracy(game, side):
    return (game.get("accuracies") or {}).get(side)


def flatten(game, user):
    """Achata uma partida na perspectiva de `user`."""
    u = user.lower()
    eu, ele = ("white", "black") if game["white"]["username"].lower() == u else ("black", "white")
    me, opp = game[eu], game[ele]
    res = me["result"]
    pontos = 1.0 if res == "win" else (0.0 if res in
                                       ("checkmated", "timeout", "resigned", "lose", "abandoned", "bughousepartnerlose")
                                       else 0.5)
    pgn = game.get("pgn") or ""
    return {
        "url": game.get("url"),
        "fim": ts(game["end_time"]),
        "epoch": game["end_time"],
        "modalidade": game.get("time_class"),
        "controle": game.get("time_control"),
        "cor": eu,
        "meu_rating": me.get("rating"),
        "rating_opp": opp.get("rating"),
        "diff": (me.get("rating") or 0) - (opp.get("rating") or 0),
        "resultado": res,
        "pontos": pontos,
        "motivo_opp": opp.get("result"),
        "opp": opp.get("username"),
        "acc_minha": accuracy(game, eu),
        "acc_opp": accuracy(game, ele),
        "lances": len(re.findall(r'\d+\.\s', pgn)),
        "abertura": (pgn_tag(pgn, "ECOUrl") or "").rsplit("/", 1)[-1].replace("-", " ") or None,
        "eco": pgn_tag(pgn, "ECO"),
        "rated": game.get("rated"),
    }


def scrape(user, count=20, modalidade=None):
    sess = requests.Session()
    sess.headers.update({"User-Agent": UA, "Accept": "application/json"})
    perfil = get(sess, f"{API}/player/{user}")
    stats = get(sess, f"{API}/player/{user}/stats")
    meses = get(sess, f"{API}/player/{user}/games/archives")["archives"]

    jogos = []
    for url in reversed(meses):                 # do mes mais recente para tras
        lote = get(sess, url).get("games", [])
        for g in sorted(lote, key=lambda x: x["end_time"], reverse=True):
            if modalidade and g.get("time_class") != modalidade:
                continue
            jogos.append(flatten(g, user))
            if len(jogos) >= count:
                break
        if len(jogos) >= count:
            break
        time.sleep(0.5)                          # educado com a API

    return {"usuario": user,
            "criada_em": ts(perfil["joined"]),
            "ultimo_online": ts(perfil["last_online"]),
            "nome": perfil.get("name"),
            "stats": stats,
            "jogos": jogos}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("usuarios", nargs="+")
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--modalidade", help="rapid|blitz|bullet|daily (padrao: todas)")
    ap.add_argument("--out", default="games.json")
    a = ap.parse_args()

    d = {}
    for u in a.usuarios:
        d[u] = scrape(u, a.count, a.modalidade)
        print(f"  {u}: {len(d[u]['jogos'])} partidas", file=sys.stderr)
    Path(a.out).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gravado: {a.out}")


if __name__ == "__main__":
    main()
