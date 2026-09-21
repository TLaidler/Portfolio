"""Testa a hipotese do "forte em transito": a faixa abaixo de 1000 esta cheia de
jogadores subcotados subindo desde a entrada em 400?

Metodo: para cada adversario, compara o rating QUE ELE TINHA na partida com o rating
que ele tem HOJE. Se a faixa estivesse cheia de gente em transito, o adversario medio
estaria hoje bem acima de onde estava.

Uso: python opponents.py [full.json] [conta] [n]
"""
import json, statistics as stat, sys, time
import requests

UA = "hutake-analysis/1.0 (chess strength analysis; contact via chess.com)"
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "full.json", encoding="utf-8"))
conta = sys.argv[2] if len(sys.argv) > 2 else "hutaketrain"
N = int(sys.argv[3]) if len(sys.argv) > 3 else 40

sess = requests.Session(); sess.headers.update({"User-Agent": UA})
jogos = [g for g in d[conta]["jogos"] if g["modalidade"] == "rapid"][:N]

print(f"{conta}: checando {len(jogos)} adversarios (rating na partida vs hoje)\n")
print(f"{'adversario':22} {'na partida':>11} {'hoje':>6} {'delta':>7} {'RD':>4} {'partidas':>9}")
deltas, sem_dado = [], 0
for g in jogos:
    try:
        st = sess.get(f"https://api.chess.com/pub/player/{g['opp']}/stats", timeout=30).json()
        r = st.get("chess_rapid")
        if not r:
            sem_dado += 1; continue
        hoje, rd = r["last"]["rating"], r["last"]["rd"]
        rec = r["record"]; n = rec["win"] + rec["loss"] + rec["draw"]
        delta = hoje - g["rating_opp"]
        deltas.append({"d": delta, "n": n, "rd": rd})
        print(f"{g['opp'][:22]:22} {g['rating_opp']:11} {hoje:6} {delta:+7} {rd:4} {n:9}")
    except Exception:
        sem_dado += 1
    time.sleep(0.35)

if deltas:
    ds = [x["d"] for x in deltas]
    print(f"\n  n={len(ds)} (sem dado publico: {sem_dado})")
    print(f"  delta medio : {round(stat.mean(ds),1):+}  | mediana {round(stat.median(ds),1):+}")
    print(f"  subiram >100: {sum(1 for x in ds if x > 100)}/{len(ds)} "
          f"({round(100*sum(1 for x in ds if x>100)/len(ds))}%)")
    print(f"  cairam >100 : {sum(1 for x in ds if x < -100)}/{len(ds)}")
    novatos = [x for x in deltas if x["n"] < 50]
    print(f"  adversarios com <50 partidas (ainda calibrando): {len(novatos)}/{len(deltas)} "
          f"({round(100*len(novatos)/len(deltas))}%), delta medio {round(stat.mean([x['d'] for x in novatos]),1):+}"
          if novatos else "  nenhum adversario com <50 partidas")
    print("\n  leitura: delta medio alto => a faixa estava cheia de gente subindo (subcotada).")
    print("           delta medio ~0    => a faixa media o que diz medir.")
