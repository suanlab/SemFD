"""E22 (pre-registered, literature/prereg_e22_2026-10-28.md): the E19 certify arm replayed against ONE fixed oracle,
the LLM answers the E19 resolve run saved for every labeler name. No LLM is called. Reference decisions are the
resolve arm's exact decisions (g3 under the same labels < delta). Seeds 0-2 match E19; 3-9 are new.
Also recorded, offline from the full fixed mapping (evaluation only, added 10-29 after the CHECK.md audit): each
candidate's exact g3 under these labels and the miss mass nu of the neighbour-only witness, to check nu <= nu_bar.
Output: results/icde27/e22_fixed_oracle.json
"""

import json
import re
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.proxy import layer1  # noqa: E402
from semfd.certify import certify, g3_codes, miss_mass  # noqa: E402
from semfd.oracle import Canonicalizer  # noqa: E402
from semfd.data import ndc  # noqa: E402

OUT = ROOT / "results/icde27"


def main(seeds=range(10), delta=0.05, alpha=0.05, nu_bar=0.01):
    res_r = json.loads((OUT / "e19_resolve.json").read_text())
    answers = res_r["answers"]
    ref = {f["fd"]: bool(f["certified"]) for f in res_r["fds"]}
    live = {s: {f["fd"]: bool(f["certified"]) for f in json.loads((OUT / f"e19_certify_s{s}.json").read_text())["fds"]}
            for s in range(3)}
    label = lambda o: "llm:" + re.sub(r"[^a-z0-9]", "", layer1(o))     # as in exp/e19_end_to_end.py
    ds = ndc(seed=0, near_miss=())
    attrs = ds.attrs()
    af = alpha / len(ds.fds)
    ent = ds.entity_codes(attrs)
    labs = [label(answers[v]) for v in attrs["labeler"].vals]
    ids = {t: i for i, t in enumerate(sorted(set(labs)))}
    ent["labeler"] = np.array([ids[t] for t in labs])
    offline = []
    for x, y in ds.fds:
        g = float(g3_codes(ent[x][attrs[x].codes], ent[y][attrs[y].codes]))
        offline.append({"fd": f"{x}->{y}", "g3": g, "nu": float(miss_mass(attrs[x], attrs[y], ent[x], ent[y], 0.9)),
                        "matches_reference": (g < delta) == ref[f"{x}->{y}"]})
    print("offline", [(d["fd"], round(d["g3"], 4), round(d["nu"], 5), d["matches_reference"]) for d in offline], flush=True)
    runs = []
    for s in seeds:
        cache = {}

        def f(v):
            if v not in cache:
                cache[v] = label(answers[v])
            return cache[v]
        orcs = ds.oracles()
        orcs["labeler"] = Canonicalizer(f, name="labeler-llm-fixed")
        fds = []
        for x, y in ds.fds:
            r = certify(attrs[x], attrs[y], orcs[x], orcs[y], 0.9, delta, af,
                        np.random.default_rng(zlib.crc32(f"e8o|{s}|{x}|{y}".encode())), nu_bar=nu_bar)
            fd = f"{x}->{y}"
            fds.append({"fd": fd, "certified": bool(r["certified"]), "ub": r["ub"], "samples": r["samples"],
                        "reference_true": ref[fd], "same_as_e19_live": live[s][fd] == bool(r["certified"]) if s in live else None})
        row = {"seed": s, "fds": fds, "calls": len(cache),
               "false_cert": sum(d["certified"] and not d["reference_true"] for d in fds),
               "missed_true": sum(d["reference_true"] and not d["certified"] for d in fds),
               "llm_sec_estimate": len(cache) * res_r["llm_sec_mean"]}
        runs.append(row)
        print(s, row["calls"], "false", row["false_cert"], "missed", row["missed_true"],
              [(d["fd"], "C" if d["certified"] else "-", round(d["ub"], 4)) for d in fds], flush=True)
    out = {"design": "literature/prereg_e22_2026-10-28.md", "delta": delta, "alpha": alpha, "nu_bar": nu_bar,
           "oracle": "e19_resolve.json answers (fixed)", "resolve_calls": res_r["llm_calls"],
           "resolve_llm_sec_mean": res_r["llm_sec_mean"], "reference": ref, "offline_fixed_mapping": offline, "runs": runs}
    (OUT / "e22_fixed_oracle.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
