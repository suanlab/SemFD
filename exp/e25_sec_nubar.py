"""E25 (R-B) post-hoc sensitivity (added after seeing the result; not in the pre-registration): the paper's neighbour-only
mode with the declared miss mass nu_bar = 0.01 (no inverse), instead of the E11 p = 0 setting with nu_bar = 0, on the
SEC table. All 40 unary candidates, alpha split over them, seeds 0-2. Writes results/icde27/e25_sec_nubar.json."""

import json
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "exp")]
from semfd.certify import certify, g3_codes  # noqa: E402
from semfd.oracle import total_calls  # noqa: E402
from e25_sec_discovery import sec  # noqa: E402


def main(seeds=range(3), delta=0.05, alpha=0.05, theta=0.9, nu_bar=0.01):
    runs = []
    for s in seeds:
        ds = sec(seed=s)
        attrs = ds.attrs()
        ent = ds.entity_codes(attrs)
        names = list(attrs)
        cands = [(x, y) for x in names for y in names if x != y and (x, y) not in ds.exclude]
        truth = {f"{x}->{y}": g3_codes(ent[x][attrs[x].codes], ent[y][attrs[y].codes]) for x, y in cands}
        orcs, fds = ds.oracles(), {}
        for x, y in cands:
            r = certify(attrs[x], attrs[y], orcs[x], orcs[y], theta, delta, alpha / len(cands),
                        np.random.default_rng(zlib.crc32(f"rbnu|{s}|{x}|{y}".encode())), nu_bar=nu_bar)
            fds[f"{x}->{y}"] = {"certified": bool(r["certified"]), "ub": float(r["ub"]), "true": bool(truth[f"{x}->{y}"] <= delta), "g3": float(truth[f"{x}->{y}"])}
        run = {"seed": s, "calls": total_calls(orcs), "fds": fds,
               "false": sorted(k for k, v in fds.items() if v["certified"] and not v["true"]),
               "missed": sorted(k for k, v in fds.items() if v["true"] and not v["certified"])}
        runs.append(run)
        print(s, "false", run["false"], "missed", run["missed"], "calls", run["calls"],
              "name->stprba U", round(fds["name->stprba"]["ub"], 4), flush=True)
    (ROOT / "results/icde27/e25_sec_nubar.json").write_text(json.dumps(
        {"design": "post-hoc sensitivity, see docstring", "nu_bar": nu_bar, "runs": runs}, indent=1))


if __name__ == "__main__":
    main()
