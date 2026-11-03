"""R-A (pre-registered, literature/prereg_ra_llm14b_2026-11-03.md): a second LLM oracle, Qwen2.5-14B-Instruct, for the
NDC labeler names, under the E8 protocol. Run after the manuscript freeze; writes only to results/rebuttal27/.
  --canon   step 1: canonicalize every labeler value once (the only step that calls the model)
  default   step 2: offline analysis and the E22-style replay (seeds 0-9) against the saved answers
"""

import argparse
import json
import re
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "exp"))
import e8_llm_oracle as e8  # noqa: E402
from semfd.proxy import layer1  # noqa: E402

OUT = ROOT / "results/rebuttal27"
MODEL = Path("/data2/llbench/models/Qwen2.5-14B-Instruct-Q4_K_S.gguf")
MODEL_SHA256 = "1350a659484c31b4d7123211733cc0deb4ab56e47ca8e2fc04b6a0c3b2e2c999"
label = lambda o: "llm:" + re.sub(r"[^a-z0-9]", "", layer1(o))     # as in E8/E19/E22


def load_ndc():
    from semfd.data import ndc
    ds = ndc(seed=0, near_miss=())
    vals = sorted(ds.oracle["labeler"])
    raw = ds.df["labeler"]
    surface = raw.groupby(raw.map(layer1)).agg(lambda s: s.value_counts().index[0]).to_dict()
    return ds, vals, raw, surface


def canon(procs, threads):
    OUT.mkdir(parents=True, exist_ok=True)
    e8.OUT, e8.MODEL = OUT / "ra_canon_14b.json", MODEL     # module globals read by e8._init / canonicalize_all
    _, vals, _, surface = load_ndc()
    done = e8.canonicalize_all(vals, procs, threads, surface)
    done["model_sha256"] = MODEL_SHA256
    e8.OUT.write_text(json.dumps(done))


def analyse(seeds=range(10), delta=0.05, alpha=0.05, nu_bar=0.01, theta=0.9):
    from semfd.certify import certify, g3_codes, miss_mass
    from semfd.oracle import Canonicalizer, disagreement_mass
    ds, vals, raw, _ = load_ndc()
    c14 = json.loads((OUT / "ra_canon_14b.json").read_text())
    c7 = json.loads((ROOT / "results/icde27/e8_llm_canon.json").read_text())
    missing = [v for v in vals if v not in c14["out"]]
    assert not missing, f"{len(missing)} labeler values not canonicalized yet"
    f14 = {v: label(c14["out"][v]) for v in vals}
    f7 = {v: label(c7["out"][v]) for v in vals}
    fcode = ds.oracle["labeler"]
    lab1 = list(raw.map(layer1))
    m_code = disagreement_mass(lab1, f14.__getitem__, fcode.__getitem__)
    m_7b = disagreement_mass(lab1, f14.__getitem__, f7.__getitem__)
    attrs = ds.attrs()

    def ents(f):
        e = ds.entity_codes(attrs)
        if f is not None:
            labs = [f[v] for v in attrs["labeler"].vals]
            ids = {t: i for i, t in enumerate(sorted(set(labs)))}
            e["labeler"] = np.array([ids[t] for t in labs])
        return e
    e14, e7, ecode = ents(f14), ents(f7), ents(None)
    g3 = lambda e, x, y: float(g3_codes(e[x][attrs[x].codes], e[y][attrs[y].codes]))
    offline = [{"fd": f"{x}->{y}", "g3_14b": g3(e14, x, y), "g3_7b": g3(e7, x, y), "g3_code": g3(ecode, x, y),
                "nu_14b": float(miss_mass(attrs[x], attrs[y], e14[x], e14[y], theta))} for x, y in ds.fds]
    ref = {d["fd"]: d["g3_14b"] < delta for d in offline}
    af = alpha / len(ds.fds)
    runs = []
    for s in seeds:
        cache = {}

        def f(v):
            if v not in cache:
                cache[v] = f14[v]
            return cache[v]
        orcs = ds.oracles()
        orcs["labeler"] = Canonicalizer(f, name="labeler-llm14b-fixed")
        fds = []
        for x, y in ds.fds:
            r = certify(attrs[x], attrs[y], orcs[x], orcs[y], theta, delta, af,
                        np.random.default_rng(zlib.crc32(f"e8o|{s}|{x}|{y}".encode())), nu_bar=nu_bar)
            fds.append({"fd": f"{x}->{y}", "certified": bool(r["certified"]), "ub": r["ub"], "samples": r["samples"],
                        "reference_true": ref[f"{x}->{y}"]})
        runs.append({"seed": s, "fds": fds, "calls": len(cache),
                     "false_cert": sum(d["certified"] and not d["reference_true"] for d in fds),
                     "missed_true": sum(d["reference_true"] and not d["certified"] for d in fds)})
        print(s, runs[-1]["calls"], "false", runs[-1]["false_cert"], "missed", runs[-1]["missed_true"],
              [(d["fd"], "C" if d["certified"] else "-", round(d["ub"], 4)) for d in fds], flush=True)
    off = {d["fd"]: d for d in offline}
    transfer = []
    for r in runs:
        for d in r["fds"]:
            if d["certified"] and "labeler" in d["fd"].split("->"):
                for name, m, key in (("code", m_code, "g3_code"), ("7b", m_7b, "g3_7b")):
                    b = min(1.0, d["ub"] + nu_bar + m)
                    transfer.append({"seed": r["seed"], "fd": d["fd"], "to": name, "bound": b,
                                     "g3_other": off[d["fd"]][key], "violated": off[d["fd"]][key] > b + 1e-12})
    sec = list(c14["sec"].values())
    res = {"design": "literature/prereg_ra_llm14b_2026-11-03.md", "model": MODEL.name,
           "model_sha256": c14.get("model_sha256"), "delta": delta, "alpha": alpha, "nu_bar": nu_bar,
           "n_values": len(vals), "sec_mean": float(np.mean(sec)), "sec_median": float(np.median(sec)),
           "empty_answers": sum(not c14["out"][v].strip() for v in vals),
           "agreement_14b_vs_code": e8.pair_metrics(vals, fcode, f14),
           "agreement_7b_vs_code": e8.pair_metrics(vals, fcode, f7),
           "agreement_14b_vs_7b": e8.pair_metrics(vals, f7, f14),
           "disagreement_mass_14b_code": m_code, "disagreement_mass_14b_7b": m_7b,
           "true_sets": {k: sorted(d["fd"] for d in offline if d[key] < delta)
                         for k, key in (("14b", "g3_14b"), ("7b", "g3_7b"), ("code", "g3_code"))},
           "offline": offline, "runs": runs,
           "summary": {"false_cert": sum(r["false_cert"] for r in runs), "missed_true": sum(r["missed_true"] for r in runs),
                       "true_opportunities": sum(ref.values()) * len(runs),
                       "calls_min": min(r["calls"] for r in runs), "calls_max": max(r["calls"] for r in runs),
                       "resolve_calls": len(vals), "max_nu": max(d["nu_14b"] for d in offline),
                       "transfer_violations": sum(t["violated"] for t in transfer), "n_transferred": len(transfer)},
           "transfer": transfer}
    (OUT / "ra_llm14b.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res["summary"]), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--canon", action="store_true")
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--threads", type=int, default=14)
    a = ap.parse_args()
    canon(a.procs, a.threads) if a.canon else analyse()
