"""Diagnostic companion to exp/e18_diag_gpg.py (H2 check, not an algorithm): if the final refined witness of GPG
name -> sic were frozen and certified on FRESH i.i.d. samples, how often would the empirical-Bernstein sequence of
Algorithm 1 (level alpha/|C|, checked every batch of 100 samples, cap 20,000) certify, and after how many samples?
The same is reported for the running mean of B that the refine runs actually saw, and for the initial witness.
Bernoulli samples with the exact means computed in e18_diag_gpg.json; 500 simulated runs each.
Output: results/icde27/e18_diag_sim.json
"""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import eb_cs  # noqa: E402


def sim(mu, alpha, target=0.05, cap=20000, batch=100, reps=500):
    ns = []
    for s in range(reps):
        x = (np.random.default_rng(s).random(cap) < mu).astype(float)
        _, hi = eb_cs(x, alpha)
        chk = hi[batch - 1::batch] < target
        ns.append((int(np.argmax(chk)) + 1) * batch if chk.any() else None)
    ok = [n for n in ns if n is not None]
    return {"mu": mu, "p_certify_within_cap": len(ok) / reps, "median_samples": float(np.median(ok)) if ok else None}


def main():
    d = json.loads((ROOT / "results/icde27/e18_diag_gpg.json").read_text())
    rows = d["rows"]
    alpha = 0.05 / 40                                   # E18 GPG: alpha / |C| with 40 unary candidates
    pick = lambda v, k: float(np.mean([r[k] for r in rows if r["variant"] == v]))
    out = {"alpha_per_candidate": alpha,
           "initial_witness": sim(pick("plain", "mu_initial"), alpha),
           "refine_running_mean": sim(pick("refine", "mean_B"), alpha),
           "refine_final_witness_frozen": sim(pick("refine", "mu_final"), alpha),
           "refine_warm_final_witness_frozen": sim(pick("refine_warm", "mu_final"), alpha)}
    (ROOT / "results/icde27/e18_diag_sim.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
