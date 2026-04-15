"""
SavGol Window Grid Search — Pipeline Completo
===============================================

Roda o pipeline AdvancedPipeline variando APENAS savgol_window,
mantendo ret_20 e ret_150 fixos. Coleta metricas CPCV e meta-labeling
para cada valor de sg_window testado.

Uso:
  python savgol_grid_pipeline.py
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from regime_detection_advanced import AdvancedPipeline, DEFAULT_CONFIG

# ═══════════════════════════════════════════════════════════════════
# CONFIGURACAO
# ═══════════════════════════════════════════════════════════════════
# Janelas SavGol a testar (devem ser impares, >= polyorder+2=5)
SG_WINDOWS = [20, 22, 23, 24]

SAVE_DIR = "save_point_sg_grid"


def run_grid():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(script_dir, SAVE_DIR)
    os.makedirs(save_dir, exist_ok=True)

    results = []

    for i, sg_w in enumerate(SG_WINDOWS):
        print("\n" + "#" * 70)
        print(f"  SG GRID [{i+1}/{len(SG_WINDOWS)}] — savgol_window = {sg_w}")
        print("#" * 70)

        # Cada run salva em subpasta propria
        run_save_dir = os.path.join(SAVE_DIR, f"sg_{sg_w}")

        config_override = {
            "savgol_window": sg_w,
            "save_dir": run_save_dir,
        }

        try:
            t0 = time.time()
            pipeline = AdvancedPipeline(config=config_override)
            run_results = pipeline.run()
            elapsed = time.time() - t0

            row = {
                "sg_window": sg_w,
                "cpcv_sharpe_mean": run_results.get("cpcv_mean_sharpe", np.nan),
                "cpcv_accuracy_mean": run_results.get("cpcv_mean_accuracy", np.nan),
                "cpcv_f1_mean": run_results.get("cpcv_mean_f1", np.nan),
                "meta_sharpe": run_results.get("sharpe_test", np.nan),
                "meta_accuracy": run_results.get("meta_accuracy", np.nan),
                "psr": run_results.get("psr_test", np.nan),
                "dsr": run_results.get("dsr_test", np.nan),
                "n_features_selected": len(run_results.get("features_selected", [])),
                "features_selected": str(run_results.get("features_selected", [])),
                "elapsed_s": elapsed,
            }
            results.append(row)
            print(f"\n  >> sg={sg_w}: CPCV Sharpe={row['cpcv_sharpe_mean']:.4f}, "
                  f"Meta Sharpe={row['meta_sharpe']:.4f}, DSR={row['dsr']:.4f}, "
                  f"Time={elapsed:.0f}s")

        except Exception as e:
            print(f"\n  >> sg={sg_w}: ERRO — {e}")
            results.append({
                "sg_window": sg_w,
                "cpcv_sharpe_mean": np.nan,
                "error": str(e),
            })

    # ── Salvar resultados ──────────────────────────────────────────
    df = pd.DataFrame(results)
    csv_path = os.path.join(save_dir, "sg_grid_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\n  Resultados salvos: {csv_path}")

    # ── Report ─────────────────────────────────────────────────────
    report = "SAVGOL WINDOW GRID SEARCH — PIPELINE COMPLETO\n"
    report += "=" * 60 + "\n\n"
    report += f"  sg_windows testados: {SG_WINDOWS}\n"
    report += f"  ret_windows: [20, 150] (fixos)\n\n"

    # Tabela resumo
    cols = ["sg_window", "cpcv_sharpe_mean", "cpcv_sharpe_std",
            "meta_sharpe", "dsr", "n_features_selected", "elapsed_s"]
    available_cols = [c for c in cols if c in df.columns]
    report += df[available_cols].to_string(index=False) + "\n\n"

    # Melhor resultado
    if "cpcv_sharpe_mean" in df.columns:
        valid = df.dropna(subset=["cpcv_sharpe_mean"])
        if len(valid) > 0:
            best_cpcv = valid.loc[valid["cpcv_sharpe_mean"].idxmax()]
            report += f"  MELHOR CPCV Sharpe: sg={int(best_cpcv['sg_window'])} "
            report += f"(SR={best_cpcv['cpcv_sharpe_mean']:.4f})\n"

        if "meta_sharpe" in valid.columns:
            best_meta = valid.loc[valid["meta_sharpe"].idxmax()]
            report += f"  MELHOR Meta Sharpe: sg={int(best_meta['sg_window'])} "
            report += f"(SR={best_meta['meta_sharpe']:.4f})\n"

        if "dsr" in valid.columns:
            best_dsr = valid.loc[valid["dsr"].idxmax()]
            report += f"  MELHOR DSR: sg={int(best_dsr['sg_window'])} "
            report += f"(DSR={best_dsr['dsr']:.4f})\n"

    report_path = os.path.join(save_dir, "sg_grid_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  Report salvo: {report_path}")

    # ── Plot ───────────────────────────────────────────────────────
    if "cpcv_sharpe_mean" in df.columns:
        valid = df.dropna(subset=["cpcv_sharpe_mean"])
        if len(valid) > 1:
            fig, axes = plt.subplots(1, 3, figsize=(18, 5))

            # CPCV Sharpe
            ax = axes[0]
            ax.plot(valid["sg_window"], valid["cpcv_sharpe_mean"],
                    marker="o", linewidth=2)
            ax.set_xlabel("SavGol Window")
            ax.set_ylabel("CPCV Sharpe (mean)")
            ax.set_title("CPCV Sharpe vs SavGol Window")
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)

            # Meta Sharpe
            ax = axes[1]
            if "meta_sharpe" in valid.columns:
                ax.plot(valid["sg_window"], valid["meta_sharpe"],
                        marker="s", linewidth=2, color="C1")
            ax.set_xlabel("SavGol Window")
            ax.set_ylabel("Meta-Label Sharpe")
            ax.set_title("Meta-Label Sharpe vs SavGol Window")
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)

            # DSR
            ax = axes[2]
            if "dsr" in valid.columns:
                colors = ["green" if d > 0.05 else "red" for d in valid["dsr"]]
                ax.bar(valid["sg_window"], valid["dsr"], color=colors, width=1.5)
            ax.set_xlabel("SavGol Window")
            ax.set_ylabel("DSR")
            ax.set_title("Deflated Sharpe Ratio vs SavGol Window")
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0.05, color="orange", linestyle="--",
                        alpha=0.7, label="5% threshold")
            ax.legend()

            plt.tight_layout()
            fig_path = os.path.join(save_dir, "sg_grid_comparison.png")
            plt.savefig(fig_path, dpi=150)
            plt.close()
            print(f"  Plot salvo: {fig_path}")

    print("\n" + "=" * 60)
    print("  GRID SEARCH CONCLUIDO")
    print("=" * 60)


if __name__ == "__main__":
    run_grid()
