"""Checagem minima: o parser RSC e o achatamento continuam batendo com o payload real."""
import json
from opgg_scraper import parse_rsc, flatten

def test():
    # formato RSC: linhas "<n>:<json>"
    g = {"id": "x", "game_length": 1800, "game_result": "WIN",
         "game_type": {"game_type": "SOLORANKED", "game_translate": "Ranked Solo/Duo"},
         "average_tier": {"tier": "gold 2"}, "champion": {"name": "Jax"},
         "position": "JUNGLE", "summoner_team": "BLUE", "team_blue": [], "team_red": [],
         "stats": {"kda": {"kill": 5, "death": 2, "assist": 7, "kda": 6.0},
                   "cs": {"totalCs": 180, "csPerMin": 6.0}, "op_score": 7.1,
                   "op_score_rank": 2, "killParticipation": 55, "keyword": "VICTOR"}}
    assert parse_rsc('0:["x"]\n1:' + json.dumps({"data": [g]}))["data"] == [g]

    f = flatten(g)
    assert f["result"] == "WIN" and f["champion"] == "Jax" and f["position"] == "JUNGLE"
    assert f["length_min"] == 30.0 and f["kda"] == 6.0 and f["cs_per_min"] == 6.0
    assert f["avg_tier"] == "gold 2" and f["keyword"] == "VICTOR"

    # op.gg manda "$undefined"/string em varios campos: nao pode explodir
    g2 = dict(g, average_tier="$undefined", stats=dict(g["stats"], keyword="$undefined"))
    assert flatten(g2)["avg_tier"] == "$undefined"
    print("ok")

if __name__ == "__main__":
    test()
