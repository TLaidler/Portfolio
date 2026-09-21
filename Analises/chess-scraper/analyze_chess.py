"""Forca real das duas contas: rating de performance, acuracia e desvio do esperado.

A pergunta e' qual dos dois numeros mede melhor o mesmo jogador. O rating sozinho nao
responde, porque cada conta enfrentou um campo diferente. Rating de performance responde.

Uso: python analyze_chess.py [games.json]
"""
import json, math, statistics as stat, sys
from collections import Counter

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "games.json", encoding="utf-8"))


def avg(xs, nd=1):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return round(stat.mean(xs), nd) if xs else None


def esperado(diff):
    """Formula de Elo: score esperado dado o diferencial de rating."""
    return 1 / (1 + 10 ** (-diff / 400))


def perf_rating(media_opp, score, n):
    """Rating de performance: quanto vale o desempenho contra o campo enfrentado."""
    p = score / n
    p = min(max(p, 1 / (2 * n)), 1 - 1 / (2 * n))      # evita log(0) em 100%/0%
    return round(media_opp - 400 * math.log10(1 / p - 1))


for u, b in d.items():
    j = b["jogos"]
    rated = [g for g in j if g.get("rated")]
    print("=" * 74)
    st = b["stats"].get("chess_rapid", {})
    print(f"{u}  ({b.get('nome') or 'sem nome'})")
    print(f"  conta criada {b['criada_em']}  |  ultimo online {b['ultimo_online']}")
    if st:
        r = st["record"]
        print(f"  RAPID atual {st['last']['rating']}  RD {st['last']['rd']}  "
              f"| pico {st['best']['rating']}  | historico {r['win']}V {r['loss']}D {r['draw']}E "
              f"({r['win']+r['loss']+r['draw']} partidas)")
    bl = b["stats"].get("chess_blitz")
    if bl:
        r = bl["record"]
        print(f"  BLITZ atual {bl['last']['rating']}  RD {bl['last']['rd']}  "
              f"| pico {bl['best']['rating']} | {r['win']}V {r['loss']}D {r['draw']}E")

    print(f"\n  ultimas {len(j)} partidas: {j[-1]['fim'][:10]} a {j[0]['fim'][:10]}")
    print(f"  modalidades: {dict(Counter(g['modalidade'] for g in j))}")
    print(f"  controles:   {dict(Counter(g['controle'] for g in j))}")
    print(f"  ranqueadas:  {len(rated)}/{len(j)}")

    # so rapid: misturar modalidades quebra o rating de performance (pools separados)
    sel = [g for g in j if g["modalidade"] == "rapid"] or j
    n = len(sel)
    score = sum(g["pontos"] for g in sel)
    w = sum(g["pontos"] == 1 for g in sel)
    l = sum(g["pontos"] == 0 for g in sel)
    dr = n - w - l
    mopp = avg([g["rating_opp"] for g in sel])
    mmeu = avg([g["meu_rating"] for g in sel])
    esp = sum(esperado(g["diff"]) for g in sel)

    print(f"\n  --- {n} partidas rapid ---")
    print(f"  placar: {w}V {l}D {dr}E  = {score}/{n} ({100*score/n:.0f}%)")
    print(f"  rating medio proprio    : {mmeu}")
    print(f"  rating medio do campo   : {mopp}")
    print(f"  score esperado pelo Elo : {esp:.1f}/{n} ({100*esp/n:.0f}%)")
    print(f"  score real              : {score}/{n} ({100*score/n:.0f}%)")
    print(f"  desvio                  : {score-esp:+.1f} pontos vs o esperado")
    print(f"  RATING DE PERFORMANCE   : {perf_rating(mopp, score, n)}")

    accs = [g["acc_minha"] for g in sel if g["acc_minha"] is not None]
    oaccs = [g["acc_opp"] for g in sel if g["acc_opp"] is not None]
    if accs:
        print(f"  acuracia media (n={len(accs)}): {avg(accs,1)}%  | adversarios: {avg(oaccs,1)}%")
        vit = [g["acc_minha"] for g in sel if g["acc_minha"] is not None and g["pontos"] == 1]
        der = [g["acc_minha"] for g in sel if g["acc_minha"] is not None and g["pontos"] == 0]
        print(f"     em vitorias {avg(vit,1)}%  | em derrotas {avg(der,1)}%")
    else:
        print("  acuracia: nenhuma partida analisada pelo chess.com")

    print(f"  duracao media: {avg([g['lances'] for g in sel],0)} lances")
    print(f"  cor: {dict(Counter(g['cor'] for g in sel))}")
    print(f"  campo enfrentado: min {min(g['rating_opp'] for g in sel)} / "
          f"max {max(g['rating_opp'] for g in sel)}")
    print(f"  sequencia (recente->antiga): "
          f"{''.join('V' if g['pontos']==1 else ('D' if g['pontos']==0 else 'E') for g in sel)}")
