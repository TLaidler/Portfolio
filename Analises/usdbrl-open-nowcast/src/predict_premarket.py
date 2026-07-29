# -*- coding: utf-8 -*-
"""
05_predict_premarket.py — Ferramenta diária do trader (rodar ~8:50 BRT).

Todos os inputs são obteníveis em tempo real ANTES das 9:00:
  --fut       cotação atual do 6L CME (broker/TradingView; negocia 23h)
  --fut-prev  6L no fechamento de ontem ~17:58 BRT
  --dxy / --dxy-prev   DXY agora e ontem 17:58
  --selic     meta Selic vigente (% a.a., conhecida)
  --us-rate   DGS1MO de ONTEM (FRED publica D-1; % a.a.)
  --du        dias úteis até o vencimento do contrato front
  --event     1 se hoje há COPOM/FOMC/CPI/IPCA/payroll/PIB no calendário (conhecido ex-ante)
  --basis-lag1  resíduo de ontem em bps (do log de ontem; 0 se feriado assimétrico)
  --vol-bps   vol overnight do 6L em bps (opcional; default = mediana histórica)

Sem argumentos --fut: modo --dry-run usando a última linha do dataset histórico.
Cada previsão é registrada em predictions_log.csv (protocolo de paper trading).
"""
import os, sys, argparse, datetime as dt
import numpy as np
import pandas as pd
import joblib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
RES = os.path.join(ROOT, "results")
MODELS = os.path.join(ROOT, "models")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fut", type=float)
    ap.add_argument("--fut-prev", type=float)
    ap.add_argument("--dxy", type=float)
    ap.add_argument("--dxy-prev", type=float)
    ap.add_argument("--selic", type=float, default=None)
    ap.add_argument("--us-rate", type=float, default=None)
    ap.add_argument("--du", type=int, default=None)
    ap.add_argument("--event", type=int, default=0)
    ap.add_argument("--basis-lag1", type=float, default=None, help="bps")
    ap.add_argument("--vol-bps", type=float, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    art = joblib.load(os.path.join(MODELS, "model_ridge.pkl"))
    reg = joblib.load(os.path.join(MODELS, "model_regime.pkl"))
    hist = pd.read_csv(os.path.join(PROC, "dataset_daily.csv"), parse_dates=["date"]).set_index("date")

    if args.dry_run or args.fut is None:
        row = hist.dropna(subset=art["feats"]).iloc[-1]
        print(f"[dry-run] usando última linha do histórico: {row.name.date()}")
        feats = {f: row[f] for f in art["feats"]}
        dolar_cc = row["dolar_cc_snap"]
    else:
        need = [args.fut_prev, args.dxy, args.dxy_prev, args.selic, args.us_rate, args.du]
        if any(v is None for v in need):
            sys.exit("Faltam argumentos: --fut-prev --dxy --dxy-prev --selic --us-rate --du")
        cc = ((1 + args.selic / 100) / (1 + args.us_rate / 100)) ** (args.du / 252)
        dolar_cc = (100.0 / args.fut) / cc
        fut_prev_usdbrl = 100.0 / args.fut_prev
        basis_lag1 = (args.basis_lag1 if args.basis_lag1 is not None
                      else hist["y_log_resid"].iloc[-1] * 1e4)
        vol = (args.vol_bps / 1e4 if args.vol_bps is not None
               else hist["vol_6l_on"].median())
        feats = {
            "ret_fut_on": np.log((100.0 / args.fut) / fut_prev_usdbrl),
            "ret_dxy_on": np.log(args.dxy / args.dxy_prev),
            "vol_6l_on": vol,
            "event_day": args.event,
            "basis_lag1": basis_lag1 / 1e4,
        }

    X = np.array([[feats[f] for f in art["feats"]]])
    pred_bps = float(art["model"].predict(art["scaler"].transform(X))[0])
    open_pred = dolar_cc * np.exp(pred_bps / 1e4)

    rf = {"vol_6l_on": feats["vol_6l_on"], "event_day": feats["event_day"],
          "abs_ret_fut_on": abs(feats["ret_fut_on"]), "abs_basis_lag1": abs(feats["basis_lag1"])}
    Xr = np.array([[rf[f] for f in reg["regime_feats"]]])
    p_abnormal = float(reg["model"].predict_proba(reg["scaler"].transform(Xr))[0, 1])

    thr = art["thresh_bps"]
    actionable = abs(pred_bps) > thr
    print("=" * 60)
    print(f"NOWCAST ABERTURA USDBRL — {dt.datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 60)
    print(f"dolar_cc (spot implícito 6L):    {dolar_cc:.4f}")
    print(f"resíduo previsto:                {pred_bps:+.1f} bps")
    print(f"ABERTURA PREVISTA:               {open_pred:.4f}")
    print(f"P(basis anormal > {thr:.0f} bps):      {p_abnormal:.0%}"
          f"  -> {'CUIDADO: dolar_cc pouco confiável hoje' if p_abnormal > 0.5 else 'dolar_cc confiável'}")
    print(f"Sinal direcional:                "
          f"{('ABERTURA ACIMA do implícito' if pred_bps > 0 else 'ABERTURA ABAIXO do implícito') if actionable else 'sem sinal (|previsão| <= custo)'}")
    if art["veredito_walkforward"] == "NO-GO":
        print("\n[!] Walk-forward = NO-GO nos critérios estritos: use como PAPER TRADING;")
        print("    o número operacional é dolar_cc + flag de regime, não a previsão pontual.")

    logp = os.path.join(RES, "predictions_log.csv")
    entry = pd.DataFrame([{"logged_at": dt.datetime.now().isoformat(timespec="seconds"),
                           "dolar_cc": dolar_cc, "pred_resid_bps": pred_bps,
                           "open_pred": open_pred, "p_abnormal": p_abnormal,
                           "actionable": actionable, "dry_run": bool(args.dry_run or args.fut is None),
                           **feats}])
    entry.to_csv(logp, mode="a", header=not os.path.exists(logp), index=False)
    print(f"\nRegistrado em {os.path.basename(logp)} (protocolo de paper trading).")

if __name__ == "__main__":
    main()
