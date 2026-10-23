"""E19 (pre-registered, literature/prereg_e19_2026-10-23.md): end-to-end wall clock with a live LLM oracle.

NDC labeler names, the seven natural candidates of E8, the same local model and prompt as E8
(exp/e8_llm_oracle.py), one process, the same number of threads, an EMPTY answer cache at the start of each arm.

  certify : load data -> build the proxy index -> certify the seven FDs (neighbour-only, declared nu_bar,
            alpha split over the candidates), each LLM call made live when a name is first queried.
  resolve : load data -> canonicalize every labeler name live -> exact g3 of the seven FDs on the
            LLM-resolved instance -> decide g3 < delta.

Each arm records its wall clock from data loading to the last decision (model loading timed separately),
the per-call latency, the 1-minute load average every 100 calls, and its decisions.
"""

import argparse
import json
import os
import re
import sys
import time
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "exp"))
import e8_llm_oracle as e8  # noqa: E402  same model, prompt and few-shot examples

OUT = ROOT / "results/icde27"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=("certify", "resolve"), required=True)
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--nu-bar", type=float, default=0.01)
    a = ap.parse_args()

    t_model = time.perf_counter()
    e8._init(a.threads)
    t_model = time.perf_counter() - t_model

    lat, load, answers = [], [], {}

    def ask(v, shown):
        _, o, sec = e8._canon((v, shown))
        answers[v] = o
        lat.append(sec)
        if len(lat) % 100 == 0:
            load.append([len(lat), os.getloadavg()[0]])
            print(a.arm, len(lat), f"{sec:.2f}s", f"load {os.getloadavg()[0]:.1f}", flush=True)

    from semfd.proxy import layer1, Attr
    from semfd.certify import certify, g3_codes
    from semfd.oracle import Canonicalizer
    from semfd.data import ndc
    label = lambda o: "llm:" + re.sub(r"[^a-z0-9]", "", layer1(o))

    t0 = time.perf_counter()
    ds = ndc(seed=0, near_miss=())
    raw = ds.df["labeler"]
    surface = raw.groupby(raw.map(layer1)).agg(lambda s: s.value_counts().index[0]).to_dict()
    phases = {"load_sec": time.perf_counter() - t0}
    res = {"arm": a.arm, "model": e8.MODEL.name, "threads": a.threads, "seed": a.seed, "delta": a.delta,
           "alpha": a.alpha, "fds": []}

    if a.arm == "certify":
        t1 = time.perf_counter()
        attrs = ds.attrs()
        phases["proxy_sec"] = time.perf_counter() - t1
        cache = {}

        def llm_f(v):
            if v not in cache:
                ask(v, surface[v])
                cache[v] = label(answers[v])
            return cache[v]
        orcs = ds.oracles()
        orcs["labeler"] = Canonicalizer(llm_f, name="labeler-llm")
        af = a.alpha / len(ds.fds)
        t2 = time.perf_counter()
        for x, y in ds.fds:            # same random streams as the E8 replay (seed s -> "e8o|s|x|y")
            r = certify(attrs[x], attrs[y], orcs[x], orcs[y], 0.9, a.delta, af,
                        np.random.default_rng(zlib.crc32(f"e8o|{a.seed}|{x}|{y}".encode())), nu_bar=a.nu_bar)
            res["fds"].append({"fd": f"{x}->{y}", "certified": bool(r["certified"]), "ub": r["ub"],
                               "samples": r["samples"]})
            print(x, y, "C" if r["certified"] else "-", f"U={r['ub']:.3f} llm_calls={len(lat)}", flush=True)
        phases["certify_sec"] = time.perf_counter() - t2
        res["llm_calls"] = len(lat)
    else:
        vals = sorted(ds.oracle["labeler"])
        t1 = time.perf_counter()
        f_llm = {}
        for v in vals:
            ask(v, surface[v])
            f_llm[v] = label(answers[v])
        phases["resolve_sec"] = time.perf_counter() - t1
        t2 = time.perf_counter()
        attrs = {c: Attr(c, ds.df[c], exact=True) for c in ds.exact}     # Layer-1 codes only, no proxy
        llm_ds = type(ds)(ds.name, ds.df, ds.exact, {**ds.oracle, "labeler": f_llm}, ds.fds, ds.meta)
        ent = llm_ds.entity_codes(attrs)
        for x, y in ds.fds:
            g = float(g3_codes(ent[x][attrs[x].codes], ent[y][attrs[y].codes]))
            res["fds"].append({"fd": f"{x}->{y}", "certified": g < a.delta, "g3_llm": g})
        phases["decide_sec"] = time.perf_counter() - t2
        res["llm_calls"] = len(lat)

    res["wall_sec"] = time.perf_counter() - t0
    res["model_load_sec"] = t_model
    res["phases"] = phases
    res["llm_sec_sum"] = float(np.sum(lat))
    res["llm_sec_p50"] = float(np.median(lat)) if lat else None
    res["llm_sec_mean"] = float(np.mean(lat)) if lat else None
    res["loadavg_1m"] = load
    res["answers"] = answers
    (OUT / f"e19_{a.arm}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "answers"}, indent=1), flush=True)


if __name__ == "__main__":
    main()
