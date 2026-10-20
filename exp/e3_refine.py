"""Power with a self-refining witness (paper Sec. VI, coverage and power).

Same E3 near-threshold setting as e3_ideal_witness.py (GeoNames, 4k cities, country FDs
with injected error rates and source conflicts). For each FD, REPS independent
certifications with the fixed proxy witness and with refine=True (semfd.certify: every
entity whose alias class an earlier batch fetched becomes its own cluster; predictable,
hence sound; no extra oracle calls). Reports certification rate, false-certification
rate (g3 > delta), mean samples and mean oracle calls (fresh caches per run).
Output: results/icde27/e3_refine<tag>.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import certify, g3_codes  # noqa: E402
from semfd.data import LOADERS  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--dataset", default="geonames")
ap.add_argument("--kw", default='{"n_cities": 4000, "near_miss": [0.03, 0.04, 0.05, 0.06, 0.07], '
                                '"conflict": [0.04, 0.06, 0.07]}')
ap.add_argument("--reps", type=int, default=200)
ap.add_argument("--prefix", default="country_", help="only FDs whose RHS starts with this")
ap.add_argument("--tag", default="")
a = ap.parse_args()
ds = LOADERS[a.dataset](seed=0, **json.loads(a.kw))
attrs = ds.attrs()
ent = ds.entity_codes(attrs)
out = {"dataset": ds.name, "reps": a.reps, "delta": 0.05, "alpha": 0.05, "fds": []}
outp = ROOT / f"results/icde27/e3_refine_{a.dataset}{a.tag}.json"
for x, y in ds.fds:
    if not y.startswith(a.prefix):
        continue
    ax, ay = attrs[x], attrs[y]
    g3 = g3_codes(ent[x][ax.codes], ent[y][ay.codes])
    rec = {"fd": f"{x}->{y}", "g3": g3}
    for name, ref in (("proxy", False), ("refine", True)):
        runs = []
        for i in range(a.reps):
            o = ds.oracles(inverse=True)
            runs.append(certify(ax, ay, o[x], o[y], 0.9, 0.05, 0.05, np.random.default_rng(i), inverse=True,
                                refine=ref))
        rec[name] = {"cert_rate": float(np.mean([r["certified"] for r in runs])),
                     "false_cert_rate": float(np.mean([r["certified"] and g3 > 0.05 for r in runs])),
                     "samples_mean": float(np.mean([r["samples"] for r in runs])),
                     "calls_mean": float(np.mean([r["calls"] for r in runs]))}
    out["fds"].append(rec)
    print(rec["fd"], f"g3={g3:.4f}", {k: rec[k] for k in ("proxy", "refine")}, flush=True)
    outp.write_text(json.dumps(out, indent=1))
