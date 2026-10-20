"""Diagnostic (paper Sec. VI, coverage and power): how much of the power loss near delta is witness slack?
Replace the proxy partition by the ORACLE-induced partition (X values grouped by entity, as inverse access reveals) and
keep the modal representative; measure E[B] and the certification rate on the E3 near-threshold FDs. Not a method
change: the ideal witness needs the full inverse, which a certificate does not have. Output:
results/icde27/e3_ideal_witness.json"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import certify, g3_codes  # noqa: E402
from semfd.data import LOADERS  # noqa: E402
sys.path.insert(0, str(ROOT / "exp"))
from e3_coverage import exact_mean_B  # noqa: E402

REPS = 200
kw = {"n_cities": 4000, "near_miss": [0.03, 0.04, 0.05, 0.06, 0.07], "conflict": [0.04, 0.06, 0.07]}
ds = LOADERS["geonames"](seed=0, **kw)
attrs = ds.attrs()
ent = ds.entity_codes(attrs)
orcs = ds.oracles(inverse=True)
out = {"reps": REPS, "fds": []}
for x, y in ds.fds:
    if not y.startswith("country_"):
        continue
    ax, ay = attrs[x], attrs[y]
    g3 = g3_codes(ent[x][ax.codes], ent[y][ay.codes])
    rec = {"fd": f"{x}->{y}", "g3": g3}
    for name in ("proxy", "ideal"):
        if name == "ideal":
            proxy_partition = ax.partition
            ax.partition = lambda theta, e=ent[x]: e      # oracle-induced partition
        EB = exact_mean_B(ax, ay, orcs[x], orcs[y], 0.9)
        runs = [certify(ax, ay, orcs[x], orcs[y], 0.9, 0.05, 0.05, np.random.default_rng(i), inverse=True)
                for i in range(REPS)]
        rec[name] = {"EB": EB, "cert_rate": float(np.mean([r["certified"] for r in runs])),
                     "false_cert_rate": float(np.mean([r["certified"] and g3 > 0.05 for r in runs])),
                     "samples_mean": float(np.mean([r["samples"] for r in runs]))}
        if name == "ideal":
            ax.partition = proxy_partition
    out["fds"].append(rec)
    print(rec["fd"], f"g3={g3:.4f}", {k: (round(v['EB'], 4), v['cert_rate']) for k, v in rec.items() if k in ('proxy', 'ideal')}, flush=True)
(ROOT / "results/icde27/e3_ideal_witness.json").write_text(json.dumps(out, indent=1))
