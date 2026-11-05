#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Estudo de caso de Quaoar refeito com os modelos finais da reanálise pós-banca
(configuração 1.2b, 12 características, sem kmeans_centroid_dist).

Substitui, para a dissertação, test_quaoar.py e test_quaoar_recortes.py, que usavam
os modelos da configuração 2 da versão apresentada à banca (outputs/resultado5).
Os dois programas antigos foram mantidos para registro.

Etapas
------
1. Curvas inteiras: as três curvas do evento (CFHT/WIRCam Ks, Gemini-'Alopeke r e z),
   sem recorte, com os quatro modelos.
2. Recortes: as mesmas seis janelas da versão anterior na curva 'Alopeke z, com os
   quatro modelos, no limiar padrão (0,5) e no limiar escolhido na validação cruzada
   (critério sensibilidade >= 99,5 %, lido de outputs/reanalise_banca/resumo.json).
3. Janelas ampliadas: o mesmo teste da versão anterior (Q2R e ruído com janelas ~3x maiores).
4. Varredura cega: janelas de mesma duração (15 s e 25 s, passo de meia janela) percorrendo
   toda a curva 'Alopeke z. As janelas que não tocam nenhum evento conhecido (corpo e anéis,
   com margem) estimam a taxa de alarmes falsos por janela em cada limiar; a posição das
   janelas dos anéis Q2R nessa ordenação mede se o modelo as prioriza sem saber onde estão.

Uso:   python quaoar_reanalise.py
Saídas: outputs_quaoar_1.2b/ (resultados.json, recortes.csv, varredura.csv)
        ../../writing_latex/Tese/pngs/reanalise/quaoar_recortes.png
"""
import json
import os
import sys
import warnings
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
QUAOAR_DIR = os.path.join(HERE, "quaoar")
MT = os.path.join(HERE, "..", "model_training")
MODELOS_PATH = os.path.join(MT, "outputs", "reanalise_banca", "modelos", "modelos_config_1.2b.joblib")
RESUMO_PATH = os.path.join(MT, "outputs", "reanalise_banca", "resumo.json")
OUT = os.path.join(HERE, "outputs_quaoar_1.2b")
FIG = os.path.join(HERE, "..", "..", "writing_latex", "Tese", "pngs", "reanalise")
os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

sys.path.insert(0, MT)
from build_dataset import extract_features          # noqa: E402
from occ_features import compute_occ_features, OCC_FEATURE_NAMES  # noqa: E402

TIME_COL, FLUX_COL = 4, 9                 # segundos UTC do dia; fluxo normalizado (PRAIA)
EVENT_REFERENCE = "2022-08-09 06:34:49.26"
CURVAS = ["CFHT_Wircam_Ks_cor-time.dat", "Gemini-Alopeke_Blue-r.dat", "Gemini-Alopeke_Red-z.dat"]
CURVA_RECORTES = "Gemini-Alopeke_Red-z.dat"
MODELOS = ["Regressão Logística", "Random Forest", "XGBoost", "CatBoost"]

# Janelas em segundos UTC do dia (idênticas às de test_quaoar_recortes.py)
RECORTES = {
    "linha de base": {"janela": (23399, 23439), "assinatura": "linha de base (controle negativo)", "cor": "tab:gray"},
    "Q1R contínua": {"janela": (23464, 23489), "assinatura": "Q1R, parte contínua", "cor": "tab:orange"},
    "Q2R (1)":      {"janela": (23560, 23575), "assinatura": "Q2R, anel fino (real)", "cor": "tab:green"},
    "ruído":        {"janela": (23580, 23590), "assinatura": "ruído parecido com anel", "cor": "tab:red"},
    "Q2R (2)":      {"janela": (23810, 23835), "assinatura": "Q2R, anel fino (real)", "cor": "tab:purple"},
    "Q1R densa":    {"janela": (23880, 23940), "assinatura": "Q1R, parte densa", "cor": "tab:brown"},
}
# Janelas ampliadas (~3x) da versão anterior, em segundos relativos ao instante de referência
AMPLIADAS_REL = {"Q2R (1)": (-160, -110), "ruído": (-110, -85), "Q2R (2)": (80, 170)}


def seconds_of_day(ref):
    d = datetime.strptime(ref, "%Y-%m-%d %H:%M:%S.%f")
    return d.hour * 3600 + d.minute * 60 + d.second + d.microsecond / 1e6


REF = seconds_of_day(EVENT_REFERENCE)


def read_curve(path, fmin=-2.0, fmax=5.0):
    data = np.genfromtxt(path, usecols=[TIME_COL, FLUX_COL], dtype=float)
    data = data[np.isfinite(data).all(axis=1)]
    t, f = data[:, 0], data[:, 1]
    keep = (f >= fmin) & (f <= fmax)
    return t[keep], f[keep]


def cut(t, f, a, b):
    m = (t >= a) & (t <= b)
    return t[m], f[m]


def features(t, f, name):
    c = {"time": t.tolist(), "flux": f.tolist(), "flux_normalized": f.tolist()}
    feats = extract_features(c, name, use_filter="savgol")
    if feats is None:
        return None
    occ = compute_occ_features(c)
    if occ is not None:
        feats.update(occ)
    else:
        feats.update({k: np.nan for k in OCC_FEATURE_NAMES})
    return feats


bundle = joblib.load(MODELOS_PATH)
FEATS, MODS = bundle["features"], bundle["modelos"]
with open(RESUMO_PATH, encoding="utf-8") as fh:
    resumo = json.load(fh)
TAU_CV = {m: float(resumo["limiares"][m]["tau_sens"]) for m in MODELOS}
FPR_OOF_003 = {m: float(resumo["limiares"][m]["fpr_real_oof_tau003"]) for m in MODELOS}


def proba(feat_rows):
    X = pd.DataFrame(feat_rows)
    for c in FEATS:
        if c not in X.columns:
            X[c] = np.nan
    X = X[FEATS]
    return {m: MODS[m].predict_proba(X)[:, 1] for m in MODELOS}


res = {"features": FEATS, "tau_cv": TAU_CV, "fpr_real_oof_tau003": FPR_OOF_003}

# --------------------------------------------------------------------------- 1. curvas inteiras
inteiras = {}
for nome in CURVAS:
    t, f = read_curve(os.path.join(QUAOAR_DIR, nome))
    p = proba([features(t, f, nome)])
    inteiras[nome] = {"n_pontos": int(len(t)), **{m: float(p[m][0]) for m in MODELOS}}
res["curvas_inteiras"] = inteiras

# --------------------------------------------------------------------------- 2. recortes
t_z, f_z = read_curve(os.path.join(QUAOAR_DIR, CURVA_RECORTES))
rows, linhas = [], []
for nome, cfg in RECORTES.items():
    a, b = cfg["janela"]
    tc, fc = cut(t_z, f_z, a, b)
    rows.append(features(tc, fc, nome))
    linhas.append({"recorte": nome, "assinatura": cfg["assinatura"], "ini_rel": a - REF, "fim_rel": b - REF,
                   "n_pontos": int(len(tc))})
p_rec = proba(rows)
for i, l in enumerate(linhas):
    for m in MODELOS:
        l[m] = float(p_rec[m][i])
rec = pd.DataFrame(linhas)
rec.to_csv(os.path.join(OUT, "recortes.csv"), index=False)
res["recortes"] = linhas

# --------------------------------------------------------------------------- 3. janelas ampliadas
amp = []
rows = []
for nome, (a, b) in AMPLIADAS_REL.items():
    tc, fc = cut(t_z, f_z, a + REF, b + REF)
    rows.append(features(tc, fc, nome + " ampliada"))
    amp.append({"recorte": nome, "ini_rel": a, "fim_rel": b, "n_pontos": int(len(tc))})
p_amp = proba(rows)
for i, l in enumerate(amp):
    for m in MODELOS:
        l[m] = float(p_amp[m][i])
res["ampliadas"] = amp

# --------------------------------------------------------------------------- 4. varredura cega
# Intervalo do corpo principal: pontos do fluxo suavizado abaixo de 0,5 perto do instante de referência
trel = t_z - REF
k = 25
fs = np.convolve(f_z, np.ones(k) / k, mode="same")
corpo = trel[(fs < 0.5) & (np.abs(trel) < 60)]
CORPO = (float(corpo.min()), float(corpo.max()))
EVENTOS = {"Q1R contínua": (-225, -200), "Q2R (1)": (-129.26, -114.26), "corpo": CORPO,
           "Q2R (2)": (120.74, 145.74), "Q1R densa": (190.74, 250.74)}
MARGEM = 3.0
res["corpo_intervalo_rel"] = CORPO
res["eventos_rel"] = EVENTOS

varr = []
for D in (15.0, 25.0):
    starts = np.arange(trel.min(), trel.max() - D, D / 2)
    rows, meta = [], []
    for s in starts:
        m_ = (trel >= s) & (trel <= s + D)
        if m_.sum() < 20:
            continue
        ev = [n for n, (a, b) in EVENTOS.items() if not (s + D < a - MARGEM or s > b + MARGEM)]
        rows.append(features(t_z[m_], f_z[m_], f"varredura_{D:.0f}_{s:.1f}"))
        meta.append({"duracao": D, "ini_rel": float(s), "fim_rel": float(s + D), "eventos": ";".join(ev)})
    p = proba(rows)
    for i, mm in enumerate(meta):
        for m in MODELOS:
            mm[m] = float(p[m][i])
    varr.extend(meta)
vdf = pd.DataFrame(varr)
vdf.to_csv(os.path.join(OUT, "varredura.csv"), index=False)

resumo_varr = {}
for D in (15.0, 25.0):
    sub = vdf[vdf.duracao == D]
    livres = sub[sub.eventos == ""]
    r = {"n_janelas": int(len(sub)), "n_livres": int(len(livres))}
    for m in MODELOS:
        r[m] = {"fpr_tau05": float((livres[m] >= 0.5).mean()),
                "fpr_tau_cv": float((livres[m] >= TAU_CV[m]).mean()),
                "fpr_tau003": float((livres[m] >= 0.03).mean()),
                "p_livres_max": float(livres[m].max()),
                "p_livres_p90": float(livres[m].quantile(0.9)),
                "p_livres_mediana": float(livres[m].median())}
    resumo_varr[f"{D:.0f}s"] = r
res["varredura"] = resumo_varr

# posição dos recortes Q2R (janelas originais) entre as janelas livres de mesma duração
pos = {}
for nome, D in (("Q2R (1)", 15.0), ("Q2R (2)", 25.0)):
    livres = vdf[(vdf.duracao == D) & (vdf.eventos == "")]
    l = next(x for x in linhas if x["recorte"] == nome)
    pos[nome] = {m: {"p": l[m], "frac_livres_acima": float((livres[m] >= l[m]).mean()),
                     "n_livres": int(len(livres))} for m in MODELOS}
res["posicao_q2r"] = pos

with open(os.path.join(OUT, "resultados.json"), "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)


# --------------------------------------------------------------------------- impressão
def fmt(x):
    return f"{x:.4f}"


print("Características:", FEATS)
print("tau (validação cruzada, sens >= 99,5 %):", TAU_CV)
print("\n[1] Curvas inteiras")
for n, d in inteiras.items():
    print(f"  {n:32s} n={d['n_pontos']:5d}  " + "  ".join(f"{m[:6]}={fmt(d[m])}" for m in MODELOS))
print("\n[2] Recortes (curva 'Alopeke z)")
print(rec.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
print("\n[3] Janelas ampliadas")
print(pd.DataFrame(amp).to_string(index=False, float_format=lambda x: f"{x:.4f}"))
print("\n[4] Corpo (rel):", CORPO)
print(json.dumps(resumo_varr, ensure_ascii=False, indent=1))
print(json.dumps(pos, ensure_ascii=False, indent=1))


# --------------------------------------------------------------------------- figura da dissertação
# Curva 'Alopeke z com os seis recortes numerados; legenda com a probabilidade do XGBoost e o
# veredito no limiar padrão (0,5) e no limiar ilustrativo (0,03).
from matplotlib.ticker import FuncFormatter  # noqa: E402

MODELO_FIG = "XGBoost"
TAU_ILUSTRATIVO = 0.03
plt.rcParams.update({"font.size": 15, "axes.labelsize": 16, "xtick.labelsize": 14, "ytick.labelsize": 14,
                     "legend.fontsize": 13, "savefig.dpi": 200, "savefig.bbox": "tight"})


def virg(x, nd):
    return f"{x:.{nd}f}".replace(".", ",")


def p_txt(p):
    return virg(p, 4) if p < 0.01 else virg(p, 3)


fig, ax = plt.subplots(figsize=(14, 6))
m_plot = (trel >= -300) & (trel <= 350)
ax.plot(trel[m_plot], f_z[m_plot], "-", lw=0.6, color="0.75")
handles = []
for i, (nome, cfg) in enumerate(RECORTES.items(), start=1):
    a, b = cfg["janela"][0] - REF, cfg["janela"][1] - REF
    mk = (trel >= a) & (trel <= b)
    ax.axvspan(a, b, color=cfg["cor"], alpha=0.18, lw=0)
    ax.plot(trel[mk], f_z[mk], "-", lw=0.8, color=cfg["cor"])
    ax.text((a + b) / 2, 1.13, str(i), ha="center", va="bottom", fontsize=15, fontweight="bold", color=cfg["cor"])
    p = next(x for x in linhas if x["recorte"] == nome)[MODELO_FIG]
    v05 = "positivo" if p >= 0.5 else "negativo"
    vt = "positivo" if p >= TAU_ILUSTRATIVO else "negativo"
    handles.append(Patch(facecolor=cfg["cor"], alpha=0.5,
                         label=f"({i}) {cfg['assinatura'][0].upper() + cfg['assinatura'][1:]}, "
                               f"[{a:+.0f}; {b:+.0f}] s: ".replace("-", "−") +
                               f"$\\hat{{p}}$ = {p_txt(p)}; "
                               f"$\\tau$ = 0,5: {v05}; $\\tau$ = {virg(TAU_ILUSTRATIVO, 2)}: {vt}"))
ax.annotate("corpo de Quaoar", xy=(0, 0.02), xytext=(45, 0.30), fontsize=14,
            arrowprops=dict(arrowstyle="->", color="0.3"), color="0.3")
ax.axhline(1.0, color="0.4", ls=":", lw=1)
ax.set_xlim(-300, 350)
ax.set_ylim(-0.08, 1.25)
ax.set_xlabel("Tempo relativo a 06:34:49,26 UTC de 09/08/2022 (s)")
ax.set_ylabel("Fluxo normalizado")
ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: virg(y, 1)))
ax.grid(alpha=0.25)
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=1, frameon=False,
          title=f"Recortes e probabilidade atribuída pelo {MODELO_FIG} (configuração 1.2b)", title_fontsize=14)
fig.savefig(os.path.join(FIG, "quaoar_recortes.png"))
plt.close(fig)
print("\nFigura:", os.path.join(FIG, "quaoar_recortes.png"))
