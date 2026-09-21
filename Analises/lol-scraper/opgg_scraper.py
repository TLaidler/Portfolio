"""Scraper de historico de partidas do op.gg (LoL).

Usa o Next.js Server Action 'getGames' que a propria pagina do op.gg chama.
Nao ha API publica; o id da action muda a cada deploy, entao ele e' descoberto
lendo os chunks JS da pagina (ACTION_FALLBACK e' so um atalho de cache).

Uso:  python opgg_scraper.py Hutake#BR1 Hipparcos#BR1 --count 20
"""
import argparse, json, re, sys, time
from pathlib import Path
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
ACTION_FALLBACK = "409a2b9ca50d15e50a4dace93552e3a40113dc2753"


def page_url(name, tag, region):
    return f"https://op.gg/lol/summoners/{region}/{name}-{tag}"


def fetch_page(sess, url):
    r = sess.get(url, timeout=40)
    r.raise_for_status()
    return r.text


def find_action_id(sess, html):
    """Le os chunks JS da pagina ate achar createServerReference(..., "getGames")."""
    for chunk in dict.fromkeys(re.findall(r'https://c-lol-web\.op\.gg/[^"]+?\.js', html)):
        try:
            js = sess.get(chunk, timeout=30).text
        except requests.RequestException:
            continue
        m = re.search(r'createServerReference\)?\("([0-9a-f]{40,})"[^)]*?"getGames"', js)
        if m:
            return m.group(1)
    return ACTION_FALLBACK


def parse_rsc(text):
    """A resposta da action e' RSC: linhas '<n>:<json>'. Devolve o 1o objeto com 'data'."""
    for line in text.splitlines():
        m = re.match(r'^\d+:(\{.*)$', line)
        if not m:
            continue
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "data" in obj:
            return obj
    raise ValueError("resposta RSC sem campo 'data'")


def get_games(sess, url, action, puuid, region, game_type, count):
    """Pagina via endedAt = created_at do ultimo jogo recebido."""
    games, ended_at = [], ""
    while len(games) < count:
        payload = [{"locale": "pt_BR", "region": region, "puuid": puuid,
                    "gameType": game_type, "endedAt": ended_at, "champion": ""}]
        r = sess.post(url, timeout=60,
                      headers={"Next-Action": action,
                               "Content-Type": "text/plain;charset=UTF-8",
                               "Referer": url},
                      data=json.dumps(payload))
        r.raise_for_status()
        batch = parse_rsc(r.text).get("data") or []
        if not batch:
            break
        games.extend(batch)
        ended_at = batch[-1]["created_at"]
        time.sleep(1)  # educado com o servidor
    return games[:count]


def flatten(game, puuid=None):
    """Achata o objeto de partida do op.gg nas colunas que interessam a analise."""
    st = game.get("stats") or {}
    kda = st.get("kda") or {}
    cs = st.get("cs") or {}
    mins = (game.get("game_length") or 1) / 60
    at = game.get("average_tier")
    kw = st.get("keyword")
    kw = kw if isinstance(kw, dict) else {"keyword": kw}
    return {
        "game_id": game.get("id"),
        "created_at": game.get("created_at"),
        "patch": game.get("game_version"),
        "queue": (game.get("game_type") or {}).get("game_translate"),
        "queue_key": (game.get("game_type") or {}).get("game_type"),
        "map": game.get("game_map"),
        "result": game.get("game_result"),
        "length_min": round(mins, 1),
        "avg_tier": at.get("tier") if isinstance(at, dict) else at,
        "side": game.get("summoner_team"),
        "champion": (game.get("champion") or {}).get("name"),
        "position": game.get("position"),
        "role": game.get("role"),
        "level": st.get("champion_level"),
        "kills": kda.get("kill"), "deaths": kda.get("death"), "assists": kda.get("assist"),
        "kda": kda.get("kda"),
        "kp": st.get("killParticipation"),
        "team_kills": st.get("teamChampionKill"),
        "cs": cs.get("totalCs"), "cs_per_min": cs.get("csPerMin"),
        "op_score": st.get("op_score"),
        "op_score_rank": st.get("op_score_rank"),
        "lane_score": st.get("lane_score"),
        "largest_multi_kill": st.get("largest_multi_kill"),
        "keyword": kw.get("keyword"),
        "spells": [x.get("key") if isinstance(x, dict) else x for x in (game.get("spells") or [])],
        "enemy_champs": [ (x.get("champion") or {}).get("name")
                          for x in (game.get("team_red") if game.get("summoner_team") == "BLUE"
                                    else game.get("team_blue")) or [] ],
        "ally_champs": [ (x.get("champion") or {}).get("name")
                         for x in (game.get("team_blue") if game.get("summoner_team") == "BLUE"
                                   else game.get("team_red")) or [] ],
    }


def scrape(account, region="br", count=20):
    name, tag = account.split("#")
    url = page_url(name, tag, region)
    sess = requests.Session()
    sess.headers.update({"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"})

    html = fetch_page(sess, url)
    # o puuid aparece escapado (RSC) e cru (JSON-LD); um padrao cobre os dois
    m = re.search(r'puuid.{0,30}?"([\w-]{70,})"', html)
    if not m:
        raise SystemExit(f"puuid nao encontrado para {account} (conta existe/renomeou?)")
    puuid = m.group(1)

    # o payload RSC vem com aspas escapadas; desfaz antes de casar o JSON
    unescaped = html.replace("\\\"", "\"")
    lp_hist = []
    mh = re.search(r'"lpHistories":(\[.*?\}\])', unescaped)
    if mh:
        try:
            lp_hist = json.loads(mh.group(1))
        except json.JSONDecodeError:
            pass

    # a meta description traz elo atual, W/L da temporada e W/L por campeao
    md = re.search(r'"description":"(.*?)","', html, re.S)

    action = find_action_id(sess, html)
    out = {"account": account, "puuid": puuid, "action_id": action,
           "lp_history": lp_hist, "season_summary": md.group(1) if md else None}
    for gt in ("total", "SOLORANKED"):
        raw = get_games(sess, url, action, puuid, region, gt, count)
        out[gt] = {"raw": raw, "flat": [flatten(g, puuid) for g in raw]}
        print(f"  {account}: {len(raw)} partidas ({gt})", file=sys.stderr)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accounts", nargs="+", help="ex: Hutake#BR1")
    ap.add_argument("--region", default="br")
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--out", default="matches.json")
    a = ap.parse_args()
    data = {acc: scrape(acc, a.region, a.count) for acc in a.accounts}
    Path(a.out).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gravado: {a.out}")


if __name__ == "__main__":
    main()
