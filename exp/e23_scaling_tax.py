"""E23 (pre-registered, literature/prereg_e23_2026-10-28.md): E20's N / D / |C| separation repeated on Tax.
  rows  : the 25k-row Tax sample with every row repeated r = 1, 4, 16 times (N grows; domains and g3 fixed).
  dom   : Tax samples of 12.5k, 50k and 200k rows, each resampled with replacement to N = 60,000 rows (D grows).
  cands : the 50k-row sample, nested subsets (fixed random order) of all unary candidates of size 8, 16, 32, all.
Same certify call and recorded fields as exp/e20_scaling.run. Output: results/icde27/e23_scaling_tax.json
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "exp"))
from semfd.data import tax  # noqa: E402
from semfd.probes import base_attr as base  # noqa: E402
from e20_scaling import run, with_rows  # noqa: E402


def main(seeds=2):
    out = []
    path = ROOT / "results/icde27/e23_scaling_tax.json"
    for s in range(seeds):
        b25 = tax(seed=s, n_rows=25000)
        for r in (1, 4, 16):
            out.append(run(with_rows(b25, pd.concat([b25.df] * r)), b25.fds, f"e23|rows_x{r}", s))
            print(out[-1]["tag"], s, out[-1]["rows"], out[-1]["calls"], out[-1]["samples"], flush=True)
            path.write_text(json.dumps(out, indent=1))
        for n in (12500, 50000, 200000):
            ds0 = tax(seed=s, n_rows=n) if n < 200000 else tax(seed=s)
            df = ds0.df.sample(n=60000, replace=True, random_state=s)
            out.append(run(with_rows(ds0, df), ds0.fds, f"e23|dom_{n}", s))
            print(out[-1]["tag"], s, out[-1]["distinct"]["city"], out[-1]["calls"], out[-1]["samples"], flush=True)
            path.write_text(json.dumps(out, indent=1))
        b50 = tax(seed=s, n_rows=50000)
        names = list(b50.exact)
        cands = [(x, y) for x in names for y in names if x != y and base(x) != base(y) and (x, y) not in b50.exclude]
        order = [cands[i] for i in np.random.default_rng(200 + s).permutation(len(cands))]
        for m in (8, 16, 32, len(order)):
            out.append(run(b50, order[:m], f"e23|cands_{m}", s))
            print(out[-1]["tag"], s, out[-1]["calls"], out[-1]["samples"], flush=True)
            path.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
