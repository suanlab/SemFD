"""Fairer canonicalize-all baseline (paper Sec. VI, Table III): resolve only the tolerant attributes that actually have
variants, i.e. whose Layer-1 domain is larger than their number of oracle entities. Choosing those attributes needs
the oracle itself, so this is an oracle-informed LOWER bound on the cost of resolution (favouring the baseline).
Counted over the same attributes as E1b (probe copies share their source's domain). Output:
results/icde27/canon_variant_only.json"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.data import LOADERS  # noqa: E402
from semfd.proxy import layer1  # noqa: E402

SETS = {"geonames_16k": ("geonames", {"n_cities": 16000}), "tax": ("tax", {}), "ndc": ("ndc", {}),
        "geonames_128k": ("geonames", {"n_cities": 128000, "source": "cities500.txt"}),   # E2's largest size (2 seeds)
        "gpg": ("gpg", {})}
out = {}
for key, (name, kw) in SETS.items():
    per_seed = []
    for seed in range(2 if key == "geonames_128k" else 3):
        ds = LOADERS[name](seed=seed, **kw)
        doms = {}
        for a, ex in ds.exact.items():
            if ex or a not in ds.oracle:
                continue
            vals = set(ds.df[a].map(layer1))
            doms.setdefault(id(ds.oracle[a]), (a, set(), ds.oracle[a]))[1].update(vals)
        full = sum(len(v) for _, v, _ in doms.values())
        var = {a: (len(v), len({o[x] for x in v})) for a, v, o in doms.values()}
        only = sum(n for n, e in var.values() if n > e)
        # with inverse access, resolution can pay one forward + one inverse call per ENTITY instead of one call per value
        inv_aware = sum(min(n, 2 * e) for n, e in var.values())
        per_seed.append({"canon_all": full, "canon_variant_only": only, "canon_inverse_aware": inv_aware, "attrs": var})
    out[key] = {"canon_all": float(np.mean([p["canon_all"] for p in per_seed])),
                "canon_variant_only": float(np.mean([p["canon_variant_only"] for p in per_seed])),
                "canon_inverse_aware": float(np.mean([p["canon_inverse_aware"] for p in per_seed])),
                "attrs_seed0": per_seed[0]["attrs"]}
    print(key, out[key]["canon_all"], out[key]["canon_variant_only"], per_seed[0]["attrs"], flush=True)
(ROOT / "results/icde27/canon_variant_only.json").write_text(json.dumps(out, indent=1))
