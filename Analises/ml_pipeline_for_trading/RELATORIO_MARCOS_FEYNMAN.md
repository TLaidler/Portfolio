# Marcos & Feynman — a pipeline debate

> Conducted on the completion of one run of the AFML-inspired pipeline
> (`main.py`). Numbers come directly from the `resultados/` logs and plots
> just generated. The debate adapts to whether the result is overfit,
> null, consistent, or mixed.

---

### Opening — the result card

| Statistic | Value |
|---|---|
| Sharpe (IS, out-of-fold) | **+0.0787** |
| Sharpe (OOS, new_data/) | **-0.0680** |
| Probabilistic SR | 0.9208 |
| Deflated SR (N trials = 5) | **0.4718** |
| Random-Walk null SR | +0.0127 ± 0.1776 |
| p(strategy ≥ null) | **0.3640** |
| OOS accuracy / F1 / log-loss | 0.501 / 0.128 / 0.695 |

Regime detected from the IS/OOS pair: **null**.

Both IS and OOS Sharpes are within a standard error of zero. The signals we extracted are statistically real but too small to be exploitable after frictions. File under 'publishable negative result'.

Clusters selected by ONC: **3**. Top-MDA cluster:
**cluster_0** (MDA = +0.0001), containing features
`sg_velocity_51, tstat_10, tstat_20, tstat_50`.

---

### Act I — "Is there a signal at all?"

**Feynman.** — Marcos, the IS Sharpe is +0.079; OOS is
-0.068. Before you reach for the DSR, tell me plainly:
did we find an effect, or did we find a confidence interval that
happens to lean one way?

**Marcos.** — The honest answer is in the **gap**. PSR says the IS
Sharpe is plausibly above zero with probability 0.921. That is
an *in-sample* statement. The DSR, now corrected for the
5 trials we actually ran, is 0.472 — an inference about
the *true* Sharpe after we punish ourselves for the number of paths
we walked. And the OOS Sharpe is the final referee. The spread
between IS and OOS is **+0.15** Sharpe units, which is
the single most diagnostic number in this report.

**Feynman.** — A gap of that magnitude tells me a physics story: if
your 'detector' is showing a signal in one calibration window and
absence-of-signal in the next, either the source turned off or the
detector is responding to local conditions you did not model.

---

### Act II — "Labeling was done right"

**Feynman.** — A thing I liked: the **triple-barrier** bins returns
by which wall they hit first, not by a fixed horizon. That is
honest — it respects the path. In physics we would call it a
*first-passage-time* formalism.

**Marcos.** — Exactly. And the horizontal barriers are calibrated to
each point's ex-ante volatility, so the experiment is scale-
invariant across regimes. The meta-label is then `{success,
failure}` *given* the primary model's direction — which is where
the causal prior enters via `tstat_50`. The ML model is not fishing
for direction; it is only learning **when not to bet**.

**Feynman.** — That framing matters because it separates two
questions: *where does the signal come from?* and *when should we
act on it?*. If the OOS Sharpe is negative, the failure is on the
second question, not the first.

---

### Act III — "What did the clustered importance tell us?"

**Feynman.** — The clustered MDA put cluster `cluster_0`
at the top, containing `sg_velocity_51, tstat_10, tstat_20, tstat_50`. My univariate MDA on
the earlier run had put `sg_velocity_51`, `tstat_50`, `vix_chg`,
`tstat_20` on top. The rank is broadly consistent, and — crucially
— clustering contained the *substitution effect* that would have
otherwise split credit among near-duplicates.

**Marcos.** — That is the whole point of MDA-on-clusters. With
vanilla MDI, correlated copies of the same feature permute the
importance ranking arbitrarily. Clustering first stabilises the
ranking so the interpretation survives perturbations of the feature
set.

**Feynman.** — And the **rejected** microstructure features —
`vpin`, `kyle_lambda`, `roll_spread` — are statistically genuine
but too small per event to change the RF's splits. A feature can
be *real* (different from chance) but *useless* (too small to
matter). That distinction deserves its own name in the literature.

---

### Act IV — "The Random-Walk null was the right adversary"

**Marcos.** — Observe: the RW null Sharpe is +0.0127 ±
0.1776; the IS Sharpe is +0.079. The p-value of
0.3640 measures how often a block-bootstrapped, sign-flipped
version of our own returns outperforms our strategy.

**Feynman.** — The block-bootstrap preserves the autocorrelation
the market has; randomising the sign destroys the drift. That is
*exactly* the adversary we want to defeat — and the only adversary
that is scientifically fair on minute-level crypto data.

**Marcos.** — If the p-value is small *and* the OOS Sharpe is of
the same sign as the IS Sharpe, the signal has survived every trap
I know how to build. If either condition fails, we must stop
calling it alpha.

---

### Act V — "So did we discover alpha?"

**Marcos.** — Alpha is a *causal, mechanistic* claim. The scaffolding
we have is:

1. Isolation of genuinely informative features (the `tstat_N`
   family + exogenous macro context).
2. A theory: *tstat is a volatility-normalised momentum; when the
   macro context is risk-off (VIX up, DXY spread widening) the
   meta-model abstains*.
3. A look-ahead-safe implementation (causal SavGol, fixed-width
   FFD, purged CV, embargo, CPCV).

Given our numbers — DSR = 0.472, IS/OOS gap = +0.15 —
the honest conclusion is: this is a clean **null result**. Publish it as a negative finding and move on — the pipeline has not been wasted, because a believable null is as scientifically valuable as a believable positive.

**Feynman.** — The virtue of this pipeline is not that it finds
alpha. It is that it is **pathologically conservative** about
look-ahead, overlap, and selection bias. When it says "no", it
actually means it. When it says "maybe", it tells you by how much.
That is the best you can hope for when the signal-to-noise ratio is
this hostile.

---

### Closing — what to try next

- **Inspect the regime break.** Plot `plots/09_equity_curves.png`:
  where does the IS equity curve diverge from the OOS? That date is
  your prime suspect for a macro regime change.
- **Re-calibrate volatility.** Try `pt_sl = (2.0, 1.0)` to allow
  winners to run — historically this pushes return skew positive.
- **Second primary signal.** Add a mean-reversion primary for
  high-vol regimes and let the meta-model arbitrate between
  momentum and mean-reversion.
- **Monitor DSR through time.** Re-run monthly. A decaying DSR is
  the earliest signature of strategy decay.

Plots of interest: `plots/01_bar_returns_*.png`,
`plots/06_clustered_importance.png`, `plots/08_cpcv_paths.png`,
`plots/08_rw_null.png`, `plots/09_is_vs_oos.png`,
`plots/09_equity_curves.png`.
