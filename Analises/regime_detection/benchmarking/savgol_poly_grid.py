"""
SavGol Polyorder Grid Search — Pipeline Completo
==================================================

Roda o pipeline AdvancedPipeline variando APENAS savgol_polyorder,
com savgol_window=21 fixo. Coleta metricas CPCV e meta-labeling.

Uso:
  python savgol_poly_grid.py
"""

import os
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
POLYORDERS = [2, 4, 5]
SG_WINDOW = 21  # fixo

SAVE_DIR = "save_point_poly_grid"


def run_grid():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(script_dir, SAVE_DIR)
    os.makedirs(save_dir, exist_ok=True)

    results = []

    for i, poly in enumerate(POLYORDERS):
        print("\n" + "#" * 70)
        print(f"  POLY GRID [{i+1}/{len(POLYORDERS)}] — polyorder = {poly}, sg_window = {SG_WINDOW}")
        print("#" * 70)

        run_save_dir = os.path.join(SAVE_DIR, f"poly_{poly}")

        config_override = {
            "savgol_window": SG_WINDOW,
            "savgol_polyorder": poly,
            "save_dir": run_save_dir,
        }

        try:
            t0 = time.time()
            pipeline = AdvancedPipeline(config=config_override)
            run_results = pipeline.run()
            elapsed = time.time() - t0

            row = {
                "polyorder": poly,
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
            print(f"\n  >> poly={poly}: CPCV Sharpe={row['cpcv_sharpe_mean']:.4f}, "
                  f"Meta Sharpe={row['meta_sharpe']:.4f}, DSR={row['dsr']:.4f}, "
                  f"Time={elapsed:.0f}s")

        except Exception as e:
            print(f"\n  >> poly={poly}: ERRO — {e}")
            results.append({
                "polyorder": poly,
                "cpcv_sharpe_mean": np.nan,
                "error": str(e),
            })

    # ── Salvar resultados ──────────────────────────────────────────
    df = pd.DataFrame(results)
    csv_path = os.path.join(save_dir, "poly_grid_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\n  Resultados salvos: {csv_path}")

    # ── Report ─────────────────────────────────────────────────────
    report = "SAVGOL POLYORDER GRID SEARCH — PIPELINE COMPLETO\n"
    report += "=" * 60 + "\n\n"
    report += f"  polyorders testados: {POLYORDERS}\n"
    report += f"  savgol_window: {SG_WINDOW} (fixo)\n"
    report += f"  ret_windows: [20, 150] (fixos)\n\n"

    cols = ["polyorder", "cpcv_sharpe_mean", "cpcv_accuracy_mean",
            "meta_sharpe", "psr", "dsr", "n_features_selected", "elapsed_s"]
    available_cols = [c for c in cols if c in df.columns]
    report += df[available_cols].to_string(index=False) + "\n\n"

    if "meta_sharpe" in df.columns:
        valid = df.dropna(subset=["meta_sharpe"])
        if len(valid) > 0:
            best = valid.loc[valid["meta_sharpe"].idxmax()]
            report += f"  MELHOR Meta Sharpe: poly={int(best['polyorder'])} "
            report += f"(SR={best['meta_sharpe']:.4f})\n"

    if "cpcv_sharpe_mean" in df.columns:
        valid = df.dropna(subset=["cpcv_sharpe_mean"])
        if len(valid) > 0:
            best = valid.loc[valid["cpcv_sharpe_mean"].idxmax()]
            report += f"  MELHOR CPCV Sharpe: poly={int(best['polyorder'])} "
            report += f"(SR={best['cpcv_sharpe_mean']:.4f})\n"

    report_path = os.path.join(save_dir, "poly_grid_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  Report salvo: {report_path}")

    # ── Plot ───────────────────────────────────────────────────────
    if "meta_sharpe" in df.columns:
        valid = df.dropna(subset=["meta_sharpe"])
        if len(valid) > 1:
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))

            ax = axes[0]
            ax.plot(valid["polyorder"], valid["cpcv_sharpe_mean"],
                    marker="o", linewidth=2, label="CPCV Sharpe")
            ax.plot(valid["polyorder"], valid["meta_sharpe"],
                    marker="s", linewidth=2, color="C1", label="Meta Sharpe")
            ax.set_xlabel("Polyorder")
            ax.set_ylabel("Sharpe Ratio")
            ax.set_title(f"Sharpe vs Polyorder (sg={SG_WINDOW})")
            ax.set_xticks(POLYORDERS)
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
            ax.legend()

            ax = axes[1]
            ax.plot(valid["polyorder"], valid["psr"],
                    marker="D", linewidth=2, color="C2")
            ax.set_xlabel("Polyorder")
            ax.set_ylabel("PSR (teste)")
            ax.set_title(f"PSR vs Polyorder (sg={SG_WINDOW})")
            ax.set_xticks(POLYORDERS)
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0.5, color="orange", linestyle="--",
                        alpha=0.7, label="50% threshold")
            ax.legend()

            plt.tight_layout()
            fig_path = os.path.join(save_dir, "poly_grid_comparison.png")
            plt.savefig(fig_path, dpi=150)
            plt.close()
            print(f"  Plot salvo: {fig_path}")

    print("\n" + "=" * 60)
    print("  POLY GRID SEARCH CONCLUIDO")
    print("=" * 60)


if __name__ == "__main__":
    run_grid()
